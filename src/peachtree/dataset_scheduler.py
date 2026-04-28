"""Dataset scheduling for automated tasks."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ScheduleType(Enum):
    """Types of schedules."""
    
    ONCE = "once"  # Run once at specific time
    HOURLY = "hourly"  # Run every N hours
    DAILY = "daily"  # Run daily at specific time
    WEEKLY = "weekly"  # Run weekly on specific day
    MONTHLY = "monthly"  # Run monthly on specific day
    CRON = "cron"  # Cron expression


class TaskType(Enum):
    """Types of scheduled tasks."""
    
    BACKUP = "backup"
    QUALITY_CHECK = "quality_check"
    COMPLIANCE_CHECK = "compliance_check"
    SYNC = "sync"
    EXPORT = "export"
    CLEANUP = "cleanup"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Status of scheduled task execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled task configuration."""
    
    task_id: str
    task_type: TaskType
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    dataset_path: str
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    failure_count: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "schedule_type": self.schedule_type.value,
            "schedule_config": self.schedule_config,
            "dataset_path": self.dataset_path,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "params": self.params,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            schedule_type=ScheduleType(data["schedule_type"]),
            schedule_config=data["schedule_config"],
            dataset_path=data["dataset_path"],
            enabled=data.get("enabled", True),
            last_run=data.get("last_run"),
            next_run=data.get("next_run"),
            run_count=data.get("run_count", 0),
            failure_count=data.get("failure_count", 0),
            params=data.get("params", {}),
        )


@dataclass
class TaskExecution:
    """Record of a task execution."""
    
    execution_id: str
    task_id: str
    status: TaskStatus
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


