"""Tests for dataset indexing."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from peachtree.dataset_indexing import (
    DatasetIndexBuilder,
    QueryOptimizer,
    HashIndex,
    InvertedIndex,
    IndexMetadata,
    IndexType,
    IndexStatus,
)


def test_index_type_enum():
    """Test IndexType enum values."""
    assert IndexType.HASH.value == "hash"
    assert IndexType.BTREE.value == "btree"
    assert IndexType.FULL_TEXT.value == "full_text"
    assert IndexType.INVERTED.value == "inverted"


def test_index_status_enum():
    """Test IndexStatus enum values."""
    assert IndexStatus.BUILDING.value == "building"
    assert IndexStatus.READY.value == "ready"
    assert IndexStatus.UPDATING.value == "updating"
    assert IndexStatus.CORRUPTED.value == "corrupted"


def test_index_metadata_creation():
    """Test IndexMetadata creation."""
    metadata = IndexMetadata(
        index_id="test-index",
        index_type=IndexType.HASH,
        field_name="id",
        record_count=100,
        status=IndexStatus.READY,
    )
    assert metadata.index_id == "test-index"
    assert metadata.index_type == IndexType.HASH
    assert metadata.field_name == "id"
    assert metadata.record_count == 100
    assert metadata.status == IndexStatus.READY


def test_index_metadata_to_dict():
    """Test IndexMetadata serialization."""
    metadata = IndexMetadata(
        index_id="test-index",
        index_type=IndexType.HASH,
        field_name="id",
        record_count=100,
        status=IndexStatus.READY,
    )
    data = metadata.to_dict()
    
    assert data["index_id"] == "test-index"
    assert data["index_type"] == "hash"
    assert data["field_name"] == "id"
    assert data["record_count"] == 100
    assert data["status"] == "ready"


def test_hash_index_init():
    """Test HashIndex initialization."""
    index = HashIndex("test-idx", "id")
    assert index.index_id == "test-idx"
    assert index.field_name == "id"


def test_hash_index_insert():
    """Test HashIndex insert operation."""
    index = HashIndex("test-idx", "id")
    
    record1 = {"id": "key1", "value": "data1"}
    record2 = {"id": "key2", "value": "data2"}
    
    index.insert("key1", record1)
    index.insert("key2", record2)
    
    assert index.size() == 2


def test_hash_index_lookup():
    """Test HashIndex lookup operation."""
    index = HashIndex("test-idx", "id")
    
    record = {"id": "key1", "value": "data1"}
    index.insert("key1", record)
    
    results = index.lookup("key1")
    
    assert len(results) == 1
    assert results[0]["id"] == "key1"
    assert results[0]["value"] == "data1"


def test_hash_index_lookup_missing():
    """Test HashIndex lookup for missing key."""
    index = HashIndex("test-idx", "id")
    
    results = index.lookup("nonexistent")
    
    assert results == []


def test_hash_index_delete():
    """Test HashIndex delete operation."""
    index = HashIndex("test-idx", "id")
    
    record = {"id": "key1", "value": "data1"}
    index.insert("key1", record)
    
    deleted = index.delete("key1")
    
    assert deleted is True
    assert index.size() == 0
    assert index.lookup("key1") == []


def test_hash_index_delete_missing():
    """Test HashIndex delete for missing key."""
    index = HashIndex("test-idx", "id")
    
    deleted = index.delete("nonexistent")
    
    assert deleted is False


def test_hash_index_multiple_values_same_key():
    """Test HashIndex with multiple records for same key."""
    index = HashIndex("test-idx", "category")
    
    record1 = {"id": 1, "category": "A"}
    record2 = {"id": 2, "category": "A"}
    
    index.insert("A", record1)
    index.insert("A", record2)
    
    results = index.lookup("A")
    
    assert len(results) == 2


def test_inverted_index_init():
    """Test InvertedIndex initialization."""
    index = InvertedIndex("test-idx", "content")
    assert index.index_id == "test-idx"
    assert index.field_name == "content"


def test_inverted_index_insert():
    """Test InvertedIndex insert operation."""
    index = InvertedIndex("test-idx", "content")
    
    record = {"id": 1, "content": "hello world"}
    index.insert(record)
    
    assert index.size() > 0


def test_inverted_index_search():
    """Test InvertedIndex search operation."""
    index = InvertedIndex("test-idx", "content")
    
    record1 = {"id": 1, "content": "hello world"}
    record2 = {"id": 2, "content": "world peace"}
    record3 = {"id": 3, "content": "hello there"}
    
    index.insert(record1)
    index.insert(record2)
    index.insert(record3)
    
    results = list(index.search("world"))
    
    assert len(results) == 2
    assert any(r["id"] == 1 for r in results)
    assert any(r["id"] == 2 for r in results)


def test_inverted_index_search_no_match():
    """Test InvertedIndex search with no matches."""
    index = InvertedIndex("test-idx", "content")
    
    record = {"id": 1, "content": "hello world"}
    index.insert(record)
    
    results = list(index.search("nonexistent"))
    
    assert results == []


def test_inverted_index_delete():
    """Test InvertedIndex delete operation."""
    index = InvertedIndex("test-idx", "content")
    
    record = {"id": 1, "content": "hello world"}
    index.insert(record)
    
    deleted = index.delete(record)
    
    assert deleted is True
    assert list(index.search("hello")) == []


def test_dataset_index_builder_init():
    """Test DatasetIndexBuilder initialization."""
    builder = DatasetIndexBuilder()
    assert builder is not None


def test_dataset_index_builder_with_index_dir(tmp_path: Path):
    """Test DatasetIndexBuilder with custom index directory."""
    index_dir = tmp_path / "indexes"
    builder = DatasetIndexBuilder(index_dir)
    assert builder is not None


def test_build_hash_index(tmp_path: Path):
    """Test building hash index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id": "a", "value": 1}\n'
        '{"id": "b", "value": 2}\n'
        '{"id": "c", "value": 3}\n'
    )
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_hash_index(dataset, "id")
    
    assert metadata.index_type == IndexType.HASH
    assert metadata.field_name == "id"
    assert metadata.record_count == 3
    assert metadata.status == IndexStatus.READY


