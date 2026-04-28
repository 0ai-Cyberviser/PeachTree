"""Tests for dataset scheduling functionality."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from peachtree.dataset_scheduler import (
    DatasetScheduler,
    ScheduleType,
    ScheduledTask,
    TaskExecution,
    TaskStatus,
    TaskType,
)


def test_scheduled_task_creation():
    """Test creating a scheduled task."""
    task = ScheduledTask(
        task_id="task_001",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.DAILY,
        schedule_config={"hour": 2, "minute": 0},
        dataset_path="/data/test.jsonl",
    )
    
    assert task.task_id == "task_001"
    assert task.task_type == TaskType.BACKUP
    assert task.schedule_type == ScheduleType.DAILY
    assert task.enabled is True
    assert task.run_count == 0


def test_scheduled_task_to_dict():
    """Test converting task to dictionary."""
    task = ScheduledTask(
        task_id="task_001",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 6},
        dataset_path="/data/test.jsonl",
    )
    
    task_dict = task.to_dict()
    
    assert task_dict["task_id"] == "task_001"
    assert task_dict["task_type"] == "quality_check"
    assert task_dict["schedule_type"] == "hourly"
    assert task_dict["schedule_config"] == {"hours": 6}


def test_scheduled_task_from_dict():
    """Test creating task from dictionary."""
    data = {
        "task_id": "task_002",
        "task_type": "sync",
        "schedule_type": "weekly",
        "schedule_config": {"day_of_week": 0, "hour": 9},
        "dataset_path": "/data/test.jsonl",
        "enabled": True,
        "run_count": 5,
    }
    
    task = ScheduledTask.from_dict(data)
    
    assert task.task_id == "task_002"
    assert task.task_type == TaskType.SYNC
    assert task.schedule_type == ScheduleType.WEEKLY
    assert task.run_count == 5


def test_scheduler_create_task():
    """Test creating a task with the scheduler."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="backup_daily",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.DAILY,
        schedule_config={"hour": 2, "minute": 0},
        dataset_path=Path("/data/dataset.jsonl"),
    )
    
    assert task.task_id == "backup_daily"
    assert task.task_id in scheduler.tasks
    assert task.next_run is not None


