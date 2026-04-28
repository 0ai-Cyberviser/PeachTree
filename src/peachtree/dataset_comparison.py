"""
PeachTree Dataset Comparison

Compare datasets to track improvements, analyze differences, and benchmark quality.
Useful for before/after optimization analysis and dataset quality tracking.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from peachtree.quality import DatasetQualityScorer
from peachtree.dedup import DatasetDeduplicator
from peachtree.health_monitor import DatasetHealthMonitor


@dataclass(frozen=True)
class DatasetMetrics:
    """Metrics for a single dataset"""
    dataset_path: str
    record_count: int
    quality_score: float
    duplicate_ratio: float
    provenance_coverage: float
    safety_coverage: float
    total_size_bytes: int
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "record_count": self.record_count,
            "quality_score": self.quality_score,
            "duplicate_ratio": self.duplicate_ratio,
            "provenance_coverage": self.provenance_coverage,
            "safety_coverage": self.safety_coverage,
            "total_size_bytes": self.total_size_bytes,
        }


@dataclass(frozen=True)
class DatasetComparison:
    """Comparison results between two datasets"""
    baseline_path: str
    candidate_path: str
    timestamp: str
    baseline_metrics: DatasetMetrics
    candidate_metrics: DatasetMetrics
    record_count_delta: int
    quality_score_delta: float
    duplicate_ratio_delta: float
    provenance_delta: float
    safety_delta: float
    size_delta_bytes: int
    improvement_percentage: float
    
    @property
    def is_improvement(self) -> bool:
        """Check if candidate is an improvement over baseline"""
        return self.improvement_percentage > 0.0
    
    @property
    def is_significant_improvement(self) -> bool:
        """Check if improvement is significant (>10%)"""
        return self.improvement_percentage > 10.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_path": self.baseline_path,
            "candidate_path": self.candidate_path,
            "timestamp": self.timestamp,
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "candidate_metrics": self.candidate_metrics.to_dict(),
            "deltas": {
                "record_count": self.record_count_delta,
                "quality_score": self.quality_score_delta,
                "duplicate_ratio": self.duplicate_ratio_delta,
                "provenance_coverage": self.provenance_delta,
                "safety_coverage": self.safety_delta,
                "size_bytes": self.size_delta_bytes,
            },
            "improvement_percentage": self.improvement_percentage,
            "is_improvement": self.is_improvement,
            "is_significant_improvement": self.is_significant_improvement,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
    
    def to_markdown(self) -> str:
        improvement_emoji = "📈" if self.is_improvement else "📉"
        significance = "✨ SIGNIFICANT" if self.is_significant_improvement else ""
        
        lines = [
            f"# Dataset Comparison Report {improvement_emoji}",
            "",
            f"**Improvement:** {self.improvement_percentage:+.1f}% {significance}",
            f"**Generated:** {self.timestamp}",
            "",
            "## Datasets",
            "",
            f"- **Baseline:** `{Path(self.baseline_path).name}`",
            f"- **Candidate:** `{Path(self.candidate_path).name}`",
            "",
            "## Metrics Comparison",
            "",
            "| Metric | Baseline | Candidate | Delta | Change |",
            "|--------|----------|-----------|-------|--------|",
        ]
        
        # Record count
        rc_emoji = "📊"
        lines.append(
            f"| {rc_emoji} Records | {self.baseline_metrics.record_count:,} | "
            f"{self.candidate_metrics.record_count:,} | "
            f"{self.record_count_delta:+,} | "
            f"{self._percent_change(self.baseline_metrics.record_count, self.candidate_metrics.record_count):+.1f}% |"
        )
        
        # Quality score
        qual_emoji = "⭐" if self.quality_score_delta > 0 else "⚠️"
        lines.append(
            f"| {qual_emoji} Quality Score | {self.baseline_metrics.quality_score:.1f} | "
            f"{self.candidate_metrics.quality_score:.1f} | "
            f"{self.quality_score_delta:+.1f} | "
            f"{self._percent_change(self.baseline_metrics.quality_score, self.candidate_metrics.quality_score):+.1f}% |"
        )
        
        # Duplicate ratio
        dup_emoji = "✅" if self.duplicate_ratio_delta < 0 else "⚠️"
        lines.append(
            f"| {dup_emoji} Duplicate Ratio | {self.baseline_metrics.duplicate_ratio:.1%} | "
            f"{self.candidate_metrics.duplicate_ratio:.1%} | "
            f"{self.duplicate_ratio_delta:+.1%} | "
            f"{self._percent_change(self.baseline_metrics.duplicate_ratio, self.candidate_metrics.duplicate_ratio):+.1f}% |"
        )
        
        # Provenance
        prov_emoji = "📋" if self.provenance_delta > 0 else "⚠️"
        lines.append(
            f"| {prov_emoji} Provenance Coverage | {self.baseline_metrics.provenance_coverage:.1%} | "
            f"{self.candidate_metrics.provenance_coverage:.1%} | "
            f"{self.provenance_delta:+.1%} | "
            f"{self._percent_change(self.baseline_metrics.provenance_coverage, self.candidate_metrics.provenance_coverage):+.1f}% |"
        )
        
        # Safety
        safe_emoji = "🛡️" if self.safety_delta > 0 else "⚠️"
        lines.append(
            f"| {safe_emoji} Safety Coverage | {self.baseline_metrics.safety_coverage:.1%} | "
            f"{self.candidate_metrics.safety_coverage:.1%} | "
            f"{self.safety_delta:+.1%} | "
            f"{self._percent_change(self.baseline_metrics.safety_coverage, self.candidate_metrics.safety_coverage):+.1f}% |"
        )
        
        # Size
        size_emoji = "💾"
        lines.append(
            f"| {size_emoji} Size (bytes) | {self.baseline_metrics.total_size_bytes:,} | "
            f"{self.candidate_metrics.total_size_bytes:,} | "
            f"{self.size_delta_bytes:+,} | "
            f"{self._percent_change(self.baseline_metrics.total_size_bytes, self.candidate_metrics.total_size_bytes):+.1f}% |"
        )
        
        # Summary
        lines.extend([
            "",
            "## Summary",
            "",
        ])
        
        if self.is_significant_improvement:
            lines.append("✨ **SIGNIFICANT IMPROVEMENT** - Candidate dataset shows strong improvements!")
        elif self.is_improvement:
            lines.append("✅ **IMPROVEMENT** - Candidate dataset is better than baseline.")
        else:
            lines.append("⚠️ **NO IMPROVEMENT** - Candidate dataset is not better than baseline.")
        
        return "\n".join(lines)
    
    @staticmethod
    def _percent_change(baseline: float, candidate: float) -> float:
        """Calculate percentage change"""
        if baseline == 0:
            return 0.0 if candidate == 0 else 100.0
        return ((candidate - baseline) / baseline) * 100.0


class DatasetComparator:
    """Compare datasets to track improvements and analyze differences"""
    
    def __init__(self):
        self.health_monitor = DatasetHealthMonitor()
        self.quality_scorer = DatasetQualityScorer()
        self.deduplicator = DatasetDeduplicator()
    
    def collect_metrics(self, dataset_path: str | Path) -> DatasetMetrics:
        """Collect comprehensive metrics for a dataset"""
        dataset_str = str(dataset_path)
        path = Path(dataset_path)
        
        # Get health snapshot
        health = self.health_monitor.check_health(dataset_str)
        
        # Get file size
        file_size = path.stat().st_size if path.exists() else 0
        
        return DatasetMetrics(
            dataset_path=dataset_str,
            record_count=health.record_count,
            quality_score=health.quality_score,
            duplicate_ratio=health.duplicate_ratio,
            provenance_coverage=health.provenance_ratio,
            safety_coverage=health.safety_ratio,
            total_size_bytes=file_size,
        )
    
    def compare(
        self,
        baseline_path: str | Path,
        candidate_path: str | Path,
    ) -> DatasetComparison:
        """Compare two datasets and generate comparison report"""
        timestamp = datetime.utcnow().isoformat()
        
        # Collect metrics for both datasets
        baseline_metrics = self.collect_metrics(baseline_path)
        candidate_metrics = self.collect_metrics(candidate_path)
        
        # Calculate deltas
        record_delta = candidate_metrics.record_count - baseline_metrics.record_count
        quality_delta = candidate_metrics.quality_score - baseline_metrics.quality_score
        dup_delta = candidate_metrics.duplicate_ratio - baseline_metrics.duplicate_ratio
        prov_delta = candidate_metrics.provenance_coverage - baseline_metrics.provenance_coverage
        safety_delta = candidate_metrics.safety_coverage - baseline_metrics.safety_coverage
        size_delta = candidate_metrics.total_size_bytes - baseline_metrics.total_size_bytes
        
        # Calculate improvement percentage (weighted)
        # Quality: 40%, Duplicates: 20%, Provenance: 20%, Safety: 20%
        quality_improvement = quality_delta  # Already 0-100 scale
        dup_improvement = -dup_delta * 100  # Negative is good, scale to 0-100
        prov_improvement = prov_delta * 100  # 0-1 to 0-100
        safety_improvement = safety_delta * 100  # 0-1 to 0-100
        
        improvement_percentage = (
            quality_improvement * 0.4 +
            dup_improvement * 0.2 +
            prov_improvement * 0.2 +
            safety_improvement * 0.2
        )
        
        return DatasetComparison(
            baseline_path=str(baseline_path),
            candidate_path=str(candidate_path),
            timestamp=timestamp,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            record_count_delta=record_delta,
            quality_score_delta=quality_delta,
            duplicate_ratio_delta=dup_delta,
            provenance_delta=prov_delta,
            safety_delta=safety_delta,
            size_delta_bytes=size_delta,
            improvement_percentage=improvement_percentage,
        )
    
    def write_comparison(
        self,
        comparison: DatasetComparison,
        json_path: str | Path | None = None,
        markdown_path: str | Path | None = None,
    ) -> None:
        """Write comparison report to files"""
        if json_path:
            json_file = Path(json_path)
            json_file.parent.mkdir(parents=True, exist_ok=True)
            json_file.write_text(comparison.to_json() + "\n", encoding="utf-8")
        
        if markdown_path:
            md_file = Path(markdown_path)
            md_file.parent.mkdir(parents=True, exist_ok=True)
            md_file.write_text(comparison.to_markdown() + "\n", encoding="utf-8")
