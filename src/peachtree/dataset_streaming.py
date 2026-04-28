"""Memory-efficient streaming for large datasets."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional


class StreamMode(Enum):
    """Streaming modes."""
    
    READ = "read"
    WRITE = "write"
    TRANSFORM = "transform"


class BufferStrategy(Enum):
    """Buffer strategies for streaming."""
    
    LINE_BUFFERED = "line_buffered"
    BLOCK_BUFFERED = "block_buffered"
    UNBUFFERED = "unbuffered"


@dataclass
class StreamConfig:
    """Configuration for streaming operations."""
    
    buffer_size: int = 8192  # 8KB default
    buffer_strategy: BufferStrategy = BufferStrategy.LINE_BUFFERED
    max_memory_mb: int = 512
    checkpoint_interval: int = 1000  # Records
    enable_compression: bool = False
    compression_level: int = 6
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "buffer_size": self.buffer_size,
            "buffer_strategy": self.buffer_strategy.value,
            "max_memory_mb": self.max_memory_mb,
            "checkpoint_interval": self.checkpoint_interval,
            "enable_compression": self.enable_compression,
            "compression_level": self.compression_level,
        }


@dataclass
class StreamStats:
    """Statistics for streaming operations."""
    
    records_processed: int = 0
    bytes_read: int = 0
    bytes_written: int = 0
    duration_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    throughput_records_per_sec: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "records_processed": self.records_processed,
            "bytes_read": self.bytes_read,
            "bytes_written": self.bytes_written,
            "duration_seconds": self.duration_seconds,
            "peak_memory_mb": self.peak_memory_mb,
            "throughput_records_per_sec": self.throughput_records_per_sec,
        }


class DatasetStreamReader:
    """Memory-efficient dataset reader with streaming."""
    
    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize stream reader."""
        self.config = config or StreamConfig()
        self.stats = StreamStats()
        self._start_time: Optional[float] = None
    
    def stream_records(
        self,
        dataset_path: Path,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
        transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream records from dataset with optional filtering and transformation."""
        from time import time
        
        self._start_time = time()
        total_records_read = 0
        
        with dataset_path.open("r", encoding="utf-8", buffering=self.config.buffer_size) as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    self.stats.bytes_read += len(line.encode("utf-8"))
                    total_records_read += 1
                    
                    # Apply filter if provided
                    if filter_fn and not filter_fn(record):
                        continue
                    
                    # Apply transformation if provided
                    if transform_fn:
                        record = transform_fn(record)
                    
                    self.stats.records_processed += 1
                    yield record
                    
                except json.JSONDecodeError:
                    continue
        
        # Calculate final stats
        if self._start_time:
            self.stats.duration_seconds = time() - self._start_time
            if self.stats.duration_seconds > 0:
                self.stats.throughput_records_per_sec = (
                    self.stats.records_processed / self.stats.duration_seconds
                )
    
    def stream_batches(
        self,
        dataset_path: Path,
        batch_size: int,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> Iterator[List[Dict[str, Any]]]:
        """Stream records in batches for efficient processing."""
        batch: List[Dict[str, Any]] = []
        
        for record in self.stream_records(dataset_path, filter_fn=filter_fn):
            batch.append(record)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield final partial batch
        if batch:
            yield batch
    
    def count_records(self, dataset_path: Path) -> int:
        """Count records efficiently without loading entire dataset."""
        count = 0
        for _ in self.stream_records(dataset_path):
            count += 1
        return count
    
    def sample_records(
        self,
        dataset_path: Path,
        sample_size: int,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Sample records from dataset."""
        samples: List[Dict[str, Any]] = []
        
        for i, record in enumerate(self.stream_records(dataset_path)):
            if i < skip:
                continue
            
            samples.append(record)
            
            if len(samples) >= sample_size:
                break
        
        return samples
    
    def get_statistics(self) -> StreamStats:
        """Get streaming statistics."""
        return self.stats


class DatasetStreamWriter:
    """Memory-efficient dataset writer with streaming."""
    
    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize stream writer."""
        self.config = config or StreamConfig()
        self.stats = StreamStats()
        self._start_time: Optional[float] = None
    
    def write_records(
        self,
        records: Iterator[Dict[str, Any]],
        output_path: Path,
        append: bool = False,
    ) -> StreamStats:
        """Write records to dataset using streaming."""
        from time import time
        
        self._start_time = time()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "a" if append else "w"
        
        with output_path.open(mode, encoding="utf-8", buffering=self.config.buffer_size) as f:
            for record in records:
                line = json.dumps(record, sort_keys=True) + "\n"
                f.write(line)
                
                self.stats.records_processed += 1
                self.stats.bytes_written += len(line.encode("utf-8"))
                
                # Flush periodically
                if self.stats.records_processed % self.config.checkpoint_interval == 0:
                    f.flush()
        
        # Calculate final stats
        if self._start_time:
            self.stats.duration_seconds = time() - self._start_time
            if self.stats.duration_seconds > 0:
                self.stats.throughput_records_per_sec = (
                    self.stats.records_processed / self.stats.duration_seconds
                )
        
        return self.stats
    
    def append_records(
        self,
        records: Iterator[Dict[str, Any]],
        output_path: Path,
    ) -> StreamStats:
        """Append records to existing dataset."""
        return self.write_records(records, output_path, append=True)


class DatasetStreamProcessor:
    """Process datasets with streaming transformations."""
    
    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize stream processor."""
        self.config = config or StreamConfig()
    
    def process(
        self,
        input_path: Path,
        output_path: Path,
        transform_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Process dataset with transformation function."""
        reader = DatasetStreamReader(self.config)
        writer = DatasetStreamWriter(self.config)
        
        def transformed_records() -> Iterator[Dict[str, Any]]:
            for record in reader.stream_records(input_path):
                transformed = transform_fn(record)
                if transformed is not None:
                    yield transformed
        
        write_stats = writer.write_records(transformed_records(), output_path)
        read_stats = reader.get_statistics()
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "read_stats": read_stats.to_dict(),
            "write_stats": write_stats.to_dict(),
            "records_filtered": read_stats.records_processed - write_stats.records_processed,
        }
    
    def filter(
        self,
        input_path: Path,
        output_path: Path,
        filter_fn: Callable[[Dict[str, Any]], bool],
    ) -> Dict[str, Any]:
        """Filter dataset records."""
        reader = DatasetStreamReader(self.config)
        writer = DatasetStreamWriter(self.config)
        
        def filtered_records() -> Iterator[Dict[str, Any]]:
            # Stream all records without filtering in reader
            for record in reader.stream_records(input_path):
                # Apply filter here so we count all records read
                if filter_fn(record):
                    yield record
        
        write_stats = writer.write_records(filtered_records(), output_path)
        read_stats = reader.get_statistics()
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "read_stats": read_stats.to_dict(),
            "write_stats": write_stats.to_dict(),
            "records_filtered": read_stats.records_processed - write_stats.records_processed,
        }
    
    def map_reduce(
        self,
        input_path: Path,
        output_path: Path,
        map_fn: Callable[[Dict[str, Any]], Any],
        reduce_fn: Callable[[List[Any]], Dict[str, Any]],
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """Map-reduce processing on dataset."""
        reader = DatasetStreamReader(self.config)
        mapped_values: List[Any] = []
        
        # Map phase
        for batch in reader.stream_batches(input_path, batch_size):
            for record in batch:
                mapped_values.append(map_fn(record))
        
        # Reduce phase
        result = reduce_fn(mapped_values)
        
        # Write result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "mapped_items": len(mapped_values),
            "read_stats": reader.get_statistics().to_dict(),
        }
    
    def merge_streams(
        self,
        input_paths: List[Path],
        output_path: Path,
        dedup: bool = False,
    ) -> Dict[str, Any]:
        """Merge multiple dataset streams."""
        writer = DatasetStreamWriter(self.config)
        seen_ids: set = set() if dedup else set()
        total_read = 0
        total_written = 0
        
        def merged_records() -> Iterator[Dict[str, Any]]:
            nonlocal total_read
            
            for input_path in input_paths:
                reader = DatasetStreamReader(self.config)
                
                for record in reader.stream_records(input_path):
                    total_read += 1
                    
                    if dedup:
                        record_id = record.get("id", str(hash(json.dumps(record, sort_keys=True))))
                        if record_id in seen_ids:
                            continue
                        seen_ids.add(record_id)
                    
                    yield record
        
        write_stats = writer.write_records(merged_records(), output_path)
        total_written = write_stats.records_processed
        
        return {
            "input_paths": [str(p) for p in input_paths],
            "output_path": str(output_path),
            "total_read": total_read,
            "total_written": total_written,
            "duplicates_removed": total_read - total_written if dedup else 0,
        }
    
    def split_stream(
        self,
        input_path: Path,
        output_dir: Path,
        split_fn: Callable[[Dict[str, Any]], str],
        max_splits: int = 10,
    ) -> Dict[str, Any]:
        """Split dataset stream into multiple outputs based on split function."""
        reader = DatasetStreamReader(self.config)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        writers: Dict[str, Any] = {}
        split_counts: Dict[str, int] = {}
        
        try:
            for record in reader.stream_records(input_path):
                split_key = split_fn(record)
                
                # Limit number of splits
                if split_key not in writers and len(writers) >= max_splits:
                    split_key = "overflow"
                
                if split_key not in writers:
                    output_path = output_dir / f"{split_key}.jsonl"
                    writers[split_key] = output_path.open("w", encoding="utf-8")
                    split_counts[split_key] = 0
                
                line = json.dumps(record, sort_keys=True) + "\n"
                writers[split_key].write(line)
                split_counts[split_key] += 1
        
        finally:
            # Close all writers
            for writer in writers.values():
                writer.close()
        
        return {
            "input_path": str(input_path),
            "output_dir": str(output_dir),
            "splits": len(split_counts),
            "split_counts": split_counts,
            "read_stats": reader.get_statistics().to_dict(),
        }


class StreamingPipeline:
    """Build and execute streaming data pipelines."""
    
    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize streaming pipeline."""
        self.config = config or StreamConfig()
        self.steps: List[Callable] = []
        self.step_names: List[str] = []
    
    def add_filter(
        self,
        name: str,
        filter_fn: Callable[[Dict[str, Any]], bool],
    ) -> "StreamingPipeline":
        """Add filter step to pipeline."""
        self.steps.append(lambda records: (r for r in records if filter_fn(r)))
        self.step_names.append(f"filter:{name}")
        return self
    
    def add_transform(
        self,
        name: str,
        transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> "StreamingPipeline":
        """Add transformation step to pipeline."""
        self.steps.append(lambda records: (transform_fn(r) for r in records))
        self.step_names.append(f"transform:{name}")
        return self
    
    def add_map(
        self,
        name: str,
        map_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> "StreamingPipeline":
        """Add map step to pipeline."""
        self.steps.append(lambda records: (map_fn(r) for r in records))
        self.step_names.append(f"map:{name}")
        return self
    
    def execute(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Dict[str, Any]:
        """Execute pipeline on dataset."""
        from time import time
        
        start_time = time()
        
        # Create initial record stream
        reader = DatasetStreamReader(self.config)
        records = reader.stream_records(input_path)
        
        # Apply each step
        for step in self.steps:
            records = step(records)
        
        # Write output
        writer = DatasetStreamWriter(self.config)
        write_stats = writer.write_records(records, output_path)
        
        duration = time() - start_time
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "pipeline_steps": self.step_names,
            "duration_seconds": duration,
            "write_stats": write_stats.to_dict(),
            "read_stats": reader.get_statistics().to_dict(),
        }
    
    def describe(self) -> Dict[str, Any]:
        """Describe pipeline configuration."""
        return {
            "steps": self.step_names,
            "total_steps": len(self.steps),
            "config": self.config.to_dict(),
        }
