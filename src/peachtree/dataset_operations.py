"""
PeachTree Dataset Merge & Split Operations

Combine multiple datasets or split large datasets into smaller chunks.
Supports stratified splitting, merge deduplication, and metadata preservation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib
import random


@dataclass
class MergeResult:
    """Result of merging datasets"""
    output_path: str
    source_datasets: list[str]
    total_records: int
    records_per_source: dict[str, int]
    duplicates_removed: int
    merge_timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "source_datasets": self.source_datasets,
            "total_records": self.total_records,
            "records_per_source": self.records_per_source,
            "duplicates_removed": self.duplicates_removed,
            "merge_timestamp": self.merge_timestamp,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate markdown summary"""
        lines = [
            "# Dataset Merge Result",
            "",
            f"**Output:** {self.output_path}",
            f"**Total Records:** {self.total_records:,}",
            f"**Source Datasets:** {len(self.source_datasets)}",
            f"**Duplicates Removed:** {self.duplicates_removed:,}",
            f"**Timestamp:** {self.merge_timestamp}",
            "",
            "## Source Breakdown",
            "",
            "| Source | Records |",
            "|--------|---------|",
        ]
        
        for source, count in self.records_per_source.items():
            lines.append(f"| {Path(source).name} | {count:,} |")
        
        lines.extend(["", ""])
        return "\n".join(lines)


@dataclass
class SplitResult:
    """Result of splitting a dataset"""
    source_dataset: str
    output_files: list[str]
    split_strategy: str
    records_per_split: dict[str, int]
    total_records: int
    split_timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dataset": self.source_dataset,
            "output_files": self.output_files,
            "split_strategy": self.split_strategy,
            "records_per_split": self.records_per_split,
            "total_records": self.total_records,
            "split_timestamp": self.split_timestamp,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate markdown summary"""
        lines = [
            "# Dataset Split Result",
            "",
            f"**Source:** {self.source_dataset}",
            f"**Strategy:** {self.split_strategy}",
            f"**Total Records:** {self.total_records:,}",
            f"**Output Files:** {len(self.output_files)}",
            f"**Timestamp:** {self.split_timestamp}",
            "",
            "## Output Files",
            "",
            "| File | Records | Percentage |",
            "|------|---------|------------|",
        ]
        
        for output_file, count in self.records_per_split.items():
            percentage = (count / self.total_records) * 100 if self.total_records > 0 else 0
            lines.append(f"| {Path(output_file).name} | {count:,} | {percentage:.1f}% |")
        
        lines.extend(["", ""])
        return "\n".join(lines)


class DatasetMerger:
    """Merge multiple datasets into one"""
    
    def __init__(self):
        """Initialize dataset merger"""
        self.seen_digests: set[str] = set()
    
    def _calculate_record_digest(self, record: dict[str, Any]) -> str:
        """Calculate digest for deduplication"""
        # Use content field for deduplication
        content = record.get("content", "")
        return hashlib.sha256(content.encode()).hexdigest()
    
    def merge(
        self,
        source_datasets: list[Path | str],
        output_path: Path | str,
        remove_duplicates: bool = True,
        preserve_source_metadata: bool = True,
    ) -> MergeResult:
        """
        Merge multiple datasets into one
        
        Args:
            source_datasets: List of dataset paths to merge
            output_path: Output merged dataset path
            remove_duplicates: Remove duplicate records during merge
            preserve_source_metadata: Add source dataset info to metadata
        
        Returns:
            MergeResult with merge statistics
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        records_per_source: dict[str, int] = {}
        total_records = 0
        duplicates_removed = 0
        self.seen_digests = set()
        
        with open(output_path, 'w') as out_file:
            for source_dataset in source_datasets:
                source_path = Path(source_dataset)
                source_count = 0
                
                with open(source_path) as in_file:
                    for line in in_file:
                        if not line.strip():
                            continue
                        
                        record = json.loads(line)
                        
                        # Check for duplicates
                        if remove_duplicates:
                            digest = self._calculate_record_digest(record)
                            if digest in self.seen_digests:
                                duplicates_removed += 1
                                continue
                            self.seen_digests.add(digest)
                        
                        # Add source metadata if requested
                        if preserve_source_metadata:
                            if "metadata" not in record:
                                record["metadata"] = {}
                            record["metadata"]["merge_source"] = str(source_path)
                        
                        out_file.write(json.dumps(record) + "\n")
                        source_count += 1
                        total_records += 1
                
                records_per_source[str(source_path)] = source_count
        
        return MergeResult(
            output_path=str(output_path),
            source_datasets=[str(p) for p in source_datasets],
            total_records=total_records,
            records_per_source=records_per_source,
            duplicates_removed=duplicates_removed,
            merge_timestamp=datetime.now().isoformat(),
        )


