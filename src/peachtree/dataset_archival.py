"""Dataset archival for long-term storage and retention.

Provides dataset archival with compression, retention policies,
indexing, and restore capabilities.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import gzip
import shutil
import hashlib


class ArchiveStatus(Enum):
    """Archive status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    RESTORING = "restoring"
    DELETED = "deleted"


class CompressionLevel(Enum):
    """Compression levels."""
    NONE = 0
    FAST = 1
    BALANCED = 5
    MAXIMUM = 9


class RetentionPolicy(Enum):
    """Retention policies."""
    SHORT = "short"  # 30 days
    MEDIUM = "medium"  # 90 days
    LONG = "long"  # 1 year
    PERMANENT = "permanent"  # Forever


@dataclass
class ArchiveMetadata:
    """Archive metadata."""
    archive_id: str
    original_path: Path
    archive_path: Path
    created_at: datetime
    size_bytes: int
    compressed_size_bytes: int
    compression_level: CompressionLevel
    retention_policy: RetentionPolicy
    expires_at: Optional[datetime] = None
    status: ArchiveStatus = ArchiveStatus.ARCHIVED
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "archive_id": self.archive_id,
            "original_path": str(self.original_path),
            "archive_path": str(self.archive_path),
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "compressed_size_bytes": self.compressed_size_bytes,
            "compression_level": self.compression_level.value,
            "retention_policy": self.retention_policy.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "checksum": self.checksum,
        }


