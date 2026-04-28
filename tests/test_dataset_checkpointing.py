"""Tests for dataset_checkpointing module."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_checkpointing import (
    CheckpointConfig,
    CheckpointedStreamProcessor,
    CheckpointManager,
    CheckpointMetadata,
    CheckpointStatus,
    CheckpointStrategy,
    ProcessingState,
    ResumableOperation,
)


@pytest.fixture
def checkpoint_config() -> CheckpointConfig:
    """Create checkpoint configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        return CheckpointConfig(
            strategy=CheckpointStrategy.RECORD_BASED,
            interval_records=10,
            max_checkpoints=3,
            checkpoint_dir=Path(tmpdir),
        )


@pytest.fixture
def sample_dataset() -> Path:
    """Create a sample dataset for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for i in range(50):
            record = {"id": f"r{i}", "value": i}
            f.write(json.dumps(record, sort_keys=True) + "\n")
        
        return Path(f.name)


def test_checkpoint_config_defaults():
    """Test CheckpointConfig defaults."""
    config = CheckpointConfig(strategy=CheckpointStrategy.TIME_BASED)
    
    assert config.strategy == CheckpointStrategy.TIME_BASED
    assert config.interval_seconds == 300
    assert config.interval_records == 10000
    assert config.max_checkpoints == 5
    assert config.compression is True


def test_checkpoint_config_to_dict():
    """Test CheckpointConfig serialization."""
    config = CheckpointConfig(
        strategy=CheckpointStrategy.RECORD_BASED,
        interval_records=100,
    )
    
    data = config.to_dict()
    
    assert data["strategy"] == "record_based"
    assert data["interval_records"] == 100


def test_checkpoint_metadata():
    """Test CheckpointMetadata creation."""
    metadata = CheckpointMetadata(
        checkpoint_id="ckpt_001",
        operation="test_op",
        status=CheckpointStatus.ACTIVE,
        created_at="2024-01-01T00:00:00Z",
        records_processed=100,
        bytes_processed=1024,
        progress_percent=50.0,
    )
    
    assert metadata.checkpoint_id == "ckpt_001"
    assert metadata.operation == "test_op"
    assert metadata.resumable is True


def test_checkpoint_metadata_to_dict():
    """Test CheckpointMetadata serialization."""
    metadata = CheckpointMetadata(
        checkpoint_id="ckpt_001",
        operation="test_op",
        status=CheckpointStatus.ACTIVE,
        created_at="2024-01-01T00:00:00Z",
        records_processed=100,
        bytes_processed=1024,
        progress_percent=50.0,
    )
    
    data = metadata.to_dict()
    
    assert data["checkpoint_id"] == "ckpt_001"
    assert data["status"] == "active"
    assert data["records_processed"] == 100


def test_processing_state():
    """Test ProcessingState creation."""
    state = ProcessingState(
        operation="test_op",
        input_path="/input.jsonl",
        output_path="/output.jsonl",
        current_position=10,
        records_processed=10,
        bytes_processed=1024,
        start_time="2024-01-01T00:00:00Z",
        last_checkpoint_time="2024-01-01T00:00:00Z",
    )
    
    assert state.operation == "test_op"
    assert state.current_position == 10
    assert state.records_processed == 10


def test_processing_state_to_dict():
    """Test ProcessingState serialization."""
    state = ProcessingState(
        operation="test_op",
        input_path="/input.jsonl",
        output_path="/output.jsonl",
        current_position=10,
        records_processed=10,
        bytes_processed=1024,
        start_time="2024-01-01T00:00:00Z",
        last_checkpoint_time="2024-01-01T00:00:00Z",
        custom_state={"key": "value"},
    )
    
    data = state.to_dict()
    
    assert data["operation"] == "test_op"
    assert data["current_position"] == 10
    assert data["custom_state"]["key"] == "value"


def test_checkpoint_manager_initialization():
    """Test CheckpointManager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.TIME_BASED,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        assert manager.config == config
        assert len(manager.checkpoints) == 0


