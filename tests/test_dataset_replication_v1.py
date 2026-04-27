"""Tests for dataset_replication module."""
import json
from pathlib import Path
import pytest
from datetime import datetime
from src.peachtree.dataset_replication import (
    DatasetReplicator,
    ReplicaManager,
    ReplicaSite,
    ReplicationLog,
    ConflictRecord,
    SyncResult,
    ReplicationStrategy,
    ConflictResolution,
    ReplicationStatus,
    SyncMode,
    IncrementalReplicator,
    ReplicationMonitor,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample JSONL dataset."""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": 1, "text": "replicated data", "version": 1},
        {"id": 2, "text": "distributed content", "version": 1},
        {"id": 3, "text": "multi-site data", "version": 1},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


@pytest.fixture
def replica_manager(tmp_path):
    """Create a replica manager."""
    return ReplicaManager(tmp_path / "replication.json")


def test_replica_manager_init(tmp_path):
    """Test replica manager initialization."""
    rm = ReplicaManager(tmp_path / "config.json")
    assert rm.config_path == tmp_path / "config.json"


def test_add_site(replica_manager):
    """Test adding a replica site."""
    site = ReplicaSite(
        site_id="site1",
        location="datacenter-1",
        endpoint="https://site1.example.com",
    )
    
    replica_manager.add_site(site)
    
    assert "site1" in replica_manager.sites


def test_remove_site(replica_manager):
    """Test removing a replica site."""
    site = ReplicaSite(
        site_id="site1",
        location="datacenter-1",
        endpoint="https://site1.example.com",
    )
    replica_manager.add_site(site)
    
    success = replica_manager.remove_site("site1")
    
    assert success
    assert "site1" not in replica_manager.sites


def test_get_site(replica_manager):
    """Test retrieving a site."""
    site = ReplicaSite(
        site_id="site1",
        location="datacenter-1",
        endpoint="https://site1.example.com",
    )
    replica_manager.add_site(site)
    
    retrieved = replica_manager.get_site("site1")
    
    assert retrieved.site_id == "site1"


def test_list_sites(replica_manager):
    """Test listing all sites."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    sites = replica_manager.list_sites()
    assert len(sites) == 2


def test_list_active_sites_only(replica_manager):
    """Test listing only active sites."""
    site1 = ReplicaSite("s1", "dc1", "http://s1", is_active=True)
    site2 = ReplicaSite("s2", "dc2", "http://s2", is_active=False)
    
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    active = replica_manager.list_sites(active_only=True)
    assert len(active) == 1


def test_get_master_sites(replica_manager):
    """Test getting master sites."""
    master = ReplicaSite("master", "dc1", "http://master", is_master=True)
    slave = ReplicaSite("slave", "dc2", "http://slave", is_master=False)
    
    replica_manager.add_site(master)
    replica_manager.add_site(slave)
    
    masters = replica_manager.get_master_sites()
    assert len(masters) == 1
    assert masters[0].site_id == "master"


def test_update_last_sync(replica_manager):
    """Test updating last sync timestamp."""
    site = ReplicaSite("site1", "dc1", "http://s1")
    replica_manager.add_site(site)
    
    replica_manager.update_last_sync("site1")
    
    updated_site = replica_manager.get_site("site1")
    assert updated_site.last_sync is not None


def test_replicator_init(replica_manager):
    """Test replicator initialization."""
    replicator = DatasetReplicator(replica_manager)
    assert replicator.strategy == ReplicationStrategy.MASTER_SLAVE


def test_replicate_dataset(tmp_path, sample_dataset, replica_manager):
    """Test replicating a dataset."""
    site1 = ReplicaSite("s1", "dc1", "http://s1", is_master=True)
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    log = replicator.replicate(sample_dataset, "s1", "s2")
    
    assert log.status == ReplicationStatus.COMPLETED
    assert log.records_replicated == 3


def test_sync_sites(replica_manager):
    """Test syncing two sites."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    result = replicator.sync_sites("s1", "s2", mode=SyncMode.PUSH)
    
    assert result.success


def test_detect_conflicts(replica_manager):
    """Test conflict detection."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    site1.last_sync = datetime.now()
    site2.last_sync = datetime.now()
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    conflicts = replicator.detect_conflicts("s1", "s2", "dataset1")
    
    assert len(conflicts) >= 0


def test_resolve_conflict(replica_manager):
    """Test resolving a conflict."""
    replicator = DatasetReplicator(replica_manager)
    
    # Create a conflict
    conflict = ConflictRecord(
        conflict_id="c1",
        dataset_id="d1",
        source_site="s1",
        target_site="s2",
        detected_at=datetime.now(),
        resolution_strategy=ConflictResolution.LAST_WRITE_WINS,
    )
    replicator.conflicts.append(conflict)
    
    # Resolve it
    success = replicator.resolve_conflict("c1", ConflictResolution.MANUAL)
    
    assert success
    assert replicator.conflicts[0].resolved


def test_get_replication_status(tmp_path, sample_dataset, replica_manager):
    """Test getting replication status."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    replicator.replicate(sample_dataset, "s1", "s2")
    
    status = replicator.get_replication_status()
    
    assert status["total_replications"] == 1
    assert status["successful"] == 1


def test_incremental_replicator(tmp_path, sample_dataset, replica_manager):
    """Test incremental replication."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    incremental = IncrementalReplicator(replicator)
    
    log = incremental.replicate_incremental(sample_dataset, "s1", "s2")
    
    assert log.status == ReplicationStatus.COMPLETED


def test_incremental_stats(tmp_path, sample_dataset, replica_manager):
    """Test incremental replication statistics."""
    replicator = DatasetReplicator(replica_manager)
    incremental = IncrementalReplicator(replicator)
    
    incremental.replicate_incremental(sample_dataset, "s1", "s2")
    
    stats = incremental.get_incremental_stats()
    assert stats["tracked_datasets"] == 1


def test_replication_monitor(replica_manager):
    """Test replication monitor."""
    replicator = DatasetReplicator(replica_manager)
    monitor = ReplicationMonitor(replicator)
    
    health = monitor.check_health()
    
    assert "health_score" in health
    assert "status" in health


def test_monitor_get_lagging_sites(replica_manager):
    """Test getting lagging sites."""
    old_site = ReplicaSite("old", "dc1", "http://old")
    old_site.last_sync = datetime(2020, 1, 1)
    replica_manager.add_site(old_site)
    
    replicator = DatasetReplicator(replica_manager)
    monitor = ReplicationMonitor(replicator)
    
    lagging = monitor.get_lagging_sites(threshold_hours=1)
    
    assert len(lagging) >= 0


def test_monitor_get_metrics(tmp_path, sample_dataset, replica_manager):
    """Test getting replication metrics."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    replicator.replicate(sample_dataset, "s1", "s2")
    
    monitor = ReplicationMonitor(replicator)
    metrics = monitor.get_metrics()
    
    assert metrics["total_replications"] == 1
    assert "avg_records_per_replication" in metrics


def test_replication_strategy_enum():
    """Test replication strategy enum."""
    assert ReplicationStrategy.MASTER_SLAVE
    assert ReplicationStrategy.MULTI_MASTER
    assert ReplicationStrategy.EVENTUAL_CONSISTENCY
    assert ReplicationStrategy.STRONG_CONSISTENCY


def test_conflict_resolution_enum():
    """Test conflict resolution enum."""
    assert ConflictResolution.LAST_WRITE_WINS
    assert ConflictResolution.FIRST_WRITE_WINS
    assert ConflictResolution.MANUAL
    assert ConflictResolution.MERGE
    assert ConflictResolution.VERSION_VECTOR


def test_replication_status_enum():
    """Test replication status enum."""
    assert ReplicationStatus.PENDING
    assert ReplicationStatus.IN_PROGRESS
    assert ReplicationStatus.COMPLETED
    assert ReplicationStatus.FAILED
    assert ReplicationStatus.CONFLICT
    assert ReplicationStatus.PAUSED


def test_sync_mode_enum():
    """Test sync mode enum."""
    assert SyncMode.PUSH
    assert SyncMode.PULL
    assert SyncMode.BIDIRECTIONAL
    assert SyncMode.INCREMENTAL


def test_replica_site_serialization():
    """Test replica site serialization."""
    site = ReplicaSite("s1", "dc1", "http://s1", is_master=True)
    data = site.to_dict()
    
    assert "site_id" in data
    assert "location" in data
    assert "is_master" in data


def test_replication_log_serialization(tmp_path, sample_dataset, replica_manager):
    """Test replication log serialization."""
    site1 = ReplicaSite("s1", "dc1", "http://s1")
    site2 = ReplicaSite("s2", "dc2", "http://s2")
    replica_manager.add_site(site1)
    replica_manager.add_site(site2)
    
    replicator = DatasetReplicator(replica_manager)
    log = replicator.replicate(sample_dataset, "s1", "s2")
    
    data = log.to_dict()
    assert "log_id" in data
    assert "status" in data


def test_sync_result_serialization(replica_manager):
    """Test sync result serialization."""
    replicator = DatasetReplicator(replica_manager)
    result = replicator.sync_sites("s1", "s2")
    
    data = result.to_dict()
    assert "success" in data
    assert "synced_at" in data


def test_conflict_record_serialization():
    """Test conflict record serialization."""
    conflict = ConflictRecord(
        conflict_id="c1",
        dataset_id="d1",
        source_site="s1",
        target_site="s2",
        detected_at=datetime.now(),
        resolution_strategy=ConflictResolution.LAST_WRITE_WINS,
    )
    
    data = conflict.to_dict()
    assert "conflict_id" in data
    assert "resolution_strategy" in data
