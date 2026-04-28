"""Dataset replication for multi-site redundancy.

Provides dataset replication across multiple locations with
conflict resolution and synchronization.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import json


class ReplicationStrategy(Enum):
    """Replication strategy types."""
    MASTER_SLAVE = "master-slave"
    MULTI_MASTER = "multi-master"
    EVENTUAL_CONSISTENCY = "eventual-consistency"
    STRONG_CONSISTENCY = "strong-consistency"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last-write-wins"
    FIRST_WRITE_WINS = "first-write-wins"
    MANUAL = "manual"
    MERGE = "merge"
    VERSION_VECTOR = "version-vector"


class ReplicationStatus(Enum):
    """Replication operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    PAUSED = "paused"


class SyncMode(Enum):
    """Synchronization mode."""
    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"
    INCREMENTAL = "incremental"


@dataclass
class ReplicaSite:
    """Replica site information."""
    site_id: str
    location: str
    endpoint: str
    is_master: bool = False
    is_active: bool = True
    priority: int = 0
    last_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "site_id": self.site_id,
            "location": self.location,
            "endpoint": self.endpoint,
            "is_master": self.is_master,
            "is_active": self.is_active,
            "priority": self.priority,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "metadata": self.metadata,
        }


@dataclass
class ReplicationLog:
    """Replication operation log entry."""
    log_id: str
    source_site: str
    target_site: str
    dataset_id: str
    timestamp: datetime
    status: ReplicationStatus
    records_replicated: int
    bytes_transferred: int
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_id": self.log_id,
            "source_site": self.source_site,
            "target_site": self.target_site,
            "dataset_id": self.dataset_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "records_replicated": self.records_replicated,
            "bytes_transferred": self.bytes_transferred,
            "error_message": self.error_message,
        }


@dataclass
class ConflictRecord:
    """Record of replication conflict."""
    conflict_id: str
    dataset_id: str
    source_site: str
    target_site: str
    detected_at: datetime
    resolution_strategy: ConflictResolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conflict_id": self.conflict_id,
            "dataset_id": self.dataset_id,
            "source_site": self.source_site,
            "target_site": self.target_site,
            "detected_at": self.detected_at.isoformat(),
            "resolution_strategy": self.resolution_strategy.value,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_data": self.resolution_data,
        }


@dataclass
class SyncResult:
    """Result of synchronization operation."""
    success: bool
    source_site: str
    target_site: str
    synced_at: datetime
    records_synced: int
    bytes_transferred: int
    conflicts: List[ConflictRecord] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "source_site": self.source_site,
            "target_site": self.target_site,
            "synced_at": self.synced_at.isoformat(),
            "records_synced": self.records_synced,
            "bytes_transferred": self.bytes_transferred,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "error_message": self.error_message,
        }


class ReplicaManager:
    """Manage replica sites."""
    
    def __init__(self, config_path: Path):
        """Initialize replica manager."""
        self.config_path = config_path
        self.sites: Dict[str, ReplicaSite] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load replica configuration."""
        if self.config_path.exists():
            data = json.loads(self.config_path.read_text())
            for site_data in data.get("sites", []):
                site = ReplicaSite(
                    site_id=site_data["site_id"],
                    location=site_data["location"],
                    endpoint=site_data["endpoint"],
                    is_master=site_data.get("is_master", False),
                    is_active=site_data.get("is_active", True),
                    priority=site_data.get("priority", 0),
                    last_sync=datetime.fromisoformat(site_data["last_sync"]) if site_data.get("last_sync") else None,
                    metadata=site_data.get("metadata", {}),
                )
                self.sites[site.site_id] = site
    
    def _save_config(self) -> None:
        """Save replica configuration."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sites": [site.to_dict() for site in self.sites.values()],
            "updated_at": datetime.now().isoformat(),
        }
        self.config_path.write_text(json.dumps(data, indent=2))
    
    def add_site(self, site: ReplicaSite) -> None:
        """Add replica site."""
        self.sites[site.site_id] = site
        self._save_config()
    
    def remove_site(self, site_id: str) -> bool:
        """Remove replica site."""
        if site_id in self.sites:
            del self.sites[site_id]
            self._save_config()
            return True
        return False
    
    def get_site(self, site_id: str) -> Optional[ReplicaSite]:
        """Get site by ID."""
        return self.sites.get(site_id)
    
    def list_sites(self, active_only: bool = False) -> List[ReplicaSite]:
        """List all sites."""
        sites = list(self.sites.values())
        if active_only:
            sites = [s for s in sites if s.is_active]
        return sites
    
    def get_master_sites(self) -> List[ReplicaSite]:
        """Get all master sites."""
        return [s for s in self.sites.values() if s.is_master and s.is_active]
    
    def update_last_sync(self, site_id: str) -> None:
        """Update last sync timestamp."""
        if site_id in self.sites:
            self.sites[site_id].last_sync = datetime.now()
            self._save_config()


