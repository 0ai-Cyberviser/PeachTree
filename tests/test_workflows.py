"""
Tests for workflows module
"""
from pathlib import Path
import pytest
import json
from peachtree.workflows import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    StepStatus,
    create_standard_pipeline,
)


@pytest.fixture
def temp_dataset(tmp_path):
    """Create a temporary dataset"""
    dataset_file = tmp_path / "data" / "raw" / "test.jsonl"
    dataset_file.parent.mkdir(parents=True, exist_ok=True)
    
    records = []
    for i in range(10):
        record = {
            "id": f"rec-{i}",
            "content": f"High quality test content with sufficient length {i}",
            "source_repo": "test-repo",
            "source_path": f"test{i}.txt",
            "digest": f"sha256-{i}",
        }
        records.append(json.dumps(record))
    dataset_file.write_text("\n".join(records) + "\n")
    return dataset_file


@pytest.fixture
def workflow_engine():
    """Create a workflow engine"""
    return WorkflowEngine()


def test_workflow_step_creation():
    """Test WorkflowStep creation"""
    step = WorkflowStep(
        name="test-step",
        operation="quality",
        params={"dataset_path": "data/test.jsonl"},
        depends_on=["previous-step"],
        skip_on_failure=True,
    )
    
    assert step.name == "test-step"
    assert step.operation == "quality"
    assert step.status == StepStatus.PENDING
    assert len(step.depends_on) == 1


def test_workflow_definition_creation():
    """Test WorkflowDefinition creation"""
    workflow = WorkflowDefinition(
        name="test-workflow",
        description="Test workflow description",
    )
    
    step1 = WorkflowStep("step1", "health", {})
    step2 = WorkflowStep("step2", "dedup", {}, depends_on=["step1"])
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    
    assert len(workflow.steps) == 2
    assert workflow.steps[0].name == "step1"
    assert workflow.steps[1].depends_on == ["step1"]


def test_workflow_to_json():
    """Test workflow serialization to JSON"""
    workflow = WorkflowDefinition("test", "Test workflow")
    workflow.add_step(WorkflowStep("step1", "quality", {"dataset_path": "test.jsonl"}))
    
    json_str = workflow.to_json()
    data = json.loads(json_str)
    
    assert data["name"] == "test"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["name"] == "step1"


def test_workflow_from_json():
    """Test loading workflow from JSON"""
    json_data = {
        "name": "loaded-workflow",
        "description": "Loaded from JSON",
        "steps": [
            {
                "name": "health-check",
                "operation": "health",
                "params": {"dataset_path": "data/test.jsonl"},
                "depends_on": [],
            }
        ],
    }
    
    workflow = WorkflowDefinition.from_dict(json_data)
    
    assert workflow.name == "loaded-workflow"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].name == "health-check"


