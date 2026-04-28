"""Tests for dataset_profiler module"""
import json
import pytest

from peachtree.dataset_profiler import (
    DatasetProfiler,
    NumericStats,
    DistributionStats,
)


@pytest.fixture
def profiler():
    return DatasetProfiler()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "content": "Test content one", "quality_score": 85.0, "category": "A", "metadata": {"source": "test"}},
        {"id": "2", "content": "Test content two longer", "quality_score": 90.0, "category": "B", "metadata": {"source": "test"}},
        {"id": "3", "content": "Short", "quality_score": 65.0, "category": "A", "metadata": {"source": "prod"}},
        {"id": "4", "content": "", "quality_score": 45.0, "category": "C"},
        {"id": "5", "content": "Test content five", "quality_score": 80.0, "category": "A", "label": "positive", "metadata": {"source": "test"}},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_numeric_stats_creation():
    stats = NumericStats(
        count=10,
        mean=75.5,
        median=76.0,
        std_dev=5.2,
        min_value=60.0,
        max_value=90.0,
        percentile_25=70.0,
        percentile_75=80.0,
        percentile_95=88.0,
        percentile_99=89.5,
    )
    assert stats.count == 10
    assert stats.mean == 75.5
    assert stats.percentile_95 == 88.0


def test_numeric_stats_to_dict():
    stats = NumericStats(
        count=5,
        mean=50.0,
        median=50.0,
        std_dev=10.0,
        min_value=30.0,
        max_value=70.0,
        percentile_25=40.0,
        percentile_75=60.0,
        percentile_95=68.0,
        percentile_99=69.5,
    )
    d = stats.to_dict()
    assert d["mean"] == 50.0
    assert d["p95"] == 68.0


def test_distribution_stats_creation():
    stats = DistributionStats(
        unique_count=5,
        top_values=[("A", 10), ("B", 5), ("C", 3)],
        distribution={"A": 10, "B": 5, "C": 3, "D": 2, "E": 1},
    )
    assert stats.unique_count == 5
    assert len(stats.top_values) == 3
    assert stats.top_values[0] == ("A", 10)


def test_distribution_stats_to_dict():
    stats = DistributionStats(
        unique_count=3,
        top_values=[("X", 100), ("Y", 50)],
        distribution={"X": 100, "Y": 50, "Z": 25},
    )
    d = stats.to_dict()
    assert d["unique_count"] == 3
    assert d["top_values"][0]["value"] == "X"
    assert d["top_values"][0]["count"] == 100


def test_dataset_profile_to_dict(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset, dataset_id="test_dataset")
    d = profile.to_dict()
    
    assert d["dataset_id"] == "test_dataset"
    assert d["total_records"] == 5
    assert "content_length_stats" in d
    assert "quality_score_stats" in d


def test_dataset_profile_to_json(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset, dataset_id="test_dataset")
    json_str = profile.to_json()
    
    data = json.loads(json_str)
    assert data["dataset_id"] == "test_dataset"
    assert data["total_records"] == 5


def test_dataset_profile_to_markdown(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset, dataset_id="test_dataset")
    markdown = profile.to_markdown()
    
    assert "# Dataset Profile: test_dataset" in markdown
    assert "Total Records:" in markdown
    assert "Content Statistics" in markdown


def test_profile_dataset(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset, dataset_id="test_ds")
    
    assert profile.dataset_id == "test_ds"
    assert profile.total_records == 5
    assert profile.content_length_stats is not None
    assert profile.quality_score_stats is not None


def test_profile_dataset_with_tokens(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset, dataset_id="test_ds", compute_tokens=True)
    
    assert profile.token_count_stats is not None
    assert profile.token_count_stats.count == 5