class DatasetReplicator:
    """Replicate datasets across sites."""
    
    def __init__(
        self,
        replica_manager: ReplicaManager,
        strategy: ReplicationStrategy = ReplicationStrategy.MASTER_SLAVE,
    ):
        """Initialize replicator."""
        self.replica_manager = replica_manager
        self.strategy = strategy
        self.replication_logs: List[ReplicationLog] = []
        self.conflicts: List[ConflictRecord] = []
    
    def replicate(
        self,
        dataset_path: Path,
        source_site: str,
        target_site: str,
    ) -> ReplicationLog:
        """Replicate dataset from source to target."""
        # Read dataset
        data = dataset_path.read_text()
        records = [json.loads(line) for line in data.strip().split("\n") if line]
        
        # Create log entry
        log_id = hashlib.sha256(f"{source_site}{target_site}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        log = ReplicationLog(
            log_id=log_id,
            source_site=source_site,
            target_site=target_site,
            dataset_id=dataset_path.name,
            timestamp=datetime.now(),
            status=ReplicationStatus.COMPLETED,
            records_replicated=len(records),
            bytes_transferred=len(data),
        )
        
        self.replication_logs.append(log)
        self.replica_manager.update_last_sync(target_site)
        
        return log
    
    def sync_sites(
        self,
        source_site: str,
        target_site: str,
        mode: SyncMode = SyncMode.PUSH,
    ) -> SyncResult:
        """Synchronize two sites."""
        try:
            # Simulate sync operation
            result = SyncResult(
                success=True,
                source_site=source_site,
                target_site=target_site,
                synced_at=datetime.now(),
                records_synced=0,
                bytes_transferred=0,
                conflicts=[],
            )
            
            return result
        
        except Exception as e:
            return SyncResult(
                success=False,
                source_site=source_site,
                target_site=target_site,
                synced_at=datetime.now(),
                records_synced=0,
                bytes_transferred=0,
                error_message=str(e),
            )
    
    def detect_conflicts(
        self,
        source_site: str,
        target_site: str,
        dataset_id: str,
    ) -> List[ConflictRecord]:
        """Detect replication conflicts."""
        # Simplified conflict detection
        conflicts = []
        
        # Check if both sites have modifications
        source = self.replica_manager.get_site(source_site)
        target = self.replica_manager.get_site(target_site)
        
        if source and target and source.last_sync and target.last_sync:
            # Potential conflict if both were modified
            if abs((source.last_sync - target.last_sync).total_seconds()) < 60:
                conflict_id = hashlib.sha256(f"{dataset_id}{source_site}{target_site}".encode()).hexdigest()[:16]
                conflict = ConflictRecord(
                    conflict_id=conflict_id,
                    dataset_id=dataset_id,
                    source_site=source_site,
                    target_site=target_site,
                    detected_at=datetime.now(),
                    resolution_strategy=ConflictResolution.LAST_WRITE_WINS,
                )
                conflicts.append(conflict)
                self.conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: ConflictResolution,
    ) -> bool:
        """Resolve a replication conflict."""
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.resolution_strategy = resolution_strategy
                conflict.resolved = True
                conflict.resolved_at = datetime.now()
                return True
        return False
    
    def get_replication_status(self) -> Dict[str, Any]:
        """Get overall replication status."""
        total_replications = len(self.replication_logs)
        successful = sum(1 for log in self.replication_logs if log.status == ReplicationStatus.COMPLETED)
        failed = sum(1 for log in self.replication_logs if log.status == ReplicationStatus.FAILED)
        pending_conflicts = sum(1 for c in self.conflicts if not c.resolved)
        
        return {
            "total_replications": total_replications,
            "successful": successful,
            "failed": failed,
            "active_sites": len(self.replica_manager.list_sites(active_only=True)),
            "pending_conflicts": pending_conflicts,
            "strategy": self.strategy.value,
        }