@dataclass
class ArchiveIndex:
    """Archive index entry."""
    index_id: str
    archives: List[ArchiveMetadata]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index_id": self.index_id,
            "archives": [a.to_dict() for a in self.archives],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DatasetArchiver:
    """Archive datasets for long-term storage."""
    
    def __init__(self, archive_dir: Path):
        """Initialize archiver."""
        self.archive_dir = archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def archive_dataset(
        self,
        dataset_path: Path,
        retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM,
        compression_level: CompressionLevel = CompressionLevel.BALANCED,
    ) -> ArchiveMetadata:
        """Archive a dataset."""
        # Generate archive ID
        archive_id = hashlib.sha256(
            f"{dataset_path}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Create archive path
        archive_path = self.archive_dir / f"{archive_id}.jsonl.gz"
        
        # Get original size
        original_size = dataset_path.stat().st_size if dataset_path.exists() else 0
        
        # Compress and archive
        with open(dataset_path, 'rb') as f_in:
            with gzip.open(archive_path, 'wb', compresslevel=compression_level.value) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Get compressed size
        compressed_size = archive_path.stat().st_size
        
        # Calculate checksum
        checksum = self._calculate_checksum(archive_path)
        
        # Calculate expiration
        expires_at = self._calculate_expiration(retention_policy)
        
        metadata = ArchiveMetadata(
            archive_id=archive_id,
            original_path=dataset_path,
            archive_path=archive_path,
            created_at=datetime.now(),
            size_bytes=original_size,
            compressed_size_bytes=compressed_size,
            compression_level=compression_level,
            retention_policy=retention_policy,
            expires_at=expires_at,
            checksum=checksum,
        )
        
        return metadata
    
    def restore_dataset(
        self,
        metadata: ArchiveMetadata,
        restore_path: Path,
    ) -> bool:
        """Restore dataset from archive."""
        try:
            if not metadata.archive_path.exists():
                return False
            
            # Decompress
            with gzip.open(metadata.archive_path, 'rb') as f_in:
                with open(restore_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify integrity if checksum available
            if metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.archive_path)
                if current_checksum != metadata.checksum:
                    restore_path.unlink()  # Remove corrupted restore
                    return False
            
            return True
        
        except Exception:
            return False
    
    def delete_archive(self, metadata: ArchiveMetadata) -> bool:
        """Delete an archive."""
        try:
            if metadata.archive_path.exists():
                metadata.archive_path.unlink()
                metadata.status = ArchiveStatus.DELETED
                return True
            return False
        except Exception:
            return False
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate file checksum."""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _calculate_expiration(self, policy: RetentionPolicy) -> Optional[datetime]:
        """Calculate expiration date."""
        if policy == RetentionPolicy.PERMANENT:
            return None
        
        days_map = {
            RetentionPolicy.SHORT: 30,
            RetentionPolicy.MEDIUM: 90,
            RetentionPolicy.LONG: 365,
        }
        
        days = days_map.get(policy, 90)
        return datetime.now() + timedelta(days=days)


class ArchiveIndexManager:
    """Manage archive index."""
    
    def __init__(self, index_path: Path):
        """Initialize index manager."""
        self.index_path = index_path
        self.archives: List[ArchiveMetadata] = []
        
        if index_path.exists():
            self._load()
    
    def _load(self) -> None:
        """Load index."""
        data = json.loads(self.index_path.read_text())
        
        for archive_data in data.get("archives", []):
            metadata = ArchiveMetadata(
                archive_id=archive_data["archive_id"],
                original_path=Path(archive_data["original_path"]),
                archive_path=Path(archive_data["archive_path"]),
                created_at=datetime.fromisoformat(archive_data["created_at"]),
                size_bytes=archive_data["size_bytes"],
                compressed_size_bytes=archive_data["compressed_size_bytes"],
                compression_level=CompressionLevel(archive_data["compression_level"]),
                retention_policy=RetentionPolicy(archive_data["retention_policy"]),
                expires_at=datetime.fromisoformat(archive_data["expires_at"]) if archive_data.get("expires_at") else None,
                status=ArchiveStatus(archive_data.get("status", "archived")),
                checksum=archive_data.get("checksum"),
            )
            self.archives.append(metadata)
    
    def _save(self) -> None:
        """Save index."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        index = ArchiveIndex(
            index_id="main",
            archives=self.archives,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        self.index_path.write_text(json.dumps(index.to_dict(), indent=2))
    
    def add_archive(self, metadata: ArchiveMetadata) -> None:
        """Add archive to index."""
        self.archives.append(metadata)
        self._save()
    
    def remove_archive(self, archive_id: str) -> bool:
        """Remove archive from index."""
        original_count = len(self.archives)
        self.archives = [a for a in self.archives if a.archive_id != archive_id]
        
        if len(self.archives) < original_count:
            self._save()
            return True
        
        return False
    
    def get_archive(self, archive_id: str) -> Optional[ArchiveMetadata]:
        """Get archive by ID."""
        for archive in self.archives:
            if archive.archive_id == archive_id:
                return archive
        return None
    
    def list_archives(
        self,
        status: Optional[ArchiveStatus] = None,
    ) -> List[ArchiveMetadata]:
        """List archives."""
        if status:
            return [a for a in self.archives if a.status == status]
        return self.archives.copy()
    
    def search_archives(self, query: str) -> List[ArchiveMetadata]:
        """Search archives by original path."""
        return [
            a for a in self.archives
            if query.lower() in str(a.original_path).lower()
        ]


class RetentionPolicyManager:
    """Manage retention policies."""
    
    def __init__(self, index_manager: ArchiveIndexManager):
        """Initialize policy manager."""
        self.index_manager = index_manager
    
    def apply_retention_policies(self) -> Dict[str, Any]:
        """Apply retention policies and delete expired archives."""
        now = datetime.now()
        deleted = []
        errors = []
        
        for archive in self.index_manager.list_archives(ArchiveStatus.ARCHIVED):
            if archive.expires_at and archive.expires_at < now:
                try:
                    # Delete archive file
                    if archive.archive_path.exists():
                        archive.archive_path.unlink()
                    
                    # Update status
                    archive.status = ArchiveStatus.DELETED
                    deleted.append(archive.archive_id)
                
                except Exception as e:
                    errors.append(f"Failed to delete {archive.archive_id}: {str(e)}")
        
        # Save updated index
        self.index_manager._save()
        
        return {
            "deleted_count": len(deleted),
            "deleted_archives": deleted,
            "errors": errors,
        }
    
    def get_expiring_soon(self, days: int = 7) -> List[ArchiveMetadata]:
        """Get archives expiring soon."""
        threshold = datetime.now() + timedelta(days=days)
        
        return [
            a for a in self.index_manager.list_archives(ArchiveStatus.ARCHIVED)
            if a.expires_at and a.expires_at <= threshold
        ]


class ArchiveStatistics:
    """Calculate archive statistics."""
    
    def __init__(self, index_manager: ArchiveIndexManager):
        """Initialize statistics."""
        self.index_manager = index_manager
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get archive statistics."""
        archives = self.index_manager.list_archives()
        
        if not archives:
            return {
                "total_archives": 0,
                "total_size_bytes": 0,
                "total_compressed_bytes": 0,
                "compression_ratio": 0.0,
                "by_status": {},
                "by_retention_policy": {},
            }
        
        total_size = sum(a.size_bytes for a in archives)
        total_compressed = sum(a.compressed_size_bytes for a in archives)
        
        # Group by status
        by_status: Dict[str, int] = {}
        for archive in archives:
            status = archive.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        # Group by retention policy
        by_policy: Dict[str, int] = {}
        for archive in archives:
            policy = archive.retention_policy.value
            by_policy[policy] = by_policy.get(policy, 0) + 1
        
        compression_ratio = total_compressed / max(total_size, 1)
        
        return {
            "total_archives": len(archives),
            "total_size_bytes": total_size,
            "total_compressed_bytes": total_compressed,
            "compression_ratio": compression_ratio,
            "space_saved_bytes": total_size - total_compressed,
            "by_status": by_status,
            "by_retention_policy": by_policy,
        }
