"""Tests for dataset_monitoring module"""
import json
import time
import pytest

from peachtree.dataset_monitoring import (
    DatasetMonitor,
    MonitoringConfig,
    HealthCheck,
    HealthStatus,
    Alert,
    MetricSnapshot,
)


@pytest.fixture
def config():
    return MonitoringConfig(
        dataset_id="test_dataset",
        quality_threshold=70.0,
        min_record_count=10,
        max_age_hours=24,
    )


@pytest.fixture
def monitor(config):
    return DatasetMonitor(config)


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": str(i), "content": f"Test content {i}", "quality_score": 75.0 + i}
        for i in range(20)
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_health_check_creation():
    check = HealthCheck(
        check_id="test_check",
        check_name="Test Check",
        status="healthy",
        message="All good",
        timestamp="2024-01-01T00:00:00Z",
    )
    assert check.check_id == "test_check"
    assert check.status == "healthy"


def test_health_check_to_dict():
    check = HealthCheck(
        check_id="test_check",
        check_name="Test Check",
        status="unhealthy",
        message="Problem detected",
        timestamp="2024-01-01T00:00:00Z",
        value=50.0,
        threshold=70.0,
    )
    d = check.to_dict()
    assert d["status"] == "unhealthy"
    assert d["value"] == 50.0


def test_health_status_creation():
    status = HealthStatus(
        overall_status="healthy",
        timestamp="2024-01-01T00:00:00Z",
    )
    assert status.overall_status == "healthy"
    assert len(status.checks) == 0


def test_health_status_add_check():
    status = HealthStatus(overall_status="healthy", timestamp="2024-01-01T00:00:00Z")
    check = HealthCheck("c1", "Check 1", "healthy", "OK", "2024-01-01T00:00:00Z")
    
    status.add_check(check)
    
    assert len(status.checks) == 1


def test_health_status_to_dict():
    status = HealthStatus(overall_status="healthy", timestamp="2024-01-01T00:00:00Z")
    status.add_check(HealthCheck("c1", "Check 1", "healthy", "OK", "2024-01-01T00:00:00Z"))
    status.add_check(HealthCheck("c2", "Check 2", "degraded", "Warning", "2024-01-01T00:00:00Z"))
    
    d = status.to_dict()
    assert d["total_checks"] == 2
    assert d["healthy_checks"] == 1
    assert d["degraded_checks"] == 1


def test_health_status_to_json():
    status = HealthStatus(overall_status="healthy", timestamp="2024-01-01T00:00:00Z")
    json_str = status.to_json()
    data = json.loads(json_str)
    
    assert data["overall_status"] == "healthy"


def test_alert_creation():
    alert = Alert(
        alert_id="alert_1",
        alert_name="Low Quality",
        severity="warning",
        message="Quality below threshold",
        timestamp="2024-01-01T00:00:00Z",
        dataset_id="test_ds",
        metric_name="quality_score",
        metric_value=65.0,
        threshold=70.0,
    )
    assert alert.severity == "warning"
    assert alert.metric_value == 65.0


def test_alert_to_dict():
    alert = Alert(
        alert_id="alert_1",
        alert_name="Low Quality",
        severity="critical",
        message="Critical quality issue",
        timestamp="2024-01-01T00:00:00Z",
        dataset_id="test_ds",
        metric_name="quality_score",
        metric_value=50.0,
        threshold=70.0,
    )
    d = alert.to_dict()
    assert d["severity"] == "critical"
    assert d["metric_value"] == 50.0


def test_metric_snapshot_creation():
    snapshot = MetricSnapshot(
        timestamp="2024-01-01T00:00:00Z",
        dataset_id="test_ds",
        record_count=100,
        avg_quality_score=80.0,
        avg_content_length=500.0,
        duplicate_rate=5.0,
        empty_content_rate=2.0,
    )
    assert snapshot.record_count == 100
    assert snapshot.avg_quality_score == 80.0


def test_metric_snapshot_to_dict():
    snapshot = MetricSnapshot(
        timestamp="2024-01-01T00:00:00Z",
        dataset_id="test_ds",
        record_count=50,
        avg_quality_score=75.0,
        avg_content_length=300.0,
        duplicate_rate=10.0,
        empty_content_rate=5.0,
    )
    d = snapshot.to_dict()
    assert d["record_count"] == 50
    assert d["duplicate_rate"] == 10.0


def test_monitoring_config_creation():
    config = MonitoringConfig(
        dataset_id="test_ds",
        quality_threshold=75.0,
        min_record_count=50,
    )
    assert config.dataset_id == "test_ds"
    assert config.quality_threshold == 75.0


def test_monitoring_config_to_dict():
    config = MonitoringConfig(
        dataset_id="test_ds",
        check_interval_seconds=600,
        quality_threshold=80.0,
    )
    d = config.to_dict()
    assert d["check_interval_seconds"] == 600
    assert d["quality_threshold"] == 80.0


def test_monitoring_config_to_json():
    config = MonitoringConfig(dataset_id="test_ds")
    json_str = config.to_json()
    data = json.loads(json_str)
    
    assert data["dataset_id"] == "test_ds"


