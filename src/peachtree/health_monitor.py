"""
PeachTree Dataset Health Monitor

Real-time monitoring and health scoring for PeachTree datasets with
automated alerts, trend analysis, and quality degradation detection.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from typing import Any, Literal

from peachtree.quality import DatasetQualityScorer
from peachtree.dedup import DatasetDeduplicator


class HealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthMetric:
    """Individual health metric measurement"""
    name: str
    value: float
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetHealthSnapshot:
    """Point-in-time health snapshot of a dataset"""
    dataset_path: str
    timestamp: str
    record_count: int
    quality_score: float
    duplicate_ratio: float
    provenance_ratio: float  # Ratio of records with complete provenance
    safety_ratio: float  # Ratio of records passing safety gates
    metrics: tuple[HealthMetric, ...]
    overall_status: HealthStatus
    alerts: tuple[str, ...]

    @property
    def is_healthy(self) -> bool:
        return self.overall_status in (HealthStatus.EXCELLENT, HealthStatus.GOOD)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "timestamp": self.timestamp,
            "record_count": self.record_count,
            "quality_score": self.quality_score,
            "duplicate_ratio": self.duplicate_ratio,
            "provenance_ratio": self.provenance_ratio,
            "safety_ratio": self.safety_ratio,
            "overall_status": self.overall_status.value,
            "is_healthy": self.is_healthy,
            "metrics": [m.to_dict() for m in self.metrics],
            "alerts": list(self.alerts),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        status_emoji = {
            HealthStatus.EXCELLENT: "🟢",
            HealthStatus.GOOD: "🟢",
            HealthStatus.WARNING: "🟡",
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.UNKNOWN: "⚪",
        }
        emoji = status_emoji.get(self.overall_status, "⚪")
        
        lines = [
            "# PeachTree Dataset Health Report",
            "",
            f"{emoji} **Status:** `{self.overall_status.value.upper()}`",
            "",
            "## Overview",
            "",
            f"- **Dataset:** `{self.dataset_path}`",
            f"- **Timestamp:** `{self.timestamp}`",
            f"- **Records:** `{self.record_count:,}`",
            f"- **Quality Score:** `{self.quality_score:.1f}/100`",
            f"- **Duplicate Ratio:** `{self.duplicate_ratio:.1%}`",
            f"- **Provenance Coverage:** `{self.provenance_ratio:.1%}`",
            f"- **Safety Coverage:** `{self.safety_ratio:.1%}`",
            "",
            "## Health Metrics",
            "",
            "| Metric | Value | Status | Warning | Critical | Message |",
            "|--------|-------|--------|---------|----------|---------|",
        ]
        
        for metric in self.metrics:
            status_icon = status_emoji.get(metric.status, "⚪")
            lines.append(
                f"| {metric.name} | {metric.value:.2f} | {status_icon} {metric.status.value} | "
                f"{metric.threshold_warning} | {metric.threshold_critical} | {metric.message} |"
            )
        
        if self.alerts:
            lines += ["", "## ⚠️ Alerts", ""]
            for alert in self.alerts:
                lines.append(f"- {alert}")
        else:
            lines += ["", "## ✅ No Active Alerts", ""]
        
        return "\n".join(lines)


@dataclass(frozen=True)
class HealthTrend:
    """Trend analysis across multiple snapshots"""
    dataset_path: str
    snapshots: tuple[DatasetHealthSnapshot, ...]
    trend_direction: Literal["improving", "stable", "degrading", "unknown"]
    quality_change: float  # Change in quality score
    record_count_change: int
    alerts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "snapshot_count": len(self.snapshots),
            "trend_direction": self.trend_direction,
            "quality_change": self.quality_change,
            "record_count_change": self.record_count_change,
            "alerts": list(self.alerts),
            "latest_status": self.snapshots[-1].overall_status.value if self.snapshots else "unknown",
        }


class DatasetHealthMonitor:
    """Monitor and track dataset health over time"""
    
    def __init__(
        self,
        history_dir: Path | str = "data/health-history",
        quality_warning: float = 75.0,
        quality_critical: float = 60.0,
        duplicate_warning: float = 0.15,
        duplicate_critical: float = 0.30,
        provenance_warning: float = 0.90,
        provenance_critical: float = 0.75,
    ):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.quality_warning = quality_warning
        self.quality_critical = quality_critical
        self.duplicate_warning = duplicate_warning
        self.duplicate_critical = duplicate_critical
        self.provenance_warning = provenance_warning
        self.provenance_critical = provenance_critical

    def check_health(self, dataset_path: str | Path, save_history: bool = True) -> DatasetHealthSnapshot:
        """Generate health snapshot for a dataset"""
        path = Path(dataset_path)
        timestamp = datetime.utcnow().isoformat()
        
        # Run quality scoring
        scorer = DatasetQualityScorer()
        quality_report = scorer.score_dataset(path)
        
        # Run deduplication analysis
        deduplicator = DatasetDeduplicator()
        dedup_report = deduplicator.analyze(path)
        
        # Calculate provenance and safety ratios
        records = self._read_jsonl(path)
        provenance_complete = sum(
            1 for r in records
            if r.get("source_repo") != "unknown" and r.get("source_path") != "unknown"
        )
        provenance_ratio = provenance_complete / len(records) if records else 0.0
        
        safety_passed = sum(
            1 for r in records
            if isinstance(r.get("safety_score"), (int, float)) and r.get("safety_score", 0) >= 0.8
        )
        safety_ratio = safety_passed / len(records) if records else 0.0
        
        # Build health metrics
        metrics: list[HealthMetric] = []
        alerts: list[str] = []
        
        # Quality metric
        quality_status = self._determine_status(
            quality_report.average_score,
            self.quality_warning,
            self.quality_critical,
            higher_is_better=True
        )
        metrics.append(HealthMetric(
            name="Quality Score",
            value=quality_report.average_score,
            status=quality_status,
            threshold_warning=self.quality_warning,
            threshold_critical=self.quality_critical,
            message="Average quality score across all records"
        ))
        if quality_status == HealthStatus.CRITICAL:
            alerts.append(f"CRITICAL: Quality score ({quality_report.average_score:.1f}) below threshold ({self.quality_critical})")
        elif quality_status == HealthStatus.WARNING:
            alerts.append(f"WARNING: Quality score ({quality_report.average_score:.1f}) below target ({self.quality_warning})")
        
        # Duplicate metric
        duplicate_status = self._determine_status(
            dedup_report.duplicate_ratio,
            self.duplicate_warning,
            self.duplicate_critical,
            higher_is_better=False
        )
        metrics.append(HealthMetric(
            name="Duplicate Ratio",
            value=dedup_report.duplicate_ratio,
            status=duplicate_status,
            threshold_warning=self.duplicate_warning,
            threshold_critical=self.duplicate_critical,
            message="Ratio of duplicate records in dataset"
        ))
        if duplicate_status == HealthStatus.CRITICAL:
            alerts.append(f"CRITICAL: Duplicate ratio ({dedup_report.duplicate_ratio:.1%}) exceeds threshold ({self.duplicate_critical:.1%})")
        elif duplicate_status == HealthStatus.WARNING:
            alerts.append(f"WARNING: High duplicate ratio ({dedup_report.duplicate_ratio:.1%})")
        
        # Provenance metric
        provenance_status = self._determine_status(
            provenance_ratio,
            self.provenance_warning,
            self.provenance_critical,
            higher_is_better=True
        )
        metrics.append(HealthMetric(
            name="Provenance Coverage",
            value=provenance_ratio,
            status=provenance_status,
            threshold_warning=self.provenance_warning,
            threshold_critical=self.provenance_critical,
            message="Ratio of records with complete provenance"
        ))
        if provenance_status == HealthStatus.WARNING:
            alerts.append(f"WARNING: Provenance coverage ({provenance_ratio:.1%}) below target")
        
        # Safety metric
        safety_status = HealthStatus.GOOD if safety_ratio >= 0.95 else HealthStatus.WARNING if safety_ratio >= 0.80 else HealthStatus.CRITICAL
        metrics.append(HealthMetric(
            name="Safety Coverage",
            value=safety_ratio,
            status=safety_status,
            threshold_warning=0.95,
            threshold_critical=0.80,
            message="Ratio of records passing safety gates"
        ))
        
        # Determine overall status
        statuses = [m.status for m in metrics]
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif quality_report.average_score >= 90:
            overall_status = HealthStatus.EXCELLENT
        else:
            overall_status = HealthStatus.GOOD
        
        snapshot = DatasetHealthSnapshot(
            dataset_path=str(path),
            timestamp=timestamp,
            record_count=len(records),
            quality_score=quality_report.average_score,
            duplicate_ratio=dedup_report.duplicate_ratio,
            provenance_ratio=provenance_ratio,
            safety_ratio=safety_ratio,
            metrics=tuple(metrics),
            overall_status=overall_status,
            alerts=tuple(alerts),
        )
        
        if save_history:
            self._save_snapshot(snapshot)
        
        return snapshot

    def analyze_trend(self, dataset_path: str | Path, days: int = 7) -> HealthTrend:
        """Analyze health trend over time"""
        path = Path(dataset_path)
        snapshots = self._load_history(path, days)
        
        if len(snapshots) < 2:
            return HealthTrend(
                dataset_path=str(path),
                snapshots=snapshots,
                trend_direction="unknown",
                quality_change=0.0,
                record_count_change=0,
                alerts=("Insufficient history for trend analysis (need at least 2 snapshots)",),
            )
        
        # Calculate changes
        oldest = snapshots[0]
        latest = snapshots[-1]
        quality_change = latest.quality_score - oldest.quality_score
        record_count_change = latest.record_count - oldest.record_count
        
        # Determine trend
        if quality_change > 5.0:
            trend_direction = "improving"
        elif quality_change < -5.0:
            trend_direction = "degrading"
        else:
            trend_direction = "stable"
        
        # Generate trend alerts
        alerts: list[str] = []
        if trend_direction == "degrading":
            alerts.append(f"Quality declining: {quality_change:+.1f} points over {days} days")
        if record_count_change < 0:
            alerts.append(f"Record count decreased by {-record_count_change:,} records")
        if latest.duplicate_ratio > oldest.duplicate_ratio + 0.05:
            alerts.append("Duplicate ratio increasing significantly")
        
        return HealthTrend(
            dataset_path=str(path),
            snapshots=snapshots,
            trend_direction=trend_direction,
            quality_change=quality_change,
            record_count_change=record_count_change,
            alerts=tuple(alerts),
        )

    def _determine_status(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        higher_is_better: bool = True,
    ) -> HealthStatus:
        """Determine health status based on value and thresholds"""
        if higher_is_better:
            if value >= warning_threshold:
                return HealthStatus.EXCELLENT if value >= 95 else HealthStatus.GOOD
            elif value >= critical_threshold:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL
        else:
            if value <= warning_threshold:
                return HealthStatus.EXCELLENT if value <= 0.05 else HealthStatus.GOOD
            elif value <= critical_threshold:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL

    def _save_snapshot(self, snapshot: DatasetHealthSnapshot) -> None:
        """Save snapshot to history"""
        dataset_name = Path(snapshot.dataset_path).stem
        date = datetime.fromisoformat(snapshot.timestamp).strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_name}_{date}.json"
        history_file = self.history_dir / filename
        history_file.write_text(snapshot.to_json(), encoding="utf-8")

    def _load_history(self, dataset_path: Path, days: int) -> tuple[DatasetHealthSnapshot, ...]:
        """Load historical snapshots for a dataset"""
        dataset_name = dataset_path.stem
        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots: list[DatasetHealthSnapshot] = []
        
        for history_file in sorted(self.history_dir.glob(f"{dataset_name}_*.json")):
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                timestamp = datetime.fromisoformat(data["timestamp"])
                if timestamp >= cutoff:
                    # Reconstruct snapshot (simplified)
                    snapshots.append(DatasetHealthSnapshot(
                        dataset_path=data["dataset_path"],
                        timestamp=data["timestamp"],
                        record_count=data["record_count"],
                        quality_score=data["quality_score"],
                        duplicate_ratio=data["duplicate_ratio"],
                        provenance_ratio=data["provenance_ratio"],
                        safety_ratio=data["safety_ratio"],
                        metrics=tuple(),  # Don't reload full metrics
                        overall_status=HealthStatus(data["overall_status"]),
                        alerts=tuple(data["alerts"]),
                    ))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        return tuple(snapshots)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        """Read JSONL file"""
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records
