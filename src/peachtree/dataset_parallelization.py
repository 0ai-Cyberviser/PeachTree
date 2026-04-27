"""Parallel processing for dataset operations with multi-threading and multi-processing."""

import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


class ParallelMode(Enum):
    """Modes for parallel processing."""
    
    THREADS = "threads"
    PROCESSES = "processes"
    ASYNC = "async"


class TaskStatus(Enum):
    """Status of parallel tasks."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""
    
    mode: ParallelMode = ParallelMode.PROCESSES
    max_workers: int = field(default_factory=lambda: mp.cpu_count())
    chunk_size: int = 1000
    timeout_seconds: Optional[int] = None
    ordered_results: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode.value,
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "timeout_seconds": self.timeout_seconds,
            "ordered_results": self.ordered_results,
        }


@dataclass
class TaskResult:
    """Result from a parallel task."""
    
    task_id: str
    status: TaskStatus
    result: Any
    error: Optional[str] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class ParallelStats:
    """Statistics for parallel processing."""
    
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_duration_seconds: float = 0.0
    avg_task_duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_duration_seconds": self.total_duration_seconds,
            "avg_task_duration_seconds": self.avg_task_duration_seconds,
        }


class ParallelExecutor:
    """Execute dataset operations in parallel."""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """Initialize parallel executor."""
        self.config = config or ParallelConfig()
        self.stats = ParallelStats()
    
    def _create_executor(self):
        """Create appropriate executor based on mode."""
        if self.config.mode == ParallelMode.THREADS:
            return ThreadPoolExecutor(max_workers=self.config.max_workers)
        elif self.config.mode == ParallelMode.PROCESSES:
            return ProcessPoolExecutor(max_workers=self.config.max_workers)
        else:
            raise ValueError(f"Unsupported mode: {self.config.mode}")
    
    def map(
        self,
        func: Callable,
        items: List[Any],
    ) -> List[TaskResult]:
        """Map function over items in parallel."""
        from time import time
        
        start_time = time()
        results: List[TaskResult] = []
        
        with self._create_executor() as executor:
            futures = {}
            
            for i, item in enumerate(items):
                task_id = f"task_{i:06d}"
                future = executor.submit(func, item)
                futures[future] = (task_id, time())
            
            self.stats.total_tasks = len(items)
            
            for future in as_completed(futures, timeout=self.config.timeout_seconds):
                task_id, task_start = futures[future]
                task_duration = time() - task_start
                
                try:
                    result_value = future.result()
                    results.append(TaskResult(
                        task_id=task_id,
                        status=TaskStatus.COMPLETED,
                        result=result_value,
                        duration_seconds=task_duration,
                    ))
                    self.stats.completed_tasks += 1
                
                except Exception as e:
                    results.append(TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        result=None,
                        error=str(e),
                        duration_seconds=task_duration,
                    ))
                    self.stats.failed_tasks += 1
        
        self.stats.total_duration_seconds = time() - start_time
        if self.stats.completed_tasks > 0:
            self.stats.avg_task_duration_seconds = (
                sum(r.duration_seconds for r in results if r.status == TaskStatus.COMPLETED) /
                self.stats.completed_tasks
            )
        
        return results
    
    def process_dataset_chunks(
        self,
        dataset_path: Path,
        process_func: Callable[[List[Dict[str, Any]]], Any],
    ) -> List[TaskResult]:
        """Process dataset in parallel chunks."""
        # Read and chunk dataset
        chunks = []
        current_chunk = []
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    current_chunk.append(record)
                    
                    if len(current_chunk) >= self.config.chunk_size:
                        chunks.append(current_chunk)
                        current_chunk = []
                
                except json.JSONDecodeError:
                    continue
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Process chunks in parallel
        return self.map(process_func, chunks)
    
    def get_statistics(self) -> ParallelStats:
        """Get processing statistics."""
        return self.stats


def _transform_record_worker(args: Tuple[Dict[str, Any], Callable]) -> Dict[str, Any]:
    """Worker function for transforming a single record."""
    record, transform_fn = args
    return transform_fn(record)


class ParallelDatasetProcessor:
    """Process datasets with parallel transformations."""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """Initialize parallel dataset processor."""
        self.config = config or ParallelConfig()
        self.executor = ParallelExecutor(config)
    
    def transform(
        self,
        input_path: Path,
        output_path: Path,
        transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Transform dataset records in parallel."""
        from time import time
        
        start_time = time()
        
        # Read all records
        records = []
        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Transform in parallel
        def process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [transform_fn(r) for r in chunk]
        
        results = self.executor.process_dataset_chunks(input_path, process_chunk)
        
        # Write results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as out_f:
            for result in results:
                if result.status == TaskStatus.COMPLETED and result.result:
                    for record in result.result:
                        out_f.write(json.dumps(record, sort_keys=True) + "\n")
        
        duration = time() - start_time
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "duration_seconds": duration,
            "stats": self.executor.get_statistics().to_dict(),
        }
    
    def filter(
        self,
        input_path: Path,
        output_path: Path,
        filter_fn: Callable[[Dict[str, Any]], bool],
    ) -> Dict[str, Any]:
        """Filter dataset records in parallel."""
        from time import time
        
        start_time = time()
        
        # Filter in parallel
        def process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [r for r in chunk if filter_fn(r)]
        
        results = self.executor.process_dataset_chunks(input_path, process_chunk)
        
        # Write results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_records = 0
        with output_path.open("w", encoding="utf-8") as out_f:
            for result in results:
                if result.status == TaskStatus.COMPLETED and result.result:
                    for record in result.result:
                        out_f.write(json.dumps(record, sort_keys=True) + "\n")
                        total_records += 1
        
        duration = time() - start_time
        
        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "records_written": total_records,
            "duration_seconds": duration,
            "stats": self.executor.get_statistics().to_dict(),
        }
    
    def aggregate(
        self,
        input_path: Path,
        aggregate_fn: Callable[[List[Dict[str, Any]]], Any],
        combine_fn: Callable[[List[Any]], Any],
    ) -> Any:
        """Aggregate dataset with parallel map-reduce."""
        # Aggregate chunks in parallel
        results = self.executor.process_dataset_chunks(input_path, aggregate_fn)
        
        # Combine results
        intermediate_results = [
            r.result for r in results
            if r.status == TaskStatus.COMPLETED and r.result is not None
        ]
        
        return combine_fn(intermediate_results)


