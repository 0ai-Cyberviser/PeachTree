"""
PeachTree Dataset Versioning System

Track dataset versions, maintain changelog, enable rollback, and manage version history.
Provides git-like versioning for JSONL datasets with snapshots and diffs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib
import shutil


@dataclass(frozen=True)
class DatasetVersion:
    """Single dataset version entry"""
    version: str  # e.g., "v1.0.0" or "1.2.3"
    timestamp: str  # ISO 8601 format
    dataset_path: str
    snapshot_path: str  # Path to archived snapshot
    digest: str  # SHA256 of dataset content
    record_count: int
    size_bytes: int
    message: str  # Commit message
    author: str  # Who created this version
    parent_version: str | None = None  # Previous version
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "dataset_path": self.dataset_path,
            "snapshot_path": self.snapshot_path,
            "digest": self.digest,
            "record_count": self.record_count,
            "size_bytes": self.size_bytes,
            "message": self.message,
            "author": self.author,
            "parent_version": self.parent_version,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class VersionHistory:
    """Complete version history for a dataset"""
    dataset_name: str
    versions: list[DatasetVersion] = field(default_factory=list)
    
    def add_version(self, version: DatasetVersion) -> None:
        """Add a version to history"""
        self.versions.append(version)
    
    def get_version(self, version: str) -> DatasetVersion | None:
        """Get specific version by version string"""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def get_latest(self) -> DatasetVersion | None:
        """Get the most recent version"""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.timestamp)
    
    def get_by_tag(self, tag: str) -> list[DatasetVersion]:
        """Get all versions with a specific tag"""
        return [v for v in self.versions if tag in v.tags]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "version_count": len(self.versions),
            "versions": [v.to_dict() for v in self.versions],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_changelog(self) -> str:
        """Generate a changelog in markdown format"""
        lines = [f"# Changelog: {self.dataset_name}", ""]
        
        # Sort versions by timestamp (newest first)
        sorted_versions = sorted(
            self.versions,
            key=lambda v: v.timestamp,
            reverse=True
        )
        
        for version in sorted_versions:
            lines.append(f"## {version.version} - {version.timestamp[:10]}")
            lines.append("")
            lines.append(f"**Author:** {version.author}")
            lines.append(f"**Records:** {version.record_count:,}")
            lines.append(f"**Size:** {version.size_bytes:,} bytes")
            if version.parent_version:
                lines.append(f"**Parent:** {version.parent_version}")
            if version.tags:
                lines.append(f"**Tags:** {', '.join(version.tags)}")
            lines.append("")
            lines.append(version.message)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)


class DatasetVersionManager:
    """Manage dataset versions with snapshots and rollback"""
    
    def __init__(self, version_dir: Path | str = ".peachtree/versions"):
        """
        Initialize version manager
        
        Args:
            version_dir: Directory to store version snapshots and metadata
        """
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_digest(self, dataset_path: Path) -> str:
        """Calculate SHA256 digest of dataset file"""
        sha256 = hashlib.sha256()
        with open(dataset_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _count_records(self, dataset_path: Path) -> int:
        """Count records in JSONL dataset"""
        count = 0
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    
    def _get_history_path(self, dataset_name: str) -> Path:
        """Get path to version history file"""
        return self.version_dir / f"{dataset_name}.history.json"
    
    def _load_history(self, dataset_name: str) -> VersionHistory:
        """Load version history from disk"""
        history_path = self._get_history_path(dataset_name)
        
        if not history_path.exists():
            return VersionHistory(dataset_name=dataset_name)
        
        data = json.loads(history_path.read_text())
        history = VersionHistory(dataset_name=dataset_name)
        
        for v_data in data.get("versions", []):
            version = DatasetVersion(
                version=v_data["version"],
                timestamp=v_data["timestamp"],
                dataset_path=v_data["dataset_path"],
                snapshot_path=v_data["snapshot_path"],
                digest=v_data["digest"],
                record_count=v_data["record_count"],
                size_bytes=v_data["size_bytes"],
                message=v_data["message"],
                author=v_data["author"],
                parent_version=v_data.get("parent_version"),
                tags=v_data.get("tags", []),
                metadata=v_data.get("metadata", {}),
            )
            history.add_version(version)
        
        return history
    
    def _save_history(self, history: VersionHistory) -> None:
        """Save version history to disk"""
        history_path = self._get_history_path(history.dataset_name)
        history_path.write_text(history.to_json())
    
    def create_version(
        self,
        dataset_path: Path | str,
        version: str,
        message: str,
        author: str = "peachtree",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        """
        Create a new dataset version
        
        Args:
            dataset_path: Path to dataset file
            version: Version string (e.g., "v1.0.0", "1.2.3")
            message: Commit message describing changes
            author: Author of this version
            tags: Optional tags (e.g., ["stable", "production"])
            metadata: Optional metadata dictionary
        
        Returns:
            Created DatasetVersion object
        """
        dataset_path = Path(dataset_path)
        dataset_name = dataset_path.stem
        
        # Load existing history
        history = self._load_history(dataset_name)
        
        # Get parent version
        latest = history.get_latest()
        parent_version = latest.version if latest else None
        
        # Calculate metrics
        digest = self._calculate_digest(dataset_path)
        record_count = self._count_records(dataset_path)
        size_bytes = dataset_path.stat().st_size
        
        # Create snapshot
        snapshot_dir = self.version_dir / dataset_name / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{version}.jsonl"
        shutil.copy2(dataset_path, snapshot_path)
        
        # Create version object
        dataset_version = DatasetVersion(
            version=version,
            timestamp=datetime.now().isoformat(),
            dataset_path=str(dataset_path),
            snapshot_path=str(snapshot_path),
            digest=digest,
            record_count=record_count,
            size_bytes=size_bytes,
            message=message,
            author=author,
            parent_version=parent_version,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        # Add to history and save
        history.add_version(dataset_version)
        self._save_history(history)
        
        return dataset_version
    
    def get_version(self, dataset_name: str, version: str) -> DatasetVersion | None:
        """Get a specific version by version string"""
        history = self._load_history(dataset_name)
        return history.get_version(version)
    
    def get_latest_version(self, dataset_name: str) -> DatasetVersion | None:
        """Get the latest version of a dataset"""
        history = self._load_history(dataset_name)
        return history.get_latest()
    
    def list_versions(self, dataset_name: str) -> list[DatasetVersion]:
        """List all versions for a dataset"""
        history = self._load_history(dataset_name)
        return sorted(history.versions, key=lambda v: v.timestamp, reverse=True)
    
    def rollback(
        self,
        dataset_name: str,
        target_version: str,
        output_path: Path | str | None = None,
    ) -> Path:
        """
        Rollback dataset to a previous version
        
        Args:
            dataset_name: Name of the dataset
            target_version: Version to rollback to
            output_path: Optional output path (defaults to original dataset path)
        
        Returns:
            Path to rolled-back dataset
        """
        version = self.get_version(dataset_name, target_version)
        
        if version is None:
            raise ValueError(f"Version {target_version} not found for dataset {dataset_name}")
        
        snapshot_path = Path(version.snapshot_path)
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
        # Determine output path
        if output_path is None:
            output_path = Path(version.dataset_path)
        else:
            output_path = Path(output_path)
        
        # Copy snapshot to output
        shutil.copy2(snapshot_path, output_path)
        
        return output_path
    
    def tag_version(
        self,
        dataset_name: str,
        version: str,
        tag: str,
    ) -> None:
        """
        Add a tag to an existing version
        
        Args:
            dataset_name: Name of the dataset
            version: Version to tag
            tag: Tag to add (e.g., "stable", "production", "v1.0-release")
        """
        history = self._load_history(dataset_name)
        version_obj = history.get_version(version)
        
        if version_obj is None:
            raise ValueError(f"Version {version} not found")
        
        # Create new version with updated tags (since frozen dataclass)
        updated_tags = list(version_obj.tags)
        if tag not in updated_tags:
            updated_tags.append(tag)
        
        new_version = DatasetVersion(
            version=version_obj.version,
            timestamp=version_obj.timestamp,
            dataset_path=version_obj.dataset_path,
            snapshot_path=version_obj.snapshot_path,
            digest=version_obj.digest,
            record_count=version_obj.record_count,
            size_bytes=version_obj.size_bytes,
            message=version_obj.message,
            author=version_obj.author,
            parent_version=version_obj.parent_version,
            tags=updated_tags,
            metadata=version_obj.metadata,
        )
        
        # Replace in history
        history.versions = [
            new_version if v.version == version else v
            for v in history.versions
        ]
        
        self._save_history(history)
    
    def generate_changelog(
        self,
        dataset_name: str,
        output_path: Path | str | None = None,
    ) -> str:
        """
        Generate changelog for a dataset
        
        Args:
            dataset_name: Name of the dataset
            output_path: Optional path to write changelog
        
        Returns:
            Changelog markdown string
        """
        history = self._load_history(dataset_name)
        changelog = history.to_changelog()
        
        if output_path:
            Path(output_path).write_text(changelog)
        
        return changelog
    
    def compare_versions(
        self,
        dataset_name: str,
        version1: str,
        version2: str,
    ) -> dict[str, Any]:
        """
        Compare two versions of a dataset
        
        Args:
            dataset_name: Name of the dataset
            version1: First version (usually older)
            version2: Second version (usually newer)
        
        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version(dataset_name, version1)
        v2 = self.get_version(dataset_name, version2)
        
        if v1 is None:
            raise ValueError(f"Version {version1} not found")
        if v2 is None:
            raise ValueError(f"Version {version2} not found")
        
        return {
            "dataset_name": dataset_name,
            "version1": version1,
            "version2": version2,
            "record_count_delta": v2.record_count - v1.record_count,
            "size_delta_bytes": v2.size_bytes - v1.size_bytes,
            "time_between": v2.timestamp,
            "digest_changed": v1.digest != v2.digest,
            "version1_metadata": v1.to_dict(),
            "version2_metadata": v2.to_dict(),
        }
