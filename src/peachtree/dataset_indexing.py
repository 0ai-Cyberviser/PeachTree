"""Build searchable indexes for fast dataset lookups and queries."""

import json
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class IndexType(Enum):
    """Types of dataset indexes."""
    
    HASH = "hash"
    BTREE = "btree"
    FULL_TEXT = "full_text"
    INVERTED = "inverted"


class IndexStatus(Enum):
    """Status of an index."""
    
    BUILDING = "building"
    READY = "ready"
    STALE = "stale"
    CORRUPTED = "corrupted"


@dataclass
class IndexMetadata:
    """Metadata for a dataset index."""
    
    index_id: str
    index_type: IndexType
    field_name: str
    record_count: int
    status: IndexStatus
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    index_size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index_id": self.index_id,
            "index_type": self.index_type.value,
            "field_name": self.field_name,
            "record_count": self.record_count,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "index_size_bytes": self.index_size_bytes,
        }


class HashIndex:
    """Hash-based index for exact match lookups."""
    
    def __init__(self, field_name: str):
        """Initialize hash index."""
        self.field_name = field_name
        self.index: Dict[Any, List[str]] = {}
    
    def add(self, record_id: str, value: Any) -> None:
        """Add record to index."""
        if value not in self.index:
            self.index[value] = []
        self.index[value].append(record_id)
    
    def lookup(self, value: Any) -> List[str]:
        """Look up records by value."""
        return self.index.get(value, [])
    
    def remove(self, record_id: str, value: Any) -> None:
        """Remove record from index."""
        if value in self.index:
            self.index[value] = [rid for rid in self.index[value] if rid != record_id]
            if not self.index[value]:
                del self.index[value]
    
    def size(self) -> int:
        """Get number of unique values in index."""
        return len(self.index)


class InvertedIndex:
    """Inverted index for full-text search."""
    
    def __init__(self, field_name: str):
        """Initialize inverted index."""
        self.field_name = field_name
        self.index: Dict[str, Set[str]] = defaultdict(set)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        return re.findall(r'\w+', text.lower())
    
    def add(self, record_id: str, text: str) -> None:
        """Add record to index."""
        tokens = self._tokenize(text)
        for token in tokens:
            self.index[token].add(record_id)
    
    def search(self, query: str) -> Set[str]:
        """Search for records matching query."""
        tokens = self._tokenize(query)
        
        if not tokens:
            return set()
        
        # Get records containing first token
        results = self.index.get(tokens[0], set()).copy()
        
        # Intersect with records containing other tokens
        for token in tokens[1:]:
            results &= self.index.get(token, set())
        
        return results
    
    def remove(self, record_id: str, text: str) -> None:
        """Remove record from index."""
        tokens = self._tokenize(text)
        for token in tokens:
            self.index[token].discard(record_id)
    
    def size(self) -> int:
        """Get number of unique tokens in index."""
        return len(self.index)


