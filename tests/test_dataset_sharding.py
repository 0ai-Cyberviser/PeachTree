"""Tests for dataset_sharding module."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_sharding import (
    DatasetSharder,
    ShardMetadata,
    ShardRebalancer,
    ShardRouter,
    ShardingConfig,
    ShardingStrategy,
    ShardStatus,
)


@pytest.fixture
def sample_dataset() -> Path:
    """Create a sample dataset for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for i in range(100):
            record = {
                "id": f"record_{i:03d}",
                "user_id": i % 10,
                "category": "A" if i < 50 else "B",
                "value": i,
            }
            f.write(json.dumps(record, sort_keys=True) + "\n")
        
        return Path(f.name)


@pytest.fixture
def sharding_config() -> ShardingConfig:
    """Create sharding configuration."""
    return ShardingConfig(
        num_shards=4,
        shard_key_field="user_id",
        strategy=ShardingStrategy.HASH,
    )


def test_sharding_config_defaults():
    """Test ShardingConfig defaults."""
    config = ShardingConfig(
        num_shards=4,
        shard_key_field="id",
        strategy=ShardingStrategy.HASH,
    )
    
    assert config.num_shards == 4
    assert config.shard_key_field == "id"
    assert config.strategy == ShardingStrategy.HASH
    assert config.replication_factor == 1
    assert config.auto_balance is True
    assert config.max_shard_size_mb == 1024


def test_sharding_config_to_dict(sharding_config: ShardingConfig):
    """Test ShardingConfig serialization."""
    data = sharding_config.to_dict()
    
    assert data["num_shards"] == 4
    assert data["shard_key_field"] == "user_id"
    assert data["strategy"] == "hash"
    assert data["replication_factor"] == 1


def test_shard_metadata():
    """Test ShardMetadata creation."""
    metadata = ShardMetadata(
        shard_id="shard_0001",
        shard_index=1,
        total_shards=4,
        record_count=25,
        file_size_bytes=1024,
        shard_key_field="id",
        shard_strategy=ShardingStrategy.HASH,
    )
    
    assert metadata.shard_id == "shard_0001"
    assert metadata.shard_index == 1
    assert metadata.status == ShardStatus.ACTIVE


def test_shard_metadata_to_dict():
    """Test ShardMetadata serialization."""
    metadata = ShardMetadata(
        shard_id="shard_0001",
        shard_index=1,
        total_shards=4,
        record_count=25,
        file_size_bytes=1024,
        shard_key_field="id",
        shard_strategy=ShardingStrategy.HASH,
    )
    
    data = metadata.to_dict()
    
    assert data["shard_id"] == "shard_0001"
    assert data["shard_index"] == 1
    assert data["status"] == "active"


def test_sharder_initialization(sharding_config: ShardingConfig):
    """Test DatasetSharder initialization."""
    sharder = DatasetSharder(sharding_config)
    
    assert sharder.config == sharding_config
    assert len(sharder.shards) == 0


def test_hash_shard(sharding_config: ShardingConfig):
    """Test hash-based sharding."""
    sharder = DatasetSharder(sharding_config)
    
    # Same value should always map to same shard
    shard_index = sharder._hash_shard("test_value")
    
    assert 0 <= shard_index < sharding_config.num_shards
    assert sharder._hash_shard("test_value") == shard_index


def test_round_robin_shard(sharding_config: ShardingConfig):
    """Test round-robin sharding."""
    config = ShardingConfig(
        num_shards=4,
        shard_key_field="id",
        strategy=ShardingStrategy.ROUND_ROBIN,
    )
    
    sharder = DatasetSharder(config)
    
    assert sharder._round_robin_shard(0) == 0
    assert sharder._round_robin_shard(1) == 1
    assert sharder._round_robin_shard(4) == 0
    assert sharder._round_robin_shard(7) == 3


def test_consistent_hash_shard(sharding_config: ShardingConfig):
    """Test consistent hashing."""
    sharder = DatasetSharder(sharding_config)
    
    # Same value should always map to same shard
    shard_index = sharder._consistent_hash_shard("test_value")
    
    assert 0 <= shard_index < sharding_config.num_shards
    assert sharder._consistent_hash_shard("test_value") == shard_index


def test_compute_shard_index_hash(sharding_config: ShardingConfig):
    """Test computing shard index with hash strategy."""
    sharder = DatasetSharder(sharding_config)
    
    record = {"user_id": 5, "value": "test"}
    shard_index = sharder.compute_shard_index(record)
    
    assert 0 <= shard_index < 4


def test_compute_shard_index_round_robin():
    """Test computing shard index with round-robin strategy."""
    config = ShardingConfig(
        num_shards=4,
        shard_key_field="id",
        strategy=ShardingStrategy.ROUND_ROBIN,
    )
    
    sharder = DatasetSharder(config)
    
    record = {"id": "test"}
    
    assert sharder.compute_shard_index(record, record_index=0) == 0
    assert sharder.compute_shard_index(record, record_index=5) == 1