def test_simple_workflow_execution(workflow_engine, temp_dataset):
    """Test executing a simple workflow"""
    workflow = WorkflowDefinition("simple", "Simple test workflow")
    
    workflow.add_step(WorkflowStep(
        "health",
        "health",
        {"dataset_path": str(temp_dataset)},
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert result.completed_steps == 1
    assert result.failed_steps == 0
    assert "health" in result.step_results


def test_multi_step_workflow(workflow_engine, temp_dataset, tmp_path):
    """Test workflow with multiple steps"""
    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    
    workflow = WorkflowDefinition("multi-step", "Multi-step workflow")
    
    workflow.add_step(WorkflowStep(
        "health",
        "health",
        {"dataset_path": str(temp_dataset)},
    ))
    
    workflow.add_step(WorkflowStep(
        "quality",
        "quality",
        {"dataset_path": str(temp_dataset)},
        depends_on=["health"],
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert result.completed_steps == 2
    assert "health" in result.step_results
    assert "quality" in result.step_results


def test_workflow_with_dependencies(workflow_engine, temp_dataset):
    """Test workflow respects step dependencies"""
    workflow = WorkflowDefinition("dependencies", "Test dependencies")
    
    workflow.add_step(WorkflowStep("step1", "health", {"dataset_path": str(temp_dataset)}))
    workflow.add_step(WorkflowStep("step2", "quality", {"dataset_path": str(temp_dataset)}, depends_on=["step1"]))
    workflow.add_step(WorkflowStep("step3", "health", {"dataset_path": str(temp_dataset)}, depends_on=["step2"]))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert result.completed_steps == 3
    
    # Verify execution order by checking step statuses
    for step in workflow.steps:
        assert step.status == StepStatus.COMPLETED


def test_workflow_failure_handling(workflow_engine):
    """Test workflow handles step failures"""
    workflow = WorkflowDefinition("failure-test", "Test failure handling")
    
    # Step with invalid dataset path should fail
    workflow.add_step(WorkflowStep(
        "bad-step",
        "health",
        {"dataset_path": "/nonexistent/dataset.jsonl"},
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is False
    assert result.failed_steps == 1


def test_skip_on_failure(workflow_engine):
    """Test skip_on_failure behavior"""
    workflow = WorkflowDefinition("skip-test", "Test skip on failure")
    
    workflow.add_step(WorkflowStep(
        "fail-step",
        "health",
        {"dataset_path": "/nonexistent/dataset.jsonl"},
    ))
    
    workflow.add_step(WorkflowStep(
        "skip-step",
        "health",
        {"dataset_path": "/another/nonexistent.jsonl"},
        depends_on=["fail-step"],
        skip_on_failure=True,
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.failed_steps == 1
    assert result.skipped_steps == 1


def test_dedup_operation(workflow_engine, temp_dataset, tmp_path):
    """Test deduplication workflow operation"""
    output_file = tmp_path / "deduped.jsonl"
    
    workflow = WorkflowDefinition("dedup-test", "Test deduplication")
    workflow.add_step(WorkflowStep(
        "dedup",
        "dedup",
        {
            "dataset_path": str(temp_dataset),
            "output_path": str(output_file),
            "similarity_threshold": 0.95,
        },
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert "dedup" in result.step_results
    assert output_file.exists()


def test_optimize_operation(workflow_engine, temp_dataset, tmp_path):
    """Test optimization workflow operation"""
    output_file = tmp_path / "optimized.jsonl"
    
    workflow = WorkflowDefinition("optimize-test", "Test optimization")
    workflow.add_step(WorkflowStep(
        "optimize",
        "optimize",
        {
            "dataset_path": str(temp_dataset),
            "output_path": str(output_file),
            "quality_threshold": 50.0,
        },
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert "optimize" in result.step_results
    assert output_file.exists()


def test_export_operation(workflow_engine, temp_dataset, tmp_path):
    """Test export workflow operation"""
    output_file = tmp_path / "export.jsonl"
    
    workflow = WorkflowDefinition("export-test", "Test export")
    workflow.add_step(WorkflowStep(
        "export",
        "export",
        {
            "dataset_path": str(temp_dataset),
            "output_path": str(output_file),
            "format": "chatml",
        },
    ))
    
    result = workflow_engine.execute(workflow)
    
    assert result.success is True
    assert "export" in result.step_results


def test_save_and_load_workflow(workflow_engine, tmp_path):
    """Test saving and loading workflows"""
    workflow = WorkflowDefinition("save-test", "Test save/load")
    workflow.add_step(WorkflowStep("step1", "health", {"dataset_path": "test.jsonl"}))
    
    workflow_file = tmp_path / "workflow.json"
    workflow_engine.save_workflow(workflow, workflow_file)
    
    assert workflow_file.exists()
    
    loaded_workflow = workflow_engine.load_workflow(workflow_file)
    
    assert loaded_workflow.name == "save-test"
    assert len(loaded_workflow.steps) == 1


def test_create_standard_pipeline():
    """Test creating standard pipeline workflow"""
    workflow = create_standard_pipeline()
    
    assert workflow.name == "standard-pipeline"
    assert len(workflow.steps) == 4  # health, dedup, optimize, export
    
    step_names = [step.name for step in workflow.steps]
    assert "health-check" in step_names
    assert "deduplicate" in step_names
    assert "optimize" in step_names
    assert "export" in step_names


def test_workflow_execution_result():
    """Test WorkflowExecutionResult fields"""
    from peachtree.workflows import WorkflowExecutionResult
    
    result = WorkflowExecutionResult(
        workflow_name="test",
        start_time="2026-04-27T10:00:00",
        end_time="2026-04-27T10:05:00",
        total_steps=5,
        completed_steps=3,
        failed_steps=1,
        skipped_steps=1,
        success=False,
        error_message="Step X failed",
    )
    
    assert result.workflow_name == "test"
    assert result.total_steps == 5
    assert result.success is False


def test_execution_result_to_summary():
    """Test execution result summary generation"""
    from peachtree.workflows import WorkflowExecutionResult
    
    result = WorkflowExecutionResult(
        workflow_name="summary-test",
        start_time="2026-04-27T10:00:00",
        end_time="2026-04-27T10:05:00",
        total_steps=3,
        completed_steps=3,
        failed_steps=0,
        skipped_steps=0,
        success=True,
    )
    
    summary = result.to_summary()
    
    assert "# Workflow Execution" in summary
    assert "summary-test" in summary
    assert "✅ SUCCESS" in summary


def test_global_params_in_workflow():
    """Test global parameters in workflow"""
    workflow = WorkflowDefinition(
        "global-params-test",
        "Test global params",
        global_params={"quality_threshold": 75.0},
    )
    
    workflow.add_step(WorkflowStep("step1", "quality", {}))
    
    assert workflow.global_params["quality_threshold"] == 75.0


def test_step_status_progression(workflow_engine, temp_dataset):
    """Test that step status progresses correctly"""
    workflow = WorkflowDefinition("status-test", "Test status progression")
    
    step = WorkflowStep("health", "health", {"dataset_path": str(temp_dataset)})
    workflow.add_step(step)
    
    # Initially pending
    assert step.status == StepStatus.PENDING
    
    workflow_engine.execute(workflow)
    
    # After execution should be completed
    assert step.status == StepStatus.COMPLETED
    assert step.start_time is not None
    assert step.end_time is not None
