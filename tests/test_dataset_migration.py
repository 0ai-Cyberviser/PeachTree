"""Tests for dataset_migration module"""
import json
from pathlib import Path
import pytest

from peachtree.dataset_migration import (
    DatasetMigrationEngine,
    MigrationPlan,
    MigrationRule,
    MigrationResult,
)


@pytest.fixture
def migration_engine():
    return DatasetMigrationEngine()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "old_name": "John", "age": "30", "content": "test content"},
        {"id": "2", "old_name": "Jane", "age": "25", "content": "more content"},
        {"id": "3", "old_name": "Bob", "age": "40", "content": "final content"},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_migration_rule_creation():
    rule = MigrationRule(
        rule_type="rename_field",
        target_field="old_name",
        params={"new_name": "name"},
    )
    assert rule.rule_type == "rename_field"
    assert rule.target_field == "old_name"
    assert rule.params["new_name"] == "name"


def test_migration_plan_creation():
    plan = MigrationPlan(
        plan_id="test_plan_v1",
        source_schema="v1",
        target_schema="v2",
    )
    assert plan.plan_id == "test_plan_v1"
    assert plan.source_schema == "v1"
    assert plan.target_schema == "v2"
    assert len(plan.rules) == 0


def test_migration_plan_add_rule():
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    rule = MigrationRule(rule_type="rename_field", target_field="old", params={"new_name": "new"})
    
    plan.add_rule(rule)
    assert len(plan.rules) == 1
    assert plan.rules[0].rule_type == "rename_field"


def test_rename_field_rule(migration_engine):
    record = {"old_name": "value", "other": "data"}
    rule = MigrationRule(rule_type="rename_field", target_field="old_name", params={"new_name": "new_name"})
    
    result = migration_engine.apply_migration_rule(record, rule)
    assert "new_name" in result
    assert "old_name" not in result
    assert result["new_name"] == "value"
    assert result["other"] == "data"


def test_add_field_rule(migration_engine):
    record = {"existing": "value"}
    rule = MigrationRule(rule_type="add_field", target_field="new_field", params={"default_value": "default"})
    
    result = migration_engine.apply_migration_rule(record, rule)
    assert "new_field" in result
    assert result["new_field"] == "default"
    assert result["existing"] == "value"


def test_remove_field_rule(migration_engine):
    record = {"to_remove": "value", "keep": "data"}
    rule = MigrationRule(rule_type="remove_field", target_field="to_remove", params={})
    
    result = migration_engine.apply_migration_rule(record, rule)
    assert "to_remove" not in result
    assert "keep" in result


def test_transform_field_rule(migration_engine):
    record = {"name": "john doe"}
    rule = MigrationRule(rule_type="transform_field", target_field="name", params={"transformer": "uppercase"})
    
    result = migration_engine.apply_migration_rule(record, rule)
    assert result["name"] == "JOHN DOE"


def test_change_type_rule(migration_engine):
    record = {"age": "30"}
    rule = MigrationRule(rule_type="change_type", target_field="age", params={"target_type": "int"})
    
    result = migration_engine.apply_migration_rule(record, rule)
    assert result["age"] == 30
    assert isinstance(result["age"], int)


def test_migrate_record(migration_engine):
    record = {"old_name": "John", "age": "30"}
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old_name", params={"new_name": "name"}))
    plan.add_rule(MigrationRule(rule_type="change_type", target_field="age", params={"target_type": "int"}))
    
    result = migration_engine.migrate_record(record, plan)
    assert "name" in result
    assert "old_name" not in result
    assert result["name"] == "John"
    assert result["age"] == 30
    assert isinstance(result["age"], int)


def test_migrate_dataset(migration_engine, sample_dataset, tmp_path):
    output = tmp_path / "migrated.jsonl"
    plan = MigrationPlan(plan_id="rename_test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old_name", params={"new_name": "name"}))
    
    result = migration_engine.migrate_dataset(sample_dataset, output, plan)
    
    assert result.source_records == 3
    assert result.migrated_records == 3
    assert result.failed_records == 0
    assert output.exists()
    
    # Verify migrated content
    with open(output) as f:
        migrated = [json.loads(line) for line in f]
    
    assert len(migrated) == 3
    assert all("name" in r for r in migrated)
    assert all("old_name" not in r for r in migrated)


