"""Dataset caching and performance optimization."""

import hashlib
import json
import pickle
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """A cached dataset entry."""
    
    key: str
    data: Any
    size_bytes: int
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False
        
        age = time.time() - self.created_at
        return age > self.ttl_seconds
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.accessed_at = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""
    
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "evictions": self.evictions,
            "total_size_bytes": self.total_size_bytes,
            "entry_count": self.entry_count,
            "hit_rate": round(self.hit_rate, 4),
        }


class DatasetCache:
    """High-performance dataset cache with multiple eviction strategies."""
    
    def __init__(
        self,
        max_size_mb: int = 1024,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl_seconds: Optional[int] = None,
    ):
        """Initialize the cache."""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.strategy = strategy
        self.default_ttl_seconds = default_ttl_seconds
        self.entries: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        self.stats.total_requests += 1
        
        if key not in self.entries:
            self.stats.cache_misses += 1
            return None
        
        entry = self.entries[key]
        
        # Check if expired
        if entry.is_expired():
            self.evict(key)
            self.stats.cache_misses += 1
            return None
        
        # Update access stats
        entry.update_access()
        self.stats.cache_hits += 1
        
        return entry.data
    
    def put(
        self,
        key: str,
        data: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Put item in cache."""
        # Calculate size
        size_bytes = self._calculate_size(data)
        
        # Check if item is too large
        if size_bytes > self.max_size_bytes:
            return False
        
        # Make room if needed
        while self._would_exceed_limit(size_bytes):
            if not self._evict_one():
                return False
        
        # Create entry
        entry = CacheEntry(
            key=key,
            data=data,
            size_bytes=size_bytes,
            created_at=time.time(),
            accessed_at=time.time(),
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
        )
        
        # Remove old entry if exists
        if key in self.entries:
            old_entry = self.entries[key]
            self.stats.total_size_bytes -= old_entry.size_bytes
        
        # Add new entry
        self.entries[key] = entry
        self.stats.total_size_bytes += size_bytes
        self.stats.entry_count = len(self.entries)
        
        return True
    
    def evict(self, key: str) -> bool:
        """Evict specific key from cache."""
        if key not in self.entries:
            return False
        
        entry = self.entries[key]
        self.stats.total_size_bytes -= entry.size_bytes
        del self.entries[key]
        self.stats.evictions += 1
        self.stats.entry_count = len(self.entries)
        
        return True
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.entries.clear()
        self.stats.total_size_bytes = 0
        self.stats.entry_count = 0
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            self.evict(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats
    
    def _would_exceed_limit(self, additional_bytes: int) -> bool:
        """Check if adding bytes would exceed limit."""
        return (self.stats.total_size_bytes + additional_bytes) > self.max_size_bytes
    
    def _evict_one(self) -> bool:
        """Evict one entry based on strategy."""
        if not self.entries:
            return False
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            victim_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].accessed_at
            )
        
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            victim_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].access_count
            )
        
        elif self.strategy == CacheStrategy.FIFO:
            # Evict oldest
            victim_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].created_at
            )
        
        elif self.strategy == CacheStrategy.TTL:
            # Evict expired first, then oldest
            expired = [k for k, e in self.entries.items() if e.is_expired()]
            if expired:
                victim_key = expired[0]
            else:
                victim_key = min(
                    self.entries.keys(),
                    key=lambda k: self.entries[k].created_at
                )
        
        else:
            # Default to LRU
            victim_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].accessed_at
            )
        
        return self.evict(victim_key)
    
    def _calculate_size(self, data: Any) -> int:
        """Calculate approximate size of data in bytes."""
        try:
            # Use pickle to estimate size
            return len(pickle.dumps(data))
        except Exception:
            # Fallback estimate
            return 1024  # 1KB default


class DatasetCacheOptimizer:
    """Optimize dataset operations with intelligent caching."""
    
    def __init__(
        self,
        cache_dir: Path = Path("/tmp/peachtree_cache"),
        max_memory_mb: int = 1024,
        max_disk_mb: int = 10240,
    ):
        """Initialize the cache optimizer."""
        self.cache_dir = cache_dir
        self.memory_cache = DatasetCache(max_size_mb=max_memory_mb)
        self.max_disk_bytes = max_disk_mb * 1024 * 1024
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def cache_dataset(
        self,
        dataset_path: Path,
        use_disk: bool = False,
    ) -> str:
        """Cache a dataset in memory or on disk."""
        cache_key = self._generate_cache_key(str(dataset_path))
        
        # Load dataset
        records = []
        with open(dataset_path, encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        
        if use_disk:
            # Cache to disk
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(records, f)
        else:
            # Cache in memory
            self.memory_cache.put(cache_key, records)
        
        return cache_key
    
    def get_cached_dataset(
        self,
        cache_key: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached dataset."""
        # Try memory cache first
        data = self.memory_cache.get(cache_key)
        if data is not None:
            return data
        
        # Try disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                data = pickle.load(f)
                # Promote to memory cache
                self.memory_cache.put(cache_key, data)
                return data
        
        return None
    
    def cache_query_result(
        self,
        query: str,
        result: List[Dict[str, Any]],
        ttl_seconds: int = 3600,
    ) -> str:
        """Cache a query result."""
        cache_key = self._generate_cache_key(query)
        self.memory_cache.put(cache_key, result, ttl_seconds=ttl_seconds)
        return cache_key
    
    def get_cached_query(
        self,
        query: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result."""
        cache_key = self._generate_cache_key(query)
        return self.memory_cache.get(cache_key)
    
    def optimize_access_pattern(
        self,
        dataset_path: Path,
        access_pattern: str = "sequential",
    ) -> Dict[str, Any]:
        """Optimize dataset for specific access pattern."""
        stats = {
            "original_size": dataset_path.stat().st_size,
            "optimized": False,
            "strategy": access_pattern,
        }
        
        if access_pattern == "random":
            # Cache entire dataset for random access
            cache_key = self.cache_dataset(dataset_path, use_disk=False)
            stats["cache_key"] = cache_key
            stats["optimized"] = True
        
        elif access_pattern == "sequential":
            # No caching needed for sequential access
            stats["optimized"] = False
            stats["reason"] = "Sequential access doesn't benefit from caching"
        
        elif access_pattern == "range":
            # Partial caching for range queries
            cache_key = self.cache_dataset(dataset_path, use_disk=True)
            stats["cache_key"] = cache_key
            stats["optimized"] = True
        
        return stats
    
    def prefetch_dataset(
        self,
        dataset_paths: List[Path],
        priority: bool = True,
    ) -> int:
        """Prefetch multiple datasets into cache."""
        cached_count = 0
        
        for path in dataset_paths:
            try:
                self.cache_dataset(path, use_disk=not priority)
                cached_count += 1
            except Exception:
                continue
        
        return cached_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        
        # Calculate disk cache size
        disk_size = 0
        disk_files = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                disk_size += cache_file.stat().st_size
                disk_files += 1
        
        return {
            "memory_cache": memory_stats.to_dict(),
            "disk_cache": {
                "total_size_bytes": disk_size,
                "file_count": disk_files,
                "max_size_bytes": self.max_disk_bytes,
                "utilization": round(disk_size / self.max_disk_bytes, 4) if self.max_disk_bytes > 0 else 0,
            },
        }
    
    def cleanup_old_cache(
        self,
        max_age_days: int = 7,
    ) -> int:
        """Clean up old cache files."""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        removed_count = 0
        
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                if cache_file.stat().st_mtime < cutoff_timestamp:
                    cache_file.unlink()
                    removed_count += 1
        
        # Also cleanup expired memory cache entries
        removed_count += self.memory_cache.cleanup_expired()
        
        return removed_count
    
    def clear_all_cache(self) -> None:
        """Clear all cache (memory and disk)."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
    
    def get_cache_efficiency(self) -> Dict[str, Any]:
        """Calculate cache efficiency metrics."""
        stats = self.memory_cache.get_stats()
        
        return {
            "hit_rate": stats.hit_rate,
            "miss_rate": 1.0 - stats.hit_rate if stats.total_requests > 0 else 0.0,
            "eviction_rate": stats.evictions / stats.total_requests if stats.total_requests > 0 else 0.0,
            "average_entry_size": stats.total_size_bytes / stats.entry_count if stats.entry_count > 0 else 0,
            "capacity_utilization": stats.total_size_bytes / self.memory_cache.max_size_bytes,
        }
    
    def recommend_cache_size(
        self,
        dataset_path: Path,
        target_hit_rate: float = 0.8,
    ) -> Dict[str, Any]:
        """Recommend optimal cache size for dataset."""
        dataset_size = dataset_path.stat().st_size
        
        # Rule of thumb: cache size should be 20-30% of dataset size for 80% hit rate
        recommended_mb = int((dataset_size * 0.25) / (1024 * 1024))
        
        return {
            "dataset_size_mb": dataset_size / (1024 * 1024),
            "recommended_cache_mb": max(recommended_mb, 128),  # Minimum 128MB
            "target_hit_rate": target_hit_rate,
            "strategy": "LRU recommended for general use",
        }
    
    def _generate_cache_key(self, data: str) -> str:
        """Generate cache key from data."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def save_cache_config(
        self,
        output_path: Path,
    ) -> None:
        """Save cache configuration."""
        config = {
            "cache_dir": str(self.cache_dir),
            "max_memory_mb": self.memory_cache.max_size_bytes / (1024 * 1024),
            "max_disk_mb": self.max_disk_bytes / (1024 * 1024),
            "strategy": self.memory_cache.strategy.value,
            "statistics": self.get_cache_statistics(),
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