class DatasetScheduler:
    """Scheduler for automated dataset tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: List[TaskExecution] = []
        self.task_handlers: Dict[TaskType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default task handlers."""
        self.task_handlers[TaskType.BACKUP] = self._handle_backup
        self.task_handlers[TaskType.QUALITY_CHECK] = self._handle_quality_check
        self.task_handlers[TaskType.COMPLIANCE_CHECK] = self._handle_compliance_check
        self.task_handlers[TaskType.SYNC] = self._handle_sync
        self.task_handlers[TaskType.EXPORT] = self._handle_export
        self.task_handlers[TaskType.CLEANUP] = self._handle_cleanup
    
    def create_task(
        self,
        task_id: str,
        task_type: TaskType,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        dataset_path: Path,
        params: Optional[Dict[str, Any]] = None,
    ) -> ScheduledTask:
        """Create a new scheduled task."""
        task = ScheduledTask(
            task_id=task_id,
            task_type=task_type,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            dataset_path=str(dataset_path),
            params=params or {},
        )
        
        # Calculate next run
        task.next_run = self._calculate_next_run(task)
        
        self.tasks[task_id] = task
        return task
    
    def enable_task(self, task_id: str) -> None:
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.tasks[task_id].next_run = self._calculate_next_run(self.tasks[task_id])
    
    def disable_task(self, task_id: str) -> None:
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.tasks[task_id].next_run = None
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get all tasks that are due to run."""
        now = datetime.utcnow().isoformat() + "Z"
        
        due_tasks = []
        for task in self.tasks.values():
            if task.enabled and task.next_run and task.next_run <= now:
                due_tasks.append(task)
        
        return due_tasks
    
    def execute_task(self, task_id: str) -> TaskExecution:
        """Execute a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        execution_id = f"exec_{task_id}_{datetime.utcnow().timestamp()}"
        
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow().isoformat() + "Z",
        )
        
        self.executions.append(execution)
        
        try:
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            
            if handler:
                result = handler(task)
                execution.result = result
                execution.status = TaskStatus.COMPLETED
                task.run_count += 1
            else:
                execution.status = TaskStatus.FAILED
                execution.error = f"No handler for task type {task.task_type}"
                task.failure_count += 1
        
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            task.failure_count += 1
        
        execution.completed_at = datetime.utcnow().isoformat() + "Z"
        task.last_run = execution.started_at
        task.next_run = self._calculate_next_run(task)
        
        return execution
    
    def run_due_tasks(self) -> List[TaskExecution]:
        """Run all due tasks."""
        due_tasks = self.get_due_tasks()
        executions = []
        
        for task in due_tasks:
            execution = self.execute_task(task.task_id)
            executions.append(execution)
        
        return executions
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[str]:
        """Calculate next run time for a task."""
        if not task.enabled:
            return None
        
        now = datetime.utcnow()
        
        if task.schedule_type == ScheduleType.ONCE:
            # Run once at specific time
            run_time = datetime.fromisoformat(task.schedule_config["run_at"].replace("Z", ""))
            if run_time > now:
                return run_time.isoformat() + "Z"
            return None  # Already ran
        
        elif task.schedule_type == ScheduleType.HOURLY:
            # Run every N hours
            hours = task.schedule_config.get("hours", 1)
            if task.last_run:
                last = datetime.fromisoformat(task.last_run.replace("Z", ""))
                next_run = last + timedelta(hours=hours)
            else:
                next_run = now + timedelta(hours=hours)
            return next_run.isoformat() + "Z"
        
        elif task.schedule_type == ScheduleType.DAILY:
            # Run daily at specific time
            hour = task.schedule_config.get("hour", 0)
            minute = task.schedule_config.get("minute", 0)
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            
            return next_run.isoformat() + "Z"
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            # Run weekly on specific day
            day_of_week = task.schedule_config.get("day_of_week", 0)  # 0 = Monday
            hour = task.schedule_config.get("hour", 0)
            minute = task.schedule_config.get("minute", 0)
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_run.isoformat() + "Z"
        
        elif task.schedule_type == ScheduleType.MONTHLY:
            # Run monthly on specific day
            day = task.schedule_config.get("day", 1)
            hour = task.schedule_config.get("hour", 0)
            minute = task.schedule_config.get("minute", 0)
            
            next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            
            return next_run.isoformat() + "Z"
        
        return None
    
    def _handle_backup(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle backup task."""
        return {
            "task_type": "backup",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def _handle_quality_check(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle quality check task."""
        return {
            "task_type": "quality_check",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def _handle_compliance_check(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle compliance check task."""
        return {
            "task_type": "compliance_check",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def _handle_sync(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle sync task."""
        return {
            "task_type": "sync",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def _handle_export(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle export task."""
        return {
            "task_type": "export",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def _handle_cleanup(self, task: ScheduledTask) -> Dict[str, Any]:
        """Handle cleanup task."""
        return {
            "task_type": "cleanup",
            "dataset_path": task.dataset_path,
            "status": "simulated_success",
        }
    
    def get_task_history(self, task_id: str, limit: int = 10) -> List[TaskExecution]:
        """Get execution history for a task."""
        history = [e for e in self.executions if e.task_id == task_id]
        history.sort(key=lambda e: e.started_at, reverse=True)
        return history[:limit]
    
    def get_task_statistics(self, task_id: str) -> Dict[str, Any]:
        """Get statistics for a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        executions = [e for e in self.executions if e.task_id == task_id]
        
        success_count = len([e for e in executions if e.status == TaskStatus.COMPLETED])
        failure_count = len([e for e in executions if e.status == TaskStatus.FAILED])
        
        return {
            "task_id": task_id,
            "total_runs": task.run_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / max(task.run_count, 1),
            "last_run": task.last_run,
            "next_run": task.next_run,
        }
    
    def save_tasks(self, output_path: Path) -> None:
        """Save all tasks to file."""
        data = {
            "tasks": [task.to_dict() for task in self.tasks.values()],
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def load_tasks(self, input_path: Path) -> None:
        """Load tasks from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        self.tasks.clear()
        for task_data in data["tasks"]:
            task = ScheduledTask.from_dict(task_data)
            self.tasks[task.task_id] = task
