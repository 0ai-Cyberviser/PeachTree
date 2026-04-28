"""
PeachTree Dataset Validation Framework

Validate dataset schemas, constraints, and quality rules. Provides extensible
validation engine for ensuring dataset integrity and compliance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import json
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity level"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationViolation:
    """Single validation violation"""
    level: ValidationLevel
    rule_name: str
    message: str
    record_id: str | None = None
    field_name: str | None = None
    value: Any = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "rule_name": self.rule_name,
            "message": self.message,
            "record_id": self.record_id,
            "field_name": self.field_name,
            "value": str(self.value) if self.value is not None else None,
        }


@dataclass
class ValidationReport:
    """Complete validation report"""
    dataset_path: str
    total_records: int
    validated_records: int
    violations: list[ValidationViolation] = field(default_factory=list)
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    validation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_violation(self, violation: ValidationViolation) -> None:
        """Add a violation to the report"""
        self.violations.append(violation)
        
        if violation.level == ValidationLevel.ERROR:
            self.errors += 1
        elif violation.level == ValidationLevel.WARNING:
            self.warnings += 1
        elif violation.level == ValidationLevel.INFO:
            self.infos += 1
    
    def is_valid(self) -> bool:
        """Check if dataset is valid (no errors)"""
        return self.errors == 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "total_records": self.total_records,
            "validated_records": self.validated_records,
            "is_valid": self.is_valid(),
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "violations": [v.to_dict() for v in self.violations],
            "validation_timestamp": self.validation_timestamp,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown validation report"""
        lines = [
            "# Dataset Validation Report",
            "",
            f"**Dataset:** {self.dataset_path}",
            f"**Total Records:** {self.total_records:,}",
            f"**Validated:** {self.validated_records:,}",
            f"**Status:** {'✅ VALID' if self.is_valid() else '❌ INVALID'}",
            f"**Timestamp:** {self.validation_timestamp}",
            "",
            "## Summary",
            "",
            f"- **Errors:** {self.errors}",
            f"- **Warnings:** {self.warnings}",
            f"- **Info:** {self.infos}",
            "",
        ]
        
        if self.violations:
            lines.extend(["## Violations", ""])
            
            # Group by level
            for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
                level_violations = [v for v in self.violations if v.level == level]
                if not level_violations:
                    continue
                
                icon = "❌" if level == ValidationLevel.ERROR else "⚠️" if level == ValidationLevel.WARNING else "ℹ️"
                lines.extend([f"### {icon} {level.value.upper()}", ""])
                
                for v in level_violations[:20]:  # Limit to first 20
                    lines.append(f"- **{v.rule_name}**: {v.message}")
                    if v.record_id:
                        lines.append(f"  - Record: `{v.record_id}`")
                    if v.field_name:
                        lines.append(f"  - Field: `{v.field_name}`")
                
                if len(level_violations) > 20:
                    lines.append(f"- ... and {len(level_violations) - 20} more {level.value}s")
                
                lines.append("")
        
        return "\n".join(lines)


class ValidationRule:
    """Base validation rule"""
    
    def __init__(self, name: str, level: ValidationLevel = ValidationLevel.ERROR):
        self.name = name
        self.level = level
    
    def validate(self, record: dict[str, Any]) -> list[ValidationViolation]:
        """Validate a single record. Override in subclasses."""
        raise NotImplementedError


class RequiredFieldRule(ValidationRule):
    """Validate that required fields are present"""
    
    def __init__(self, fields: list[str], level: ValidationLevel = ValidationLevel.ERROR):
        super().__init__("required_fields", level)
        self.fields = fields
    
    def validate(self, record: dict[str, Any]) -> list[ValidationViolation]:
        violations = []
        
        for field in self.fields:
            if field not in record or record[field] is None or record[field] == "":
                violations.append(ValidationViolation(
                    level=self.level,
                    rule_name=self.name,
                    message=f"Required field '{field}' is missing or empty",
                    record_id=record.get("id"),
                    field_name=field,
                ))
        
        return violations


class FieldTypeRule(ValidationRule):
    """Validate field types"""
    
    def __init__(self, field_types: dict[str, type], level: ValidationLevel = ValidationLevel.ERROR):
        super().__init__("field_types", level)
        self.field_types = field_types
    
    def validate(self, record: dict[str, Any]) -> list[ValidationViolation]:
        violations = []
        
        for field, expected_type in self.field_types.items():
            if field in record and record[field] is not None:
                if not isinstance(record[field], expected_type):
                    violations.append(ValidationViolation(
                        level=self.level,
                        rule_name=self.name,
                        message=f"Field '{field}' has wrong type. Expected {expected_type.__name__}, got {type(record[field]).__name__}",
                        record_id=record.get("id"),
                        field_name=field,
                        value=record[field],
                    ))
        
        return violations


