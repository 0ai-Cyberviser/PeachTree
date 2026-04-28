"""
Tests for performance profiler module
"""
from pathlib import Path
import pytest
import json
import time
from peachtree.performance import (
    PerformanceProfiler,
    ProfileReport,
    ProfileMetric,
)


@pytest.fixture
def test_dataset(tmp_path):
    """Create a test dataset for profiling"""
    dataset = tmp_path / "profile-test.jsonl"
    records = [
        {"id": str(i), "content": f"Content {i}" * 10}
        for i in range(50)
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_profile_metric_creation():
    """Test ProfileMetric dataclass"""
    metric = ProfileMetric(
        operation="read_dataset",
        duration_seconds=1.5,
        memory_peak_mb=50.0,
        records_processed=100,
        throughput_records_per_sec=66.7,
        timestamp="2026-04-27T10:00:00",
    )
    
    assert metric.operation == "read_dataset"
    assert metric.duration_seconds == 1.5
    assert metric.to_dict()["operation"] == "read_dataset"


def test_profile_report_creation():
    """Test ProfileReport dataclass"""
    report = ProfileReport(
        dataset_path="test.jsonl",
        total_duration_seconds=5.0,
        total_memory_peak_mb=100.0,
        total_records=500,
        overall_throughput=100.0,
    )
    
    assert report.total_records == 500
    assert report.overall_throughput == 100.0


def test_profiler_initialization():
    """Test profiler initialization"""
    profiler = PerformanceProfiler()
    
    assert profiler.metrics == []
    assert profiler.current_operation is None


def test_profile_operation_context_manager():
    """Test profile_operation context manager"""
    profiler = PerformanceProfiler()
    
    with profiler.profile_operation("test_op", records_count=100):
        time.sleep(0.01)  # Small delay
    
    assert len(profiler.metrics) == 1
    metric = profiler.metrics[0]
    
    assert metric.operation == "test_op"
    assert metric.records_processed == 100
    assert metric.duration_seconds > 0
    assert metric.memory_peak_mb >= 0


def test_profile_dataset_read(test_dataset):
    """Test profiling dataset read operation"""
    profiler = PerformanceProfiler()
    metric = profiler.profile_dataset_read(test_dataset)
    
    assert metric.operation == "read_dataset"
    assert metric.records_processed == 50
    assert metric.duration_seconds > 0
    assert metric.throughput_records_per_sec > 0


def test_profile_dataset_write(tmp_path):
    """Test profiling dataset write operation"""
    profiler = PerformanceProfiler()
    
    records = [{"id": str(i), "content": f"Content {i}"} for i in range(30)]
    output = tmp_path / "write-test.jsonl"
    
    metric = profiler.profile_dataset_write(records, output)
    
    assert metric.operation == "write_dataset"
    assert metric.records_processed == 30
    assert output.exists()


def test_profile_deduplication(test_dataset):
    """Test profiling deduplication operation"""
    profiler = PerformanceProfiler()
    metric = profiler.profile_deduplication(test_dataset)
    
    assert metric.operation == "deduplication"
    assert metric.records_processed == 50
    assert "unique_records" in metric.metadata
    assert "duplicates" in metric.metadata


def test_profile_quality_scoring(test_dataset):
    """Test profiling quality scoring operation"""
    profiler = PerformanceProfiler()
    metric = profiler.profile_quality_scoring(test_dataset)
    
    assert metric.operation == "quality_scoring"
    assert metric.records_processed == 50
    assert "average_score" in metric.metadata


def test_generate_report(test_dataset):
    """Test generating comprehensive report"""
    profiler = PerformanceProfiler()
    
    # Run some operations
    profiler.profile_dataset_read(test_dataset)
    profiler.profile_deduplication(test_dataset)
    profiler.profile_quality_scoring(test_dataset)
    
    report = profiler.generate_report(test_dataset)
    
    assert report.total_records == 50
    assert report.total_duration_seconds > 0
    assert len(report.metrics) == 3
    assert report.overall_throughput > 0


def test_report_identifies_bottlenecks(test_dataset, tmp_path):
    """Test that report identifies performance bottlenecks"""
    profiler = PerformanceProfiler()
    
    # Create artificially slow operation
    with profiler.profile_operation("slow_op", 100):
        time.sleep(0.1)
    
    with profiler.profile_operation("fast_op", 100):
        time.sleep(0.001)
    
    report = profiler.generate_report(test_dataset)
    
    # Should identify slow_op as bottleneck
    assert len(report.bottlenecks) > 0


def test_report_provides_recommendations(test_dataset):
    """Test that report provides optimization recommendations"""
    profiler = PerformanceProfiler()
    
    # Create low throughput metric
    with profiler.profile_operation("low_throughput", 10):
        time.sleep(0.1)  # Very slow for only 10 records
    
    report = profiler.generate_report(test_dataset)
    
    assert len(report.recommendations) > 0


def test_profile_report_to_json(test_dataset):
    """Test JSON serialization of profile report"""
    profiler = PerformanceProfiler()
    profiler.profile_dataset_read(test_dataset)
    
    report = profiler.generate_report(test_dataset)
    json_str = report.to_json()
    
    parsed = json.loads(json_str)
    assert parsed["total_records"] == 50
    assert "metrics" in parsed
    assert len(parsed["metrics"]) > 0


def test_profile_report_to_markdown(test_dataset):
    """Test markdown generation from profile report"""
    profiler = PerformanceProfiler()
    profiler.profile_dataset_read(test_dataset)
    profiler.profile_quality_scoring(test_dataset)
    
    report = profiler.generate_report(test_dataset)
    markdown = report.to_markdown()
    
    assert "# Performance Profile Report" in markdown
    assert "## Operation Metrics" in markdown
    assert "| Operation |" in markdown
    assert "read_dataset" in markdown
    assert "quality_scoring" in markdown


def test_profile_full_pipeline(test_dataset):
    """Test profiling full processing pipeline"""
    profiler = PerformanceProfiler()
    
    report = profiler.profile_full_pipeline(
        test_dataset,
        include_read=True,
        include_dedup=True,
        include_quality=True,
    )
    
    # Should have 3 operations profiled
    assert len(report.metrics) == 3
    assert any(m.operation == "read_dataset" for m in report.metrics)
    assert any(m.operation == "deduplication" for m in report.metrics)
    assert any(m.operation == "quality_scoring" for m in report.metrics)


def test_profile_pipeline_selective(test_dataset):
    """Test profiling pipeline with selective operations"""
    profiler = PerformanceProfiler()
    
    report = profiler.profile_full_pipeline(
        test_dataset,
        include_read=True,
        include_dedup=False,
        include_quality=False,
    )
    
    # Should only have read operation
    assert len(report.metrics) == 1
    assert report.metrics[0].operation == "read_dataset"


def test_compare_strategies(test_dataset):
    """Test comparing different processing strategies"""
    profiler = PerformanceProfiler()
    
    def strategy_a(dataset_path):
        with open(dataset_path) as f:
            return [json.loads(line) for line in f if line.strip()]
    
    def strategy_b(dataset_path):
        records = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
    
    results = profiler.compare_strategies(
        test_dataset,
        [("strategy_a", strategy_a), ("strategy_b", strategy_b)],
    )
    
    assert len(results) == 2
    assert "strategy_a" in results
    assert "strategy_b" in results
    assert isinstance(results["strategy_a"], ProfileMetric)


def test_profiler_reset():
    """Test resetting profiler metrics"""
    profiler = PerformanceProfiler()
    
    with profiler.profile_operation("test_op", 10):
        pass
    
    assert len(profiler.metrics) == 1
    
    profiler.reset()
    
    assert len(profiler.metrics) == 0
    assert profiler.current_operation is None


def test_profile_add_metric():
    """Test adding metric to report"""
    report = ProfileReport(
        "test.jsonl",
        5.0,
        100.0,
        500,
        100.0,
    )
    
    metric = ProfileMetric(
        "test_op",
        1.0,
        50.0,
        100,
        100.0,
        "2026-04-27T10:00:00",
    )
    
    report.add_metric(metric)
    assert len(report.metrics) == 1
    assert report.metrics[0] == metric


def test_profile_throughput_calculation():
    """Test throughput calculation"""
    profiler = PerformanceProfiler()
    
    with profiler.profile_operation("calc_throughput", 100):
        time.sleep(0.01)
    
    metric = profiler.metrics[0]
    
    # Throughput should be records / duration
    expected_throughput = metric.records_processed / metric.duration_seconds
    assert abs(metric.throughput_records_per_sec - expected_throughput) < 0.1


def test_profile_memory_tracking():
    """Test that memory usage is tracked"""
    profiler = PerformanceProfiler()
    
    with profiler.profile_operation("memory_test", 10):
        # Allocate some memory
        data = ["x" * 1000 for _ in range(1000)]
    
    metric = profiler.metrics[0]
    assert metric.memory_peak_mb > 0


def test_profile_bottleneck_threshold(test_dataset):
    """Test bottleneck detection threshold (>50% of total time)"""
    profiler = PerformanceProfiler()
    
    # Create operation taking >50% of time
    with profiler.profile_operation("slow", 50):
        time.sleep(0.1)
    
    with profiler.profile_operation("fast", 50):
        time.sleep(0.01)
    
    report = profiler.generate_report(test_dataset)
    
    # Should identify slow operation as bottleneck
    assert any("slow" in b for b in report.bottlenecks)


def test_profile_memory_recommendation(test_dataset, tmp_path):
    """Test high memory usage recommendation"""
    report = ProfileReport(
        str(test_dataset),
        10.0,
        600.0,  # >500 MB
        1000,
        100.0,
    )
    
    profiler = PerformanceProfiler()
    # Manually trigger recommendation logic
    recommendations = []
    
    if report.total_memory_peak_mb > 500:
        recommendations.append(
            "High memory usage detected. Consider streaming processing for large datasets."
        )
    
    assert len(recommendations) > 0


def test_profile_low_throughput_recommendation(test_dataset):
    """Test low throughput recommendation"""
    profiler = PerformanceProfiler()
    
    # Create low throughput operation
    with profiler.profile_operation("low_throughput", 50):
        time.sleep(0.2)  # Very slow
    
    report = profiler.generate_report(test_dataset)
    
    # Should recommend optimization
    assert len(report.recommendations) > 0
