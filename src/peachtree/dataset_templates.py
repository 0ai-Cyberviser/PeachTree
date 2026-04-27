"""Dataset templates for common patterns and configurations."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TemplateCategory(Enum):
    """Categories of dataset templates."""
    
    GENERAL = "general"
    CYBERSECURITY = "cybersecurity"
    NLP = "nlp"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    TIME_SERIES = "time_series"
    SCIENTIFIC = "scientific"


class TemplateComplexity(Enum):
    """Complexity levels of templates."""
    
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class TemplateMetadata:
    """Metadata for a dataset template."""
    
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    complexity: TemplateComplexity
    author: str
    version: str
    created_at: str
    updated_at: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "complexity": self.complexity.value,
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
        }


@dataclass
class DatasetTemplate:
    """A dataset template with configuration and settings."""
    
    metadata: TemplateMetadata
    config: Dict[str, Any]
    pipeline_steps: List[Dict[str, Any]] = field(default_factory=list)
    quality_gates: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    example_data: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "config": self.config,
            "pipeline_steps": self.pipeline_steps,
            "quality_gates": self.quality_gates,
            "validation_rules": self.validation_rules,
            "example_data": self.example_data,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class DatasetTemplateManager:
    """Manager for dataset templates."""
    
    def __init__(self):
        """Initialize the template manager."""
        self.templates: Dict[str, DatasetTemplate] = {}
        self._register_builtin_templates()
    
    def _register_builtin_templates(self) -> None:
        """Register built-in templates."""
        # Cybersecurity training template
        self._register_cybersecurity_training()
        
        # NLP text classification template
        self._register_nlp_classification()
        
        # Question-answering template
        self._register_question_answering()
        
        # Code generation template
        self._register_code_generation()
        
        # Instruction tuning template
        self._register_instruction_tuning()
    
    def _register_cybersecurity_training(self) -> None:
        """Register cybersecurity training template."""
        metadata = TemplateMetadata(
            template_id="cybersecurity_training_v1",
            name="Cybersecurity Training Dataset",
            description="Template for creating cybersecurity training datasets with CVEs, exploits, and mitigations",
            category=TemplateCategory.CYBERSECURITY,
            complexity=TemplateComplexity.INTERMEDIATE,
            author="PeachTree",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            tags=["cybersecurity", "cve", "exploits", "training"],
        )
        
        config = {
            "domain": "cybersecurity",
            "format": "instruction",
            "min_quality_score": 80.0,
            "dedup_threshold": 0.9,
            "required_fields": ["cve_id", "description", "mitigation"],
        }
        
        pipeline_steps = [
            {"step": "ingest", "source_type": "cve_database"},
            {"step": "enrich", "enrichment_type": "exploit_details"},
            {"step": "validate", "validation_type": "cve_format"},
            {"step": "quality_check", "min_score": 80.0},
            {"step": "dedup", "method": "content_hash"},
            {"step": "export", "format": "chatml"},
        ]
        
        quality_gates = [
            {"gate": "min_records", "threshold": 100},
            {"gate": "avg_quality_score", "threshold": 80.0},
            {"gate": "max_duplicate_ratio", "threshold": 0.1},
        ]
        
        validation_rules = [
            {"rule": "required_fields", "fields": ["cve_id", "description"]},
            {"rule": "cve_format", "pattern": "^CVE-\\d{4}-\\d{4,}$"},
            {"rule": "min_description_length", "chars": 50},
        ]
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
            pipeline_steps=pipeline_steps,
            quality_gates=quality_gates,
            validation_rules=validation_rules,
        )
        
        self.templates[metadata.template_id] = template
    
    def _register_nlp_classification(self) -> None:
        """Register NLP text classification template."""
        metadata = TemplateMetadata(
            template_id="nlp_text_classification_v1",
            name="Text Classification Dataset",
            description="Template for text classification tasks with labels and categories",
            category=TemplateCategory.NLP,
            complexity=TemplateComplexity.BASIC,
            author="PeachTree",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            tags=["nlp", "classification", "text"],
        )
        
        config = {
            "domain": "nlp",
            "format": "labeled",
            "min_quality_score": 75.0,
            "required_fields": ["text", "label"],
            "label_balance_threshold": 0.1,
        }
        
        pipeline_steps = [
            {"step": "ingest", "source_type": "text_corpus"},
            {"step": "label", "labeling_method": "manual"},
            {"step": "validate", "validation_type": "label_consistency"},
            {"step": "balance", "method": "oversample"},
            {"step": "split", "ratios": {"train": 0.8, "val": 0.1, "test": 0.1}},
        ]
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
            pipeline_steps=pipeline_steps,
        )
        
        self.templates[metadata.template_id] = template
    
    def _register_question_answering(self) -> None:
        """Register question-answering template."""
        metadata = TemplateMetadata(
            template_id="question_answering_v1",
            name="Question Answering Dataset",
            description="Template for QA datasets with context, questions, and answers",
            category=TemplateCategory.NLP,
            complexity=TemplateComplexity.INTERMEDIATE,
            author="PeachTree",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            tags=["qa", "nlp", "reading-comprehension"],
        )
        
        config = {
            "domain": "qa",
            "format": "qa_pairs",
            "min_quality_score": 85.0,
            "required_fields": ["context", "question", "answer"],
        }
        
        pipeline_steps = [
            {"step": "ingest", "source_type": "documents"},
            {"step": "generate_qa", "method": "automatic"},
            {"step": "validate", "validation_type": "answer_in_context"},
            {"step": "quality_check", "min_score": 85.0},
        ]
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
            pipeline_steps=pipeline_steps,
        )
        
        self.templates[metadata.template_id] = template
    
    def _register_code_generation(self) -> None:
        """Register code generation template."""
        metadata = TemplateMetadata(
            template_id="code_generation_v1",
            name="Code Generation Dataset",
            description="Template for code generation tasks with prompts and solutions",
            category=TemplateCategory.NLP,
            complexity=TemplateComplexity.ADVANCED,
            author="PeachTree",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            tags=["code", "generation", "programming"],
        )
        
        config = {
            "domain": "code",
            "format": "instruction",
            "min_quality_score": 90.0,
            "required_fields": ["prompt", "code", "language"],
            "supported_languages": ["python", "javascript", "go", "rust"],
        }
        
        pipeline_steps = [
            {"step": "ingest", "source_type": "code_repos"},
            {"step": "extract", "extraction_method": "function_level"},
            {"step": "generate_prompt", "method": "docstring_to_prompt"},
            {"step": "validate", "validation_type": "syntax_check"},
            {"step": "test", "testing_method": "unit_tests"},
        ]
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
            pipeline_steps=pipeline_steps,
        )
        
        self.templates[metadata.template_id] = template
    
    def _register_instruction_tuning(self) -> None:
        """Register instruction tuning template."""
        metadata = TemplateMetadata(
            template_id="instruction_tuning_v1",
            name="Instruction Tuning Dataset",
            description="Template for instruction-following datasets with diverse tasks",
            category=TemplateCategory.GENERAL,
            complexity=TemplateComplexity.ADVANCED,
            author="PeachTree",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            tags=["instruction", "tuning", "general"],
        )
        
        config = {
            "domain": "general",
            "format": "instruction",
            "min_quality_score": 85.0,
            "required_fields": ["instruction", "response"],
            "diversity_threshold": 0.7,
        }
        
        pipeline_steps = [
            {"step": "ingest", "source_type": "multi_source"},
            {"step": "format", "format_type": "instruction_response"},
            {"step": "diversify", "method": "task_clustering"},
            {"step": "quality_check", "min_score": 85.0},
            {"step": "balance", "method": "task_distribution"},
        ]
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
            pipeline_steps=pipeline_steps,
        )
        
        self.templates[metadata.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[DatasetTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        complexity: Optional[TemplateComplexity] = None,
    ) -> List[DatasetTemplate]:
        """List all templates with optional filtering."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.metadata.category == category]
        
        if complexity:
            templates = [t for t in templates if t.metadata.complexity == complexity]
        
        return templates
    
    def create_custom_template(
        self,
        template_id: str,
        name: str,
        description: str,
        category: TemplateCategory,
        complexity: TemplateComplexity,
        config: Dict[str, Any],
        author: str = "custom",
    ) -> DatasetTemplate:
        """Create a custom template."""
        metadata = TemplateMetadata(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            complexity=complexity,
            author=author,
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
        )
        
        template = DatasetTemplate(
            metadata=metadata,
            config=config,
        )
        
        self.templates[template_id] = template
        return template
    
    def update_template(
        self,
        template_id: str,
        config: Optional[Dict[str, Any]] = None,
        pipeline_steps: Optional[List[Dict[str, Any]]] = None,
        quality_gates: Optional[List[Dict[str, Any]]] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DatasetTemplate]:
        """Update an existing template."""
        template = self.templates.get(template_id)
        
        if not template:
            return None
        
        if config:
            template.config.update(config)
        
        if pipeline_steps is not None:
            template.pipeline_steps = pipeline_steps
        
        if quality_gates is not None:
            template.quality_gates = quality_gates
        
        if validation_rules is not None:
            template.validation_rules = validation_rules
        
        template.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def instantiate_template(
        self,
        template_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Instantiate a template with parameters."""
        template = self.get_template(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Start with template config
        instance_config = template.config.copy()
        
        # Override with params
        if params:
            instance_config.update(params)
        
        return {
            "template_id": template_id,
            "config": instance_config,
            "pipeline_steps": template.pipeline_steps.copy(),
            "quality_gates": template.quality_gates.copy(),
            "validation_rules": template.validation_rules.copy(),
        }
    
    def save_template(self, template_id: str, output_path: Path) -> None:
        """Save a template to file."""
        template = self.get_template(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template.to_json() + "\n", encoding="utf-8")
    
    def load_template(self, input_path: Path) -> DatasetTemplate:
        """Load a template from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        metadata = TemplateMetadata(
            template_id=data["metadata"]["template_id"],
            name=data["metadata"]["name"],
            description=data["metadata"]["description"],
            category=TemplateCategory(data["metadata"]["category"]),
            complexity=TemplateComplexity(data["metadata"]["complexity"]),
            author=data["metadata"]["author"],
            version=data["metadata"]["version"],
            created_at=data["metadata"]["created_at"],
            updated_at=data["metadata"]["updated_at"],
            tags=data["metadata"].get("tags", []),
        )
        
        template = DatasetTemplate(
            metadata=metadata,
            config=data["config"],
            pipeline_steps=data.get("pipeline_steps", []),
            quality_gates=data.get("quality_gates", []),
            validation_rules=data.get("validation_rules", []),
            example_data=data.get("example_data"),
        )
        
        self.templates[metadata.template_id] = template
        return template
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get template statistics."""
        total = len(self.templates)
        
        by_category = {}
        by_complexity = {}
        
        for template in self.templates.values():
            category = template.metadata.category.value
            complexity = template.metadata.complexity.value
            
            by_category[category] = by_category.get(category, 0) + 1
            by_complexity[complexity] = by_complexity.get(complexity, 0) + 1
        
        return {
            "total_templates": total,
            "by_category": by_category,
            "by_complexity": by_complexity,
        }
