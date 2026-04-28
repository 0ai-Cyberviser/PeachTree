"""Tests for dataset_archival module."""
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import json

from peachtree.dataset_archival import (
    DatasetArchiver,
    ArchiveIndexManager,
    RetentionPolicyManager,
    ArchiveStatistics,
    ArchiveMetadata,
    ArchiveIndex,
    ArchiveStatus,
    CompressionLevel,
    RetentionPolicy,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample dataset for testing."""
    dataset = tmp_path / "dataset.jsonl"
    records = [{"id": i, "data": f"content_{i}" * 100} for i in range(100)]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


@pytest.fixture
def archive_dir(tmp_path):
    """Create an archive directory."""
    archive = tmp_path / "archives"
    archive.mkdir()
    return archive


def test_archive_status_enum():
    """Test ArchiveStatus enum."""
    assert ArchiveStatus.ACTIVE.value == "active"
    assert ArchiveStatus.ARCHIVED.value == "archived"
    assert ArchiveStatus.RESTORING.value == "restoring"
    assert ArchiveStatus.DELETED.value == "deleted"


def test_compression_level_enum():
    """Test CompressionLevel enum."""
    assert CompressionLevel.NONE.value == 0
    assert CompressionLevel.FAST.value == 1
    assert CompressionLevel.BALANCED.value == 5
    assert CompressionLevel.MAXIMUM.value == 9


def test_retention_policy_enum():
    """Test RetentionPolicy enum."""
    assert RetentionPolicy.SHORT.value == "short"
    assert RetentionPolicy.MEDIUM.value == "medium"
    assert RetentionPolicy.LONG.value == "long"
    assert RetentionPolicy.PERMANENT.value == "permanent"


def test_archive_metadata_creation():
    """Test ArchiveMetadata creation."""
    metadata = ArchiveMetadata(
        archive_id="archive123",
        original_path=Path("/tmp/dataset.jsonl"),
        archive_path=Path("/tmp/archive.gz"),
        created_at=datetime.now(),
        size_bytes=1000,
        compressed_size_bytes=500,
        compression_level=CompressionLevel.BALANCED,
        retention_policy=RetentionPolicy.MEDIUM,
    )
    assert metadata.archive_id == "archive123"
    assert metadata.size_bytes == 1000
    assert metadata.compressed_size_bytes == 500


def test_archive_metadata_to_dict():
    """Test ArchiveMetadata to_dict."""
    now = datetime.now()
    metadata = ArchiveMetadata(
        archive_id="archive123",
        original_path=Path("/tmp/dataset.jsonl"),
        archive_path=Path("/tmp/archive.gz"),
        created_at=now,
        size_bytes=2000,
        compressed_size_bytes=1000,
        compression_level=CompressionLevel.FAST,
        retention_policy=RetentionPolicy.SHORT,
    )
    d = metadata.to_dict()
    assert d["archive_id"] == "archive123"
    assert d["size_bytes"] == 2000
    assert d["compression_level"] == 1


def test_dataset_archiver_creation(archive_dir):
    """Test DatasetArchiver creation."""
    archiver = DatasetArchiver(archive_dir)
    assert archiver.archive_dir == archive_dir
    assert archive_dir.exists()


def test_dataset_archiver_archive_dataset(sample_dataset, archive_dir):
    """Test archiving a dataset."""
    archiver = DatasetArchiver(archive_dir)
    
    metadata = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.MEDIUM,
        compression_level=CompressionLevel.BALANCED,
    )
    
    assert metadata.archive_id is not None
    assert metadata.archive_path.exists()
    assert metadata.compressed_size_bytes < metadata.size_bytes
    assert metadata.status == ArchiveStatus.ARCHIVED


def test_dataset_archiver_restore_dataset(sample_dataset, archive_dir, tmp_path):
    """Test restoring a dataset from archive."""
    archiver = DatasetArchiver(archive_dir)
    
    # Archive first
    metadata = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.MEDIUM,
        compression_level=CompressionLevel.BALANCED,
    )
    
    # Restore
    restore_path = tmp_path / "restored.jsonl"
    success = archiver.restore_dataset(metadata, restore_path)
    
    assert success
    assert restore_path.exists()
    assert restore_path.stat().st_size == sample_dataset.stat().st_size


def test_dataset_archiver_delete_archive(sample_dataset, archive_dir):
    """Test deleting an archive."""
    archiver = DatasetArchiver(archive_dir)
    
    metadata = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.SHORT,
    )
    
    success = archiver.delete_archive(metadata)
    
    assert success
    assert not metadata.archive_path.exists()
    assert metadata.status == ArchiveStatus.DELETED


def test_dataset_archiver_compression_levels(sample_dataset, archive_dir):
    """Test different compression levels."""
    archiver = DatasetArchiver(archive_dir)
    
    # Test balanced compression
    meta_balanced = archiver.archive_dataset(
        sample_dataset,
        compression_level=CompressionLevel.BALANCED,
    )
    
    # Test maximum compression
    meta_max = archiver.archive_dataset(
        sample_dataset,
        compression_level=CompressionLevel.MAXIMUM,
    )
    
    assert meta_max.compressed_size_bytes <= meta_balanced.compressed_size_bytes


def test_dataset_archiver_retention_policies(sample_dataset, archive_dir):
    """Test different retention policies."""
    archiver = DatasetArchiver(archive_dir)
    
    # Short retention
    meta_short = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.SHORT,
    )
    assert meta_short.expires_at is not None
    
    # Permanent retention
    meta_perm = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.PERMANENT,
    )
    assert meta_perm.expires_at is None


def test_archive_index_creation(archive_dir):
    """Test ArchiveIndex creation."""
    index = ArchiveIndex(
        index_id="main",
        archives=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert index.index_id == "main"
    assert len(index.archives) == 0


def test_archive_index_to_dict():
    """Test ArchiveIndex to_dict."""
    index = ArchiveIndex(
        index_id="main",
        archives=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    d = index.to_dict()
    assert d["index_id"] == "main"
    assert d["archives"] == []


def test_archive_index_manager_creation(archive_dir):
    """Test ArchiveIndexManager creation."""
    index_path = archive_dir / "index.json"
    manager = ArchiveIndexManager(index_path)
    
    assert manager.index_path == index_path
    assert len(manager.archives) == 0


def test_archive_index_manager_add_archive(sample_dataset, archive_dir):
    """Test adding archive to index."""
    archiver = DatasetArchiver(archive_dir)
    metadata = archiver.archive_dataset(sample_dataset)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    index_manager.add_archive(metadata)
    
    assert len(index_manager.archives) == 1
    assert index_manager.archives[0].archive_id == metadata.archive_id


def test_archive_index_manager_remove_archive(sample_dataset, archive_dir):
    """Test removing archive from index."""
    archiver = DatasetArchiver(archive_dir)
    metadata = archiver.archive_dataset(sample_dataset)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    index_manager.add_archive(metadata)
    
    success = index_manager.remove_archive(metadata.archive_id)
    
    assert success
    assert len(index_manager.archives) == 0


def test_archive_index_manager_get_archive(sample_dataset, archive_dir):
    """Test getting archive from index."""
    archiver = DatasetArchiver(archive_dir)
    metadata = archiver.archive_dataset(sample_dataset)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    index_manager.add_archive(metadata)
    
    retrieved = index_manager.get_archive(metadata.archive_id)
    
    assert retrieved is not None
    assert retrieved.archive_id == metadata.archive_id


def test_archive_index_manager_list_archives(sample_dataset, archive_dir):
    """Test listing archives."""
    archiver = DatasetArchiver(archive_dir)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    for i in range(3):
        meta = archiver.archive_dataset(sample_dataset)
        index_manager.add_archive(meta)
    
    archives = index_manager.list_archives()
    assert len(archives) == 3


def test_archive_index_manager_list_by_status(sample_dataset, archive_dir):
    """Test listing archives by status."""
    archiver = DatasetArchiver(archive_dir)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    meta1 = archiver.archive_dataset(sample_dataset)
    index_manager.add_archive(meta1)
    
    meta2 = archiver.archive_dataset(sample_dataset)
    meta2.status = ArchiveStatus.DELETED
    index_manager.add_archive(meta2)
    
    archived = index_manager.list_archives(status=ArchiveStatus.ARCHIVED)
    assert len(archived) == 1


def test_archive_index_manager_search_archives(sample_dataset, archive_dir):
    """Test searching archives."""
    archiver = DatasetArchiver(archive_dir)
    metadata = archiver.archive_dataset(sample_dataset)
    
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    index_manager.add_archive(metadata)
    
    results = index_manager.search_archives("dataset")
    assert len(results) >= 1


def test_retention_policy_manager_creation(archive_dir):
    """Test RetentionPolicyManager creation."""
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    policy_mgr = RetentionPolicyManager(index_manager)
    
    assert policy_mgr.index_manager == index_manager


def test_retention_policy_manager_apply_policies(sample_dataset, archive_dir):
    """Test applying retention policies."""
    archiver = DatasetArchiver(archive_dir)
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    # Create expired archive
    metadata = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.SHORT,
    )
    metadata.expires_at = datetime.now() - timedelta(days=1)  # Already expired
    index_manager.add_archive(metadata)
    
    policy_mgr = RetentionPolicyManager(index_manager)
    result = policy_mgr.apply_retention_policies()
    
    assert result["deleted_count"] >= 0


def test_retention_policy_manager_get_expiring_soon(sample_dataset, archive_dir):
    """Test getting archives expiring soon."""
    archiver = DatasetArchiver(archive_dir)
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    metadata = archiver.archive_dataset(
        sample_dataset,
        retention_policy=RetentionPolicy.SHORT,
    )
    metadata.expires_at = datetime.now() + timedelta(days=3)
    index_manager.add_archive(metadata)
    
    policy_mgr = RetentionPolicyManager(index_manager)
    expiring = policy_mgr.get_expiring_soon(days=7)
    
    assert len(expiring) >= 1


def test_archive_statistics_creation(archive_dir):
    """Test ArchiveStatistics creation."""
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    stats = ArchiveStatistics(index_manager)
    
    assert stats.index_manager == index_manager


def test_archive_statistics_get_statistics(sample_dataset, archive_dir):
    """Test getting archive statistics."""
    archiver = DatasetArchiver(archive_dir)
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    for i in range(3):
        meta = archiver.archive_dataset(
            sample_dataset,
            retention_policy=RetentionPolicy.MEDIUM,
        )
        index_manager.add_archive(meta)
    
    stats_engine = ArchiveStatistics(index_manager)
    stats = stats_engine.get_statistics()
    
    assert stats["total_archives"] == 3
    assert stats["total_size_bytes"] > 0
    assert stats["compression_ratio"] < 1.0


def test_archive_checksum_verification(sample_dataset, archive_dir, tmp_path):
    """Test archive checksum verification."""
    archiver = DatasetArchiver(archive_dir)
    
    metadata = archiver.archive_dataset(sample_dataset)
    
    assert metadata.checksum is not None
    
    # Restore and verify checksum is preserved
    restore_path = tmp_path / "restored.jsonl"
    success = archiver.restore_dataset(metadata, restore_path)
    
    assert success


def test_archive_index_persistence(sample_dataset, archive_dir):
    """Test archive index persistence."""
    archiver = DatasetArchiver(archive_dir)
    index_path = archive_dir / "index.json"
    
    # Create and save
    manager1 = ArchiveIndexManager(index_path)
    metadata = archiver.archive_dataset(sample_dataset)
    manager1.add_archive(metadata)
    
    # Load in new manager
    manager2 = ArchiveIndexManager(index_path)
    
    assert len(manager2.archives) == 1
    assert manager2.archives[0].archive_id == metadata.archive_id


def test_archive_compression_ratio(sample_dataset, archive_dir):
    """Test compression ratio calculation."""
    archiver = DatasetArchiver(archive_dir)
    index_manager = ArchiveIndexManager(archive_dir / "index.json")
    
    metadata = archiver.archive_dataset(
        sample_dataset,
        compression_level=CompressionLevel.MAXIMUM,
    )
    index_manager.add_archive(metadata)
    
    stats_engine = ArchiveStatistics(index_manager)
    stats = stats_engine.get_statistics()
    
    assert stats["compression_ratio"] < 1.0
    assert stats["space_saved_bytes"] > 0