def test_check_health_healthy(monitor, sample_dataset):
    status = monitor.check_health(sample_dataset)
    
    assert status.overall_status == "healthy"
    assert len(status.checks) > 0


def test_check_health_dataset_not_exists(monitor, tmp_path):
    missing = tmp_path / "missing.jsonl"
    
    status = monitor.check_health(missing)
    
    assert status.overall_status == "unhealthy"


def test_check_health_quality_degraded(tmp_path):
    dataset = tmp_path / "low_quality.jsonl"
    with open(dataset, 'w') as f:
        for i in range(20):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 50.0}) + "\n")
    
    config = MonitoringConfig(
        dataset_id="test",
        quality_threshold=70.0,
        min_record_count=10,
    )
    monitor = DatasetMonitor(config)
    
    status = monitor.check_health(dataset)
    
    assert status.overall_status == "degraded"


def test_check_health_low_record_count(tmp_path):
    dataset = tmp_path / "small.jsonl"
    with open(dataset, 'w') as f:
        for i in range(5):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 80.0}) + "\n")
    
    config = MonitoringConfig(
        dataset_id="test",
        min_record_count=10,
    )
    monitor = DatasetMonitor(config)
    
    status = monitor.check_health(dataset)
    
    # Should be degraded or unhealthy
    assert status.overall_status in ["degraded", "unhealthy"]


def test_compute_metrics(monitor, sample_dataset):
    metrics = monitor._compute_metrics(sample_dataset)
    
    assert metrics.dataset_id == "test_dataset"
    assert metrics.record_count == 20
    assert metrics.avg_quality_score > 0


def test_compute_metrics_empty_dataset(monitor, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.touch()
    
    metrics = monitor._compute_metrics(empty)
    
    assert metrics.record_count == 0
    assert metrics.avg_quality_score == 0.0


def test_check_alerts_quality(monitor, tmp_path):
    dataset = tmp_path / "low_quality.jsonl"
    with open(dataset, 'w') as f:
        for i in range(10):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 60.0}) + "\n")
    
    metrics = monitor._compute_metrics(dataset)
    alerts = monitor.check_alerts(metrics)
    
    assert len(alerts) > 0
    assert any(a.metric_name == "quality_score" for a in alerts)


def test_check_alerts_size(monitor, tmp_path):
    dataset = tmp_path / "small.jsonl"
    with open(dataset, 'w') as f:
        for i in range(5):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 80.0}) + "\n")
    
    metrics = monitor._compute_metrics(dataset)
    alerts = monitor.check_alerts(metrics)
    
    assert len(alerts) > 0
    assert any(a.metric_name == "record_count" for a in alerts)


def test_get_metric_trend(monitor, sample_dataset):
    # Perform multiple health checks to build history
    for _ in range(3):
        monitor.check_health(sample_dataset)
    
    trend = monitor.get_metric_trend("avg_quality_score", hours=24)
    
    assert len(trend) == 3


def test_get_alert_summary(monitor, sample_dataset):
    # Trigger some alerts
    metrics = monitor._compute_metrics(sample_dataset)
    monitor.check_alerts(metrics)
    
    summary = monitor.get_alert_summary(hours=24)
    
    assert "total_alerts" in summary
    assert "severity_counts" in summary


def test_save_health_status(monitor, sample_dataset, tmp_path):
    status = monitor.check_health(sample_dataset)
    output = tmp_path / "health.json"
    
    monitor.save_health_status(status, output)
    
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
    assert data["overall_status"] == status.overall_status


def test_save_metrics_history(monitor, sample_dataset, tmp_path):
    # Build some history
    monitor.check_health(sample_dataset)
    monitor.check_health(sample_dataset)
    
    output = tmp_path / "metrics_history.json"
    monitor.save_metrics_history(output)
    
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
    assert len(data) == 2


def test_generate_dashboard(monitor, sample_dataset):
    # Perform health check to populate metrics
    monitor.check_health(sample_dataset)
    
    dashboard = monitor.generate_dashboard()
    
    assert dashboard["dataset_id"] == "test_dataset"
    assert "current_metrics" in dashboard
    assert "trends" in dashboard


def test_generate_dashboard_no_data():
    config = MonitoringConfig(dataset_id="test")
    monitor = DatasetMonitor(config)
    
    dashboard = monitor.generate_dashboard()
    
    assert dashboard["status"] == "no_data"


def test_get_file_age(monitor, sample_dataset):
    age = monitor._get_file_age(sample_dataset)
    
    # File was just created, should be close to 0
    assert age < 1.0  # Less than 1 hour


def test_multiple_health_checks(monitor, sample_dataset):
    # Perform multiple checks
    status1 = monitor.check_health(sample_dataset)
    time.sleep(0.1)
    status2 = monitor.check_health(sample_dataset)
    
    assert len(monitor.metric_history) == 2
    assert status1.overall_status == status2.overall_status


def test_health_check_all_checks_present(monitor, sample_dataset):
    status = monitor.check_health(sample_dataset)
    
    check_ids = [c.check_id for c in status.checks]
    assert "dataset_exists" in check_ids
    assert "record_count" in check_ids
    assert "quality_score" in check_ids
    assert "freshness" in check_ids
    assert "duplicate_rate" in check_ids
