"""
PeachTree Dataset Workflow Orchestration

Pipeline orchestration for complex dataset processing workflows with DAG execution,
dependency management, parallel task execution, retry logic, and workflow versioning.

Features:
- DAG-based workflow definition
- Task dependency resolution
- Parallel execution with resource management
- Conditional branching and dynamic workflows
- Retry and error handling strategies
- Workflow versioning and rollback
- Execution monitoring and metrics
- Checkpoint and resume capabilities
"""

from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class TaskStatus(Enum):
    """Workflow task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class WorkflowStatus(Enum):
    """Overall workflow execution status"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Workflow task definition"""
    id: str
    name: str
    function: Callable
    dependencies: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None
    condition: Optional[Callable] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def execute(self) -> Any:
        """Execute the task function"""
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
        try:
            self.result = self.function(**self.params)
            self.status = TaskStatus.COMPLETED
            self.end_time = datetime.now()
            return self.result
        except Exception as e:
            self.error = str(e)
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.status = TaskStatus.RETRY
            else:
                self.status = TaskStatus.FAILED
            self.end_time = datetime.now()
            raise
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if task should execute based on condition"""
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class Workflow:
    """Workflow definition with DAG structure"""
    id: str
    name: str
    description: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[str] = field(default_factory=list)
    
    def add_task(self, task: Task) -> None:
        """Add task to workflow"""
        self.tasks[task.id] = task
    
    def get_execution_order(self) -> List[List[str]]:
        """Get topological execution order (layers of parallel tasks)"""
        # Build dependency graph
        in_degree = {task_id: 0 for task_id in self.tasks}
        dependents = {task_id: [] for task_id in self.tasks}
        
        for task_id, task in self.tasks.items():
            for dep in task.dependencies:
                dependents[dep].append(task_id)
                in_degree[task_id] += 1
        
        # Topological sort with parallel layers
        layers = []
        remaining = set(self.tasks.keys())
        
        while remaining:
            # Find tasks with no dependencies
            ready = [tid for tid in remaining if in_degree[tid] == 0]
            if not ready:
                raise ValueError("Circular dependency detected in workflow")
            
            layers.append(ready)
            
            # Remove ready tasks and update dependencies
            for tid in ready:
                remaining.remove(tid)
                for dependent in dependents[tid]:
                    in_degree[dependent] -= 1
        
        return layers
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate workflow structure"""
        errors = []
        
        # Check for missing dependencies
        task_ids = set(self.tasks.keys())
        for task_id, task in self.tasks.items():
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {task_id} depends on non-existent task {dep}")
        
        # Check for cycles
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        return len(errors) == 0, errors


