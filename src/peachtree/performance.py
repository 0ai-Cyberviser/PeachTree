"""
PeachTree Performance Profiler

Analyze and optimize dataset processing performance. Track execution time,
memory usage, and identify bottlenecks in dataset operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import json
import time
import tracemalloc
from contextlib import contextmanager


@dataclass
class ProfileMetric:
    """Single profiling metric"""
    operation: str
    duration_seconds: float
    memory_peak_mb: float
    records_processed: int
    throughput_records_per_sec: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "duration_seconds": self.duration_seconds,
            "memory_peak_mb": self.memory_peak_mb,
            "records_processed": self.records_processed,
            "throughput_records_per_sec": self.throughput_records_per_sec,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ProfileReport:
    """Complete performance profile report"""
    dataset_path: str
    total_duration_seconds: float
    total_memory_peak_mb: float
    total_records: int
    overall_throughput: float
    metrics: list[ProfileMetric] = field(default_factory=list)
    bottlenecks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    profile_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_metric(self, metric: ProfileMetric) -> None:
        """Add a profiling metric"""
        self.metrics.append(metric)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "total_duration_seconds": self.total_duration_seconds,
            "total_memory_peak_mb": self.total_memory_peak_mb,
            "total_records": self.total_records,
            "overall_throughput": self.overall_throughput,
            "metrics": [m.to_dict() for m in self.metrics],
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations,
            "profile_timestamp": self.profile_timestamp,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown performance report"""
        lines = [
            "# Performance Profile Report",
            "",
            f"**Dataset:** {self.dataset_path}",
            f"**Total Duration:** {self.total_duration_seconds:.2f}s",
            f"**Peak Memory:** {self.total_memory_peak_mb:.1f} MB",
            f"**Total Records:** {self.total_records:,}",
            f"**Throughput:** {self.overall_throughput:.1f} records/sec",
            f"**Timestamp:** {self.profile_timestamp}",
            "",
            "## Operation Metrics",
            "",
            "| Operation | Duration | Memory (MB) | Records | Throughput |",
            "|-----------|----------|-------------|---------|------------|",
        ]
        
        for metric in self.metrics:
            lines.append(
                f"| {metric.operation} | {metric.duration_seconds:.2f}s | "
                f"{metric.memory_peak_mb:.1f} | {metric.records_processed:,} | "
                f"{metric.throughput_records_per_sec:.1f}/s |"
            )
        
        lines.extend(["", ""])
        
        if self.bottlenecks:
            lines.extend(["## ⚠️ Bottlenecks Identified", ""])
            for bottleneck in self.bottlenecks:
                lines.append(f"- {bottleneck}")
            lines.append("")
        
        if self.recommendations:
            lines.extend(["## 💡 Recommendations", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)


class PerformanceProfiler:
    """Profile dataset processing performance"""
    
    def __init__(self):
        """Initialize performance profiler"""
        self.metrics: list[ProfileMetric] = []
        self.current_operation: str | None = None
        self.start_time: float = 0.0
        self.start_memory: int = 0
    
    @contextmanager
    def profile_operation(self, operation: str, records_count: int = 0):
        """
        Context manager for profiling an operation
        
        Args:
            operation: Operation name
            records_count: Number of records being processed
        
        Yields:
            None
        """
        # Start profiling
        tracemalloc.start()
        start_time = time.time()
        
        try:
            yield
        finally:
            # End profiling
            duration = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            throughput = records_count / duration if duration > 0 else 0.0
            
            metric = ProfileMetric(
                operation=operation,
                duration_seconds=duration,
                memory_peak_mb=peak / (1024 * 1024),
                records_processed=records_count,
                throughput_records_per_sec=throughput,
                timestamp=datetime.now().isoformat(),
            )
            
            self.metrics.append(metric)
    
    def profile_dataset_read(
        self,
        dataset_path: Path | str,
    ) -> ProfileMetric:
        """
        Profile dataset reading performance
        
        Args:
            dataset_path: Dataset path to profile
        
        Returns:
            ProfileMetric with read performance
        """
        dataset_path = Path(dataset_path)
        
        with self.profile_operation("read_dataset") as _:
            records = []
            with open(dataset_path) as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            
            # Update records count in last metric
            if self.metrics:
                self.metrics[-1] = ProfileMetric(
                    operation="read_dataset",
                    duration_seconds=self.metrics[-1].duration_seconds,
                    memory_peak_mb=self.metrics[-1].memory_peak_mb,
                    records_processed=len(records),
                    throughput_records_per_sec=len(records) / self.metrics[-1].duration_seconds if self.metrics[-1].duration_seconds > 0 else 0.0,
                    timestamp=self.metrics[-1].timestamp,
                )
        
        return self.metrics[-1]
    
    def profile_dataset_write(
        self,
        records: list[dict[str, Any]],
        output_path: Path | str,
    ) -> ProfileMetric:
        """
        Profile dataset writing performance
        
        Args:
            records: Records to write
            output_path: Output path
        
        Returns:
            ProfileMetric with write performance
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.profile_operation("write_dataset", len(records)):
            with open(output_path, 'w') as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")
        
        return self.metrics[-1]
    
    def profile_deduplication(
        self,
        dataset_path: Path | str,
    ) -> ProfileMetric:
        """
        Profile deduplication performance
        
        Args:
            dataset_path: Dataset path
        
        Returns:
            ProfileMetric with dedup performance
        """
        dataset_path = Path(dataset_path)
        
        with self.profile_operation("deduplication") as _:
            seen = set()
            unique_count = 0
            total_count = 0
            
            with open(dataset_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    total_count += 1
                    record = json.loads(line)
                    content = record.get("content", "")
                    
                    if content not in seen:
                        seen.add(content)
                        unique_count += 1
            
            # Update metric with accurate counts
            if self.metrics:
                self.metrics[-1] = ProfileMetric(
                    operation="deduplication",
                    duration_seconds=self.metrics[-1].duration_seconds,
                    memory_peak_mb=self.metrics[-1].memory_peak_mb,
                    records_processed=total_count,
                    throughput_records_per_sec=total_count / self.metrics[-1].duration_seconds if self.metrics[-1].duration_seconds > 0 else 0.0,
                    timestamp=self.metrics[-1].timestamp,
                    metadata={"unique_records": unique_count, "duplicates": total_count - unique_count},
                )
        
        return self.metrics[-1]
    
    def profile_quality_scoring(
        self,
        dataset_path: Path | str,
    ) -> ProfileMetric:
        """
        Profile quality scoring performance
        
        Args:
            dataset_path: Dataset path
        
        Returns:
            ProfileMetric with scoring performance
        """
        dataset_path = Path(dataset_path)
        
        with self.profile_operation("quality_scoring") as _:
            total_score = 0.0
            record_count = 0
            
            with open(dataset_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    record = json.loads(line)
                    # Simple quality scoring
                    score = 50.0
                    content = record.get("content", "")
                    if len(content) >= 100:
                        score += 30
                    if record.get("source_repo"):
                        score += 20
                    
                    total_score += score
                    record_count += 1
            
            avg_score = total_score / record_count if record_count > 0 else 0.0
            
            # Update metric
            if self.metrics:
                self.metrics[-1] = ProfileMetric(
                    operation="quality_scoring",
                    duration_seconds=self.metrics[-1].duration_seconds,
                    memory_peak_mb=self.metrics[-1].memory_peak_mb,
                    records_processed=record_count,
                    throughput_records_per_sec=record_count / self.metrics[-1].duration_seconds if self.metrics[-1].duration_seconds > 0 else 0.0,
                    timestamp=self.metrics[-1].timestamp,
                    metadata={"average_score": avg_score},
                )
        
        return self.metrics[-1]
    
    def generate_report(
        self,
        dataset_path: Path | str,
    ) -> ProfileReport:
        """
        Generate comprehensive performance report
        
        Args:
            dataset_path: Dataset path
        
        Returns:
            ProfileReport with full analysis
        """
        # Count total records
        total_records = sum(1 for line in open(dataset_path) if line.strip())
        
        # Calculate totals
        total_duration = sum(m.duration_seconds for m in self.metrics)
        total_memory = max((m.memory_peak_mb for m in self.metrics), default=0.0)
        overall_throughput = total_records / total_duration if total_duration > 0 else 0.0
        
        # Identify bottlenecks
        bottlenecks = []
        if self.metrics:
            slowest = max(self.metrics, key=lambda m: m.duration_seconds)
            if slowest.duration_seconds > total_duration * 0.5:
                bottlenecks.append(
                    f"{slowest.operation} takes {slowest.duration_seconds:.2f}s "
                    f"({slowest.duration_seconds / total_duration * 100:.1f}% of total time)"
                )
            
            memory_heavy = max(self.metrics, key=lambda m: m.memory_peak_mb)
            if memory_heavy.memory_peak_mb > 100:
                bottlenecks.append(
                    f"{memory_heavy.operation} uses {memory_heavy.memory_peak_mb:.1f} MB of memory"
                )
        
        # Generate recommendations
        recommendations = []
        
        if overall_throughput < 1000:
            recommendations.append(
                "Low throughput detected. Consider using batch processing or parallel operations."
            )
        
        if total_memory > 500:
            recommendations.append(
                "High memory usage detected. Consider streaming processing for large datasets."
            )
        
        for metric in self.metrics:
            if metric.throughput_records_per_sec < 500:
                recommendations.append(
                    f"Optimize {metric.operation} operation - current throughput is "
                    f"{metric.throughput_records_per_sec:.1f} records/sec"
                )
        
        # Create report
        report = ProfileReport(
            dataset_path=str(dataset_path),
            total_duration_seconds=total_duration,
            total_memory_peak_mb=total_memory,
            total_records=total_records,
            overall_throughput=overall_throughput,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )
        
        for metric in self.metrics:
            report.add_metric(metric)
        
        return report
    
    def profile_full_pipeline(
        self,
        dataset_path: Path | str,
        include_read: bool = True,
        include_dedup: bool = True,
        include_quality: bool = True,
    ) -> ProfileReport:
        """
        Profile a full dataset processing pipeline
        
        Args:
            dataset_path: Dataset path to profile
            include_read: Profile read operation
            include_dedup: Profile deduplication
            include_quality: Profile quality scoring
        
        Returns:
            ProfileReport with full pipeline analysis
        """
        dataset_path = Path(dataset_path)
        
        if include_read:
            self.profile_dataset_read(dataset_path)
        
        if include_dedup:
            self.profile_deduplication(dataset_path)
        
        if include_quality:
            self.profile_quality_scoring(dataset_path)
        
        return self.generate_report(dataset_path)
    
    def compare_strategies(
        self,
        dataset_path: Path | str,
        strategies: list[tuple[str, Callable]],
    ) -> dict[str, ProfileMetric]:
        """
        Compare performance of different processing strategies
        
        Args:
            dataset_path: Dataset path
            strategies: List of (name, function) tuples to compare
        
        Returns:
            Dict mapping strategy name to ProfileMetric
        """
        results: dict[str, ProfileMetric] = {}
        
        for name, func in strategies:
            with self.profile_operation(name):
                func(dataset_path)
            
            results[name] = self.metrics[-1]
        
        return results
    
    def reset(self) -> None:
        """Reset profiler metrics"""
        self.metrics = []
        self.current_operation = None