def test_create_checkpoint():
    """Test creating a checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        metadata = manager.create_checkpoint("ckpt_001", state, "test_op")
        
        assert metadata.checkpoint_id == "ckpt_001"
        assert metadata.operation == "test_op"
        assert metadata.status == CheckpointStatus.ACTIVE


def test_load_checkpoint():
    """Test loading a checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
            compression=False,
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        manager.create_checkpoint("ckpt_001", state, "test_op")
        
        loaded_state = manager.load_checkpoint("ckpt_001")
        
        assert loaded_state is not None
        assert loaded_state.operation == "test_op"
        assert loaded_state.current_position == 10


def test_delete_checkpoint():
    """Test deleting a checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        manager.create_checkpoint("ckpt_001", state, "test_op")
        
        success = manager.delete_checkpoint("ckpt_001")
        
        assert success is True
        assert manager.checkpoints["ckpt_001"].status == CheckpointStatus.DELETED


def test_list_checkpoints():
    """Test listing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        # Create multiple checkpoints
        for i in range(3):
            state = ProcessingState(
                operation=f"op_{i}",
                input_path="/input.jsonl",
                output_path="/output.jsonl",
                current_position=i * 10,
                records_processed=i * 10,
                bytes_processed=i * 1024,
                start_time="2024-01-01T00:00:00Z",
                last_checkpoint_time="2024-01-01T00:00:00Z",
            )
            manager.create_checkpoint(f"ckpt_{i:03d}", state, f"op_{i}")
        
        checkpoints = manager.list_checkpoints()
        
        assert len(checkpoints) == 3


def test_list_checkpoints_filtered():
    """Test listing checkpoints with filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        # Create checkpoints for different operations
        for i in range(3):
            state = ProcessingState(
                operation="op_test" if i < 2 else "op_other",
                input_path="/input.jsonl",
                output_path="/output.jsonl",
                current_position=i * 10,
                records_processed=i * 10,
                bytes_processed=i * 1024,
                start_time="2024-01-01T00:00:00Z",
                last_checkpoint_time="2024-01-01T00:00:00Z",
            )
            manager.create_checkpoint(f"ckpt_{i:03d}", state, state.operation)
        
        checkpoints = manager.list_checkpoints(operation="op_test")
        
        assert len(checkpoints) == 2


def test_get_latest_checkpoint():
    """Test getting latest checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        # Create checkpoints with delays
        for i in range(3):
            state = ProcessingState(
                operation="test_op",
                input_path="/input.jsonl",
                output_path="/output.jsonl",
                current_position=i * 10,
                records_processed=i * 10,
                bytes_processed=i * 1024,
                start_time="2024-01-01T00:00:00Z",
                last_checkpoint_time="2024-01-01T00:00:00Z",
            )
            manager.create_checkpoint(f"ckpt_{i:03d}", state, "test_op")
        
        latest = manager.get_latest_checkpoint("test_op")
        
        assert latest is not None
        assert latest.checkpoint_id == "ckpt_002"


def test_mark_completed():
    """Test marking checkpoint as completed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        manager.create_checkpoint("ckpt_001", state, "test_op")
        manager.mark_completed("ckpt_001")
        
        assert manager.checkpoints["ckpt_001"].status == CheckpointStatus.COMPLETED


def test_mark_failed():
    """Test marking checkpoint as failed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        manager.create_checkpoint("ckpt_001", state, "test_op")
        manager.mark_failed("ckpt_001", "Test error")
        
        assert manager.checkpoints["ckpt_001"].status == CheckpointStatus.FAILED
        assert manager.checkpoints["ckpt_001"].error_message == "Test error"
        assert manager.checkpoints["ckpt_001"].resumable is False


def test_should_checkpoint_time_based():
    """Test time-based checkpoint strategy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.TIME_BASED,
            interval_seconds=10,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        from time import time
        
        # Should not checkpoint immediately
        assert manager.should_checkpoint(state, time()) is False
        
        # Should checkpoint after interval
        assert manager.should_checkpoint(state, time() - 15) is True


def test_should_checkpoint_record_based():
    """Test record-based checkpoint strategy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.RECORD_BASED,
            interval_records=10,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=20,
            records_processed=20,
            bytes_processed=2048,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        from time import time
        
        assert manager.should_checkpoint(state, time()) is True