def test_create_simple_plan(migration_engine):
    plan = migration_engine.create_simple_plan("test_plan", "v1", "v2")
    assert plan.plan_id == "test_plan"
    assert plan.source_schema == "v1"
    assert plan.target_schema == "v2"
    assert len(plan.rules) == 0


def test_create_field_rename_plan(migration_engine):
    renames = {"old1": "new1", "old2": "new2"}
    plan = migration_engine.create_field_rename_plan("rename_plan", renames)
    
    assert len(plan.rules) == 2
    assert all(r.rule_type == "rename_field" for r in plan.rules)


def test_create_type_migration_plan(migration_engine):
    type_changes = {"field1": "int", "field2": "float"}
    plan = migration_engine.create_type_migration_plan("type_plan", type_changes)
    
    assert len(plan.rules) == 2
    assert all(r.rule_type == "change_type" for r in plan.rules)


def test_save_load_plan(migration_engine, tmp_path):
    plan = MigrationPlan(plan_id="save_test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old", params={"new_name": "new"}))
    
    plan_file = tmp_path / "plan.json"
    migration_engine.save_plan(plan, plan_file)
    
    assert plan_file.exists()
    
    loaded = migration_engine.load_plan(plan_file)
    assert loaded.plan_id == plan.plan_id
    assert loaded.source_schema == plan.source_schema
    assert loaded.target_schema == plan.target_schema
    assert len(loaded.rules) == len(plan.rules)
    assert loaded.rules[0].rule_type == "rename_field"


def test_validate_plan_success(migration_engine):
    plan = MigrationPlan(plan_id="valid", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old", params={"new_name": "new"}))
    
    errors = migration_engine.validate_plan(plan)
    assert len(errors) == 0


def test_validate_plan_missing_plan_id(migration_engine):
    plan = MigrationPlan(plan_id="", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old", params={"new_name": "new"}))
    
    errors = migration_engine.validate_plan(plan)
    assert len(errors) > 0
    assert any("plan_id" in e for e in errors)


def test_validate_plan_no_rules(migration_engine):
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    
    errors = migration_engine.validate_plan(plan)
    assert len(errors) > 0
    assert any("at least one rule" in e for e in errors)


def test_validate_plan_rename_missing_param(migration_engine):
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old", params={}))
    
    errors = migration_engine.validate_plan(plan)
    assert len(errors) > 0
    assert any("new_name" in e for e in errors)


def test_validate_plan_unknown_transformer(migration_engine):
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="transform_field", target_field="field", params={"transformer": "unknown"}))
    
    errors = migration_engine.validate_plan(plan)
    assert len(errors) > 0
    assert any("unknown transformer" in e for e in errors)


def test_register_custom_transformer(migration_engine):
    def double(x):
        return x * 2
    
    migration_engine.register_transformer("double", double)
    assert "double" in migration_engine.transformers
    
    record = {"value": 5}
    rule = MigrationRule(rule_type="transform_field", target_field="value", params={"transformer": "double"})
    result = migration_engine.apply_migration_rule(record, rule)
    assert result["value"] == 10


def test_migration_result_to_dict():
    result = MigrationResult(
        source_path="input.jsonl",
        output_path="output.jsonl",
        source_records=100,
        migrated_records=98,
        failed_records=2,
        migration_plan="plan_v1",
    )
    
    d = result.to_dict()
    assert d["source_records"] == 100
    assert d["migrated_records"] == 98
    assert d["success_rate"] == 98.0


def test_plan_to_json():
    plan = MigrationPlan(plan_id="test", source_schema="v1", target_schema="v2")
    plan.add_rule(MigrationRule(rule_type="rename_field", target_field="old", params={"new_name": "new"}))
    
    json_str = plan.to_json()
    data = json.loads(json_str)
    
    assert data["plan_id"] == "test"
    assert len(data["rules"]) == 1
    assert data["rules"][0]["rule_type"] == "rename_field"