class ParallelBatchProcessor:
    """Process multiple datasets in parallel."""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """Initialize parallel batch processor."""
        self.config = config or ParallelConfig()
        self.executor = ParallelExecutor(config)
    
    def process_datasets(
        self,
        dataset_paths: List[Path],
        process_fn: Callable[[Path], Any],
    ) -> List[TaskResult]:
        """Process multiple datasets in parallel."""
        return self.executor.map(process_fn, dataset_paths)
    
    def transform_datasets(
        self,
        dataset_paths: List[Path],
        output_dir: Path,
        transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Transform multiple datasets in parallel."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        def transform_dataset(input_path: Path) -> Dict[str, Any]:
            output_path = output_dir / input_path.name
            
            processor = ParallelDatasetProcessor(self.config)
            return processor.transform(input_path, output_path, transform_fn)
        
        results = self.executor.map(transform_dataset, dataset_paths)
        
        return [r.result for r in results if r.status == TaskStatus.COMPLETED]
    
    def merge_datasets(
        self,
        dataset_paths: List[Path],
        output_path: Path,
    ) -> Dict[str, Any]:
        """Merge multiple datasets in parallel."""
        from time import time
        
        start_time = time()
        
        def read_dataset(path: Path) -> List[Dict[str, Any]]:
            records = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            return records
        
        # Read all datasets in parallel
        results = self.executor.map(read_dataset, dataset_paths)
        
        # Merge results
        all_records = []
        for result in results:
            if result.status == TaskStatus.COMPLETED:
                all_records.extend(result.result)
        
        # Write merged dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as out_f:
            for record in all_records:
                out_f.write(json.dumps(record, sort_keys=True) + "\n")
        
        duration = time() - start_time
        
        return {
            "input_datasets": len(dataset_paths),
            "output_path": str(output_path),
            "total_records": len(all_records),
            "duration_seconds": duration,
            "stats": self.executor.get_statistics().to_dict(),
        }
