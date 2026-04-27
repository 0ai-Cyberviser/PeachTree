"""Tests for backup_restore module"""
import json
from pathlib import Path
import pytest

from peachtree.backup_restore import (
    DatasetBackupRestore,
    BackupMetadata,
    RestoreResult,
    BackupInventory,
)


@pytest.fixture
def backup_restore(tmp_path):
    return DatasetBackupRestore(backup_dir=tmp_path / "backups")


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "content": "First record", "quality_score": 85.0},
        {"id": "2", "content": "Second record", "quality_score": 90.0},
        {"id": "3", "content": "Third record", "quality_score": 75.0},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_backup_metadata_creation():
    metadata = BackupMetadata(
        backup_id="test_backup_v1",
        dataset_id="test_dataset",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
        record_count=100,
        total_bytes=5000,
        checksum="abc123",
    )
    assert metadata.backup_id == "test_backup_v1"
    assert metadata.backup_type == "full"
    assert metadata.record_count == 100


def test_backup_metadata_to_dict():
    metadata = BackupMetadata(
        backup_id="test",
        dataset_id="dataset",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    )
    d = metadata.to_dict()
    assert d["backup_id"] == "test"
    assert d["backup_type"] == "full"


def test_backup_metadata_to_json():
    metadata = BackupMetadata(
        backup_id="test",
        dataset_id="dataset",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    )
    json_str = metadata.to_json()
    data = json.loads(json_str)
    assert data["backup_id"] == "test"


def test_restore_result_creation():
    result = RestoreResult(
        backup_id="test_backup",
        dataset_path="/path/to/dataset.jsonl",
        records_restored=100,
        restore_timestamp="2024-01-01T00:00:00",
        checksum_verified=True,
    )
    assert result.backup_id == "test_backup"
    assert result.records_restored == 100
    assert result.checksum_verified is True


def test_backup_inventory_creation():
    inventory = BackupInventory(dataset_id="test_dataset")
    assert inventory.dataset_id == "test_dataset"
    assert len(inventory.backups) == 0


def test_backup_inventory_add_backup():
    inventory = BackupInventory(dataset_id="test")
    metadata = BackupMetadata(
        backup_id="backup1",
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    )
    
    inventory.add_backup(metadata)
    assert len(inventory.backups) == 1
    assert inventory.backups[0].backup_id == "backup1"


def test_backup_inventory_get_backup():
    inventory = BackupInventory(dataset_id="test")
    metadata = BackupMetadata(
        backup_id="backup1",
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    )
    inventory.add_backup(metadata)
    
    found = inventory.get_backup("backup1")
    assert found is not None
    assert found.backup_id == "backup1"
    
    not_found = inventory.get_backup("missing")
    assert not_found is None


def test_backup_inventory_get_latest_backup():
    inventory = BackupInventory(dataset_id="test")
    
    backup1 = BackupMetadata(
        backup_id="backup1",
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    )
    backup2 = BackupMetadata(
        backup_id="backup2",
        dataset_id="test",
        timestamp="2024-01-02T00:00:00",
        backup_type="incremental",
    )
    
    inventory.add_backup(backup1)
    inventory.add_backup(backup2)
    
    latest = inventory.get_latest_backup()
    assert latest is not None
    assert latest.backup_id == "backup2"


def test_create_full_backup(backup_restore, sample_dataset):
    metadata = backup_restore.create_full_backup(
        sample_dataset,
        dataset_id="test_dataset",
        tags={"version": "1.0"},
    )
    
    assert metadata.dataset_id == "test_dataset"
    assert metadata.backup_type == "full"
    assert metadata.record_count == 3
    assert metadata.total_bytes > 0
    assert metadata.checksum != ""
    assert metadata.tags["version"] == "1.0"


def test_list_backups(backup_restore, sample_dataset):
    # Create multiple backups
    backup_restore.create_full_backup(sample_dataset, "test_dataset")
    backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    inventory = backup_restore.list_backups("test_dataset")
    
    assert inventory.dataset_id == "test_dataset"
    assert len(inventory.backups) == 2
    # Should be sorted by timestamp (newest first)
    assert inventory.backups[0].timestamp >= inventory.backups[1].timestamp


def test_restore_backup(backup_restore, sample_dataset, tmp_path):
    # Create backup
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Restore to new location
    restored_path = tmp_path / "restored.jsonl"
    result = backup_restore.restore_backup(
        metadata.backup_id,
        "test_dataset",
        restored_path,
        verify_checksum=True,
    )
    
    assert result.backup_id == metadata.backup_id
    assert result.records_restored == 3
    assert result.checksum_verified is True
    assert Path(result.dataset_path).exists()
    
    # Verify restored content
    with open(restored_path) as f:
        restored_records = [json.loads(line) for line in f if line.strip()]
    assert len(restored_records) == 3


