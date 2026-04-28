"""Dataset enrichment for augmentation and enhancement.

Provides data enrichment, augmentation, and enhancement capabilities
for improving dataset quality and coverage.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import hashlib


class EnrichmentType(Enum):
    """Enrichment operation types."""
    AUGMENT = "augment"
    ENHANCE = "enhance"
    EXPAND = "expand"
    ANNOTATE = "annotate"
    DERIVE = "derive"


class EnrichmentStrategy(Enum):
    """Enrichment strategies."""
    RULE_BASED = "rule_based"
    ML_BASED = "ml_based"
    HYBRID = "hybrid"
    EXTERNAL_API = "external_api"


@dataclass
class EnrichmentRule:
    """Single enrichment rule."""
    rule_id: str
    rule_type: EnrichmentType
    source_field: str
    target_field: str
    strategy: EnrichmentStrategy
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "strategy": self.strategy.value,
            "config": self.config,
        }


@dataclass
class EnrichmentResult:
    """Enrichment operation result."""
    enrichment_id: str
    total_records: int
    enriched_records: int
    failed_records: int
    new_fields_added: List[str]
    enrichment_time_ms: float
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enrichment_id": self.enrichment_id,
            "total_records": self.total_records,
            "enriched_records": self.enriched_records,
            "failed_records": self.failed_records,
            "new_fields_added": self.new_fields_added,
            "enrichment_time_ms": self.enrichment_time_ms,
            "success": self.success,
        }


class DatasetEnricher:
    """Main dataset enrichment engine."""
    
    def __init__(self):
        """Initialize enricher."""
        self.rules: List[EnrichmentRule] = []
    
    def add_rule(self, rule: EnrichmentRule) -> None:
        """Add enrichment rule."""
        self.rules.append(rule)
    
    def enrich_dataset(
        self,
        dataset_path: Path,
        output_path: Path,
    ) -> EnrichmentResult:
        """Enrich dataset with all rules."""
        start_time = datetime.now()
        
        records = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        enriched_count = 0
        failed_count = 0
        new_fields = set()
        
        enriched_records = []
        for record in records:
            try:
                enriched = self._enrich_record(record)
                enriched_records.append(enriched)
                enriched_count += 1
                
                # Track new fields
                for key in enriched.keys():
                    if key not in record:
                        new_fields.add(key)
            except Exception:
                enriched_records.append(record)
                failed_count += 1
        
        # Write enriched dataset
        with open(output_path, "w") as f:
            for record in enriched_records:
                f.write(json.dumps(record) + "\n")
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        enrichment_id = hashlib.sha256(
            f"{dataset_path}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return EnrichmentResult(
            enrichment_id=enrichment_id,
            total_records=len(records),
            enriched_records=enriched_count,
            failed_records=failed_count,
            new_fields_added=list(new_fields),
            enrichment_time_ms=elapsed,
            success=failed_count == 0,
        )
    
    def _enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich single record with all rules."""
        enriched = record.copy()
        
        for rule in self.rules:
            if rule.source_field in enriched:
                source_value = enriched[rule.source_field]
                
                if rule.rule_type == EnrichmentType.DERIVE:
                    # Derive new field from source
                    enriched[rule.target_field] = self._derive_field(
                        source_value, rule.config
                    )
                elif rule.rule_type == EnrichmentType.AUGMENT:
                    # Augment existing field
                    enriched[rule.target_field] = self._augment_field(
                        source_value, rule.config
                    )
                elif rule.rule_type == EnrichmentType.ANNOTATE:
                    # Add annotation
                    enriched[rule.target_field] = self._annotate_field(
                        source_value, rule.config
                    )
        
        return enriched
    
    def _derive_field(self, value: Any, config: Dict[str, Any]) -> Any:
        """Derive new field value."""
        # Simple derivation logic
        if isinstance(value, str):
            return len(value)  # Example: derive length
        return value
    
    def _augment_field(self, value: Any, config: Dict[str, Any]) -> Any:
        """Augment field value."""
        # Simple augmentation logic
        if isinstance(value, str):
            return value.upper()  # Example: uppercase
        return value
    
    def _annotate_field(self, value: Any, config: Dict[str, Any]) -> Any:
        """Annotate field value."""
        # Simple annotation logic
        return {"original": value, "annotated": True}


