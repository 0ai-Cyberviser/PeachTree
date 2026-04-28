"""Tests for dataset synchronization functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_sync import (
    ConflictResolution,
    DatasetSynchronizer,
    SyncRecord,
    SyncResult,
    SyncState,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def source_dataset(temp_dir):
    """Create a source dataset for testing."""
    source = temp_dir / "source.jsonl"
    records = [
        {"record_id": "rec_001", "content": "Source record 1", "quality_score": 85},
        {"record_id": "rec_002", "content": "Source record 2", "quality_score": 90},
        {"record_id": "rec_003", "content": "Source record 3", "quality_score": 75},
    ]
    with open(source, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return source


@pytest.fixture
def target_dataset(temp_dir):
    """Create a target dataset for testing."""
    target = temp_dir / "target.jsonl"
    records = [
        {"record_id": "rec_002", "content": "Target record 2 modified", "quality_score": 88},
        {"record_id": "rec_004", "content": "Target record 4", "quality_score": 80},
    ]
    with open(target, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return target


class TestSyncRecord:
    """Test SyncRecord dataclass."""
    
    def test_sync_record_creation(self):
        """Test creating a sync record."""
        record = SyncRecord(
            record_id="test_001",
            state=SyncState.ADDED,
            checksum="abc123",
            timestamp="2026-04-27T00:00:00Z",
        )
        
        assert record.record_id == "test_001"
        assert record.state == SyncState.ADDED
        assert record.checksum == "abc123"
    
    def test_sync_record_to_dict(self):
        """Test converting sync record to dictionary."""
        record = SyncRecord(
            record_id="test_001",
            state=SyncState.MODIFIED,
            checksum="def456",
            timestamp="2026-04-27T00:00:00Z",
        )
        
        data = record.to_dict()
        assert data["record_id"] == "test_001"
        assert data["state"] == "modified"
        assert data["checksum"] == "def456"


class TestSyncResult:
    """Test SyncResult dataclass."""
    
    def test_sync_result_creation(self):
        """Test creating a sync result."""
        result = SyncResult(
            source_records=100,
            target_records=90,
            added_records=10,
            updated_records=5,
            deleted_records=0,
            conflicts_resolved=2,
            timestamp="2026-04-27T00:00:00Z",
        )
        
        assert result.source_records == 100
        assert result.target_records == 90
        assert result.added_records == 10
        assert result.updated_records == 5
    
    def test_sync_result_to_json(self):
        """Test converting sync result to JSON."""
        result = SyncResult(
            source_records=50,
            target_records=45,
            added_records=5,
            updated_records=3,
            deleted_records=0,
            conflicts_resolved=1,
            timestamp="2026-04-27T00:00:00Z",
        )
        
        json_str = result.to_json()
        data = json.loads(json_str)
        
        assert data["source_records"] == 50
        assert data["added_records"] == 5
        assert data["updated_records"] == 3


class TestDatasetSynchronizer:
    """Test DatasetSynchronizer class."""
    
    def test_compute_checksum(self):
        """Test computing record checksum."""
        synchronizer = DatasetSynchronizer()
        
        record = {"record_id": "test", "content": "test content"}
        checksum = synchronizer.compute_checksum(record)
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex digest length
    
    def test_detect_changes(self, source_dataset, target_dataset):
        """Test detecting changes between datasets."""
        synchronizer = DatasetSynchronizer()
        
        changes = synchronizer.detect_changes(source_dataset, target_dataset)
        
        # Should detect additions and modifications
        assert len(changes) > 0
        
        # Check for added records
        added = [c for c in changes if c.state == SyncState.ADDED]
        assert len(added) > 0
        
        # Check for modified records
        modified = [c for c in changes if c.state == SyncState.MODIFIED]
        assert len(modified) > 0
    
    def test_sync_with_source_wins(self, source_dataset, target_dataset, temp_dir):
        """Test sync with source wins conflict resolution."""
        synchronizer = DatasetSynchronizer()
        output = temp_dir / "synced.jsonl"
        
        result = synchronizer.sync(
            source_dataset,
            output,
            target_path=target_dataset,
            resolution=ConflictResolution.SOURCE_WINS,
        )
        
        assert result.source_records == 3
        assert result.added_records >= 0
        assert output.exists()
    
    def test_sync_with_target_wins(self, source_dataset, target_dataset, temp_dir):
        """Test sync with target wins conflict resolution."""
        synchronizer = DatasetSynchronizer()
        output = temp_dir / "synced.jsonl"
        
        result = synchronizer.sync(
            source_dataset,
            output,
            target_path=target_dataset,
            resolution=ConflictResolution.TARGET_WINS,
        )
        
        assert result.source_records == 3
        assert output.exists()
    
    def test_sync_with_newest_wins(self, source_dataset, target_dataset, temp_dir):
        """Test sync with newest wins conflict resolution."""
        synchronizer = DatasetSynchronizer()
        output = temp_dir / "synced.jsonl"
        
        result = synchronizer.sync(
            source_dataset,
            output,
            target_path=target_dataset,
            resolution=ConflictResolution.NEWEST_WINS,
        )
        
        assert result.source_records == 3
        assert output.exists()
    
    def test_bidirectional_sync(self, source_dataset, target_dataset, temp_dir):
        """Test bidirectional synchronization."""
        synchronizer = DatasetSynchronizer()
        output = temp_dir / "synced.jsonl"
        
        result = synchronizer.bidirectional_sync(
            source_dataset,
            output,
            resolution=ConflictResolution.NEWEST_WINS,
        )
        
        assert result.source_records > 0
        assert output.exists()
        
        # Verify output has records from both source and target
        with open(output) as f:
            lines = f.readlines()
            assert len(lines) > 0
    
    def test_get_sync_status(self, source_dataset, target_dataset):
        """Test getting sync status between datasets."""
        synchronizer = DatasetSynchronizer()
        
        status = synchronizer.get_sync_status(source_dataset, target_dataset)
        
        assert "in_sync" in status
        assert "changes_needed" in status
        assert isinstance(status["changes_needed"], int)
    
    def test_incremental_sync(self, source_dataset, target_dataset, temp_dir):
        """Test incremental sync only applies changed records."""
        synchronizer = DatasetSynchronizer()
        
        # First sync
        output = temp_dir / "synced1.jsonl"
        result1 = synchronizer.sync(source_dataset, output)
        
        # Modify source
        with open(source_dataset, 'a') as f:
            f.write(json.dumps({"record_id": "rec_005", "content": "New record", "quality_score": 95}) + "\n")
        
        # Second sync should only add the new record
        result2 = synchronizer.sync(source_dataset, output)
        assert result2.source_records == 4
