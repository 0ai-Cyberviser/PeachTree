"""
PeachTree Dataset Analytics Engine

Statistical analysis and insights for datasets including token distributions,
content length analysis, quality metrics, and trend detection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
from typing import Any
import json
import re


@dataclass
class ContentStatistics:
    """Content-level statistics"""
    total_records: int
    total_characters: int
    total_words: int
    total_tokens: int  # Approximation
    avg_length: float
    min_length: int
    max_length: int
    median_length: float
    length_distribution: dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "total_characters": self.total_characters,
            "total_words": self.total_words,
            "total_tokens": self.total_tokens,
            "avg_length": round(self.avg_length, 2),
            "min_length": self.min_length,
            "max_length": self.max_length,
            "median_length": round(self.median_length, 2),
            "length_distribution": self.length_distribution,
        }


@dataclass
class ProvenanceStatistics:
    """Provenance and source statistics"""
    total_repos: int
    total_files: int
    repo_distribution: dict[str, int] = field(default_factory=dict)
    file_type_distribution: dict[str, int] = field(default_factory=dict)
    top_repos: list[tuple[str, int]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_repos": self.total_repos,
            "total_files": self.total_files,
            "repo_distribution": self.repo_distribution,
            "file_type_distribution": self.file_type_distribution,
            "top_repos": self.top_repos,
        }


@dataclass
class QualityStatistics:
    """Quality-related statistics"""
    records_with_quality: int
    avg_quality_score: float
    quality_distribution: dict[str, int] = field(default_factory=dict)
    low_quality_count: int = 0
    medium_quality_count: int = 0
    high_quality_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "records_with_quality": self.records_with_quality,
            "avg_quality_score": round(self.avg_quality_score, 2),
            "quality_distribution": self.quality_distribution,
            "low_quality_count": self.low_quality_count,
            "medium_quality_count": self.medium_quality_count,
            "high_quality_count": self.high_quality_count,
        }


@dataclass
class DatasetAnalyticsReport:
    """Complete analytics report"""
    dataset_path: str
    content_stats: ContentStatistics
    provenance_stats: ProvenanceStatistics
    quality_stats: QualityStatistics | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        data = {
            "dataset_path": self.dataset_path,
            "content_statistics": self.content_stats.to_dict(),
            "provenance_statistics": self.provenance_stats.to_dict(),
            "metadata": self.metadata,
        }
        if self.quality_stats:
            data["quality_statistics"] = self.quality_stats.to_dict()
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown analytics report"""
        lines = [
            "# Dataset Analytics Report",
            "",
            f"**Dataset:** `{Path(self.dataset_path).name}`",
            "",
            "## Content Statistics",
            "",
            f"- **Total Records:** {self.content_stats.total_records:,}",
            f"- **Total Characters:** {self.content_stats.total_characters:,}",
            f"- **Total Words:** {self.content_stats.total_words:,}",
            f"- **Estimated Tokens:** {self.content_stats.total_tokens:,}",
            "",
            "### Length Metrics",
            "",
            f"- **Average Length:** {self.content_stats.avg_length:.1f} characters",
            f"- **Median Length:** {self.content_stats.median_length:.1f} characters",
            f"- **Min Length:** {self.content_stats.min_length:,} characters",
            f"- **Max Length:** {self.content_stats.max_length:,} characters",
            "",
        ]
        
        if self.content_stats.length_distribution:
            lines.extend([
                "### Length Distribution",
                "",
            ])
            for bucket, count in sorted(self.content_stats.length_distribution.items()):
                lines.append(f"- **{bucket}:** {count:,} records")
            lines.append("")
        
        lines.extend([
            "## Provenance Statistics",
            "",
            f"- **Unique Repositories:** {self.provenance_stats.total_repos}",
            f"- **Unique Files:** {self.provenance_stats.total_files}",
            "",
        ])
        
        if self.provenance_stats.top_repos:
            lines.extend([
                "### Top Repositories",
                "",
            ])
            for repo, count in self.provenance_stats.top_repos[:10]:
                lines.append(f"- **{repo}:** {count:,} records")
            lines.append("")
        
        if self.provenance_stats.file_type_distribution:
            lines.extend([
                "### File Type Distribution",
                "",
            ])
            for file_type, count in sorted(
                self.provenance_stats.file_type_distribution.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]:
                lines.append(f"- **{file_type}:** {count:,} files")
            lines.append("")
        
        if self.quality_stats:
            lines.extend([
                "## Quality Statistics",
                "",
                f"- **Records with Quality Scores:** {self.quality_stats.records_with_quality:,}",
                f"- **Average Quality Score:** {self.quality_stats.avg_quality_score:.1f}",
                "",
                "### Quality Distribution",
                "",
                f"- **High Quality (80-100):** {self.quality_stats.high_quality_count:,}",
                f"- **Medium Quality (60-79):** {self.quality_stats.medium_quality_count:,}",
                f"- **Low Quality (0-59):** {self.quality_stats.low_quality_count:,}",
                "",
            ])
        
        return "\n".join(lines)


