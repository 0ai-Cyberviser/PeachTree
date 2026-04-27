"""Tests for dataset indexing - matching actual APIs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from peachtree.dataset_indexing import (
    DatasetIndexBuilder,
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
    assert IndexStatus.STALE.value == "stale"
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
    index = HashIndex("id")
    assert index.field_name == "id"


def test_hash_index_add():
    """Test HashIndex add operation."""
    index = HashIndex("id")
    
    index.add("rec1", "key1")
    index.add("rec2", "key2")
    
    assert index.size() == 2


def test_hash_index_lookup():
    """Test HashIndex lookup operation."""
    index = HashIndex("id")
    
    index.add("rec1", "key1")
    index.add("rec2", "key1")  # Same key, different record
    
    results = index.lookup("key1")
    
    assert len(results) == 2
    assert "rec1" in results
    assert "rec2" in results


def test_hash_index_lookup_missing():
    """Test HashIndex lookup for missing key."""
    index = HashIndex("id")
    
    results = index.lookup("nonexistent")
    
    assert results == []


def test_hash_index_remove():
    """Test HashIndex remove operation."""
    index = HashIndex("id")
    
    index.add("rec1", "key1")
    index.remove("rec1", "key1")
    
    assert index.lookup("key1") == []


def test_hash_index_size():
    """Test HashIndex size method."""
    index = HashIndex("category")
    
    index.add("rec1", "A")
    index.add("rec2", "A")
    index.add("rec3", "B")
    
    # Size is number of unique values
    assert index.size() == 2


def test_inverted_index_init():
    """Test InvertedIndex initialization."""
    index = InvertedIndex("content")
    assert index.field_name == "content"


def test_inverted_index_add():
    """Test InvertedIndex add operation."""
    index = InvertedIndex("content")
    
    index.add("rec1", "hello world")
    
    assert index.size() > 0


def test_inverted_index_search():
    """Test InvertedIndex search operation."""
    index = InvertedIndex("content")
    
    index.add("rec1", "hello world")
    index.add("rec2", "world peace")
    index.add("rec3", "hello there")
    
    results = index.search("world")
    
    assert len(results) == 2
    assert "rec1" in results
    assert "rec2" in results


def test_inverted_index_search_no_match():
    """Test InvertedIndex search with no matches."""
    index = InvertedIndex("content")
    
    index.add("rec1", "hello world")
    
    results = index.search("nonexistent")
    
    assert len(results) == 0


def test_inverted_index_remove():
    """Test InvertedIndex remove operation."""
    index = InvertedIndex("content")
    
    index.add("rec1", "hello world")
    index.remove("rec1", "hello world")
    
    results = index.search("hello")
    assert len(results) == 0


def test_inverted_index_size():
    """Test InvertedIndex size method."""
    index = InvertedIndex("content")
    
    index.add("rec1", "hello world")
    index.add("rec2", "world peace")
    
    # Size is number of unique tokens
    assert index.size() > 0


def test_dataset_index_builder_init():
    """Test DatasetIndexBuilder initialization."""
    builder = DatasetIndexBuilder()
    assert builder is not None


def test_dataset_index_builder_with_index_dir(tmp_path: Path):
    """Test DatasetIndexBuilder with custom index directory."""
    index_dir = tmp_path / "indexes"
    builder = DatasetIndexBuilder(index_dir)
    assert builder.index_dir == index_dir


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
        '{"id": "1", "content": "hello world"}\n'
        '{"id": "2", "content": "world peace"}\n'
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
    
    # lookup returns list of record IDs
    results = builder.lookup("test-idx", "key1")
    
    assert len(results) >= 1


def test_search_inverted_index(tmp_path: Path):
    """Test searching inverted index."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id": "1", "content": "hello world"}\n'
        '{"id": "2", "content": "world peace"}\n'
    )
    
    builder = DatasetIndexBuilder()
    metadata = builder.build_inverted_index(dataset, "content", index_id="test-idx")
    
    # search returns set of record IDs
    results = builder.search("test-idx", "world")
    
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
