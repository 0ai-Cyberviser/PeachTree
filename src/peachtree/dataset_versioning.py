"""Dataset versioning with Git-like semantics for tracking dataset changes."""

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class VersionStatus(Enum):
    """Status of a version."""
    
    DRAFT = "draft"
    COMMITTED = "committed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChangeType(Enum):
    """Type of change in a version."""
    
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class VersionMetadata:
    """Metadata for a dataset version."""
    
    version_id: str
    parent_version_id: Optional[str]
    message: str
    author: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    status: VersionStatus = VersionStatus.COMMITTED
    tags: List[str] = field(default_factory=list)
    record_count: int = 0
    size_bytes: int = 0
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "parent_version_id": self.parent_version_id,
            "message": self.message,
            "author": self.author,
            "created_at": self.created_at,
            "status": self.status.value,
            "tags": self.tags,
            "record_count": self.record_count,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
        }


@dataclass
class VersionDiff:
    """Diff between two versions."""
    
    from_version: str
    to_version: str
    added_records: int = 0
    modified_records: int = 0
    deleted_records: int = 0
    changes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "added_records": self.added_records,
            "modified_records": self.modified_records,
            "deleted_records": self.deleted_records,
            "total_changes": self.added_records + self.modified_records + self.deleted_records,
            "changes": self.changes,
        }


