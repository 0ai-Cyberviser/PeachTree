"""Tests for dataset_streaming module."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from peachtree.dataset_streaming import (
    BufferStrategy,
    DatasetStreamProcessor,
    DatasetStreamReader,
    DatasetStreamWriter,
    StreamConfig,
    StreamingPipeline,
    StreamMode,
)


@pytest.fixture
def sample_dataset() -> Path:
    """Create a sample dataset for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for i in range(100):
            record = {
                "id": f"record_{i:03d}",
                "text": f"Sample text {i}",
                "category": "test" if i % 2 == 0 else "train",
                "value": i,
            }
            f.write(json.dumps(record, sort_keys=True) + "\n")
        
        return Path(f.name)


@pytest.fixture
def stream_config() -> StreamConfig:
    """Create stream configuration."""
    return StreamConfig(
        buffer_size=4096,
        buffer_strategy=BufferStrategy.LINE_BUFFERED,
        max_memory_mb=256,
    )


def test_stream_config_defaults():
    """Test StreamConfig defaults."""
    config = StreamConfig()
    
    assert config.buffer_size == 8192
    assert config.buffer_strategy == BufferStrategy.LINE_BUFFERED
    assert config.max_memory_mb == 512
    assert config.checkpoint_interval == 1000
    assert config.enable_compression is False


def test_stream_config_to_dict():
    """Test StreamConfig serialization."""
    config = StreamConfig(buffer_size=4096)
    
    data = config.to_dict()
    
    assert data["buffer_size"] == 4096
    assert data["buffer_strategy"] == "line_buffered"
    assert data["max_memory_mb"] == 512


def test_stream_reader_initialization(stream_config: StreamConfig):
    """Test DatasetStreamReader initialization."""
    reader = DatasetStreamReader(stream_config)
    
    assert reader.config == stream_config
    assert reader.stats.records_processed == 0


def test_stream_records(sample_dataset: Path, stream_config: StreamConfig):
    """Test streaming records."""
    reader = DatasetStreamReader(stream_config)
    
    records = list(reader.stream_records(sample_dataset))
    
    assert len(records) == 100
    assert records[0]["id"] == "record_000"
    assert reader.stats.records_processed == 100


def test_stream_records_with_filter(sample_dataset: Path):
    """Test streaming with filter."""
    reader = DatasetStreamReader()
    
    def filter_test(record: Dict[str, Any]) -> bool:
        return record["category"] == "test"
    
    records = list(reader.stream_records(sample_dataset, filter_fn=filter_test))
    
    assert len(records) == 50
    assert all(r["category"] == "test" for r in records)


def test_stream_records_with_transform(sample_dataset: Path):
    """Test streaming with transformation."""
    reader = DatasetStreamReader()
    
    def add_label(record: Dict[str, Any]) -> Dict[str, Any]:
        record["label"] = "transformed"
        return record
    
    records = list(reader.stream_records(sample_dataset, transform_fn=add_label))
    
    assert len(records) == 100
    assert all(r["label"] == "transformed" for r in records)


def test_stream_batches(sample_dataset: Path):
    """Test streaming in batches."""
    reader = DatasetStreamReader()
    
    batches = list(reader.stream_batches(sample_dataset, batch_size=10))
    
    assert len(batches) == 10
    assert len(batches[0]) == 10
    assert len(batches[-1]) == 10


def test_stream_batches_partial(sample_dataset: Path):
    """Test streaming with partial final batch."""
    reader = DatasetStreamReader()
    
    batches = list(reader.stream_batches(sample_dataset, batch_size=15))
    
    assert len(batches) == 7
    assert len(batches[-1]) == 10


def test_count_records(sample_dataset: Path):
    """Test counting records."""
    reader = DatasetStreamReader()
    
    count = reader.count_records(sample_dataset)
    
    assert count == 100


def test_sample_records(sample_dataset: Path):
    """Test sampling records."""
    reader = DatasetStreamReader()
    
    samples = reader.sample_records(sample_dataset, sample_size=10)
    
    assert len(samples) == 10
    assert samples[0]["id"] == "record_000"


def test_sample_records_with_skip(sample_dataset: Path):
    """Test sampling with skip."""
    reader = DatasetStreamReader()
    
    samples = reader.sample_records(sample_dataset, sample_size=5, skip=10)
    
    assert len(samples) == 5
    assert samples[0]["id"] == "record_010"


def test_stream_writer_initialization(stream_config: StreamConfig):
    """Test DatasetStreamWriter initialization."""
    writer = DatasetStreamWriter(stream_config)
    
    assert writer.config == stream_config
    assert writer.stats.records_processed == 0


def test_write_records():
    """Test writing records."""
    writer = DatasetStreamWriter()
    
    def records():
        for i in range(50):
            yield {"id": f"r{i}", "value": i}
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    stats = writer.write_records(records(), output_path)
    
    assert stats.records_processed == 50
    assert output_path.exists()
    
    # Verify content
    lines = output_path.read_text().splitlines()
    assert len(lines) == 50


def test_append_records(sample_dataset: Path):
    """Test appending records."""
    writer = DatasetStreamWriter()
    
    def new_records():
        for i in range(100, 110):
            yield {"id": f"record_{i:03d}", "value": i}
    
    # Append to existing dataset
    stats = writer.append_records(new_records(), sample_dataset)
    
    assert stats.records_processed == 10
    
    # Verify total count
    lines = sample_dataset.read_text().splitlines()
    assert len(lines) == 110


def test_stream_processor_initialization(stream_config: StreamConfig):
    """Test DatasetStreamProcessor initialization."""
    processor = DatasetStreamProcessor(stream_config)
    
    assert processor.config == stream_config