def test_build_hash_index_custom_id(tmp_path: Path):
    """Test building hash index with custom ID."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id": "a", "value": 1}\n')
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_hash_index(dataset, "id", index_id="custom-idx")
    
    assert metadata.index_id == "custom-idx"


def test_build_inverted_index(tmp_path: Path):
    """Test building inverted index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id": 1, "content": "hello world"}\n'
        '{"id": 2, "content": "world peace"}\n'
    )
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_inverted_index(dataset, "content")
    
    assert metadata.index_type == IndexType.INVERTED
    assert metadata.field_name == "content"
    assert metadata.record_count == 2
    assert metadata.status == IndexStatus.READY


def test_lookup_hash_index(tmp_path: Path):
    """Test looking up values in hash index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id": "key1", "value": "data1"}\n'
        '{"id": "key2", "value": "data2"}\n'
    )
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_hash_index(dataset, "id", index_id="test-idx")
    
    results = builder.lookup("test-idx", "key1")
    
    assert len(results) == 1
    assert results[0]["id"] == "key1"
    assert results[0]["value"] == "data1"


def test_search_inverted_index(tmp_path: Path):
    """Test searching inverted index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id": 1, "content": "hello world"}\n'
        '{"id": 2, "content": "world peace"}\n'
    )
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_inverted_index(dataset, "content", index_id="test-idx")
    
    results = list(builder.search("test-idx", "world"))
    
    assert len(results) == 2


def test_list_indexes(tmp_path: Path):
    """Test listing all indexes."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id": "a"}\n')
    
    builder = DatasetIndexBuilder()
    builder.build_hash_index(dataset, "id", index_id="idx1")
    builder.build_hash_index(dataset, "id", index_id="idx2")
    
    indexes = builder.list_indexes()
    
    assert len(indexes) == 2
    assert any(idx.index_id == "idx1" for idx in indexes)
    assert any(idx.index_id == "idx2" for idx in indexes)


def test_drop_index(tmp_path: Path):
    """Test dropping index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id": "a"}\n')
    
    builder = DatasetIndexBuilder()
    builder.build_hash_index(dataset, "id", index_id="test-idx")
    
    success = builder.drop_index("test-idx")
    
    assert success is True
    assert len(builder.list_indexes()) == 0


def test_drop_nonexistent_index():
    """Test dropping nonexistent index."""
    builder = DatasetIndexBuilder()
    
    success = builder.drop_index("nonexistent")
    
    assert success is False


def test_save_and_load_index(tmp_path: Path):
    """Test saving and loading index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id": "a", "value": 1}\n')
    
    index_dir = tmp_path / "indexes"
    builder = DatasetIndexBuilder(index_dir)
    
    metadata = builder.build_hash_index(dataset, "id", index_id="test-idx")
    builder.save_index("test-idx")
    
    # Create new builder and load
    new_builder = DatasetIndexBuilder(index_dir)
    loaded_metadata = new_builder.load_index("test-idx")
    
    assert loaded_metadata.index_id == metadata.index_id
    assert loaded_metadata.index_type == metadata.index_type


def test_get_statistics(tmp_path: Path):
    """Test getting index statistics."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id": "a"}\n')
    
    builder = DatasetIndexBuilder()
    builder.build_hash_index(dataset, "id", index_id="idx1")
    builder.build_hash_index(dataset, "id", index_id="idx2")
    
    stats = builder.get_statistics()
    
    assert stats["total_indexes"] == 2
    assert stats["total_records_indexed"] == 2


def test_query_optimizer_init():
    """Test QueryOptimizer initialization."""
    optimizer = QueryOptimizer()
    assert optimizer is not None


def test_query_optimizer_recommend_index():
    """Test QueryOptimizer index recommendation."""
    optimizer = QueryOptimizer()
    
    # Recommend hash index for exact match queries
    recommendation = optimizer.recommend_index_type("id", query_pattern="exact_match")
    assert recommendation == IndexType.HASH
    
    # Recommend inverted index for text search
    recommendation = optimizer.recommend_index_type("content", query_pattern="text_search")
    assert recommendation == IndexType.INVERTED


def test_query_optimizer_estimate_cost():
    """Test QueryOptimizer query cost estimation."""
    optimizer = QueryOptimizer()
    
    # Indexed query should have lower cost
    indexed_cost = optimizer.estimate_query_cost(indexed=True, dataset_size=10000)
    full_scan_cost = optimizer.estimate_query_cost(indexed=False, dataset_size=10000)
    
    assert indexed_cost < full_scan_cost


def test_build_hash_index_empty_dataset(tmp_path: Path):
    """Test building hash index on empty dataset."""
    dataset = tmp_path / "empty.jsonl"
    dataset.write_text("")
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_hash_index(dataset, "id")
    
    assert metadata.record_count == 0
    assert metadata.status == IndexStatus.READY


def test_build_inverted_index_empty_dataset(tmp_path: Path):
    """Test building inverted index on empty dataset."""
    dataset = tmp_path / "empty.jsonl"
    dataset.write_text("")
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_inverted_index(dataset, "content")
    
    assert metadata.record_count == 0
    assert metadata.status == IndexStatus.READY