class DatasetIndexBuilder:
    """Build and manage dataset indexes."""
    
    def __init__(self, index_dir: Optional[Path] = None):
        """Initialize index builder."""
        self.index_dir = index_dir or Path.cwd() / ".indexes"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.indexes: Dict[str, Any] = {}
        self.metadata: Dict[str, IndexMetadata] = {}
    
    def build_hash_index(
        self,
        dataset_path: Path,
        field_name: str,
        index_id: Optional[str] = None,
    ) -> IndexMetadata:
        """Build hash index on a field."""
        index_id = index_id or f"hash_{field_name}"
        
        index = HashIndex(field_name)
        record_count = 0
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    record_id = record.get("id", str(hash(json.dumps(record, sort_keys=True))))
                    value = record.get(field_name)
                    
                    if value is not None:
                        index.add(record_id, value)
                        record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        self.indexes[index_id] = index
        
        metadata = IndexMetadata(
            index_id=index_id,
            index_type=IndexType.HASH,
            field_name=field_name,
            record_count=record_count,
            status=IndexStatus.READY,
        )
        
        self.metadata[index_id] = metadata
        
        return metadata
    
    def build_inverted_index(
        self,
        dataset_path: Path,
        field_name: str,
        index_id: Optional[str] = None,
    ) -> IndexMetadata:
        """Build inverted index for full-text search."""
        index_id = index_id or f"inverted_{field_name}"
        
        index = InvertedIndex(field_name)
        record_count = 0
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    record_id = record.get("id", str(hash(json.dumps(record, sort_keys=True))))
                    text = record.get(field_name, "")
                    
                    if text:
                        index.add(record_id, str(text))
                        record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        self.indexes[index_id] = index
        
        metadata = IndexMetadata(
            index_id=index_id,
            index_type=IndexType.INVERTED,
            field_name=field_name,
            record_count=record_count,
            status=IndexStatus.READY,
        )
        
        self.metadata[index_id] = metadata
        
        return metadata
    
    def lookup(self, index_id: str, value: Any) -> List[str]:
        """Look up records by value in hash index."""
        if index_id not in self.indexes:
            return []
        
        index = self.indexes[index_id]
        
        if isinstance(index, HashIndex):
            return index.lookup(value)
        
        return []
    
    def search(self, index_id: str, query: str) -> Set[str]:
        """Search records in inverted index."""
        if index_id not in self.indexes:
            return set()
        
        index = self.indexes[index_id]
        
        if isinstance(index, InvertedIndex):
            return index.search(query)
        
        return set()
    
    def save_index(self, index_id: str) -> None:
        """Save index to disk."""
        if index_id not in self.indexes:
            return
        
        index_path = self.index_dir / f"{index_id}.idx"
        metadata_path = self.index_dir / f"{index_id}.meta"
        
        with index_path.open("wb") as f:
            pickle.dump(self.indexes[index_id], f)
        
        # Save metadata as JSON
        if index_id in self.metadata:
            import json
            self.metadata[index_id].index_size_bytes = index_path.stat().st_size
            self.metadata[index_id].updated_at = datetime.utcnow().isoformat() + "Z"
            
            with metadata_path.open("w") as f:
                json.dump(self.metadata[index_id].to_dict(), f, indent=2)
    
    def load_index(self, index_id: str) -> IndexMetadata:
        """Load index from disk."""
        index_path = self.index_dir / f"{index_id}.idx"
        metadata_path = self.index_dir / f"{index_id}.meta"
        
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        try:
            with index_path.open("rb") as f:
                self.indexes[index_id] = pickle.load(f)
            
            # Load metadata if exists
            if metadata_path.exists():
                with metadata_path.open("r") as f:
                    import json
                    meta_data = json.load(f)
                    metadata = IndexMetadata(
                        index_id=meta_data["index_id"],
                        index_type=IndexType(meta_data["index_type"]),
                        field_name=meta_data["field_name"],
                        record_count=meta_data["record_count"],
                        status=IndexStatus(meta_data["status"]),
                        created_at=meta_data.get("created_at", ""),
                        updated_at=meta_data.get("updated_at", ""),
                        index_size_bytes=meta_data.get("index_size_bytes", 0),
                    )
                    self.metadata[index_id] = metadata
                    return metadata
            
            # If no metadata file, return None
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        except (pickle.UnpicklingError, EOFError) as e:
            raise ValueError(f"Failed to load index: {e}")
    
    def drop_index(self, index_id: str) -> bool:
        """Drop an index."""
        found = False
        
        if index_id in self.indexes:
            del self.indexes[index_id]
            found = True
        
        if index_id in self.metadata:
            del self.metadata[index_id]
            found = True
        
        index_path = self.index_dir / f"{index_id}.idx"
        
        if index_path.exists():
            index_path.unlink()
            found = True
        
        metadata_path = self.index_dir / f"{index_id}.meta"
        if metadata_path.exists():
            metadata_path.unlink()
        
        return found
    
    def list_indexes(self) -> List[IndexMetadata]:
        """List all indexes."""
        return list(self.metadata.values())
    
    def get_index_metadata(self, index_id: str) -> Optional[IndexMetadata]:
        """Get metadata for an index."""
        return self.metadata.get(index_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        total_indexes = len(self.indexes)
        total_size = sum(m.index_size_bytes for m in self.metadata.values())
        
        by_type = {}
        for metadata in self.metadata.values():
            idx_type = metadata.index_type.value
            by_type[idx_type] = by_type.get(idx_type, 0) + 1
        
        return {
            "total_indexes": total_indexes,
            "total_size_bytes": total_size,
            "indexes_by_type": by_type,
            "index_ids": list(self.indexes.keys()),
        }


class QueryOptimizer:
    """Optimize dataset queries using indexes."""
    
    def __init__(self, index_builder: DatasetIndexBuilder):
        """Initialize query optimizer."""
        self.index_builder = index_builder
    
    def find_best_index(
        self,
        field_name: str,
        query_type: str,
    ) -> Optional[str]:
        """Find best index for a query."""
        for index_id, metadata in self.index_builder.metadata.items():
            if metadata.field_name != field_name:
                continue
            
            if query_type == "exact" and metadata.index_type == IndexType.HASH:
                return index_id
            
            if query_type == "text" and metadata.index_type == IndexType.INVERTED:
                return index_id
        
        return None
    
    def execute_query(
        self,
        dataset_path: Path,
        field_name: str,
        value: Any = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute optimized query using indexes."""
        # Determine query type
        if value is not None:
            query_type = "exact"
            index_id = self.find_best_index(field_name, query_type)
            
            if index_id:
                record_ids = self.index_builder.lookup(index_id, value)
            else:
                # Fallback to sequential scan
                return self._sequential_scan(dataset_path, field_name, value)
        
        elif query is not None:
            query_type = "text"
            index_id = self.find_best_index(field_name, query_type)
            
            if index_id:
                record_ids = list(self.index_builder.search(index_id, query))
            else:
                # Fallback to sequential scan
                return self._sequential_search(dataset_path, field_name, query)
        
        else:
            return []
        
        # Retrieve full records
        return self._fetch_records(dataset_path, set(record_ids))
    
    def _sequential_scan(
        self,
        dataset_path: Path,
        field_name: str,
        value: Any,
    ) -> List[Dict[str, Any]]:
        """Sequential scan fallback."""
        results = []
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    if record.get(field_name) == value:
                        results.append(record)
                
                except json.JSONDecodeError:
                    continue
        
        return results
    
    def _sequential_search(
        self,
        dataset_path: Path,
        field_name: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Sequential search fallback."""
        results = []
        query_lower = query.lower()
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    text = str(record.get(field_name, "")).lower()
                    
                    if query_lower in text:
                        results.append(record)
                
                except json.JSONDecodeError:
                    continue
        
        return results
    
    def _fetch_records(
        self,
        dataset_path: Path,
        record_ids: Set[str],
    ) -> List[Dict[str, Any]]:
        """Fetch records by IDs."""
        results = []
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    record_id = record.get("id", str(hash(json.dumps(record, sort_keys=True))))
                    
                    if record_id in record_ids:
                        results.append(record)
                        
                        if len(results) == len(record_ids):
                            break
                
                except json.JSONDecodeError:
                    continue
        
        return results
