"""Dataset compliance tracking for regulatory requirements."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ComplianceRegulation(Enum):
    """Supported compliance regulations."""
    
    GDPR = "gdpr"  # EU General Data Protection Regulation
    CCPA = "ccpa"  # California Consumer Privacy Act
    AI_ACT = "ai_act"  # EU AI Act
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"  # Service Organization Control 2
    ISO27001 = "iso27001"  # Information Security Management
    CUSTOM = "custom"


class ComplianceStatus(Enum):
    """Compliance check status."""
    
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NEEDS_REVIEW = "needs_review"
    EXEMPTED = "exempted"


@dataclass
class ComplianceRequirement:
    """A specific compliance requirement."""
    
    requirement_id: str
    regulation: ComplianceRegulation
    title: str
    description: str
    mandatory: bool = True
    check_function: Optional[str] = None
    remediation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement_id": self.requirement_id,
            "regulation": self.regulation.value,
            "title": self.title,
            "description": self.description,
            "mandatory": self.mandatory,
            "check_function": self.check_function,
            "remediation": self.remediation,
        }


@dataclass
class ComplianceCheck:
    """Result of a compliance check."""
    
    check_id: str
    requirement: ComplianceRequirement
    status: ComplianceStatus
    timestamp: str
    details: str = ""
    evidence: List[str] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "requirement": self.requirement.to_dict(),
            "status": self.status.value,
            "timestamp": self.timestamp,
            "details": self.details,
            "evidence": self.evidence,
            "violations": self.violations,
        }


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""
    
    report_id: str
    dataset_path: str
    regulations: List[ComplianceRegulation]
    checks: List[ComplianceCheck]
    timestamp: str
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "report_id": self.report_id,
            "dataset_path": self.dataset_path,
            "regulations": [r.value for r in self.regulations],
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
            "summary": self.summary,
        }, indent=2)


class DatasetComplianceTracker:
    """Track compliance with regulatory requirements."""
    
    def __init__(self):
        """Initialize the compliance tracker."""
        self.requirements: Dict[str, ComplianceRequirement] = {}
        self._load_default_requirements()
    
    def _load_default_requirements(self) -> None:
        """Load default compliance requirements."""
        # GDPR requirements
        self.add_requirement(ComplianceRequirement(
            requirement_id="gdpr_consent",
            regulation=ComplianceRegulation.GDPR,
            title="Data Collection Consent",
            description="Data must be collected with explicit user consent",
            mandatory=True,
            check_function="check_consent_documentation",
            remediation="Document consent mechanisms and user agreements",
        ))
        
        self.add_requirement(ComplianceRequirement(
            requirement_id="gdpr_right_to_erasure",
            regulation=ComplianceRegulation.GDPR,
            title="Right to Erasure",
            description="System must support data deletion on request",
            mandatory=True,
            check_function="check_deletion_capability",
            remediation="Implement data deletion mechanism",
        ))
        
        self.add_requirement(ComplianceRequirement(
            requirement_id="gdpr_data_minimization",
            regulation=ComplianceRegulation.GDPR,
            title="Data Minimization",
            description="Only necessary data should be collected",
            mandatory=True,
            check_function="check_data_minimization",
            remediation="Review and remove unnecessary fields",
        ))
        
        # AI Act requirements
        self.add_requirement(ComplianceRequirement(
            requirement_id="ai_act_training_data_governance",
            regulation=ComplianceRegulation.AI_ACT,
            title="Training Data Governance",
            description="Training data must be managed with appropriate governance",
            mandatory=True,
            check_function="check_data_governance",
            remediation="Implement data governance policies",
        ))
        
        self.add_requirement(ComplianceRequirement(
            requirement_id="ai_act_transparency",
            regulation=ComplianceRegulation.AI_ACT,
            title="Transparency Requirements",
            description="AI systems must be transparent and explainable",
            mandatory=True,
            check_function="check_transparency_documentation",
            remediation="Document model training process and data sources",
        ))
        
        # CCPA requirements
        self.add_requirement(ComplianceRequirement(
            requirement_id="ccpa_data_disclosure",
            regulation=ComplianceRegulation.CCPA,
            title="Data Disclosure",
            description="Must disclose data collection practices",
            mandatory=True,
            check_function="check_disclosure_documentation",
            remediation="Create privacy disclosure documentation",
        ))
    
    def add_requirement(
        self,
        requirement: ComplianceRequirement,
    ) -> None:
        """Add a compliance requirement."""
        self.requirements[requirement.requirement_id] = requirement
    
    def check_consent_documentation(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for consent documentation."""
        requirement = self.requirements["gdpr_consent"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check if consent is documented
        has_consent = metadata.get("consent_documented", False)
        has_legal_basis = metadata.get("legal_basis") is not None
        
        if has_consent and has_legal_basis:
            status = ComplianceStatus.COMPLIANT
            details = "Consent and legal basis documented"
        elif has_consent or has_legal_basis:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Partial consent documentation found"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = "No consent documentation found"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_deletion_capability(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for data deletion capability."""
        requirement = self.requirements["gdpr_right_to_erasure"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check if deletion mechanism exists
        has_record_ids = metadata.get("has_record_identifiers", False)
        has_deletion_api = metadata.get("deletion_api_available", False)
        
        if has_record_ids and has_deletion_api:
            status = ComplianceStatus.COMPLIANT
            details = "Record identifiers and deletion API available"
        elif has_record_ids:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Record identifiers available, deletion API needed"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = "No deletion capability found"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_data_minimization(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for data minimization."""
        requirement = self.requirements["gdpr_data_minimization"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check field justification
        field_justification = metadata.get("field_justification", {})
        required_fields = metadata.get("required_fields", [])
        
        if field_justification and required_fields:
            status = ComplianceStatus.COMPLIANT
            details = "Data minimization documented and justified"
        elif required_fields:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Required fields identified, justification needed"
        else:
            status = ComplianceStatus.NEEDS_REVIEW
            details = "Data minimization needs review"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_data_governance(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for data governance."""
        requirement = self.requirements["ai_act_training_data_governance"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check governance documentation
        has_governance_policy = metadata.get("governance_policy") is not None
        has_data_steward = metadata.get("data_steward") is not None
        has_quality_checks = metadata.get("quality_checks_enabled", False)
        
        compliant_count = sum([has_governance_policy, has_data_steward, has_quality_checks])
        
        if compliant_count == 3:
            status = ComplianceStatus.COMPLIANT
            details = "Data governance fully implemented"
        elif compliant_count >= 2:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Data governance partially implemented"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = "Data governance not implemented"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_transparency_documentation(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for transparency documentation."""
        requirement = self.requirements["ai_act_transparency"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check transparency docs
        has_model_card = metadata.get("model_card_path") is not None
        has_dataset_card = metadata.get("dataset_card_path") is not None
        has_provenance = metadata.get("provenance_tracked", False)
        
        compliant_count = sum([has_model_card, has_dataset_card, has_provenance])
        
        if compliant_count == 3:
            status = ComplianceStatus.COMPLIANT
            details = "Transparency documentation complete"
        elif compliant_count >= 2:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Transparency documentation partial"
        else:
            status = ComplianceStatus.NEEDS_REVIEW
            details = "Transparency documentation needed"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_disclosure_documentation(
        self,
        dataset_path: Path,
        metadata: Dict[str, Any],
    ) -> ComplianceCheck:
        """Check for disclosure documentation."""
        requirement = self.requirements["ccpa_data_disclosure"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check disclosure
        has_privacy_policy = metadata.get("privacy_policy") is not None
        has_data_sources = metadata.get("data_sources_disclosed", False)
        
        if has_privacy_policy and has_data_sources:
            status = ComplianceStatus.COMPLIANT
            details = "Disclosure documentation complete"
        elif has_privacy_policy or has_data_sources:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            details = "Partial disclosure documentation"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = "No disclosure documentation"
        
        return ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.utcnow().timestamp()}",
            requirement=requirement,
            status=status,
            timestamp=timestamp,
            details=details,
        )
    
    def check_compliance(
        self,
        dataset_path: Path,
        regulations: List[ComplianceRegulation],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComplianceReport:
        """Check compliance for specified regulations."""
        if metadata is None:
            metadata = {}
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        report_id = f"compliance_report_{datetime.utcnow().timestamp()}"
        
        checks = []
        
        # Run checks for each regulation
        for regulation in regulations:
            reg_requirements = [
                r for r in self.requirements.values()
                if r.regulation == regulation
            ]
            
            for req in reg_requirements:
                if req.check_function:
                    check_method = getattr(self, req.check_function, None)
                    if check_method:
                        check = check_method(dataset_path, metadata)
                        checks.append(check)
        
        # Generate summary
        summary = {
            "total_checks": len(checks),
            "compliant": len([c for c in checks if c.status == ComplianceStatus.COMPLIANT]),
            "non_compliant": len([c for c in checks if c.status == ComplianceStatus.NON_COMPLIANT]),
            "partially_compliant": len([c for c in checks if c.status == ComplianceStatus.PARTIALLY_COMPLIANT]),
            "needs_review": len([c for c in checks if c.status == ComplianceStatus.NEEDS_REVIEW]),
            "compliance_score": 0.0,
        }
        
        # Calculate compliance score
        if summary["total_checks"] > 0:
            score = (
                summary["compliant"] * 1.0 +
                summary["partially_compliant"] * 0.5
            ) / summary["total_checks"]
            summary["compliance_score"] = round(score, 2)
        
        return ComplianceReport(
            report_id=report_id,
            dataset_path=str(dataset_path),
            regulations=regulations,
            checks=checks,
            timestamp=timestamp,
            summary=summary,
        )
    
    def save_report(
        self,
        report: ComplianceReport,
        output_path: Path,
    ) -> None:
        """Save compliance report to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.to_json() + "\n", encoding="utf-8")
    
    def load_report(
        self,
        input_path: Path,
    ) -> ComplianceReport:
        """Load compliance report from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        checks = []
        for check_data in data["checks"]:
            req_data = check_data["requirement"]
            requirement = ComplianceRequirement(
                requirement_id=req_data["requirement_id"],
                regulation=ComplianceRegulation(req_data["regulation"]),
                title=req_data["title"],
                description=req_data["description"],
                mandatory=req_data["mandatory"],
                check_function=req_data.get("check_function"),
                remediation=req_data.get("remediation", ""),
            )
            
            check = ComplianceCheck(
                check_id=check_data["check_id"],
                requirement=requirement,
                status=ComplianceStatus(check_data["status"]),
                timestamp=check_data["timestamp"],
                details=check_data.get("details", ""),
                evidence=check_data.get("evidence", []),
                violations=check_data.get("violations", []),
            )
            checks.append(check)
        
        return ComplianceReport(
            report_id=data["report_id"],
            dataset_path=data["dataset_path"],
            regulations=[ComplianceRegulation(r) for r in data["regulations"]],
            checks=checks,
            timestamp=data["timestamp"],
            summary=data.get("summary", {}),
        )
    
    def get_remediation_plan(
        self,
        report: ComplianceReport,
    ) -> Dict[str, List[str]]:
        """Generate remediation plan for non-compliant items."""
        plan = {
            "critical": [],
            "important": [],
            "recommended": [],
        }
        
        for check in report.checks:
            if check.status == ComplianceStatus.NON_COMPLIANT and check.requirement.mandatory:
                plan["critical"].append(check.requirement.remediation)
            elif check.status == ComplianceStatus.PARTIALLY_COMPLIANT and check.requirement.mandatory:
                plan["important"].append(check.requirement.remediation)
            elif check.status == ComplianceStatus.NEEDS_REVIEW:
                plan["recommended"].append(check.requirement.remediation)
        
        return plan
