"""Tests for dataset_migration module."""
import pytest
import json

from peachtree.dataset_migration import (
    DatasetMigrationEngine,
    MigrationRule,
    MigrationPlan,
    MigrationResult,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample dataset for testing."""
    dataset = tmp_path / "dataset.jsonl"
    records = [
        {"id": i, "old_field": f"value_{i}", "data": {"nested": i}}
        for i in range(10)
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


def test_migration_rule_creation():
    """Test MigrationRule creation."""
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_field",
        params={"new_name": "new_field"}
    )
    assert rule.rule_type == "rename_field"
    assert rule.target_field == "old_field"
    assert rule.params["new_name"] == "new_field"


def test_migration_rule_to_dict():
    """Test MigrationRule to_dict."""
    rule = MigrationRule(
        rule_type="add_field",
        target_field="new_field",
        params={"value": "default"}
    )
    d = rule.to_dict()
    assert d["rule_type"] == "add_field"
    assert d["target_field"] == "new_field"


def test_migration_plan_creation():
    """Test MigrationPlan creation."""
    plan = MigrationPlan(
        plan_id="plan123",
        source_schema="v1",
        target_schema="v2",
    )
    assert plan.plan_id == "plan123"
    assert plan.source_schema == "v1"
    assert plan.target_schema == "v2"


def test_migration_plan_add_rule():
    """Test adding rules to MigrationPlan."""
    plan = MigrationPlan(
        plan_id="plan123",
        source_schema="v1",
        target_schema="v2",
    )
    
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_field",
        params={"new_name": "new_field"}
    )
    
    plan.add_rule(rule)
    assert len(plan.rules) == 1
    assert plan.rules[0] == rule


def test_migration_plan_to_dict():
    """Test MigrationPlan to_dict."""
    plan = MigrationPlan(
        plan_id="plan123",
        source_schema="v1",
        target_schema="v2",
    )
    
    rule = MigrationRule(
        rule_type="remove_field",
        target_field="deprecated_field"
    )
    plan.add_rule(rule)
    
    d = plan.to_dict()
    assert d["plan_id"] == "plan123"
    assert d["source_schema"] == "v1"
    assert d["target_schema"] == "v2"
    assert len(d["rules"]) == 1


def test_migration_engine_creation():
    """Test DatasetMigrationEngine creation."""
    engine = DatasetMigrationEngine()
    assert engine is not None


def test_migration_engine_create_plan():
    """Test creating migration plan."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    assert plan.source_schema == "v1"
    assert plan.target_schema == "v2"
    assert len(plan.rules) == 0


def test_migration_engine_rename_field(sample_dataset, tmp_path):
    """Test field renaming migration."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_field",
        params={"new_name": "new_field"}
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    assert result.source_records == 10
    assert result.migrated_records == 10


def test_migration_engine_add_field(sample_dataset, tmp_path):
    """Test adding new field migration."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="add_field",
        target_field="new_field",
        params={"value": "default_value"}
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    assert result.migrated_records == 10


def test_migration_engine_remove_field(sample_dataset, tmp_path):
    """Test removing field migration."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="remove_field",
        target_field="old_field"
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    assert result.migrated_records == 10


def test_migration_engine_transform_field(sample_dataset, tmp_path):
    """Test field transformation migration."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="transform_field",
        target_field="old_field",
        params={"transform": "uppercase"}
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    assert result.migrated_records == 10


def test_migration_result_creation():
    """Test MigrationResult creation."""
    result = MigrationResult(
        plan_id="plan123",
        success=True,
        source_records=100,
        migrated_records=100,
        failed_records=0,
    )
    assert result.success
    assert result.source_records == 100
    assert result.migrated_records == 100


def test_migration_result_to_dict():
    """Test MigrationResult to_dict."""
    result = MigrationResult(
        plan_id="plan123",
        success=True,
        source_records=50,
        migrated_records=48,
        failed_records=2,
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["source_records"] == 50
    assert d["failed_records"] == 2


def test_migration_engine_validate_plan():
    """Test migration plan validation."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="field1",
        params={"new_name": "field2"}
    )
    plan.add_rule(rule)
    
    errors = engine.validate_plan(plan)
    assert isinstance(errors, list)


def test_migration_engine_load_plan(tmp_path):
    """Test loading migration plan from file."""
    engine = DatasetMigrationEngine()
    plan_file = tmp_path / "plan.json"
    
    plan_data = {
        "plan_id": "test_plan",
        "source_schema": "v1",
        "target_schema": "v2",
        "rules": [
            {
                "rule_type": "rename_field",
                "target_field": "old_name",
                "params": {"new_name": "new_name"}
            }
        ]
    }
    
    plan_file.write_text(json.dumps(plan_data, indent=2))
    
    plan = engine.load_plan(plan_file)
    assert plan.plan_id == "test_plan"
    assert plan.source_schema == "v1"
    assert len(plan.rules) == 1


def test_migration_engine_save_plan(tmp_path):
    """Test saving migration plan to file."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="add_field",
        target_field="new_field",
        params={"value": "default"}
    )
    plan.add_rule(rule)
    
    plan_file = tmp_path / "plan.json"
    engine.save_plan(plan, plan_file)
    
    assert plan_file.exists()
    plan_data = json.loads(plan_file.read_text())
    assert plan_data["source_schema"] == "v1"


def test_migration_engine_multiple_rules(sample_dataset, tmp_path):
    """Test migration with multiple rules."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    plan.add_rule(MigrationRule("add_field", "status", {"value": "active"}))
    plan.add_rule(MigrationRule("rename_field", "old_field", {"new_name": "field"}))
    plan.add_rule(MigrationRule("remove_field", "deprecated"))
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    assert result.migrated_records == 10


def test_migration_engine_dry_run(sample_dataset):
    """Test migration dry run."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_field",
        params={"new_name": "new_field"}
    )
    plan.add_rule(rule)
    
    preview = engine.preview_migration(sample_dataset, plan, num_records=3)
    
    assert len(preview) == 3


def test_migration_engine_rollback(sample_dataset, tmp_path):
    """Test migration rollback capability."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_field",
        params={"new_name": "new_field"}
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.success
    
    # Create rollback plan
    rollback_plan = engine.create_rollback_plan(plan)
    assert rollback_plan.source_schema == "v2"
    assert rollback_plan.target_schema == "v1"


def test_migration_result_partial_success():
    """Test MigrationResult with partial success."""
    result = MigrationResult(
        plan_id="plan123",
        success=False,
        source_records=100,
        migrated_records=95,
        failed_records=5,
    )
    assert result.success is False
    assert result.failed_records == 5


def test_migration_plan_with_metadata():
    """Test MigrationPlan with metadata."""
    plan = MigrationPlan(
        plan_id="plan123",
        source_schema="v1",
        target_schema="v2",
        metadata={"created_by": "test", "purpose": "upgrade"}
    )
    assert plan.metadata["created_by"] == "test"


def test_migration_engine_statistics(sample_dataset, tmp_path):
    """Test migration statistics collection."""
    engine = DatasetMigrationEngine()
    plan = engine.create_plan("v1", "v2")
    
    rule = MigrationRule(
        rule_type="add_field",
        target_field="new_field",
        params={"value": "test"}
    )
    plan.add_rule(rule)
    
    output = tmp_path / "migrated.jsonl"
    result = engine.migrate_dataset(sample_dataset, output, plan)
    
    stats = engine.get_migration_statistics(result)
    assert stats["success_rate"] == 1.0
    assert stats["total_records"] == 10
