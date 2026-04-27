"""
PeachTree Dataset Metrics Dashboard

Real-time metrics aggregation and health scoring for dataset monitoring.
Provides unified dashboard for quality, provenance, and operational metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json


@dataclass
class MetricValue:
    """Single metric value with timestamp"""
    name: str
    value: float
    unit: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }


@dataclass
class MetricCategory:
    """Category of related metrics"""
    category: str
    metrics: list[MetricValue] = field(default_factory=list)
    health_score: float = 100.0
    
    def add_metric(self, metric: MetricValue) -> None:
        """Add metric to category"""
        self.metrics.append(metric)
    
    def get_metric(self, name: str) -> MetricValue | None:
        """Get metric by name"""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "metrics": [m.to_dict() for m in self.metrics],
            "health_score": self.health_score,
            "metric_count": len(self.metrics),
        }


@dataclass
class DatasetDashboard:
    """Complete dataset metrics dashboard"""
    dataset_id: str
    timestamp: str
    categories: dict[str, MetricCategory] = field(default_factory=dict)
    overall_health: float = 100.0
    alerts: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def add_category(self, category: MetricCategory) -> None:
        """Add metric category to dashboard"""
        self.categories[category.category] = category
    
    def get_category(self, name: str) -> MetricCategory | None:
        """Get category by name"""
        return self.categories.get(name)
    
    def add_alert(self, alert: str) -> None:
        """Add alert to dashboard"""
        self.alerts.append(alert)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "timestamp": self.timestamp,
            "overall_health": self.overall_health,
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "alerts": self.alerts,
            "total_metrics": sum(len(c.metrics) for c in self.categories.values()),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown dashboard report"""
        lines = [
            f"# Dataset Metrics Dashboard",
            f"",
            f"**Dataset:** {self.dataset_id}  ",
            f"**Timestamp:** {self.timestamp}  ",
            f"**Overall Health:** {self.overall_health:.1f}/100  ",
            f"",
        ]
        
        # Alerts
        if self.alerts:
            lines.extend([
                "## 🚨 Alerts",
                "",
            ])
            for alert in self.alerts:
                lines.append(f"- ⚠️ {alert}")
            lines.append("")
        
        # Categories
        for category_name, category in self.categories.items():
            lines.extend([
                f"## {category_name.replace('_', ' ').title()}",
                f"",
                f"**Health Score:** {category.health_score:.1f}/100  ",
                f"",
                "| Metric | Value | Unit |",
                "|--------|-------|------|",
            ])
            
            for metric in category.metrics:
                unit = metric.unit if metric.unit else "-"
                lines.append(f"| {metric.name} | {metric.value} | {unit} |")
            
            lines.append("")
        
        return "\n".join(lines)


