"""Save and restore processing state for long-running dataset operations."""

import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CheckpointStrategy(Enum):
    """Strategies for creating checkpoints."""
    
    TIME_BASED = "time_based"
    RECORD_BASED = "record_based"
    SIZE_BASED = "size_based"
    MANUAL = "manual"


class CheckpointStatus(Enum):
    """Status of a checkpoint."""
    
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    DELETED = "deleted"


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    
    checkpoint_id: str
    operation: str
    status: CheckpointStatus
    created_at: str
    records_processed: int
    bytes_processed: int
    progress_percent: float
    resumable: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "operation": self.operation,
            "status": self.status.value,
            "created_at": self.created_at,
            "records_processed": self.records_processed,
            "bytes_processed": self.bytes_processed,
            "progress_percent": self.progress_percent,
            "resumable": self.resumable,
            "error_message": self.error_message,
        }


@dataclass
class CheckpointConfig:
    """Configuration for checkpointing."""
    
    strategy: CheckpointStrategy
    interval_seconds: int = 300  # 5 minutes
    interval_records: int = 10000
    interval_bytes: int = 10 * 1024 * 1024  # 10MB
    max_checkpoints: int = 5
    compression: bool = True
    checkpoint_dir: Optional[Path] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy": self.strategy.value,
            "interval_seconds": self.interval_seconds,
            "interval_records": self.interval_records,
            "interval_bytes": self.interval_bytes,
            "max_checkpoints": self.max_checkpoints,
            "compression": self.compression,
            "checkpoint_dir": str(self.checkpoint_dir) if self.checkpoint_dir else None,
        }


@dataclass
class ProcessingState:
    """State of a processing operation."""
    
    operation: str
    input_path: str
    output_path: str
    current_position: int
    records_processed: int
    bytes_processed: int
    start_time: str
    last_checkpoint_time: str
    custom_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "current_position": self.current_position,
            "records_processed": self.records_processed,
            "bytes_processed": self.bytes_processed,
            "start_time": self.start_time,
            "last_checkpoint_time": self.last_checkpoint_time,
            "custom_state": self.custom_state,
        }


