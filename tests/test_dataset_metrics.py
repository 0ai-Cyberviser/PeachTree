"""Tests for dataset_metrics module"""
import json
import pytest

from peachtree.dataset_metrics import (
    DatasetMetricsDashboard,
    DatasetDashboard,
    MetricCategory,
    MetricValue,
)


@pytest.fixture
def dashboard_engine():
    return DatasetMetricsDashboard()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {
            "id": "1",
            "content": "High quality content here with good length",
            "quality_score": 85.0,
            "source_document": {"repo_id": "repo1", "source_path": "file1.py"},
        },
        {
            "id": "2",
            "content": "Medium quality content",
            "quality_score": 65.0,
            "source_document": {"repo_id": "repo1", "source_path": "file2.py"},
        },
        {
            "id": "3",
            "content": "Another high quality piece",
            "quality_score": 90.0,
            "source_document": {"repo_id": "repo2", "source_path": "file3.py"},
        },
        {
            "id": "4",
            "content": "Low quality",
            "quality_score": 40.0,
            "source_document": {"repo_id": "repo2", "source_path": "file4.py"},
        },
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_metric_value_creation():
    metric = MetricValue(
        name="total_records",
        value=100.0,
        unit="records",
    )
    assert metric.name == "total_records"
    assert metric.value == 100.0
    assert metric.unit == "records"
    assert metric.timestamp  # Should have timestamp


def test_metric_value_to_dict():
    metric = MetricValue(name="test", value=50.0, unit="items")
    d = metric.to_dict()
    
    assert d["name"] == "test"
    assert d["value"] == 50.0
    assert d["unit"] == "items"
    assert "timestamp" in d


def test_metric_category_creation():
    category = MetricCategory(category="size")
    assert category.category == "size"
    assert len(category.metrics) == 0
    assert category.health_score == 100.0


def test_metric_category_add_metric():
    category = MetricCategory(category="size")
    metric = MetricValue("total_records", 100.0, "records")
    
    category.add_metric(metric)
    assert len(category.metrics) == 1
    assert category.metrics[0].name == "total_records"


def test_metric_category_get_metric():
    category = MetricCategory(category="size")
    category.add_metric(MetricValue("metric1", 10.0))
    category.add_metric(MetricValue("metric2", 20.0))
    
    found = category.get_metric("metric1")
    assert found is not None
    assert found.value == 10.0
    
    not_found = category.get_metric("missing")
    assert not_found is None


def test_metric_category_to_dict():
    category = MetricCategory(category="test", health_score=85.0)
    category.add_metric(MetricValue("metric1", 100.0))
    
    d = category.to_dict()
    assert d["category"] == "test"
    assert d["health_score"] == 85.0
    assert d["metric_count"] == 1
    assert len(d["metrics"]) == 1


def test_dataset_dashboard_creation():
    dashboard = DatasetDashboard(
        dataset_id="test_dataset",
        timestamp="2024-01-01T00:00:00",
    )
    assert dashboard.dataset_id == "test_dataset"
    assert dashboard.timestamp == "2024-01-01T00:00:00"
    assert dashboard.overall_health == 100.0
    assert len(dashboard.categories) == 0
    assert len(dashboard.alerts) == 0


def test_dataset_dashboard_add_category():
    dashboard = DatasetDashboard(dataset_id="test", timestamp="2024-01-01T00:00:00")
    category = MetricCategory(category="size")
    
    dashboard.add_category(category)
    assert len(dashboard.categories) == 1
    assert "size" in dashboard.categories


def test_dataset_dashboard_get_category():
    dashboard = DatasetDashboard(dataset_id="test", timestamp="2024-01-01T00:00:00")
    dashboard.add_category(MetricCategory(category="size"))
    
    found = dashboard.get_category("size")
    assert found is not None
    assert found.category == "size"
    
    not_found = dashboard.get_category("missing")
    assert not_found is None


