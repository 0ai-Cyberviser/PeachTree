"""Dataset transformation pipeline for ETL workflows.

This module provides transformation capabilities including:
- Field mapping and renaming
- Content transformation (uppercase, lowercase, trim, etc.)
- Filtering records by conditions
- Aggregation and grouping
- Custom transformation functions
- Pipeline composition and chaining
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TransformationStep:
    """A single transformation step in the pipeline."""
    
    step_id: str
    step_type: str  # map, filter, transform, aggregate, custom
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "params": self.params,
        }


@dataclass
class TransformationPipeline:
    """A pipeline of transformation steps."""
    
    pipeline_id: str
    pipeline_name: str
    steps: List[TransformationStep] = field(default_factory=list)
    
    def add_step(self, step: TransformationStep) -> None:
        """Add a transformation step."""
        self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "steps": [s.to_dict() for s in self.steps],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TransformationResult:
    """Result of applying a transformation pipeline."""
    
    pipeline_id: str
    input_records: int
    output_records: int
    filtered_records: int
    transformed_fields: int
    timestamp: str
    success: bool
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "input_records": self.input_records,
            "output_records": self.output_records,
            "filtered_records": self.filtered_records,
            "transformed_fields": self.transformed_fields,
            "timestamp": self.timestamp,
            "success": self.success,
            "error_message": self.error_message,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DatasetTransformer:
    """Transform datasets using configurable pipelines."""
    
    def __init__(self) -> None:
        """Initialize the transformer."""
        pass
    
    def map_fields(
        self,
        record: Dict[str, Any],
        field_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """Map/rename fields in a record.
        
        Args:
            record: Input record
            field_mapping: Old field name -> new field name mapping
        
        Returns:
            Record with renamed fields
        """
        result = {}
        
        for old_field, new_field in field_mapping.items():
            if old_field in record:
                result[new_field] = record[old_field]
        
        # Keep unmapped fields
        for field, value in record.items():
            if field not in field_mapping:
                result[field] = value
        
        return result
    
    def filter_record(
        self,
        record: Dict[str, Any],
        condition: str,
    ) -> bool:
        """Check if record matches filter condition.
        
        Args:
            record: Input record
            condition: Filter condition (e.g., "quality_score >= 70")
        
        Returns:
            True if record matches condition
        """
        try:
            # Simple condition evaluation
            # Support: field >= value, field <= value, field == value, field != value
            
            if ">=" in condition:
                field, value = condition.split(">=")
                field = field.strip()
                value = float(value.strip())
                return record.get(field, 0) >= value
            elif "<=" in condition:
                field, value = condition.split("<=")
                field = field.strip()
                value = float(value.strip())
                return record.get(field, 0) <= value
            elif "==" in condition:
                field, value = condition.split("==")
                field = field.strip()
                value = value.strip().strip('"\'')
                return str(record.get(field, "")) == value
            elif "!=" in condition:
                field, value = condition.split("!=")
                field = field.strip()
                value = value.strip().strip('"\'')
                return str(record.get(field, "")) != value
            elif "contains" in condition:
                field, value = condition.split("contains")
                field = field.strip()
                value = value.strip().strip('"\'')
                return value in str(record.get(field, ""))
            else:
                return True
        except Exception:
            return True
    
    def transform_field(
        self,
        record: Dict[str, Any],
        field: str,
        transformation: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transform a field in a record.
        
        Args:
            record: Input record
            field: Field to transform
            transformation: Transformation type
            params: Transformation parameters
        
        Returns:
            Record with transformed field
        """
        if field not in record:
            return record
        
        value = record[field]
        params = params or {}
        
        if transformation == "uppercase":
            record[field] = str(value).upper()
        elif transformation == "lowercase":
            record[field] = str(value).lower()
        elif transformation == "trim":
            record[field] = str(value).strip()
        elif transformation == "prefix":
            prefix = params.get("prefix", "")
            record[field] = prefix + str(value)
        elif transformation == "suffix":
            suffix = params.get("suffix", "")
            record[field] = str(value) + suffix
        elif transformation == "replace":
            old = params.get("old", "")
            new = params.get("new", "")
            record[field] = str(value).replace(old, new)
        elif transformation == "regex_replace":
            pattern = params.get("pattern", "")
            replacement = params.get("replacement", "")
            record[field] = re.sub(pattern, replacement, str(value))
        elif transformation == "truncate":
            max_length = params.get("max_length", 100)
            record[field] = str(value)[:max_length]
        elif transformation == "multiply":
            factor = params.get("factor", 1.0)
            record[field] = float(value) * factor
        elif transformation == "add":
            amount = params.get("amount", 0.0)
            record[field] = float(value) + amount
        
        return record
    
    def add_field(
        self,
        record: Dict[str, Any],
        field: str,
        value: Any,
    ) -> Dict[str, Any]:
        """Add a new field to a record.
        
        Args:
            record: Input record
            field: New field name
            value: Field value
        
        Returns:
            Record with new field
        """
        record[field] = value
        return record
    
    def remove_field(
        self,
        record: Dict[str, Any],
        field: str,
    ) -> Dict[str, Any]:
        """Remove a field from a record.
        
        Args:
            record: Input record
            field: Field to remove
        
        Returns:
            Record without the field
        """
        record.pop(field, None)
        return record
    
    def apply_step(
        self,
        record: Dict[str, Any],
        step: TransformationStep,
    ) -> Optional[Dict[str, Any]]:
        """Apply a single transformation step.
        
        Args:
            record: Input record
            step: Transformation step
        
        Returns:
            Transformed record or None if filtered out
        """
        if step.step_type == "map":
            # Field mapping/renaming
            field_mapping = step.params.get("field_mapping", {})
            return self.map_fields(record, field_mapping)
        
        elif step.step_type == "filter":
            # Filter records
            condition = step.params.get("condition", "")
            if self.filter_record(record, condition):
                return record
            else:
                return None
        
        elif step.step_type == "transform":
            # Transform a field
            field = step.params.get("field", "")
            transformation = step.params.get("transformation", "")
            transform_params = step.params.get("params", {})
            return self.transform_field(record, field, transformation, transform_params)
        
        elif step.step_type == "add_field":
            # Add a new field
            field = step.params.get("field", "")
            value = step.params.get("value", "")
            return self.add_field(record, field, value)
        
        elif step.step_type == "remove_field":
            # Remove a field
            field = step.params.get("field", "")
            return self.remove_field(record, field)
        
        else:
            return record
    
    def apply_pipeline(
        self,
        input_path: Path,
        output_path: Path,
        pipeline: TransformationPipeline,
    ) -> TransformationResult:
        """Apply transformation pipeline to a dataset.
        
        Args:
            input_path: Input dataset path
            output_path: Output dataset path
            pipeline: Transformation pipeline
        
        Returns:
            TransformationResult with statistics
        """
        from datetime import datetime
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        input_count = 0
        output_count = 0
        filtered_count = 0
        transformed_fields = 0
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(input_path) as input_f, open(output_path, 'w') as output_f:
                for line in input_f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    input_count += 1
                    record = json.loads(line)
                    
                    # Apply each step in the pipeline
                    for step in pipeline.steps:
                        record = self.apply_step(record, step)
                        
                        if record is None:
                            # Record filtered out
                            filtered_count += 1
                            break
                        
                        if step.step_type == "transform":
                            transformed_fields += 1
                    
                    # Write output record if not filtered
                    if record is not None:
                        output_f.write(json.dumps(record) + "\n")
                        output_count += 1
            
            return TransformationResult(
                pipeline_id=pipeline.pipeline_id,
                input_records=input_count,
                output_records=output_count,
                filtered_records=filtered_count,
                transformed_fields=transformed_fields,
                timestamp=timestamp,
                success=True,
            )
            
        except Exception as e:
            return TransformationResult(
                pipeline_id=pipeline.pipeline_id,
                input_records=input_count,
                output_records=output_count,
                filtered_records=filtered_count,
                transformed_fields=transformed_fields,
                timestamp=timestamp,
                success=False,
                error_message=str(e),
            )
    
    def create_pipeline(
        self,
        pipeline_id: str,
        pipeline_name: str,
    ) -> TransformationPipeline:
        """Create a new transformation pipeline.
        
        Args:
            pipeline_id: Pipeline identifier
            pipeline_name: Pipeline name
        
        Returns:
            Empty transformation pipeline
        """
        return TransformationPipeline(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
        )
    
    def save_pipeline(
        self,
        pipeline: TransformationPipeline,
        output_path: Path,
    ) -> None:
        """Save pipeline to file.
        
        Args:
            pipeline: Transformation pipeline
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(pipeline.to_json())
    
    def load_pipeline(self, pipeline_path: Path) -> TransformationPipeline:
        """Load pipeline from file.
        
        Args:
            pipeline_path: Pipeline file path
        
        Returns:
            TransformationPipeline
        """
        with open(pipeline_path) as f:
            data = json.load(f)
        
        pipeline = TransformationPipeline(
            pipeline_id=data["pipeline_id"],
            pipeline_name=data["pipeline_name"],
        )
        
        for step_data in data.get("steps", []):
            step = TransformationStep(
                step_id=step_data["step_id"],
                step_type=step_data["step_type"],
                params=step_data.get("params", {}),
            )
            pipeline.add_step(step)
        
        return pipeline
    
    def create_standard_pipeline(
        self,
        pipeline_id: str = "standard_etl",
    ) -> TransformationPipeline:
        """Create a standard ETL pipeline.
        
        Args:
            pipeline_id: Pipeline identifier
        
        Returns:
            Standard transformation pipeline
        """
        pipeline = self.create_pipeline(pipeline_id, "Standard ETL Pipeline")
        
        # Step 1: Filter out low quality records
        pipeline.add_step(TransformationStep(
            step_id="filter_quality",
            step_type="filter",
            params={"condition": "quality_score >= 70"},
        ))
        
        # Step 2: Trim content
        pipeline.add_step(TransformationStep(
            step_id="trim_content",
            step_type="transform",
            params={"field": "content", "transformation": "trim"},
        ))
        
        # Step 3: Add processing timestamp
        pipeline.add_step(TransformationStep(
            step_id="add_timestamp",
            step_type="add_field",
            params={"field": "processed_at", "value": "{{timestamp}}"},
        ))
        
        return pipeline