def test_content_length_stats(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert profile.content_length_stats.count == 5
    assert profile.content_length_stats.mean > 0
    assert profile.content_length_stats.min_value == 0  # Empty content


def test_quality_score_stats(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert profile.quality_score_stats.count == 5
    # Average: (85 + 90 + 65 + 45 + 80) / 5 = 73.0
    assert profile.quality_score_stats.mean == 73.0
    assert profile.quality_score_stats.min_value == 45.0
    assert profile.quality_score_stats.max_value == 90.0


def test_metadata_coverage(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert "source" in profile.metadata_coverage
    # 4 out of 5 records have source
    assert profile.metadata_coverage["source"] == 0.8


def test_category_distribution(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert profile.category_distribution is not None
    assert profile.category_distribution.unique_count == 3  # A, B, C
    # A appears 3 times
    assert profile.category_distribution.distribution["A"] == 3


def test_label_distribution(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert profile.label_distribution is not None
    assert profile.label_distribution.unique_count == 1
    assert profile.label_distribution.distribution["positive"] == 1


def test_empty_content_count(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert profile.empty_content_count == 1  # Record 4 has empty content


def test_duplicate_content_count(profiler, tmp_path):
    dataset = tmp_path / "duplicates.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "duplicate"}) + "\n")
        f.write(json.dumps({"id": "2", "content": "duplicate"}) + "\n")
        f.write(json.dumps({"id": "3", "content": "unique"}) + "\n")
    
    profile = profiler.profile_dataset(dataset)
    
    assert profile.duplicate_content_count == 1  # One duplicate


def test_outlier_detection(profiler, tmp_path):
    dataset = tmp_path / "outliers.jsonl"
    records = [
        {"id": str(i), "content": "x" * 100} for i in range(10)
    ]
    # Add an outlier with very long content
    records.append({"id": "outlier", "content": "x" * 10000})
    
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    profile = profiler.profile_dataset(dataset)
    
    assert len(profile.outliers) > 0
    assert "outlier" in profile.outliers


def test_field_types(profiler, sample_dataset):
    profile = profiler.profile_dataset(sample_dataset)
    
    assert "id" in profile.field_types
    assert profile.field_types["id"] == "string"
    assert profile.field_types["quality_score"] == "float"


def test_save_profile_json(profiler, sample_dataset, tmp_path):
    profile = profiler.profile_dataset(sample_dataset)
    output = tmp_path / "profile.json"
    
    profiler.save_profile(profile, output, format="json")
    
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
    assert data["dataset_id"] == profile.dataset_id


def test_save_profile_markdown(profiler, sample_dataset, tmp_path):
    profile = profiler.profile_dataset(sample_dataset)
    output = tmp_path / "profile.md"
    
    profiler.save_profile(profile, output, format="markdown")
    
    assert output.exists()
    content = output.read_text()
    assert "# Dataset Profile" in content


def test_compare_profiles(profiler, tmp_path):
    # Create baseline dataset
    baseline = tmp_path / "baseline.jsonl"
    with open(baseline, 'w') as f:
        for i in range(100):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 75.0}) + "\n")
    
    # Create current dataset
    current = tmp_path / "current.jsonl"
    with open(current, 'w') as f:
        for i in range(120):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 80.0}) + "\n")
    
    profile1 = profiler.profile_dataset(baseline, dataset_id="baseline")
    profile2 = profiler.profile_dataset(current, dataset_id="current")
    
    comparison = profiler.compare_profiles(profile1, profile2)
    
    assert comparison["record_count_diff"] == 20
    assert comparison["quality_mean_diff"] == 5.0


def test_profile_empty_dataset(profiler, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.touch()
    
    profile = profiler.profile_dataset(empty)
    
    assert profile.total_records == 0
    assert profile.content_length_stats is None


def test_percentile_calculation(profiler):
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    sorted_values = sorted(values)
    
    p50 = profiler._percentile(sorted_values, 50)
    p95 = profiler._percentile(sorted_values, 95)
    
    assert p50 == pytest.approx(5.5, rel=0.1)
    assert p95 == pytest.approx(9.55, rel=0.1)


def test_estimate_tokens(profiler):
    text = "This is a test sentence with multiple words"
    tokens = profiler._estimate_tokens(text)
    
    # Rough estimation: ~4 chars per token
    assert tokens > 0
    assert tokens < len(text)


def test_infer_field_types(profiler, tmp_path):
    dataset = tmp_path / "types.jsonl"
    record = {
        "id": "test",
        "count": 42,
        "score": 85.5,
        "active": True,
        "tags": ["a", "b"],
        "meta": {"key": "value"},
    }
    with open(dataset, 'w') as f:
        f.write(json.dumps(record) + "\n")
    
    profile = profiler.profile_dataset(dataset)
    
    assert profile.field_types["id"] == "string"
    assert profile.field_types["count"] == "integer"
    assert profile.field_types["score"] == "float"
    assert profile.field_types["active"] == "boolean"
    assert profile.field_types["tags"] == "array"
    assert profile.field_types["meta"] == "object"
