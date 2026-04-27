"""
Tests for status_dashboard module
"""
from pathlib import Path
import pytest
import json
from peachtree.status_dashboard import (
    StatusDashboard,
    DatasetStatus,
    MultiDatasetStatus,
)
from peachtree.health_monitor import HealthStatus


@pytest.fixture
def temp_dataset_dir(tmp_path):
    """Create temporary directory with sample datasets"""
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Create sample datasets
    for i in range(2):
        dataset_file = dataset_dir / f"dataset{i}.jsonl"
        records = []
        for j in range(5):
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


def test_dataset_status_creation():
    """Test DatasetStatus dataclass creation"""
    status = DatasetStatus(
        dataset_path="test.jsonl",
        timestamp="2026-04-27T10:00:00",
        record_count=100,
        health_status=HealthStatus.GOOD,
        quality_score=85.0,
        quality_gate_passed=True,
        duplicate_ratio=0.05,
        provenance_coverage=0.95,
        safety_coverage=0.98,
        overall_ready=True,
        issues=(),
    )
    
    assert status.dataset_path == "test.jsonl"
    assert status.record_count == 100
    assert status.health_status == HealthStatus.GOOD
    assert status.overall_ready is True
    
    # Test to_dict
    status_dict = status.to_dict()
    assert status_dict["metrics"]["quality_score"] == 85.0
    assert status_dict["gates"]["overall_ready"] is True
    
    # Test to_json
    json_str = status.to_json()
    assert "test.jsonl" in json_str


def test_multi_dataset_status_creation():
    """Test MultiDatasetStatus creation"""
    datasets = [
        DatasetStatus(
            "dataset1.jsonl",
            "2026-04-27T10:00:00",
            100,
            HealthStatus.GOOD,
            85.0,
            True,
            0.05,
            0.95,
            0.98,
            True,
            (),
        ),
        DatasetStatus(
            "dataset2.jsonl",
            "2026-04-27T10:00:00",
            50,
            HealthStatus.WARNING,
            70.0,
            False,
            0.20,
            0.80,
            0.85,
            False,
            ("Low quality score", "High duplicates"),
        ),
    ]
    
    status = MultiDatasetStatus(
        directory="/test/datasets",
        timestamp="2026-04-27T10:00:00",
        total_datasets=2,
        ready_datasets=1,
        datasets=tuple(datasets),
    )
    
    assert status.total_datasets == 2
    assert status.ready_datasets == 1
    
    # Test to_dict
    status_dict = status.to_dict()
    assert status_dict["summary"]["total_datasets"] == 2
    assert status_dict["summary"]["ready_datasets"] == 1
    assert status_dict["summary"]["readiness_ratio"] == 0.5


def test_multi_dataset_status_markdown():
    """Test markdown generation for multi-dataset status"""
    datasets = [
        DatasetStatus(
            "dataset1.jsonl",
            "2026-04-27T10:00:00",
            100,
            HealthStatus.EXCELLENT,
            92.0,
            True,
            0.02,
            0.98,
            0.99,
            True,
            (),
        ),
        DatasetStatus(
            "dataset2.jsonl",
            "2026-04-27T10:00:00",
            50,
            HealthStatus.CRITICAL,
            45.0,
            False,
            0.35,
            0.60,
            0.70,
            False,
            ("Critical quality score", "Excessive duplicates", "Low provenance"),
        ),
    ]
    
    status = MultiDatasetStatus(
        directory="/test/datasets",
        timestamp="2026-04-27T10:00:00",
        total_datasets=2,
        ready_datasets=1,
        datasets=tuple(datasets),
    )
    
    md = status.to_markdown()
    
    # Check structure
    assert "# Dataset Status Dashboard" in md
    assert "## Summary" in md
    assert "## Dataset Status" in md
    
    # Check emojis
    assert "🟢" in md  # EXCELLENT
    assert "🔴" in md  # CRITICAL
    assert "✅" in md  # ready
    assert "❌" in md  # not ready
    
    # Check issues section
    assert "## Issues" in md
    assert "Critical quality score" in md
    assert "Excessive duplicates" in md


def test_status_dashboard_initialization():
    """Test StatusDashboard initialization"""
    dashboard = StatusDashboard(
        quality_warning=80.0,
        quality_critical=65.0,
        duplicate_warning=0.10,
        duplicate_critical=0.25,
        min_average_score=75,
        max_failed_ratio=0.12,
    )
    
    assert dashboard.health_monitor.quality_warning == 80.0
    assert dashboard.quality_scorer.min_average_score == 75


def test_status_dashboard_get_status(temp_dataset_dir):
    """Test getting status for single dataset"""
    dashboard = StatusDashboard()
    
    dataset_file = list(temp_dataset_dir.glob("*.jsonl"))[0]
    status = dashboard.get_status(dataset_file)
    
    assert isinstance(status, DatasetStatus)
    assert status.dataset_path == str(dataset_file)
    assert status.record_count >= 0
    assert isinstance(status.health_status, HealthStatus)
    assert 0.0 <= status.quality_score <= 100.0
    assert 0.0 <= status.duplicate_ratio <= 1.0


