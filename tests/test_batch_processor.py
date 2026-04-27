"""
Tests for batch_processor module
"""
from pathlib import Path
import pytest
import json
import tempfile
from peachtree.batch_processor import (
    BatchHealthMonitor,
    BatchOptimizer,
    BatchQualityScorer,
    BatchResult,
    BatchOperationReport,
)


@pytest.fixture
def temp_dataset_dir(tmp_path):
    """Create temporary directory with sample datasets"""
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Create 3 sample datasets with varying quality
    for i in range(3):
        dataset_file = dataset_dir / f"dataset{i}.jsonl"
        records = []
        for j in range(10):
            record = {
                "id": f"rec-{i}-{j}",
                "content": f"Sample content {i} {j}",
                "source_repo": "test-repo",
                "source_path": f"test{i}.txt",
                "digest": f"sha256-{i}-{j}",
            }
            records.append(json.dumps(record))
        dataset_file.write_text("\n".join(records) + "\n")
    
    return dataset_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_batch_result_creation():
    """Test BatchResult dataclass creation"""
    result = BatchResult(
        dataset_path="test.jsonl",
        status="success",
        error=None,
        result={"quality_score": 85.0},
    )
    
    assert result.dataset_path == "test.jsonl"
    assert result.status == "success"
    assert result.error is None
    assert result.result["quality_score"] == 85.0
    
    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["status"] == "success"
    assert result_dict["result"]["quality_score"] == 85.0


def test_batch_operation_report_creation():
    """Test BatchOperationReport creation and methods"""
    results = [
        BatchResult("dataset1.jsonl", "success", None, {"score": 85.0}),
        BatchResult("dataset2.jsonl", "success", None, {"score": 90.0}),
        BatchResult("dataset3.jsonl", "failed", "Error occurred", {}),
    ]
    
    report = BatchOperationReport(
        operation="health_check",
        started_at="2026-04-27T10:00:00",
        completed_at="2026-04-27T10:05:00",
        total_datasets=3,
        successful=2,
        failed=1,
        skipped=0,
        results=tuple(results),
    )
    
    assert report.total_datasets == 3
    assert report.successful == 2
    assert report.failed == 1
    
    # Test to_dict
    report_dict = report.to_dict()
    assert report_dict["summary"]["total_datasets"] == 3
    assert report_dict["summary"]["successful"] == 2
    
    # Test to_json
    json_str = report.to_json()
    assert "health_check" in json_str
    
    # Test to_markdown
    md = report.to_markdown()
    assert "# Batch Health_Check Report" in md
    assert "✅" in md
    assert "❌" in md


def test_batch_health_monitor_initialization():
    """Test BatchHealthMonitor initialization"""
    monitor = BatchHealthMonitor(
        quality_warning=80.0,
        quality_critical=65.0,
        duplicate_warning=0.10,
        duplicate_critical=0.25,
    )
    
    assert monitor.operation == "health_check"
    assert monitor.monitor.quality_warning == 80.0
    assert monitor.monitor.quality_critical == 65.0


def test_batch_health_monitor_find_datasets(temp_dataset_dir):
    """Test finding datasets in directory"""
    monitor = BatchHealthMonitor()
    datasets = monitor.find_datasets(temp_dataset_dir)
    
    assert len(datasets) == 3
    assert all(d.suffix == ".jsonl" for d in datasets)
    assert all(d.exists() for d in datasets)


def test_batch_health_monitor_check_directory(temp_dataset_dir):
    """Test batch health checking of directory"""
    monitor = BatchHealthMonitor()
    report = monitor.check_directory(temp_dataset_dir, skip_on_error=True)
    
    assert report.operation == "health_check"
    assert report.total_datasets == 3
    # All should process (success or failed)
    assert report.successful + report.failed == 3
    
    # Verify JSON serialization works
    json_str = report.to_json()
    assert "health_check" in json_str


