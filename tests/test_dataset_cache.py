"""Tests for dataset caching functionality."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from peachtree.dataset_cache import (
    CacheEntry,
    CacheStats,
    CacheStrategy,
    DatasetCache,
    DatasetCacheOptimizer,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample dataset for testing."""
    dataset = temp_dir / "dataset.jsonl"
    records = []
    for i in range(100):
        records.append({
            "record_id": f"rec_{i:03d}",
            "content": f"Test content {i}" * 10,
            "quality_score": 70 + (i % 30),
        })
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


class TestCacheEntry:
    """Test CacheEntry dataclass."""
    
    def test_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            data={"content": "test"},
            size_bytes=1024,
            created_at=time.time(),
            accessed_at=time.time(),
        )
        
        assert entry.key == "test_key"
        assert entry.access_count == 0
        assert entry.is_expired() is False
    
    def test_entry_with_ttl(self):
        """Test entry with TTL."""
        entry = CacheEntry(
            key="test_key",
            data={"content": "test"},
            size_bytes=1024,
            created_at=time.time() - 3700,  # Created over an hour ago
            accessed_at=time.time(),
            ttl_seconds=3600,  # 1 hour TTL
        )
        
        assert entry.is_expired() is True
    
    def test_update_access(self):
        """Test updating access statistics."""
        entry = CacheEntry(
            key="test_key",
            data={"content": "test"},
            size_bytes=1024,
            created_at=time.time(),
            accessed_at=time.time(),
        )
        
        original_accessed = entry.accessed_at
        time.sleep(0.01)  # Small delay
        entry.update_access()
        
        assert entry.accessed_at > original_accessed
        assert entry.access_count == 1


class TestCacheStats:
    """Test CacheStats dataclass."""
    
    def test_stats_creation(self):
        """Test creating cache statistics."""
        stats = CacheStats()
        
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(
            total_requests=100,
            cache_hits=80,
            cache_misses=20,
        )
        
        assert stats.hit_rate == 0.8
    
    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = CacheStats(
            total_requests=50,
            cache_hits=40,
            cache_misses=10,
            evictions=5,
            total_size_bytes=1024 * 1024,
            entry_count=10,
        )
        
        data = stats.to_dict()
        assert data["total_requests"] == 50
        assert data["hit_rate"] == 0.8
        assert "cache_hits" in data


class TestDatasetCache:
    """Test DatasetCache class."""
    
    def test_cache_creation(self):
        """Test creating a cache."""
        cache = DatasetCache(max_size_mb=100)
        
        assert cache.max_size_bytes == 100 * 1024 * 1024
        assert cache.strategy == CacheStrategy.LRU
    
    def test_put_and_get(self):
        """Test putting and getting items."""
        cache = DatasetCache()
        
        data = {"record_id": "test", "content": "test data"}
        cache.put("test_key", data)
        
        retrieved = cache.get("test_key")
        
        assert retrieved == data
        assert cache.stats.cache_hits == 1
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = DatasetCache()
        
        result = cache.get("nonexistent_key")
        
        assert result is None
        assert cache.stats.cache_misses == 1
    
    def test_cache_eviction_lru(self):
        """Test LRU cache eviction."""
        cache = DatasetCache(max_size_mb=1, strategy=CacheStrategy.LRU)
        
        # Fill cache
        for i in range(100):
            cache.put(f"key_{i}", {"data": "x" * 10000})
        
        # Should have evicted some entries
        assert cache.stats.evictions > 0
    
    def test_cache_eviction_lfu(self):
        """Test LFU cache eviction."""
        cache = DatasetCache(max_size_mb=1, strategy=CacheStrategy.LFU)
        
        # Add items and access them different amounts
        cache.put("key_1", {"data": "x" * 10000})
        cache.put("key_2", {"data": "x" * 10000})
        
        # Access key_1 multiple times
        for _ in range(5):
            cache.get("key_1")
        
        # Add more items to trigger eviction
        for i in range(100):
            cache.put(f"key_{i + 3}", {"data": "x" * 10000})
        
        # key_1 (frequently accessed) should still be in cache
        # key_2 (less frequently accessed) might be evicted
        assert cache.stats.evictions > 0
    
    def test_cache_with_ttl(self):
        """Test cache with TTL expiration."""
        cache = DatasetCache(strategy=CacheStrategy.TTL, default_ttl_seconds=1)
        
        cache.put("test_key", {"content": "test"})
        
        # Should be in cache immediately
        assert cache.get("test_key") is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("test_key") is None
    
    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = DatasetCache(default_ttl_seconds=1)
        
        # Add some entries
        cache.put("key_1", {"data": "test1"}, ttl_seconds=1)
        cache.put("key_2", {"data": "test2"}, ttl_seconds=10)
        
        # Wait for first to expire
        time.sleep(1.1)
        
        # Cleanup
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("key_2") is not None
    
    def test_clear_cache(self):
        """Test clearing all cache entries."""
        cache = DatasetCache()
        
        for i in range(10):
            cache.put(f"key_{i}", {"data": f"test_{i}"})
        
        cache.clear()
        
        assert cache.stats.total_size_bytes == 0
        assert cache.stats.entry_count == 0
    
    def test_evict_specific_key(self):
        """Test evicting a specific key."""
        cache = DatasetCache()
        
        cache.put("test_key", {"data": "test"})
        
        assert cache.evict("test_key") is True
        assert cache.get("test_key") is None
        assert cache.stats.evictions == 1
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = DatasetCache()
        
        # Add items
        for i in range(5):
            cache.put(f"key_{i}", {"data": f"test_{i}"})
        
        # Access some items
        cache.get("key_1")
        cache.get("key_2")
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats.total_requests == 3
        assert stats.cache_hits == 2
        assert stats.cache_misses == 1
        assert stats.hit_rate == pytest.approx(0.666, rel=0.01)


