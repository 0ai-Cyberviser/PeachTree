"""
PeachTree Dataset Migration Engine

Transform datasets between formats, migrate schemas, and perform field-level
transformations for dataset evolution and compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import json
import re


@dataclass
class MigrationRule:
    """Single migration transformation rule"""
    rule_type: str  # rename_field, add_field, remove_field, transform_field, change_type
    target_field: str
    params: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_type": self.rule_type,
            "target_field": self.target_field,
            "params": self.params,
        }


@dataclass
class MigrationPlan:
    """Complete migration plan with multiple rules"""
    plan_id: str
    source_schema: str
    target_schema: str
    rules: list[MigrationRule] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, rule: MigrationRule) -> None:
        """Add migration rule to plan"""
        self.rules.append(rule)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
            "rules": [r.to_dict() for r in self.rules],
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class MigrationResult:
    """Result of migration operation"""
    source_path: str
    output_path: str
    source_records: int
    migrated_records: int
    failed_records: int
    migration_plan: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "source_records": self.source_records,
            "migrated_records": self.migrated_records,
            "failed_records": self.failed_records,
            "migration_plan": self.migration_plan,
            "success_rate": (self.migrated_records / self.source_records * 100) if self.source_records > 0 else 0,
        }


class DatasetMigrationEngine:
    """Transform datasets with schema migrations and field transformations"""
    
    def __init__(self):
        """Initialize migration engine"""
        self.transformers: dict[str, Callable] = {
            "uppercase": lambda x: x.upper() if isinstance(x, str) else x,
            "lowercase": lambda x: x.lower() if isinstance(x, str) else x,
            "trim": lambda x: x.strip() if isinstance(x, str) else x,
            "int": lambda x: int(x) if x is not None else None,
            "float": lambda x: float(x) if x is not None else None,
            "str": lambda x: str(x) if x is not None else None,
            "bool": lambda x: bool(x) if x is not None else None,
        }
    
    def register_transformer(self, name: str, transformer: Callable) -> None:
        """Register custom field transformer"""
        self.transformers[name] = transformer
    
    def _apply_rename_field(self, record: dict[str, Any], rule: MigrationRule) -> dict[str, Any]:
        """Apply rename field rule"""
        old_name = rule.target_field
        new_name = rule.params.get("new_name", old_name)
        
        if old_name in record:
            record[new_name] = record.pop(old_name)
        
        return record
    
    def _apply_add_field(self, record: dict[str, Any], rule: MigrationRule) -> dict[str, Any]:
        """Apply add field rule"""
        field_name = rule.target_field
        default_value = rule.params.get("default_value")
        
        if field_name not in record:
            record[field_name] = default_value
        
        return record
    
    def _apply_remove_field(self, record: dict[str, Any], rule: MigrationRule) -> dict[str, Any]:
        """Apply remove field rule"""
        field_name = rule.target_field
        record.pop(field_name, None)
        return record
    
    def _apply_transform_field(self, record: dict[str, Any], rule: MigrationRule) -> dict[str, Any]:
        """Apply field transformation rule"""
        field_name = rule.target_field
        transformer_name = rule.params.get("transformer", "str")
        
        if field_name in record and transformer_name in self.transformers:
            try:
                transformer = self.transformers[transformer_name]
                record[field_name] = transformer(record[field_name])
            except (ValueError, TypeError):
                pass  # Keep original value on error
        
        return record
    
    def _apply_change_type(self, record: dict[str, Any], rule: MigrationRule) -> dict[str, Any]:
        """Apply type change rule"""
        field_name = rule.target_field
        target_type = rule.params.get("target_type", "str")
        
        if field_name in record and target_type in self.transformers:
            try:
                transformer = self.transformers[target_type]
                record[field_name] = transformer(record[field_name])
            except (ValueError, TypeError):
                pass  # Keep original value on error
        
        return record
    
    def apply_migration_rule(
        self,
        record: dict[str, Any],
        rule: MigrationRule,
    ) -> dict[str, Any]:
        """Apply single migration rule to record"""
        if rule.rule_type == "rename_field":
            return self._apply_rename_field(record, rule)
        elif rule.rule_type == "add_field":
            return self._apply_add_field(record, rule)
        elif rule.rule_type == "remove_field":
            return self._apply_remove_field(record, rule)
        elif rule.rule_type == "transform_field":
            return self._apply_transform_field(record, rule)
        elif rule.rule_type == "change_type":
            return self._apply_change_type(record, rule)
        else:
            return record
    
    def migrate_record(
        self,
        record: dict[str, Any],
        plan: MigrationPlan,
    ) -> dict[str, Any]:
        """Apply migration plan to single record"""
        migrated = record.copy()
        
        for rule in plan.rules:
            migrated = self.apply_migration_rule(migrated, rule)
        
        return migrated
    
    def migrate_dataset(
        self,
        source_path: Path | str,
        output_path: Path | str,
        plan: MigrationPlan,
    ) -> MigrationResult:
        """
        Migrate entire dataset using migration plan
        
        Args:
            source_path: Source dataset path
            output_path: Output dataset path
            plan: Migration plan with rules
        
        Returns:
            MigrationResult with statistics
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        source_count = 0
        migrated_count = 0
        failed_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                source_count += 1
                
                try:
                    record = json.loads(line)
                    migrated = self.migrate_record(record, plan)
                    f_out.write(json.dumps(migrated) + "\n")
                    migrated_count += 1
                except (json.JSONDecodeError, Exception):
                    failed_count += 1
        
        return MigrationResult(
            source_path=str(source_path),
            output_path=str(output_path),
            source_records=source_count,
            migrated_records=migrated_count,
            failed_records=failed_count,
            migration_plan=plan.plan_id,
        )
    
    def create_simple_plan(
        self,
        plan_id: str,
        source_schema: str = "v1",
        target_schema: str = "v2",
    ) -> MigrationPlan:
        """Create empty migration plan"""
        return MigrationPlan(
            plan_id=plan_id,
            source_schema=source_schema,
            target_schema=target_schema,
        )
    
    def create_field_rename_plan(
        self,
        plan_id: str,
        renames: dict[str, str],
    ) -> MigrationPlan:
        """Create plan for renaming fields"""
        plan = self.create_simple_plan(plan_id)
        
        for old_name, new_name in renames.items():
            plan.add_rule(MigrationRule(
                rule_type="rename_field",
                target_field=old_name,
                params={"new_name": new_name},
            ))
        
        return plan
    
    def create_type_migration_plan(
        self,
        plan_id: str,
        type_changes: dict[str, str],
    ) -> MigrationPlan:
        """Create plan for changing field types"""
        plan = self.create_simple_plan(plan_id)
        
        for field_name, target_type in type_changes.items():
            plan.add_rule(MigrationRule(
                rule_type="change_type",
                target_field=field_name,
                params={"target_type": target_type},
            ))
        
        return plan
    
    def save_plan(self, plan: MigrationPlan, output_path: Path | str) -> None:
        """Save migration plan to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan.to_json() + "\n", encoding="utf-8")
    
    def load_plan(self, plan_path: Path | str) -> MigrationPlan:
        """Load migration plan from file"""
        with open(plan_path) as f:
            data = json.load(f)
        
        plan = MigrationPlan(
            plan_id=data["plan_id"],
            source_schema=data["source_schema"],
            target_schema=data["target_schema"],
            metadata=data.get("metadata", {}),
        )
        
        for rule_data in data.get("rules", []):
            rule = MigrationRule(
                rule_type=rule_data["rule_type"],
                target_field=rule_data["target_field"],
                params=rule_data.get("params", {}),
            )
            plan.add_rule(rule)
        
        return plan
    
    def validate_plan(self, plan: MigrationPlan) -> list[str]:
        """Validate migration plan for errors"""
        errors = []
        
        if not plan.plan_id:
            errors.append("Migration plan must have a plan_id")
        
        if not plan.rules:
            errors.append("Migration plan must have at least one rule")
        
        for idx, rule in enumerate(plan.rules):
            if not rule.rule_type:
                errors.append(f"Rule {idx}: missing rule_type")
            
            if not rule.target_field:
                errors.append(f"Rule {idx}: missing target_field")
            
            if rule.rule_type == "rename_field" and "new_name" not in rule.params:
                errors.append(f"Rule {idx}: rename_field requires new_name parameter")
            
            if rule.rule_type in ("transform_field", "change_type"):
                transformer = rule.params.get("transformer") or rule.params.get("target_type")
                if transformer and transformer not in self.transformers:
                    errors.append(f"Rule {idx}: unknown transformer '{transformer}'")
        
        return errors
    
    def convert_format(
        self,
        source_path: Path | str,
        output_path: Path | str,
        source_format: str = "jsonl",
        target_format: str = "jsonl",
    ) -> int:
        """
        Convert dataset between formats
        
        Currently supports: jsonl (default)
        Future: csv, parquet, json
        
        Returns:
            Number of records converted
        """
        if source_format != "jsonl" or target_format != "jsonl":
            raise NotImplementedError(f"Format conversion {source_format} -> {target_format} not yet implemented")
        
        # For now, just copy (same format)
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if line.strip():
                    f_out.write(line)
                    count += 1
        
        return count