class CheckpointManager:
    """Manage checkpoints for long-running operations."""
    
    def __init__(self, config: CheckpointConfig):
        """Initialize checkpoint manager."""
        self.config = config
        
        # Use default checkpoint directory if not specified
        if self.config.checkpoint_dir is None:
            self.config.checkpoint_dir = Path.cwd() / ".checkpoints"
        
        self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints: Dict[str, CheckpointMetadata] = {}
        self._load_checkpoint_index()
    
    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get path for checkpoint file."""
        return self.config.checkpoint_dir / f"{checkpoint_id}.ckpt"
    
    def _get_index_path(self) -> Path:
        """Get path for checkpoint index."""
        return self.config.checkpoint_dir / "checkpoint_index.json"
    
    def _load_checkpoint_index(self) -> None:
        """Load checkpoint index from disk."""
        index_path = self._get_index_path()
        
        if not index_path.exists():
            return
        
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            
            for checkpoint_data in data.get("checkpoints", []):
                metadata = CheckpointMetadata(
                    checkpoint_id=checkpoint_data["checkpoint_id"],
                    operation=checkpoint_data["operation"],
                    status=CheckpointStatus(checkpoint_data["status"]),
                    created_at=checkpoint_data["created_at"],
                    records_processed=checkpoint_data["records_processed"],
                    bytes_processed=checkpoint_data["bytes_processed"],
                    progress_percent=checkpoint_data["progress_percent"],
                    resumable=checkpoint_data.get("resumable", True),
                    error_message=checkpoint_data.get("error_message"),
                )
                self.checkpoints[metadata.checkpoint_id] = metadata
        
        except (json.JSONDecodeError, KeyError):
            pass
    
    def _save_checkpoint_index(self) -> None:
        """Save checkpoint index to disk."""
        data = {
            "checkpoints": [m.to_dict() for m in self.checkpoints.values()],
            "config": self.config.to_dict(),
        }
        
        index_path = self._get_index_path()
        index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def create_checkpoint(
        self,
        checkpoint_id: str,
        state: ProcessingState,
        operation: str,
    ) -> CheckpointMetadata:
        """Create a checkpoint."""
        from time import time
        
        # Create metadata
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            operation=operation,
            status=CheckpointStatus.ACTIVE,
            created_at=datetime.utcnow().isoformat() + "Z",
            records_processed=state.records_processed,
            bytes_processed=state.bytes_processed,
            progress_percent=0.0,
            resumable=True,
        )
        
        # Save state to file
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        if self.config.compression:
            import gzip
            with gzip.open(str(checkpoint_path) + ".gz", "wb") as f:
                pickle.dump(state.to_dict(), f)
        else:
            checkpoint_path.write_bytes(pickle.dumps(state.to_dict()))
        
        # Update index
        self.checkpoints[checkpoint_id] = metadata
        self._save_checkpoint_index()
        
        # Clean up old checkpoints
        self._cleanup_old_checkpoints(operation)
        
        return metadata
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[ProcessingState]:
        """Load checkpoint state."""
        if checkpoint_id not in self.checkpoints:
            return None
        
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        # Try compressed first
        compressed_path = Path(str(checkpoint_path) + ".gz")
        
        try:
            if compressed_path.exists():
                import gzip
                with gzip.open(compressed_path, "rb") as f:
                    state_dict = pickle.load(f)
            elif checkpoint_path.exists():
                state_dict = pickle.loads(checkpoint_path.read_bytes())
            else:
                return None
            
            # Reconstruct ProcessingState
            return ProcessingState(
                operation=state_dict["operation"],
                input_path=state_dict["input_path"],
                output_path=state_dict["output_path"],
                current_position=state_dict["current_position"],
                records_processed=state_dict["records_processed"],
                bytes_processed=state_dict["bytes_processed"],
                start_time=state_dict["start_time"],
                last_checkpoint_time=state_dict["last_checkpoint_time"],
                custom_state=state_dict.get("custom_state", {}),
            )
        
        except (pickle.UnpicklingError, KeyError):
            # Mark checkpoint as corrupted
            if checkpoint_id in self.checkpoints:
                self.checkpoints[checkpoint_id].status = CheckpointStatus.CORRUPTED
                self._save_checkpoint_index()
            return None
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return False
        
        # Delete checkpoint file
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        compressed_path = Path(str(checkpoint_path) + ".gz")
        
        if compressed_path.exists():
            compressed_path.unlink()
        elif checkpoint_path.exists():
            checkpoint_path.unlink()
        
        # Update metadata
        self.checkpoints[checkpoint_id].status = CheckpointStatus.DELETED
        self._save_checkpoint_index()
        
        return True
    
    def list_checkpoints(
        self,
        operation: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
    ) -> List[CheckpointMetadata]:
        """List checkpoints with optional filtering."""
        checkpoints = list(self.checkpoints.values())
        
        if operation:
            checkpoints = [c for c in checkpoints if c.operation == operation]
        
        if status:
            checkpoints = [c for c in checkpoints if c.status == status]
        
        return sorted(checkpoints, key=lambda c: c.created_at, reverse=True)
    
    def get_latest_checkpoint(
        self,
        operation: str,
        resumable_only: bool = True,
    ) -> Optional[CheckpointMetadata]:
        """Get the most recent checkpoint for an operation."""
        checkpoints = self.list_checkpoints(operation=operation)
        
        if resumable_only:
            checkpoints = [c for c in checkpoints if c.resumable and c.status == CheckpointStatus.ACTIVE]
        
        return checkpoints[0] if checkpoints else None
    
    def mark_completed(self, checkpoint_id: str) -> None:
        """Mark checkpoint as completed."""
        if checkpoint_id in self.checkpoints:
            self.checkpoints[checkpoint_id].status = CheckpointStatus.COMPLETED
            self._save_checkpoint_index()
    
    def mark_failed(self, checkpoint_id: str, error_message: str) -> None:
        """Mark checkpoint as failed."""
        if checkpoint_id in self.checkpoints:
            self.checkpoints[checkpoint_id].status = CheckpointStatus.FAILED
            self.checkpoints[checkpoint_id].error_message = error_message
            self.checkpoints[checkpoint_id].resumable = False
            self._save_checkpoint_index()
    
    def _cleanup_old_checkpoints(self, operation: str) -> None:
        """Remove old checkpoints beyond max limit."""
        operation_checkpoints = self.list_checkpoints(operation=operation)
        
        # Keep only most recent max_checkpoints
        if len(operation_checkpoints) > self.config.max_checkpoints:
            checkpoints_to_delete = operation_checkpoints[self.config.max_checkpoints:]
            
            for checkpoint in checkpoints_to_delete:
                if checkpoint.status in [CheckpointStatus.COMPLETED, CheckpointStatus.ACTIVE]:
                    self.delete_checkpoint(checkpoint.checkpoint_id)
    
    def should_checkpoint(
        self,
        state: ProcessingState,
        last_checkpoint_time: float,
    ) -> bool:
        """Determine if a checkpoint should be created."""
        from time import time
        
        current_time = time()
        
        if self.config.strategy == CheckpointStrategy.TIME_BASED:
            return (current_time - last_checkpoint_time) >= self.config.interval_seconds
        
        elif self.config.strategy == CheckpointStrategy.RECORD_BASED:
            return state.records_processed % self.config.interval_records == 0
        
        elif self.config.strategy == CheckpointStrategy.SIZE_BASED:
            return state.bytes_processed % self.config.interval_bytes < 1024
        
        else:  # MANUAL
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get checkpoint statistics."""
        total = len(self.checkpoints)
        
        status_counts = {}
        for status in CheckpointStatus:
            count = sum(1 for c in self.checkpoints.values() if c.status == status)
            status_counts[status.value] = count
        
        operations = set(c.operation for c in self.checkpoints.values())
        
        return {
            "total_checkpoints": total,
            "status_counts": status_counts,
            "unique_operations": len(operations),
            "operations": list(operations),
            "config": self.config.to_dict(),
        }


