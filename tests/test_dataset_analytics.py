"""
Tests for dataset_analytics module
"""
import pytest
import json
from peachtree.dataset_analytics import (
    DatasetAnalyticsEngine,
    DatasetAnalyticsReport,
    ContentStatistics,
    ProvenanceStatistics,
    QualityStatistics,
)


@pytest.fixture
def test_dataset(tmp_path):
    """Create test dataset with analytics data"""
    dataset = tmp_path / "analytics_test.jsonl"
    records = [
        {
            "id": "1",
            "content": "Short text",
            "source_repo": "org/repo1",
            "source_path": "file1.py",
            "quality_score": 85,
        },
        {
            "id": "2",
            "content": "This is a medium length text with more words",
            "source_repo": "org/repo1",
            "source_path": "file2.py",
            "quality_score": 90,
        },
        {
            "id": "3",
            "content": "A" * 1000,  # Long text
            "source_repo": "org/repo2",
            "source_path": "docs/file1.md",
            "quality_score": 75,
        },
        {
            "id": "4",
            "content": "Another short one",
            "source_repo": "org/repo2",
            "source_path": "docs/file2.md",
            "quality_score": 50,
        },
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_content_statistics_creation():
    """Test ContentStatistics dataclass"""
    stats = ContentStatistics(
        total_records=100,
        total_characters=10000,
        total_words=2000,
        total_tokens=2500,
        avg_length=100.0,
        min_length=10,
        max_length=500,
        median_length=95.0,
    )
    
    assert stats.total_records == 100
    assert stats.avg_length == 100.0


def test_content_statistics_to_dict():
    """Test ContentStatistics serialization"""
    stats = ContentStatistics(
        total_records=50,
        total_characters=5000,
        total_words=1000,
        total_tokens=1250,
        avg_length=100.0,
        min_length=10,
        max_length=200,
        median_length=95.0,
    )
    
    data = stats.to_dict()
    assert data["total_records"] == 50
    assert data["avg_length"] == 100.0


def test_provenance_statistics_creation():
    """Test ProvenanceStatistics dataclass"""
    stats = ProvenanceStatistics(
        total_repos=5,
        total_files=20,
        repo_distribution={"repo1": 10, "repo2": 10},
    )
    
    assert stats.total_repos == 5
    assert stats.total_files == 20


def test_quality_statistics_creation():
    """Test QualityStatistics dataclass"""
    stats = QualityStatistics(
        records_with_quality=100,
        avg_quality_score=85.5,
        low_quality_count=10,
        medium_quality_count=30,
        high_quality_count=60,
    )
    
    assert stats.avg_quality_score == 85.5
    assert stats.high_quality_count == 60


def test_analytics_report_creation():
    """Test DatasetAnalyticsReport initialization"""
    content_stats = ContentStatistics(100, 10000, 2000, 2500, 100.0, 10, 500, 95.0)
    provenance_stats = ProvenanceStatistics(5, 20)
    
    report = DatasetAnalyticsReport(
        dataset_path="test.jsonl",
        content_stats=content_stats,
        provenance_stats=provenance_stats,
    )
    
    assert report.dataset_path == "test.jsonl"
    assert report.content_stats.total_records == 100


def test_analytics_report_to_json():
    """Test analytics report JSON serialization"""
    content_stats = ContentStatistics(10, 1000, 200, 250, 100.0, 10, 200, 95.0)
    provenance_stats = ProvenanceStatistics(2, 5)
    report = DatasetAnalyticsReport("test.jsonl", content_stats, provenance_stats)
    
    json_str = report.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["dataset_path"] == "test.jsonl"
    assert parsed["content_statistics"]["total_records"] == 10


def test_analytics_report_to_markdown():
    """Test markdown report generation"""
    content_stats = ContentStatistics(100, 10000, 2000, 2500, 100.0, 10, 500, 95.0)
    provenance_stats = ProvenanceStatistics(5, 20)
    report = DatasetAnalyticsReport("test.jsonl", content_stats, provenance_stats)
    
    markdown = report.to_markdown()
    
    assert "# Dataset Analytics Report" in markdown
    assert "## Content Statistics" in markdown
    assert "**Total Records:** 100" in markdown


def test_analytics_engine_initialization():
    """Test DatasetAnalyticsEngine initialization"""
    engine = DatasetAnalyticsEngine()
    assert engine is not None


def test_estimate_tokens():
    """Test token estimation"""
    engine = DatasetAnalyticsEngine()
    
    text = "a" * 100
    tokens = engine._estimate_tokens(text)
    
    assert tokens == 25  # 100 chars / 4


def test_compute_median_odd_count():
    """Test median computation with odd count"""
    engine = DatasetAnalyticsEngine()
    
    values = [1, 3, 5, 7, 9]
    median = engine._compute_median(values)
    
    assert median == 5.0


def test_compute_median_even_count():
    """Test median computation with even count"""
    engine = DatasetAnalyticsEngine()
    
    values = [1, 3, 5, 7]
    median = engine._compute_median(values)
    
    assert median == 4.0


def test_compute_median_empty():
    """Test median computation with empty list"""
    engine = DatasetAnalyticsEngine()
    
    median = engine._compute_median([])
    assert median == 0.0


def test_get_length_bucket():
    """Test length bucket categorization"""
    engine = DatasetAnalyticsEngine()
    
    assert engine._get_length_bucket(50) == "0-99"
    assert engine._get_length_bucket(200) == "100-499"
    assert engine._get_length_bucket(750) == "500-999"
    assert engine._get_length_bucket(2000) == "1K-5K"
    assert engine._get_length_bucket(7500) == "5K-10K"
    assert engine._get_length_bucket(15000) == "10K+"


def test_get_quality_category():
    """Test quality category assignment"""
    engine = DatasetAnalyticsEngine()
    
    assert engine._get_quality_category(90) == "high"
    assert engine._get_quality_category(70) == "medium"
    assert engine._get_quality_category(50) == "low"


def test_analyze_basic(test_dataset):
    """Test basic dataset analysis"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset, compute_quality=False)
    
    assert report.content_stats.total_records == 4
    assert report.content_stats.total_characters > 0
    assert report.provenance_stats.total_repos == 2


def test_analyze_with_quality(test_dataset):
    """Test analysis with quality computation"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset, compute_quality=True)
    
    assert report.quality_stats is not None
    assert report.quality_stats.records_with_quality == 4
    assert report.quality_stats.avg_quality_score > 0


def test_analyze_content_metrics(test_dataset):
    """Test content metrics calculation"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset)
    
    assert report.content_stats.min_length > 0
    assert report.content_stats.max_length >= report.content_stats.min_length
    assert report.content_stats.avg_length > 0
    assert report.content_stats.median_length > 0


def test_analyze_provenance_distribution(test_dataset):
    """Test provenance distribution tracking"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset)
    
    assert "org/repo1" in report.provenance_stats.repo_distribution
    assert "org/repo2" in report.provenance_stats.repo_distribution
    assert report.provenance_stats.repo_distribution["org/repo1"] == 2
    assert report.provenance_stats.repo_distribution["org/repo2"] == 2


def test_analyze_file_type_distribution(test_dataset):
    """Test file type distribution tracking"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset)
    
    assert ".py" in report.provenance_stats.file_type_distribution
    assert ".md" in report.provenance_stats.file_type_distribution


def test_analyze_length_distribution(test_dataset):
    """Test length distribution buckets"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset)
    
    assert len(report.content_stats.length_distribution) > 0
    assert "0-99" in report.content_stats.length_distribution or "100-499" in report.content_stats.length_distribution


def test_analyze_quality_distribution(test_dataset):
    """Test quality score distribution"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset, compute_quality=True)
    
    assert report.quality_stats.high_quality_count > 0
    assert report.quality_stats.low_quality_count > 0


def test_compare_datasets(test_dataset, tmp_path):
    """Test comparing two datasets"""
    # Create second dataset
    dataset2 = tmp_path / "dataset2.jsonl"
    records = [
        {"id": "1", "content": "Test 1", "source_repo": "org/repo1"},
        {"id": "2", "content": "Test 2", "source_repo": "org/repo1"},
    ]
    dataset2.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    
    engine = DatasetAnalyticsEngine()
    comparison = engine.compare_datasets(test_dataset, dataset2)
    
    assert "dataset1" in comparison
    assert "dataset2" in comparison
    assert "comparison" in comparison
    assert "record_delta" in comparison["comparison"]


def test_compare_datasets_deltas(test_dataset, tmp_path):
    """Test comparison deltas calculation"""
    dataset2 = tmp_path / "dataset2.jsonl"
    records = [{"id": str(i), "content": "Test"} for i in range(10)]
    dataset2.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    
    engine = DatasetAnalyticsEngine()
    comparison = engine.compare_datasets(test_dataset, dataset2)
    
    assert comparison["comparison"]["record_delta"] == 6  # 10 - 4


def test_find_outliers_basic(test_dataset):
    """Test finding outlier records"""
    engine = DatasetAnalyticsEngine()
    outliers = engine.find_outliers(test_dataset, threshold=1.0)
    
    # With threshold=1.0, should find some outliers
    assert isinstance(outliers, list)


def test_find_outliers_high_threshold(test_dataset):
    """Test outliers with high threshold"""
    engine = DatasetAnalyticsEngine()
    outliers = engine.find_outliers(test_dataset, threshold=10.0)
    
    # Very high threshold should find few/no outliers
    assert isinstance(outliers, list)


def test_find_outliers_structure(test_dataset):
    """Test outlier record structure"""
    engine = DatasetAnalyticsEngine()
    outliers = engine.find_outliers(test_dataset, threshold=0.5)
    
    if outliers:
        outlier = outliers[0]
        assert "record_id" in outlier
        assert "length" in outlier
        assert "z_score" in outlier
        assert "type" in outlier


def test_generate_summary_statistics(test_dataset):
    """Test quick summary generation"""
    engine = DatasetAnalyticsEngine()
    summary = engine.generate_summary_statistics(test_dataset)
    
    assert "total_records" in summary
    assert "total_tokens" in summary
    assert "avg_length" in summary
    assert "unique_repos" in summary
    assert "unique_files" in summary


def test_summary_statistics_values(test_dataset):
    """Test summary statistics values"""
    engine = DatasetAnalyticsEngine()
    summary = engine.generate_summary_statistics(test_dataset)
    
    assert summary["total_records"] == 4
    assert summary["unique_repos"] == 2
    assert summary["unique_files"] == 4


def test_analyze_empty_dataset(tmp_path):
    """Test analyzing empty dataset"""
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(empty)
    
    assert report.content_stats.total_records == 0


def test_top_repos_list(test_dataset):
    """Test top repositories list"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset)
    
    assert len(report.provenance_stats.top_repos) <= 10
    if report.provenance_stats.top_repos:
        repo, count = report.provenance_stats.top_repos[0]
        assert isinstance(repo, str)
        assert isinstance(count, int)


def test_markdown_report_sections(test_dataset):
    """Test markdown report contains all sections"""
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(test_dataset, compute_quality=True)
    markdown = report.to_markdown()
    
    assert "## Content Statistics" in markdown
    assert "## Provenance Statistics" in markdown
    assert "## Quality Statistics" in markdown


def test_analyze_with_missing_provenance(tmp_path):
    """Test analyzing dataset with missing provenance"""
    dataset = tmp_path / "no_provenance.jsonl"
    records = [
        {"id": "1", "content": "Test content"},
        {"id": "2", "content": "More content"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    
    engine = DatasetAnalyticsEngine()
    report = engine.analyze(dataset)
    
    assert report.content_stats.total_records == 2
    assert report.provenance_stats.total_repos == 0
