"""
Tests for dataset_versions module
"""
from pathlib import Path
import pytest
import json
from peachtree.dataset_versions import (
    DatasetVersionManager,
    DatasetVersion,
    VersionHistory,
)


@pytest.fixture
def temp_dataset(tmp_path):
    """Create a temporary dataset"""
    dataset_file = tmp_path / "test-dataset.jsonl"
    records = []
    for i in range(5):
        record = {
            "id": f"rec-{i}",
            "content": f"Test content {i}",
            "source_repo": "test-repo",
            "source_path": f"test{i}.txt",
            "digest": f"sha256-{i}",
        }
        records.append(json.dumps(record))
    dataset_file.write_text("\n".join(records) + "\n")
    return dataset_file


@pytest.fixture
def version_manager(tmp_path):
    """Create a version manager with temp directory"""
    version_dir = tmp_path / "versions"
    return DatasetVersionManager(version_dir)


def test_dataset_version_creation():
    """Test DatasetVersion dataclass creation"""
    version = DatasetVersion(
        version="v1.0.0",
        timestamp="2026-04-27T10:00:00",
        dataset_path="data/test.jsonl",
        snapshot_path=".peachtree/versions/test/v1.0.0.jsonl",
        digest="abc123",
        record_count=100,
        size_bytes=10240,
        message="Initial version",
        author="test-user",
    )
    
    assert version.version == "v1.0.0"
    assert version.record_count == 100
    assert version.to_dict()["version"] == "v1.0.0"


def test_version_history():
    """Test VersionHistory management"""
    history = VersionHistory(dataset_name="test-dataset")
    
    v1 = DatasetVersion(
        "v1.0.0", "2026-04-27T10:00:00", "test.jsonl", "snap1.jsonl",
        "digest1", 100, 1024, "Version 1", "author1"
    )
    v2 = DatasetVersion(
        "v2.0.0", "2026-04-27T11:00:00", "test.jsonl", "snap2.jsonl",
        "digest2", 110, 1124, "Version 2", "author1", parent_version="v1.0.0"
    )
    
    history.add_version(v1)
    history.add_version(v2)
    
    assert len(history.versions) == 2
    assert history.get_latest() == v2
    assert history.get_version("v1.0.0") == v1


def test_version_history_to_changelog():
    """Test changelog generation"""
    history = VersionHistory(dataset_name="my-dataset")
    
    v1 = DatasetVersion(
        "v1.0.0", "2026-04-27T10:00:00", "test.jsonl", "snap1.jsonl",
        "digest1", 100, 1024, "Initial release", "author1",
        tags=["stable"]
    )
    history.add_version(v1)
    
    changelog = history.to_changelog()
    
    assert "# Changelog: my-dataset" in changelog
    assert "## v1.0.0" in changelog
    assert "Initial release" in changelog
    assert "**Tags:** stable" in changelog


def test_create_version(version_manager, temp_dataset):
    """Test creating a dataset version"""
    version = version_manager.create_version(
        dataset_path=temp_dataset,
        version="v1.0.0",
        message="First version",
        author="test-user",
        tags=["stable"],
    )
    
    assert version.version == "v1.0.0"
    assert version.record_count == 5
    assert version.message == "First version"
    assert "stable" in version.tags
    assert Path(version.snapshot_path).exists()


def test_list_versions(version_manager, temp_dataset):
    """Test listing versions"""
    # Create multiple versions
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    version_manager.create_version(temp_dataset, "v1.1.0", "Version 1.1")
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    versions = version_manager.list_versions(temp_dataset.stem)
    
    assert len(versions) == 3
    assert versions[0].version == "v2.0.0"  # Sorted newest first
    assert versions[2].version == "v1.0.0"


def test_get_version(version_manager, temp_dataset):
    """Test getting a specific version"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    v1 = version_manager.get_version(temp_dataset.stem, "v1.0.0")
    
    assert v1 is not None
    assert v1.version == "v1.0.0"
    assert v1.message == "Version 1"


def test_get_latest_version(version_manager, temp_dataset):
    """Test getting the latest version"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    latest = version_manager.get_latest_version(temp_dataset.stem)
    
    assert latest is not None
    assert latest.version == "v2.0.0"