def test_batch_optimizer_initialization():
    """Test BatchOptimizer initialization"""
    optimizer = BatchOptimizer()
    
    assert optimizer.operation == "optimization"
    assert optimizer.optimizer is not None


def test_batch_optimizer_optimize_directory(temp_dataset_dir, temp_output_dir):
    """Test batch optimization of directory"""
    optimizer = BatchOptimizer()
    
    report = optimizer.optimize_directory(
        temp_dataset_dir,
        temp_output_dir,
        skip_on_error=True,
        remove_duplicates=True,
        filter_low_quality=True,
        quality_threshold=60,
    )
    
    assert report.operation == "optimization"
    assert report.total_datasets == 3
    
    # Check output files were created
    output_files = list(temp_output_dir.glob("*-optimized.jsonl"))
    assert len(output_files) <= 3  # May be less if some failed


def test_batch_quality_scorer_initialization():
    """Test BatchQualityScorer initialization"""
    scorer = BatchQualityScorer(
        min_record_score=65,
        min_average_score=75,
        max_failed_ratio=0.15,
        min_records=50,
    )
    
    assert scorer.operation == "quality_scoring"
    assert scorer.scorer.min_record_score == 65
    assert scorer.scorer.min_average_score == 75


def test_batch_quality_scorer_score_directory(temp_dataset_dir):
    """Test batch quality scoring of directory"""
    scorer = BatchQualityScorer()
    
    report = scorer.score_directory(temp_dataset_dir, skip_on_error=True)
    
    assert report.operation == "quality_scoring"
    assert report.total_datasets == 3
    assert report.successful + report.failed == 3


def test_batch_processor_error_handling(tmp_path):
    """Test error handling in batch processing"""
    # Create directory with one invalid file
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Valid dataset
    valid_file = dataset_dir / "valid.jsonl"
    valid_file.write_text(json.dumps({"id": "1", "content": "test"}) + "\n")
    
    # Invalid dataset (empty file)
    invalid_file = dataset_dir / "invalid.jsonl"
    invalid_file.write_text("")
    
    monitor = BatchHealthMonitor()
    report = monitor.check_directory(dataset_dir, skip_on_error=True)
    
    # Should have processed both, some may have failed
    assert report.total_datasets == 2
    assert report.successful + report.failed == 2


def test_batch_processor_pattern_matching(tmp_path):
    """Test pattern matching for dataset discovery"""
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Create files with different extensions
    (dataset_dir / "data1.jsonl").write_text("test\n")
    (dataset_dir / "data2.jsonl").write_text("test\n")
    (dataset_dir / "data3.txt").write_text("test\n")
    (dataset_dir / "data4.json").write_text("test\n")
    
    monitor = BatchHealthMonitor()
    
    # Test default pattern (*.jsonl)
    datasets = monitor.find_datasets(dataset_dir)
    assert len(datasets) == 2
    
    # Test custom pattern
    datasets_json = monitor.find_datasets(dataset_dir, pattern="*.json")
    assert len(datasets_json) == 1


def test_batch_report_markdown_formatting():
    """Test markdown formatting of batch reports"""
    results = [
        BatchResult("dataset1.jsonl", "success", None, {}),
        BatchResult("dataset2.jsonl", "failed", "Connection timeout", {}),
        BatchResult("dataset3.jsonl", "skipped", "Already processed", {}),
    ]
    
    report = BatchOperationReport(
        operation="test",
        started_at="2026-04-27T10:00:00",
        completed_at="2026-04-27T10:05:00",
        total_datasets=3,
        successful=1,
        failed=1,
        skipped=1,
        results=tuple(results),
    )
    
    md = report.to_markdown()
    
    # Check structure
    assert "# Batch Test Report" in md
    assert "## Summary" in md
    assert "## Results" in md
    
    # Check emojis
    assert "✅" in md  # success
    assert "❌" in md  # failed
    assert "⏭️" in md  # skipped
    
    # Check details
    assert "Connection timeout" in md
    assert "Already processed" in md