class DatasetSplitter:
    """Split datasets into smaller chunks"""
    
    def __init__(self):
        """Initialize dataset splitter"""
        pass
    
    def split_by_count(
        self,
        source_dataset: Path | str,
        output_dir: Path | str,
        split_count: int,
        prefix: str = "split",
    ) -> SplitResult:
        """
        Split dataset into N equal parts
        
        Args:
            source_dataset: Source dataset path
            output_dir: Output directory for splits
            split_count: Number of splits to create
            prefix: Prefix for output filenames
        
        Returns:
            SplitResult with split statistics
        """
        source_path = Path(source_dataset)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Count total records
        total_records = sum(1 for line in open(source_path) if line.strip())
        records_per_split_target = total_records // split_count
        
        # Create splits
        output_files: list[str] = []
        records_per_split: dict[str, int] = {}
        
        current_split = 0
        current_count = 0
        current_file = None
        
        with open(source_path) as in_file:
            for line in in_file:
                if not line.strip():
                    continue
                
                # Open new split file if needed
                if current_file is None or (current_count >= records_per_split_target and current_split < split_count - 1):
                    if current_file:
                        current_file.close()
                    
                    split_filename = f"{prefix}-{current_split:03d}.jsonl"
                    split_path = output_dir / split_filename
                    current_file = open(split_path, 'w')
                    output_files.append(str(split_path))
                    records_per_split[str(split_path)] = 0
                    current_count = 0
                    current_split += 1
                
                current_file.write(line)
                records_per_split[str(output_files[-1])] += 1
                current_count += 1
        
        if current_file:
            current_file.close()
        
        return SplitResult(
            source_dataset=str(source_path),
            output_files=output_files,
            split_strategy="by_count",
            records_per_split=records_per_split,
            total_records=total_records,
            split_timestamp=datetime.now().isoformat(),
        )
    
    def split_by_ratio(
        self,
        source_dataset: Path | str,
        output_dir: Path | str,
        ratios: dict[str, float],
        shuffle: bool = True,
        seed: int | None = None,
    ) -> SplitResult:
        """
        Split dataset by specified ratios (e.g., train/val/test)
        
        Args:
            source_dataset: Source dataset path
            output_dir: Output directory for splits
            ratios: Dict of split name to ratio (e.g., {"train": 0.8, "val": 0.1, "test": 0.1})
            shuffle: Shuffle records before splitting
            seed: Random seed for reproducibility
        
        Returns:
            SplitResult with split statistics
        """
        source_path = Path(source_dataset)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate ratios sum to 1.0
        ratio_sum = sum(ratios.values())
        if not (0.99 <= ratio_sum <= 1.01):
            raise ValueError(f"Ratios must sum to 1.0, got {ratio_sum}")
        
        # Load all records
        records = []
        with open(source_path) as in_file:
            for line in in_file:
                if line.strip():
                    records.append(line)
        
        total_records = len(records)
        
        # Shuffle if requested
        if shuffle:
            if seed is not None:
                random.seed(seed)
            random.shuffle(records)
        
        # Calculate split sizes
        split_sizes: dict[str, int] = {}
        remaining = total_records
        split_names = list(ratios.keys())
        
        for i, name in enumerate(split_names[:-1]):
            size = int(total_records * ratios[name])
            split_sizes[name] = size
            remaining -= size
        # Last split gets remaining records
        split_sizes[split_names[-1]] = remaining
        
        # Write splits
        output_files: list[str] = []
        records_per_split: dict[str, int] = {}
        current_idx = 0
        
        for name, size in split_sizes.items():
            split_path = output_dir / f"{name}.jsonl"
            output_files.append(str(split_path))
            
            with open(split_path, 'w') as out_file:
                for i in range(size):
                    out_file.write(records[current_idx])
                    current_idx += 1
            
            records_per_split[str(split_path)] = size
        
        return SplitResult(
            source_dataset=str(source_path),
            output_files=output_files,
            split_strategy=f"by_ratio({'_shuffled' if shuffle else ''})",
            records_per_split=records_per_split,
            total_records=total_records,
            split_timestamp=datetime.now().isoformat(),
            metadata={"ratios": ratios, "shuffle": shuffle, "seed": seed},
        )
    
    def split_by_size(
        self,
        source_dataset: Path | str,
        output_dir: Path | str,
        max_records_per_split: int,
        prefix: str = "chunk",
    ) -> SplitResult:
        """
        Split dataset into chunks of maximum size
        
        Args:
            source_dataset: Source dataset path
            output_dir: Output directory for splits
            max_records_per_split: Maximum records per split file
            prefix: Prefix for output filenames
        
        Returns:
            SplitResult with split statistics
        """
        source_path = Path(source_dataset)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files: list[str] = []
        records_per_split: dict[str, int] = {}
        total_records = 0
        
        current_split = 0
        current_count = 0
        current_file = None
        
        with open(source_path) as in_file:
            for line in in_file:
                if not line.strip():
                    continue
                
                # Open new split file if needed
                if current_file is None or current_count >= max_records_per_split:
                    if current_file:
                        current_file.close()
                    
                    split_filename = f"{prefix}-{current_split:04d}.jsonl"
                    split_path = output_dir / split_filename
                    current_file = open(split_path, 'w')
                    output_files.append(str(split_path))
                    records_per_split[str(split_path)] = 0
                    current_count = 0
                    current_split += 1
                
                current_file.write(line)
                records_per_split[str(output_files[-1])] += 1
                current_count += 1
                total_records += 1
        
        if current_file:
            current_file.close()
        
        return SplitResult(
            source_dataset=str(source_path),
            output_files=output_files,
            split_strategy="by_size",
            records_per_split=records_per_split,
            total_records=total_records,
            split_timestamp=datetime.now().isoformat(),
            metadata={"max_records_per_split": max_records_per_split},
        )
