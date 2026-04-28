"""Tests for health_monitor module"""
import json

import pytest

from peachtree.health_monitor import (
    DatasetHealthMonitor,
    HealthStatus,
    DatasetHealthSnapshot,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample dataset for testing"""
    dataset = tmp_path / "test_dataset.jsonl"
    records = [
        {
            "id": "rec1",
            "instruction": "Test instruction 1",
            "input": "",
            "output": "Test output 1",
            "source_repo": "test/repo",
            "source_path": "test.py",
            "source_digest": "abc123",
            "license_id": "MIT",
            "safety_score": 0.9,
            "quality_score": 0.85,
        },
        {
            "id": "rec2",
            "instruction": "Test instruction 2",
            "input": "context",
            "output": "Test output 2",
            "source_repo": "test/repo",
            "source_path": "test2.py",
            "source_digest": "def456",
            "license_id": "Apache-2.0",
            "safety_score": 0.95,
            "quality_score": 0.90,
        },
    ]
    lines = [json.dumps(r) for r in records]
    dataset.write_text("\n".join(lines) + "\n")
    return dataset


def test_health_monitor_initialization():
    """Test health monitor initialization"""
    monitor = DatasetHealthMonitor()
    assert monitor.quality_warning == 75.0
    assert monitor.quality_critical == 60.0
    assert monitor.duplicate_warning == 0.15
    assert monitor.duplicate_critical == 0.30


def test_check_health_snapshot(sample_dataset, tmp_path):
    """Test generating health snapshot"""
    history_dir = tmp_path / "history"
    monitor = DatasetHealthMonitor(history_dir=history_dir)
    
    snapshot = monitor.check_health(sample_dataset, save_history=False)
    
    assert isinstance(snapshot, DatasetHealthSnapshot)
    assert snapshot.record_count == 2
    assert snapshot.quality_score > 0
    assert isinstance(snapshot.overall_status, HealthStatus)
    assert len(snapshot.metrics) > 0


def test_health_snapshot_to_json(sample_dataset, tmp_path):
    """Test health snapshot JSON serialization"""
    monitor = DatasetHealthMonitor(history_dir=tmp_path / "history")
    snapshot = monitor.check_health(sample_dataset, save_history=False)
    
    json_output = snapshot.to_json()
    assert isinstance(json_output, str)
    
    data = json.loads(json_output)
    assert "dataset_path" in data
    assert "overall_status" in data
    assert "quality_score" in data
    assert "metrics" in data


def test_health_snapshot_to_markdown(sample_dataset, tmp_path):
    """Test health snapshot markdown generation"""
    monitor = DatasetHealthMonitor(history_dir=tmp_path / "history")
    snapshot = monitor.check_health(sample_dataset, save_history=False)
    
    markdown = snapshot.to_markdown()
    assert "# PeachTree Dataset Health Report" in markdown
    assert "Health Metrics" in markdown
    assert "Status:" in markdown


def test_health_status_determination(sample_dataset, tmp_path):
    """Test health status is determined correctly"""
    monitor = DatasetHealthMonitor(
        history_dir=tmp_path / "history",
        quality_warning=50.0,
        quality_critical=30.0,
    )
    snapshot = monitor.check_health(sample_dataset, save_history=False)
    
    # With good quality data, should be EXCELLENT or GOOD
    assert snapshot.overall_status in (HealthStatus.EXCELLENT, HealthStatus.GOOD)
    assert snapshot.is_healthy


def test_trend_analysis_insufficient_history(sample_dataset, tmp_path):
    """Test trend analysis with insufficient history"""
    monitor = DatasetHealthMonitor(history_dir=tmp_path / "history")
    
    # First snapshot
    monitor.check_health(sample_dataset, save_history=True)
    
    # Analyze trend with only 1 snapshot
    trend = monitor.analyze_trend(sample_dataset, days=7)
    
    assert trend.trend_direction == "unknown"
    assert len(trend.alerts) > 0


def test_health_history_persistence(sample_dataset, tmp_path):
    """Test that health snapshots are persisted"""
    history_dir = tmp_path / "history"
    monitor = DatasetHealthMonitor(history_dir=history_dir)
    
    monitor.check_health(sample_dataset, save_history=True)
    
    # Check that history file was created
    history_files = list(history_dir.glob("*.json"))
    assert len(history_files) == 1
    
    # Verify content
    saved_data = json.loads(history_files[0].read_text())
    assert saved_data["dataset_path"] == str(sample_dataset)
    assert saved_data["record_count"] == 2


def test_custom_thresholds(sample_dataset, tmp_path):
    """Test health monitor with custom thresholds"""
    monitor = DatasetHealthMonitor(
        history_dir=tmp_path / "history",
        quality_warning=90.0,
        quality_critical=80.0,
        duplicate_warning=0.05,
        duplicate_critical=0.10,
    )
    
    snapshot = monitor.check_health(sample_dataset, save_history=False)
    
    # Metrics should use custom thresholds
    for metric in snapshot.metrics:
        if metric.name == "Quality Score":
            assert metric.threshold_warning == 90.0
            assert metric.threshold_critical == 80.0
        elif metric.name == "Duplicate Ratio":
            assert metric.threshold_warning == 0.05
            assert metric.threshold_critical == 0.10
