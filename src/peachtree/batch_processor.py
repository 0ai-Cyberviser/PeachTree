"""
PeachTree Batch Processing

Batch operations for processing multiple datasets efficiently.
Enables directory-level health monitoring, optimization, and quality scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Literal

from peachtree.health_monitor import DatasetHealthMonitor
from peachtree.optimizer import DatasetOptimizer
from peachtree.quality import DatasetQualityScorer


@dataclass(frozen=True)
class BatchResult:
    """Result of a batch operation on a single dataset"""
    dataset_path: str
    status: Literal["success", "failed", "skipped"]
    error: str | None
    result: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "status": self.status,
            "error": self.error,
            "result": self.result,
        }


@dataclass(frozen=True)
class BatchOperationReport:
    """Summary report of batch operation across multiple datasets"""
    operation: str
    started_at: str
    completed_at: str
    total_datasets: int
    successful: int
    failed: int
    skipped: int
    results: tuple[BatchResult, ...]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "summary": {
                "total_datasets": self.total_datasets,
                "successful": self.successful,
                "failed": self.failed,
                "skipped": self.skipped,
            },
            "results": [r.to_dict() for r in self.results],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
    
    def to_markdown(self) -> str:
        lines = [
            f"# Batch {self.operation.title()} Report",
            "",
            "## Summary",
            "",
            f"- **Started:** {self.started_at}",
            f"- **Completed:** {self.completed_at}",
            f"- **Total Datasets:** {self.total_datasets}",
            f"- **Successful:** {self.successful} ✅",
            f"- **Failed:** {self.failed} ❌",
            f"- **Skipped:** {self.skipped} ⏭️",
            "",
            "## Results",
            "",
            "| Dataset | Status | Details |",
            "|---------|--------|---------|",
        ]
        
        for result in self.results:
            dataset_name = Path(result.dataset_path).name
            status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}[result.status]
            details = result.error if result.error else "OK"
            lines.append(f"| {dataset_name} | {status_emoji} {result.status} | {details} |")
        
        return "\n".join(lines)


class BatchProcessor:
    """Base batch processor for multi-dataset operations"""
    
    def __init__(self, operation: str):
        self.operation = operation
    
    def find_datasets(self, directory: str | Path, pattern: str = "*.jsonl") -> list[Path]:
        """Find all dataset files in directory matching pattern"""
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        datasets = sorted(directory_path.glob(pattern))
        return datasets
    
    def process_batch(
        self,
        datasets: list[Path],
        processor_func: Any,
        skip_on_error: bool = True,
    ) -> BatchOperationReport:
        """Process multiple datasets with given function"""
        started_at = datetime.utcnow().isoformat()
        results: list[BatchResult] = []
        
        for dataset_path in datasets:
            try:
                result_data = processor_func(dataset_path)
                results.append(BatchResult(
                    dataset_path=str(dataset_path),
                    status="success",
                    error=None,
                    result=result_data,
                ))
            except Exception as e:
                results.append(BatchResult(
                    dataset_path=str(dataset_path),
                    status="failed",
                    error=str(e),
                    result={},
                ))
                if not skip_on_error:
                    raise
        
        completed_at = datetime.utcnow().isoformat()
        
        successful = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        
        return BatchOperationReport(
            operation=self.operation,
            started_at=started_at,
            completed_at=completed_at,
            total_datasets=len(datasets),
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=tuple(results),
        )


class BatchHealthMonitor(BatchProcessor):
    """Batch health monitoring for multiple datasets"""
    
    def __init__(
        self,
        quality_warning: float = 75.0,
        quality_critical: float = 60.0,
        duplicate_warning: float = 0.15,
        duplicate_critical: float = 0.30,
    ):
        super().__init__("health_check")
        self.monitor = DatasetHealthMonitor(
            quality_warning=quality_warning,
            quality_critical=quality_critical,
            duplicate_warning=duplicate_warning,
            duplicate_critical=duplicate_critical,
        )
    
    def check_health(self, dataset_path: Path) -> dict[str, Any]:
        """Check health of a single dataset"""
        snapshot = self.monitor.check_health(str(dataset_path))
        return snapshot.to_dict()
    
    def check_directory(
        self,
        directory: str | Path,
        pattern: str = "*.jsonl",
        skip_on_error: bool = True,
    ) -> BatchOperationReport:
        """Check health of all datasets in directory"""
        datasets = self.find_datasets(directory, pattern)
        return self.process_batch(datasets, self.check_health, skip_on_error)


class BatchOptimizer(BatchProcessor):
    """Batch optimization for multiple datasets"""
    
    def __init__(self):
        super().__init__("optimization")
        self.optimizer = DatasetOptimizer()
    
    def optimize_dataset(
        self,
        dataset_path: Path,
        output_dir: Path,
        remove_duplicates: bool = True,
        filter_low_quality: bool = True,
        quality_threshold: int = 60,
    ) -> dict[str, Any]:
        """Optimize a single dataset"""
        output_path = output_dir / f"{dataset_path.stem}-optimized.jsonl"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = self.optimizer.optimize(
            str(dataset_path),
            output_path=str(output_path),
            remove_duplicates=remove_duplicates,
            filter_low_quality=filter_low_quality,
            quality_threshold=quality_threshold,
        )
        return report.to_dict()
    
    def optimize_directory(
        self,
        directory: str | Path,
        output_dir: str | Path,
        pattern: str = "*.jsonl",
        skip_on_error: bool = True,
        remove_duplicates: bool = True,
        filter_low_quality: bool = True,
        quality_threshold: int = 60,
    ) -> BatchOperationReport:
        """Optimize all datasets in directory"""
        datasets = self.find_datasets(directory, pattern)
        output_path = Path(output_dir)
        
        def optimize_func(dataset_path: Path) -> dict[str, Any]:
            return self.optimize_dataset(
                dataset_path,
                output_path,
                remove_duplicates,
                filter_low_quality,
                quality_threshold,
            )
        
        return self.process_batch(datasets, optimize_func, skip_on_error)


class BatchQualityScorer(BatchProcessor):
    """Batch quality scoring for multiple datasets"""
    
    def __init__(
        self,
        min_record_score: int = 60,
        min_average_score: int = 70,
        max_failed_ratio: float = 0.1,
        min_records: int = 100,
    ):
        super().__init__("quality_scoring")
        self.scorer = DatasetQualityScorer(
            min_record_score=min_record_score,
            min_average_score=min_average_score,
            max_failed_ratio=max_failed_ratio,
            min_records=min_records,
        )
    
    def score_dataset(self, dataset_path: Path) -> dict[str, Any]:
        """Score quality of a single dataset"""
        report = self.scorer.score_dataset(str(dataset_path))
        return report.to_dict(include_records=False)
    
    def score_directory(
        self,
        directory: str | Path,
        pattern: str = "*.jsonl",
        skip_on_error: bool = True,
    ) -> BatchOperationReport:
        """Score quality of all datasets in directory"""
        datasets = self.find_datasets(directory, pattern)
        return self.process_batch(datasets, self.score_dataset, skip_on_error)