def test_shard_dataset(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test sharding a dataset."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        shards = sharder.shard_dataset(sample_dataset, output_dir, prefix="test_shard")
        
        assert len(shards) == 4
        assert all(s.total_shards == 4 for s in shards)
        assert sum(s.record_count for s in shards) == 100


def test_shard_dataset_files_created(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test that shard files are created."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        sharder.shard_dataset(sample_dataset, output_dir, prefix="test")
        
        # Check that shard files exist
        for i in range(4):
            shard_file = output_dir / f"test_{i:04d}.jsonl"
            assert shard_file.exists()


def test_merge_shards(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test merging shards back together."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        shard_dir = Path(tmpdir)
        
        # Create shards
        sharder.shard_dataset(sample_dataset, shard_dir, prefix="test")
        
        # Merge shards
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            output_path = Path(f.name)
        
        result = sharder.merge_shards(shard_dir, output_path, prefix="test")
        
        assert result["total_records"] == 100
        assert result["shards_merged"] == 4


def test_get_shard_statistics(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test getting shard statistics."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        sharder.shard_dataset(sample_dataset, output_dir)
        
        stats = sharder.get_shard_statistics()
        
        assert stats["total_shards"] == 4
        assert stats["total_records"] == 100
        assert stats["avg_records_per_shard"] == 25.0
        assert stats["balance_ratio"] <= 1.0


def test_save_shard_manifest(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test saving shard manifest."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        sharder.shard_dataset(sample_dataset, output_dir)
        
        manifest_path = output_dir / "manifest.json"
        sharder.save_shard_manifest(manifest_path)
        
        assert manifest_path.exists()
        
        # Verify manifest content
        manifest = json.loads(manifest_path.read_text())
        assert "config" in manifest
        assert "shards" in manifest
        assert "statistics" in manifest
        assert len(manifest["shards"]) == 4


def test_load_shard_manifest(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test loading shard manifest."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Create and save manifest
        sharder.shard_dataset(sample_dataset, output_dir)
        manifest_path = output_dir / "manifest.json"
        sharder.save_shard_manifest(manifest_path)
        
        # Load manifest in new sharder
        new_sharder = DatasetSharder(sharding_config)
        new_sharder.load_shard_manifest(manifest_path)
        
        assert new_sharder.config.num_shards == 4
        assert len(new_sharder.shards) == 4


def test_shard_router_initialization(sharding_config: ShardingConfig):
    """Test ShardRouter initialization."""
    sharder = DatasetSharder(sharding_config)
    router = ShardRouter(sharder)
    
    assert router.sharder == sharder


def test_route_query(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test routing a query to shard."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        sharder.shard_dataset(sample_dataset, output_dir)
        
        router = ShardRouter(sharder)
        shard_ids = router.route_query(5)
        
        assert len(shard_ids) == 1


def test_broadcast_query(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test broadcast query to all shards."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        sharder.shard_dataset(sample_dataset, output_dir)
        
        router = ShardRouter(sharder)
        shard_ids = router.broadcast_query()
        
        assert len(shard_ids) == 4


def test_shard_rebalancer_initialization(sharding_config: ShardingConfig):
    """Test ShardRebalancer initialization."""
    sharder = DatasetSharder(sharding_config)
    rebalancer = ShardRebalancer(sharder)
    
    assert rebalancer.sharder == sharder


def test_analyze_balance(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test analyzing shard balance."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        sharder.shard_dataset(sample_dataset, output_dir)
        
        rebalancer = ShardRebalancer(sharder)
        analysis = rebalancer.analyze_balance()
        
        assert "balanced" in analysis
        assert "imbalance_ratio" in analysis
        assert "min_records" in analysis
        assert "max_records" in analysis


def test_suggest_rebalancing_balanced(sample_dataset: Path, sharding_config: ShardingConfig):
    """Test rebalancing suggestion for balanced shards."""
    sharder = DatasetSharder(sharding_config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        sharder.shard_dataset(sample_dataset, output_dir)
        
        rebalancer = ShardRebalancer(sharder)
        suggestion = rebalancer.suggest_rebalancing()
        
        assert "needs_rebalancing" in suggestion
        assert "suggestion" in suggestion


def test_sharding_strategy_enum():
    """Test ShardingStrategy enum."""
    assert ShardingStrategy.HASH.value == "hash"
    assert ShardingStrategy.RANGE.value == "range"
    assert ShardingStrategy.LIST.value == "list"
    assert ShardingStrategy.ROUND_ROBIN.value == "round_robin"
    assert ShardingStrategy.CONSISTENT_HASH.value == "consistent_hash"


def test_shard_status_enum():
    """Test ShardStatus enum."""
    assert ShardStatus.ACTIVE.value == "active"
    assert ShardStatus.READONLY.value == "readonly"
    assert ShardStatus.MIGRATING.value == "migrating"
    assert ShardStatus.INACTIVE.value == "inactive"


def test_shard_with_different_strategies(sample_dataset: Path):
    """Test sharding with different strategies."""
    strategies = [ShardingStrategy.HASH, ShardingStrategy.ROUND_ROBIN, ShardingStrategy.CONSISTENT_HASH]
    
    for strategy in strategies:
        config = ShardingConfig(
            num_shards=4,
            shard_key_field="user_id",
            strategy=strategy,
        )
        
        sharder = DatasetSharder(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            shards = sharder.shard_dataset(sample_dataset, output_dir)
            
            assert len(shards) == 4
            assert sum(s.record_count for s in shards) == 100
