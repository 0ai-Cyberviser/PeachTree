"""
Tests for dataset_operations module (merge and split)
"""
from pathlib import Path
import pytest
import json
from peachtree.dataset_operations import (
    DatasetMerger,
    DatasetSplitter,
    MergeResult,
    SplitResult,
)


@pytest.fixture
def temp_datasets(tmp_path):
    """Create temporary test datasets"""
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    
    # Dataset 1
    ds1 = dataset_dir / "dataset1.jsonl"
    records1 = [
        {"id": "1", "content": "Content A", "source_repo": "repo1"},
        {"id": "2", "content": "Content B", "source_repo": "repo1"},
        {"id": "3", "content": "Content C", "source_repo": "repo1"},
    ]
    ds1.write_text("\n".join(json.dumps(r) for r in records1) + "\n")
    
    # Dataset 2
    ds2 = dataset_dir / "dataset2.jsonl"
    records2 = [
        {"id": "4", "content": "Content D", "source_repo": "repo2"},
        {"id": "5", "content": "Content E", "source_repo": "repo2"},
        {"id": "2", "content": "Content B", "source_repo": "repo2"},  # Duplicate
    ]
    ds2.write_text("\n".join(json.dumps(r) for r in records2) + "\n")
    
    return ds1, ds2


def test_merge_result_creation():
    """Test MergeResult dataclass"""
    result = MergeResult(
        output_path="output.jsonl",
        source_datasets=["ds1.jsonl", "ds2.jsonl"],
        total_records=100,
        records_per_source={"ds1.jsonl": 60, "ds2.jsonl": 40},
        duplicates_removed=5,
        merge_timestamp="2026-04-27T10:00:00",
    )
    
    assert result.total_records == 100
    assert result.duplicates_removed == 5
    assert result.to_dict()["total_records"] == 100


def test_split_result_creation():
    """Test SplitResult dataclass"""
    result = SplitResult(
        source_dataset="input.jsonl",
        output_files=["split-000.jsonl", "split-001.jsonl"],
        split_strategy="by_count",
        records_per_split={"split-000.jsonl": 50, "split-001.jsonl": 50},
        total_records=100,
        split_timestamp="2026-04-27T10:00:00",
    )
    
    assert result.total_records == 100
    assert len(result.output_files) == 2


def test_merge_basic(temp_datasets, tmp_path):
    """Test basic dataset merging"""
    ds1, ds2 = temp_datasets
    output = tmp_path / "merged.jsonl"
    
    merger = DatasetMerger()
    result = merger.merge([ds1, ds2], output)
    
    assert output.exists()
    assert result.total_records > 0
    assert len(result.source_datasets) == 2


def test_merge_with_deduplication(temp_datasets, tmp_path):
    """Test merging with duplicate removal"""
    ds1, ds2 = temp_datasets
    output = tmp_path / "merged-dedup.jsonl"
    
    merger = DatasetMerger()
    result = merger.merge([ds1, ds2], output, remove_duplicates=True)
    
    # Should remove 1 duplicate (Content B)
    assert result.duplicates_removed >= 1
    assert result.total_records == 5  # 6 total - 1 duplicate


def test_merge_keep_duplicates(temp_datasets, tmp_path):
    """Test merging while keeping duplicates"""
    ds1, ds2 = temp_datasets
    output = tmp_path / "merged-no-dedup.jsonl"
    
    merger = DatasetMerger()
    result = merger.merge([ds1, ds2], output, remove_duplicates=False)
    
    assert result.duplicates_removed == 0
    assert result.total_records == 6  # All records kept


def test_merge_preserve_metadata(temp_datasets, tmp_path):
    """Test merging with source metadata preservation"""
    ds1, ds2 = temp_datasets
    output = tmp_path / "merged-meta.jsonl"
    
    merger = DatasetMerger()
    result = merger.merge([ds1, ds2], output, preserve_source_metadata=True)
    
    # Check that merged records have metadata
    with open(output) as f:
        record = json.loads(f.readline())
        assert "metadata" in record
        assert "merge_source" in record["metadata"]


