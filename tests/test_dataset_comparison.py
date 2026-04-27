"""
Tests for dataset_comparison module
"""
from pathlib import Path
import pytest
import json
from peachtree.dataset_comparison import (
    DatasetComparator,
    DatasetComparison,
    DatasetMetrics,
)


@pytest.fixture
def temp_datasets(tmp_path):
    """Create two temporary datasets - baseline and improved"""
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Baseline dataset with some quality issues
    baseline_file = dataset_dir / "baseline.jsonl"
    baseline_records = []
    for i in range(10):
        record = {
            "id": f"rec-{i}",
            "content": f"Sample content {i}",
            "source_repo": "test-repo",
            "source_path": f"test{i}.txt",
            "digest": f"sha256-{i}",
        }
        baseline_records.append(json.dumps(record))
    # Add some duplicates
    baseline_records.append(json.dumps(baseline_records[0]))  # Duplicate
    baseline_file.write_text("\n".join(baseline_records) + "\n")
    
    # Improved dataset (deduplicated, better quality)
    improved_file = dataset_dir / "improved.jsonl"
    improved_records = []
    for i in range(10):  # No duplicates
        record = {
            "id": f"rec-{i}",
            "content": f"High quality improved content {i}",
            "source_repo": "test-repo",
            "source_path": f"test{i}.txt",
            "digest": f"sha256-{i}",
        }
        improved_records.append(json.dumps(record))
    improved_file.write_text("\n".join(improved_records) + "\n")
    
    return baseline_file, improved_file


def test_dataset_metrics_creation():
    """Test DatasetMetrics dataclass creation"""
    metrics = DatasetMetrics(
        dataset_path="test.jsonl",
        record_count=100,
        quality_score=85.0,
        duplicate_ratio=0.05,
        provenance_coverage=0.95,
        safety_coverage=0.98,
        total_size_bytes=102400,
    )
    
    assert metrics.dataset_path == "test.jsonl"
    assert metrics.record_count == 100
    assert metrics.quality_score == 85.0
    
    # Test to_dict
    metrics_dict = metrics.to_dict()
    assert metrics_dict["record_count"] == 100
    assert metrics_dict["quality_score"] == 85.0


def test_dataset_comparison_creation():
    """Test DatasetComparison dataclass creation"""
    baseline_metrics = DatasetMetrics(
        "baseline.jsonl", 100, 70.0, 0.15, 0.80, 0.85, 100000
    )
    candidate_metrics = DatasetMetrics(
        "candidate.jsonl", 95, 85.0, 0.05, 0.95, 0.98, 95000
    )
    
    comparison = DatasetComparison(
        baseline_path="baseline.jsonl",
        candidate_path="candidate.jsonl",
        timestamp="2026-04-27T10:00:00",
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        record_count_delta=-5,
        quality_score_delta=15.0,
        duplicate_ratio_delta=-0.10,
        provenance_delta=0.15,
        safety_delta=0.13,
        size_delta_bytes=-5000,
        improvement_percentage=12.5,
    )
    
    assert comparison.baseline_path == "baseline.jsonl"
    assert comparison.quality_score_delta == 15.0
    assert comparison.improvement_percentage == 12.5


def test_dataset_comparison_is_improvement():
    """Test improvement detection logic"""
    baseline_metrics = DatasetMetrics(
        "baseline.jsonl", 100, 70.0, 0.15, 0.80, 0.85, 100000
    )
    
    # Better candidate
    better_metrics = DatasetMetrics(
        "better.jsonl", 100, 85.0, 0.05, 0.95, 0.98, 100000
    )
    
    comparison_better = DatasetComparison(
        "baseline.jsonl", "better.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, better_metrics,
        0, 15.0, -0.10, 0.15, 0.13, 0, 12.5
    )
    
    assert comparison_better.is_improvement is True
    assert comparison_better.is_significant_improvement is True
    
    # Worse candidate
    worse_metrics = DatasetMetrics(
        "worse.jsonl", 100, 60.0, 0.25, 0.70, 0.75, 100000
    )
    
    comparison_worse = DatasetComparison(
        "baseline.jsonl", "worse.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, worse_metrics,
        0, -10.0, 0.10, -0.10, -0.10, 0, -8.0
    )
    
    assert comparison_worse.is_improvement is False
    assert comparison_worse.is_significant_improvement is False