def test_scheduler_enable_disable_task():
    """Test enabling and disabling tasks."""
    scheduler = DatasetScheduler()
    
    scheduler.create_task(
        task_id="task_001",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Disable task
    scheduler.disable_task("task_001")
    assert scheduler.tasks["task_001"].enabled is False
    assert scheduler.tasks["task_001"].next_run is None
    
    # Enable task
    scheduler.enable_task("task_001")
    assert scheduler.tasks["task_001"].enabled is True
    assert scheduler.tasks["task_001"].next_run is not None


def test_scheduler_delete_task():
    """Test deleting a task."""
    scheduler = DatasetScheduler()
    
    scheduler.create_task(
        task_id="task_001",
        task_type=TaskType.CLEANUP,
        schedule_type=ScheduleType.MONTHLY,
        schedule_config={"day": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert "task_001" in scheduler.tasks
    
    deleted = scheduler.delete_task("task_001")
    assert deleted is True
    assert "task_001" not in scheduler.tasks
    
    deleted = scheduler.delete_task("nonexistent")
    assert deleted is False


def test_schedule_type_once():
    """Test once schedule calculation."""
    scheduler = DatasetScheduler()
    
    # Future run time
    run_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    
    task = scheduler.create_task(
        task_id="once_task",
        task_type=TaskType.EXPORT,
        schedule_type=ScheduleType.ONCE,
        schedule_config={"run_at": run_at},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert task.next_run is not None
    assert task.next_run == run_at


def test_schedule_type_hourly():
    """Test hourly schedule calculation."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="hourly_task",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 2},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert task.next_run is not None
    next_run_time = datetime.fromisoformat(task.next_run.replace("Z", ""))
    assert next_run_time > datetime.utcnow()


def test_schedule_type_daily():
    """Test daily schedule calculation."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="daily_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.DAILY,
        schedule_config={"hour": 3, "minute": 30},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert task.next_run is not None
    next_run_time = datetime.fromisoformat(task.next_run.replace("Z", ""))
    assert next_run_time.hour == 3
    assert next_run_time.minute == 30


def test_schedule_type_weekly():
    """Test weekly schedule calculation."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="weekly_task",
        task_type=TaskType.COMPLIANCE_CHECK,
        schedule_type=ScheduleType.WEEKLY,
        schedule_config={"day_of_week": 0, "hour": 9, "minute": 0},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert task.next_run is not None
    next_run_time = datetime.fromisoformat(task.next_run.replace("Z", ""))
    assert next_run_time.weekday() == 0  # Monday


def test_schedule_type_monthly():
    """Test monthly schedule calculation."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="monthly_task",
        task_type=TaskType.SYNC,
        schedule_type=ScheduleType.MONTHLY,
        schedule_config={"day": 1, "hour": 0, "minute": 0},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert task.next_run is not None
    next_run_time = datetime.fromisoformat(task.next_run.replace("Z", ""))
    assert next_run_time.day == 1


def test_get_due_tasks():
    """Test getting due tasks."""
    scheduler = DatasetScheduler()
    
    # Create past task (should be due)
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    task1 = scheduler.create_task(
        task_id="past_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.ONCE,
        schedule_config={"run_at": past_time},
        dataset_path=Path("/data/test.jsonl"),
    )
    task1.next_run = past_time
    
    # Create future task (not due)
    future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    task2 = scheduler.create_task(
        task_id="future_task",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.ONCE,
        schedule_config={"run_at": future_time},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    due_tasks = scheduler.get_due_tasks()
    
    assert len(due_tasks) == 1
    assert due_tasks[0].task_id == "past_task"


def test_execute_task():
    """Test executing a task."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="exec_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    execution = scheduler.execute_task("exec_task")
    
    assert execution.task_id == "exec_task"
    assert execution.status == TaskStatus.COMPLETED
    assert task.run_count == 1
    assert task.last_run is not None


def test_execute_task_failure():
    """Test task execution failure handling."""
    scheduler = DatasetScheduler()
    
    # Create custom task type without handler
    task = ScheduledTask(
        task_id="fail_task",
        task_type=TaskType.CUSTOM,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path="/data/test.jsonl",
    )
    scheduler.tasks["fail_task"] = task
    
    execution = scheduler.execute_task("fail_task")
    
    assert execution.status == TaskStatus.FAILED
    assert task.failure_count == 1


def test_run_due_tasks():
    """Test running all due tasks."""
    scheduler = DatasetScheduler()
    
    # Create multiple due tasks
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    
    for i in range(3):
        task = scheduler.create_task(
            task_id=f"task_{i}",
            task_type=TaskType.QUALITY_CHECK,
            schedule_type=ScheduleType.ONCE,
            schedule_config={"run_at": past_time},
            dataset_path=Path("/data/test.jsonl"),
        )
        task.next_run = past_time
    
    executions = scheduler.run_due_tasks()
    
    assert len(executions) == 3
    assert all(e.status == TaskStatus.COMPLETED for e in executions)


def test_task_history():
    """Test getting task execution history."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="hist_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Execute task multiple times
    for _ in range(5):
        scheduler.execute_task("hist_task")
    
    history = scheduler.get_task_history("hist_task", limit=3)
    
    assert len(history) == 3
    assert all(h.task_id == "hist_task" for h in history)


def test_task_statistics():
    """Test getting task statistics."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="stats_task",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Execute task multiple times
    for _ in range(10):
        scheduler.execute_task("stats_task")
    
    stats = scheduler.get_task_statistics("stats_task")
    
    assert stats["task_id"] == "stats_task"
    assert stats["total_runs"] == 10
    assert stats["success_count"] == 10
    assert stats["failure_count"] == 0
    assert stats["success_rate"] == 1.0


def test_save_and_load_tasks(tmp_path):
    """Test saving and loading tasks."""
    scheduler = DatasetScheduler()
    
    # Create tasks
    scheduler.create_task(
        task_id="task_001",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.DAILY,
        schedule_config={"hour": 2},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    scheduler.create_task(
        task_id="task_002",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 6},
        dataset_path=Path("/data/test2.jsonl"),
    )
    
    # Save
    output_path = tmp_path / "tasks.json"
    scheduler.save_tasks(output_path)
    
    # Load
    new_scheduler = DatasetScheduler()
    new_scheduler.load_tasks(output_path)
    
    assert len(new_scheduler.tasks) == 2
    assert "task_001" in new_scheduler.tasks
    assert "task_002" in new_scheduler.tasks
    assert new_scheduler.tasks["task_001"].task_type == TaskType.BACKUP


def test_task_execution_to_dict():
    """Test converting task execution to dictionary."""
    execution = TaskExecution(
        execution_id="exec_001",
        task_id="task_001",
        status=TaskStatus.COMPLETED,
        started_at="2026-04-27T00:00:00Z",
        completed_at="2026-04-27T00:01:00Z",
        result={"status": "success"},
    )
    
    exec_dict = execution.to_dict()
    
    assert exec_dict["execution_id"] == "exec_001"
    assert exec_dict["task_id"] == "task_001"
    assert exec_dict["status"] == "completed"
    assert exec_dict["result"]["status"] == "success"


def test_default_task_handlers():
    """Test all default task handlers execute successfully."""
    scheduler = DatasetScheduler()
    
    task_types = [
        TaskType.BACKUP,
        TaskType.QUALITY_CHECK,
        TaskType.COMPLIANCE_CHECK,
        TaskType.SYNC,
        TaskType.EXPORT,
        TaskType.CLEANUP,
    ]
    
    for task_type in task_types:
        task = scheduler.create_task(
            task_id=f"test_{task_type.value}",
            task_type=task_type,
            schedule_type=ScheduleType.ONCE,
            schedule_config={"run_at": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"},
            dataset_path=Path("/data/test.jsonl"),
        )
        
        execution = scheduler.execute_task(task.task_id)
        
        assert execution.status == TaskStatus.COMPLETED
        assert execution.result is not None
        assert execution.result["task_type"] == task_type.value


def test_task_with_params():
    """Test tasks with custom parameters."""
    scheduler = DatasetScheduler()
    
    params = {"backup_dir": "/backups", "compress": True}
    
    task = scheduler.create_task(
        task_id="param_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.DAILY,
        schedule_config={"hour": 2},
        dataset_path=Path("/data/test.jsonl"),
        params=params,
    )
    
    assert task.params == params
    assert task.params["compress"] is True


def test_multiple_schedules():
    """Test multiple tasks with different schedule types."""
    scheduler = DatasetScheduler()
    
    # Create tasks with all schedule types
    schedules = [
        (ScheduleType.HOURLY, {"hours": 1}),
        (ScheduleType.DAILY, {"hour": 2, "minute": 0}),
        (ScheduleType.WEEKLY, {"day_of_week": 0, "hour": 9}),
        (ScheduleType.MONTHLY, {"day": 1, "hour": 0}),
    ]
    
    for i, (schedule_type, config) in enumerate(schedules):
        task = scheduler.create_task(
            task_id=f"task_{i}",
            task_type=TaskType.BACKUP,
            schedule_type=schedule_type,
            schedule_config=config,
            dataset_path=Path("/data/test.jsonl"),
        )
        
        assert task.next_run is not None
        assert task.schedule_type == schedule_type


def test_disabled_task_not_in_due():
    """Test that disabled tasks are not returned as due."""
    scheduler = DatasetScheduler()
    
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    
    task = scheduler.create_task(
        task_id="disabled_task",
        task_type=TaskType.BACKUP,
        schedule_type=ScheduleType.ONCE,
        schedule_config={"run_at": past_time},
        dataset_path=Path("/data/test.jsonl"),
    )
    task.next_run = past_time
    
    # Disable task
    scheduler.disable_task("disabled_task")
    
    due_tasks = scheduler.get_due_tasks()
    
    assert len(due_tasks) == 0


def test_next_run_updates_after_execution():
    """Test that next_run is updated after task execution."""
    scheduler = DatasetScheduler()
    
    task = scheduler.create_task(
        task_id="update_task",
        task_type=TaskType.QUALITY_CHECK,
        schedule_type=ScheduleType.HOURLY,
        schedule_config={"hours": 1},
        dataset_path=Path("/data/test.jsonl"),
    )
    
    original_next_run = task.next_run
    
    scheduler.execute_task("update_task")
    
    assert task.next_run is not None
    assert task.next_run != original_next_run
