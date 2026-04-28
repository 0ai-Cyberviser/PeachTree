"""
Tests for dataset_workflow module - Pipeline orchestration
"""

import pytest
from datetime import datetime
from peachtree.dataset_workflow import (
    Task, TaskStatus, Workflow, WorkflowStatus, WorkflowEngine,
    WorkflowBuilder, create_linear_workflow, create_parallel_workflow
)


def dummy_task_func(**kwargs):
    """Dummy task function for testing"""
    return "completed"


def add_task(x, y):
    """Simple addition task"""
    return x + y


def failing_task():
    """Task that always fails"""
    raise ValueError("Task failed")


class TestTask:
    def test_task_creation(self):
        task = Task(
            id="task1",
            name="Test Task",
            function=dummy_task_func,
            params={"param1": "value1"}
        )
        assert task.id == "task1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.result is None
    
    def test_task_execution_success(self):
        task = Task(
            id="task1",
            name="Add Task",
            function=add_task,
            params={"x": 5, "y": 3}
        )
        result = task.execute()
        assert result == 8
        assert task.status == TaskStatus.COMPLETED
        assert task.start_time is not None
        assert task.end_time is not None
    
    def test_task_execution_failure(self):
        task = Task(
            id="fail_task",
            name="Failing Task",
            function=failing_task,
            max_retries=2
        )
        
        with pytest.raises(ValueError):
            task.execute()
        
        assert task.status == TaskStatus.RETRY
        assert task.retry_count == 1
    
    def test_task_max_retries_exceeded(self):
        task = Task(
            id="fail_task",
            name="Failing Task",
            function=failing_task,
            max_retries=0
        )
        
        with pytest.raises(ValueError):
            task.execute()
        
        assert task.status == TaskStatus.FAILED
        assert task.error is not None
    
    def test_task_conditional_execution(self):
        task = Task(
            id="cond_task",
            name="Conditional Task",
            function=dummy_task_func,
            condition=lambda ctx: ctx.get("execute", False)
        )
        
        assert not task.should_execute({})
        assert task.should_execute({"execute": True})


class TestWorkflow:
    def test_workflow_creation(self):
        workflow = Workflow(
            id="wf1",
            name="Test Workflow",
            description="Test workflow"
        )
        assert workflow.id == "wf1"
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.DRAFT
        assert len(workflow.tasks) == 0
    
    def test_workflow_add_task(self):
        workflow = Workflow(id="wf1", name="Test", description="")
        task = Task(id="t1", name="Task 1", function=dummy_task_func)
        workflow.add_task(task)
        assert "t1" in workflow.tasks
        assert workflow.tasks["t1"] == task
    
    def test_workflow_execution_order_linear(self):
        workflow = Workflow(id="wf1", name="Linear", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func, dependencies=[]))
        workflow.add_task(Task(id="t2", name="Task 2", function=dummy_task_func, dependencies=["t1"]))
        workflow.add_task(Task(id="t3", name="Task 3", function=dummy_task_func, dependencies=["t2"]))
        
        layers = workflow.get_execution_order()
        assert len(layers) == 3
        assert layers[0] == ["t1"]
        assert layers[1] == ["t2"]
        assert layers[2] == ["t3"]
    
    def test_workflow_execution_order_parallel(self):
        workflow = Workflow(id="wf1", name="Parallel", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func, dependencies=[]))
        workflow.add_task(Task(id="t2", name="Task 2", function=dummy_task_func, dependencies=[]))
        workflow.add_task(Task(id="t3", name="Task 3", function=dummy_task_func, dependencies=["t1", "t2"]))
        
        layers = workflow.get_execution_order()
        assert len(layers) == 2
        assert set(layers[0]) == {"t1", "t2"}
        assert layers[1] == ["t3"]
    
    def test_workflow_validation_missing_dependency(self):
        workflow = Workflow(id="wf1", name="Invalid", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func, dependencies=["t_missing"]))
        
        is_valid, errors = workflow.validate()
        assert not is_valid
        assert len(errors) > 0
        assert "non-existent" in errors[0]
    
    def test_workflow_validation_circular_dependency(self):
        workflow = Workflow(id="wf1", name="Circular", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func, dependencies=["t2"]))
        workflow.add_task(Task(id="t2", name="Task 2", function=dummy_task_func, dependencies=["t1"]))
        
        is_valid, errors = workflow.validate()
        assert not is_valid
        assert "Circular dependency" in errors[0]


