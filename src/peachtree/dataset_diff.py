"""
PeachTree Dataset Diff Engine

Advanced dataset comparison with detailed change tracking, record-level diffs,
and visual diff reports. Complements dataset_comparison.py with granular analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib


@dataclass
class RecordChange:
    """Individual record-level change"""
    change_type: str  # added, removed, modified
    record_id: str
    old_content: dict[str, Any] | None = None
    new_content: dict[str, Any] | None = None
    field_changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type,
            "record_id": self.record_id,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "field_changes": {k: {"old": v[0], "new": v[1]} for k, v in self.field_changes.items()},
        }


@dataclass
class DatasetDiffReport:
    """Complete dataset diff report"""
    base_dataset: str
    compare_dataset: str
    base_records: int
    compare_records: int
    added_records: list[RecordChange] = field(default_factory=list)
    removed_records: list[RecordChange] = field(default_factory=list)
    modified_records: list[RecordChange] = field(default_factory=list)
    unchanged_records: int = 0
    similarity_score: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "base_dataset": self.base_dataset,
            "compare_dataset": self.compare_dataset,
            "base_records": self.base_records,
            "compare_records": self.compare_records,
            "added_count": len(self.added_records),
            "removed_count": len(self.removed_records),
            "modified_count": len(self.modified_records),
            "unchanged_count": self.unchanged_records,
            "similarity_score": self.similarity_score,
            "added_records": [r.to_dict() for r in self.added_records],
            "removed_records": [r.to_dict() for r in self.removed_records],
            "modified_records": [r.to_dict() for r in self.modified_records],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown diff report"""
        lines = [
            "# Dataset Diff Report",
            "",
            f"**Base Dataset:** `{Path(self.base_dataset).name}`",
            f"**Compare Dataset:** `{Path(self.compare_dataset).name}`",
            "",
            "## Summary",
            "",
            f"- **Base Records:** {self.base_records:,}",
            f"- **Compare Records:** {self.compare_records:,}",
            f"- **Similarity Score:** {self.similarity_score:.1f}%",
            "",
            "## Changes",
            "",
            f"- ✅ **Unchanged:** {self.unchanged_records:,} records",
            f"- ➕ **Added:** {len(self.added_records):,} records",
            f"- ➖ **Removed:** {len(self.removed_records):,} records",
            f"- 📝 **Modified:** {len(self.modified_records):,} records",
            "",
        ]
        
        if self.added_records:
            lines.extend([
                "## Added Records",
                "",
            ])
            for change in self.added_records[:10]:  # Show first 10
                lines.append(f"- **{change.record_id}**: New record")
            if len(self.added_records) > 10:
                lines.append(f"- ... and {len(self.added_records) - 10} more")
            lines.append("")
        
        if self.removed_records:
            lines.extend([
                "## Removed Records",
                "",
            ])
            for change in self.removed_records[:10]:
                lines.append(f"- **{change.record_id}**: Deleted record")
            if len(self.removed_records) > 10:
                lines.append(f"- ... and {len(self.removed_records) - 10} more")
            lines.append("")
        
        if self.modified_records:
            lines.extend([
                "## Modified Records",
                "",
            ])
            for change in self.modified_records[:10]:
                field_list = ", ".join(change.field_changes.keys())
                lines.append(f"- **{change.record_id}**: Changed fields: {field_list}")
            if len(self.modified_records) > 10:
                lines.append(f"- ... and {len(self.modified_records) - 10} more")
            lines.append("")
        
        return "\n".join(lines)


