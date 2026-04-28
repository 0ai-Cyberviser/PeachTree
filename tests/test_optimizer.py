"""Tests for optimizer module"""
from pathlib import Path
import json

import pytest

from peachtree.optimizer import DatasetOptimizer, OptimizationReport


@pytest.fixture
def sample_dataset_with_duplicates(tmp_path):
    """Create a sample dataset with duplicates and low-quality records"""
    dataset = tmp_path / "test_dataset.jsonl"
    records = [
        # Good quality record
        {
            "id": "rec1",
            "instruction": "What is machine learning?",
            "input": "",
            "output": "Machine learning is a subset of AI that enables systems to learn from data.",
            "source_repo": "test/repo",
            "source_path": "ml.md",
            "source_digest": "abc123",
            "license_id": "MIT",
            "safety_score": 0.95,
            "quality_score": 0.90,
        },
        # Duplicate (same normalized content)
        {
            "id": "rec2",
            "instruction": "What  is   machine learning?",  # Extra spaces
            "input": "",
            "output": "Machine learning is a subset of AI that enables systems to learn from data.",
            "source_repo": "test/repo2",
            "source_path": "ml2.md",
            "source_digest": "def456",
            "license_id": "MIT",
            "safety_score": 0.95,
            "quality_score": 0.90,
        },
        # Low quality (short output)
        {
            "id": "rec3",
            "instruction": "Test",
            "input": "",
            "output": "Bad",
            "source_repo": "test/repo",
            "source_path": "bad.md",
            "source_digest": "ghi789",
            "license_id": "MIT",
            "safety_score": 0.70,
            "quality_score": 0.40,
        },
        # Good quality record 2
        {
            "id": "rec4",
            "instruction": "Explain neural networks",
            "input": "in simple terms",
            "output": "Neural networks are computing systems inspired by biological neural networks.",
            "source_repo": "test/repo",
            "source_path": "nn.md",
            "source_digest": "jkl012",
            "license_id": "Apache-2.0",
            "safety_score": 0.92,
            "quality_score": 0.88,
        },
    ]
    lines = [json.dumps(r) for r in records]
    dataset.write_text("\n".join(lines) + "\n")
    return dataset


def test_optimizer_initialization():
    """Test optimizer initialization"""
    optimizer = DatasetOptimizer()
    assert optimizer.output_dir == Path("data/optimized")


def test_optimize_full_workflow(sample_dataset_with_duplicates, tmp_path):
    """Test full optimization workflow"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        remove_duplicates=True,
        filter_low_quality=True,
        quality_threshold=60,
        output_path=output,
    )
    
    assert isinstance(report, OptimizationReport)
    assert report.status == "completed"
    assert report.initial_record_count == 4
    assert report.records_removed > 0  # Should remove duplicate and low-quality
    assert output.exists()


def test_optimize_duplicate_removal_only(sample_dataset_with_duplicates, tmp_path):
    """Test optimization with only duplicate removal"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        remove_duplicates=True,
        filter_low_quality=False,
        output_path=output,
    )
    
    assert report.status == "completed"
    # Should remove 1 duplicate but keep low-quality record
    assert report.records_removed >= 1


def test_optimize_quality_filter_only(sample_dataset_with_duplicates, tmp_path):
    """Test optimization with only quality filtering"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        remove_duplicates=False,
        filter_low_quality=True,
        quality_threshold=60,
        output_path=output,
    )
    
    assert report.status == "completed"
    # Should filter low-quality but keep duplicates
    assert report.records_removed >= 1


def test_optimization_report_to_json(sample_dataset_with_duplicates, tmp_path):
    """Test optimization report JSON serialization"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        output_path=output,
    )
    
    json_output = report.to_json()
    assert isinstance(json_output, str)
    
    data = json.loads(json_output)
    assert "dataset_path" in data
    assert "status" in data
    assert "initial_quality" in data
    assert "final_quality" in data
    assert "steps" in data


def test_optimization_report_to_markdown(sample_dataset_with_duplicates, tmp_path):
    """Test optimization report markdown generation"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        output_path=output,
    )
    
    markdown = report.to_markdown()
    assert "# PeachTree Dataset Optimization Report" in markdown
    assert "Results" in markdown
    assert "Optimization Steps" in markdown


def test_optimization_steps_tracking(sample_dataset_with_duplicates, tmp_path):
    """Test that optimization steps are properly tracked"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        remove_duplicates=True,
        filter_low_quality=True,
        output_path=output,
    )
    
    # Should have 4 steps: baseline, dedup, filter, final
    assert len(report.steps) == 4
    
    step_names = [step.name for step in report.steps]
    assert "Baseline Quality Assessment" in step_names
    assert "Duplicate Removal" in step_names
    assert "Quality Filtering" in step_names
    assert "Final Quality Assessment" in step_names
    
    # All steps should be completed
    for step in report.steps:
        assert step.status == "completed"


def test_quality_improvement_tracking(sample_dataset_with_duplicates, tmp_path):
    """Test that quality improvement is tracked"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        remove_duplicates=True,
        filter_low_quality=True,
        quality_threshold=60,
        output_path=output,
    )
    
    assert report.initial_quality is not None
    assert report.final_quality is not None
    # Quality should improve after removing bad records
    assert report.final_quality >= report.initial_quality


def test_custom_quality_threshold(sample_dataset_with_duplicates, tmp_path):
    """Test optimization with custom quality threshold"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    # Very high threshold - should filter more
    report = optimizer.optimize(
        sample_dataset_with_duplicates,
        filter_low_quality=True,
        quality_threshold=85,
        output_path=output,
    )
    
    assert report.status == "completed"
    # Should remove more records with higher threshold
    assert report.records_removed > 0


def test_output_file_created(sample_dataset_with_duplicates, tmp_path):
    """Test that output file is created correctly"""
    output = tmp_path / "optimized.jsonl"
    optimizer = DatasetOptimizer(output_dir=tmp_path)
    
    optimizer.optimize(
        sample_dataset_with_duplicates,
        output_path=output,
    )
    
    assert output.exists()
    assert output.stat().st_size > 0
    
    # Verify it's valid JSONL
    lines = output.read_text().strip().split("\n")
    for line in lines:
        record = json.loads(line)
        assert "id" in record
        assert "instruction" in record
