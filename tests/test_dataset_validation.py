"""
Tests for dataset_validation module
"""
from pathlib import Path
import pytest
import json
from peachtree.dataset_validation import (
    DatasetValidator,
    ValidationReport,
    ValidationViolation,
    ValidationLevel,
    RequiredFieldRule,
    FieldTypeRule,
    ContentLengthRule,
    CustomRule,
)


@pytest.fixture
def test_dataset(tmp_path):
    """Create test dataset"""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": "1", "content": "Short"},
        {"id": "2", "content": "Medium length content here"},
        {"id": "3", "content": "Very long content " * 10, "source_repo": "repo1"},
        {"id": "4"},  # Missing content
        {"id": "5", "content": "Valid content", "source_repo": "repo2", "digest": "hash123"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_validation_violation_creation():
    """Test ValidationViolation dataclass"""
    violation = ValidationViolation(
        level=ValidationLevel.ERROR,
        rule_name="test_rule",
        message="Test error",
        record_id="123",
        field_name="content",
    )
    
    assert violation.level == ValidationLevel.ERROR
    assert violation.to_dict()["level"] == "error"


def test_validation_report_creation():
    """Test ValidationReport initialization"""
    report = ValidationReport(
        dataset_path="test.jsonl",
        total_records=100,
        validated_records=100,
    )
    
    assert report.total_records == 100
    assert report.is_valid()  # No errors yet


def test_validation_report_add_violation():
    """Test adding violations to report"""
    report = ValidationReport("test.jsonl", 10, 10)
    
    violation = ValidationViolation(
        ValidationLevel.ERROR,
        "test",
        "Test error",
    )
    
    report.add_violation(violation)
    
    assert len(report.violations) == 1
    assert report.errors == 1
    assert not report.is_valid()


def test_validation_report_tracks_levels():
    """Test that report tracks all violation levels"""
    report = ValidationReport("test.jsonl", 10, 10)
    
    report.add_violation(ValidationViolation(ValidationLevel.ERROR, "r1", "Error"))
    report.add_violation(ValidationViolation(ValidationLevel.WARNING, "r2", "Warning"))
    report.add_violation(ValidationViolation(ValidationLevel.INFO, "r3", "Info"))
    
    assert report.errors == 1
    assert report.warnings == 1
    assert report.infos == 1


def test_validation_report_to_json():
    """Test JSON serialization"""
    report = ValidationReport("test.jsonl", 5, 5)
    report.add_violation(ValidationViolation(ValidationLevel.ERROR, "test", "msg"))
    
    json_str = report.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["total_records"] == 5
    assert parsed["is_valid"] is False
    assert len(parsed["violations"]) == 1


def test_validation_report_to_markdown():
    """Test markdown generation"""
    report = ValidationReport("test.jsonl", 10, 10)
    report.add_violation(ValidationViolation(ValidationLevel.ERROR, "test", "error message"))
    
    markdown = report.to_markdown()
    
    assert "# Dataset Validation Report" in markdown
    assert "❌ INVALID" in markdown
    assert "error message" in markdown


def test_required_field_rule():
    """Test required field validation"""
    rule = RequiredFieldRule(["id", "content"])
    
    # Valid record
    valid = {"id": "1", "content": "text"}
    violations = rule.validate(valid)
    assert len(violations) == 0
    
    # Missing field
    invalid = {"id": "1"}
    violations = rule.validate(invalid)
    assert len(violations) == 1
    assert violations[0].field_name == "content"


def test_required_field_rule_empty_value():
    """Test that empty values are caught"""
    rule = RequiredFieldRule(["content"])
    
    record = {"content": ""}
    violations = rule.validate(record)
    
    assert len(violations) == 1


def test_field_type_rule():
    """Test field type validation"""
    rule = FieldTypeRule({
        "id": str,
        "count": int,
        "score": float,
    })
    
    # Valid
    valid = {"id": "123", "count": 10, "score": 95.5}
    violations = rule.validate(valid)
    assert len(violations) == 0
    
    # Wrong type
    invalid = {"id": 123, "count": "ten"}
    violations = rule.validate(invalid)
    assert len(violations) == 2


def test_content_length_rule_min():
    """Test minimum content length"""
    rule = ContentLengthRule("content", min_length=10)
    
    short = {"content": "short"}
    violations = rule.validate(short)
    
    assert len(violations) == 1
    assert "too short" in violations[0].message


def test_content_length_rule_max():
    """Test maximum content length"""
    rule = ContentLengthRule("content", max_length=20)
    
    long_record = {"content": "x" * 50}
    violations = rule.validate(long_record)
    
    assert len(violations) == 1
    assert "too long" in violations[0].message


def test_content_length_rule_range():
    """Test content length within range"""
    rule = ContentLengthRule("content", min_length=5, max_length=20)
    
    # Valid
    valid = {"content": "valid content"}
    violations = rule.validate(valid)
    assert len(violations) == 0
    
    # Too short
    short = {"content": "hi"}
    violations = rule.validate(short)
    assert len(violations) == 1
    
    # Too long
    long_record = {"content": "x" * 50}
    violations = rule.validate(long_record)
    assert len(violations) == 1


def test_custom_rule():
    """Test custom validation rule"""
    def validator(record):
        if record.get("value", 0) < 0:
            return "Value must be non-negative"
        return None
    
    rule = CustomRule("positive_value", validator)
    
    # Valid
    valid = {"value": 10}
    violations = rule.validate(valid)
    assert len(violations) == 0
    
    # Invalid
    invalid = {"value": -5}
    violations = rule.validate(invalid)
    assert len(violations) == 1


def test_dataset_validator_add_rule():
    """Test adding rules to validator"""
    validator = DatasetValidator()
    rule = RequiredFieldRule(["id"])
    
    validator.add_rule(rule)
    
    assert len(validator.rules) == 1


def test_dataset_validator_validate_record():
    """Test validating a single record"""
    validator = DatasetValidator()
    validator.add_rule(RequiredFieldRule(["id", "content"]))
    
    record = {"id": "1"}  # Missing content
    violations = validator.validate_record(record)
    
    assert len(violations) == 1


def test_dataset_validator_validate_dataset(test_dataset):
    """Test validating entire dataset"""
    validator = DatasetValidator()
    validator.add_rule(RequiredFieldRule(["id", "content"]))
    
    report = validator.validate_dataset(test_dataset)
    
    assert report.total_records == 5
    assert report.validated_records == 5
    assert report.errors > 0  # Record 4 missing content


def test_dataset_validator_stop_on_error(test_dataset):
    """Test stop_on_error flag"""
    validator = DatasetValidator()
    validator.add_rule(RequiredFieldRule(["content"]))
    
    report = validator.validate_dataset(test_dataset, stop_on_error=True)
    
    # Should stop on first record missing content
    assert report.validated_records < report.total_records


def test_dataset_validator_with_schema(test_dataset):
    """Test schema-based validation"""
    validator = DatasetValidator()
    
    schema = {
        "required_fields": ["id", "content"],
        "field_types": {
            "id": "string",
            "content": "string",
        },
        "constraints": [
            {"type": "length", "field": "content", "min": 5}
        ],
    }
    
    report = validator.validate_with_schema(test_dataset, schema)
    
    assert report.total_records == 5
    # Should have violations for missing content and short content
    assert len(report.violations) > 0


def test_validation_with_multiple_rules(test_dataset):
    """Test validation with multiple rules"""
    validator = DatasetValidator()
    validator.add_rule(RequiredFieldRule(["id"]))
    validator.add_rule(ContentLengthRule("content", min_length=10))
    
    report = validator.validate_dataset(test_dataset)
    
    # Should catch both missing and short content
    assert len(report.violations) >= 2


def test_validation_warning_level():
    """Test validation with warning level"""
    rule = ContentLengthRule("content", min_length=20, level=ValidationLevel.WARNING)
    
    record = {"content": "short"}
    violations = rule.validate(record)
    
    assert len(violations) == 1
    assert violations[0].level == ValidationLevel.WARNING


def test_validation_info_level():
    """Test validation with info level"""
    def info_check(record):
        if "metadata" not in record:
            return "Metadata is recommended"
        return None
    
    rule = CustomRule("metadata_check", info_check, level=ValidationLevel.INFO)
    
    record = {"id": "1"}
    violations = rule.validate(record)
    
    assert len(violations) == 1
    assert violations[0].level == ValidationLevel.INFO


def test_validation_report_summary_counts():
    """Test that summary includes violation counts"""
    report = ValidationReport("test.jsonl", 100, 100)
    
    for _ in range(5):
        report.add_violation(ValidationViolation(ValidationLevel.ERROR, "r1", "e"))
    for _ in range(3):
        report.add_violation(ValidationViolation(ValidationLevel.WARNING, "r2", "w"))
    
    markdown = report.to_markdown()
    
    assert "Errors:** 5" in markdown
    assert "Warnings:** 3" in markdown
