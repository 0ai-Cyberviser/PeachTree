"""Tests for dataset templates functionality."""

from pathlib import Path
import json
import pytest

from peachtree.dataset_templates import (
    DatasetTemplateManager,
    DatasetTemplate,
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)


def test_template_manager_initialization():
    """Test that template manager initializes with built-in templates."""
    manager = DatasetTemplateManager()
    
    assert len(manager.templates) >= 5  # Should have at least 5 built-in templates
    assert "cybersecurity_training_v1" in manager.templates
    assert "nlp_text_classification_v1" in manager.templates
    assert "question_answering_v1" in manager.templates
    assert "code_generation_v1" in manager.templates
    assert "instruction_tuning_v1" in manager.templates


def test_get_template():
    """Test getting a template by ID."""
    manager = DatasetTemplateManager()
    
    template = manager.get_template("cybersecurity_training_v1")
    
    assert template is not None
    assert template.metadata.template_id == "cybersecurity_training_v1"
    assert template.metadata.category == TemplateCategory.CYBERSECURITY
    assert template.metadata.complexity == TemplateComplexity.INTERMEDIATE


def test_get_nonexistent_template():
    """Test getting a template that doesn't exist."""
    manager = DatasetTemplateManager()
    
    template = manager.get_template("nonexistent_template")
    
    assert template is None


def test_list_all_templates():
    """Test listing all templates."""
    manager = DatasetTemplateManager()
    
    templates = manager.list_templates()
    
    assert len(templates) >= 5
    assert all(isinstance(t, DatasetTemplate) for t in templates)


def test_list_templates_by_category():
    """Test filtering templates by category."""
    manager = DatasetTemplateManager()
    
    nlp_templates = manager.list_templates(category=TemplateCategory.NLP)
    
    assert len(nlp_templates) >= 2  # At least NLP classification and QA
    assert all(t.metadata.category == TemplateCategory.NLP for t in nlp_templates)


def test_list_templates_by_complexity():
    """Test filtering templates by complexity."""
    manager = DatasetTemplateManager()
    
    basic_templates = manager.list_templates(complexity=TemplateComplexity.BASIC)
    
    assert all(t.metadata.complexity == TemplateComplexity.BASIC for t in basic_templates)


def test_list_templates_by_category_and_complexity():
    """Test filtering by both category and complexity."""
    manager = DatasetTemplateManager()
    
    advanced_nlp = manager.list_templates(
        category=TemplateCategory.NLP,
        complexity=TemplateComplexity.ADVANCED,
    )
    
    assert all(
        t.metadata.category == TemplateCategory.NLP 
        and t.metadata.complexity == TemplateComplexity.ADVANCED 
        for t in advanced_nlp
    )


def test_create_custom_template():
    """Test creating a custom template."""
    manager = DatasetTemplateManager()
    
    template = manager.create_custom_template(
        template_id="custom_test",
        name="Test Template",
        description="A test template",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        config={"test_key": "test_value"},
        author="test_author",
    )
    
    assert template.metadata.template_id == "custom_test"
    assert template.metadata.name == "Test Template"
    assert template.metadata.author == "test_author"
    assert template.config["test_key"] == "test_value"
    assert "custom_test" in manager.templates


def test_update_template_config():
    """Test updating template configuration."""
    manager = DatasetTemplateManager()
    
    # Create custom template
    manager.create_custom_template(
        template_id="update_test",
        name="Update Test",
        description="Template for update testing",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        config={"key1": "value1"},
    )
    
    # Update config
    updated = manager.update_template(
        "update_test",
        config={"key2": "value2"},
    )
    
    assert updated is not None
    assert "key1" in updated.config  # Original key preserved
    assert "key2" in updated.config  # New key added


def test_update_template_pipeline_steps():
    """Test updating template pipeline steps."""
    manager = DatasetTemplateManager()
    
    manager.create_custom_template(
        template_id="pipeline_test",
        name="Pipeline Test",
        description="Test",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        config={},
    )
    
    new_steps = [{"step": "ingest"}, {"step": "transform"}]
    updated = manager.update_template("pipeline_test", pipeline_steps=new_steps)
    
    assert len(updated.pipeline_steps) == 2
    assert updated.pipeline_steps[0]["step"] == "ingest"


def test_update_nonexistent_template():
    """Test updating a template that doesn't exist."""
    manager = DatasetTemplateManager()
    
    updated = manager.update_template("nonexistent", config={})
    
    assert updated is None


def test_delete_template():
    """Test deleting a template."""
    manager = DatasetTemplateManager()
    
    manager.create_custom_template(
        template_id="delete_test",
        name="Delete Test",
        description="Test",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        config={},
    )
    
    assert "delete_test" in manager.templates
    
    success = manager.delete_template("delete_test")
    
    assert success
    assert "delete_test" not in manager.templates


def test_delete_nonexistent_template():
    """Test deleting a template that doesn't exist."""
    manager = DatasetTemplateManager()
    
    success = manager.delete_template("nonexistent")
    
    assert not success


def test_instantiate_template():
    """Test instantiating a template with parameters."""
    manager = DatasetTemplateManager()
    
    instance = manager.instantiate_template(
        "cybersecurity_training_v1",
        params={"min_quality_score": 90.0},
    )
    
    assert instance["template_id"] == "cybersecurity_training_v1"
    assert instance["config"]["min_quality_score"] == 90.0
    assert "pipeline_steps" in instance
    assert "quality_gates" in instance