class DatasetDiffEngine:
    """Advanced dataset comparison with granular change tracking"""
    
    def __init__(self):
        """Initialize diff engine"""
        pass
    
    def _compute_record_hash(self, record: dict[str, Any]) -> str:
        """Compute content hash for record"""
        # Use content only, ignore provenance fields
        content = record.get("content", "")
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    
    def _load_dataset(self, dataset_path: Path | str) -> dict[str, dict[str, Any]]:
        """Load dataset into dict keyed by record ID"""
        dataset_path = Path(dataset_path)
        records = {}
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get("id", self._compute_record_hash(record))
                records[record_id] = record
        
        return records
    
    def diff(
        self,
        base_dataset: Path | str,
        compare_dataset: Path | str,
        compare_content: bool = True,
    ) -> DatasetDiffReport:
        """
        Compare two datasets and generate detailed diff report
        
        Args:
            base_dataset: Path to base dataset
            compare_dataset: Path to compare dataset
            compare_content: If True, detect content changes within records
        
        Returns:
            DatasetDiffReport with detailed changes
        """
        base_records = self._load_dataset(base_dataset)
        compare_records = self._load_dataset(compare_dataset)
        
        report = DatasetDiffReport(
            base_dataset=str(base_dataset),
            compare_dataset=str(compare_dataset),
            base_records=len(base_records),
            compare_records=len(compare_records),
        )
        
        base_ids = set(base_records.keys())
        compare_ids = set(compare_records.keys())
        
        # Find added records
        added_ids = compare_ids - base_ids
        for record_id in added_ids:
            report.added_records.append(RecordChange(
                change_type="added",
                record_id=record_id,
                new_content=compare_records[record_id],
            ))
        
        # Find removed records
        removed_ids = base_ids - compare_ids
        for record_id in removed_ids:
            report.removed_records.append(RecordChange(
                change_type="removed",
                record_id=record_id,
                old_content=base_records[record_id],
            ))
        
        # Find modified records
        common_ids = base_ids & compare_ids
        for record_id in common_ids:
            base_record = base_records[record_id]
            compare_record = compare_records[record_id]
            
            if compare_content:
                field_changes = self._find_field_changes(base_record, compare_record)
                
                if field_changes:
                    report.modified_records.append(RecordChange(
                        change_type="modified",
                        record_id=record_id,
                        old_content=base_record,
                        new_content=compare_record,
                        field_changes=field_changes,
                    ))
                else:
                    report.unchanged_records += 1
            else:
                report.unchanged_records += 1
        
        # Calculate similarity score
        total_records = max(len(base_records), len(compare_records))
        if total_records > 0:
            report.similarity_score = (report.unchanged_records / total_records) * 100
        
        return report
    
    def _find_field_changes(
        self,
        old_record: dict[str, Any],
        new_record: dict[str, Any],
    ) -> dict[str, tuple[Any, Any]]:
        """Find changed fields between two records"""
        changes = {}
        
        all_keys = set(old_record.keys()) | set(new_record.keys())
        
        for key in all_keys:
            old_value = old_record.get(key)
            new_value = new_record.get(key)
            
            if old_value != new_value:
                changes[key] = (old_value, new_value)
        
        return changes
    
    def generate_patch(
        self,
        base_dataset: Path | str,
        compare_dataset: Path | str,
        output_path: Path | str,
    ) -> int:
        """
        Generate patch file that transforms base into compare
        
        Returns:
            Number of operations in patch
        """
        report = self.diff(base_dataset, compare_dataset)
        
        patch_ops = []
        
        # Add operations
        for change in report.added_records:
            patch_ops.append({
                "op": "add",
                "record_id": change.record_id,
                "content": change.new_content,
            })
        
        # Remove operations
        for change in report.removed_records:
            patch_ops.append({
                "op": "remove",
                "record_id": change.record_id,
            })
        
        # Modify operations
        for change in report.modified_records:
            patch_ops.append({
                "op": "modify",
                "record_id": change.record_id,
                "field_changes": change.field_changes,
            })
        
        patch_data = {
            "base_dataset": report.base_dataset,
            "compare_dataset": report.compare_dataset,
            "generated_at": datetime.now().isoformat(),
            "operations": patch_ops,
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(patch_data, indent=2) + "\n", encoding="utf-8")
        
        return len(patch_ops)
    
    def apply_patch(
        self,
        base_dataset: Path | str,
        patch_path: Path | str,
        output_path: Path | str,
    ) -> int:
        """
        Apply patch file to base dataset
        
        Returns:
            Number of records in output dataset
        """
        base_records = self._load_dataset(base_dataset)
        
        with open(patch_path) as f:
            patch_data = json.load(f)
        
        # Apply operations
        for op in patch_data["operations"]:
            if op["op"] == "add":
                base_records[op["record_id"]] = op["content"]
            elif op["op"] == "remove":
                base_records.pop(op["record_id"], None)
            elif op["op"] == "modify":
                if op["record_id"] in base_records:
                    record = base_records[op["record_id"]]
                    for field, (old_val, new_val) in op["field_changes"].items():
                        record[field] = new_val
        
        # Write output
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for record in base_records.values():
                f.write(json.dumps(record) + "\n")
        
        return len(base_records)
    
    def find_duplicates_between_datasets(
        self,
        dataset1: Path | str,
        dataset2: Path | str,
    ) -> list[tuple[str, str]]:
        """
        Find duplicate records across two datasets
        
        Returns:
            List of (record_id_1, record_id_2) tuples
        """
        records1 = self._load_dataset(dataset1)
        records2 = self._load_dataset(dataset2)
        
        duplicates = []
        
        # Build content hash map for dataset1
        hash_to_id1 = {}
        for id1, record1 in records1.items():
            content_hash = self._compute_record_hash(record1)
            hash_to_id1[content_hash] = id1
        
        # Check dataset2 against dataset1
        for id2, record2 in records2.items():
            content_hash = self._compute_record_hash(record2)
            if content_hash in hash_to_id1:
                duplicates.append((hash_to_id1[content_hash], id2))
        
        return duplicates