class TestDatasetCacheOptimizer:
    """Test DatasetCacheOptimizer class."""
    
    def test_optimizer_creation(self, temp_dir):
        """Test creating a cache optimizer."""
        optimizer = DatasetCacheOptimizer(
            cache_dir=temp_dir / "cache",
            max_memory_mb=512,
            max_disk_mb=5120,
        )
        
        assert optimizer.cache_dir.exists()
        assert optimizer.memory_cache.max_size_bytes == 512 * 1024 * 1024
    
    def test_cache_dataset_memory(self, sample_dataset):
        """Test caching a dataset in memory."""
        optimizer = DatasetCacheOptimizer()
        
        cache_key = optimizer.cache_dataset(sample_dataset, use_disk=False)
        
        assert cache_key is not None
        assert len(cache_key) == 16  # Hash length
    
    def test_cache_dataset_disk(self, sample_dataset, temp_dir):
        """Test caching a dataset on disk."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        cache_key = optimizer.cache_dataset(sample_dataset, use_disk=True)
        
        cache_file = optimizer.cache_dir / f"{cache_key}.pkl"
        assert cache_file.exists()
    
    def test_get_cached_dataset_memory(self, sample_dataset):
        """Test retrieving cached dataset from memory."""
        optimizer = DatasetCacheOptimizer()
        
        cache_key = optimizer.cache_dataset(sample_dataset, use_disk=False)
        cached_data = optimizer.get_cached_dataset(cache_key)
        
        assert cached_data is not None
        assert len(cached_data) == 100
    
    def test_get_cached_dataset_disk(self, sample_dataset, temp_dir):
        """Test retrieving cached dataset from disk."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        cache_key = optimizer.cache_dataset(sample_dataset, use_disk=True)
        cached_data = optimizer.get_cached_dataset(cache_key)
        
        assert cached_data is not None
        assert len(cached_data) == 100
    
    def test_cache_query_result(self):
        """Test caching query results."""
        optimizer = DatasetCacheOptimizer()
        
        query = "SELECT * FROM dataset WHERE quality > 80"
        result = [{"record_id": "rec_001", "quality_score": 85}]
        
        cache_key = optimizer.cache_query_result(query, result, ttl_seconds=3600)
        
        assert cache_key is not None
    
    def test_get_cached_query(self):
        """Test retrieving cached query."""
        optimizer = DatasetCacheOptimizer()
        
        query = "SELECT * FROM dataset WHERE quality > 80"
        result = [{"record_id": "rec_001", "quality_score": 85}]
        
        optimizer.cache_query_result(query, result)
        cached_result = optimizer.get_cached_query(query)
        
        assert cached_result == result
    
    def test_optimize_access_pattern_random(self, sample_dataset):
        """Test optimizing for random access."""
        optimizer = DatasetCacheOptimizer()
        
        stats = optimizer.optimize_access_pattern(sample_dataset, "random")
        
        assert stats["optimized"] is True
        assert stats["strategy"] == "random"
        assert "cache_key" in stats
    
    def test_optimize_access_pattern_sequential(self, sample_dataset):
        """Test optimizing for sequential access."""
        optimizer = DatasetCacheOptimizer()
        
        stats = optimizer.optimize_access_pattern(sample_dataset, "sequential")
        
        assert stats["optimized"] is False
        assert "reason" in stats
    
    def test_prefetch_dataset(self, sample_dataset, temp_dir):
        """Test prefetching multiple datasets."""
        dataset2 = temp_dir / "dataset2.jsonl"
        dataset2.write_text(sample_dataset.read_text())
        
        optimizer = DatasetCacheOptimizer()
        
        cached_count = optimizer.prefetch_dataset([sample_dataset, dataset2])
        
        assert cached_count == 2
    
    def test_get_cache_statistics(self, sample_dataset, temp_dir):
        """Test getting cache statistics."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        # Cache some datasets
        optimizer.cache_dataset(sample_dataset, use_disk=False)
        optimizer.cache_dataset(sample_dataset, use_disk=True)
        
        stats = optimizer.get_cache_statistics()
        
        assert "memory_cache" in stats
        assert "disk_cache" in stats
        assert stats["disk_cache"]["file_count"] >= 1
    
    def test_cleanup_old_cache(self, sample_dataset, temp_dir):
        """Test cleaning up old cache files."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        # Cache a dataset
        optimizer.cache_dataset(sample_dataset, use_disk=True)
        
        # Cleanup (won't remove recent files)
        removed_count = optimizer.cleanup_old_cache(max_age_days=7)
        
        # Recent cache files shouldn't be removed
        assert removed_count == 0
    
    def test_clear_all_cache(self, sample_dataset, temp_dir):
        """Test clearing all cache."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        # Cache some datasets
        optimizer.cache_dataset(sample_dataset, use_disk=False)
        optimizer.cache_dataset(sample_dataset, use_disk=True)
        
        optimizer.clear_all_cache()
        
        stats = optimizer.get_cache_statistics()
        assert stats["memory_cache"]["entry_count"] == 0
        assert stats["disk_cache"]["file_count"] == 0
    
    def test_get_cache_efficiency(self, sample_dataset):
        """Test getting cache efficiency metrics."""
        optimizer = DatasetCacheOptimizer()
        
        # Cache and access
        cache_key = optimizer.cache_dataset(sample_dataset, use_disk=False)
        optimizer.get_cached_dataset(cache_key)
        optimizer.get_cached_dataset("nonexistent")
        
        efficiency = optimizer.get_cache_efficiency()
        
        assert "hit_rate" in efficiency
        assert "miss_rate" in efficiency
        assert "eviction_rate" in efficiency
        assert "capacity_utilization" in efficiency
    
    def test_recommend_cache_size(self, sample_dataset):
        """Test recommending optimal cache size."""
        optimizer = DatasetCacheOptimizer()
        
        recommendations = optimizer.recommend_cache_size(sample_dataset)
        
        assert "dataset_size_mb" in recommendations
        assert "recommended_cache_mb" in recommendations
        assert "target_hit_rate" in recommendations
        assert recommendations["recommended_cache_mb"] >= 128
    
    def test_save_cache_config(self, temp_dir):
        """Test saving cache configuration."""
        optimizer = DatasetCacheOptimizer(cache_dir=temp_dir / "cache")
        
        output = temp_dir / "cache_config.json"
        optimizer.save_cache_config(output)
        
        assert output.exists()
        
        config = json.loads(output.read_text())
        assert "cache_dir" in config
        assert "max_memory_mb" in config
        assert "strategy" in config
