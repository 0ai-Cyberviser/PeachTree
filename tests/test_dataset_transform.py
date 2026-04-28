"""Tests for dataset transformation functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_transform import (
    DatasetTransformer,
    TransformationPipeline,
    TransformationStep,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample dataset for testing."""
    dataset = temp_dir / "dataset.jsonl"
    records = [
        {"record_id": "rec_001", "content": "  Test Content 1  ", "quality_score": 85, "source": "repo1"},
        {"record_id": "rec_002", "content": "Test Content 2", "quality_score": 65, "source": "repo2"},
        {"record_id": "rec_003", "content": "Test Content 3", "quality_score": 90, "source": "repo1"},
        {"record_id": "rec_004", "content": "Test Content 4", "quality_score": 55, "source": "repo3"},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


class TestTransformationStep:
    """Test TransformationStep dataclass."""
    
    def test_step_creation(self):
        """Test creating a transformation step."""
        step = TransformationStep(
            step_id="step1",
            step_type="map",
            params={"field_mapping": {"old": "new"}},
        )
        
        assert step.step_id == "step1"
        assert step.step_type == "map"
        assert "field_mapping" in step.params
    
    def test_step_to_dict(self):
        """Test converting step to dictionary."""
        step = TransformationStep(
            step_id="step2",
            step_type="filter",
            params={"condition": "quality_score >= 70"},
        )
        
        data = step.to_dict()
        assert data["step_id"] == "step2"
        assert data["step_type"] == "filter"
        assert data["params"]["condition"] == "quality_score >= 70"


class TestTransformationPipeline:
    """Test TransformationPipeline class."""
    
    def test_pipeline_creation(self):
        """Test creating a transformation pipeline."""
        pipeline = TransformationPipeline(
            pipeline_id="test_pipeline",
            pipeline_name="Test Pipeline",
        )
        
        assert pipeline.pipeline_id == "test_pipeline"
        assert pipeline.pipeline_name == "Test Pipeline"
        assert len(pipeline.steps) == 0
    
    def test_add_step(self):
        """Test adding steps to pipeline."""
        pipeline = TransformationPipeline(
            pipeline_id="test",
            pipeline_name="Test",
        )
        
        step1 = TransformationStep("step1", "map", {})
        step2 = TransformationStep("step2", "filter", {})
        
        pipeline.add_step(step1)
        pipeline.add_step(step2)
        
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0].step_id == "step1"
    
    def test_pipeline_to_json(self):
        """Test converting pipeline to JSON."""
        pipeline = TransformationPipeline("test", "Test")
        pipeline.add_step(TransformationStep("s1", "map", {}))
        
        json_str = pipeline.to_json()
        data = json.loads(json_str)
        
        assert data["pipeline_id"] == "test"
        assert len(data["steps"]) == 1


