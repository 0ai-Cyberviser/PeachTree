"""Dataset profiler for statistical analysis and data profiling.

This module provides comprehensive dataset profiling capabilities including:
- Statistical analysis (mean, median, std dev, percentiles)
- Content length and quality score distributions
- Metadata coverage analysis
- Outlier detection
- Data type profiling
- Profile report generation (JSON/Markdown)
"""

import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class NumericStats:
    """Statistical measures for numeric data."""
    
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    percentile_99: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "std_dev": self.std_dev,
            "min": self.min_value,
            "max": self.max_value,
            "p25": self.percentile_25,
            "p75": self.percentile_75,
            "p95": self.percentile_95,
            "p99": self.percentile_99,
        }


@dataclass
class DistributionStats:
    """Distribution statistics for categorical or text data."""
    
    unique_count: int
    top_values: List[Tuple[str, int]]
    distribution: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "unique_count": self.unique_count,
            "top_values": [{"value": v, "count": c} for v, c in self.top_values],
            "distribution_sample": dict(list(self.distribution.items())[:20]),
        }


@dataclass
class DatasetProfile:
    """Complete profile of a dataset."""
    
    dataset_id: str
    total_records: int
    timestamp: str
    
    # Content statistics
    content_length_stats: Optional[NumericStats] = None
    quality_score_stats: Optional[NumericStats] = None
    token_count_stats: Optional[NumericStats] = None
    
    # Metadata analysis
    metadata_coverage: Dict[str, float] = field(default_factory=dict)
    metadata_field_counts: Dict[str, int] = field(default_factory=dict)
    
    # Distributions
    category_distribution: Optional[DistributionStats] = None
    label_distribution: Optional[DistributionStats] = None
    
    # Data quality
    empty_content_count: int = 0
    duplicate_content_count: int = 0
    outliers: List[str] = field(default_factory=list)
    
    # Data types
    field_types: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "total_records": self.total_records,
            "timestamp": self.timestamp,
            "content_length_stats": self.content_length_stats.to_dict() if self.content_length_stats else None,
            "quality_score_stats": self.quality_score_stats.to_dict() if self.quality_score_stats else None,
            "token_count_stats": self.token_count_stats.to_dict() if self.token_count_stats else None,
            "metadata_coverage": self.metadata_coverage,
            "metadata_field_counts": self.metadata_field_counts,
            "category_distribution": self.category_distribution.to_dict() if self.category_distribution else None,
            "label_distribution": self.label_distribution.to_dict() if self.label_distribution else None,
            "empty_content_count": self.empty_content_count,
            "duplicate_content_count": self.duplicate_content_count,
            "outliers": self.outliers,
            "field_types": self.field_types,
        }
    
    def to_json(self) -> str:
        """Convert profile to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Convert profile to Markdown report."""
        lines = [
            f"# Dataset Profile: {self.dataset_id}",
            "",
            f"**Generated:** {self.timestamp}",
            f"**Total Records:** {self.total_records:,}",
            "",
            "## Content Statistics",
            "",
        ]
        
        if self.content_length_stats:
            lines.extend([
                "### Content Length",
                f"- Mean: {self.content_length_stats.mean:.2f} characters",
                f"- Median: {self.content_length_stats.median:.2f} characters",
                f"- Std Dev: {self.content_length_stats.std_dev:.2f}",
                f"- Range: {self.content_length_stats.min_value:.0f} - {self.content_length_stats.max_value:.0f}",
                f"- P95: {self.content_length_stats.percentile_95:.2f}",
                "",
            ])
        
        if self.quality_score_stats:
            lines.extend([
                "### Quality Scores",
                f"- Mean: {self.quality_score_stats.mean:.2f}",
                f"- Median: {self.quality_score_stats.median:.2f}",
                f"- Std Dev: {self.quality_score_stats.std_dev:.2f}",
                f"- Range: {self.quality_score_stats.min_value:.2f} - {self.quality_score_stats.max_value:.2f}",
                "",
            ])
        
        if self.token_count_stats:
            lines.extend([
                "### Token Counts",
                f"- Mean: {self.token_count_stats.mean:.2f} tokens",
                f"- Median: {self.token_count_stats.median:.2f} tokens",
                f"- P95: {self.token_count_stats.percentile_95:.2f} tokens",
                "",
            ])
        
        lines.extend([
            "## Data Quality",
            f"- Empty Content: {self.empty_content_count} ({self.empty_content_count / max(self.total_records, 1) * 100:.2f}%)",
            f"- Duplicates: {self.duplicate_content_count} ({self.duplicate_content_count / max(self.total_records, 1) * 100:.2f}%)",
            f"- Outliers: {len(self.outliers)}",
            "",
        ])
        
        if self.metadata_coverage:
            lines.extend([
                "## Metadata Coverage",
                "",
            ])
            for field, coverage in sorted(self.metadata_coverage.items()):
                lines.append(f"- {field}: {coverage * 100:.2f}%")
            lines.append("")
        
        if self.category_distribution:
            lines.extend([
                "## Category Distribution",
                f"- Unique Categories: {self.category_distribution.unique_count}",
                "",
                "Top Categories:",
            ])
            for value, count in self.category_distribution.top_values[:10]:
                pct = count / max(self.total_records, 1) * 100
                lines.append(f"- {value}: {count} ({pct:.2f}%)")
            lines.append("")
        
        return "\n".join(lines)