def test_get_statistics():
    """Test getting checkpoint statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        
        # Create checkpoints
        for i in range(3):
            state = ProcessingState(
                operation=f"op_{i}",
                input_path="/input.jsonl",
                output_path="/output.jsonl",
                current_position=i * 10,
                records_processed=i * 10,
                bytes_processed=i * 1024,
                start_time="2024-01-01T00:00:00Z",
                last_checkpoint_time="2024-01-01T00:00:00Z",
            )
            manager.create_checkpoint(f"ckpt_{i:03d}", state, f"op_{i}")
        
        stats = manager.get_statistics()
        
        assert stats["total_checkpoints"] == 3
        assert stats["unique_operations"] == 3
        assert "status_counts" in stats


def test_resumable_operation_initialization():
    """Test ResumableOperation initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        operation = ResumableOperation("test_op", manager)
        
        assert operation.operation_name == "test_op"
        assert operation.checkpoint_manager == manager


def test_resumable_operation_initialize_state():
    """Test initializing state in resumable operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        operation = ResumableOperation("test_op", manager)
        
        state = operation.initialize_state(
            Path("/input.jsonl"),
            Path("/output.jsonl"),
        )
        
        assert state.operation == "test_op"
        assert state.current_position == 0


def test_checkpoint_strategy_enum():
    """Test CheckpointStrategy enum."""
    assert CheckpointStrategy.TIME_BASED.value == "time_based"
    assert CheckpointStrategy.RECORD_BASED.value == "record_based"
    assert CheckpointStrategy.SIZE_BASED.value == "size_based"
    assert CheckpointStrategy.MANUAL.value == "manual"


def test_checkpoint_status_enum():
    """Test CheckpointStatus enum."""
    assert CheckpointStatus.ACTIVE.value == "active"
    assert CheckpointStatus.COMPLETED.value == "completed"
    assert CheckpointStatus.FAILED.value == "failed"
    assert CheckpointStatus.CORRUPTED.value == "corrupted"
    assert CheckpointStatus.DELETED.value == "deleted"


def test_checkpointed_stream_processor_initialization():
    """Test CheckpointedStreamProcessor initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.RECORD_BASED,
            interval_records=10,
            checkpoint_dir=Path(tmpdir),
        )
        
        manager = CheckpointManager(config)
        processor = CheckpointedStreamProcessor(manager)
        
        assert processor.operation_name == "stream_process"
        assert processor.checkpoint_manager == manager


def test_checkpoint_compression():
    """Test checkpoint with compression."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
            compression=True,
        )
        
        manager = CheckpointManager(config)
        
        state = ProcessingState(
            operation="test_op",
            input_path="/input.jsonl",
            output_path="/output.jsonl",
            current_position=10,
            records_processed=10,
            bytes_processed=1024,
            start_time="2024-01-01T00:00:00Z",
            last_checkpoint_time="2024-01-01T00:00:00Z",
        )
        
        manager.create_checkpoint("ckpt_001", state, "test_op")
        
        # Check compressed file exists
        checkpoint_path = manager._get_checkpoint_path("ckpt_001")
        compressed_path = Path(str(checkpoint_path) + ".gz")
        
        assert compressed_path.exists()
        
        # Load and verify
        loaded_state = manager.load_checkpoint("ckpt_001")
        assert loaded_state is not None
        assert loaded_state.current_position == 10


def test_cleanup_old_checkpoints():
    """Test cleanup of old checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CheckpointConfig(
            strategy=CheckpointStrategy.MANUAL,
            checkpoint_dir=Path(tmpdir),
            max_checkpoints=2,
        )
        
        manager = CheckpointManager(config)
        
        # Create 4 checkpoints
        for i in range(4):
            state = ProcessingState(
                operation="test_op",
                input_path="/input.jsonl",
                output_path="/output.jsonl",
                current_position=i * 10,
                records_processed=i * 10,
                bytes_processed=i * 1024,
                start_time="2024-01-01T00:00:00Z",
                last_checkpoint_time="2024-01-01T00:00:00Z",
            )
            manager.create_checkpoint(f"ckpt_{i:03d}", state, "test_op")
        
        # Check that old checkpoints were deleted
        active = manager.list_checkpoints(operation="test_op", status=CheckpointStatus.ACTIVE)
        assert len(active) <= 2
