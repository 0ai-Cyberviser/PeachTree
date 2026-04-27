"""Tests for quality_gates module"""
import json
from pathlib import Path
import pytest

from peachtree.quality_gates import (
    QualityGateEngine,
    QualityGateConfig,
    GateRule,
    GateCheckResult,
    GateEvaluationReport,
)


@pytest.fixture
def gate_engine():
    return QualityGateEngine()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "content": "High quality content here", "quality_score": 85.0, "source_document": {"repo": "r1"}},
        {"id": "2", "content": "More high quality", "quality_score": 90.0, "source_document": {"repo": "r2"}},
        {"id": "3", "content": "Medium quality", "quality_score": 65.0, "source_document": {"repo": "r3"}},
        {"id": "4", "content": "Low quality", "quality_score": 45.0, "source_document": {"repo": "r4"}},
        {"id": "5", "content": "Good quality", "quality_score": 80.0, "source_document": {"repo": "r5"}},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_gate_rule_creation():
    rule = GateRule(
        rule_id="min_quality",
        rule_name="Minimum Quality",
        rule_type="must_pass",
        threshold=70.0,
        message="Quality must be >= 70",
    )
    assert rule.rule_id == "min_quality"
    assert rule.rule_type == "must_pass"
    assert rule.threshold == 70.0


def test_gate_rule_to_dict():
    rule = GateRule(
        rule_id="test_rule",
        rule_name="Test Rule",
        rule_type="should_pass",
        threshold=50.0,
    )
    d = rule.to_dict()
    assert d["rule_id"] == "test_rule"
    assert d["rule_type"] == "should_pass"


def test_gate_check_result_creation():
    result = GateCheckResult(
        rule_id="test_rule",
        passed=True,
        actual_value=85.0,
        threshold=70.0,
        message="Passed",
    )
    assert result.rule_id == "test_rule"
    assert result.passed is True
    assert result.actual_value == 85.0


def test_gate_check_result_to_dict():
    result = GateCheckResult(
        rule_id="test",
        passed=False,
        actual_value=60.0,
        threshold=70.0,
    )
    d = result.to_dict()
    assert d["passed"] is False
    assert d["actual_value"] == 60.0


def test_gate_evaluation_report_creation():
    report = GateEvaluationReport(
        dataset_id="test_dataset",
        timestamp="2024-01-01T00:00:00",
        total_rules=5,
        passed_rules=4,
        failed_rules=1,
        warnings=0,
        gate_passed=False,
    )
    assert report.dataset_id == "test_dataset"
    assert report.total_rules == 5
    assert report.gate_passed is False


def test_gate_evaluation_report_to_dict():
    report = GateEvaluationReport(
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        total_rules=10,
        passed_rules=8,
        failed_rules=2,
        warnings=1,
        gate_passed=False,
    )
    d = report.to_dict()
    assert d["total_rules"] == 10
    assert d["passed_rules"] == 8
    assert d["pass_rate"] == 80.0


def test_gate_evaluation_report_to_json():
    report = GateEvaluationReport(
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        total_rules=5,
        passed_rules=5,
        failed_rules=0,
        warnings=0,
        gate_passed=True,
    )
    json_str = report.to_json()
    data = json.loads(json_str)
    assert data["gate_passed"] is True


def test_gate_evaluation_report_to_markdown():
    report = GateEvaluationReport(
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        total_rules=2,
        passed_rules=2,
        failed_rules=0,
        warnings=0,
        gate_passed=True,
    )
    report.results = [
        GateCheckResult("rule1", True, 90.0, 70.0, "Passed"),
        GateCheckResult("rule2", True, 85.0, 80.0, "Passed"),
    ]
    
    markdown = report.to_markdown()
    assert "# Quality Gate Report" in markdown
    assert "✅ PASSED" in markdown
    assert "test" in markdown