def test_restore_backup_checksum_mismatch(backup_restore, sample_dataset, tmp_path):
    # Create backup
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Corrupt the backup file
    dataset_backup_dir = backup_restore._get_dataset_backup_dir("test_dataset")
    backup_file = dataset_backup_dir / f"{metadata.backup_id}.jsonl"
    with open(backup_file, 'a') as f:
        f.write("corrupted data\n")
    
    # Attempt restore with checksum verification
    restored_path = tmp_path / "restored.jsonl"
    
    with pytest.raises(ValueError, match="Checksum mismatch"):
        backup_restore.restore_backup(
            metadata.backup_id,
            "test_dataset",
            restored_path,
            verify_checksum=True,
        )


def test_validate_backup(backup_restore, sample_dataset):
    # Create backup
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Validate backup
    valid = backup_restore.validate_backup(metadata.backup_id, "test_dataset")
    assert valid is True


def test_validate_backup_corrupted(backup_restore, sample_dataset):
    # Create backup
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Corrupt backup
    dataset_backup_dir = backup_restore._get_dataset_backup_dir("test_dataset")
    backup_file = dataset_backup_dir / f"{metadata.backup_id}.jsonl"
    with open(backup_file, 'a') as f:
        f.write("corrupted\n")
    
    # Validation should fail
    valid = backup_restore.validate_backup(metadata.backup_id, "test_dataset")
    assert valid is False


def test_delete_backup(backup_restore, sample_dataset):
    # Create backup
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Delete backup
    deleted = backup_restore.delete_backup(metadata.backup_id, "test_dataset")
    assert deleted is True
    
    # Verify deletion
    dataset_backup_dir = backup_restore._get_dataset_backup_dir("test_dataset")
    backup_file = dataset_backup_dir / f"{metadata.backup_id}.jsonl"
    assert not backup_file.exists()


def test_cleanup_old_backups(backup_restore, sample_dataset):
    # Create 5 backups
    for _ in range(5):
        backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    # Keep only 3
    deleted = backup_restore.cleanup_old_backups("test_dataset", keep_count=3)
    
    assert deleted == 2
    
    inventory = backup_restore.list_backups("test_dataset")
    assert len(inventory.backups) == 3


def test_get_backup_size(backup_restore, sample_dataset):
    metadata = backup_restore.create_full_backup(sample_dataset, "test_dataset")
    
    size = backup_restore.get_backup_size(metadata.backup_id, "test_dataset")
    assert size > 0
    assert size == metadata.total_bytes


def test_create_incremental_backup(backup_restore, tmp_path):
    # Create initial dataset
    initial_dataset = tmp_path / "initial.jsonl"
    with open(initial_dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "First"}) + "\n")
        f.write(json.dumps({"id": "2", "content": "Second"}) + "\n")
    
    # Create full backup
    metadata_full = backup_restore.create_full_backup(initial_dataset, "test_dataset")
    
    # Create updated dataset with new record
    updated_dataset = tmp_path / "updated.jsonl"
    with open(updated_dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "First"}) + "\n")
        f.write(json.dumps({"id": "2", "content": "Second"}) + "\n")
        f.write(json.dumps({"id": "3", "content": "Third"}) + "\n")
    
    # Create incremental backup
    metadata_inc = backup_restore.create_incremental_backup(
        updated_dataset,
        "test_dataset",
        metadata_full.backup_id,
    )
    
    assert metadata_inc.backup_type == "incremental"
    assert metadata_inc.parent_backup_id == metadata_full.backup_id
    assert metadata_inc.record_count == 1  # Only one new record


def test_compute_checksum(backup_restore, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content", encoding="utf-8")
    
    checksum = backup_restore._compute_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex digest length


def test_count_records(backup_restore, sample_dataset):
    count = backup_restore._count_records(sample_dataset)
    assert count == 3


def test_backup_with_empty_dataset(backup_restore, tmp_path):
    empty_dataset = tmp_path / "empty.jsonl"
    empty_dataset.touch()
    
    metadata = backup_restore.create_full_backup(empty_dataset, "test_dataset")
    assert metadata.record_count == 0


def test_backup_inventory_to_json():
    inventory = BackupInventory(dataset_id="test")
    inventory.add_backup(BackupMetadata(
        backup_id="b1",
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        backup_type="full",
    ))
    
    json_str = inventory.to_json()
    data = json.loads(json_str)
    
    assert data["dataset_id"] == "test"
    assert data["total_backups"] == 1
    assert len(data["backups"]) == 1
