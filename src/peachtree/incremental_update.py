"""
PeachTree Incremental Dataset Updates

Efficiently update datasets with delta changes. Track additions, modifications,
and deletions without rebuilding entire datasets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib


@dataclass
class DatasetDelta:
    """Delta changes to a dataset"""
    additions: list[dict[str, Any]] = field(default_factory=list)
    modifications: list[dict[str, Any]] = field(default_factory=list)
    deletions: list[str] = field(default_factory=list)  # Record IDs
    
    def __len__(self) -> int:
        return len(self.additions) + len(self.modifications) + len(self.deletions)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "additions": self.additions,
            "modifications": self.modifications,
            "deletions": self.deletions,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class IncrementalUpdateResult:
    """Result of incremental update operation"""
    dataset_path: str
    base_records: int
    additions: int
    modifications: int
    deletions: int
    final_records: int
    update_timestamp: str
    delta_applied: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "base_records": self.base_records,
            "additions": self.additions,
            "modifications": self.modifications,
            "deletions": self.deletions,
            "final_records": self.final_records,
            "update_timestamp": self.update_timestamp,
            "delta_applied": self.delta_applied,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate markdown summary"""
        lines = [
            "# Incremental Update Result",
            "",
            f"**Dataset:** {self.dataset_path}",
            f"**Base Records:** {self.base_records:,}",
            f"**Additions:** +{self.additions:,}",
            f"**Modifications:** ~{self.modifications:,}",
            f"**Deletions:** -{self.deletions:,}",
            f"**Final Records:** {self.final_records:,}",
            f"**Status:** {'✅ Applied' if self.delta_applied else '❌ Failed'}",
            f"**Timestamp:** {self.update_timestamp}",
            "",
        ]
        
        if self.metadata:
            lines.extend(["## Metadata", ""])
            for key, value in self.metadata.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        return "\n".join(lines)


class IncrementalUpdater:
    """Apply incremental updates to datasets efficiently"""
    
    def __init__(self, id_field: str = "id"):
        """
        Initialize incremental updater
        
        Args:
            id_field: Field to use as record identifier
        """
        self.id_field = id_field
    
    def _compute_record_hash(self, record: dict[str, Any]) -> str:
        """Compute hash of record content (excluding ID)"""
        # Create copy without ID
        content = {k: v for k, v in record.items() if k != self.id_field}
        
        # Sort keys for consistent hashing
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def detect_changes(
        self,
        baseline_dataset: Path | str,
        updated_dataset: Path | str,
    ) -> DatasetDelta:
        """
        Detect changes between baseline and updated datasets
        
        Args:
            baseline_dataset: Original dataset path
            updated_dataset: New dataset path
        
        Returns:
            DatasetDelta with additions, modifications, deletions
        """
        baseline_path = Path(baseline_dataset)
        updated_path = Path(updated_dataset)
        
        # Load baseline records
        baseline_records: dict[str, dict[str, Any]] = {}
        baseline_hashes: dict[str, str] = {}
        
        with open(baseline_path) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get(self.id_field)
                
                if record_id:
                    baseline_records[record_id] = record
                    baseline_hashes[record_id] = self._compute_record_hash(record)
        
        # Compare with updated records
        delta = DatasetDelta()
        seen_ids = set()
        
        with open(updated_path) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get(self.id_field)
                
                if not record_id:
                    continue
                
                seen_ids.add(record_id)
                
                if record_id not in baseline_records:
                    # New record
                    delta.additions.append(record)
                else:
                    # Check if modified
                    updated_hash = self._compute_record_hash(record)
                    if updated_hash != baseline_hashes[record_id]:
                        delta.modifications.append(record)
        
        # Find deletions (in baseline but not in updated)
        for record_id in baseline_records:
            if record_id not in seen_ids:
                delta.deletions.append(record_id)
        
        return delta
    
    def apply_delta(
        self,
        dataset_path: Path | str,
        delta: DatasetDelta,
        output_path: Path | str | None = None,
    ) -> IncrementalUpdateResult:
        """
        Apply delta changes to a dataset
        
        Args:
            dataset_path: Dataset to update
            delta: Delta changes to apply
            output_path: Output path (if None, updates in-place)
        
        Returns:
            IncrementalUpdateResult with update statistics
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path) if output_path else dataset_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing records
        existing_records: dict[str, dict[str, Any]] = {}
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get(self.id_field)
                if record_id:
                    existing_records[record_id] = record
        
        base_count = len(existing_records)
        
        # Apply deletions
        for record_id in delta.deletions:
            existing_records.pop(record_id, None)
        
        # Apply modifications
        for record in delta.modifications:
            record_id = record.get(self.id_field)
            if record_id:
                existing_records[record_id] = record
        
        # Apply additions
        for record in delta.additions:
            record_id = record.get(self.id_field)
            if record_id:
                existing_records[record_id] = record
        
        # Write updated dataset
        with open(output_path, 'w') as f:
            for record in existing_records.values():
                f.write(json.dumps(record) + "\n")
        
        return IncrementalUpdateResult(
            dataset_path=str(output_path),
            base_records=base_count,
            additions=len(delta.additions),
            modifications=len(delta.modifications),
            deletions=len(delta.deletions),
            final_records=len(existing_records),
            update_timestamp=datetime.now().isoformat(),
            delta_applied=True,
        )
    
    def update_from_source(
        self,
        dataset_path: Path | str,
        source_dataset: Path | str,
        output_path: Path | str | None = None,
    ) -> IncrementalUpdateResult:
        """
        Update dataset from a source dataset (detects changes automatically)
        
        Args:
            dataset_path: Current dataset
            source_dataset: Source dataset with updates
            output_path: Output path (if None, updates in-place)
        
        Returns:
            IncrementalUpdateResult
        """
        # Detect changes
        delta = self.detect_changes(dataset_path, source_dataset)
        
        # Apply delta
        return self.apply_delta(dataset_path, delta, output_path)
    
    def save_delta(
        self,
        delta: DatasetDelta,
        output_path: Path | str,
    ) -> None:
        """
        Save delta to a file for later application
        
        Args:
            delta: Delta to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(delta.to_json() + "\n", encoding="utf-8")
    
    def load_delta(
        self,
        delta_path: Path | str,
    ) -> DatasetDelta:
        """
        Load delta from a file
        
        Args:
            delta_path: Delta file path
        
        Returns:
            DatasetDelta
        """
        delta_path = Path(delta_path)
        data = json.loads(delta_path.read_text(encoding="utf-8"))
        
        return DatasetDelta(
            additions=data.get("additions", []),
            modifications=data.get("modifications", []),
            deletions=data.get("deletions", []),
        )