def test_quality_gate_config_creation():
    config = QualityGateConfig(
        gate_id="test_gate",
        gate_name="Test Gate",
    )
    assert config.gate_id == "test_gate"
    assert len(config.rules) == 0


def test_quality_gate_config_add_rule():
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    rule = GateRule("rule1", "Rule 1", "must_pass", 70.0)
    
    config.add_rule(rule)
    assert len(config.rules) == 1


def test_quality_gate_config_to_json():
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("rule1", "Rule 1", "must_pass", 70.0))
    
    json_str = config.to_json()
    data = json.loads(json_str)
    assert data["gate_id"] == "test"
    assert len(data["rules"]) == 1


def test_check_min_quality_score(gate_engine, sample_dataset):
    passed, actual = gate_engine._check_min_quality_score(sample_dataset, 70.0)
    
    # Average: (85 + 90 + 65 + 45 + 80) / 5 = 73.0
    assert actual == 73.0
    assert passed is True


def test_check_min_quality_score_fail(gate_engine, sample_dataset):
    passed, actual = gate_engine._check_min_quality_score(sample_dataset, 80.0)
    
    assert actual == 73.0
    assert passed is False


def test_check_min_record_count(gate_engine, sample_dataset):
    passed, actual = gate_engine._check_min_record_count(sample_dataset, 3.0)
    
    assert actual == 5.0
    assert passed is True


def test_check_min_record_count_fail(gate_engine, sample_dataset):
    passed, actual = gate_engine._check_min_record_count(sample_dataset, 10.0)
    
    assert actual == 5.0
    assert passed is False


def test_check_max_duplicate_rate(gate_engine, tmp_path):
    dataset = tmp_path / "duplicates.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "duplicate"}) + "\n")
        f.write(json.dumps({"id": "2", "content": "duplicate"}) + "\n")
        f.write(json.dumps({"id": "3", "content": "unique"}) + "\n")
    
    passed, actual = gate_engine._check_max_duplicate_rate(dataset, 0.5)
    
    # 1 duplicate out of 3 = 33%
    assert actual > 0.3
    assert passed is True


def test_check_min_metadata_coverage(gate_engine, sample_dataset):
    passed, actual = gate_engine._check_min_metadata_coverage(sample_dataset, 0.8)
    
    # All 5 records have source_document
    assert actual == 1.0
    assert passed is True


def test_check_max_empty_content_rate(gate_engine, tmp_path):
    dataset = tmp_path / "empty.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "text"}) + "\n")
        f.write(json.dumps({"id": "2", "content": ""}) + "\n")
        f.write(json.dumps({"id": "3", "content": "more"}) + "\n")
    
    passed, actual = gate_engine._check_max_empty_content_rate(dataset, 0.5)
    
    # 1 empty out of 3 = 33%
    assert actual > 0.3
    assert passed is True


def test_check_min_avg_content_length(gate_engine, tmp_path):
    dataset = tmp_path / "lengths.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "short"}) + "\n")  # 5 chars
        f.write(json.dumps({"id": "2", "content": "longer text here"}) + "\n")  # 16 chars
    
    passed, actual = gate_engine._check_min_avg_content_length(dataset, 5.0)
    
    # Average: (5 + 16) / 2 = 10.5
    assert actual == 10.5
    assert passed is True


def test_execute_rule(gate_engine, sample_dataset):
    rule = GateRule(
        rule_id="min_quality_score",
        rule_name="Min Quality",
        rule_type="must_pass",
        threshold=70.0,
        message="Quality >= 70",
    )
    
    result = gate_engine.execute_rule(rule, sample_dataset)
    
    assert result.rule_id == "min_quality_score"
    assert result.passed is True
    assert result.actual_value == 73.0


def test_execute_rule_unknown(gate_engine, sample_dataset):
    rule = GateRule(
        rule_id="unknown_rule",
        rule_name="Unknown",
        rule_type="must_pass",
        threshold=50.0,
    )
    
    result = gate_engine.execute_rule(rule, sample_dataset)
    
    assert result.passed is False
    assert "Unknown rule" in result.message