def test_instantiate_template_no_params():
    """Test instantiating without custom parameters."""
    manager = DatasetTemplateManager()
    
    instance = manager.instantiate_template("nlp_text_classification_v1")
    
    assert instance["template_id"] == "nlp_text_classification_v1"
    assert "config" in instance


def test_instantiate_nonexistent_template():
    """Test instantiating a template that doesn't exist."""
    manager = DatasetTemplateManager()
    
    with pytest.raises(ValueError, match="not found"):
        manager.instantiate_template("nonexistent")


def test_save_template(tmp_path):
    """Test saving a template to file."""
    manager = DatasetTemplateManager()
    output_path = tmp_path / "template.json"
    
    manager.save_template("cybersecurity_training_v1", output_path)
    
    assert output_path.exists()
    
    # Verify content
    data = json.loads(output_path.read_text())
    assert data["metadata"]["template_id"] == "cybersecurity_training_v1"


def test_save_nonexistent_template(tmp_path):
    """Test saving a template that doesn't exist."""
    manager = DatasetTemplateManager()
    output_path = tmp_path / "template.json"
    
    with pytest.raises(ValueError, match="not found"):
        manager.save_template("nonexistent", output_path)


def test_load_template(tmp_path):
    """Test loading a template from file."""
    manager1 = DatasetTemplateManager()
    output_path = tmp_path / "template.json"
    
    # Save template
    manager1.save_template("code_generation_v1", output_path)
    
    # Load in new manager
    manager2 = DatasetTemplateManager()
    # Clear existing templates for clean test
    manager2.templates.clear()
    
    loaded = manager2.load_template(output_path)
    
    assert loaded.metadata.template_id == "code_generation_v1"
    assert "code_generation_v1" in manager2.templates


def test_template_metadata_to_dict():
    """Test converting template metadata to dictionary."""
    metadata = TemplateMetadata(
        template_id="test_id",
        name="Test Template",
        description="Test description",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        author="test_author",
        version="1.0.0",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        tags=["test", "sample"],
    )
    
    data = metadata.to_dict()
    
    assert data["template_id"] == "test_id"
    assert data["name"] == "Test Template"
    assert data["category"] == "general"
    assert data["complexity"] == "basic"
    assert "test" in data["tags"]


def test_template_to_dict():
    """Test converting complete template to dictionary."""
    metadata = TemplateMetadata(
        template_id="test",
        name="Test",
        description="Test",
        category=TemplateCategory.GENERAL,
        complexity=TemplateComplexity.BASIC,
        author="test",
        version="1.0.0",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    
    template = DatasetTemplate(
        metadata=metadata,
        config={"key": "value"},
        pipeline_steps=[{"step": "ingest"}],
        quality_gates=[{"gate": "min_records"}],
        validation_rules=[{"rule": "required_fields"}],
    )
    
    data = template.to_dict()
    
    assert "metadata" in data
    assert "config" in data
    assert "pipeline_steps" in data
    assert "quality_gates" in data
    assert "validation_rules" in data


def test_template_to_json():
    """Test converting template to JSON string."""
    manager = DatasetTemplateManager()
    template = manager.get_template("instruction_tuning_v1")
    
    json_str = template.to_json()
    
    # Should be valid JSON
    data = json.loads(json_str)
    assert data["metadata"]["template_id"] == "instruction_tuning_v1"


def test_get_statistics():
    """Test getting template statistics."""
    manager = DatasetTemplateManager()
    
    stats = manager.get_statistics()
    
    assert "total_templates" in stats
    assert "by_category" in stats
    assert "by_complexity" in stats
    assert stats["total_templates"] >= 5


def test_cybersecurity_template_structure():
    """Test cybersecurity template has required structure."""
    manager = DatasetTemplateManager()
    template = manager.get_template("cybersecurity_training_v1")
    
    assert template.metadata.category == TemplateCategory.CYBERSECURITY
    assert "domain" in template.config
    assert template.config["domain"] == "cybersecurity"
    assert len(template.pipeline_steps) > 0
    assert len(template.quality_gates) > 0
    assert len(template.validation_rules) > 0


def test_nlp_classification_template_structure():
    """Test NLP classification template structure."""
    manager = DatasetTemplateManager()
    template = manager.get_template("nlp_text_classification_v1")
    
    assert template.metadata.category == TemplateCategory.NLP
    assert template.metadata.complexity == TemplateComplexity.BASIC
    assert "required_fields" in template.config
    assert "text" in template.config["required_fields"]
    assert "label" in template.config["required_fields"]


def test_question_answering_template_structure():
    """Test QA template structure."""
    manager = DatasetTemplateManager()
    template = manager.get_template("question_answering_v1")
    
    assert template.metadata.category == TemplateCategory.NLP
    assert "qa" in template.config["domain"]
    assert "context" in template.config["required_fields"]
    assert "question" in template.config["required_fields"]
    assert "answer" in template.config["required_fields"]


def test_code_generation_template_structure():
    """Test code generation template structure."""
    manager = DatasetTemplateManager()
    template = manager.get_template("code_generation_v1")
    
    assert template.metadata.category == TemplateCategory.NLP
    assert template.metadata.complexity == TemplateComplexity.ADVANCED
    assert "supported_languages" in template.config
    assert "python" in template.config["supported_languages"]


def test_instruction_tuning_template_structure():
    """Test instruction tuning template structure."""
    manager = DatasetTemplateManager()
    template = manager.get_template("instruction_tuning_v1")
    
    assert template.metadata.category == TemplateCategory.GENERAL
    assert template.config["format"] == "instruction"
    assert "instruction" in template.config["required_fields"]
    assert "response" in template.config["required_fields"]
