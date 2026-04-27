"""Tests for dataset_versioning module."""
import json
from pathlib import Path
import pytest
from src.peachtree.dataset_versioning import (
    DatasetVersionControl,
    VersionMetadata,
    VersionDiff,
    VersionStatus,
    ChangeType,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample JSONL dataset."""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": 1, "text": "hello", "label": "greeting"},
        {"id": 2, "text": "world", "label": "noun"},
        {"id": 3, "text": "test", "label": "noun"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


def test_version_control_init(tmp_path):
    """Test version control initialization."""
    vc = DatasetVersionControl(tmp_path)
    assert vc.repository_path == tmp_path


def test_commit_creates_version(tmp_path, sample_dataset):
    """Test committing a dataset version."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(sample_dataset, "Initial commit", "test@example.com")
    
    assert metadata.message == "Initial commit"
    assert metadata.author == "test@example.com"
    assert metadata.record_count == 3
    assert metadata.status == VersionStatus.COMMITTED


def test_commit_with_tags(tmp_path, sample_dataset):
    """Test committing with tags."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(
        sample_dataset,
        "Tagged version",
        "test@example.com",
        tags=["v1.0", "prod"],
    )
    
    assert "v1.0" in metadata.tags
    assert "prod" in metadata.tags


def test_list_versions(tmp_path, sample_dataset):
    """Test listing versions."""
    vc = DatasetVersionControl(tmp_path)
    vc.commit(sample_dataset, "First", "test@example.com")
    vc.commit(sample_dataset, "Second", "test@example.com")
    
    versions = vc.list_versions()
    assert len(versions) == 2
    assert versions[0].message == "First"
    assert versions[1].message == "Second"


def test_checkout_version(tmp_path, sample_dataset):
    """Test checking out a version."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(sample_dataset, "Test", "test@example.com")
    
    output = tmp_path / "checkout.jsonl"
    success = vc.checkout(metadata.version_id, output)
    
    assert success
    assert output.exists()
    assert output.read_text() == sample_dataset.read_text()


def test_checkout_nonexistent(tmp_path):
    """Test checking out nonexistent version."""
    vc = DatasetVersionControl(tmp_path)
    output = tmp_path / "out.jsonl"
    
    success = vc.checkout("nonexistent", output)
    assert not success


def test_diff_identical(tmp_path, sample_dataset):
    """Test diff between identical versions."""
    vc = DatasetVersionControl(tmp_path)
    v1 = vc.commit(sample_dataset, "V1", "test@example.com")
    v2 = vc.commit(sample_dataset, "V2", "test@example.com")
    
    diff = vc.diff(v1.version_id, v2.version_id)
    
    assert diff.added_records == 0
    assert diff.deleted_records == 0
    assert diff.modified_records == 0


def test_diff_with_changes(tmp_path):
    """Test diff with actual changes."""
    vc = DatasetVersionControl(tmp_path)
    
    # Create first version
    ds1 = tmp_path / "v1.jsonl"
    ds1.write_text(json.dumps({"id": 1, "text": "hello"}))
    v1 = vc.commit(ds1, "V1", "test@example.com")
    
    # Create modified version
    ds2 = tmp_path / "v2.jsonl"
    ds2.write_text(
        json.dumps({"id": 1, "text": "hello modified"}) + "\n" +
        json.dumps({"id": 2, "text": "new"})
    )
    v2 = vc.commit(ds2, "V2", "test@example.com")
    
    diff = vc.diff(v1.version_id, v2.version_id)
    
    assert diff.added_records + diff.modified_records + diff.deleted_records > 0


def test_tag_version(tmp_path, sample_dataset):
    """Test tagging a version."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(sample_dataset, "Test", "test@example.com")
    
    success = vc.tag_version(metadata.version_id, "production")
    assert success
    
    versions = vc.list_versions()
    assert "production" in versions[0].tags


def test_tag_nonexistent(tmp_path):
    """Test tagging nonexistent version."""
    vc = DatasetVersionControl(tmp_path)
    
    success = vc.tag_version("nonexistent", "tag")
    assert not success


def test_get_history(tmp_path, sample_dataset):
    """Test getting version history."""
    vc = DatasetVersionControl(tmp_path)
    v1 = vc.commit(sample_dataset, "V1", "test@example.com")
    v2 = vc.commit(sample_dataset, "V2", "test@example.com")
    
    history = vc.get_history(v2.version_id)
    
    assert len(history) == 2
    assert history[0].version_id == v1.version_id
    assert history[1].version_id == v2.version_id


def test_get_statistics(tmp_path, sample_dataset):
    """Test getting statistics."""
    vc = DatasetVersionControl(tmp_path)
    vc.commit(sample_dataset, "V1", "test@example.com")
    vc.commit(sample_dataset, "V2", "test@example.com")
    
    stats = vc.get_statistics()
    
    assert stats["total_versions"] == 2
    assert "total_records" in stats


def test_version_metadata_serialization(tmp_path, sample_dataset):
    """Test version metadata serialization."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(sample_dataset, "Test", "test@example.com")
    
    data = metadata.to_dict()
    
    assert data["message"] == "Test"
    assert data["author"] == "test@example.com"
    assert "version_id" in data


def test_version_diff_serialization(tmp_path, sample_dataset):
    """Test version diff serialization."""
    vc = DatasetVersionControl(tmp_path)
    v1 = vc.commit(sample_dataset, "V1", "test@example.com")
    v2 = vc.commit(sample_dataset, "V2", "test@example.com")
    
    diff = vc.diff(v1.version_id, v2.version_id)
    data = diff.to_dict()
    
    assert "added_records" in data
    assert "deleted_records" in data
    assert "modified_records" in data


def test_multiple_commits(tmp_path, sample_dataset):
    """Test multiple commits."""
    vc = DatasetVersionControl(tmp_path)
    
    for i in range(5):
        vc.commit(sample_dataset, f"Commit {i}", "test@example.com")
    
    versions = vc.list_versions()
    assert len(versions) == 5


def test_version_status_enum():
    """Test VersionStatus enum."""
    assert VersionStatus.DRAFT
    assert VersionStatus.COMMITTED
    assert VersionStatus.ARCHIVED
    assert VersionStatus.DELETED


def test_change_type_enum():
    """Test ChangeType enum."""
    assert ChangeType.ADDED
    assert ChangeType.MODIFIED
    assert ChangeType.DELETED
    assert ChangeType.RENAMED


def test_empty_dataset(tmp_path):
    """Test versioning an empty dataset."""
    vc = DatasetVersionControl(tmp_path)
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    
    metadata = vc.commit(empty, "Empty", "test@example.com")
    assert metadata.record_count == 0


def test_large_version_list(tmp_path, sample_dataset):
    """Test handling many versions."""
    vc = DatasetVersionControl(tmp_path)
    
    for i in range(20):
        vc.commit(sample_dataset, f"Version {i}", f"author{i}@example.com")
    
    versions = vc.list_versions()
    assert len(versions) == 20


def test_version_metadata_validation(tmp_path, sample_dataset):
    """Test version metadata contains required fields."""
    vc = DatasetVersionControl(tmp_path)
    metadata = vc.commit(sample_dataset, "Test", "test@example.com")
    
    assert metadata.version_id
    assert metadata.timestamp
    assert metadata.message
    assert metadata.author
    assert isinstance(metadata.record_count, int)
    assert isinstance(metadata.status, VersionStatus)