def test_evaluate_gate_pass(gate_engine, sample_dataset):
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("min_quality_score", "Quality", "must_pass", 70.0))
    config.add_rule(GateRule("min_record_count", "Records", "must_pass", 3.0))
    
    report = gate_engine.evaluate_gate(config, sample_dataset, "test_dataset")
    
    assert report.dataset_id == "test_dataset"
    assert report.total_rules == 2
    assert report.passed_rules == 2
    assert report.failed_rules == 0
    assert report.gate_passed is True


def test_evaluate_gate_fail(gate_engine, sample_dataset):
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("min_quality_score", "Quality", "must_pass", 90.0))  # Will fail
    
    report = gate_engine.evaluate_gate(config, sample_dataset, "test_dataset")
    
    assert report.failed_rules == 1
    assert report.gate_passed is False


def test_evaluate_gate_with_warnings(gate_engine, sample_dataset):
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("min_quality_score", "Quality", "warn_only", 90.0))  # Will warn
    
    report = gate_engine.evaluate_gate(config, sample_dataset)
    
    assert report.warnings == 1
    assert report.gate_passed is True  # Warnings don't fail gate by default


def test_evaluate_gate_fail_on_warning(gate_engine, sample_dataset):
    config = QualityGateConfig(gate_id="test", gate_name="Test", fail_on_warning=True)
    config.add_rule(GateRule("min_quality_score", "Quality", "warn_only", 90.0))
    
    report = gate_engine.evaluate_gate(config, sample_dataset)
    
    assert report.warnings == 1
    assert report.gate_passed is False  # fail_on_warning=True


def test_create_standard_gate(gate_engine):
    config = gate_engine.create_standard_gate(strict=False)
    
    assert config.gate_id == "standard_quality_gate"
    assert len(config.rules) == 4
    assert any(r.rule_id == "min_quality_score" for r in config.rules)


def test_create_standard_gate_strict(gate_engine):
    config = gate_engine.create_standard_gate(strict=True)
    
    # Find quality rule
    quality_rule = next(r for r in config.rules if r.rule_id == "min_quality_score")
    
    assert quality_rule.threshold == 80.0  # Strict threshold
    assert quality_rule.rule_type == "must_pass"


def test_create_ci_gate(gate_engine):
    config = gate_engine.create_ci_gate()
    
    assert config.gate_id == "ci_quality_gate"
    assert len(config.rules) == 3
    assert any(r.rule_id == "min_record_count" for r in config.rules)
    assert any(r.rule_id == "max_empty_content_rate" for r in config.rules)


def test_save_load_config(gate_engine, tmp_path):
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("min_quality_score", "Quality", "must_pass", 70.0))
    
    config_file = tmp_path / "gate_config.json"
    gate_engine.save_config(config, config_file)
    
    assert config_file.exists()
    
    loaded = gate_engine.load_config(config_file)
    assert loaded.gate_id == "test"
    assert len(loaded.rules) == 1
    assert loaded.rules[0].rule_id == "min_quality_score"


def test_gate_with_empty_dataset(gate_engine, tmp_path):
    empty_dataset = tmp_path / "empty.jsonl"
    empty_dataset.touch()
    
    config = QualityGateConfig(gate_id="test", gate_name="Test")
    config.add_rule(GateRule("min_record_count", "Records", "must_pass", 1.0))
    
    report = gate_engine.evaluate_gate(config, empty_dataset)
    
    assert report.gate_passed is False


def test_gate_pass_rate_calculation():
    report = GateEvaluationReport(
        dataset_id="test",
        timestamp="2024-01-01T00:00:00",
        total_rules=10,
        passed_rules=7,
        failed_rules=3,
        warnings=0,
        gate_passed=False,
    )
    d = report.to_dict()
    assert d["pass_rate"] == 70.0