class DatasetVersionControl:
    """Version control for datasets with Git-like operations."""
    
    def __init__(self, repository_path: Path):
        """Initialize version control repository."""
        self.repo_path = repository_path
        self.versions_dir = repository_path / ".versions"
        self.metadata_file = self.versions_dir / "metadata.json"
        self.head_file = self.versions_dir / "HEAD"
        
        # Initialize repository structure
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions: Dict[str, VersionMetadata] = {}
        self.head: Optional[str] = None
        
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load version metadata from disk."""
        if self.metadata_file.exists():
            with self.metadata_file.open("r") as f:
                data = json.load(f)
                
                for version_data in data.get("versions", []):
                    metadata = VersionMetadata(
                        version_id=version_data["version_id"],
                        parent_version_id=version_data.get("parent_version_id"),
                        message=version_data["message"],
                        author=version_data["author"],
                        created_at=version_data.get("created_at", ""),
                        status=VersionStatus(version_data.get("status", "committed")),
                        tags=version_data.get("tags", []),
                        record_count=version_data.get("record_count", 0),
                        size_bytes=version_data.get("size_bytes", 0),
                        checksum=version_data.get("checksum", ""),
                    )
                    self.versions[metadata.version_id] = metadata
        
        if self.head_file.exists():
            self.head = self.head_file.read_text().strip()
    
    def _save_metadata(self) -> None:
        """Save version metadata to disk."""
        data = {
            "versions": [v.to_dict() for v in self.versions.values()],
        }
        
        with self.metadata_file.open("w") as f:
            json.dump(data, f, indent=2)
        
        if self.head:
            self.head_file.write_text(self.head)
    
    def _compute_checksum(self, dataset_path: Path) -> str:
        """Compute SHA256 checksum of dataset."""
        sha256 = hashlib.sha256()
        
        with dataset_path.open("rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _generate_version_id(self) -> str:
        """Generate unique version ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def commit(
        self,
        dataset_path: Path,
        message: str,
        author: str,
        tags: Optional[List[str]] = None,
    ) -> VersionMetadata:
        """Create a new version (commit) of the dataset."""
        version_id = self._generate_version_id()
        
        # Count records
        record_count = 0
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record_count += 1
        
        # Compute checksum
        checksum = self._compute_checksum(dataset_path)
        
        # Get file size
        size_bytes = dataset_path.stat().st_size
        
        # Create version directory and copy dataset
        version_dir = self.versions_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        version_file = version_dir / "dataset.jsonl"
        shutil.copy2(dataset_path, version_file)
        
        # Create metadata
        metadata = VersionMetadata(
            version_id=version_id,
            parent_version_id=self.head,
            message=message,
            author=author,
            tags=tags or [],
            record_count=record_count,
            size_bytes=size_bytes,
            checksum=checksum,
            status=VersionStatus.COMMITTED,
        )
        
        self.versions[version_id] = metadata
        self.head = version_id
        
        self._save_metadata()
        
        return metadata
    
    def checkout(self, version_id: str, output_path: Path) -> bool:
        """Checkout a specific version to output path."""
        if version_id not in self.versions:
            return False
        
        version_dir = self.versions_dir / version_id
        version_file = version_dir / "dataset.jsonl"
        
        if not version_file.exists():
            return False
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(version_file, output_path)
        
        self.head = version_id
        self._save_metadata()
        
        return True
    
    def diff(self, from_version: str, to_version: str) -> VersionDiff:
        """Compute diff between two versions."""
        if from_version not in self.versions or to_version not in self.versions:
            raise ValueError("Version not found")
        
        from_file = self.versions_dir / from_version / "dataset.jsonl"
        to_file = self.versions_dir / to_version / "dataset.jsonl"
        
        # Load records
        from_records = {}
        with from_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    record_id = record.get("id", str(hash(line)))
                    from_records[record_id] = record
                except json.JSONDecodeError:
                    continue
        
        to_records = {}
        with to_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    record_id = record.get("id", str(hash(line)))
                    to_records[record_id] = record
                except json.JSONDecodeError:
                    continue
        
        # Compute changes
        from_ids = set(from_records.keys())
        to_ids = set(to_records.keys())
        
        added = to_ids - from_ids
        deleted = from_ids - to_ids
        common = from_ids & to_ids
        
        modified = set()
        for record_id in common:
            if from_records[record_id] != to_records[record_id]:
                modified.add(record_id)
        
        # Build diff
        diff = VersionDiff(
            from_version=from_version,
            to_version=to_version,
            added_records=len(added),
            modified_records=len(modified),
            deleted_records=len(deleted),
        )
        
        # Add detailed changes (limited to first 100)
        for record_id in list(added)[:100]:
            diff.changes.append({
                "type": "added",
                "record_id": record_id,
                "record": to_records[record_id],
            })
        
        for record_id in list(modified)[:100]:
            diff.changes.append({
                "type": "modified",
                "record_id": record_id,
                "from_record": from_records[record_id],
                "to_record": to_records[record_id],
            })
        
        for record_id in list(deleted)[:100]:
            diff.changes.append({
                "type": "deleted",
                "record_id": record_id,
                "record": from_records[record_id],
            })
        
        return diff
    
    def list_versions(self) -> List[VersionMetadata]:
        """List all versions."""
        return sorted(
            self.versions.values(),
            key=lambda v: v.created_at,
            reverse=True,
        )
    
    def get_version(self, version_id: str) -> Optional[VersionMetadata]:
        """Get metadata for a specific version."""
        return self.versions.get(version_id)
    
    def tag_version(self, version_id: str, tag: str) -> bool:
        """Add tag to a version."""
        if version_id not in self.versions:
            return False
        
        if tag not in self.versions[version_id].tags:
            self.versions[version_id].tags.append(tag)
            self._save_metadata()
        
        return True
    
    def get_version_by_tag(self, tag: str) -> Optional[VersionMetadata]:
        """Get version by tag."""
        for version in self.versions.values():
            if tag in version.tags:
                return version
        
        return None
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a version (soft delete)."""
        if version_id not in self.versions:
            return False
        
        self.versions[version_id].status = VersionStatus.DELETED
        self._save_metadata()
        
        return True
    
    def get_history(self, version_id: Optional[str] = None) -> List[VersionMetadata]:
        """Get version history starting from a version."""
        if version_id is None:
            version_id = self.head
        
        if not version_id or version_id not in self.versions:
            return []
        
        history = []
        current = version_id
        
        while current:
            version = self.versions[current]
            history.append(version)
            current = version.parent_version_id
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        total_versions = len(self.versions)
        committed = sum(1 for v in self.versions.values() if v.status == VersionStatus.COMMITTED)
        total_size = sum(v.size_bytes for v in self.versions.values())
        
        authors = set(v.author for v in self.versions.values())
        tags = set(tag for v in self.versions.values() for tag in v.tags)
        
        return {
            "total_versions": total_versions,
            "committed_versions": committed,
            "total_size_bytes": total_size,
            "unique_authors": len(authors),
            "total_tags": len(tags),
            "head_version": self.head,
        }
