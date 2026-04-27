"""
Tests for incremental_update module
"""
from pathlib import Path
import pytest
import json
from peachtree.incremental_update import (
    IncrementalUpdater,
    DatasetDelta,
    IncrementalUpdateResult,
    ChangeTracker,
)


@pytest.fixture
def baseline_dataset(tmp_path):
    """Create baseline dataset"""
    dataset = tmp_path / "baseline.jsonl"
    records = [
        {"id": "1", "content": "Record 1", "version": 1},
        {"id": "2", "content": "Record 2", "version": 1},
        {"id": "3", "content": "Record 3", "version": 1},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


@pytest.fixture
def updated_dataset(tmp_path):
    """Create updated dataset with changes"""
    dataset = tmp_path / "updated.jsonl"
    records = [
        {"id": "1", "content": "Record 1 UPDATED", "version": 2},  # Modified
        {"id": "2", "content": "Record 2", "version": 1},  # Unchanged
        {"id": "4", "content": "Record 4 NEW", "version": 1},  # Added
        # Record 3 deleted
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_dataset_delta_creation():
    """Test DatasetDelta initialization"""
    delta = DatasetDelta(
        additions=[{"id": "4"}],
        modifications=[{"id": "1"}],
        deletions=["3"],
    )
    
    assert len(delta) == 3
    assert len(delta.additions) == 1
    assert len(delta.modifications) == 1
    assert len(delta.deletions) == 1


def test_dataset_delta_to_json():
    """Test delta JSON serialization"""
    delta = DatasetDelta(additions=[{"id": "new"}])
    json_str = delta.to_json()
    
    parsed = json.loads(json_str)
    assert "additions" in parsed
    assert len(parsed["additions"]) == 1


def test_incremental_update_result_creation():
    """Test IncrementalUpdateResult dataclass"""
    result = IncrementalUpdateResult(
        dataset_path="test.jsonl",
        base_records=10,
        additions=2,
        modifications=3,
        deletions=1,
        final_records=11,
        update_timestamp="2026-04-27T10:00:00",
        delta_applied=True,
    )
    
    assert result.final_records == 11
    assert result.delta_applied


def test_incremental_update_result_to_summary():
    """Test update result markdown summary"""
    result = IncrementalUpdateResult(
        "test.jsonl", 100, 10, 5, 3, 107, "2026-04-27T10:00:00", True
    )
    
    summary = result.to_summary()
    
    assert "# Incremental Update Result" in summary
    assert "+10" in summary  # Additions
    assert "~5" in summary   # Modifications
    assert "-3" in summary   # Deletions


def test_incremental_updater_initialization():
    """Test updater initialization"""
    updater = IncrementalUpdater(id_field="custom_id")
    
    assert updater.id_field == "custom_id"


def test_compute_record_hash():
    """Test record hashing"""
    updater = IncrementalUpdater()
    
    record1 = {"id": "1", "content": "same"}
    record2 = {"id": "2", "content": "same"}
    
    # Same content, different ID = same hash
    hash1 = updater._compute_record_hash(record1)
    hash2 = updater._compute_record_hash(record2)
    
    assert hash1 == hash2


def test_detect_changes_additions(baseline_dataset, updated_dataset):
    """Test detecting additions"""
    updater = IncrementalUpdater()
    delta = updater.detect_changes(baseline_dataset, updated_dataset)
    
    assert len(delta.additions) == 1
    assert delta.additions[0]["id"] == "4"


def test_detect_changes_modifications(baseline_dataset, updated_dataset):
    """Test detecting modifications"""
    updater = IncrementalUpdater()
    delta = updater.detect_changes(baseline_dataset, updated_dataset)
    
    assert len(delta.modifications) == 1
    assert delta.modifications[0]["id"] == "1"
    assert "UPDATED" in delta.modifications[0]["content"]


def test_detect_changes_deletions(baseline_dataset, updated_dataset):
    """Test detecting deletions"""
    updater = IncrementalUpdater()
    delta = updater.detect_changes(baseline_dataset, updated_dataset)
    
    assert len(delta.deletions) == 1
    assert "3" in delta.deletions


def test_detect_changes_unchanged_ignored(baseline_dataset, updated_dataset):
    """Test that unchanged records aren't marked as modified"""
    updater = IncrementalUpdater()
    delta = updater.detect_changes(baseline_dataset, updated_dataset)
    
    # Record 2 is unchanged - should not be in additions or modifications
    modification_ids = [m["id"] for m in delta.modifications]
    addition_ids = [a["id"] for a in delta.additions]
    
    assert "2" not in modification_ids
    assert "2" not in addition_ids


def test_apply_delta_additions(baseline_dataset, tmp_path):
    """Test applying additions"""
    updater = IncrementalUpdater()
    output = tmp_path / "output.jsonl"
    
    delta = DatasetDelta(additions=[{"id": "4", "content": "New"}])
    
    result = updater.apply_delta(baseline_dataset, delta, output)
    
    assert result.additions == 1
    assert result.final_records == 4


def test_apply_delta_modifications(baseline_dataset, tmp_path):
    """Test applying modifications"""
    updater = IncrementalUpdater()
    output = tmp_path / "output.jsonl"
    
    delta = DatasetDelta(modifications=[{"id": "1", "content": "Updated"}])
    
    result = updater.apply_delta(baseline_dataset, delta, output)
    
    assert result.modifications == 1
    
    # Verify content was updated
    with open(output) as f:
        records = [json.loads(line) for line in f if line.strip()]
    
    updated_record = next(r for r in records if r["id"] == "1")
    assert updated_record["content"] == "Updated"


def test_apply_delta_deletions(baseline_dataset, tmp_path):
    """Test applying deletions"""
    updater = IncrementalUpdater()
    output = tmp_path / "output.jsonl"
    
    delta = DatasetDelta(deletions=["2"])
    
    result = updater.apply_delta(baseline_dataset, delta, output)
    
    assert result.deletions == 1
    assert result.final_records == 2


def test_apply_delta_combined(baseline_dataset, tmp_path):
    """Test applying combined changes"""
    updater = IncrementalUpdater()
    output = tmp_path / "output.jsonl"
    
    delta = DatasetDelta(
        additions=[{"id": "4", "content": "New"}],
        modifications=[{"id": "1", "content": "Modified"}],
        deletions=["3"],
    )
    
    result = updater.apply_delta(baseline_dataset, delta, output)
    
    assert result.additions == 1
    assert result.modifications == 1
    assert result.deletions == 1
    assert result.final_records == 3  # 3 - 1 + 1 = 3


def test_apply_delta_in_place(baseline_dataset):
    """Test applying delta in-place (no output path)"""
    updater = IncrementalUpdater()
    
    delta = DatasetDelta(additions=[{"id": "4", "content": "New"}])
    
    result = updater.apply_delta(baseline_dataset, delta)
    
    # Should update baseline file
    assert result.dataset_path == str(baseline_dataset)
    assert result.final_records == 4


def test_update_from_source(baseline_dataset, updated_dataset, tmp_path):
    """Test automatic update from source dataset"""
    updater = IncrementalUpdater()
    output = tmp_path / "merged.jsonl"
    
    result = updater.update_from_source(baseline_dataset, updated_dataset, output)
    
    # Should have detected and applied all changes
    assert result.additions == 1
    assert result.modifications == 1
    assert result.deletions == 1


def test_save_and_load_delta(tmp_path):
    """Test saving and loading delta files"""
    updater = IncrementalUpdater()
    delta_path = tmp_path / "delta.json"
    
    delta = DatasetDelta(
        additions=[{"id": "new"}],
        deletions=["old"],
    )
    
    updater.save_delta(delta, delta_path)
    
    assert delta_path.exists()
    
    loaded_delta = updater.load_delta(delta_path)
    
    assert len(loaded_delta.additions) == 1
    assert len(loaded_delta.deletions) == 1


def test_change_tracker_initialization(tmp_path):
    """Test change tracker initialization"""
    tracker = ChangeTracker(tmp_path / "history")
    
    assert tracker.history_dir.exists()


def test_change_tracker_record_change(tmp_path):
    """Test recording changes to history"""
    tracker = ChangeTracker(tmp_path / "history")
    
    delta = DatasetDelta(additions=[{"id": "1"}])
    
    filepath = tracker.record_change("test-dataset", delta, metadata={"version": "1.0"})
    
    assert Path(filepath).exists()
    assert "test-dataset" in filepath


def test_change_tracker_get_history(tmp_path):
    """Test retrieving change history"""
    tracker = ChangeTracker(tmp_path / "history")
    
    delta1 = DatasetDelta(additions=[{"id": "1"}])
    delta2 = DatasetDelta(modifications=[{"id": "1"}])
    
    tracker.record_change("test-dataset", delta1)
    tracker.record_change("test-dataset", delta2)
    
    history = tracker.get_history("test-dataset")
    
    assert len(history) == 2


def test_change_tracker_generate_changelog(tmp_path):
    """Test changelog generation"""
    tracker = ChangeTracker(tmp_path / "history")
    
    delta = DatasetDelta(additions=[{"id": "1"}], modifications=[{"id": "2"}], deletions=["3"])
    tracker.record_change("test-dataset", delta)
    
    changelog = tracker.generate_changelog("test-dataset")
    
    assert "# test-dataset - Change Log" in changelog
    assert "+1" in changelog  # 1 addition
    assert "~1" in changelog  # 1 modification
    assert "-1" in changelog  # 1 deletion


def test_change_tracker_save_changelog_to_file(tmp_path):
    """Test saving changelog to file"""
    tracker = ChangeTracker(tmp_path / "history")
    delta = DatasetDelta(additions=[{"id": "1"}])
    tracker.record_change("test-dataset", delta)
    
    output = tmp_path / "changelog.md"
    changelog = tracker.generate_changelog("test-dataset", output_path=output)
    
    assert output.exists()
    assert output.read_text() == changelog + "\n"


def test_custom_id_field(tmp_path):
    """Test using custom ID field"""
    baseline = tmp_path / "baseline.jsonl"
    updated = tmp_path / "updated.jsonl"
    
    baseline.write_text(json.dumps({"custom_id": "1", "data": "old"}) + "\n")
    updated.write_text(json.dumps({"custom_id": "1", "data": "new"}) + "\n")
    
    updater = IncrementalUpdater(id_field="custom_id")
    delta = updater.detect_changes(baseline, updated)
    
    assert len(delta.modifications) == 1
