"""
PeachTree Quality Trend Analyzer

Track dataset quality metrics over time, identify trends, generate quality reports,
and provide insights into dataset quality evolution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
import json
import statistics

from peachtree.quality import DatasetQualityScorer


@dataclass(frozen=True)
class QualitySnapshot:
    """Single quality measurement at a point in time"""
    timestamp: str  # ISO 8601
    dataset_path: str
    overall_score: float
    record_count: int
    passed_count: int
    failed_count: int
    avg_length: float
    min_quality: float
    max_quality: float
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "dataset_path": self.dataset_path,
            "overall_score": self.overall_score,
            "record_count": self.record_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "avg_length": self.avg_length,
            "min_quality": self.min_quality,
            "max_quality": self.max_quality,
            "metadata": self.metadata,
        }


@dataclass
class QualityTrend:
    """Quality trend analysis over time"""
    dataset_name: str
    snapshots: list[QualitySnapshot] = field(default_factory=list)
    
    def add_snapshot(self, snapshot: QualitySnapshot) -> None:
        """Add a quality snapshot"""
        self.snapshots.append(snapshot)
    
    def get_latest(self) -> QualitySnapshot | None:
        """Get the most recent snapshot"""
        if not self.snapshots:
            return None
        return max(self.snapshots, key=lambda s: s.timestamp)
    
    def get_average_score(self) -> float:
        """Calculate average quality score across all snapshots"""
        if not self.snapshots:
            return 0.0
        return statistics.mean(s.overall_score for s in self.snapshots)
    
    def get_trend_direction(self) -> Literal["improving", "declining", "stable"]:
        """Determine overall trend direction"""
        if len(self.snapshots) < 2:
            return "stable"
        
        # Compare first half to second half
        mid = len(self.snapshots) // 2
        first_half_avg = statistics.mean(s.overall_score for s in self.snapshots[:mid])
        second_half_avg = statistics.mean(s.overall_score for s in self.snapshots[mid:])
        
        diff = second_half_avg - first_half_avg
        
        if diff > 2.0:
            return "improving"
        elif diff < -2.0:
            return "declining"
        else:
            return "stable"
    
    def get_volatility(self) -> float:
        """Calculate quality score volatility (standard deviation)"""
        if len(self.snapshots) < 2:
            return 0.0
        return statistics.stdev(s.overall_score for s in self.snapshots)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "snapshot_count": len(self.snapshots),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "average_score": self.get_average_score(),
            "trend_direction": self.get_trend_direction(),
            "volatility": self.get_volatility(),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate a markdown summary"""
        lines = [f"# Quality Trend: {self.dataset_name}", ""]
        
        if not self.snapshots:
            lines.append("No quality snapshots recorded.")
            return "\n".join(lines)
        
        latest = self.get_latest()
        avg_score = self.get_average_score()
        trend = self.get_trend_direction()
        volatility = self.get_volatility()
        
        # Trend emoji
        trend_emoji = {
            "improving": "📈",
            "declining": "📉",
            "stable": "➡️",
        }[trend]
        
        lines.extend([
            "## Current Status",
            "",
            f"- **Latest Score:** {latest.overall_score:.1f}",
            f"- **Average Score:** {avg_score:.1f}",
            f"- **Trend:** {trend_emoji} {trend.upper()}",
            f"- **Volatility:** {volatility:.2f}",
            f"- **Snapshots:** {len(self.snapshots)}",
            "",
            "## Recent Snapshots",
            "",
            "| Date | Score | Records | Passed | Trend |",
            "|------|-------|---------|--------|-------|",
        ])
        
        # Show last 10 snapshots
        recent = sorted(self.snapshots, key=lambda s: s.timestamp, reverse=True)[:10]
        
        for i, snapshot in enumerate(recent):
            date = snapshot.timestamp[:10]
            score = snapshot.overall_score
            records = snapshot.record_count
            passed = snapshot.passed_count
            
            # Trend indicator for this snapshot
            if i < len(recent) - 1:
                prev_score = recent[i + 1].overall_score
                if score > prev_score:
                    trend_icon = "⬆️"
                elif score < prev_score:
                    trend_icon = "⬇️"
                else:
                    trend_icon = "➡️"
            else:
                trend_icon = "—"
            
            lines.append(
                f"| {date} | {score:.1f} | {records} | {passed} | {trend_icon} |"
            )
        
        lines.extend(["", ""])
        
        return "\n".join(lines)


@dataclass
class TrendInsight:
    """Insight or recommendation from trend analysis"""
    severity: Literal["info", "warning", "critical"]
    category: Literal["quality", "volume", "stability", "performance"]
    title: str
    description: str
    recommendation: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
        }