def test_dataset_dashboard_add_alert():
    dashboard = DatasetDashboard(dataset_id="test", timestamp="2024-01-01T00:00:00")
    dashboard.add_alert("Low quality detected")
    
    assert len(dashboard.alerts) == 1
    assert dashboard.alerts[0] == "Low quality detected"


def test_dataset_dashboard_to_dict():
    dashboard = DatasetDashboard(dataset_id="test", timestamp="2024-01-01T00:00:00")
    category = MetricCategory(category="size")
    category.add_metric(MetricValue("total", 100.0))
    dashboard.add_category(category)
    
    d = dashboard.to_dict()
    assert d["dataset_id"] == "test"
    assert d["overall_health"] == 100.0
    assert "size" in d["categories"]
    assert d["total_metrics"] == 1


def test_dataset_dashboard_to_json():
    dashboard = DatasetDashboard(dataset_id="test", timestamp="2024-01-01T00:00:00")
    json_str = dashboard.to_json()
    data = json.loads(json_str)
    
    assert data["dataset_id"] == "test"


def test_dataset_dashboard_to_markdown():
    dashboard = DatasetDashboard(dataset_id="test_dataset", timestamp="2024-01-01T00:00:00")
    dashboard.overall_health = 85.0
    
    category = MetricCategory(category="size", health_score=90.0)
    category.add_metric(MetricValue("total_records", 100.0, "records"))
    dashboard.add_category(category)
    
    dashboard.add_alert("Test alert")
    
    markdown = dashboard.to_markdown()
    
    assert "# Dataset Metrics Dashboard" in markdown
    assert "test_dataset" in markdown
    assert "85.0" in markdown
    assert "🚨 Alerts" in markdown
    assert "Test alert" in markdown
    assert "Size" in markdown


def test_collect_size_metrics(dashboard_engine, sample_dataset):
    category = dashboard_engine._collect_size_metrics(sample_dataset)
    
    assert category.category == "size"
    assert len(category.metrics) == 4
    
    total_records = category.get_metric("total_records")
    assert total_records is not None
    assert total_records.value == 4.0


def test_collect_quality_metrics(dashboard_engine, sample_dataset):
    category = dashboard_engine._collect_quality_metrics(sample_dataset)
    
    assert category.category == "quality"
    
    avg_quality = category.get_metric("avg_quality_score")
    assert avg_quality is not None
    assert avg_quality.value > 0
    
    high_count = category.get_metric("high_quality_count")
    assert high_count is not None
    assert high_count.value == 2.0  # Two records with score >= 80


def test_collect_provenance_metrics(dashboard_engine, sample_dataset):
    category = dashboard_engine._collect_provenance_metrics(sample_dataset)
    
    assert category.category == "provenance"
    
    metadata_coverage = category.get_metric("metadata_coverage")
    assert metadata_coverage is not None
    assert metadata_coverage.value == 100.0  # All records have source_document
    
    unique_repos = category.get_metric("unique_repos")
    assert unique_repos is not None
    assert unique_repos.value == 2.0


def test_collect_content_metrics(dashboard_engine, sample_dataset):
    category = dashboard_engine._collect_content_metrics(sample_dataset)
    
    assert category.category == "content"
    
    avg_words = category.get_metric("avg_words_per_record")
    assert avg_words is not None
    assert avg_words.value > 0
    
    empty_count = category.get_metric("empty_content_count")
    assert empty_count is not None
    assert empty_count.value == 0.0


def test_generate_dashboard(dashboard_engine, sample_dataset):
    dashboard = dashboard_engine.generate_dashboard(sample_dataset, dataset_id="test")
    
    assert dashboard.dataset_id == "test"
    assert len(dashboard.categories) == 4
    assert "size" in dashboard.categories
    assert "quality" in dashboard.categories
    assert "provenance" in dashboard.categories
    assert "content" in dashboard.categories
    assert dashboard.overall_health > 0