class DatasetProfiler:
    """Generate comprehensive dataset profiles."""
    
    def __init__(self) -> None:
        """Initialize the profiler."""
        pass
    
    def profile_dataset(
        self,
        dataset_path: Path,
        dataset_id: str = "dataset",
        compute_tokens: bool = False,
    ) -> DatasetProfile:
        """Generate a complete profile of a dataset.
        
        Args:
            dataset_path: Path to JSONL dataset file
            dataset_id: Dataset identifier
            compute_tokens: Whether to compute token counts (slower)
        
        Returns:
            DatasetProfile with comprehensive statistics
        """
        from datetime import datetime
        
        records = self._load_records(dataset_path)
        
        profile = DatasetProfile(
            dataset_id=dataset_id,
            total_records=len(records),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
        if not records:
            return profile
        
        # Analyze content lengths
        content_lengths = [len(r.get("content", "")) for r in records]
        if content_lengths:
            profile.content_length_stats = self._compute_numeric_stats(content_lengths)
        
        # Analyze quality scores
        quality_scores = [r.get("quality_score", 0.0) for r in records if "quality_score" in r]
        if quality_scores:
            profile.quality_score_stats = self._compute_numeric_stats(quality_scores)
        
        # Analyze token counts
        if compute_tokens:
            token_counts = [self._estimate_tokens(r.get("content", "")) for r in records]
            if token_counts:
                profile.token_count_stats = self._compute_numeric_stats(token_counts)
        
        # Metadata coverage
        profile.metadata_coverage = self._compute_metadata_coverage(records)
        profile.metadata_field_counts = self._count_metadata_fields(records)
        
        # Category and label distributions
        categories = [r.get("category", "") for r in records if r.get("category")]
        if categories:
            profile.category_distribution = self._compute_distribution(categories)
        
        labels = [r.get("label", "") for r in records if r.get("label")]
        if labels:
            profile.label_distribution = self._compute_distribution(labels)
        
        # Data quality checks
        profile.empty_content_count = sum(1 for r in records if not r.get("content", "").strip())
        profile.duplicate_content_count = self._count_duplicates(records)
        profile.outliers = self._detect_outliers(records, content_lengths)
        
        # Field types
        profile.field_types = self._infer_field_types(records)
        
        return profile
    
    def _load_records(self, dataset_path: Path) -> List[Dict[str, Any]]:
        """Load records from JSONL file."""
        records = []
        with open(dataset_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    
    def _compute_numeric_stats(self, values: List[float]) -> NumericStats:
        """Compute statistical measures for numeric data."""
        if not values:
            return NumericStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        sorted_values = sorted(values)
        
        return NumericStats(
            count=len(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            min_value=min(values),
            max_value=max(values),
            percentile_25=self._percentile(sorted_values, 25),
            percentile_75=self._percentile(sorted_values, 75),
            percentile_95=self._percentile(sorted_values, 95),
            percentile_99=self._percentile(sorted_values, 99),
        )
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not sorted_values:
            return 0.0
        
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_values):
            return sorted_values[f] + (sorted_values[f + 1] - sorted_values[f]) * c
        else:
            return sorted_values[f]
    
    def _compute_distribution(self, values: List[str]) -> DistributionStats:
        """Compute distribution statistics."""
        counter = Counter(values)
        
        return DistributionStats(
            unique_count=len(counter),
            top_values=counter.most_common(10),
            distribution=dict(counter),
        )
    
    def _compute_metadata_coverage(self, records: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute coverage percentage for metadata fields."""
        if not records:
            return {}
        
        field_counts: Dict[str, int] = defaultdict(int)
        total = len(records)
        
        for record in records:
            metadata = record.get("metadata", {})
            for field in metadata.keys():
                field_counts[field] += 1
        
        return {field: count / total for field, count in field_counts.items()}
    
    def _count_metadata_fields(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of metadata fields."""
        field_counts: Dict[str, int] = defaultdict(int)
        
        for record in records:
            metadata = record.get("metadata", {})
            for field in metadata.keys():
                field_counts[field] += 1
        
        return dict(field_counts)
    
    def _count_duplicates(self, records: List[Dict[str, Any]]) -> int:
        """Count duplicate content."""
        content_set = set()
        duplicates = 0
        
        for record in records:
            content = record.get("content", "")
            if content:
                if content in content_set:
                    duplicates += 1
                else:
                    content_set.add(content)
        
        return duplicates
    
    def _detect_outliers(
        self,
        records: List[Dict[str, Any]],
        content_lengths: List[int],
    ) -> List[str]:
        """Detect outlier records based on content length."""
        if len(content_lengths) < 4:
            return []
        
        sorted_lengths = sorted(content_lengths)
        q1 = self._percentile(sorted_lengths, 25)
        q3 = self._percentile(sorted_lengths, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        
        outliers = []
        for record, length in zip(records, content_lengths):
            if length < lower_bound or length > upper_bound:
                outliers.append(record.get("id", "unknown"))
        
        return outliers[:100]  # Limit to 100 outliers
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def _infer_field_types(self, records: List[Dict[str, Any]]) -> Dict[str, str]:
        """Infer data types for fields."""
        if not records:
            return {}
        
        field_types: Dict[str, str] = {}
        sample = records[0]
        
        for field, value in sample.items():
            if isinstance(value, bool):
                field_types[field] = "boolean"
            elif isinstance(value, int):
                field_types[field] = "integer"
            elif isinstance(value, float):
                field_types[field] = "float"
            elif isinstance(value, str):
                field_types[field] = "string"
            elif isinstance(value, dict):
                field_types[field] = "object"
            elif isinstance(value, list):
                field_types[field] = "array"
            else:
                field_types[field] = "unknown"
        
        return field_types
    
    def save_profile(self, profile: DatasetProfile, output_path: Path, format: str = "json") -> None:
        """Save profile to file.
        
        Args:
            profile: Dataset profile to save
            output_path: Output file path
            format: Output format ('json' or 'markdown')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            if format == "json":
                f.write(profile.to_json())
            elif format == "markdown":
                f.write(profile.to_markdown())
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def compare_profiles(
        self,
        profile1: DatasetProfile,
        profile2: DatasetProfile,
    ) -> Dict[str, Any]:
        """Compare two dataset profiles.
        
        Args:
            profile1: First profile
            profile2: Second profile
        
        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "dataset1_id": profile1.dataset_id,
            "dataset2_id": profile2.dataset_id,
            "record_count_diff": profile2.total_records - profile1.total_records,
            "record_count_pct_change": ((profile2.total_records - profile1.total_records) / max(profile1.total_records, 1)) * 100,
        }
        
        # Compare quality scores
        if profile1.quality_score_stats and profile2.quality_score_stats:
            comparison["quality_mean_diff"] = profile2.quality_score_stats.mean - profile1.quality_score_stats.mean
            comparison["quality_median_diff"] = profile2.quality_score_stats.median - profile1.quality_score_stats.median
        
        # Compare content lengths
        if profile1.content_length_stats and profile2.content_length_stats:
            comparison["length_mean_diff"] = profile2.content_length_stats.mean - profile1.content_length_stats.mean
            comparison["length_median_diff"] = profile2.content_length_stats.median - profile1.content_length_stats.median
        
        # Compare data quality
        comparison["empty_content_diff"] = profile2.empty_content_count - profile1.empty_content_count
        comparison["duplicate_diff"] = profile2.duplicate_content_count - profile1.duplicate_content_count
        
        return comparison
