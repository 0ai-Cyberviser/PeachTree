"""Dataset benchmarking for performance measurement and comparison."""

import gc
import json
import psutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class BenchmarkCategory(Enum):
    """Categories of benchmarks."""
    
    IO = "io"
    PROCESSING = "processing"
    MEMORY = "memory"
    QUALITY = "quality"
    TRANSFORMATION = "transformation"


class BenchmarkStatus(Enum):
    """Status of a benchmark."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    
    benchmark_id: str
    name: str
    category: BenchmarkCategory
    duration_seconds: float
    records_processed: int
    throughput_records_per_sec: float
    memory_used_mb: float
    cpu_percent: float
    status: BenchmarkStatus = BenchmarkStatus.COMPLETED
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "name": self.name,
            "category": self.category.value,
            "duration_seconds": self.duration_seconds,
            "records_processed": self.records_processed,
            "throughput_records_per_sec": self.throughput_records_per_sec,
            "memory_used_mb": self.memory_used_mb,
            "cpu_percent": self.cpu_percent,
            "status": self.status.value,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class BenchmarkComparison:
    """Comparison between two benchmark results."""
    
    baseline_id: str
    current_id: str
    duration_change_percent: float
    throughput_change_percent: float
    memory_change_percent: float
    is_regression: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_id": self.baseline_id,
            "current_id": self.current_id,
            "duration_change_percent": self.duration_change_percent,
            "throughput_change_percent": self.throughput_change_percent,
            "memory_change_percent": self.memory_change_percent,
            "is_regression": self.is_regression,
        }


class DatasetBenchmark:
    """Run performance benchmarks on datasets."""
    
    def __init__(self):
        """Initialize benchmark runner."""
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        mem_info = self.process.memory_info()
        return mem_info.rss / (1024 * 1024)
    
    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percent."""
        return self.process.cpu_percent(interval=0.1)
    
    def benchmark_read(
        self,
        dataset_path: Path,
        benchmark_id: Optional[str] = None,
    ) -> BenchmarkResult:
        """Benchmark dataset reading performance."""
        benchmark_id = benchmark_id or f"read_{int(time.time())}"
        
        gc.collect()
        start_memory = self._get_memory_usage_mb()
        start_time = time.time()
        
        record_count = 0
        
        try:
            with dataset_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            json.loads(line)
                            record_count += 1
                        except json.JSONDecodeError:
                            continue
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            cpu_percent = self._get_cpu_percent()
            
            duration = end_time - start_time
            throughput = record_count / duration if duration > 0 else 0
            memory_used = max(0, end_memory - start_memory)
            
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Read",
                category=BenchmarkCategory.IO,
                duration_seconds=duration,
                records_processed=record_count,
                throughput_records_per_sec=throughput,
                memory_used_mb=memory_used,
                cpu_percent=cpu_percent,
                status=BenchmarkStatus.COMPLETED,
            )
        
        except Exception as e:
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Read",
                category=BenchmarkCategory.IO,
                duration_seconds=0.0,
                records_processed=0,
                throughput_records_per_sec=0.0,
                memory_used_mb=0.0,
                cpu_percent=0.0,
                status=BenchmarkStatus.FAILED,
                error=str(e),
            )
        
        self.results.append(result)
        return result
    
    def benchmark_write(
        self,
        dataset_path: Path,
        output_path: Path,
        benchmark_id: Optional[str] = None,
    ) -> BenchmarkResult:
        """Benchmark dataset writing performance."""
        benchmark_id = benchmark_id or f"write_{int(time.time())}"
        
        # First read dataset
        records = []
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        gc.collect()
        start_memory = self._get_memory_usage_mb()
        start_time = time.time()
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with output_path.open("w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            cpu_percent = self._get_cpu_percent()
            
            duration = end_time - start_time
            throughput = len(records) / duration if duration > 0 else 0
            memory_used = max(0, end_memory - start_memory)
            
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Write",
                category=BenchmarkCategory.IO,
                duration_seconds=duration,
                records_processed=len(records),
                throughput_records_per_sec=throughput,
                memory_used_mb=memory_used,
                cpu_percent=cpu_percent,
                status=BenchmarkStatus.COMPLETED,
            )
        
        except Exception as e:
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Write",
                category=BenchmarkCategory.IO,
                duration_seconds=0.0,
                records_processed=0,
                throughput_records_per_sec=0.0,
                memory_used_mb=0.0,
                cpu_percent=0.0,
                status=BenchmarkStatus.FAILED,
                error=str(e),
            )
        
        self.results.append(result)
        return result
    
    def benchmark_transform(
        self,
        dataset_path: Path,
        transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        output_path: Path,
        benchmark_id: Optional[str] = None,
    ) -> BenchmarkResult:
        """Benchmark dataset transformation performance."""
        benchmark_id = benchmark_id or f"transform_{int(time.time())}"
        
        gc.collect()
        start_memory = self._get_memory_usage_mb()
        start_time = time.time()
        
        record_count = 0
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with dataset_path.open("r", encoding="utf-8") as in_f:
                with output_path.open("w", encoding="utf-8") as out_f:
                    for line in in_f:
                        if not line.strip():
                            continue
                        
                        try:
                            record = json.loads(line)
                            transformed = transform_fn(record)
                            out_f.write(json.dumps(transformed) + "\n")
                            record_count += 1
                        except (json.JSONDecodeError, Exception):
                            continue
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            cpu_percent = self._get_cpu_percent()
            
            duration = end_time - start_time
            throughput = record_count / duration if duration > 0 else 0
            memory_used = max(0, end_memory - start_memory)
            
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Transform",
                category=BenchmarkCategory.TRANSFORMATION,
                duration_seconds=duration,
                records_processed=record_count,
                throughput_records_per_sec=throughput,
                memory_used_mb=memory_used,
                cpu_percent=cpu_percent,
                status=BenchmarkStatus.COMPLETED,
            )
        
        except Exception as e:
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Transform",
                category=BenchmarkCategory.TRANSFORMATION,
                duration_seconds=0.0,
                records_processed=0,
                throughput_records_per_sec=0.0,
                memory_used_mb=0.0,
                cpu_percent=0.0,
                status=BenchmarkStatus.FAILED,
                error=str(e),
            )
        
        self.results.append(result)
        return result
    
    def benchmark_filter(
        self,
        dataset_path: Path,
        filter_fn: Callable[[Dict[str, Any]], bool],
        output_path: Path,
        benchmark_id: Optional[str] = None,
    ) -> BenchmarkResult:
        """Benchmark dataset filtering performance."""
        benchmark_id = benchmark_id or f"filter_{int(time.time())}"
        
        gc.collect()
        start_memory = self._get_memory_usage_mb()
        start_time = time.time()
        
        processed = 0
        output = 0
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with dataset_path.open("r", encoding="utf-8") as in_f:
                with output_path.open("w", encoding="utf-8") as out_f:
                    for line in in_f:
                        if not line.strip():
                            continue
                        
                        try:
                            record = json.loads(line)
                            processed += 1
                            
                            if filter_fn(record):
                                out_f.write(json.dumps(record) + "\n")
                                output += 1
                        except (json.JSONDecodeError, Exception):
                            continue
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            cpu_percent = self._get_cpu_percent()
            
            duration = end_time - start_time
            throughput = processed / duration if duration > 0 else 0
            memory_used = max(0, end_memory - start_memory)
            
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Filter",
                category=BenchmarkCategory.PROCESSING,
                duration_seconds=duration,
                records_processed=processed,
                throughput_records_per_sec=throughput,
                memory_used_mb=memory_used,
                cpu_percent=cpu_percent,
                status=BenchmarkStatus.COMPLETED,
                metadata={"records_output": output},
            )
        
        except Exception as e:
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name="Dataset Filter",
                category=BenchmarkCategory.PROCESSING,
                duration_seconds=0.0,
                records_processed=0,
                throughput_records_per_sec=0.0,
                memory_used_mb=0.0,
                cpu_percent=0.0,
                status=BenchmarkStatus.FAILED,
                error=str(e),
            )
        
        self.results.append(result)
        return result
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self.results
    
    def get_result(self, benchmark_id: str) -> Optional[BenchmarkResult]:
        """Get specific benchmark result."""
        for result in self.results:
            if result.benchmark_id == benchmark_id:
                return result
        return None
    
    def compare(
        self,
        baseline_id: str,
        current_id: str,
        regression_threshold: float = 0.1,
    ) -> BenchmarkComparison:
        """Compare two benchmark results."""
        baseline = self.get_result(baseline_id)
        current = self.get_result(current_id)
        
        if not baseline or not current:
            raise ValueError("Benchmark results not found")
        
        duration_change = (
            (current.duration_seconds - baseline.duration_seconds) / baseline.duration_seconds
            if baseline.duration_seconds > 0 else 0
        )
        
        throughput_change = (
            (current.throughput_records_per_sec - baseline.throughput_records_per_sec) / baseline.throughput_records_per_sec
            if baseline.throughput_records_per_sec > 0 else 0
        )
        
        memory_change = (
            (current.memory_used_mb - baseline.memory_used_mb) / baseline.memory_used_mb
            if baseline.memory_used_mb > 0 else 0
        )
        
        is_regression = (
            duration_change > regression_threshold or
            throughput_change < -regression_threshold or
            memory_change > regression_threshold
        )
        
        return BenchmarkComparison(
            baseline_id=baseline_id,
            current_id=current_id,
            duration_change_percent=duration_change * 100,
            throughput_change_percent=throughput_change * 100,
            memory_change_percent=memory_change * 100,
            is_regression=is_regression,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        if not self.results:
            return {
                "total_benchmarks": 0,
                "completed": 0,
                "failed": 0,
            }
        
        completed = [r for r in self.results if r.status == BenchmarkStatus.COMPLETED]
        
        avg_duration = sum(r.duration_seconds for r in completed) / len(completed) if completed else 0
        avg_throughput = sum(r.throughput_records_per_sec for r in completed) / len(completed) if completed else 0
        avg_memory = sum(r.memory_used_mb for r in completed) / len(completed) if completed else 0
        
        by_category = {}
        for result in self.results:
            category = result.category.value
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += 1
        
        return {
            "total_benchmarks": len(self.results),
            "completed": len([r for r in self.results if r.status == BenchmarkStatus.COMPLETED]),
            "failed": len([r for r in self.results if r.status == BenchmarkStatus.FAILED]),
            "avg_duration_seconds": avg_duration,
            "avg_throughput_records_per_sec": avg_throughput,
            "avg_memory_used_mb": avg_memory,
            "by_category": by_category,
        }