def test_generate_dashboard_with_alerts(dashboard_engine, tmp_path):
    dataset = tmp_path / "low_quality.jsonl"
    records = [
        {"id": str(i), "content": "low quality", "quality_score": 30.0}
        for i in range(5)
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    dashboard = dashboard_engine.generate_dashboard(dataset, dataset_id="low_test")
    
    # Should have alerts due to low quality and low record count
    assert len(dashboard.alerts) > 0


def test_save_dashboard_json(dashboard_engine, sample_dataset, tmp_path):
    dashboard = dashboard_engine.generate_dashboard(sample_dataset, dataset_id="test")
    output = tmp_path / "dashboard.json"
    
    dashboard_engine.save_dashboard(dashboard, output, format="json")
    
    assert output.exists()
    
    with open(output) as f:
        data = json.load(f)
    
    assert data["dataset_id"] == "test"


def test_save_dashboard_markdown(dashboard_engine, sample_dataset, tmp_path):
    dashboard = dashboard_engine.generate_dashboard(sample_dataset, dataset_id="test")
    output = tmp_path / "dashboard.md"
    
    dashboard_engine.save_dashboard(dashboard, output, format="markdown")
    
    assert output.exists()
    
    content = output.read_text()
    assert "# Dataset Metrics Dashboard" in content


def test_compare_dashboards(dashboard_engine, sample_dataset, tmp_path):
    # Create two slightly different datasets
    dataset1 = sample_dataset
    
    dataset2 = tmp_path / "dataset2.jsonl"
    records = [
        {"id": "1", "content": "content", "quality_score": 90.0, "source_document": {"repo_id": "r1"}},
        {"id": "2", "content": "content", "quality_score": 85.0, "source_document": {"repo_id": "r1"}},
    ]
    with open(dataset2, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    dashboard1 = dashboard_engine.generate_dashboard(dataset1, dataset_id="d1")
    dashboard2 = dashboard_engine.generate_dashboard(dataset2, dataset_id="d2")
    
    comparison = dashboard_engine.compare_dashboards(dashboard1, dashboard2)
    
    assert comparison["dataset1"] == "d1"
    assert comparison["dataset2"] == "d2"
    assert "health_change" in comparison
    assert "category_changes" in comparison


def test_generate_alerts_low_records(dashboard_engine, tmp_path):
    dataset = tmp_path / "small.jsonl"
    records = [{"id": "1", "content": "test", "quality_score": 80.0}]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    dashboard = dashboard_engine.generate_dashboard(dataset, dataset_id="small")
    
    # Should have alert for low record count
    assert len(dashboard.alerts) > 0
    assert any("Low record count" in alert for alert in dashboard.alerts)


def test_generate_alerts_low_quality(dashboard_engine, tmp_path):
    dataset = tmp_path / "low_quality.jsonl"
    records = [
        {"id": str(i), "content": "test", "quality_score": 40.0, "source_document": {"repo": "r1"}}
        for i in range(150)
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    dashboard = dashboard_engine.generate_dashboard(dataset, dataset_id="low")
    
    # Should have alert for low average quality
    assert len(dashboard.alerts) > 0
    assert any("Low average quality" in alert for alert in dashboard.alerts)


def test_generate_alerts_low_metadata_coverage(dashboard_engine, tmp_path):
    dataset = tmp_path / "missing_metadata.jsonl"
    records = [
        {"id": str(i), "content": "test", "quality_score": 80.0}
        for i in range(150)
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    dashboard = dashboard_engine.generate_dashboard(dataset, dataset_id="missing")
    
    # Should have alert for low metadata coverage
    assert len(dashboard.alerts) > 0
    assert any("metadata coverage" in alert for alert in dashboard.alerts)


def test_quality_thresholds_customization():
    engine = DatasetMetricsDashboard()
    engine.quality_thresholds["min_quality_score"] = 80.0
    engine.quality_thresholds["min_records"] = 50
    
    assert engine.quality_thresholds["min_quality_score"] == 80.0
    assert engine.quality_thresholds["min_records"] == 50