class DatasetAnalyticsEngine:
    """Statistical analysis and insights for datasets"""
    
    def __init__(self):
        """Initialize analytics engine"""
        pass
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple heuristic: ~4 characters per token
        return len(text) // 4
    
    def _compute_median(self, values: list[int]) -> float:
        """Compute median from list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return float(sorted_values[n // 2])
    
    def _get_length_bucket(self, length: int) -> str:
        """Get length bucket label"""
        if length < 100:
            return "0-99"
        elif length < 500:
            return "100-499"
        elif length < 1000:
            return "500-999"
        elif length < 5000:
            return "1K-5K"
        elif length < 10000:
            return "5K-10K"
        else:
            return "10K+"
    
    def _get_quality_category(self, score: float) -> str:
        """Get quality category"""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium"
        else:
            return "low"
    
    def analyze(
        self,
        dataset_path: Path | str,
        compute_quality: bool = True,
    ) -> DatasetAnalyticsReport:
        """
        Analyze dataset and generate comprehensive analytics report
        
        Args:
            dataset_path: Path to dataset
            compute_quality: If True, compute quality statistics
        
        Returns:
            DatasetAnalyticsReport with full analysis
        """
        dataset_path = Path(dataset_path)
        
        # Content statistics
        lengths = []
        total_chars = 0
        total_words = 0
        total_tokens = 0
        length_buckets = Counter()
        
        # Provenance statistics
        repos = set()
        files = set()
        repo_counts = Counter()
        file_type_counts = Counter()
        
        # Quality statistics
        quality_scores = []
        quality_categories = Counter()
        
        record_count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                record_count += 1
                
                # Content analysis
                content = record.get("content", "")
                length = len(content)
                lengths.append(length)
                total_chars += length
                
                words = len(re.findall(r'\b\w+\b', content))
                total_words += words
                
                tokens = self._estimate_tokens(content)
                total_tokens += tokens
                
                bucket = self._get_length_bucket(length)
                length_buckets[bucket] += 1
                
                # Provenance analysis
                if "source_repo" in record:
                    repo = record["source_repo"]
                    repos.add(repo)
                    repo_counts[repo] += 1
                
                if "source_path" in record:
                    path = record["source_path"]
                    files.add(path)
                    
                    # Extract file extension
                    ext = Path(path).suffix or "no_extension"
                    file_type_counts[ext] += 1
                
                # Quality analysis
                if compute_quality and "quality_score" in record:
                    score = record["quality_score"]
                    quality_scores.append(score)
                    
                    category = self._get_quality_category(score)
                    quality_categories[category] += 1
        
        # Build content statistics
        content_stats = ContentStatistics(
            total_records=record_count,
            total_characters=total_chars,
            total_words=total_words,
            total_tokens=total_tokens,
            avg_length=total_chars / record_count if record_count > 0 else 0,
            min_length=min(lengths) if lengths else 0,
            max_length=max(lengths) if lengths else 0,
            median_length=self._compute_median(lengths),
            length_distribution=dict(length_buckets),
        )
        
        # Build provenance statistics
        provenance_stats = ProvenanceStatistics(
            total_repos=len(repos),
            total_files=len(files),
            repo_distribution=dict(repo_counts),
            file_type_distribution=dict(file_type_counts),
            top_repos=repo_counts.most_common(10),
        )
        
        # Build quality statistics
        quality_stats = None
        if compute_quality and quality_scores:
            quality_stats = QualityStatistics(
                records_with_quality=len(quality_scores),
                avg_quality_score=sum(quality_scores) / len(quality_scores),
                quality_distribution=dict(quality_categories),
                low_quality_count=quality_categories["low"],
                medium_quality_count=quality_categories["medium"],
                high_quality_count=quality_categories["high"],
            )
        
        return DatasetAnalyticsReport(
            dataset_path=str(dataset_path),
            content_stats=content_stats,
            provenance_stats=provenance_stats,
            quality_stats=quality_stats,
        )
    
    def compare_datasets(
        self,
        dataset1: Path | str,
        dataset2: Path | str,
    ) -> dict[str, Any]:
        """
        Compare analytics between two datasets
        
        Returns:
            Comparison report with side-by-side metrics
        """
        report1 = self.analyze(dataset1)
        report2 = self.analyze(dataset2)
        
        return {
            "dataset1": {
                "path": report1.dataset_path,
                "records": report1.content_stats.total_records,
                "avg_length": report1.content_stats.avg_length,
                "total_repos": report1.provenance_stats.total_repos,
            },
            "dataset2": {
                "path": report2.dataset_path,
                "records": report2.content_stats.total_records,
                "avg_length": report2.content_stats.avg_length,
                "total_repos": report2.provenance_stats.total_repos,
            },
            "comparison": {
                "record_delta": report2.content_stats.total_records - report1.content_stats.total_records,
                "avg_length_delta": report2.content_stats.avg_length - report1.content_stats.avg_length,
                "repo_delta": report2.provenance_stats.total_repos - report1.provenance_stats.total_repos,
            },
        }
    
    def find_outliers(
        self,
        dataset_path: Path | str,
        threshold: float = 3.0,
    ) -> list[dict[str, Any]]:
        """
        Find outlier records based on statistical analysis
        
        Args:
            dataset_path: Path to dataset
            threshold: Standard deviation threshold
        
        Returns:
            List of outlier records with metadata
        """
        # First pass: calculate mean and std dev
        lengths = []
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                content = record.get("content", "")
                lengths.append(len(content))
        
        if not lengths:
            return []
        
        mean_length = sum(lengths) / len(lengths)
        variance = sum((x - mean_length) ** 2 for x in lengths) / len(lengths)
        std_dev = variance ** 0.5
        
        # Second pass: find outliers
        outliers = []
        
        with open(dataset_path) as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                length = len(content)
                
                # Calculate z-score
                z_score = (length - mean_length) / std_dev if std_dev > 0 else 0
                
                if abs(z_score) > threshold:
                    outliers.append({
                        "record_id": record.get("id", f"record_{idx}"),
                        "length": length,
                        "z_score": round(z_score, 2),
                        "type": "too_long" if z_score > 0 else "too_short",
                    })
        
        return outliers
    
    def generate_summary_statistics(
        self,
        dataset_path: Path | str,
    ) -> dict[str, Any]:
        """
        Generate quick summary statistics
        
        Returns:
            Dictionary with key metrics
        """
        report = self.analyze(dataset_path, compute_quality=False)
        
        return {
            "total_records": report.content_stats.total_records,
            "total_tokens": report.content_stats.total_tokens,
            "avg_length": round(report.content_stats.avg_length, 1),
            "unique_repos": report.provenance_stats.total_repos,
            "unique_files": report.provenance_stats.total_files,
        }
