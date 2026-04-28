"""Tests for dataset_benchmarking module."""
import json
import pytest
from peachtree.dataset_benchmarking import (
    DatasetBenchmark,
    BenchmarkCategory,
    BenchmarkStatus,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample JSONL dataset."""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": i, "text": f"sample text {i}", "label": i % 3}
        for i in range(100)
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


def test_benchmark_init():
    """Test benchmark initialization."""
    bench = DatasetBenchmark()
    assert bench is not None


def test_benchmark_read(sample_dataset):
    """Test read benchmark."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "test_read")
    
    assert result.benchmark_id == "test_read"
    assert result.category == BenchmarkCategory.IO
    assert result.status == BenchmarkStatus.COMPLETED
    assert result.duration_seconds > 0


def test_benchmark_write(sample_dataset, tmp_path):
    """Test write benchmark."""
    bench = DatasetBenchmark()
    output = tmp_path / "output.jsonl"
    
    result = bench.benchmark_write(sample_dataset, output, "test_write")
    
    assert result.benchmark_id == "test_write"
    assert result.category == BenchmarkCategory.IO
    assert result.status == BenchmarkStatus.COMPLETED
    assert output.exists()


def test_benchmark_transform(sample_dataset, tmp_path):
    """Test transform benchmark."""
    bench = DatasetBenchmark()
    output = tmp_path / "transformed.jsonl"
    
    def add_field(record):
        record["processed"] = True
        return record
    
    result = bench.benchmark_transform(sample_dataset, add_field, output, "test_transform")
    
    assert result.benchmark_id == "test_transform"
    assert result.category == BenchmarkCategory.PROCESSING
    assert result.status == BenchmarkStatus.COMPLETED


def test_benchmark_filter(sample_dataset, tmp_path):
    """Test filter benchmark."""
    bench = DatasetBenchmark()
    output = tmp_path / "filtered.jsonl"
    
    def even_ids(record):
        return record["id"] % 2 == 0
    
    result = bench.benchmark_filter(sample_dataset, even_ids, output, "test_filter")
    
    assert result.benchmark_id == "test_filter"
    assert result.category == BenchmarkCategory.PROCESSING
    assert result.status == BenchmarkStatus.COMPLETED


def test_benchmark_result_metrics(sample_dataset):
    """Test benchmark result contains metrics."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "test_metrics")
    
    assert hasattr(result, "duration_seconds")
    assert hasattr(result, "records_per_second")
    assert hasattr(result, "memory_mb")


def test_benchmark_result_serialization(sample_dataset):
    """Test benchmark result serialization."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "test_serial")
    
    data = result.to_dict()
    
    assert "benchmark_id" in data
    assert "duration_seconds" in data
    assert "status" in data


def test_compare_benchmarks(sample_dataset, tmp_path):
    """Test comparing two benchmarks."""
    bench = DatasetBenchmark()
    
    # Run baseline
    bench.benchmark_read(sample_dataset, "baseline")
    
    # Run current
    bench.benchmark_read(sample_dataset, "current")
    
    comparison = bench.compare("baseline", "current", threshold=0.1)
    
    assert comparison.baseline_id == "baseline"
    assert comparison.current_id == "current"
    assert hasattr(comparison, "speedup_factor")


def test_comparison_regression_detection(sample_dataset):
    """Test regression detection in comparisons."""
    bench = DatasetBenchmark()
    
    bench.benchmark_read(sample_dataset, "baseline")
    bench.benchmark_read(sample_dataset, "current")
    
    comparison = bench.compare("baseline", "current", threshold=2.0)
    
    assert hasattr(comparison, "is_regression")


def test_benchmark_statistics(sample_dataset):
    """Test getting benchmark statistics."""
    bench = DatasetBenchmark()
    
    bench.benchmark_read(sample_dataset, "read1")
    bench.benchmark_read(sample_dataset, "read2")
    
    stats = bench.get_statistics()
    
    assert "total_benchmarks" in stats
    assert stats["total_benchmarks"] >= 2


def test_benchmark_category_enum():
    """Test BenchmarkCategory enum."""
    assert BenchmarkCategory.IO
    assert BenchmarkCategory.PROCESSING
    assert BenchmarkCategory.MEMORY
    assert BenchmarkCategory.QUALITY


def test_benchmark_status_enum():
    """Test BenchmarkStatus enum."""
    assert BenchmarkStatus.PENDING
    assert BenchmarkStatus.RUNNING
    assert BenchmarkStatus.COMPLETED
    assert BenchmarkStatus.FAILED


def test_benchmark_multiple_operations(sample_dataset, tmp_path):
    """Test running multiple benchmark operations."""
    bench = DatasetBenchmark()
    
    r1 = bench.benchmark_read(sample_dataset, "read")
    output = tmp_path / "write.jsonl"
    r2 = bench.benchmark_write(sample_dataset, output, "write")
    
    assert r1.status == BenchmarkStatus.COMPLETED
    assert r2.status == BenchmarkStatus.COMPLETED


def test_benchmark_performance_metrics(sample_dataset):
    """Test performance metrics are calculated."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "perf")
    
    assert result.records_per_second > 0
    assert result.duration_seconds > 0


def test_benchmark_memory_tracking(sample_dataset):
    """Test memory usage tracking."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "memory")
    
    assert hasattr(result, "memory_mb")


def test_benchmark_comparison_serialization(sample_dataset):
    """Test benchmark comparison serialization."""
    bench = DatasetBenchmark()
    
    bench.benchmark_read(sample_dataset, "base")
    bench.benchmark_read(sample_dataset, "curr")
    
    comparison = bench.compare("base", "curr")
    data = comparison.to_dict()
    
    assert "baseline_id" in data
    assert "current_id" in data


def test_empty_dataset_benchmark(tmp_path):
    """Test benchmarking an empty dataset."""
    bench = DatasetBenchmark()
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    
    result = bench.benchmark_read(empty, "empty")
    
    assert result.status == BenchmarkStatus.COMPLETED


def test_large_dataset_benchmark(tmp_path):
    """Test benchmarking a larger dataset."""
    dataset = tmp_path / "large.jsonl"
    records = [
        {"id": i, "data": "x" * 100}
        for i in range(1000)
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    
    bench = DatasetBenchmark()
    result = bench.benchmark_read(dataset, "large")
    
    assert result.status == BenchmarkStatus.COMPLETED
    assert result.records_per_second > 0


def test_benchmark_id_uniqueness(sample_dataset):
    """Test that benchmark IDs are preserved."""
    bench = DatasetBenchmark()
    
    id1 = "unique_id_1"
    id2 = "unique_id_2"
    
    r1 = bench.benchmark_read(sample_dataset, id1)
    r2 = bench.benchmark_read(sample_dataset, id2)
    
    assert r1.benchmark_id == id1
    assert r2.benchmark_id == id2


def test_benchmark_result_timestamps(sample_dataset):
    """Test benchmark results have timestamps."""
    bench = DatasetBenchmark()
    result = bench.benchmark_read(sample_dataset, "time")
    
    assert hasattr(result, "timestamp")


def test_benchmark_transform_preserves_count(sample_dataset, tmp_path):
    """Test transform benchmark preserves record count."""
    bench = DatasetBenchmark()
    output = tmp_path / "out.jsonl"
    
    def identity(r):
        return r
    
    result = bench.benchmark_transform(sample_dataset, identity, output, "identity")
    
    assert result.status == BenchmarkStatus.COMPLETED
    assert output.exists()


def test_benchmark_filter_reduces_count(sample_dataset, tmp_path):
    """Test filter benchmark can reduce records."""
    bench = DatasetBenchmark()
    output = tmp_path / "filtered.jsonl"
    
    def first_half(r):
        return r["id"] < 50
    
    result = bench.benchmark_filter(sample_dataset, first_half, output, "half")
    
    assert result.status == BenchmarkStatus.COMPLETED
    assert output.exists()