class DatasetMetricsDashboard:
    """Generate and manage dataset metrics dashboards"""
    
    def __init__(self):
        """Initialize metrics dashboard manager"""
        self.quality_thresholds = {
            "min_quality_score": 70.0,
            "min_records": 100,
            "max_duplicate_rate": 0.05,
            "min_metadata_coverage": 0.8,
        }
    
    def _collect_size_metrics(self, dataset_path: Path) -> MetricCategory:
        """Collect dataset size metrics"""
        category = MetricCategory(category="size")
        
        # Count records and size
        record_count = 0
        total_bytes = 0
        total_chars = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record_count += 1
                total_bytes += len(line.encode('utf-8'))
                
                try:
                    record = json.loads(line)
                    content = record.get("content", "")
                    total_chars += len(content)
                except json.JSONDecodeError:
                    continue
        
        # Add metrics
        category.add_metric(MetricValue("total_records", record_count, "records"))
        category.add_metric(MetricValue("total_bytes", total_bytes, "bytes"))
        category.add_metric(MetricValue("total_chars", total_chars, "characters"))
        category.add_metric(MetricValue("avg_record_size", total_bytes / record_count if record_count > 0 else 0, "bytes"))
        
        # Calculate health
        if record_count < self.quality_thresholds["min_records"]:
            category.health_score = 60.0
        
        return category
    
    def _collect_quality_metrics(self, dataset_path: Path) -> MetricCategory:
        """Collect quality metrics"""
        category = MetricCategory(category="quality")
        
        # Count quality levels
        total_records = 0
        quality_sum = 0.0
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_records += 1
                
                try:
                    record = json.loads(line)
                    quality_score = record.get("quality_score", 0.0)
                    quality_sum += quality_score
                    
                    if quality_score >= 80:
                        high_quality += 1
                    elif quality_score >= 50:
                        medium_quality += 1
                    else:
                        low_quality += 1
                
                except json.JSONDecodeError:
                    continue
        
        avg_quality = quality_sum / total_records if total_records > 0 else 0.0
        
        # Add metrics
        category.add_metric(MetricValue("avg_quality_score", avg_quality, "score"))
        category.add_metric(MetricValue("high_quality_count", high_quality, "records"))
        category.add_metric(MetricValue("medium_quality_count", medium_quality, "records"))
        category.add_metric(MetricValue("low_quality_count", low_quality, "records"))
        category.add_metric(MetricValue("high_quality_rate", high_quality / total_records * 100 if total_records > 0 else 0, "%"))
        
        # Calculate health
        category.health_score = min(100.0, avg_quality)
        
        return category
    
    def _collect_provenance_metrics(self, dataset_path: Path) -> MetricCategory:
        """Collect provenance metrics"""
        category = MetricCategory(category="provenance")
        
        # Track provenance coverage
        total_records = 0
        with_source = 0
        unique_repos: set[str] = set()
        unique_files: set[str] = set()
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_records += 1
                
                try:
                    record = json.loads(line)
                    
                    if "source_document" in record:
                        with_source += 1
                        source = record["source_document"]
                        
                        if "repo_id" in source:
                            unique_repos.add(source["repo_id"])
                        
                        if "source_path" in source:
                            unique_files.add(source["source_path"])
                
                except json.JSONDecodeError:
                    continue
        
        metadata_coverage = with_source / total_records if total_records > 0 else 0.0
        
        # Add metrics
        category.add_metric(MetricValue("metadata_coverage", metadata_coverage * 100, "%"))
        category.add_metric(MetricValue("unique_repos", len(unique_repos), "repos"))
        category.add_metric(MetricValue("unique_files", len(unique_files), "files"))
        category.add_metric(MetricValue("records_with_source", with_source, "records"))
        
        # Calculate health
        if metadata_coverage < self.quality_thresholds["min_metadata_coverage"]:
            category.health_score = 70.0
        
        return category
    
    def _collect_content_metrics(self, dataset_path: Path) -> MetricCategory:
        """Collect content metrics"""
        category = MetricCategory(category="content")
        
        # Content statistics
        total_records = 0
        total_words = 0
        total_tokens = 0
        empty_content = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_records += 1
                
                try:
                    record = json.loads(line)
                    content = record.get("content", "")
                    
                    if not content.strip():
                        empty_content += 1
                        continue
                    
                    words = len(content.split())
                    total_words += words
                    total_tokens += len(content) // 4  # Rough estimate
                
                except json.JSONDecodeError:
                    continue
        
        # Add metrics
        category.add_metric(MetricValue("avg_words_per_record", total_words / total_records if total_records > 0 else 0, "words"))
        category.add_metric(MetricValue("avg_tokens_per_record", total_tokens / total_records if total_records > 0 else 0, "tokens"))
        category.add_metric(MetricValue("empty_content_count", empty_content, "records"))
        category.add_metric(MetricValue("empty_content_rate", empty_content / total_records * 100 if total_records > 0 else 0, "%"))
        
        # Calculate health
        if empty_content > 0:
            category.health_score = 90.0
        
        return category
    
    def generate_dashboard(
        self,
        dataset_path: Path | str,
        dataset_id: str = "dataset",
    ) -> DatasetDashboard:
        """
        Generate comprehensive metrics dashboard
        
        Args:
            dataset_path: Path to dataset JSONL file
            dataset_id: Dataset identifier
        
        Returns:
            DatasetDashboard with all metrics
        """
        dataset_path = Path(dataset_path)
        dashboard = DatasetDashboard(
            dataset_id=dataset_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Collect all metric categories
        categories = [
            self._collect_size_metrics(dataset_path),
            self._collect_quality_metrics(dataset_path),
            self._collect_provenance_metrics(dataset_path),
            self._collect_content_metrics(dataset_path),
        ]
        
        for category in categories:
            dashboard.add_category(category)
        
        # Calculate overall health
        health_scores = [c.health_score for c in categories]
        dashboard.overall_health = sum(health_scores) / len(health_scores) if health_scores else 100.0
        
        # Generate alerts
        self._generate_alerts(dashboard)
        
        return dashboard
    
    def _generate_alerts(self, dashboard: DatasetDashboard) -> None:
        """Generate alerts based on metrics"""
        # Check size
        size_cat = dashboard.get_category("size")
        if size_cat:
            records_metric = size_cat.get_metric("total_records")
            if records_metric and records_metric.value < self.quality_thresholds["min_records"]:
                dashboard.add_alert(f"Low record count: {records_metric.value} < {self.quality_thresholds['min_records']}")
        
        # Check quality
        quality_cat = dashboard.get_category("quality")
        if quality_cat:
            avg_quality = quality_cat.get_metric("avg_quality_score")
            if avg_quality and avg_quality.value < self.quality_thresholds["min_quality_score"]:
                dashboard.add_alert(f"Low average quality: {avg_quality.value:.1f} < {self.quality_thresholds['min_quality_score']}")
        
        # Check provenance
        prov_cat = dashboard.get_category("provenance")
        if prov_cat:
            coverage = prov_cat.get_metric("metadata_coverage")
            if coverage and coverage.value < self.quality_thresholds["min_metadata_coverage"] * 100:
                dashboard.add_alert(f"Low metadata coverage: {coverage.value:.1f}% < {self.quality_thresholds['min_metadata_coverage'] * 100}%")
        
        # Check content
        content_cat = dashboard.get_category("content")
        if content_cat:
            empty_rate = content_cat.get_metric("empty_content_rate")
            if empty_rate and empty_rate.value > 0:
                dashboard.add_alert(f"Empty content detected: {empty_rate.value:.1f}% of records")
    
    def save_dashboard(
        self,
        dashboard: DatasetDashboard,
        output_path: Path | str,
        format: str = "json",
    ) -> None:
        """
        Save dashboard to file
        
        Args:
            dashboard: Dashboard to save
            output_path: Output file path
            format: Output format (json or markdown)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            content = dashboard.to_markdown()
        else:
            content = dashboard.to_json()
        
        output_path.write_text(content + "\n", encoding="utf-8")
    
    def compare_dashboards(
        self,
        dashboard1: DatasetDashboard,
        dashboard2: DatasetDashboard,
    ) -> dict[str, Any]:
        """
        Compare two dashboards and return differences
        
        Args:
            dashboard1: First dashboard (baseline)
            dashboard2: Second dashboard (current)
        
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "dataset1": dashboard1.dataset_id,
            "dataset2": dashboard2.dataset_id,
            "timestamp1": dashboard1.timestamp,
            "timestamp2": dashboard2.timestamp,
            "health_change": dashboard2.overall_health - dashboard1.overall_health,
            "category_changes": {},
        }
        
        # Compare each category
        for cat_name in dashboard1.categories:
            if cat_name in dashboard2.categories:
                cat1 = dashboard1.categories[cat_name]
                cat2 = dashboard2.categories[cat_name]
                
                comparison["category_changes"][cat_name] = {
                    "health_change": cat2.health_score - cat1.health_score,
                    "metric_changes": {},
                }
                
                # Compare metrics
                for metric1 in cat1.metrics:
                    metric2 = cat2.get_metric(metric1.name)
                    if metric2:
                        change = metric2.value - metric1.value
                        comparison["category_changes"][cat_name]["metric_changes"][metric1.name] = {
                            "value1": metric1.value,
                            "value2": metric2.value,
                            "change": change,
                            "change_percent": (change / metric1.value * 100) if metric1.value != 0 else 0,
                        }
        
        return comparison
