"""Horizontal partitioning (sharding) for distributed dataset processing."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ShardingStrategy(Enum):
    """Strategies for sharding datasets."""
    
    HASH = "hash"
    RANGE = "range"
    LIST = "list"
    ROUND_ROBIN = "round_robin"
    CONSISTENT_HASH = "consistent_hash"


class ShardStatus(Enum):
    """Status of a shard."""
    
    ACTIVE = "active"
    READONLY = "readonly"
    MIGRATING = "migrating"
    INACTIVE = "inactive"


@dataclass
class ShardMetadata:
    """Metadata for a dataset shard."""
    
    shard_id: str
    shard_index: int
    total_shards: int
    record_count: int
    file_size_bytes: int
    shard_key_field: str
    shard_strategy: ShardingStrategy
    status: ShardStatus = ShardStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    shard_range: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "shard_id": self.shard_id,
            "shard_index": self.shard_index,
            "total_shards": self.total_shards,
            "record_count": self.record_count,
            "file_size_bytes": self.file_size_bytes,
            "shard_key_field": self.shard_key_field,
            "shard_strategy": self.shard_strategy.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "shard_range": self.shard_range,
        }


@dataclass
class ShardingConfig:
    """Configuration for sharding operations."""
    
    num_shards: int
    shard_key_field: str
    strategy: ShardingStrategy
    replication_factor: int = 1
    auto_balance: bool = True
    max_shard_size_mb: int = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "num_shards": self.num_shards,
            "shard_key_field": self.shard_key_field,
            "strategy": self.strategy.value,
            "replication_factor": self.replication_factor,
            "auto_balance": self.auto_balance,
            "max_shard_size_mb": self.max_shard_size_mb,
        }


class DatasetSharder:
    """Shard datasets for distributed processing."""
    
    def __init__(self, config: ShardingConfig):
        """Initialize sharder with configuration."""
        self.config = config
        self.shards: Dict[str, ShardMetadata] = {}
    
    def _hash_shard(self, value: Any) -> int:
        """Compute shard index using hash strategy."""
        hash_value = hashlib.md5(str(value).encode()).hexdigest()
        return int(hash_value, 16) % self.config.num_shards
    
    def _range_shard(self, value: Any, ranges: List[tuple]) -> int:
        """Compute shard index using range strategy."""
        for i, (start, end) in enumerate(ranges):
            if start <= value < end:
                return i
        return self.config.num_shards - 1  # Default to last shard
    
    def _list_shard(self, value: Any, lists: List[List[Any]]) -> int:
        """Compute shard index using list strategy."""
        for i, value_list in enumerate(lists):
            if value in value_list:
                return i
        return self.config.num_shards - 1  # Default to last shard
    
    def _round_robin_shard(self, index: int) -> int:
        """Compute shard index using round-robin strategy."""
        return index % self.config.num_shards
    
    def _consistent_hash_shard(self, value: Any) -> int:
        """Compute shard index using consistent hashing."""
        # Simple consistent hashing implementation
        hash_value = hashlib.sha256(str(value).encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)
        return hash_int % self.config.num_shards
    
    def compute_shard_index(
        self,
        record: Dict[str, Any],
        record_index: int = 0,
        ranges: Optional[List[tuple]] = None,
        lists: Optional[List[List[Any]]] = None,
    ) -> int:
        """Compute which shard a record belongs to."""
        shard_value = record.get(self.config.shard_key_field)
        
        if self.config.strategy == ShardingStrategy.HASH:
            return self._hash_shard(shard_value)
        
        elif self.config.strategy == ShardingStrategy.RANGE:
            if not ranges:
                raise ValueError("Range strategy requires ranges parameter")
            return self._range_shard(shard_value, ranges)
        
        elif self.config.strategy == ShardingStrategy.LIST:
            if not lists:
                raise ValueError("List strategy requires lists parameter")
            return self._list_shard(shard_value, lists)
        
        elif self.config.strategy == ShardingStrategy.ROUND_ROBIN:
            return self._round_robin_shard(record_index)
        
        elif self.config.strategy == ShardingStrategy.CONSISTENT_HASH:
            return self._consistent_hash_shard(shard_value)
        
        else:
            return 0  # Default to first shard
    
    def shard_dataset(
        self,
        input_path: Path,
        output_dir: Path,
        prefix: str = "shard",
        ranges: Optional[List[tuple]] = None,
        lists: Optional[List[List[Any]]] = None,
    ) -> List[ShardMetadata]:
        """Shard dataset into multiple files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open shard files
        shard_files = {}
        shard_counts = [0] * self.config.num_shards
        
        try:
            # Create shard files
            for i in range(self.config.num_shards):
                shard_path = output_dir / f"{prefix}_{i:04d}.jsonl"
                shard_files[i] = shard_path.open("w", encoding="utf-8")
            
            # Read and distribute records
            with input_path.open("r", encoding="utf-8") as f:
                for record_index, line in enumerate(f):
                    if not line.strip():
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Compute shard
                        shard_index = self.compute_shard_index(
                            record,
                            record_index,
                            ranges,
                            lists,
                        )
                        
                        # Write to shard
                        shard_files[shard_index].write(line)
                        shard_counts[shard_index] += 1
                    
                    except json.JSONDecodeError:
                        continue
        
        finally:
            # Close all shard files
            for f in shard_files.values():
                f.close()
        
        # Create shard metadata
        shards = []
        for i in range(self.config.num_shards):
            shard_path = output_dir / f"{prefix}_{i:04d}.jsonl"
            
            metadata = ShardMetadata(
                shard_id=f"{prefix}_{i:04d}",
                shard_index=i,
                total_shards=self.config.num_shards,
                record_count=shard_counts[i],
                file_size_bytes=shard_path.stat().st_size if shard_path.exists() else 0,
                shard_key_field=self.config.shard_key_field,
                shard_strategy=self.config.strategy,
            )
            
            shards.append(metadata)
            self.shards[metadata.shard_id] = metadata
        
        return shards
    
    def merge_shards(
        self,
        shard_dir: Path,
        output_path: Path,
        prefix: str = "shard",
    ) -> Dict[str, Any]:
        """Merge sharded dataset back into single file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_records = 0
        total_bytes = 0
        
        with output_path.open("w", encoding="utf-8") as out_f:
            for i in range(self.config.num_shards):
                shard_path = shard_dir / f"{prefix}_{i:04d}.jsonl"
                
                if not shard_path.exists():
                    continue
                
                with shard_path.open("r", encoding="utf-8") as shard_f:
                    for line in shard_f:
                        out_f.write(line)
                        total_records += 1
                        total_bytes += len(line.encode("utf-8"))
        
        return {
            "output_path": str(output_path),
            "total_records": total_records,
            "total_bytes": total_bytes,
            "shards_merged": self.config.num_shards,
        }
    
    def get_shard_statistics(self) -> Dict[str, Any]:
        """Get statistics across all shards."""
        if not self.shards:
            return {
                "total_shards": 0,
                "total_records": 0,
                "total_size_bytes": 0,
            }
        
        total_records = sum(s.record_count for s in self.shards.values())
        total_size = sum(s.file_size_bytes for s in self.shards.values())
        
        shard_records = [s.record_count for s in self.shards.values()]
        avg_records = total_records / len(self.shards)
        
        return {
            "total_shards": len(self.shards),
            "total_records": total_records,
            "total_size_bytes": total_size,
            "avg_records_per_shard": avg_records,
            "min_records": min(shard_records) if shard_records else 0,
            "max_records": max(shard_records) if shard_records else 0,
            "balance_ratio": min(shard_records) / max(shard_records) if shard_records and max(shard_records) > 0 else 0.0,
        }
    
    def save_shard_manifest(self, output_path: Path) -> None:
        """Save shard manifest with metadata."""
        manifest = {
            "config": self.config.to_dict(),
            "shards": [s.to_dict() for s in self.shards.values()],
            "statistics": self.get_shard_statistics(),
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    
    def load_shard_manifest(self, manifest_path: Path) -> None:
        """Load shard manifest from file."""
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        
        # Load config
        self.config = ShardingConfig(
            num_shards=data["config"]["num_shards"],
            shard_key_field=data["config"]["shard_key_field"],
            strategy=ShardingStrategy(data["config"]["strategy"]),
            replication_factor=data["config"].get("replication_factor", 1),
            auto_balance=data["config"].get("auto_balance", True),
            max_shard_size_mb=data["config"].get("max_shard_size_mb", 1024),
        )
        
        # Load shards
        self.shards = {}
        for shard_data in data["shards"]:
            metadata = ShardMetadata(
                shard_id=shard_data["shard_id"],
                shard_index=shard_data["shard_index"],
                total_shards=shard_data["total_shards"],
                record_count=shard_data["record_count"],
                file_size_bytes=shard_data["file_size_bytes"],
                shard_key_field=shard_data["shard_key_field"],
                shard_strategy=ShardingStrategy(shard_data["shard_strategy"]),
                status=ShardStatus(shard_data["status"]),
                created_at=shard_data["created_at"],
                updated_at=shard_data["updated_at"],
                shard_range=shard_data.get("shard_range"),
            )
            self.shards[metadata.shard_id] = metadata


class ShardRouter:
    """Route queries to appropriate shards."""
    
    def __init__(self, sharder: DatasetSharder):
        """Initialize shard router."""
        self.sharder = sharder
    
    def route_query(
        self,
        shard_key_value: Any,
        ranges: Optional[List[tuple]] = None,
        lists: Optional[List[List[Any]]] = None,
    ) -> List[str]:
        """Determine which shards should handle a query."""
        # Create dummy record with shard key
        record = {self.sharder.config.shard_key_field: shard_key_value}
        
        shard_index = self.sharder.compute_shard_index(
            record,
            ranges=ranges,
            lists=lists,
        )
        
        # Find shard by index
        for shard_id, metadata in self.sharder.shards.items():
            if metadata.shard_index == shard_index:
                return [shard_id]
        
        return []
    
    def route_range_query(
        self,
        start_value: Any,
        end_value: Any,
    ) -> List[str]:
        """Determine which shards overlap with a range query."""
        # For hash-based strategies, may need to query all shards
        if self.sharder.config.strategy in [ShardingStrategy.HASH, ShardingStrategy.CONSISTENT_HASH]:
            return list(self.sharder.shards.keys())
        
        # For range-based strategies, identify overlapping shards
        relevant_shards = []
        for shard_id, metadata in self.sharder.shards.items():
            if metadata.shard_range:
                shard_start = metadata.shard_range.get("start")
                shard_end = metadata.shard_range.get("end")
                
                # Check for overlap
                if shard_start <= end_value and shard_end >= start_value:
                    relevant_shards.append(shard_id)
        
        return relevant_shards if relevant_shards else list(self.sharder.shards.keys())
    
    def broadcast_query(self) -> List[str]:
        """Return all active shards for broadcast queries."""
        return [
            shard_id
            for shard_id, metadata in self.sharder.shards.items()
            if metadata.status == ShardStatus.ACTIVE
        ]


class ShardRebalancer:
    """Rebalance shards to maintain even distribution."""
    
    def __init__(self, sharder: DatasetSharder):
        """Initialize shard rebalancer."""
        self.sharder = sharder
    
    def analyze_balance(self) -> Dict[str, Any]:
        """Analyze shard balance."""
        stats = self.sharder.get_shard_statistics()
        
        if stats["total_shards"] == 0:
            return {"balanced": True, "imbalance_ratio": 0.0}
        
        imbalance_ratio = 1.0 - stats["balance_ratio"]
        
        return {
            "balanced": imbalance_ratio < 0.2,  # Less than 20% imbalance
            "imbalance_ratio": imbalance_ratio,
            "min_records": stats["min_records"],
            "max_records": stats["max_records"],
            "avg_records": stats["avg_records_per_shard"],
        }
    
    def suggest_rebalancing(self) -> Dict[str, Any]:
        """Suggest rebalancing strategy."""
        analysis = self.analyze_balance()
        
        if analysis["balanced"]:
            return {
                "needs_rebalancing": False,
                "suggestion": "Shards are well balanced",
            }
        
        return {
            "needs_rebalancing": True,
            "suggestion": "Consider resharding with different strategy or more shards",
            "imbalance_ratio": analysis["imbalance_ratio"],
        }
