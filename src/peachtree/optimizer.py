"""
PeachTree Dataset Optimization Workflows

Automated workflows for dataset optimization, quality improvement,
and continuous enhancement of training datasets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Literal

from peachtree.dedup import DatasetDeduplicator, DedupReport
from peachtree.quality import DatasetQualityScorer, DatasetQualityReport


@dataclass
class OptimizationStep:
    """Single optimization step"""
    name: str
    description: str
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class OptimizationReport:
    """Complete optimization workflow report"""
    dataset_path: str
    started_at: str
    completed_at: str | None
    steps: list[OptimizationStep]
    initial_quality: float | None = None
    final_quality: float | None = None
    initial_record_count: int | None = None
    final_record_count: int | None = None
    records_removed: int = 0
    records_improved: int = 0
    status: Literal["running", "completed", "failed"] = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "initial_quality": self.initial_quality,
            "final_quality": self.final_quality,
            "quality_improvement": (
                self.final_quality - self.initial_quality
                if self.final_quality is not None and self.initial_quality is not None
                else None
            ),
            "initial_record_count": self.initial_record_count,
            "final_record_count": self.final_record_count,
            "records_removed": self.records_removed,
            "records_improved": self.records_improved,
            "steps": [step.to_dict() for step in self.steps],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        improvement = (
            f"+{self.final_quality - self.initial_quality:.1f}"
            if self.final_quality and self.initial_quality
            else "N/A"
        )
        
        lines = [
            "# PeachTree Dataset Optimization Report",
            "",
            f"- **Dataset:** `{self.dataset_path}`",
            f"- **Started:** `{self.started_at}`",
            f"- **Completed:** `{self.completed_at or 'In Progress'}`",
            f"- **Status:** `{self.status.upper()}`",
            "",
            "## Results",
            "",
            f"- **Initial Quality:** `{self.initial_quality:.1f}/100`" if self.initial_quality else "",
            f"- **Final Quality:** `{self.final_quality:.1f}/100`" if self.final_quality else "",
            f"- **Improvement:** `{improvement} points`",
            f"- **Records (Before):** `{self.initial_record_count:,}`" if self.initial_record_count else "",
            f"- **Records (After):** `{self.final_record_count:,}`" if self.final_record_count else "",
            f"- **Records Removed:** `{self.records_removed:,}`",
            f"- **Records Improved:** `{self.records_improved:,}`",
            "",
            "## Optimization Steps",
            "",
        ]
        
        for i, step in enumerate(self.steps, 1):
            status_emoji = {
                "completed": "✅",
                "running": "⏳",
                "failed": "❌",
                "skipped": "⏭️",
                "pending": "⏸️",
            }
            emoji = status_emoji.get(step.status, "❓")
            lines.append(f"{i}. {emoji} **{step.name}** ({step.status})")
            lines.append(f"   - {step.description}")
            if step.result:
                lines.append(f"   - Result: {json.dumps(step.result, indent=6)}")
            if step.error:
                lines.append(f"   - Error: {step.error}")
            lines.append("")
        
        return "\n".join(lines)


class DatasetOptimizer:
    """Automated dataset optimization workflows"""
    
    def __init__(self, output_dir: Path | str = "data/optimized"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def optimize(
        self,
        dataset_path: str | Path,
        remove_duplicates: bool = True,
        filter_low_quality: bool = True,
        quality_threshold: int = 60,
        output_path: str | Path | None = None,
    ) -> OptimizationReport:
        """
        Run automated optimization workflow on a dataset.
        
        Steps:
        1. Baseline quality assessment
        2. Remove exact duplicates
        3. Filter low-quality records
        4. Final quality assessment
        """
        path = Path(dataset_path)
        started_at = datetime.utcnow().isoformat()
        
        if output_path is None:
            output_path = self.output_dir / f"{path.stem}_optimized.jsonl"
        else:
            output_path = Path(output_path)
        
        report = OptimizationReport(
            dataset_path=str(path),
            started_at=started_at,
            completed_at=None,
            steps=[],
        )
        
        try:
            # Step 1: Baseline quality assessment
            step1 = OptimizationStep(
                name="Baseline Quality Assessment",
                description="Measure initial dataset quality before optimization",
                status="running",
                started_at=datetime.utcnow().isoformat(),
            )
            report.steps.append(step1)
            
            scorer = DatasetQualityScorer()
            initial_quality = scorer.score_dataset(path)
            report.initial_quality = initial_quality.average_score
            report.initial_record_count = initial_quality.record_count
            
            step1.status = "completed"
            step1.completed_at = datetime.utcnow().isoformat()
            step1.result = {
                "quality_score": initial_quality.average_score,
                "record_count": initial_quality.record_count,
                "failed_records": initial_quality.failed_records,
            }
            
            current_path = path
            
            # Step 2: Remove duplicates
            if remove_duplicates:
                step2 = OptimizationStep(
                    name="Duplicate Removal",
                    description="Remove exact duplicate records based on normalized content",
                    status="running",
                    started_at=datetime.utcnow().isoformat(),
                )
                report.steps.append(step2)
                
                deduplicator = DatasetDeduplicator()
                dedup_temp = self.output_dir / f"{path.stem}_deduped.jsonl"
                dedup_result = deduplicator.deduplicate(current_path, dedup_temp)
                
                step2.status = "completed"
                step2.completed_at = datetime.utcnow().isoformat()
                step2.result = {
                    "duplicates_removed": dedup_result.duplicate_count,
                    "duplicate_ratio": dedup_result.duplicate_ratio,
                    "records_kept": dedup_result.output_count,
                }
                
                report.records_removed += dedup_result.duplicate_count
                current_path = dedup_temp
            
            # Step 3: Filter low-quality records
            if filter_low_quality:
                step3 = OptimizationStep(
                    name="Quality Filtering",
                    description=f"Remove records below quality threshold ({quality_threshold})",
                    status="running",
                    started_at=datetime.utcnow().isoformat(),
                )
                report.steps.append(step3)
                
                records = self._read_jsonl(current_path)
                filtered_records: list[dict[str, Any]] = []
                removed = 0
                
                for record in records:
                    # Score individual record
                    record_score = scorer.score_record(record, 0)
                    if record_score.score >= quality_threshold:
                        filtered_records.append(record)
                    else:
                        removed += 1
                
                # Write filtered dataset
                self._write_jsonl(output_path, filtered_records)
                
                step3.status = "completed"
                step3.completed_at = datetime.utcnow().isoformat()
                step3.result = {
                    "records_removed": removed,
                    "records_kept": len(filtered_records),
                    "removal_ratio": round(removed / len(records), 4) if records else 0.0,
                }
                
                report.records_removed += removed
                current_path = output_path
            else:
                # Just copy to output
                if current_path != output_path:
                    import shutil
                    shutil.copy(current_path, output_path)
            
            # Step 4: Final quality assessment
            step4 = OptimizationStep(
                name="Final Quality Assessment",
                description="Measure dataset quality after optimization",
                status="running",
                started_at=datetime.utcnow().isoformat(),
            )
            report.steps.append(step4)
            
            final_quality = scorer.score_dataset(output_path)
            report.final_quality = final_quality.average_score
            report.final_record_count = final_quality.record_count
            
            step4.status = "completed"
            step4.completed_at = datetime.utcnow().isoformat()
            step4.result = {
                "quality_score": final_quality.average_score,
                "record_count": final_quality.record_count,
                "failed_records": final_quality.failed_records,
            }
            
            report.status = "completed"
            report.completed_at = datetime.utcnow().isoformat()
            
        except Exception as e:
            report.status = "failed"
            report.completed_at = datetime.utcnow().isoformat()
            # Mark last step as failed
            if report.steps:
                report.steps[-1].status = "failed"
                report.steps[-1].error = str(e)
                report.steps[-1].completed_at = datetime.utcnow().isoformat()
        
        return report

    def batch_optimize(
        self,
        dataset_paths: list[str | Path],
        **optimize_kwargs: Any,
    ) -> list[OptimizationReport]:
        """Optimize multiple datasets"""
        reports: list[OptimizationReport] = []
        
        for dataset_path in dataset_paths:
            report = self.optimize(dataset_path, **optimize_kwargs)
            reports.append(report)
        
        return reports

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        """Read JSONL file"""
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        """Write JSONL file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(record, sort_keys=True) for record in records]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