def test_process_transform(sample_dataset: Path):
    """Test process with transformation."""
    processor = DatasetStreamProcessor()
    
    def uppercase_text(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record["text"] = record["text"].upper()
        return record
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.process(sample_dataset, output_path, uppercase_text)
    
    assert result["records_filtered"] == 0
    assert output_path.exists()


def test_process_filter(sample_dataset: Path):
    """Test process with filtering."""
    processor = DatasetStreamProcessor()
    
    def filter_low_values(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return record if record["value"] >= 50 else None
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.process(sample_dataset, output_path, filter_low_values)
    
    assert result["records_filtered"] == 50


def test_filter_operation(sample_dataset: Path):
    """Test filter operation."""
    processor = DatasetStreamProcessor()
    
    def is_test(record: Dict[str, Any]) -> bool:
        return record["category"] == "test"
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.filter(sample_dataset, output_path, is_test)
    
    assert result["records_filtered"] == 50


def test_map_reduce(sample_dataset: Path):
    """Test map-reduce operation."""
    processor = DatasetStreamProcessor()
    
    def map_value(record: Dict[str, Any]) -> int:
        return record["value"]
    
    def sum_values(values: list) -> Dict[str, Any]:
        return {"total": sum(values), "count": len(values)}
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.map_reduce(sample_dataset, output_path, map_value, sum_values, batch_size=20)
    
    assert result["mapped_items"] == 100
    
    # Verify output
    output_data = json.loads(output_path.read_text())
    assert output_data["total"] == sum(range(100))
    assert output_data["count"] == 100


def test_merge_streams():
    """Test merging multiple streams."""
    processor = DatasetStreamProcessor()
    
    # Create two datasets
    datasets = []
    for idx in range(2):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(50):
                record = {"id": f"d{idx}_r{i}", "dataset": idx, "value": i}
                f.write(json.dumps(record, sort_keys=True) + "\n")
            datasets.append(Path(f.name))
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.merge_streams(datasets, output_path, dedup=False)
    
    assert result["total_read"] == 100
    assert result["total_written"] == 100


def test_merge_streams_with_dedup():
    """Test merging with deduplication."""
    processor = DatasetStreamProcessor()
    
    # Create datasets with duplicates
    datasets = []
    for idx in range(2):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(50):
                record = {"id": f"r{i}", "value": i}  # Same IDs
                f.write(json.dumps(record, sort_keys=True) + "\n")
            datasets.append(Path(f.name))
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = processor.merge_streams(datasets, output_path, dedup=True)
    
    assert result["total_read"] == 100
    assert result["total_written"] == 50
    assert result["duplicates_removed"] == 50


def test_split_stream(sample_dataset: Path):
    """Test splitting stream."""
    processor = DatasetStreamProcessor()
    
    def split_by_category(record: Dict[str, Any]) -> str:
        return record["category"]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        result = processor.split_stream(sample_dataset, output_dir, split_by_category, max_splits=10)
        
        assert result["splits"] == 2
        assert result["split_counts"]["test"] == 50
        assert result["split_counts"]["train"] == 50


def test_streaming_pipeline_initialization():
    """Test StreamingPipeline initialization."""
    pipeline = StreamingPipeline()
    
    assert len(pipeline.steps) == 0
    assert len(pipeline.step_names) == 0


def test_pipeline_add_filter():
    """Test adding filter to pipeline."""
    pipeline = StreamingPipeline()
    
    result = pipeline.add_filter("test_filter", lambda r: r["value"] > 10)
    
    assert result == pipeline
    assert len(pipeline.steps) == 1
    assert pipeline.step_names[0] == "filter:test_filter"


def test_pipeline_add_transform():
    """Test adding transform to pipeline."""
    pipeline = StreamingPipeline()
    
    result = pipeline.add_transform("uppercase", lambda r: {**r, "text": r["text"].upper()})
    
    assert result == pipeline
    assert len(pipeline.steps) == 1
    assert pipeline.step_names[0] == "transform:uppercase"


def test_pipeline_execute(sample_dataset: Path):
    """Test pipeline execution."""
    pipeline = StreamingPipeline()
    
    pipeline.add_filter("test_only", lambda r: r["category"] == "test")
    pipeline.add_transform("add_label", lambda r: {**r, "label": "processed"})
    
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        output_path = Path(f.name)
    
    result = pipeline.execute(sample_dataset, output_path)
    
    assert result["pipeline_steps"] == ["filter:test_only", "transform:add_label"]
    assert output_path.exists()
    
    # Verify filtered and transformed
    records = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert len(records) == 50
    assert all(r["category"] == "test" for r in records)
    assert all(r["label"] == "processed" for r in records)


def test_pipeline_describe():
    """Test pipeline description."""
    pipeline = StreamingPipeline()
    
    pipeline.add_filter("f1", lambda r: True)
    pipeline.add_transform("t1", lambda r: r)
    pipeline.add_map("m1", lambda r: r)
    
    description = pipeline.describe()
    
    assert description["total_steps"] == 3
    assert len(description["steps"]) == 3
    assert "filter:f1" in description["steps"]
    assert "transform:t1" in description["steps"]
    assert "map:m1" in description["steps"]


def test_stream_mode_enum():
    """Test StreamMode enum."""
    assert StreamMode.READ.value == "read"
    assert StreamMode.WRITE.value == "write"
    assert StreamMode.TRANSFORM.value == "transform"


def test_buffer_strategy_enum():
    """Test BufferStrategy enum."""
    assert BufferStrategy.LINE_BUFFERED.value == "line_buffered"
    assert BufferStrategy.BLOCK_BUFFERED.value == "block_buffered"
    assert BufferStrategy.UNBUFFERED.value == "unbuffered"
