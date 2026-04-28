"""Tests for parallel dataset processing."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


from peachtree.dataset_parallelization import (
    ParallelExecutor,
    ParallelDatasetProcessor,
    ParallelBatchProcessor,
    ParallelConfig,
    ParallelStats,
    ParallelMode,
    TaskStatus,
    TaskResult,
)


def test_parallel_mode_enum():
    """Test ParallelMode enum values."""
    assert ParallelMode.THREADS.value == "threads"
    assert ParallelMode.PROCESSES.value == "processes"
    assert ParallelMode.ASYNC.value == "async"


def test_task_status_enum():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


def test_parallel_config_defaults():
    """Test ParallelConfig default values."""
    config = ParallelConfig()
    assert config.mode == ParallelMode.PROCESSES
    assert config.max_workers is None
    assert config.chunk_size == 1000


def test_parallel_config_custom():
    """Test ParallelConfig custom values."""
    config = ParallelConfig(
        mode=ParallelMode.THREADS,
        max_workers=4,
        chunk_size=500,
    )
    assert config.mode == ParallelMode.THREADS
    assert config.max_workers == 4
    assert config.chunk_size == 500


def test_task_result_success():
    """Test TaskResult for successful task."""
    result = TaskResult(task_id=0, status=TaskStatus.COMPLETED, result="success")
    assert result.task_id == 0
    assert result.status == TaskStatus.COMPLETED
    assert result.result == "success"
    assert result.error is None


def test_task_result_failure():
    """Test TaskResult for failed task."""
    result = TaskResult(task_id=1, status=TaskStatus.FAILED, error="test error")
    assert result.task_id == 1
    assert result.status == TaskStatus.FAILED
    assert result.result is None
    assert result.error == "test error"


def test_parallel_stats_empty():
    """Test ParallelStats with no tasks."""
    stats = ParallelStats(
        total_tasks=0,
        completed_tasks=0,
        failed_tasks=0,
        total_time_seconds=0.0,
        avg_task_time_seconds=0.0,
    )
    assert stats.total_tasks == 0
    assert stats.completed_tasks == 0
    assert stats.failed_tasks == 0


def test_parallel_stats_with_tasks():
    """Test ParallelStats with tasks."""
    stats = ParallelStats(
        total_tasks=10,
        completed_tasks=8,
        failed_tasks=2,
        total_time_seconds=5.0,
        avg_task_time_seconds=0.5,
    )
    assert stats.total_tasks == 10
    assert stats.completed_tasks == 8
    assert stats.failed_tasks == 2
    assert stats.total_time_seconds == 5.0


def test_parallel_executor_init():
    """Test ParallelExecutor initialization."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=4)
    executor = ParallelExecutor(config)
    assert executor.config == config


def test_parallel_executor_execute_tasks():
    """Test ParallelExecutor task execution."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    executor = ParallelExecutor(config)
    
    def square(x: int) -> int:
        return x * x
    
    results = executor.execute_tasks(square, [1, 2, 3, 4, 5])
    
    assert len(results) == 5
    assert all(r.status == TaskStatus.COMPLETED for r in results)
    assert [r.result for r in results] == [1, 4, 9, 16, 25]


def test_parallel_executor_execute_with_error():
    """Test ParallelExecutor handles errors."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    executor = ParallelExecutor(config)
    
    def failing_func(x: int) -> int:
        if x == 3:
            raise ValueError("Test error")
        return x * x
    
    results = executor.execute_tasks(failing_func, [1, 2, 3, 4, 5])
    
    assert len(results) == 5
    completed = [r for r in results if r.status == TaskStatus.COMPLETED]
    failed = [r for r in results if r.status == TaskStatus.FAILED]
    
    assert len(completed) == 4
    assert len(failed) == 1
    assert "Test error" in failed[0].error


def test_parallel_executor_get_statistics():
    """Test ParallelExecutor statistics."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    executor = ParallelExecutor(config)
    
    def identity(x: int) -> int:
        return x
    
    executor.execute_tasks(identity, [1, 2, 3, 4, 5])
    stats = executor.get_statistics()
    
    assert stats.total_tasks == 5
    assert stats.completed_tasks == 5
    assert stats.failed_tasks == 0


def test_parallel_dataset_processor_init():
    """Test ParallelDatasetProcessor initialization."""
    config = ParallelConfig()
    processor = ParallelDatasetProcessor(config)
    assert processor.config == config


def test_parallel_dataset_processor_transform(tmp_path: Path):
    """Test parallel dataset transformation."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelDatasetProcessor(config)
    
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "output.jsonl"
    
    input_file.write_text('{"id": 1, "value": "a"}\n{"id": 2, "value": "b"}\n')
    
    def transform(record: Dict[str, Any]) -> Dict[str, Any]:
        record["value"] = record["value"].upper()
        return record
    
    result = processor.transform(input_file, output_file, transform)
    
    assert result["records_processed"] == 2
    assert result["records_output"] == 2
    
    output_records = [line for line in output_file.read_text().strip().split("\n")]
    assert len(output_records) == 2


