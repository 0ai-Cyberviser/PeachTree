"""Tests for dataset compliance functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_compliance import (
    ComplianceCheck,
    ComplianceRegulation,
    ComplianceReport,
    ComplianceRequirement,
    ComplianceStatus,
    DatasetComplianceTracker,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample dataset for testing."""
    dataset = temp_dir / "dataset.jsonl"
    records = [
        {"record_id": "rec_001", "content": "Test content 1", "quality_score": 85},
        {"record_id": "rec_002", "content": "Test content 2", "quality_score": 90},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


@pytest.fixture
def compliant_metadata():
    """Create compliant metadata."""
    return {
        "consent_documented": True,
        "legal_basis": "explicit_consent",
        "has_record_identifiers": True,
        "deletion_api_available": True,
        "field_justification": {"content": "training data", "quality_score": "quality metric"},
        "required_fields": ["record_id", "content"],
        "governance_policy": "v1.0",
        "data_steward": "admin@example.com",
        "quality_checks_enabled": True,
        "model_card_path": "model_card.md",
        "dataset_card_path": "dataset_card.md",
        "provenance_tracked": True,
        "privacy_policy": "privacy_v1.0",
        "data_sources_disclosed": True,
    }


class TestComplianceRequirement:
    """Test ComplianceRequirement dataclass."""
    
    def test_requirement_creation(self):
        """Test creating a compliance requirement."""
        req = ComplianceRequirement(
            requirement_id="test_req",
            regulation=ComplianceRegulation.GDPR,
            title="Test Requirement",
            description="A test requirement",
            mandatory=True,
        )
        
        assert req.requirement_id == "test_req"
        assert req.regulation == ComplianceRegulation.GDPR
        assert req.mandatory is True
    
    def test_requirement_to_dict(self):
        """Test converting requirement to dictionary."""
        req = ComplianceRequirement(
            requirement_id="test_req",
            regulation=ComplianceRegulation.CCPA,
            title="Test Requirement",
            description="A test requirement",
            mandatory=False,
            remediation="Fix this issue",
        )
        
        data = req.to_dict()
        assert data["requirement_id"] == "test_req"
        assert data["regulation"] == "ccpa"
        assert data["mandatory"] is False


class TestComplianceCheck:
    """Test ComplianceCheck dataclass."""
    
    def test_check_creation(self):
        """Test creating a compliance check."""
        req = ComplianceRequirement(
            requirement_id="test_req",
            regulation=ComplianceRegulation.GDPR,
            title="Test Requirement",
            description="A test requirement",
        )
        
        check = ComplianceCheck(
            check_id="check_001",
            requirement=req,
            status=ComplianceStatus.COMPLIANT,
            timestamp="2026-04-27T00:00:00Z",
            details="All requirements met",
        )
        
        assert check.check_id == "check_001"
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_with_violations(self):
        """Test check with violations."""
        req = ComplianceRequirement(
            requirement_id="test_req",
            regulation=ComplianceRegulation.AI_ACT,
            title="Test Requirement",
            description="A test requirement",
        )
        
        check = ComplianceCheck(
            check_id="check_001",
            requirement=req,
            status=ComplianceStatus.NON_COMPLIANT,
            timestamp="2026-04-27T00:00:00Z",
            violations=[{"field": "consent", "issue": "missing"}],
        )
        
        assert len(check.violations) == 1
        assert check.violations[0]["field"] == "consent"


class TestDatasetComplianceTracker:
    """Test DatasetComplianceTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initializes with default requirements."""
        tracker = DatasetComplianceTracker()
        
        assert len(tracker.requirements) > 0
        assert "gdpr_consent" in tracker.requirements
        assert "ai_act_training_data_governance" in tracker.requirements
    
    def test_add_requirement(self):
        """Test adding a custom requirement."""
        tracker = DatasetComplianceTracker()
        
        req = ComplianceRequirement(
            requirement_id="custom_req",
            regulation=ComplianceRegulation.CUSTOM,
            title="Custom Requirement",
            description="A custom requirement",
        )
        
        tracker.add_requirement(req)
        
        assert "custom_req" in tracker.requirements
    
    def test_check_consent_documentation_compliant(self, sample_dataset, compliant_metadata):
        """Test consent documentation check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_consent_documentation(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
        assert "consent" in check.details.lower()
    
    def test_check_consent_documentation_non_compliant(self, sample_dataset):
        """Test consent documentation check with non-compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_consent_documentation(sample_dataset, {})
        
        assert check.status == ComplianceStatus.NON_COMPLIANT
    
    def test_check_deletion_capability_compliant(self, sample_dataset, compliant_metadata):
        """Test deletion capability check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_deletion_capability(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_deletion_capability_partial(self, sample_dataset):
        """Test deletion capability check with partial compliance."""
        tracker = DatasetComplianceTracker()
        
        metadata = {"has_record_identifiers": True}
        check = tracker.check_deletion_capability(sample_dataset, metadata)
        
        assert check.status == ComplianceStatus.PARTIALLY_COMPLIANT
    
    def test_check_data_minimization_compliant(self, sample_dataset, compliant_metadata):
        """Test data minimization check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_data_minimization(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_data_governance_compliant(self, sample_dataset, compliant_metadata):
        """Test data governance check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_data_governance(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_data_governance_partial(self, sample_dataset):
        """Test data governance check with partial compliance."""
        tracker = DatasetComplianceTracker()
        
        metadata = {
            "governance_policy": "v1.0",
            "data_steward": "admin@example.com",
        }
        check = tracker.check_data_governance(sample_dataset, metadata)
        
        assert check.status == ComplianceStatus.PARTIALLY_COMPLIANT
    
    def test_check_transparency_documentation_compliant(self, sample_dataset, compliant_metadata):
        """Test transparency documentation check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_transparency_documentation(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_disclosure_documentation_compliant(self, sample_dataset, compliant_metadata):
        """Test disclosure documentation check with compliant metadata."""
        tracker = DatasetComplianceTracker()
        
        check = tracker.check_disclosure_documentation(sample_dataset, compliant_metadata)
        
        assert check.status == ComplianceStatus.COMPLIANT
    
    def test_check_compliance_gdpr(self, sample_dataset, compliant_metadata):
        """Test compliance check for GDPR."""
        tracker = DatasetComplianceTracker()
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR],
            compliant_metadata,
        )
        
        assert isinstance(report, ComplianceReport)
        assert report.dataset_path == str(sample_dataset)
        assert ComplianceRegulation.GDPR in report.regulations
        assert len(report.checks) > 0
        assert report.summary["compliance_score"] > 0
    
    def test_check_compliance_multiple_regulations(self, sample_dataset, compliant_metadata):
        """Test compliance check for multiple regulations."""
        tracker = DatasetComplianceTracker()
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR, ComplianceRegulation.AI_ACT, ComplianceRegulation.CCPA],
            compliant_metadata,
        )
        
        assert len(report.regulations) == 3
        assert len(report.checks) > 0
        assert "compliance_score" in report.summary
    
    def test_check_compliance_non_compliant(self, sample_dataset):
        """Test compliance check with non-compliant dataset."""
        tracker = DatasetComplianceTracker()
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR],
            {},  # Empty metadata = non-compliant
        )
        
        assert report.summary["compliance_score"] < 0.5
        assert report.summary["non_compliant"] > 0
    
    def test_save_and_load_report(self, sample_dataset, compliant_metadata, temp_dir):
        """Test saving and loading a compliance report."""
        tracker = DatasetComplianceTracker()
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR],
            compliant_metadata,
        )
        
        # Save report
        output = temp_dir / "compliance_report.json"
        tracker.save_report(report, output)
        
        assert output.exists()
        
        # Load report
        loaded_report = tracker.load_report(output)
        
        assert loaded_report.dataset_path == report.dataset_path
        assert len(loaded_report.checks) == len(report.checks)
        assert loaded_report.summary["compliance_score"] == report.summary["compliance_score"]
    
    def test_get_remediation_plan_critical(self, sample_dataset):
        """Test getting remediation plan for critical issues."""
        tracker = DatasetComplianceTracker()
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR],
            {},  # Non-compliant
        )
        
        plan = tracker.get_remediation_plan(report)
        
        assert "critical" in plan
        assert "important" in plan
        assert "recommended" in plan
        assert len(plan["critical"]) > 0
    
    def test_compliance_score_calculation(self, sample_dataset):
        """Test compliance score calculation."""
        tracker = DatasetComplianceTracker()
        
        # Partially compliant metadata
        metadata = {
            "consent_documented": True,
            "legal_basis": "explicit_consent",
            "has_record_identifiers": True,
            # Missing deletion_api_available - partial compliance
        }
        
        report = tracker.check_compliance(
            sample_dataset,
            [ComplianceRegulation.GDPR],
            metadata,
        )
        
        # Score should be between 0 and 1
        assert 0 <= report.summary["compliance_score"] <= 1
        
        # Should have some partial compliance
        assert report.summary["partially_compliant"] > 0
    
    def test_all_regulations_supported(self, sample_dataset):
        """Test that all regulation types are supported."""
        tracker = DatasetComplianceTracker()
        
        all_regulations = [
            ComplianceRegulation.GDPR,
            ComplianceRegulation.CCPA,
            ComplianceRegulation.AI_ACT,
            ComplianceRegulation.HIPAA,
            ComplianceRegulation.SOC2,
            ComplianceRegulation.ISO27001,
        ]
        
        for regulation in all_regulations:
            report = tracker.check_compliance(
                sample_dataset,
                [regulation],
                {},
            )
            
            assert regulation in report.regulations
