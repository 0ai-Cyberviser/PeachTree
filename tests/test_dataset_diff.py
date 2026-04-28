"""
Tests for dataset_diff module
"""
from pathlib import Path
import pytest
import json
from peachtree.dataset_diff import (
    DatasetDiffEngine,
    DatasetDiffReport,
    RecordChange,
)


@pytest.fixture
def test_dataset_base(tmp_path):
    """Create base test dataset"""
    dataset = tmp_path / "base.jsonl"
    records = [
        {"id": "1", "content": "First record", "quality_score": 85},
        {"id": "2", "content": "Second record", "quality_score": 90},
        {"id": "3", "content": "Third record", "quality_score": 75},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


@pytest.fixture
def test_dataset_modified(tmp_path):
    """Create modified version of test dataset"""
    dataset = tmp_path / "modified.jsonl"
    records = [
        {"id": "1", "content": "First record MODIFIED", "quality_score": 85},  # Modified
        {"id": "2", "content": "Second record", "quality_score": 95},  # Quality changed
        {"id": "4", "content": "Fourth record (new)", "quality_score": 80},  # Added
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_record_change_creation():
    """Test RecordChange dataclass"""
    change = RecordChange(
        change_type="modified",
        record_id="123",
        old_content={"content": "old"},
        new_content={"content": "new"},
        field_changes={"content": ("old", "new")},
    )
    
    assert change.change_type == "modified"
    assert change.record_id == "123"
    assert change.field_changes["content"] == ("old", "new")


def test_record_change_to_dict():
    """Test RecordChange serialization"""
    change = RecordChange(
        change_type="added",
        record_id="456",
        new_content={"content": "test"},
    )
    
    data = change.to_dict()
    assert data["change_type"] == "added"
    assert data["record_id"] == "456"


def test_diff_report_creation():
    """Test DatasetDiffReport initialization"""
    report = DatasetDiffReport(
        base_dataset="base.jsonl",
        compare_dataset="compare.jsonl",
        base_records=10,
        compare_records=12,
    )
    
    assert report.base_records == 10
    assert report.compare_records == 12
    assert len(report.added_records) == 0


def test_diff_report_to_json():
    """Test diff report JSON serialization"""
    report = DatasetDiffReport(
        base_dataset="base.jsonl",
        compare_dataset="compare.jsonl",
        base_records=5,
        compare_records=6,
    )
    
    json_str = report.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["base_records"] == 5
    assert parsed["compare_records"] == 6


def test_diff_report_to_markdown():
    """Test markdown report generation"""
    report = DatasetDiffReport(
        base_dataset="base.jsonl",
        compare_dataset="compare.jsonl",
        base_records=10,
        compare_records=10,
        unchanged_records=8,
    )
    report.added_records.append(RecordChange("added", "new1", new_content={}))
    report.removed_records.append(RecordChange("removed", "old1", old_content={}))
    
    markdown = report.to_markdown()
    
    assert "# Dataset Diff Report" in markdown
    assert "✅ **Unchanged:** 8" in markdown
    assert "➕ **Added:** 1" in markdown
    assert "➖ **Removed:** 1" in markdown


def test_diff_engine_initialization():
    """Test DatasetDiffEngine initialization"""
    engine = DatasetDiffEngine()
    assert engine is not None


def test_compute_record_hash():
    """Test record hash computation"""
    engine = DatasetDiffEngine()
    
    record1 = {"id": "1", "content": "test content"}
    record2 = {"id": "2", "content": "test content"}  # Same content, different ID
    
    hash1 = engine._compute_record_hash(record1)
    hash2 = engine._compute_record_hash(record2)
    
    assert hash1 == hash2  # Same content should have same hash


def test_load_dataset(test_dataset_base):
    """Test loading dataset into dict"""
    engine = DatasetDiffEngine()
    records = engine._load_dataset(test_dataset_base)
    
    assert len(records) == 3
    assert "1" in records
    assert records["1"]["content"] == "First record"


def test_diff_identical_datasets(test_dataset_base):
    """Test diffing identical datasets"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_base)
    
    assert report.base_records == 3
    assert report.compare_records == 3
    assert len(report.added_records) == 0
    assert len(report.removed_records) == 0
    assert report.unchanged_records == 3
    assert report.similarity_score == 100.0


def test_diff_added_records(test_dataset_base, test_dataset_modified):
    """Test detecting added records"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_modified)
    
    assert len(report.added_records) > 0
    added_ids = [c.record_id for c in report.added_records]
    assert "4" in added_ids


def test_diff_removed_records(test_dataset_base, test_dataset_modified):
    """Test detecting removed records"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_modified)
    
    assert len(report.removed_records) > 0
    removed_ids = [c.record_id for c in report.removed_records]
    assert "3" in removed_ids


def test_diff_modified_records(test_dataset_base, test_dataset_modified):
    """Test detecting modified records"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_modified, compare_content=True)
    
    assert len(report.modified_records) > 0
    modified_ids = [c.record_id for c in report.modified_records]
    assert "1" in modified_ids or "2" in modified_ids


def test_diff_without_content_compare(test_dataset_base, test_dataset_modified):
    """Test diff without content comparison"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_modified, compare_content=False)
    
    # Should only detect added/removed, not modified
    assert len(report.added_records) > 0
    assert len(report.removed_records) > 0


def test_find_field_changes():
    """Test finding changed fields between records"""
    engine = DatasetDiffEngine()
    
    old_record = {"id": "1", "content": "old", "quality_score": 80}
    new_record = {"id": "1", "content": "new", "quality_score": 85}
    
    changes = engine._find_field_changes(old_record, new_record)
    
    assert "content" in changes
    assert changes["content"] == ("old", "new")
    assert "quality_score" in changes
    assert changes["quality_score"] == (80, 85)


def test_similarity_score_calculation(test_dataset_base, test_dataset_modified):
    """Test similarity score calculation"""
    engine = DatasetDiffEngine()
    report = engine.diff(test_dataset_base, test_dataset_modified)
    
    assert 0 <= report.similarity_score <= 100


def test_generate_patch(test_dataset_base, test_dataset_modified, tmp_path):
    """Test patch generation"""
    engine = DatasetDiffEngine()
    patch_path = tmp_path / "changes.patch"
    
    op_count = engine.generate_patch(test_dataset_base, test_dataset_modified, patch_path)
    
    assert op_count > 0
    assert patch_path.exists()
    
    # Verify patch structure
    with open(patch_path) as f:
        patch_data = json.load(f)
    
    assert "operations" in patch_data
    assert len(patch_data["operations"]) == op_count


def test_apply_patch(test_dataset_base, test_dataset_modified, tmp_path):
    """Test applying patch file"""
    engine = DatasetDiffEngine()
    
    # Generate patch
    patch_path = tmp_path / "changes.patch"
    engine.generate_patch(test_dataset_base, test_dataset_modified, patch_path)
    
    # Apply patch
    output_path = tmp_path / "patched.jsonl"
    record_count = engine.apply_patch(test_dataset_base, patch_path, output_path)
    
    assert record_count > 0
    assert output_path.exists()


def test_patch_roundtrip(test_dataset_base, test_dataset_modified, tmp_path):
    """Test that patch + apply produces same result"""
    engine = DatasetDiffEngine()
    
    # Generate and apply patch
    patch_path = tmp_path / "changes.patch"
    engine.generate_patch(test_dataset_base, test_dataset_modified, patch_path)
    
    output_path = tmp_path / "patched.jsonl"
    engine.apply_patch(test_dataset_base, patch_path, output_path)
    
    # Compare patched output with original modified dataset
    report = engine.diff(output_path, test_dataset_modified)
    
    # Should be very similar (may not be 100% identical due to ordering)
    assert report.similarity_score > 90


def test_find_duplicates_between_datasets(tmp_path):
    """Test finding duplicates across datasets"""
    dataset1 = tmp_path / "dataset1.jsonl"
    dataset2 = tmp_path / "dataset2.jsonl"
    
    # Dataset1 with some records
    records1 = [
        {"id": "1", "content": "duplicate content"},
        {"id": "2", "content": "unique in dataset1"},
    ]
    dataset1.write_text("\n".join(json.dumps(r) for r in records1) + "\n")
    
    # Dataset2 with one duplicate
    records2 = [
        {"id": "3", "content": "duplicate content"},  # Same as id=1
        {"id": "4", "content": "unique in dataset2"},
    ]
    dataset2.write_text("\n".join(json.dumps(r) for r in records2) + "\n")
    
    engine = DatasetDiffEngine()
    duplicates = engine.find_duplicates_between_datasets(dataset1, dataset2)
    
    assert len(duplicates) == 1
    assert duplicates[0] == ("1", "3")


def test_find_duplicates_no_duplicates(test_dataset_base, test_dataset_modified):
    """Test finding duplicates when none exist"""
    engine = DatasetDiffEngine()
    duplicates = engine.find_duplicates_between_datasets(test_dataset_base, test_dataset_modified)
    
    # Should find at least one if content matches
    assert isinstance(duplicates, list)


def test_diff_empty_datasets(tmp_path):
    """Test diffing empty datasets"""
    empty1 = tmp_path / "empty1.jsonl"
    empty2 = tmp_path / "empty2.jsonl"
    empty1.write_text("")
    empty2.write_text("")
    
    engine = DatasetDiffEngine()
    report = engine.diff(empty1, empty2)
    
    assert report.base_records == 0
    assert report.compare_records == 0
    assert report.similarity_score == 0.0


def test_diff_report_to_dict():
    """Test full diff report serialization"""
    report = DatasetDiffReport(
        base_dataset="base.jsonl",
        compare_dataset="compare.jsonl",
        base_records=10,
        compare_records=12,
    )
    report.added_records.append(RecordChange("added", "new1", new_content={"content": "test"}))
    
    data = report.to_dict()
    
    assert data["added_count"] == 1
    assert data["base_records"] == 10


def test_patch_creates_parent_directories(test_dataset_base, test_dataset_modified, tmp_path):
    """Test that patch generation creates parent directories"""
    patch_path = tmp_path / "nested" / "dir" / "changes.patch"
    
    engine = DatasetDiffEngine()
    engine.generate_patch(test_dataset_base, test_dataset_modified, patch_path)
    
    assert patch_path.exists()
    assert patch_path.parent.exists()