def test_dataset_comparison_to_dict():
    """Test to_dict method"""
    baseline_metrics = DatasetMetrics(
        "baseline.jsonl", 100, 70.0, 0.15, 0.80, 0.85, 100000
    )
    candidate_metrics = DatasetMetrics(
        "candidate.jsonl", 95, 85.0, 0.05, 0.95, 0.98, 95000
    )
    
    comparison = DatasetComparison(
        "baseline.jsonl", "candidate.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, candidate_metrics,
        -5, 15.0, -0.10, 0.15, 0.13, -5000, 12.5
    )
    
    comp_dict = comparison.to_dict()
    
    assert "baseline_path" in comp_dict
    assert "candidate_path" in comp_dict
    assert "deltas" in comp_dict
    assert comp_dict["deltas"]["quality_score"] == 15.0
    assert comp_dict["is_improvement"] is True


def test_dataset_comparison_to_json():
    """Test JSON serialization"""
    baseline_metrics = DatasetMetrics(
        "baseline.jsonl", 100, 70.0, 0.15, 0.80, 0.85, 100000
    )
    candidate_metrics = DatasetMetrics(
        "candidate.jsonl", 95, 85.0, 0.05, 0.95, 0.98, 95000
    )
    
    comparison = DatasetComparison(
        "baseline.jsonl", "candidate.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, candidate_metrics,
        -5, 15.0, -0.10, 0.15, 0.13, -5000, 12.5
    )
    
    json_str = comparison.to_json()
    
    assert "baseline.jsonl" in json_str
    assert "15.0" in json_str
    assert "12.5" in json_str
    
    # Verify it's valid JSON
    json_data = json.loads(json_str)
    assert json_data["improvement_percentage"] == 12.5


def test_dataset_comparison_to_markdown():
    """Test Markdown generation"""
    baseline_metrics = DatasetMetrics(
        "baseline.jsonl", 100, 70.0, 0.15, 0.80, 0.85, 100000
    )
    candidate_metrics = DatasetMetrics(
        "candidate.jsonl", 95, 85.0, 0.05, 0.95, 0.98, 95000
    )
    
    comparison = DatasetComparison(
        "baseline.jsonl", "candidate.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, candidate_metrics,
        -5, 15.0, -0.10, 0.15, 0.13, -5000, 12.5
    )
    
    md = comparison.to_markdown()
    
    # Check structure
    assert "# Dataset Comparison Report" in md
    assert "## Datasets" in md
    assert "## Metrics Comparison" in md
    assert "## Summary" in md
    
    # Check emojis
    assert "📈" in md or "📉" in md
    assert "⭐" in md or "⚠️" in md
    
    # Check data
    assert "baseline.jsonl" in md
    assert "candidate.jsonl" in md
    assert "+12.5%" in md


def test_comparator_initialization():
    """Test DatasetComparator initialization"""
    comparator = DatasetComparator()
    
    assert comparator.health_monitor is not None
    assert comparator.quality_scorer is not None
    assert comparator.deduplicator is not None


def test_comparator_collect_metrics(temp_datasets):
    """Test metrics collection for a dataset"""
    baseline_file, improved_file = temp_datasets
    
    comparator = DatasetComparator()
    metrics = comparator.collect_metrics(baseline_file)
    
    assert isinstance(metrics, DatasetMetrics)
    assert metrics.dataset_path == str(baseline_file)
    assert metrics.record_count >= 0
    assert 0.0 <= metrics.quality_score <= 100.0
    assert 0.0 <= metrics.duplicate_ratio <= 1.0
    assert metrics.total_size_bytes > 0


def test_comparator_compare(temp_datasets):
    """Test dataset comparison"""
    baseline_file, improved_file = temp_datasets
    
    comparator = DatasetComparator()
    comparison = comparator.compare(baseline_file, improved_file)
    
    assert isinstance(comparison, DatasetComparison)
    assert comparison.baseline_path == str(baseline_file)
    assert comparison.candidate_path == str(improved_file)
    
    # Improved should have fewer duplicates
    assert comparison.duplicate_ratio_delta <= 0
    
    # Should have improvement metrics
    assert isinstance(comparison.improvement_percentage, float)