def test_status_dashboard_get_directory_status(temp_dataset_dir):
    """Test getting status for directory of datasets"""
    dashboard = StatusDashboard()
    
    status = dashboard.get_directory_status(temp_dataset_dir)
    
    assert isinstance(status, MultiDatasetStatus)
    assert status.directory == str(temp_dataset_dir)
    assert status.total_datasets == 2
    assert len(status.datasets) == 2
    assert 0 <= status.ready_datasets <= status.total_datasets


def test_status_dashboard_write_status(temp_dataset_dir, tmp_path):
    """Test writing status to files"""
    dashboard = StatusDashboard()
    
    # Get single dataset status
    dataset_file = list(temp_dataset_dir.glob("*.jsonl"))[0]
    status = dashboard.get_status(dataset_file)
    
    # Write JSON
    json_path = tmp_path / "status.json"
    dashboard.write_status(status, json_path=json_path)
    
    assert json_path.exists()
    content = json.loads(json_path.read_text())
    assert "dataset_path" in content
    
    # Get directory status
    dir_status = dashboard.get_directory_status(temp_dataset_dir)
    
    # Write both JSON and markdown
    json_path2 = tmp_path / "dir_status.json"
    md_path = tmp_path / "dir_status.md"
    dashboard.write_status(dir_status, json_path=json_path2, markdown_path=md_path)
    
    assert json_path2.exists()
    assert md_path.exists()
    assert "# Dataset Status Dashboard" in md_path.read_text()


def test_status_overall_readiness_logic():
    """Test overall readiness determination logic"""
    # Ready dataset - all gates pass
    ready_status = DatasetStatus(
        "ready.jsonl",
        "2026-04-27T10:00:00",
        100,
        HealthStatus.GOOD,
        85.0,
        quality_gate_passed=True,
        duplicate_ratio=0.10,
        provenance_coverage=0.90,
        safety_coverage=0.95,
        overall_ready=True,
        issues=(),
    )
    assert ready_status.overall_ready is True
    
    # Not ready - low quality
    not_ready_status = DatasetStatus(
        "not_ready.jsonl",
        "2026-04-27T10:00:00",
        100,
        HealthStatus.CRITICAL,
        45.0,
        quality_gate_passed=False,
        duplicate_ratio=0.10,
        provenance_coverage=0.90,
        safety_coverage=0.95,
        overall_ready=False,
        issues=("Low quality",),
    )
    assert not_ready_status.overall_ready is False


def test_status_dashboard_custom_thresholds(temp_dataset_dir):
    """Test status dashboard with custom thresholds"""
    # Strict thresholds
    strict_dashboard = StatusDashboard(
        quality_warning=85.0,
        quality_critical=75.0,
        duplicate_warning=0.05,
        duplicate_critical=0.10,
        min_average_score=80,
        max_failed_ratio=0.05,
    )
    
    status = strict_dashboard.get_directory_status(temp_dataset_dir)
    
    # Should work but may have different readiness
    assert isinstance(status, MultiDatasetStatus)
    assert status.total_datasets > 0


def test_status_issues_collection():
    """Test that issues are properly collected"""
    # Dataset with multiple issues
    status = DatasetStatus(
        "problem.jsonl",
        "2026-04-27T10:00:00",
        100,
        HealthStatus.WARNING,
        70.0,
        quality_gate_passed=False,
        duplicate_ratio=0.25,
        provenance_coverage=0.70,
        safety_coverage=0.75,
        overall_ready=False,
        issues=(
            "Quality gate failed (score: 70.0)",
            "High duplicate ratio (25.0%)",
            "Low provenance coverage (70.0%)",
            "Low safety coverage (75.0%)",
        ),
    )
    
    assert len(status.issues) == 4
    assert all(isinstance(issue, str) for issue in status.issues)
    
    # Check to_dict includes issues
    status_dict = status.to_dict()
    assert len(status_dict["issues"]) == 4


def test_status_dashboard_empty_directory(tmp_path):
    """Test status dashboard with empty directory"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    dashboard = StatusDashboard()
    status = dashboard.get_directory_status(empty_dir)
    
    assert status.total_datasets == 0
    assert status.ready_datasets == 0
    assert len(status.datasets) == 0


def test_status_markdown_table_formatting():
    """Test markdown table formatting for dataset status"""
    datasets = [
        DatasetStatus(
            "small.jsonl",
            "2026-04-27T10:00:00",
            10,
            HealthStatus.GOOD,
            85.0,
            True,
            0.05,
            0.95,
            0.98,
            True,
            (),
        ),
        DatasetStatus(
            "large-dataset-with-long-name.jsonl",
            "2026-04-27T10:00:00",
            1000000,
            HealthStatus.EXCELLENT,
            95.5,
            True,
            0.01,
            0.99,
            0.99,
            True,
            (),
        ),
    ]
    
    status = MultiDatasetStatus(
        "/test/datasets",
        "2026-04-27T10:00:00",
        2,
        2,
        tuple(datasets),
    )
    
    md = status.to_markdown()
    
    # Check table structure
    assert "|" in md
    assert "Records" in md
    assert "Health" in md
    assert "Quality" in md
    assert "Duplicates" in md
    assert "Provenance" in md
    assert "Ready" in md
    
    # Check number formatting
    assert "1,000,000" in md  # Large number formatted
    assert "95.5" in md  # Decimal quality score
    assert "1.0%" in md or "0.0%" in md  # Percentage