class TestWorkflowEngine:
    def test_engine_creation(self):
        engine = WorkflowEngine(max_workers=4)
        assert engine.max_workers == 4
        assert len(engine.workflows) == 0
    
    def test_register_workflow(self):
        engine = WorkflowEngine()
        workflow = Workflow(id="wf1", name="Test", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func))
        
        engine.register_workflow(workflow)
        assert "wf1" in engine.workflows
    
    def test_register_invalid_workflow(self):
        engine = WorkflowEngine()
        workflow = Workflow(id="wf1", name="Invalid", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func, dependencies=["missing"]))
        
        with pytest.raises(ValueError):
            engine.register_workflow(workflow)
    
    def test_execute_linear_workflow(self):
        engine = WorkflowEngine()
        
        def task1():
            return "result1"
        
        def task2(task_1):
            return f"{task_1}_result2"
        
        workflow = Workflow(id="wf1", name="Linear", description="")
        workflow.add_task(Task(id="task_1", name="Task 1", function=task1))
        workflow.add_task(Task(id="task_2", name="Task 2", function=task2, dependencies=["task_1"]))
        
        engine.register_workflow(workflow)
        results = engine.execute_workflow("wf1")
        
        assert results["task_1"] == "result1"
        assert results["task_2"] == "result1_result2"
        assert workflow.status == WorkflowStatus.COMPLETED
    
    def test_execute_parallel_workflow(self):
        engine = WorkflowEngine(max_workers=2)
        
        workflow = Workflow(id="wf1", name="Parallel", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=lambda: "r1"))
        workflow.add_task(Task(id="t2", name="Task 2", function=lambda: "r2"))
        
        engine.register_workflow(workflow)
        results = engine.execute_workflow("wf1")
        
        assert results["t1"] == "r1"
        assert results["t2"] == "r2"
        assert workflow.status == WorkflowStatus.COMPLETED
    
    def test_workflow_with_failure(self):
        engine = WorkflowEngine()
        
        workflow = Workflow(id="wf1", name="Failing", description="")
        workflow.add_task(Task(id="t1", name="Failing Task", function=failing_task, max_retries=0))
        
        engine.register_workflow(workflow)
        
        with pytest.raises(RuntimeError):
            engine.execute_workflow("wf1")
        
        assert workflow.status == WorkflowStatus.FAILED
    
    def test_workflow_status(self):
        engine = WorkflowEngine()
        
        workflow = Workflow(id="wf1", name="Test", description="")
        workflow.add_task(Task(id="t1", name="Task 1", function=dummy_task_func))
        
        engine.register_workflow(workflow)
        engine.execute_workflow("wf1")
        
        status = engine.get_workflow_status("wf1")
        assert status["workflow_id"] == "wf1"
        assert status["status"] == WorkflowStatus.COMPLETED.value
        assert status["tasks"]["completed"] == 1


class TestWorkflowBuilder:
    def test_builder_basic(self):
        builder = WorkflowBuilder("wf1", "Test Workflow")
        builder.add_task("t1", "Task 1", dummy_task_func)
        workflow = builder.build()
        
        assert workflow.id == "wf1"
        assert workflow.name == "Test Workflow"
        assert "t1" in workflow.tasks
    
    def test_builder_with_dependencies(self):
        builder = WorkflowBuilder("wf1", "Test")
        builder.add_task("t1", "Task 1", dummy_task_func)
        builder.add_task("t2", "Task 2", dummy_task_func, dependencies=["t1"])
        workflow = builder.build()
        
        assert workflow.tasks["t2"].dependencies == ["t1"]
    
    def test_builder_with_context(self):
        builder = WorkflowBuilder("wf1", "Test")
        builder.set_context({"key": "value"})
        workflow = builder.build()
        
        assert workflow.context["key"] == "value"


class TestUtilityFunctions:
    def test_create_linear_workflow(self):
        tasks = [
            ("Task 1", lambda: "r1", {}),
            ("Task 2", lambda task_0: f"{task_0}_r2", {}),
            ("Task 3", lambda task_1: f"{task_1}_r3", {})
        ]
        
        workflow = create_linear_workflow("wf1", "Linear", tasks)
        layers = workflow.get_execution_order()
        
        assert len(layers) == 3
        assert layers[0] == ["task_0"]
        assert layers[1] == ["task_1"]
        assert layers[2] == ["task_2"]
    
    def test_create_parallel_workflow(self):
        tasks = [
            ("Task 1", lambda: "r1", {}),
            ("Task 2", lambda: "r2", {}),
            ("Task 3", lambda: "r3", {})
        ]
        
        workflow = create_parallel_workflow("wf1", "Parallel", tasks)
        layers = workflow.get_execution_order()
        
        assert len(layers) == 1
        assert len(layers[0]) == 3
    
    def test_create_parallel_workflow_with_final_task(self):
        tasks = [
            ("Task 1", lambda: "r1", {}),
            ("Task 2", lambda: "r2", {})
        ]
        final_task = ("Final", lambda task_0, task_1: f"{task_0}_{task_1}", {})
        
        workflow = create_parallel_workflow("wf1", "Parallel with final", tasks, final_task)
        layers = workflow.get_execution_order()
        
        assert len(layers) == 2
        assert len(layers[0]) == 2
        assert layers[1] == ["final"]
