"""
PeachTree Dataset Backup and Restore System

Snapshot management, incremental backups, and point-in-time restore for datasets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib
import shutil


@dataclass
class BackupMetadata:
    """Metadata for a dataset backup snapshot"""
    backup_id: str
    dataset_id: str
    timestamp: str
    backup_type: str  # full, incremental
    parent_backup_id: str = ""
    record_count: int = 0
    total_bytes: int = 0
    checksum: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "dataset_id": self.dataset_id,
            "timestamp": self.timestamp,
            "backup_type": self.backup_type,
            "parent_backup_id": self.parent_backup_id,
            "record_count": self.record_count,
            "total_bytes": self.total_bytes,
            "checksum": self.checksum,
            "tags": self.tags,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class RestoreResult:
    """Result of dataset restore operation"""
    backup_id: str
    dataset_path: str
    records_restored: int
    restore_timestamp: str
    checksum_verified: bool
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "dataset_path": self.dataset_path,
            "records_restored": self.records_restored,
            "restore_timestamp": self.restore_timestamp,
            "checksum_verified": self.checksum_verified,
        }


@dataclass
class BackupInventory:
    """Inventory of all backups for a dataset"""
    dataset_id: str
    backups: list[BackupMetadata] = field(default_factory=list)
    
    def add_backup(self, backup: BackupMetadata) -> None:
        """Add backup to inventory"""
        self.backups.append(backup)
    
    def get_backup(self, backup_id: str) -> BackupMetadata | None:
        """Get backup by ID"""
        for backup in self.backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def get_latest_backup(self) -> BackupMetadata | None:
        """Get most recent backup"""
        if not self.backups:
            return None
        return max(self.backups, key=lambda b: b.timestamp)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "total_backups": len(self.backups),
            "backups": [b.to_dict() for b in self.backups],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DatasetBackupRestore:
    """Backup and restore datasets with snapshot management"""
    
    def __init__(self, backup_dir: Path | str = "data/backups"):
        """Initialize backup/restore manager"""
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _generate_backup_id(self, dataset_id: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{dataset_id}_{timestamp}"
    
    def _get_dataset_backup_dir(self, dataset_id: str) -> Path:
        """Get backup directory for dataset"""
        dataset_dir = self.backup_dir / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir
    
    def _count_records(self, dataset_path: Path) -> int:
        """Count records in dataset"""
        count = 0
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    
    def create_full_backup(
        self,
        dataset_path: Path | str,
        dataset_id: str,
        tags: dict[str, str] | None = None,
    ) -> BackupMetadata:
        """
        Create full backup snapshot
        
        Args:
            dataset_path: Path to dataset to backup
            dataset_id: Dataset identifier
            tags: Optional tags for backup
        
        Returns:
            BackupMetadata with backup information
        """
        dataset_path = Path(dataset_path)
        backup_id = self._generate_backup_id(dataset_id)
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        
        # Create backup file
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        shutil.copy2(dataset_path, backup_file)
        
        # Compute checksum
        checksum = self._compute_checksum(backup_file)
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            dataset_id=dataset_id,
            timestamp=datetime.utcnow().isoformat(),
            backup_type="full",
            record_count=self._count_records(backup_file),
            total_bytes=backup_file.stat().st_size,
            checksum=checksum,
            tags=tags or {},
        )
        
        # Save metadata
        metadata_file = dataset_backup_dir / f"{backup_id}.meta.json"
        metadata_file.write_text(metadata.to_json() + "\n", encoding="utf-8")
        
        # Update inventory
        self._update_inventory(dataset_id, metadata)
        
        return metadata
    
    def create_incremental_backup(
        self,
        dataset_path: Path | str,
        dataset_id: str,
        parent_backup_id: str,
        tags: dict[str, str] | None = None,
    ) -> BackupMetadata:
        """
        Create incremental backup (only changed records)
        
        Args:
            dataset_path: Current dataset path
            dataset_id: Dataset identifier
            parent_backup_id: Parent backup ID to diff against
            tags: Optional tags
        
        Returns:
            BackupMetadata for incremental backup
        """
        dataset_path = Path(dataset_path)
        backup_id = self._generate_backup_id(dataset_id)
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        
        # Load parent backup
        parent_file = dataset_backup_dir / f"{parent_backup_id}.jsonl"
        if not parent_file.exists():
            raise ValueError(f"Parent backup not found: {parent_backup_id}")
        
        # Find changed records (simple comparison)
        parent_records: set[str] = set()
        with open(parent_file) as f:
            for line in f:
                if line.strip():
                    parent_records.add(line.strip())
        
        # Write only new/changed records
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        new_record_count = 0
        with open(dataset_path) as f_in, open(backup_file, 'w') as f_out:
            for line in f_in:
                if line.strip() and line.strip() not in parent_records:
                    f_out.write(line)
                    new_record_count += 1
        
        # Compute checksum
        checksum = self._compute_checksum(backup_file)
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            dataset_id=dataset_id,
            timestamp=datetime.utcnow().isoformat(),
            backup_type="incremental",
            parent_backup_id=parent_backup_id,
            record_count=new_record_count,
            total_bytes=backup_file.stat().st_size,
            checksum=checksum,
            tags=tags or {},
        )
        
        # Save metadata
        metadata_file = dataset_backup_dir / f"{backup_id}.meta.json"
        metadata_file.write_text(metadata.to_json() + "\n", encoding="utf-8")
        
        # Update inventory
        self._update_inventory(dataset_id, metadata)
        
        return metadata
    
    def restore_backup(
        self,
        backup_id: str,
        dataset_id: str,
        output_path: Path | str,
        verify_checksum: bool = True,
    ) -> RestoreResult:
        """
        Restore dataset from backup
        
        Args:
            backup_id: Backup ID to restore
            dataset_id: Dataset identifier
            output_path: Where to restore dataset
            verify_checksum: Verify backup integrity
        
        Returns:
            RestoreResult with restore information
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        metadata_file = dataset_backup_dir / f"{backup_id}.meta.json"
        
        if not backup_file.exists():
            raise ValueError(f"Backup not found: {backup_id}")
        
        # Load metadata
        with open(metadata_file) as f:
            meta_data = json.load(f)
        metadata = BackupMetadata(**meta_data)
        
        # Verify checksum if requested
        checksum_verified = False
        if verify_checksum:
            current_checksum = self._compute_checksum(backup_file)
            if current_checksum != metadata.checksum:
                raise ValueError(f"Checksum mismatch for backup {backup_id}")
            checksum_verified = True
        
        # Restore file
        shutil.copy2(backup_file, output_path)
        
        return RestoreResult(
            backup_id=backup_id,
            dataset_path=str(output_path),
            records_restored=metadata.record_count,
            restore_timestamp=datetime.utcnow().isoformat(),
            checksum_verified=checksum_verified,
        )
    
    def list_backups(self, dataset_id: str) -> BackupInventory:
        """
        List all backups for dataset
        
        Args:
            dataset_id: Dataset identifier
        
        Returns:
            BackupInventory with all backups
        """
        inventory = BackupInventory(dataset_id=dataset_id)
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        
        # Load all metadata files
        for meta_file in dataset_backup_dir.glob("*.meta.json"):
            with open(meta_file) as f:
                meta_data = json.load(f)
            metadata = BackupMetadata(**meta_data)
            inventory.add_backup(metadata)
        
        # Sort by timestamp
        inventory.backups.sort(key=lambda b: b.timestamp, reverse=True)
        
        return inventory
    
    def delete_backup(self, backup_id: str, dataset_id: str) -> bool:
        """
        Delete a backup
        
        Args:
            backup_id: Backup ID to delete
            dataset_id: Dataset identifier
        
        Returns:
            True if deleted successfully
        """
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        metadata_file = dataset_backup_dir / f"{backup_id}.meta.json"
        
        deleted = False
        if backup_file.exists():
            backup_file.unlink()
            deleted = True
        
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True
        
        return deleted
    
    def validate_backup(self, backup_id: str, dataset_id: str) -> bool:
        """
        Validate backup integrity
        
        Args:
            backup_id: Backup ID to validate
            dataset_id: Dataset identifier
        
        Returns:
            True if backup is valid
        """
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        metadata_file = dataset_backup_dir / f"{backup_id}.meta.json"
        
        if not backup_file.exists() or not metadata_file.exists():
            return False
        
        # Load metadata
        with open(metadata_file) as f:
            meta_data = json.load(f)
        metadata = BackupMetadata(**meta_data)
        
        # Verify checksum
        current_checksum = self._compute_checksum(backup_file)
        if current_checksum != metadata.checksum:
            return False
        
        # Verify record count
        current_count = self._count_records(backup_file)
        if current_count != metadata.record_count:
            return False
        
        return True
    
    def _update_inventory(self, dataset_id: str, metadata: BackupMetadata) -> None:
        """Update backup inventory file"""
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        inventory_file = dataset_backup_dir / "inventory.json"
        
        # Load existing inventory
        if inventory_file.exists():
            with open(inventory_file) as f:
                inv_data = json.load(f)
            inventory = BackupInventory(
                dataset_id=inv_data["dataset_id"],
                backups=[BackupMetadata(**b) for b in inv_data.get("backups", [])],
            )
        else:
            inventory = BackupInventory(dataset_id=dataset_id)
        
        # Add new backup
        inventory.add_backup(metadata)
        
        # Save inventory
        inventory_file.write_text(inventory.to_json() + "\n", encoding="utf-8")
    
    def get_backup_size(self, backup_id: str, dataset_id: str) -> int:
        """Get backup file size in bytes"""
        dataset_backup_dir = self._get_dataset_backup_dir(dataset_id)
        backup_file = dataset_backup_dir / f"{backup_id}.jsonl"
        
        if backup_file.exists():
            return backup_file.stat().st_size
        return 0
    
    def cleanup_old_backups(
        self,
        dataset_id: str,
        keep_count: int = 10,
    ) -> int:
        """
        Delete old backups, keeping only the most recent
        
        Args:
            dataset_id: Dataset identifier
            keep_count: Number of backups to keep
        
        Returns:
            Number of backups deleted
        """
        inventory = self.list_backups(dataset_id)
        
        if len(inventory.backups) <= keep_count:
            return 0
        
        # Sort by timestamp, oldest first
        sorted_backups = sorted(inventory.backups, key=lambda b: b.timestamp)
        
        # Delete oldest backups
        to_delete = sorted_backups[:-keep_count]
        deleted_count = 0
        
        for backup in to_delete:
            if self.delete_backup(backup.backup_id, dataset_id):
                deleted_count += 1
        
        return deleted_count