def test_parallel_dataset_processor_filter(tmp_path: Path):
    """Test parallel dataset filtering."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelDatasetProcessor(config)
    
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "output.jsonl"
    
    input_file.write_text(
        '{"id": 1, "value": 10}\n'
        '{"id": 2, "value": 5}\n'
        '{"id": 3, "value": 20}\n'
    )
    
    def is_large(record: Dict[str, Any]) -> bool:
        return record["value"] > 8
    
    result = processor.filter(input_file, output_file, is_large)
    
    assert result["records_processed"] == 3
    assert result["records_output"] == 2


def test_parallel_dataset_processor_aggregate(tmp_path: Path):
    """Test parallel dataset aggregation."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelDatasetProcessor(config)
    
    input_file = tmp_path / "input.jsonl"
    input_file.write_text(
        '{"id": 1, "value": 10}\n'
        '{"id": 2, "value": 20}\n'
        '{"id": 3, "value": 30}\n'
    )
    
    def sum_values(records: list[Dict[str, Any]]) -> Dict[str, Any]:
        total = sum(r["value"] for r in records)
        return {"total": total, "count": len(records)}
    
    result = processor.aggregate(input_file, sum_values)
    
    assert result["total"] == 60
    assert result["count"] == 3


def test_parallel_batch_processor_init():
    """Test ParallelBatchProcessor initialization."""
    config = ParallelConfig()
    processor = ParallelBatchProcessor(config)
    assert processor.config == config


def test_parallel_batch_processor_transform_datasets(tmp_path: Path):
    """Test batch dataset transformation."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelBatchProcessor(config)
    
    input1 = tmp_path / "input1.jsonl"
    input2 = tmp_path / "input2.jsonl"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    input1.write_text('{"id": 1}\n')
    input2.write_text('{"id": 2}\n')
    
    def transform(record: Dict[str, Any]) -> Dict[str, Any]:
        record["processed"] = True
        return record
    
    result = processor.transform_datasets([input1, input2], output_dir, transform)
    
    assert result["total_datasets"] == 2
    assert result["successful"] == 2
    assert result["failed"] == 0


def test_parallel_batch_processor_merge_datasets(tmp_path: Path):
    """Test batch dataset merging."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelBatchProcessor(config)
    
    input1 = tmp_path / "input1.jsonl"
    input2 = tmp_path / "input2.jsonl"
    output = tmp_path / "merged.jsonl"
    
    input1.write_text('{"id": 1}\n{"id": 2}\n')
    input2.write_text('{"id": 3}\n')
    
    result = processor.merge_datasets([input1, input2], output)
    
    assert result["total_datasets"] == 2
    assert result["total_records"] == 3
    
    output_records = output.read_text().strip().split("\n")
    assert len(output_records) == 3


def test_parallel_batch_processor_filter_datasets(tmp_path: Path):
    """Test batch dataset filtering."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2)
    processor = ParallelBatchProcessor(config)
    
    input1 = tmp_path / "input1.jsonl"
    input2 = tmp_path / "input2.jsonl"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    input1.write_text('{"id": 1, "value": 10}\n')
    input2.write_text('{"id": 2, "value": 5}\n')
    
    def is_large(record: Dict[str, Any]) -> bool:
        return record["value"] > 8
    
    result = processor.filter_datasets([input1, input2], output_dir, is_large)
    
    assert result["total_datasets"] == 2
    assert result["successful"] == 2


def test_parallel_batch_processor_get_statistics():
    """Test ParallelBatchProcessor statistics."""
    config = ParallelConfig()
    processor = ParallelBatchProcessor(config)
    
    results = [
        {"records_processed": 10},
        {"records_processed": 20},
    ]
    
    stats = processor.get_statistics(results)
    
    assert stats["total_operations"] == 2
    assert stats["total_records"] == 30


def test_parallel_executor_processes_mode():
    """Test ParallelExecutor with processes mode."""
    config = ParallelConfig(mode=ParallelMode.PROCESSES, max_workers=2)
    executor = ParallelExecutor(config)
    
    def double(x: int) -> int:
        return x * 2
    
    results = executor.execute_tasks(double, [1, 2, 3])
    
    assert len(results) == 3
    assert all(r.status == TaskStatus.COMPLETED for r in results)
    assert [r.result for r in results] == [2, 4, 6]


def test_parallel_executor_chunk_size():
    """Test ParallelExecutor respects chunk size."""
    config = ParallelConfig(mode=ParallelMode.THREADS, max_workers=2, chunk_size=2)
    executor = ParallelExecutor(config)
    
    def identity(x: int) -> int:
        return x
    
    results = executor.execute_tasks(identity, list(range(10)))
    
    assert len(results) == 10
    assert all(r.status == TaskStatus.COMPLETED for r in results)


def test_parallel_dataset_processor_empty_dataset(tmp_path: Path):
    """Test processing empty dataset."""
    config = ParallelConfig()
    processor = ParallelDatasetProcessor(config)
    
    input_file = tmp_path / "empty.jsonl"
    output_file = tmp_path / "output.jsonl"
    
    input_file.write_text("")
    
    def transform(record: Dict[str, Any]) -> Dict[str, Any]:
        return record
    
    result = processor.transform(input_file, output_file, transform)
    
    assert result["records_processed"] == 0
    assert result["records_output"] == 0


def test_parallel_batch_processor_empty_batch(tmp_path: Path):
    """Test processing empty batch."""
    config = ParallelConfig()
    processor = ParallelBatchProcessor(config)
    
    output = tmp_path / "output.jsonl"
    
    result = processor.merge_datasets([], output)
    
    assert result["total_datasets"] == 0
    assert result["total_records"] == 0


def test_parallel_executor_no_workers_specified():
    """Test ParallelExecutor uses default worker count."""
    config = ParallelConfig(mode=ParallelMode.THREADS)
    executor = ParallelExecutor(config)
    
    def identity(x: int) -> int:
        return x
    
    results = executor.execute_tasks(identity, [1, 2, 3])
    
    assert len(results) == 3
    assert all(r.status == TaskStatus.COMPLETED for r in results)