class ContentLengthRule(ValidationRule):
    """Validate content length constraints"""
    
    def __init__(
        self,
        field: str,
        min_length: int | None = None,
        max_length: int | None = None,
        level: ValidationLevel = ValidationLevel.WARNING,
    ):
        super().__init__("content_length", level)
        self.field = field
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, record: dict[str, Any]) -> list[ValidationViolation]:
        violations = []
        
        if self.field not in record:
            return violations
        
        content = str(record[self.field])
        length = len(content)
        
        if self.min_length is not None and length < self.min_length:
            violations.append(ValidationViolation(
                level=self.level,
                rule_name=self.name,
                message=f"Field '{self.field}' is too short. Length: {length}, minimum: {self.min_length}",
                record_id=record.get("id"),
                field_name=self.field,
            ))
        
        if self.max_length is not None and length > self.max_length:
            violations.append(ValidationViolation(
                level=self.level,
                rule_name=self.name,
                message=f"Field '{self.field}' is too long. Length: {length}, maximum: {self.max_length}",
                record_id=record.get("id"),
                field_name=self.field,
            ))
        
        return violations


class CustomRule(ValidationRule):
    """Custom validation rule with user-defined function"""
    
    def __init__(
        self,
        name: str,
        validator_func: Callable[[dict[str, Any]], str | None],
        level: ValidationLevel = ValidationLevel.ERROR,
    ):
        super().__init__(name, level)
        self.validator_func = validator_func
    
    def validate(self, record: dict[str, Any]) -> list[ValidationViolation]:
        violations = []
        
        error_message = self.validator_func(record)
        if error_message:
            violations.append(ValidationViolation(
                level=self.level,
                rule_name=self.name,
                message=error_message,
                record_id=record.get("id"),
            ))
        
        return violations


class DatasetValidator:
    """Validate datasets using configurable rules"""
    
    def __init__(self):
        self.rules: list[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule"""
        self.rules.append(rule)
    
    def validate_record(self, record: dict[str, Any]) -> list[ValidationViolation]:
        """Validate a single record against all rules"""
        violations = []
        
        for rule in self.rules:
            violations.extend(rule.validate(record))
        
        return violations
    
    def validate_dataset(
        self,
        dataset_path: Path | str,
        stop_on_error: bool = False,
    ) -> ValidationReport:
        """
        Validate entire dataset
        
        Args:
            dataset_path: Dataset path to validate
            stop_on_error: Stop validation on first error
        
        Returns:
            ValidationReport with all violations
        """
        dataset_path = Path(dataset_path)
        
        report = ValidationReport(
            dataset_path=str(dataset_path),
            total_records=0,
            validated_records=0,
        )
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                report.total_records += 1
                record = json.loads(line)
                
                violations = self.validate_record(record)
                
                for violation in violations:
                    report.add_violation(violation)
                    
                    if stop_on_error and violation.level == ValidationLevel.ERROR:
                        report.validated_records += 1
                        return report
                
                report.validated_records += 1
        
        return report
    
    def validate_with_schema(
        self,
        dataset_path: Path | str,
        schema: dict[str, Any],
    ) -> ValidationReport:
        """
        Validate dataset using a JSON schema
        
        Args:
            dataset_path: Dataset path
            schema: Schema definition with required_fields, field_types, constraints
        
        Returns:
            ValidationReport
        """
        # Clear existing rules
        self.rules = []
        
        # Add required fields rule
        if "required_fields" in schema:
            self.add_rule(RequiredFieldRule(schema["required_fields"]))
        
        # Add field type rules
        if "field_types" in schema:
            type_map = {
                "string": str,
                "integer": int,
                "float": float,
                "boolean": bool,
                "dict": dict,
                "list": list,
            }
            
            field_types = {}
            for field, type_name in schema["field_types"].items():
                if type_name in type_map:
                    field_types[field] = type_map[type_name]
            
            if field_types:
                self.add_rule(FieldTypeRule(field_types))
        
        # Add content length constraints
        if "constraints" in schema:
            for constraint in schema["constraints"]:
                if constraint["type"] == "length":
                    self.add_rule(ContentLengthRule(
                        constraint["field"],
                        min_length=constraint.get("min"),
                        max_length=constraint.get("max"),
                    ))
        
        return self.validate_dataset(dataset_path)
