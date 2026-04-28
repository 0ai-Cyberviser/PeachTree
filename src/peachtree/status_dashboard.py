"""
PeachTree Dataset Status Dashboard

Unified status view combining health, quality, deduplication, and provenance metrics.
Provides quick at-a-glance status for single datasets or entire directories.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from peachtree.health_monitor import DatasetHealthMonitor, HealthStatus
from peachtree.quality import DatasetQualityScorer
from peachtree.dedup import DatasetDeduplicator


@dataclass(frozen=True)
class DatasetStatus:
    """Unified status for a dataset"""
    dataset_path: str
    timestamp: str
    record_count: int
    health_status: HealthStatus
    quality_score: float
    quality_gate_passed: bool
    duplicate_ratio: float
    provenance_coverage: float
    safety_coverage: float
    overall_ready: bool
    issues: tuple[str, ...]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "timestamp": self.timestamp,
            "metrics": {
                "record_count": self.record_count,
                "quality_score": self.quality_score,
                "duplicate_ratio": self.duplicate_ratio,
                "provenance_coverage": self.provenance_coverage,
                "safety_coverage": self.safety_coverage,
            },
            "gates": {
                "health_status": self.health_status.value,
                "quality_gate_passed": self.quality_gate_passed,
                "overall_ready": self.overall_ready,
            },
            "issues": list(self.issues),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class MultiDatasetStatus:
    """Status summary for multiple datasets"""
    directory: str
    timestamp: str
    total_datasets: int
    ready_datasets: int
    datasets: tuple[DatasetStatus, ...]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "directory": self.directory,
            "timestamp": self.timestamp,
            "summary": {
                "total_datasets": self.total_datasets,
                "ready_datasets": self.ready_datasets,
                "not_ready": self.total_datasets - self.ready_datasets,
                "readiness_ratio": self.ready_datasets / self.total_datasets if self.total_datasets > 0 else 0.0,
            },
            "datasets": [d.to_dict() for d in self.datasets],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
    
    def to_markdown(self) -> str:
        lines = [
            "# Dataset Status Dashboard",
            "",
            f"**Directory:** `{self.directory}`",
            f"**Generated:** {self.timestamp}",
            "",
            "## Summary",
            "",
            f"- Total Datasets: {self.total_datasets}",
            f"- Ready: {self.ready_datasets} ✅",
            f"- Not Ready: {self.total_datasets - self.ready_datasets} ❌",
            f"- Readiness: {self.ready_datasets / self.total_datasets * 100 if self.total_datasets > 0 else 0:.1f}%",
            "",
            "## Dataset Status",
            "",
            "| Dataset | Records | Health | Quality | Duplicates | Provenance | Ready |",
            "|---------|---------|--------|---------|------------|------------|-------|",
        ]
        
        for dataset in self.datasets:
            name = Path(dataset.dataset_path).name
            health_emoji = {
                HealthStatus.EXCELLENT: "🟢",
                HealthStatus.GOOD: "🟢",
                HealthStatus.WARNING: "🟡",
                HealthStatus.CRITICAL: "🔴",
                HealthStatus.UNKNOWN: "⚪",
            }[dataset.health_status]
            
            quality_emoji = "✅" if dataset.quality_gate_passed else "❌"
            dup_emoji = "✅" if dataset.duplicate_ratio < 0.15 else "⚠️" if dataset.duplicate_ratio < 0.30 else "❌"
            prov_emoji = "✅" if dataset.provenance_coverage > 0.9 else "⚠️" if dataset.provenance_coverage > 0.75 else "❌"
            ready_emoji = "✅" if dataset.overall_ready else "❌"
            
            lines.append(
                f"| {name} | {dataset.record_count:,} | "
                f"{health_emoji} {dataset.health_status.value} | "
                f"{quality_emoji} {dataset.quality_score:.1f} | "
                f"{dup_emoji} {dataset.duplicate_ratio:.1%} | "
                f"{prov_emoji} {dataset.provenance_coverage:.1%} | "
                f"{ready_emoji} |"
            )
        
        # Add issues section if any dataset has issues
        has_issues = any(dataset.issues for dataset in self.datasets)
        if has_issues:
            lines.extend(["", "## Issues", ""])
            for dataset in self.datasets:
                if dataset.issues:
                    name = Path(dataset.dataset_path).name
                    lines.append(f"### {name}")
                    for issue in dataset.issues:
                        lines.append(f"- {issue}")
                    lines.append("")
        
        return "\n".join(lines)


class StatusDashboard:
    """Collect and display unified dataset status"""
    
    def __init__(
        self,
        quality_warning: float = 75.0,
        quality_critical: float = 60.0,
        duplicate_warning: float = 0.15,
        duplicate_critical: float = 0.30,
        min_average_score: int = 70,
        max_failed_ratio: float = 0.1,
    ):
        self.health_monitor = DatasetHealthMonitor(
            quality_warning=quality_warning,
            quality_critical=quality_critical,
            duplicate_warning=duplicate_warning,
            duplicate_critical=duplicate_critical,
        )
        self.quality_scorer = DatasetQualityScorer(
            min_average_score=min_average_score,
            max_failed_ratio=max_failed_ratio,
        )
        self.deduplicator = DatasetDeduplicator()
    
    def get_status(self, dataset_path: str | Path) -> DatasetStatus:
        """Get unified status for a single dataset"""
        dataset_str = str(dataset_path)
        timestamp = datetime.utcnow().isoformat()
        
        # Gather metrics from different modules
        health_snapshot = self.health_monitor.check_health(dataset_str)
        quality_report = self.quality_scorer.score_dataset(dataset_str)
        dedup_report = self.deduplicator.analyze(dataset_str)
        
        # Collect issues
        issues: list[str] = []
        issues.extend(health_snapshot.alerts)
        
        if not quality_report.gate_passed:
            issues.append(f"Quality gate failed (score: {quality_report.average_score:.1f})")
        
        if dedup_report.duplicate_ratio > 0.15:
            issues.append(f"High duplicate ratio ({dedup_report.duplicate_ratio:.1%})")
        
        if health_snapshot.provenance_ratio < 0.75:
            issues.append(f"Low provenance coverage ({health_snapshot.provenance_ratio:.1%})")
        
        if health_snapshot.safety_ratio < 0.8:
            issues.append(f"Low safety coverage ({health_snapshot.safety_ratio:.1%})")
        
        # Determine overall readiness
        overall_ready = (
            health_snapshot.is_healthy
            and quality_report.gate_passed
            and dedup_report.duplicate_ratio <= 0.30
            and health_snapshot.provenance_ratio >= 0.75
            and health_snapshot.safety_ratio >= 0.8
        )
        
        return DatasetStatus(
            dataset_path=dataset_str,
            timestamp=timestamp,
            record_count=health_snapshot.record_count,
            health_status=health_snapshot.overall_status,
            quality_score=health_snapshot.quality_score,
            quality_gate_passed=quality_report.gate_passed,
            duplicate_ratio=dedup_report.duplicate_ratio,
            provenance_coverage=health_snapshot.provenance_ratio,
            safety_coverage=health_snapshot.safety_ratio,
            overall_ready=overall_ready,
            issues=tuple(issues),
        )
    
    def get_directory_status(
        self,
        directory: str | Path,
        pattern: str = "*.jsonl",
    ) -> MultiDatasetStatus:
        """Get status for all datasets in directory"""
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        datasets = sorted(directory_path.glob(pattern))
        statuses: list[DatasetStatus] = []
        
        for dataset_path in datasets:
            try:
                status = self.get_status(dataset_path)
                statuses.append(status)
            except Exception:
                # Skip datasets that fail to process
                continue
        
        ready_count = sum(1 for s in statuses if s.overall_ready)
        
        return MultiDatasetStatus(
            directory=str(directory_path),
            timestamp=datetime.utcnow().isoformat(),
            total_datasets=len(statuses),
            ready_datasets=ready_count,
            datasets=tuple(statuses),
        )
    
    def write_status(
        self,
        status: DatasetStatus | MultiDatasetStatus,
        json_path: str | Path | None = None,
        markdown_path: str | Path | None = None,
    ) -> None:
        """Write status to files"""
        if json_path:
            json_file = Path(json_path)
            json_file.parent.mkdir(parents=True, exist_ok=True)
            json_file.write_text(status.to_json() + "\n", encoding="utf-8")
        
        if markdown_path and isinstance(status, MultiDatasetStatus):
            md_file = Path(markdown_path)
            md_file.parent.mkdir(parents=True, exist_ok=True)
            md_file.write_text(status.to_markdown() + "\n", encoding="utf-8")