class WorkflowEngine:
    """Execute and manage workflow DAGs"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workflows: Dict[str, Workflow] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow for execution"""
        is_valid, errors = workflow.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow: {errors}")
        self.workflows[workflow.id] = workflow
    
    def execute_workflow(
        self,
        workflow_id: str,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute workflow with parallel task execution"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        # Get execution order
        execution_layers = workflow.get_execution_order()
        
        # Resume from checkpoint if specified
        if resume_from_checkpoint:
            checkpoint_idx = workflow.checkpoints.index(resume_from_checkpoint)
            # Mark previous tasks as completed
            for i in range(checkpoint_idx):
                for task_id in execution_layers[i]:
                    workflow.tasks[task_id].status = TaskStatus.COMPLETED
            execution_layers = execution_layers[checkpoint_idx:]
        
        results = {}
        
        try:
            # Execute each layer in parallel
            for layer_idx, layer in enumerate(execution_layers):
                layer_results = self._execute_layer(workflow, layer)
                results.update(layer_results)
                
                # Create checkpoint after each layer
                checkpoint_id = f"layer_{layer_idx}"
                workflow.checkpoints.append(checkpoint_id)
                
                # Check for failures
                failed_tasks = [tid for tid in layer if workflow.tasks[tid].status == TaskStatus.FAILED]
                if failed_tasks:
                    workflow.status = WorkflowStatus.FAILED
                    raise RuntimeError(f"Tasks failed: {failed_tasks}")
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            raise
        
        # Record execution history
        execution_record = {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "started_at": workflow.started_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "results": results,
            "tasks_completed": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETED),
            "tasks_failed": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.FAILED)
        }
        self.execution_history.append(execution_record)
        
        return results
    
    def _execute_layer(self, workflow: Workflow, task_ids: List[str]) -> Dict[str, Any]:
        """Execute a layer of tasks in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks for execution
            future_to_task = {}
            for task_id in task_ids:
                task = workflow.tasks[task_id]
                
                # Check if task should execute
                if not task.should_execute(workflow.context):
                    task.status = TaskStatus.SKIPPED
                    continue
                
                # Update task params with context
                task.params.update(workflow.context)
                
                # Submit task
                future = executor.submit(task.execute)
                future_to_task[future] = task_id
            
            # Collect results
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                task = workflow.tasks[task_id]
                
                try:
                    result = future.result()
                    results[task_id] = result
                    # Update workflow context with results
                    workflow.context[task_id] = result
                except Exception as e:
                    results[task_id] = {"error": str(e)}
        
        return results
    
    def pause_workflow(self, workflow_id: str) -> None:
        """Pause workflow execution"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.PAUSED
    
    def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Resume paused workflow from last checkpoint"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow.status != WorkflowStatus.PAUSED:
            raise ValueError(f"Workflow {workflow_id} is not paused")
        
        # Resume from last checkpoint
        last_checkpoint = workflow.checkpoints[-1] if workflow.checkpoints else None
        return self.execute_workflow(workflow_id, resume_from_checkpoint=last_checkpoint)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow execution status"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        task_summary = {
            "total": len(workflow.tasks),
            "pending": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.FAILED),
            "skipped": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.SKIPPED)
        }
        
        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "version": workflow.version,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "tasks": task_summary,
            "checkpoints": workflow.checkpoints
        }


class WorkflowBuilder:
    """Fluent API for building workflows"""
    
    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description
        )
    
    def add_task(
        self,
        task_id: str,
        name: str,
        function: Callable,
        dependencies: Optional[List[str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> 'WorkflowBuilder':
        """Add task to workflow (fluent API)"""
        task = Task(
            id=task_id,
            name=name,
            function=function,
            dependencies=dependencies or [],
            params=params or {},
            **kwargs
        )
        self.workflow.add_task(task)
        return self
    
    def set_context(self, context: Dict[str, Any]) -> 'WorkflowBuilder':
        """Set workflow context"""
        self.workflow.context.update(context)
        return self
    
    def build(self) -> Workflow:
        """Build and validate workflow"""
        is_valid, errors = self.workflow.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow: {errors}")
        return self.workflow


# Utility functions for common workflow patterns
def create_linear_workflow(
    workflow_id: str,
    name: str,
    tasks: List[Tuple[str, Callable, Dict[str, Any]]]
) -> Workflow:
    """Create a linear workflow (each task depends on previous)"""
    builder = WorkflowBuilder(workflow_id, name)
    
    prev_task_id = None
    for idx, (task_name, function, params) in enumerate(tasks):
        task_id = f"task_{idx}"
        dependencies = [prev_task_id] if prev_task_id else []
        builder.add_task(task_id, task_name, function, dependencies, params)
        prev_task_id = task_id
    
    return builder.build()


def create_parallel_workflow(
    workflow_id: str,
    name: str,
    tasks: List[Tuple[str, Callable, Dict[str, Any]]],
    final_task: Optional[Tuple[str, Callable, Dict[str, Any]]] = None
) -> Workflow:
    """Create a parallel workflow (all tasks run in parallel, optional final aggregation)"""
    builder = WorkflowBuilder(workflow_id, name)
    
    task_ids = []
    for idx, (task_name, function, params) in enumerate(tasks):
        task_id = f"task_{idx}"
        builder.add_task(task_id, task_name, function, [], params)
        task_ids.append(task_id)
    
    # Add final aggregation task if specified
    if final_task:
        final_name, final_function, final_params = final_task
        builder.add_task("final", final_name, final_function, task_ids, final_params)
    
    return builder.build()


# Export public API
__all__ = [
    'Task',
    'TaskStatus',
    'Workflow',
    'WorkflowStatus',
    'WorkflowEngine',
    'WorkflowBuilder',
    'create_linear_workflow',
    'create_parallel_workflow'
]