class ChangeTracker:
    """Track changes to datasets over time"""
    
    def __init__(self, history_dir: Path | str):
        """
        Initialize change tracker
        
        Args:
            history_dir: Directory to store change history
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def record_change(
        self,
        dataset_name: str,
        delta: DatasetDelta,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a change to history
        
        Args:
            dataset_name: Name of dataset
            delta: Delta changes
            metadata: Optional metadata
        
        Returns:
            Path to recorded change file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_name}_{timestamp}_delta.json"
        filepath = self.history_dir / filename
        
        change_record = {
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "delta": delta.to_dict(),
            "metadata": metadata or {},
        }
        
        filepath.write_text(json.dumps(change_record, indent=2) + "\n", encoding="utf-8")
        
        return str(filepath)
    
    def get_history(
        self,
        dataset_name: str,
    ) -> list[dict[str, Any]]:
        """
        Get change history for a dataset
        
        Args:
            dataset_name: Dataset name
        
        Returns:
            List of change records
        """
        history = []
        
        for filepath in sorted(self.history_dir.glob(f"{dataset_name}_*_delta.json")):
            change_record = json.loads(filepath.read_text(encoding="utf-8"))
            history.append(change_record)
        
        return history
    
    def generate_changelog(
        self,
        dataset_name: str,
        output_path: Path | str | None = None,
    ) -> str:
        """
        Generate markdown changelog
        
        Args:
            dataset_name: Dataset name
            output_path: Optional output file path
        
        Returns:
            Markdown changelog
        """
        history = self.get_history(dataset_name)
        
        lines = [
            f"# {dataset_name} - Change Log",
            "",
            f"**Total Changes:** {len(history)}",
            "",
        ]
        
        for change in reversed(history):  # Most recent first
            timestamp = change["timestamp"]
            delta = change["delta"]
            
            additions = len(delta.get("additions", []))
            modifications = len(delta.get("modifications", []))
            deletions = len(delta.get("deletions", []))
            
            lines.extend([
                f"## {timestamp}",
                "",
                f"- **Additions:** +{additions}",
                f"- **Modifications:** ~{modifications}",
                f"- **Deletions:** -{deletions}",
                "",
            ])
        
        changelog = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(changelog + "\n", encoding="utf-8")
        
        return changelog