def test_comparator_write_comparison(temp_datasets, tmp_path):
    """Test writing comparison to files"""
    baseline_file, improved_file = temp_datasets
    
    comparator = DatasetComparator()
    comparison = comparator.compare(baseline_file, improved_file)
    
    # Write JSON
    json_path = tmp_path / "comparison.json"
    comparator.write_comparison(comparison, json_path=json_path)
    
    assert json_path.exists()
    json_data = json.loads(json_path.read_text())
    assert "baseline_path" in json_data
    
    # Write markdown
    md_path = tmp_path / "comparison.md"
    comparator.write_comparison(comparison, markdown_path=md_path)
    
    assert md_path.exists()
    md_content = md_path.read_text()
    assert "# Dataset Comparison Report" in md_content


def test_percent_change_calculation():
    """Test percentage change calculation"""
    # Normal case
    change = DatasetComparison._percent_change(100.0, 120.0)
    assert change == 20.0
    
    # Decrease
    change = DatasetComparison._percent_change(100.0, 80.0)
    assert change == -20.0
    
    # No change
    change = DatasetComparison._percent_change(100.0, 100.0)
    assert change == 0.0
    
    # Zero baseline
    change = DatasetComparison._percent_change(0.0, 50.0)
    assert change == 100.0
    
    # Both zero
    change = DatasetComparison._percent_change(0.0, 0.0)
    assert change == 0.0


def test_comparison_markdown_formatting():
    """Test markdown table formatting"""
    baseline_metrics = DatasetMetrics(
        "data.jsonl", 1000000, 92.5, 0.02, 0.98, 0.99, 5242880
    )
    candidate_metrics = DatasetMetrics(
        "improved.jsonl", 1050000, 95.8, 0.01, 0.99, 0.995, 5500000
    )
    
    comparison = DatasetComparison(
        "data.jsonl", "improved.jsonl", "2026-04-27T10:00:00",
        baseline_metrics, candidate_metrics,
        50000, 3.3, -0.01, 0.01, 0.005, 257120, 3.37
    )
    
    md = comparison.to_markdown()
    
    # Check number formatting
    assert "1,000,000" in md  # Large numbers formatted
    assert "95.8" in md  # Decimal quality score
    assert "1.0%" in md or "2.0%" in md  # Percentages
    
    # Check improvement indicators
    assert "IMPROVEMENT" in md or "SIGNIFICANT" in md


def test_comparison_improvement_calculation():
    """Test weighted improvement percentage calculation"""
    # Scenario 1: Big quality improvement, small dup improvement
    baseline1 = DatasetMetrics("b.jsonl", 100, 60.0, 0.20, 0.80, 0.85, 100000)
    candidate1 = DatasetMetrics("c.jsonl", 100, 80.0, 0.18, 0.82, 0.87, 100000)
    
    comparison1 = DatasetComparison(
        "b.jsonl", "c.jsonl", "2026-04-27T10:00:00",
        baseline1, candidate1,
        0, 20.0, -0.02, 0.02, 0.02, 0,
        # Quality: 20*0.4=8, Dup: 2*0.2=0.4, Prov: 2*0.2=0.4, Safety: 2*0.2=0.4 = 9.2
        9.2
    )
    
    # Should be improvement due to quality increase
    assert comparison1.is_improvement is True
    
    # Scenario 2: Small changes, not significant
    baseline2 = DatasetMetrics("b.jsonl", 100, 85.0, 0.05, 0.95, 0.98, 100000)
    candidate2 = DatasetMetrics("c.jsonl", 100, 86.0, 0.05, 0.95, 0.98, 100000)
    
    comparison2 = DatasetComparison(
        "b.jsonl", "c.jsonl", "2026-04-27T10:00:00",
        baseline2, candidate2,
        0, 1.0, 0.0, 0.0, 0.0, 0,
        0.4  # Only quality improved slightly
    )
    
    # Should be improvement but not significant
    assert comparison2.is_improvement is True
    assert comparison2.is_significant_improvement is False