@dataclass
class TrendAnalysisReport:
    """Complete trend analysis report"""
    dataset_name: str
    analysis_timestamp: str
    trend_direction: str
    average_score: float
    volatility: float
    snapshot_count: int
    insights: list[TrendInsight] = field(default_factory=list)
    
    def add_insight(self, insight: TrendInsight) -> None:
        """Add an insight to the report"""
        self.insights.append(insight)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "analysis_timestamp": self.analysis_timestamp,
            "trend_direction": self.trend_direction,
            "average_score": self.average_score,
            "volatility": self.volatility,
            "snapshot_count": self.snapshot_count,
            "insights": [i.to_dict() for i in self.insights],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        lines = [
            f"# Trend Analysis: {self.dataset_name}",
            "",
            f"**Analysis Date:** {self.analysis_timestamp[:10]}",
            "",
            "## Summary",
            "",
            f"- **Trend Direction:** {self.trend_direction.upper()}",
            f"- **Average Quality:** {self.average_score:.1f}",
            f"- **Volatility:** {self.volatility:.2f}",
            f"- **Data Points:** {self.snapshot_count}",
            "",
        ]
        
        if self.insights:
            lines.extend(["## Insights & Recommendations", ""])
            
            for insight in self.insights:
                severity_emoji = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "critical": "🚨",
                }[insight.severity]
                
                lines.extend([
                    f"### {severity_emoji} {insight.title}",
                    "",
                    f"**Category:** {insight.category.title()}",
                    f"**Severity:** {insight.severity.upper()}",
                    "",
                    insight.description,
                    "",
                ])
                
                if insight.recommendation:
                    lines.extend([
                        "**Recommendation:**",
                        "",
                        insight.recommendation,
                        "",
                    ])
        
        return "\n".join(lines)