def test_rollback(version_manager, temp_dataset, tmp_path):
    """Test rolling back to a previous version"""
    # Create versions
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    # Modify dataset
    temp_dataset.write_text('{"modified": true}\n')
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    # Rollback to v1.0.0
    output_path = tmp_path / "rolled-back.jsonl"
    result_path = version_manager.rollback(
        temp_dataset.stem,
        "v1.0.0",
        output_path
    )
    
    assert result_path == output_path
    assert output_path.exists()
    
    # Verify content matches v1.0.0
    content = output_path.read_text()
    assert "modified" not in content
    assert "Test content" in content


def test_tag_version(version_manager, temp_dataset):
    """Test adding tags to versions"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    # Add tag
    version_manager.tag_version(temp_dataset.stem, "v1.0.0", "production")
    
    # Verify tag was added
    version = version_manager.get_version(temp_dataset.stem, "v1.0.0")
    assert "production" in version.tags


def test_generate_changelog(version_manager, temp_dataset):
    """Test changelog generation"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Initial version", tags=["stable"])
    version_manager.create_version(temp_dataset, "v1.1.0", "Bug fixes")
    version_manager.create_version(temp_dataset, "v2.0.0", "Major update", tags=["breaking"])
    
    changelog = version_manager.generate_changelog(temp_dataset.stem)
    
    assert "# Changelog" in changelog
    assert "v1.0.0" in changelog
    assert "v1.1.0" in changelog
    assert "v2.0.0" in changelog
    assert "Initial version" in changelog
    assert "stable" in changelog


def test_compare_versions(version_manager, temp_dataset):
    """Test comparing two versions"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    # Modify dataset (add more records)
    with open(temp_dataset, "a") as f:
        f.write('{"id": "new-record", "content": "New content"}\n')
    
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    comparison = version_manager.compare_versions(temp_dataset.stem, "v1.0.0", "v2.0.0")
    
    assert comparison["version1"] == "v1.0.0"
    assert comparison["version2"] == "v2.0.0"
    assert comparison["record_count_delta"] == 1
    assert comparison["digest_changed"] is True


def test_version_with_metadata(version_manager, temp_dataset):
    """Test version with custom metadata"""
    metadata = {
        "quality_score": 85.5,
        "duplicate_ratio": 0.05,
        "notes": "High quality dataset",
    }
    
    version = version_manager.create_version(
        temp_dataset,
        "v1.0.0",
        "Version with metadata",
        metadata=metadata
    )
    
    assert version.metadata["quality_score"] == 85.5
    assert version.metadata["notes"] == "High quality dataset"


def test_parent_version_tracking(version_manager, temp_dataset):
    """Test that parent versions are tracked"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    version_manager.create_version(temp_dataset, "v2.0.0", "Version 2")
    
    v2 = version_manager.get_version(temp_dataset.stem, "v2.0.0")
    
    assert v2.parent_version == "v1.0.0"


def test_version_history_persistence(tmp_path, temp_dataset):
    """Test that version history persists across manager instances"""
    version_dir = tmp_path / "versions"
    
    # Create version with first manager
    manager1 = DatasetVersionManager(version_dir)
    manager1.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    # Create new manager instance
    manager2 = DatasetVersionManager(version_dir)
    versions = manager2.list_versions(temp_dataset.stem)
    
    assert len(versions) == 1
    assert versions[0].version == "v1.0.0"


def test_rollback_nonexistent_version(version_manager, temp_dataset):
    """Test rollback to non-existent version raises error"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    with pytest.raises(ValueError, match="Version .* not found"):
        version_manager.rollback(temp_dataset.stem, "v999.0.0")


def test_tag_nonexistent_version(version_manager, temp_dataset):
    """Test tagging non-existent version raises error"""
    version_manager.create_version(temp_dataset, "v1.0.0", "Version 1")
    
    with pytest.raises(ValueError, match="Version .* not found"):
        version_manager.tag_version(temp_dataset.stem, "v999.0.0", "production")