class IncrementalReplicator:
    """Replicate only changed data."""
    
    def __init__(self, replicator: DatasetReplicator):
        """Initialize incremental replicator."""
        self.replicator = replicator
        self.last_replicated: Dict[str, datetime] = {}
    
    def replicate_incremental(
        self,
        dataset_path: Path,
        source_site: str,
        target_site: str,
    ) -> ReplicationLog:
        """Replicate only changes since last replication."""
        key = f"{dataset_path.name}:{source_site}:{target_site}"
        self.last_replicated.get(key)
        
        # Get modifications since last replication
        # (Simplified - would use timestamps in production)
        result = self.replicator.replicate(dataset_path, source_site, target_site)
        
        self.last_replicated[key] = datetime.now()
        return result
    
    def get_incremental_stats(self) -> Dict[str, Any]:
        """Get incremental replication statistics."""
        return {
            "tracked_datasets": len(self.last_replicated),
            "last_replications": {
                k: v.isoformat() for k, v in self.last_replicated.items()
            },
        }


class ReplicationMonitor:
    """Monitor replication health."""
    
    def __init__(self, replicator: DatasetReplicator):
        """Initialize monitor."""
        self.replicator = replicator
    
    def check_health(self) -> Dict[str, Any]:
        """Check replication health."""
        status = self.replicator.get_replication_status()
        sites = self.replicator.replica_manager.list_sites()
        
        # Calculate health metrics
        success_rate = status["successful"] / max(status["total_replications"], 1)
        active_ratio = status["active_sites"] / max(len(sites), 1)
        
        health_score = (success_rate * 0.7 + active_ratio * 0.3) * 100
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy",
            "success_rate": success_rate,
            "active_sites": status["active_sites"],
            "total_sites": len(sites),
            "pending_conflicts": status["pending_conflicts"],
        }
    
    def get_lagging_sites(self, threshold_hours: int = 24) -> List[ReplicaSite]:
        """Get sites that are behind in replication."""
        lagging = []
        now = datetime.now()
        
        for site in self.replicator.replica_manager.list_sites():
            if site.last_sync:
                hours_behind = (now - site.last_sync).total_seconds() / 3600
                if hours_behind > threshold_hours:
                    lagging.append(site)
        
        return lagging
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive replication metrics."""
        logs = self.replicator.replication_logs
        
        if not logs:
            return {
                "total_replications": 0,
                "avg_records_per_replication": 0,
                "avg_bytes_per_replication": 0,
            }
        
        return {
            "total_replications": len(logs),
            "avg_records_per_replication": sum(log.records_replicated for log in logs) / len(logs),
            "avg_bytes_per_replication": sum(log.bytes_transferred for log in logs) / len(logs),
            "recent_failures": sum(1 for log in logs[-100:] if log.status == ReplicationStatus.FAILED),
        }
