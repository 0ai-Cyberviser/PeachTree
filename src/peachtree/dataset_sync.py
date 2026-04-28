"""Dataset synchronization for multi-environment workflows.

This module provides dataset synchronization capabilities including:
- Dataset syncing across environments (dev, staging, production)
- Incremental sync (only changed records)
- Bidirectional sync with conflict resolution
- Sync status tracking and reporting
- Sync scheduling and automation
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class SyncRecord:
    """A record in the sync state."""
    
    record_id: str
    checksum: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
        }


@dataclass
class SyncState:
    """Synchronization state for tracking changes."""
    
    environment: str
    dataset_id: str
    last_sync_time: str
    record_checksums: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "dataset_id": self.dataset_id,
            "last_sync_time": self.last_sync_time,
            "record_checksums": self.record_checksums,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncState":
        return cls(
            environment=data["environment"],
            dataset_id=data["dataset_id"],
            last_sync_time=data["last_sync_time"],
            record_checksums=data.get("record_checksums", {}),
        )


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    
    source_env: str
    target_env: str
    records_added: int
    records_updated: int
    records_deleted: int
    conflicts: int
    timestamp: str
    success: bool
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_env": self.source_env,
            "target_env": self.target_env,
            "records_added": self.records_added,
            "records_updated": self.records_updated,
            "records_deleted": self.records_deleted,
            "conflicts": self.conflicts,
            "timestamp": self.timestamp,
            "success": self.success,
            "error_message": self.error_message,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ConflictResolution:
    """Conflict resolution strategy."""
    
    strategy: str  # source_wins, target_wins, newest_wins, manual
    manual_resolutions: Dict[str, str] = field(default_factory=dict)  # record_id -> chosen_version


class DatasetSynchronizer:
    """Synchronize datasets across environments."""
    
    def __init__(self, sync_dir: Path = Path("data/sync")) -> None:
        """Initialize the synchronizer.
        
        Args:
            sync_dir: Directory for sync state files
        """
        self.sync_dir = sync_dir
        self.sync_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_checksum(self, record: Dict[str, Any]) -> str:
        """Compute checksum for a record.
        
        Args:
            record: Dataset record
        
        Returns:
            SHA256 checksum hex string
        """
        # Create deterministic JSON string
        record_json = json.dumps(record, sort_keys=True)
        return hashlib.sha256(record_json.encode()).hexdigest()
    
    def load_sync_state(self, environment: str, dataset_id: str) -> Optional[SyncState]:
        """Load sync state from file.
        
        Args:
            environment: Environment name
            dataset_id: Dataset identifier
        
        Returns:
            SyncState or None if not found
        """
        state_file = self.sync_dir / f"{environment}_{dataset_id}_state.json"
        if not state_file.exists():
            return None
        
        with open(state_file) as f:
            data = json.load(f)
        
        return SyncState.from_dict(data)
    
    def save_sync_state(self, state: SyncState) -> None:
        """Save sync state to file.
        
        Args:
            state: Sync state to save
        """
        state_file = self.sync_dir / f"{state.environment}_{state.dataset_id}_state.json"
        with open(state_file, 'w') as f:
            f.write(state.to_json())
    
    def build_sync_state(
        self,
        dataset_path: Path,
        environment: str,
        dataset_id: str,
    ) -> SyncState:
        """Build sync state from current dataset.
        
        Args:
            dataset_path: Path to dataset file
            environment: Environment name
            dataset_id: Dataset identifier
        
        Returns:
            SyncState with checksums for all records
        """
        state = SyncState(
            environment=environment,
            dataset_id=dataset_id,
            last_sync_time=datetime.utcnow().isoformat() + "Z",
        )
        
        with open(dataset_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                record_id = record.get("id", "")
                if record_id:
                    checksum = self.compute_checksum(record)
                    state.record_checksums[record_id] = checksum
        
        return state
    
    def detect_changes(
        self,
        source_path: Path,
        target_state: Optional[SyncState],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Set[str]]:
        """Detect changes between source dataset and target state.
        
        Args:
            source_path: Path to source dataset
            target_state: Target sync state (None if first sync)
        
        Returns:
            (added_records, updated_records, deleted_record_ids)
        """
        added: List[Dict[str, Any]] = []
        updated: List[Dict[str, Any]] = []
        deleted: Set[str] = set()
        
        # Track seen record IDs
        source_ids: Set[str] = set()
        
        # Read source dataset
        with open(source_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                record_id = record.get("id", "")
                if not record_id:
                    continue
                
                source_ids.add(record_id)
                checksum = self.compute_checksum(record)
                
                if target_state is None:
                    # First sync - all records are new
                    added.append(record)
                elif record_id not in target_state.record_checksums:
                    # New record
                    added.append(record)
                elif target_state.record_checksums[record_id] != checksum:
                    # Record changed
                    updated.append(record)
        
        # Find deleted records
        if target_state:
            for record_id in target_state.record_checksums:
                if record_id not in source_ids:
                    deleted.add(record_id)
        
        return added, updated, deleted
    
    def apply_changes(
        self,
        target_path: Path,
        added: List[Dict[str, Any]],
        updated: List[Dict[str, Any]],
        deleted: Set[str],
    ) -> int:
        """Apply changes to target dataset.
        
        Args:
            target_path: Path to target dataset
            added: Records to add
            updated: Records to update
            deleted: Record IDs to delete
        
        Returns:
            Total number of records in target after sync
        """
        # Load existing target records
        existing_records: Dict[str, Dict[str, Any]] = {}
        
        if target_path.exists():
            with open(target_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    record = json.loads(line)
                    record_id = record.get("id", "")
                    if record_id:
                        existing_records[record_id] = record
        
        # Apply deletions
        for record_id in deleted:
            existing_records.pop(record_id, None)
        
        # Apply additions
        for record in added:
            record_id = record.get("id", "")
            if record_id:
                existing_records[record_id] = record
        
        # Apply updates
        for record in updated:
            record_id = record.get("id", "")
            if record_id:
                existing_records[record_id] = record
        
        # Write updated dataset
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w') as f:
            for record in existing_records.values():
                f.write(json.dumps(record) + "\n")
        
        return len(existing_records)
    
    def sync(
        self,
        source_path: Path,
        target_path: Path,
        source_env: str,
        target_env: str,
        dataset_id: str,
        incremental: bool = True,
    ) -> SyncResult:
        """Synchronize source dataset to target.
        
        Args:
            source_path: Source dataset path
            target_path: Target dataset path
            source_env: Source environment name
            target_env: Target environment name
            dataset_id: Dataset identifier
            incremental: Use incremental sync (only changes)
        
        Returns:
            SyncResult with sync statistics
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        try:
            # Load or build target state
            target_state = self.load_sync_state(target_env, dataset_id) if incremental else None
            
            # Detect changes
            added, updated, deleted = self.detect_changes(source_path, target_state)
            
            # Apply changes
            total_records = self.apply_changes(target_path, added, updated, deleted)
            
            # Update target state
            new_state = self.build_sync_state(target_path, target_env, dataset_id)
            self.save_sync_state(new_state)
            
            # Create result
            result = SyncResult(
                source_env=source_env,
                target_env=target_env,
                records_added=len(added),
                records_updated=len(updated),
                records_deleted=len(deleted),
                conflicts=0,
                timestamp=timestamp,
                success=True,
            )
            
            return result
            
        except Exception as e:
            return SyncResult(
                source_env=source_env,
                target_env=target_env,
                records_added=0,
                records_updated=0,
                records_deleted=0,
                conflicts=0,
                timestamp=timestamp,
                success=False,
                error_message=str(e),
            )
    
    def bidirectional_sync(
        self,
        env1_path: Path,
        env2_path: Path,
        env1_name: str,
        env2_name: str,
        dataset_id: str,
        conflict_resolution: ConflictResolution,
    ) -> Tuple[SyncResult, SyncResult]:
        """Perform bidirectional sync between two environments.
        
        Args:
            env1_path: Environment 1 dataset path
            env2_path: Environment 2 dataset path
            env1_name: Environment 1 name
            env2_name: Environment 2 name
            dataset_id: Dataset identifier
            conflict_resolution: Conflict resolution strategy
        
        Returns:
            (env1_to_env2_result, env2_to_env1_result)
        """
        # Load both states
        env1_state = self.load_sync_state(env1_name, dataset_id)
        env2_state = self.load_sync_state(env2_name, dataset_id)
        
        # Detect changes in both directions
        env1_added, env1_updated, env1_deleted = self.detect_changes(env1_path, env1_state)
        env2_added, env2_updated, env2_deleted = self.detect_changes(env2_path, env2_state)
        
        # Detect conflicts (same record modified in both environments)
        conflicts: Set[str] = set()
        for record in env1_updated:
            record_id = record.get("id", "")
            if any(r.get("id") == record_id for r in env2_updated):
                conflicts.add(record_id)
        
        # Resolve conflicts based on strategy
        if conflict_resolution.strategy == "source_wins":
            # Env1 changes win
            result1 = self.sync(env1_path, env2_path, env1_name, env2_name, dataset_id)
            result2 = SyncResult(env2_name, env1_name, 0, 0, 0, len(conflicts), datetime.utcnow().isoformat() + "Z", True)
        elif conflict_resolution.strategy == "target_wins":
            # Env2 changes win
            result2 = self.sync(env2_path, env1_path, env2_name, env1_name, dataset_id)
            result1 = SyncResult(env1_name, env2_name, 0, 0, 0, len(conflicts), datetime.utcnow().isoformat() + "Z", True)
        else:
            # Default: apply non-conflicting changes from both sides
            result1 = self.sync(env1_path, env2_path, env1_name, env2_name, dataset_id)
            result2 = self.sync(env2_path, env1_path, env2_name, env1_name, dataset_id)
        
        result1.conflicts = len(conflicts)
        result2.conflicts = len(conflicts)
        
        return result1, result2
    
    def get_sync_status(self, environment: str, dataset_id: str) -> Dict[str, Any]:
        """Get sync status for an environment.
        
        Args:
            environment: Environment name
            dataset_id: Dataset identifier
        
        Returns:
            Status dictionary
        """
        state = self.load_sync_state(environment, dataset_id)
        
        if state is None:
            return {
                "environment": environment,
                "dataset_id": dataset_id,
                "status": "never_synced",
                "record_count": 0,
                "last_sync_time": None,
            }
        
        return {
            "environment": environment,
            "dataset_id": dataset_id,
            "status": "synced",
            "record_count": len(state.record_checksums),
            "last_sync_time": state.last_sync_time,
        }