class TestDatasetTransformer:
    """Test DatasetTransformer class."""
    
    def test_map_fields(self):
        """Test field mapping transformation."""
        transformer = DatasetTransformer()
        
        record = {"old_field": "value", "keep_field": "keep"}
        mapping = {"old_field": "new_field"}
        
        result = transformer.map_fields(record, mapping)
        
        assert "new_field" in result
        assert result["new_field"] == "value"
        assert "keep_field" in result
    
    def test_filter_record_greater_than(self):
        """Test filter with >= condition."""
        transformer = DatasetTransformer()
        
        record = {"quality_score": 85}
        
        assert transformer.filter_record(record, "quality_score >= 70") is True
        assert transformer.filter_record(record, "quality_score >= 90") is False
    
    def test_filter_record_equals(self):
        """Test filter with == condition."""
        transformer = DatasetTransformer()
        
        record = {"status": "active"}
        
        assert transformer.filter_record(record, 'status == "active"') is True
        assert transformer.filter_record(record, 'status == "inactive"') is False
    
    def test_filter_record_contains(self):
        """Test filter with contains condition."""
        transformer = DatasetTransformer()
        
        record = {"content": "test content here"}
        
        assert transformer.filter_record(record, 'content contains "test"') is True
        assert transformer.filter_record(record, 'content contains "missing"') is False
    
    def test_transform_field_uppercase(self):
        """Test uppercase transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "test"}
        result = transformer.transform_field(record, "content", "uppercase")
        
        assert result["content"] == "TEST"
    
    def test_transform_field_lowercase(self):
        """Test lowercase transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "TEST"}
        result = transformer.transform_field(record, "content", "lowercase")
        
        assert result["content"] == "test"
    
    def test_transform_field_trim(self):
        """Test trim transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "  test  "}
        result = transformer.transform_field(record, "content", "trim")
        
        assert result["content"] == "test"
    
    def test_transform_field_prefix(self):
        """Test prefix transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "test"}
        result = transformer.transform_field(record, "content", "prefix", {"prefix": "PREFIX_"})
        
        assert result["content"] == "PREFIX_test"
    
    def test_transform_field_replace(self):
        """Test replace transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "test old test"}
        result = transformer.transform_field(record, "content", "replace", {"old": "old", "new": "new"})
        
        assert result["content"] == "test new test"
    
    def test_transform_field_truncate(self):
        """Test truncate transformation."""
        transformer = DatasetTransformer()
        
        record = {"content": "long content here"}
        result = transformer.transform_field(record, "content", "truncate", {"max_length": 4})
        
        assert result["content"] == "long"
    
    def test_add_field(self):
        """Test adding a new field."""
        transformer = DatasetTransformer()
        
        record = {"existing": "value"}
        result = transformer.add_field(record, "new_field", "new_value")
        
        assert "new_field" in result
        assert result["new_field"] == "new_value"
        assert result["existing"] == "value"
    
    def test_remove_field(self):
        """Test removing a field."""
        transformer = DatasetTransformer()
        
        record = {"field1": "value1", "field2": "value2"}
        result = transformer.remove_field(record, "field1")
        
        assert "field1" not in result
        assert "field2" in result
    
    def test_apply_step_map(self):
        """Test applying a map step."""
        transformer = DatasetTransformer()
        
        record = {"old": "value"}
        step = TransformationStep(
            "step1",
            "map",
            {"field_mapping": {"old": "new"}},
        )
        
        result = transformer.apply_step(record, step)
        
        assert result is not None
        assert "new" in result
    
    def test_apply_step_filter(self):
        """Test applying a filter step."""
        transformer = DatasetTransformer()
        
        record = {"quality_score": 85}
        step = TransformationStep(
            "step1",
            "filter",
            {"condition": "quality_score >= 70"},
        )
        
        result = transformer.apply_step(record, step)
        assert result is not None
        
        # Filter out low quality
        step2 = TransformationStep(
            "step2",
            "filter",
            {"condition": "quality_score >= 90"},
        )
        
        result2 = transformer.apply_step(record, step2)
        assert result2 is None
    
    def test_apply_pipeline(self, sample_dataset, temp_dir):
        """Test applying a complete pipeline."""
        transformer = DatasetTransformer()
        
        # Create pipeline
        pipeline = TransformationPipeline("test", "Test Pipeline")
        
        # Filter high quality records
        pipeline.add_step(TransformationStep(
            "filter_quality",
            "filter",
            {"condition": "quality_score >= 70"},
        ))
        
        # Trim content
        pipeline.add_step(TransformationStep(
            "trim_content",
            "transform",
            {"field": "content", "transformation": "trim"},
        ))
        
        output = temp_dir / "transformed.jsonl"
        result = transformer.apply_pipeline(sample_dataset, output, pipeline)
        
        assert result.success is True
        assert result.output_records > 0
        assert result.filtered_records > 0
        assert output.exists()
    
    def test_create_pipeline(self):
        """Test creating a new pipeline."""
        transformer = DatasetTransformer()
        
        pipeline = transformer.create_pipeline("test_id", "Test Name")
        
        assert pipeline.pipeline_id == "test_id"
        assert pipeline.pipeline_name == "Test Name"
        assert len(pipeline.steps) == 0
    
    def test_save_and_load_pipeline(self, temp_dir):
        """Test saving and loading a pipeline."""
        transformer = DatasetTransformer()
        
        # Create and save pipeline
        pipeline = TransformationPipeline("saved", "Saved Pipeline")
        pipeline.add_step(TransformationStep("s1", "map", {"field_mapping": {"a": "b"}}))
        
        path = temp_dir / "pipeline.json"
        transformer.save_pipeline(pipeline, path)
        
        assert path.exists()
        
        # Load pipeline
        loaded = transformer.load_pipeline(path)
        
        assert loaded.pipeline_id == "saved"
        assert loaded.pipeline_name == "Saved Pipeline"
        assert len(loaded.steps) == 1
        assert loaded.steps[0].step_id == "s1"
    
    def test_create_standard_pipeline(self):
        """Test creating a standard ETL pipeline."""
        transformer = DatasetTransformer()
        
        pipeline = transformer.create_standard_pipeline()
        
        assert pipeline.pipeline_id == "standard_etl"
        assert len(pipeline.steps) == 3  # filter, trim, add_timestamp