class QualityTrendAnalyzer:
    """Analyze dataset quality trends over time"""
    
    def __init__(self, trend_dir: Path | str = ".peachtree/trends"):
        """
        Initialize trend analyzer
        
        Args:
            trend_dir: Directory to store trend data
        """
        self.trend_dir = Path(trend_dir)
        self.trend_dir.mkdir(parents=True, exist_ok=True)
        self.scorer = DatasetQualityScorer()
    
    def _get_trend_path(self, dataset_name: str) -> Path:
        """Get path to trend data file"""
        return self.trend_dir / f"{dataset_name}.trend.json"
    
    def _load_trend(self, dataset_name: str) -> QualityTrend:
        """Load trend data from disk"""
        trend_path = self._get_trend_path(dataset_name)
        
        if not trend_path.exists():
            return QualityTrend(dataset_name=dataset_name)
        
        data = json.loads(trend_path.read_text())
        trend = QualityTrend(dataset_name=dataset_name)
        
        for snapshot_data in data.get("snapshots", []):
            snapshot = QualitySnapshot(
                timestamp=snapshot_data["timestamp"],
                dataset_path=snapshot_data["dataset_path"],
                overall_score=snapshot_data["overall_score"],
                record_count=snapshot_data["record_count"],
                passed_count=snapshot_data["passed_count"],
                failed_count=snapshot_data["failed_count"],
                avg_length=snapshot_data["avg_length"],
                min_quality=snapshot_data["min_quality"],
                max_quality=snapshot_data["max_quality"],
                metadata=snapshot_data.get("metadata", {}),
            )
            trend.add_snapshot(snapshot)
        
        return trend
    
    def _save_trend(self, trend: QualityTrend) -> None:
        """Save trend data to disk"""
        trend_path = self._get_trend_path(trend.dataset_name)
        trend_path.write_text(trend.to_json())
    
    def record_snapshot(
        self,
        dataset_path: Path | str,
        metadata: dict[str, Any] | None = None,
    ) -> QualitySnapshot:
        """
        Record a quality snapshot for a dataset
        
        Args:
            dataset_path: Path to dataset file
            metadata: Optional metadata to attach to snapshot
        
        Returns:
            Created QualitySnapshot
        """
        dataset_path = Path(dataset_path)
        dataset_name = dataset_path.stem
        
        # Score the dataset
        report = self.scorer.score_dataset(dataset_path)
        
        # Calculate additional metrics
        record_lengths = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    record_lengths.append(len(line))
        
        avg_length = statistics.mean(record_lengths) if record_lengths else 0.0
        min_quality = report.min_score if hasattr(report, 'min_score') else 0.0
        max_quality = report.max_score if hasattr(report, 'max_score') else 100.0
        
        # Create snapshot
        snapshot = QualitySnapshot(
            timestamp=datetime.now().isoformat(),
            dataset_path=str(dataset_path),
            overall_score=report.overall_score,
            record_count=report.total_records,
            passed_count=report.passed,
            failed_count=report.failed,
            avg_length=avg_length,
            min_quality=min_quality,
            max_quality=max_quality,
            metadata=metadata or {},
        )
        
        # Load existing trend and add snapshot
        trend = self._load_trend(dataset_name)
        trend.add_snapshot(snapshot)
        self._save_trend(trend)
        
        return snapshot
    
    def get_trend(self, dataset_name: str) -> QualityTrend:
        """Get quality trend for a dataset"""
        return self._load_trend(dataset_name)
    
    def analyze_trend(
        self,
        dataset_name: str,
    ) -> TrendAnalysisReport:
        """
        Analyze quality trend and generate insights
        
        Args:
            dataset_name: Name of the dataset
        
        Returns:
            TrendAnalysisReport with insights and recommendations
        """
        trend = self._load_trend(dataset_name)
        
        report = TrendAnalysisReport(
            dataset_name=dataset_name,
            analysis_timestamp=datetime.now().isoformat(),
            trend_direction=trend.get_trend_direction(),
            average_score=trend.get_average_score(),
            volatility=trend.get_volatility(),
            snapshot_count=len(trend.snapshots),
        )
        
        # Generate insights
        
        # 1. Quality trend insight
        if trend.get_trend_direction() == "declining":
            report.add_insight(TrendInsight(
                severity="warning",
                category="quality",
                title="Quality Declining",
                description=f"Dataset quality has declined over the last {len(trend.snapshots)} snapshots.",
                recommendation="Review recent changes and consider running optimization workflow.",
            ))
        elif trend.get_trend_direction() == "improving":
            report.add_insight(TrendInsight(
                severity="info",
                category="quality",
                title="Quality Improving",
                description=f"Dataset quality is improving. Average score: {report.average_score:.1f}.",
            ))
        
        # 2. Volatility insight
        if report.volatility > 10.0:
            report.add_insight(TrendInsight(
                severity="warning",
                category="stability",
                title="High Quality Volatility",
                description=f"Quality scores vary significantly (σ={report.volatility:.2f}).",
                recommendation="Stabilize data ingestion and processing pipelines.",
            ))
        
        # 3. Low quality insight
        if report.average_score < 60.0:
            report.add_insight(TrendInsight(
                severity="critical",
                category="quality",
                title="Low Average Quality",
                description=f"Average quality score ({report.average_score:.1f}) is below recommended threshold (60.0).",
                recommendation="Run quality improvement workflow or review data sources.",
            ))
        
        # 4. Volume insight
        latest = trend.get_latest()
        if latest and len(trend.snapshots) >= 2:
            prev = sorted(trend.snapshots, key=lambda s: s.timestamp, reverse=True)[1]
            volume_change = ((latest.record_count - prev.record_count) / prev.record_count) * 100
            
            if abs(volume_change) > 20.0:
                report.add_insight(TrendInsight(
                    severity="info",
                    category="volume",
                    title=f"Volume {'Increase' if volume_change > 0 else 'Decrease'}: {abs(volume_change):.1f}%",
                    description=f"Record count changed from {prev.record_count} to {latest.record_count}.",
                ))
        
        # 5. Data freshness insight
        if len(trend.snapshots) == 1:
            report.add_insight(TrendInsight(
                severity="info",
                category="performance",
                title="First Snapshot Recorded",
                description="This is the first quality snapshot. Continue recording to establish trends.",
            ))
        
        return report
    
    def compare_periods(
        self,
        dataset_name: str,
        period1_start: str,
        period1_end: str,
        period2_start: str,
        period2_end: str,
    ) -> dict[str, Any]:
        """
        Compare quality between two time periods
        
        Args:
            dataset_name: Name of the dataset
            period1_start: Start timestamp for period 1
            period1_end: End timestamp for period 1
            period2_start: Start timestamp for period 2
            period2_end: End timestamp for period 2
        
        Returns:
            Dictionary with comparison results
        """
        trend = self._load_trend(dataset_name)
        
        # Filter snapshots for each period
        period1_snapshots = [
            s for s in trend.snapshots
            if period1_start <= s.timestamp <= period1_end
        ]
        period2_snapshots = [
            s for s in trend.snapshots
            if period2_start <= s.timestamp <= period2_end
        ]
        
        if not period1_snapshots or not period2_snapshots:
            return {
                "error": "Insufficient data for comparison",
                "period1_count": len(period1_snapshots),
                "period2_count": len(period2_snapshots),
            }
        
        period1_avg = statistics.mean(s.overall_score for s in period1_snapshots)
        period2_avg = statistics.mean(s.overall_score for s in period2_snapshots)
        
        return {
            "dataset_name": dataset_name,
            "period1": {
                "start": period1_start,
                "end": period1_end,
                "snapshots": len(period1_snapshots),
                "average_score": period1_avg,
            },
            "period2": {
                "start": period2_start,
                "end": period2_end,
                "snapshots": len(period2_snapshots),
                "average_score": period2_avg,
            },
            "score_change": period2_avg - period1_avg,
            "percent_change": ((period2_avg - period1_avg) / period1_avg) * 100,
        }
    
    def generate_report(
        self,
        dataset_name: str,
        output_path: Path | str | None = None,
    ) -> str:
        """
        Generate comprehensive trend report
        
        Args:
            dataset_name: Name of the dataset
            output_path: Optional path to write report
        
        Returns:
            Markdown report string
        """
        trend = self._load_trend(dataset_name)
        analysis = self.analyze_trend(dataset_name)
        
        # Combine trend summary and analysis
        report = trend.to_summary() + "\n" + analysis.to_markdown()
        
        if output_path:
            Path(output_path).write_text(report)
        
        return report
