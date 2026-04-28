"""
PeachTree Automated Workflow Engine

Chain multiple PeachTree operations together with dependencies, error handling,
and automated execution. Enables complex dataset processing pipelines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal
import json

from peachtree.builder import DatasetBuilder
from peachtree.quality import DatasetQualityScorer
from peachtree.dedup import DatasetDeduplicator
from peachtree.optimizer import DatasetOptimizer
from peachtree.health_monitor import DatasetHealthMonitor
from peachtree.exporters import ModelExporter


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    name: str
    operation: Literal["build", "quality", "dedup", "optimize", "health", "export", "custom"]
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    skip_on_failure: bool = False
    retry_count: int = 0
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    start_time: str | None = None
    end_time: str | None = None
    error_message: str | None = None
    result: Any = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "operation": self.operation,
            "params": self.params,
            "depends_on": self.depends_on,
            "skip_on_failure": self.skip_on_failure,
            "retry_count": self.retry_count,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error_message,
        }


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    global_params: dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "global_params": self.global_params,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        """Load workflow from dictionary"""
        workflow = cls(
            name=data["name"],
            description=data["description"],
            global_params=data.get("global_params", {}),
        )
        
        for step_data in data.get("steps", []):
            step = WorkflowStep(
                name=step_data["name"],
                operation=step_data["operation"],
                params=step_data.get("params", {}),
                depends_on=step_data.get("depends_on", []),
                skip_on_failure=step_data.get("skip_on_failure", False),
                retry_count=step_data.get("retry_count", 0),
            )
            workflow.add_step(step)
        
        return workflow
    
    @classmethod
    def from_json(cls, json_str: str) -> WorkflowDefinition:
        """Load workflow from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    workflow_name: str
    start_time: str
    end_time: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    success: bool
    error_message: str | None = None
    step_results: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "success": self.success,
            "error_message": self.error_message,
            "step_results": self.step_results,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate a summary in markdown"""
        lines = [
            f"# Workflow Execution: {self.workflow_name}",
            "",
            f"**Status:** {'✅ SUCCESS' if self.success else '❌ FAILED'}",
            f"**Started:** {self.start_time}",
            f"**Ended:** {self.end_time}",
            "",
            "## Step Summary",
            "",
            f"- Total: {self.total_steps}",
            f"- ✅ Completed: {self.completed_steps}",
            f"- ❌ Failed: {self.failed_steps}",
            f"- ⏭️  Skipped: {self.skipped_steps}",
            "",
        ]
        
        if self.error_message:
            lines.extend([
                "## Error",
                "",
                f"```\n{self.error_message}\n```",
                "",
            ])
        
        if self.step_results:
            lines.extend([
                "## Step Results",
                "",
            ])
            for step_name, result in self.step_results.items():
                lines.append(f"### {step_name}")
                lines.append("")
                if isinstance(result, dict):
                    for key, value in result.items():
                        lines.append(f"- **{key}:** {value}")
                else:
                    lines.append(f"- Result: {result}")
                lines.append("")
        
        return "\n".join(lines)


class WorkflowEngine:
    """Execute automated dataset processing workflows"""
    
    def __init__(self):
        """Initialize workflow engine with operation handlers"""
        self.builder = DatasetBuilder()
        self.quality_scorer = DatasetQualityScorer()
        self.deduplicator = DatasetDeduplicator()
        self.optimizer = DatasetOptimizer()
        self.health_monitor = DatasetHealthMonitor()
        self.exporter = ModelExporter()
    
    def _execute_build(self, params: dict[str, Any]) -> Any:
        """Execute dataset build operation"""
        # Simplified build - would call builder methods
        return {"operation": "build", "status": "completed"}
    
    def _execute_quality(self, params: dict[str, Any]) -> Any:
        """Execute quality scoring operation"""
        dataset_path = Path(params["dataset_path"])
        report = self.quality_scorer.score_dataset(dataset_path)
        return {
            "score": report.overall_score,
            "passed": report.passed,
            "total_records": report.total_records,
        }
    
    def _execute_dedup(self, params: dict[str, Any]) -> Any:
        """Execute deduplication operation"""
        dataset_path = Path(params["dataset_path"])
        output_path = Path(params.get("output_path", dataset_path.with_suffix(".dedup.jsonl")))
        
        report = self.deduplicator.deduplicate(
            dataset_path=dataset_path,
            output_path=output_path,
            similarity_threshold=params.get("similarity_threshold", 0.95),
        )
        
        return {
            "duplicates_removed": report.duplicates_removed,
            "unique_kept": report.unique_kept,
            "output_path": str(output_path),
        }
    
    def _execute_optimize(self, params: dict[str, Any]) -> Any:
        """Execute optimization operation"""
        dataset_path = Path(params["dataset_path"])
        output_path = Path(params.get("output_path", dataset_path.with_suffix(".optimized.jsonl")))
        
        report = self.optimizer.optimize(
            dataset_path=dataset_path,
            output_path=output_path,
            quality_threshold=params.get("quality_threshold", 70.0),
        )
        
        return {
            "steps_completed": len(report.steps_completed),
            "quality_improvement": report.quality_after - report.quality_before,
            "output_path": str(output_path),
        }
    
    def _execute_health(self, params: dict[str, Any]) -> Any:
        """Execute health check operation"""
        dataset_path = Path(params["dataset_path"])
        snapshot = self.health_monitor.capture_snapshot(dataset_path)
        
        return {
            "status": snapshot.status.value,
            "record_count": snapshot.record_count,
            "quality_score": snapshot.quality_score,
            "issues_found": len(snapshot.issues),
        }
    
    def _execute_export(self, params: dict[str, Any]) -> Any:
        """Execute export operation"""
        dataset_path = Path(params["dataset_path"])
        output_path = Path(params["output_path"])
        format_name = params.get("format", "chatml")
        
        self.exporter.export_dataset(
            source_dataset=dataset_path,
            output_path=output_path,
            format_name=format_name,
        )
        
        return {
            "format": format_name,
            "output_path": str(output_path),
        }
    
    def _can_execute_step(
        self,
        step: WorkflowStep,
        completed_steps: set[str],
    ) -> bool:
        """Check if a step's dependencies are satisfied"""
        return all(dep in completed_steps for dep in step.depends_on)
    
    def _execute_step(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> Any:
        """Execute a single workflow step"""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now().isoformat()
        
        try:
            # Merge context into params
            params = {**context, **step.params}
            
            # Execute based on operation type
            if step.operation == "build":
                result = self._execute_build(params)
            elif step.operation == "quality":
                result = self._execute_quality(params)
            elif step.operation == "dedup":
                result = self._execute_dedup(params)
            elif step.operation == "optimize":
                result = self._execute_optimize(params)
            elif step.operation == "health":
                result = self._execute_health(params)
            elif step.operation == "export":
                result = self._execute_export(params)
            elif step.operation == "custom":
                # Custom operations would call user-provided functions
                result = {"operation": "custom", "status": "completed"}
            else:
                raise ValueError(f"Unknown operation: {step.operation}")
            
            step.status = StepStatus.COMPLETED
            step.result = result
            step.end_time = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.end_time = datetime.now().isoformat()
            raise
    
    def execute(
        self,
        workflow: WorkflowDefinition,
        context: dict[str, Any] | None = None,
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow
        
        Args:
            workflow: Workflow definition to execute
            context: Optional context dictionary with global parameters
        
        Returns:
            WorkflowExecutionResult with execution details
        """
        start_time = datetime.now().isoformat()
        context = context or workflow.global_params
        
        completed_steps: set[str] = set()
        failed_steps: set[str] = set()
        skipped_steps: set[str] = set()
        step_results: dict[str, Any] = {}
        
        # Execute steps in dependency order
        remaining_steps = list(workflow.steps)
        max_iterations = len(remaining_steps) * 2  # Prevent infinite loop
        iteration = 0
        
        while remaining_steps and iteration < max_iterations:
            iteration += 1
            executed_this_iteration = False
            
            for step in list(remaining_steps):
                # Check if dependencies are satisfied
                if not self._can_execute_step(step, completed_steps):
                    continue
                
                # Check if should skip due to failed dependency
                failed_deps = [dep for dep in step.depends_on if dep in failed_steps]
                if failed_deps and step.skip_on_failure:
                    step.status = StepStatus.SKIPPED
                    skipped_steps.add(step.name)
                    remaining_steps.remove(step)
                    executed_this_iteration = True
                    continue
                
                # Execute step
                try:
                    result = self._execute_step(step, context)
                    completed_steps.add(step.name)
                    step_results[step.name] = result
                    
                    # Update context with result for next steps
                    if isinstance(result, dict):
                        context.update(result)
                    
                except Exception as e:
                    failed_steps.add(step.name)
                    step_results[step.name] = {"error": str(e)}
                    
                    if not step.skip_on_failure:
                        # Workflow fails on critical step failure
                        end_time = datetime.now().isoformat()
                        return WorkflowExecutionResult(
                            workflow_name=workflow.name,
                            start_time=start_time,
                            end_time=end_time,
                            total_steps=len(workflow.steps),
                            completed_steps=len(completed_steps),
                            failed_steps=len(failed_steps),
                            skipped_steps=len(skipped_steps),
                            success=False,
                            error_message=f"Step '{step.name}' failed: {str(e)}",
                            step_results=step_results,
                        )
                
                remaining_steps.remove(step)
                executed_this_iteration = True
            
            if not executed_this_iteration:
                # No progress made - circular dependency or unsatisfied deps
                break
        
        end_time = datetime.now().isoformat()
        success = len(failed_steps) == 0 and len(remaining_steps) == 0
        
        return WorkflowExecutionResult(
            workflow_name=workflow.name,
            start_time=start_time,
            end_time=end_time,
            total_steps=len(workflow.steps),
            completed_steps=len(completed_steps),
            failed_steps=len(failed_steps),
            skipped_steps=len(skipped_steps),
            success=success,
            error_message=None if success else f"{len(remaining_steps)} steps could not execute",
            step_results=step_results,
        )
    
    def save_workflow(
        self,
        workflow: WorkflowDefinition,
        output_path: Path | str,
    ) -> None:
        """Save workflow definition to file"""
        Path(output_path).write_text(workflow.to_json())
    
    def load_workflow(
        self,
        workflow_path: Path | str,
    ) -> WorkflowDefinition:
        """Load workflow definition from file"""
        json_str = Path(workflow_path).read_text()
        return WorkflowDefinition.from_json(json_str)


def create_standard_pipeline() -> WorkflowDefinition:
    """Create standard dataset processing pipeline workflow"""
    workflow = WorkflowDefinition(
        name="standard-pipeline",
        description="Standard dataset processing: health check → dedup → optimize → export",
    )
    
    workflow.add_step(WorkflowStep(
        name="health-check",
        operation="health",
        params={"dataset_path": "data/raw/dataset.jsonl"},
    ))
    
    workflow.add_step(WorkflowStep(
        name="deduplicate",
        operation="dedup",
        params={
            "dataset_path": "data/raw/dataset.jsonl",
            "output_path": "data/processed/dataset-dedup.jsonl",
            "similarity_threshold": 0.95,
        },
        depends_on=["health-check"],
    ))
    
    workflow.add_step(WorkflowStep(
        name="optimize",
        operation="optimize",
        params={
            "dataset_path": "data/processed/dataset-dedup.jsonl",
            "output_path": "data/processed/dataset-optimized.jsonl",
            "quality_threshold": 75.0,
        },
        depends_on=["deduplicate"],
    ))
    
    workflow.add_step(WorkflowStep(
        name="export",
        operation="export",
        params={
            "dataset_path": "data/processed/dataset-optimized.jsonl",
            "output_path": "data/exports/dataset.chatml.jsonl",
            "format": "chatml",
        },
        depends_on=["optimize"],
    ))
    
    return workflow