class TextEnricher:
    """Text-specific enrichment operations."""
    
    def __init__(self):
        """Initialize text enricher."""
        pass
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text."""
        # Placeholder for entity extraction
        entities = []
        
        # Simple word extraction as example
        words = text.split()
        for i, word in enumerate(words):
            if word.isupper() and len(word) > 1:
                entities.append({
                    "text": word,
                    "type": "ACRONYM",
                    "position": i,
                })
        
        return entities
    
    def add_metadata(self, text: str) -> Dict[str, Any]:
        """Add metadata to text."""
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "char_count": len(text),
            "has_numbers": any(c.isdigit() for c in text),
            "has_uppercase": any(c.isupper() for c in text),
        }


class DataAugmenter:
    """Data augmentation operations."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize augmenter."""
        self.seed = seed
    
    def augment_text(self, text: str, strategy: str = "synonym") -> List[str]:
        """Generate augmented text variations."""
        variations = [text]
        
        if strategy == "case":
            variations.append(text.upper())
            variations.append(text.lower())
            variations.append(text.title())
        
        return variations
    
    def augment_numeric(self, value: float, noise_level: float = 0.1) -> List[float]:
        """Generate augmented numeric variations."""
        variations = [value]
        
        # Add noise
        variations.append(value * (1 + noise_level))
        variations.append(value * (1 - noise_level))
        
        return variations


class FieldDeriver:
    """Derive new fields from existing ones."""
    
    def __init__(self):
        """Initialize field deriver."""
        pass
    
    def derive_length_field(self, record: Dict[str, Any], source_field: str) -> int:
        """Derive length field."""
        value = record.get(source_field)
        if isinstance(value, str):
            return len(value)
        elif isinstance(value, (list, dict)):
            return len(value)
        return 0
    
    def derive_type_field(self, record: Dict[str, Any], source_field: str) -> str:
        """Derive type field."""
        value = record.get(source_field)
        return type(value).__name__
    
    def derive_hash_field(self, record: Dict[str, Any], source_field: str) -> str:
        """Derive hash field."""
        value = record.get(source_field)
        if value is not None:
            value_str = str(value)
            return hashlib.sha256(value_str.encode()).hexdigest()[:16]
        return ""


class EnrichmentPipeline:
    """Pipeline for multiple enrichment operations."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.stages: List[DatasetEnricher] = []
    
    def add_stage(self, enricher: DatasetEnricher) -> None:
        """Add enrichment stage."""
        self.stages.append(enricher)
    
    def execute(
        self,
        dataset_path: Path,
        output_path: Path,
    ) -> List[EnrichmentResult]:
        """Execute all enrichment stages."""
        results = []
        current_input = dataset_path
        
        for i, enricher in enumerate(self.stages):
            if i == len(self.stages) - 1:
                # Last stage writes to final output
                stage_output = output_path
            else:
                # Intermediate stages write to temp files
                stage_output = output_path.parent / f"{output_path.stem}_stage{i}.jsonl"
            
            result = enricher.enrich_dataset(current_input, stage_output)
            results.append(result)
            current_input = stage_output
        
        return results


class EnrichmentValidator:
    """Validate enrichment results."""
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    def validate_enrichment(
        self,
        original_path: Path,
        enriched_path: Path,
    ) -> Dict[str, Any]:
        """Validate enrichment quality."""
        # Load datasets
        original_records = []
        with open(original_path) as f:
            for line in f:
                if line.strip():
                    original_records.append(json.loads(line))
        
        enriched_records = []
        with open(enriched_path) as f:
            for line in f:
                if line.strip():
                    enriched_records.append(json.loads(line))
        
        # Validation checks
        validation = {
            "record_count_match": len(original_records) == len(enriched_records),
            "original_count": len(original_records),
            "enriched_count": len(enriched_records),
            "new_fields": [],
            "modified_fields": [],
        }
        
        if len(original_records) > 0 and len(enriched_records) > 0:
            orig_fields = set(original_records[0].keys())
            enr_fields = set(enriched_records[0].keys())
            
            validation["new_fields"] = list(enr_fields - orig_fields)
            validation["modified_fields"] = list(enr_fields & orig_fields)
        
        return validation