def test_split_by_count(temp_datasets, tmp_path):
    """Test splitting by count"""
    ds1, _ = temp_datasets
    output_dir = tmp_path / "splits"
    
    splitter = DatasetSplitter()
    result = splitter.split_by_count(ds1, output_dir, split_count=2)
    
    assert len(result.output_files) == 2
    assert result.total_records == 3
    
    # Verify splits exist
    for split_path in result.output_files:
        assert Path(split_path).exists()


def test_split_by_ratio(temp_datasets, tmp_path):
    """Test splitting by ratio (train/val/test)"""
    ds1, _ = temp_datasets
    output_dir = tmp_path / "ratio-splits"
    
    splitter = DatasetSplitter()
    result = splitter.split_by_ratio(
        ds1,
        output_dir,
        ratios={"train": 0.6, "val": 0.2, "test": 0.2},
        shuffle=False,
    )
    
    assert len(result.output_files) == 3
    assert "train" in result.to_json()
    assert "val" in result.to_json()
    assert "test" in result.to_json()


def test_split_by_ratio_with_shuffle(temp_datasets, tmp_path):
    """Test splitting by ratio with shuffling"""
    ds1, _ = temp_datasets
    output_dir = tmp_path / "shuffle-splits"
    
    splitter = DatasetSplitter()
    result = splitter.split_by_ratio(
        ds1,
        output_dir,
        ratios={"train": 0.7, "test": 0.3},
        shuffle=True,
        seed=42,
    )
    
    assert result.metadata["shuffle"] is True
    assert result.metadata["seed"] == 42


def test_split_by_size(temp_datasets, tmp_path):
    """Test splitting by maximum size"""
    # Create larger dataset
    large_ds = tmp_path / "large.jsonl"
    records = [{"id": str(i), "content": f"Content {i}"} for i in range(25)]
    large_ds.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    
    output_dir = tmp_path / "size-splits"
    
    splitter = DatasetSplitter()
    result = splitter.split_by_size(large_ds, output_dir, max_records_per_split=10)
    
    # Should create 3 splits (10, 10, 5)
    assert len(result.output_files) == 3
    assert result.total_records == 25


def test_split_by_ratio_validation(temp_datasets, tmp_path):
    """Test that ratios must sum to 1.0"""
    ds1, _ = temp_datasets
    output_dir = tmp_path / "invalid-splits"
    
    splitter = DatasetSplitter()
    
    with pytest.raises(ValueError, match="must sum to 1.0"):
        splitter.split_by_ratio(ds1, output_dir, ratios={"train": 0.5, "test": 0.3})


def test_merge_result_to_summary():
    """Test merge result markdown summary"""
    result = MergeResult(
        "out.jsonl",
        ["ds1.jsonl", "ds2.jsonl"],
        100,
        {"ds1.jsonl": 60, "ds2.jsonl": 40},
        5,
        "2026-04-27T10:00:00"
    )
    
    summary = result.to_summary()
    assert "# Dataset Merge Result" in summary
    assert "100" in summary
    assert "5" in summary


def test_split_result_to_summary():
    """Test split result markdown summary"""
    result = SplitResult(
        "input.jsonl",
        ["split-0.jsonl", "split-1.jsonl"],
        "by_count",
        {"split-0.jsonl": 50, "split-1.jsonl": 50},
        100,
        "2026-04-27T10:00:00"
    )
    
    summary = result.to_summary()
    assert "# Dataset Split Result" in summary
    assert "by_count" in summary
    assert "100" in summary


def test_merge_empty_datasets(tmp_path):
    """Test merging with empty dataset list"""
    merger = DatasetMerger()
    output = tmp_path / "empty-merge.jsonl"
    
    result = merger.merge([], output)
    
    assert result.total_records == 0
    assert len(result.source_datasets) == 0


def test_split_creates_output_directory(temp_datasets, tmp_path):
    """Test that split creates output directory if missing"""
    ds1, _ = temp_datasets
    output_dir = tmp_path / "nonexistent" / "splits"
    
    splitter = DatasetSplitter()
    result = splitter.split_by_count(ds1, output_dir, split_count=2)
    
    assert output_dir.exists()
    assert len(result.output_files) == 2