class ResumableOperation:
    """Base class for resumable operations with checkpointing."""
    
    def __init__(
        self,
        operation_name: str,
        checkpoint_manager: CheckpointManager,
    ):
        """Initialize resumable operation."""
        self.operation_name = operation_name
        self.checkpoint_manager = checkpoint_manager
        self.state: Optional[ProcessingState] = None
        self.current_checkpoint_id: Optional[str] = None
    
    def initialize_state(
        self,
        input_path: Path,
        output_path: Path,
        custom_state: Optional[Dict[str, Any]] = None,
    ) -> ProcessingState:
        """Initialize or resume processing state."""
        # Try to resume from checkpoint
        latest = self.checkpoint_manager.get_latest_checkpoint(self.operation_name)
        
        if latest:
            self.current_checkpoint_id = latest.checkpoint_id
            state = self.checkpoint_manager.load_checkpoint(latest.checkpoint_id)
            
            if state and state.input_path == str(input_path):
                return state
        
        # Create new state
        self.current_checkpoint_id = f"{self.operation_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return ProcessingState(
            operation=self.operation_name,
            input_path=str(input_path),
            output_path=str(output_path),
            current_position=0,
            records_processed=0,
            bytes_processed=0,
            start_time=datetime.utcnow().isoformat() + "Z",
            last_checkpoint_time=datetime.utcnow().isoformat() + "Z",
            custom_state=custom_state or {},
        )
    
    def create_checkpoint(self, state: ProcessingState) -> None:
        """Create a checkpoint for current state."""
        if self.current_checkpoint_id:
            self.checkpoint_manager.create_checkpoint(
                self.current_checkpoint_id,
                state,
                self.operation_name,
            )
    
    def mark_completed(self) -> None:
        """Mark operation as completed."""
        if self.current_checkpoint_id:
            self.checkpoint_manager.mark_completed(self.current_checkpoint_id)
    
    def mark_failed(self, error_message: str) -> None:
        """Mark operation as failed."""
        if self.current_checkpoint_id:
            self.checkpoint_manager.mark_failed(self.current_checkpoint_id, error_message)


class CheckpointedStreamProcessor(ResumableOperation):
    """Stream processor with checkpointing support."""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        """Initialize checkpointed stream processor."""
        super().__init__("stream_process", checkpoint_manager)
    
    def process(
        self,
        input_path: Path,
        output_path: Path,
        transform_fn: Any,
    ) -> Dict[str, Any]:
        """Process dataset with checkpointing."""
        from time import time
        
        # Initialize or resume state
        state = self.initialize_state(input_path, output_path)
        
        last_checkpoint_time = time()
        
        try:
            # Open files
            with input_path.open("r", encoding="utf-8") as in_f:
                # Skip to last position if resuming
                for _ in range(state.current_position):
                    in_f.readline()
                
                # Open output in append mode if resuming
                mode = "a" if state.current_position > 0 else "w"
                
                with output_path.open(mode, encoding="utf-8") as out_f:
                    for line in in_f:
                        if not line.strip():
                            continue
                        
                        try:
                            record = json.loads(line)
                            transformed = transform_fn(record)
                            
                            if transformed:
                                out_f.write(json.dumps(transformed, sort_keys=True) + "\n")
                            
                            state.current_position += 1
                            state.records_processed += 1
                            state.bytes_processed += len(line.encode("utf-8"))
                            
                            # Check if should checkpoint
                            if self.checkpoint_manager.should_checkpoint(state, last_checkpoint_time):
                                self.create_checkpoint(state)
                                last_checkpoint_time = time()
                        
                        except json.JSONDecodeError:
                            continue
            
            # Mark as completed
            self.mark_completed()
            
            return {
                "status": "completed",
                "records_processed": state.records_processed,
                "bytes_processed": state.bytes_processed,
            }
        
        except Exception as e:
            # Save checkpoint on error
            self.create_checkpoint(state)
            self.mark_failed(str(e))
            raise
