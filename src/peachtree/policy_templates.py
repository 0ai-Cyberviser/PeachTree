"""
PeachTree Policy Templates Library

Pre-built compliance policy packs for common regulatory and safety requirements.
Includes GDPR, HIPAA, SOC2, commercial-ready, and open-safe templates.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class PolicyTemplate:
    """Pre-configured policy template"""
    template_id: str
    name: str
    description: str
    rules: dict[str, Any]
    metadata: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "rules": self.rules,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class PolicyTemplateLibrary:
    """Library of pre-built compliance policy templates"""
    
    @staticmethod
    def get_gdpr_template() -> PolicyTemplate:
        """
        GDPR (General Data Protection Regulation) compliance template
        
        Enforces:
        - No personally identifiable information (PII)
        - No email addresses or phone numbers
        - Data minimization principles
        - Right to be forgotten compliance
        """
        return PolicyTemplate(
            template_id="gdpr_compliance_v1",
            name="GDPR Compliance Policy",
            description="EU General Data Protection Regulation compliance for ML training data",
            rules={
                "quality_gates": {
                    "min_quality_score": 70,
                    "require_provenance": True,
                    "block_low_quality": True,
                },
                "license_gates": {
                    "allowed_licenses": ["MIT", "Apache-2.0", "BSD-3-Clause", "CC-BY-4.0"],
                    "deny_unknown": True,
                },
                "safety_gates": {
                    "block_pii": True,
                    "block_emails": True,
                    "block_phone_numbers": True,
                    "block_addresses": True,
                    "block_names": False,  # Allow names in documentation
                },
                "security_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                    "block_api_keys": True,
                },
                "content_gates": {
                    "min_content_length": 10,
                    "max_content_length": 100000,
                    "require_text_content": True,
                },
            },
            metadata={
                "regulation": "GDPR",
                "jurisdiction": "EU",
                "compliance_level": "strict",
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_hipaa_template() -> PolicyTemplate:
        """
        HIPAA (Health Insurance Portability and Accountability Act) template
        
        Enforces:
        - No protected health information (PHI)
        - No medical record numbers
        - No patient identifiers
        - Strict access controls
        """
        return PolicyTemplate(
            template_id="hipaa_compliance_v1",
            name="HIPAA Compliance Policy",
            description="US healthcare data protection for ML training datasets",
            rules={
                "quality_gates": {
                    "min_quality_score": 80,
                    "require_provenance": True,
                    "require_encryption": True,
                },
                "license_gates": {
                    "allowed_licenses": ["MIT", "Apache-2.0", "Proprietary-Safe"],
                    "deny_unknown": True,
                },
                "safety_gates": {
                    "block_pii": True,
                    "block_phi": True,
                    "block_medical_records": True,
                    "block_patient_ids": True,
                    "block_ssn": True,
                    "block_dates": True,  # Dates related to patients
                },
                "security_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                    "require_audit_trail": True,
                },
                "content_gates": {
                    "min_content_length": 20,
                    "require_de_identification": True,
                },
            },
            metadata={
                "regulation": "HIPAA",
                "jurisdiction": "US",
                "compliance_level": "maximum",
                "phi_handling": "prohibited",
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_soc2_template() -> PolicyTemplate:
        """
        SOC 2 (Service Organization Control 2) template
        
        Enforces:
        - Trust principles (security, availability, confidentiality)
        - Data integrity requirements
        - Access control and audit logging
        """
        return PolicyTemplate(
            template_id="soc2_compliance_v1",
            name="SOC 2 Compliance Policy",
            description="SOC 2 trust principles for dataset management",
            rules={
                "quality_gates": {
                    "min_quality_score": 75,
                    "require_provenance": True,
                    "require_integrity_checks": True,
                },
                "license_gates": {
                    "allowed_licenses": ["MIT", "Apache-2.0", "BSD-3-Clause"],
                    "deny_unknown": True,
                    "require_license_tracking": True,
                },
                "safety_gates": {
                    "block_pii": True,
                    "block_sensitive_data": True,
                },
                "security_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                    "block_private_keys": True,
                    "require_access_logs": True,
                },
                "audit_gates": {
                    "require_change_tracking": True,
                    "require_version_history": True,
                    "require_approval_records": True,
                },
            },
            metadata={
                "framework": "SOC 2",
                "trust_principles": ["security", "availability", "confidentiality"],
                "compliance_level": "type_ii",
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_commercial_ready_template() -> PolicyTemplate:
        """
        Commercial-ready template for production model training
        
        Enforces:
        - High quality standards
        - License compliance for commercial use
        - No secrets or sensitive data
        """
        return PolicyTemplate(
            template_id="commercial_ready_v1",
            name="Commercial-Ready Policy",
            description="Production-grade quality and licensing for commercial model training",
            rules={
                "quality_gates": {
                    "min_quality_score": 85,
                    "min_dedup_score": 90,
                    "require_provenance": True,
                    "block_low_quality": True,
                },
                "license_gates": {
                    "allowed_licenses": [
                        "MIT",
                        "Apache-2.0",
                        "BSD-3-Clause",
                        "BSD-2-Clause",
                        "ISC",
                        "CC0-1.0",
                    ],
                    "deny_copyleft": True,  # No GPL/AGPL
                    "deny_unknown": True,
                    "require_commercial_use": True,
                },
                "safety_gates": {
                    "block_pii": True,
                    "block_harmful_content": True,
                },
                "security_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                    "block_api_keys": True,
                    "block_private_keys": True,
                },
                "content_gates": {
                    "min_content_length": 50,
                    "max_content_length": 50000,
                    "require_english": False,
                },
            },
            metadata={
                "purpose": "commercial_training",
                "quality_level": "production",
                "license_risk": "low",
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_open_safe_template() -> PolicyTemplate:
        """
        Open-safe template for open-source model training
        
        Enforces:
        - Open-source license compatibility
        - Community safety standards
        - Basic quality requirements
        """
        return PolicyTemplate(
            template_id="open_safe_v1",
            name="Open-Safe Policy",
            description="Open-source compatible dataset with safety standards",
            rules={
                "quality_gates": {
                    "min_quality_score": 60,
                    "require_provenance": True,
                },
                "license_gates": {
                    "allowed_licenses": [
                        "MIT",
                        "Apache-2.0",
                        "BSD-3-Clause",
                        "GPL-3.0",
                        "AGPL-3.0",
                        "CC-BY-4.0",
                        "CC-BY-SA-4.0",
                    ],
                    "allow_copyleft": True,
                    "deny_unknown": False,  # More permissive
                },
                "safety_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                    "block_harmful_content": True,
                },
                "security_gates": {
                    "block_api_keys": True,
                    "block_private_keys": True,
                },
                "content_gates": {
                    "min_content_length": 10,
                },
            },
            metadata={
                "purpose": "open_source_training",
                "license_compatibility": "permissive_and_copyleft",
                "community": "open_source",
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_research_template() -> PolicyTemplate:
        """
        Research template for academic/experimental use
        
        Enforces:
        - Minimal restrictions for research
        - Basic safety requirements
        - Citation tracking
        """
        return PolicyTemplate(
            template_id="research_v1",
            name="Research Policy",
            description="Academic research dataset with minimal restrictions",
            rules={
                "quality_gates": {
                    "min_quality_score": 50,
                    "require_provenance": True,
                },
                "license_gates": {
                    "allowed_licenses": "*",  # Accept all licenses
                    "deny_unknown": False,
                    "require_attribution": True,
                },
                "safety_gates": {
                    "block_secrets": True,
                    "block_credentials": True,
                },
                "security_gates": {
                    "block_api_keys": True,
                },
                "metadata_gates": {
                    "require_citation": True,
                    "require_source_repo": True,
                },
            },
            metadata={
                "purpose": "academic_research",
                "restrictions": "minimal",
                "citation_required": True,
                "last_updated": "2026-04-27",
            },
        )
    
    @staticmethod
    def get_hancock_cybersecurity_template() -> PolicyTemplate:
        """
        Hancock cybersecurity template for security training data
        
        Enforces:
        - Security-focused quality standards
        - IOC and TTP validation
        - Threat intelligence requirements
        """
        return PolicyTemplate(
            template_id="hancock_cybersecurity_v1",
            name="Hancock Cybersecurity Policy",
            description="Security training dataset for Hancock cybersecurity AI",
            rules={
                "quality_gates": {
                    "min_quality_score": 75,
                    "require_provenance": True,
                    "require_security_context": True,
                },
                "license_gates": {
                    "allowed_licenses": ["MIT", "Apache-2.0", "Proprietary-Security"],
                    "deny_unknown": True,
                },
                "safety_gates": {
                    "block_live_credentials": True,
                    "allow_sanitized_examples": True,
                },
                "security_gates": {
                    "require_ioc_validation": True,
                    "require_ttp_mapping": True,
                    "block_live_exploits": True,
                },
                "content_gates": {
                    "require_security_labels": True,
                    "require_mitre_attack_mapping": False,
                },
            },
            metadata={
                "purpose": "cybersecurity_training",
                "framework": "mitre_attack",
                "threat_intel": "enabled",
                "last_updated": "2026-04-27",
            },
        )
    
    @classmethod
    def list_templates(cls) -> list[str]:
        """List all available template IDs"""
        return [
            "gdpr_compliance_v1",
            "hipaa_compliance_v1",
            "soc2_compliance_v1",
            "commercial_ready_v1",
            "open_safe_v1",
            "research_v1",
            "hancock_cybersecurity_v1",
        ]
    
    @classmethod
    def get_template(cls, template_id: str) -> PolicyTemplate:
        """Get policy template by ID"""
        template_map = {
            "gdpr_compliance_v1": cls.get_gdpr_template,
            "hipaa_compliance_v1": cls.get_hipaa_template,
            "soc2_compliance_v1": cls.get_soc2_template,
            "commercial_ready_v1": cls.get_commercial_ready_template,
            "open_safe_v1": cls.get_open_safe_template,
            "research_v1": cls.get_research_template,
            "hancock_cybersecurity_v1": cls.get_hancock_cybersecurity_template,
        }
        
        if template_id not in template_map:
            raise ValueError(f"Unknown template ID: {template_id}")
        
        return template_map[template_id]()
    
    @classmethod
    def save_template(cls, template: PolicyTemplate, output_path: Path | str) -> None:
        """Save policy template to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template.to_json() + "\n", encoding="utf-8")
    
    @classmethod
    def load_template(cls, template_path: Path | str) -> PolicyTemplate:
        """Load policy template from file"""
        with open(template_path) as f:
            data = json.load(f)
        
        return PolicyTemplate(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            rules=data["rules"],
            metadata=data["metadata"],
        )
