"""
Tests for policy_templates module
"""
import pytest
import json
from peachtree.policy_templates import (
    PolicyTemplateLibrary,
    PolicyTemplate,
)


def test_policy_template_creation():
    """Test PolicyTemplate dataclass"""
    template = PolicyTemplate(
        template_id="test_template_v1",
        name="Test Template",
        description="Test policy template",
        rules={"quality_gates": {"min_quality_score": 70}},
        metadata={"purpose": "testing"},
    )
    
    assert template.template_id == "test_template_v1"
    assert template.name == "Test Template"
    assert template.rules["quality_gates"]["min_quality_score"] == 70


def test_policy_template_to_dict():
    """Test policy template serialization"""
    template = PolicyTemplate(
        template_id="test_v1",
        name="Test",
        description="Test template",
        rules={},
        metadata={},
    )
    
    data = template.to_dict()
    
    assert data["template_id"] == "test_v1"
    assert data["name"] == "Test"


def test_policy_template_to_json():
    """Test policy template JSON serialization"""
    template = PolicyTemplate(
        template_id="test_v1",
        name="Test",
        description="Test template",
        rules={"key": "value"},
        metadata={},
    )
    
    json_str = template.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["template_id"] == "test_v1"


def test_get_gdpr_template():
    """Test GDPR compliance template"""
    template = PolicyTemplateLibrary.get_gdpr_template()
    
    assert template.template_id == "gdpr_compliance_v1"
    assert "GDPR" in template.name
    assert "quality_gates" in template.rules
    assert "license_gates" in template.rules
    assert "safety_gates" in template.rules
    assert template.rules["safety_gates"]["block_pii"] is True


def test_get_hipaa_template():
    """Test HIPAA compliance template"""
    template = PolicyTemplateLibrary.get_hipaa_template()
    
    assert template.template_id == "hipaa_compliance_v1"
    assert "HIPAA" in template.name
    assert template.rules["safety_gates"]["block_phi"] is True
    assert template.rules["safety_gates"]["block_ssn"] is True
    assert template.metadata["regulation"] == "HIPAA"


def test_get_soc2_template():
    """Test SOC 2 compliance template"""
    template = PolicyTemplateLibrary.get_soc2_template()
    
    assert template.template_id == "soc2_compliance_v1"
    assert "SOC 2" in template.name
    assert "audit_gates" in template.rules
    assert template.rules["audit_gates"]["require_change_tracking"] is True
    assert "security" in template.metadata["trust_principles"]


def test_get_commercial_ready_template():
    """Test commercial-ready template"""
    template = PolicyTemplateLibrary.get_commercial_ready_template()
    
    assert template.template_id == "commercial_ready_v1"
    assert "quality_gates" in template.rules
    assert template.rules["quality_gates"]["min_quality_score"] == 85
    assert template.rules["license_gates"]["deny_copyleft"] is True
    assert "MIT" in template.rules["license_gates"]["allowed_licenses"]


def test_get_open_safe_template():
    """Test open-safe template"""
    template = PolicyTemplateLibrary.get_open_safe_template()
    
    assert template.template_id == "open_safe_v1"
    assert template.rules["license_gates"]["allow_copyleft"] is True
    assert "GPL-3.0" in template.rules["license_gates"]["allowed_licenses"]
    assert template.metadata["purpose"] == "open_source_training"


def test_get_research_template():
    """Test research template"""
    template = PolicyTemplateLibrary.get_research_template()
    
    assert template.template_id == "research_v1"
    assert template.rules["quality_gates"]["min_quality_score"] == 50
    assert template.rules["license_gates"]["allowed_licenses"] == "*"
    assert template.metadata["purpose"] == "academic_research"


def test_get_hancock_cybersecurity_template():
    """Test Hancock cybersecurity template"""
    template = PolicyTemplateLibrary.get_hancock_cybersecurity_template()
    
    assert template.template_id == "hancock_cybersecurity_v1"
    assert "security_gates" in template.rules
    assert template.rules["security_gates"]["require_ioc_validation"] is True
    assert template.metadata["framework"] == "mitre_attack"


def test_list_templates():
    """Test listing all available templates"""
    templates = PolicyTemplateLibrary.list_templates()
    
    assert isinstance(templates, list)
    assert len(templates) == 7
    assert "gdpr_compliance_v1" in templates
    assert "hipaa_compliance_v1" in templates
    assert "soc2_compliance_v1" in templates
    assert "commercial_ready_v1" in templates
    assert "open_safe_v1" in templates
    assert "research_v1" in templates
    assert "hancock_cybersecurity_v1" in templates


def test_get_template_by_id_gdpr():
    """Test getting template by ID (GDPR)"""
    template = PolicyTemplateLibrary.get_template("gdpr_compliance_v1")
    
    assert template.template_id == "gdpr_compliance_v1"
    assert "GDPR" in template.name


def test_get_template_by_id_hipaa():
    """Test getting template by ID (HIPAA)"""
    template = PolicyTemplateLibrary.get_template("hipaa_compliance_v1")
    
    assert template.template_id == "hipaa_compliance_v1"
    assert "HIPAA" in template.name


def test_get_template_by_id_commercial():
    """Test getting template by ID (commercial)"""
    template = PolicyTemplateLibrary.get_template("commercial_ready_v1")
    
    assert template.template_id == "commercial_ready_v1"


def test_get_template_invalid_id():
    """Test getting template with invalid ID"""
    with pytest.raises(ValueError, match="Unknown template ID"):
        PolicyTemplateLibrary.get_template("invalid_template_id")


def test_save_template(tmp_path):
    """Test saving template to file"""
    template = PolicyTemplateLibrary.get_gdpr_template()
    output_path = tmp_path / "gdpr_policy.json"
    
    PolicyTemplateLibrary.save_template(template, output_path)
    
    assert output_path.exists()
    
    # Verify content
    with open(output_path) as f:
        data = json.load(f)
    
    assert data["template_id"] == "gdpr_compliance_v1"


def test_save_template_creates_parent_dirs(tmp_path):
    """Test that save creates parent directories"""
    template = PolicyTemplateLibrary.get_soc2_template()
    output_path = tmp_path / "nested" / "dir" / "policy.json"
    
    PolicyTemplateLibrary.save_template(template, output_path)
    
    assert output_path.exists()
    assert output_path.parent.exists()


def test_load_template(tmp_path):
    """Test loading template from file"""
    # Save template first
    template = PolicyTemplateLibrary.get_commercial_ready_template()
    template_path = tmp_path / "commercial.json"
    PolicyTemplateLibrary.save_template(template, template_path)
    
    # Load it back
    loaded = PolicyTemplateLibrary.load_template(template_path)
    
    assert loaded.template_id == template.template_id
    assert loaded.name == template.name
    assert loaded.rules == template.rules


def test_template_roundtrip(tmp_path):
    """Test save and load roundtrip"""
    original = PolicyTemplateLibrary.get_open_safe_template()
    template_path = tmp_path / "roundtrip.json"
    
    # Save and load
    PolicyTemplateLibrary.save_template(original, template_path)
    loaded = PolicyTemplateLibrary.load_template(template_path)
    
    # Compare
    assert loaded.template_id == original.template_id
    assert loaded.description == original.description
    assert loaded.metadata == original.metadata


def test_gdpr_blocks_pii():
    """Test GDPR template blocks PII"""
    template = PolicyTemplateLibrary.get_gdpr_template()
    
    assert template.rules["safety_gates"]["block_pii"] is True
    assert template.rules["safety_gates"]["block_emails"] is True
    assert template.rules["safety_gates"]["block_phone_numbers"] is True


def test_hipaa_strict_compliance():
    """Test HIPAA has strict compliance settings"""
    template = PolicyTemplateLibrary.get_hipaa_template()
    
    assert template.metadata["compliance_level"] == "maximum"
    assert template.rules["quality_gates"]["min_quality_score"] >= 80


def test_commercial_denies_copyleft():
    """Test commercial template denies copyleft licenses"""
    template = PolicyTemplateLibrary.get_commercial_ready_template()
    
    assert template.rules["license_gates"]["deny_copyleft"] is True
    assert "GPL" not in " ".join(template.rules["license_gates"]["allowed_licenses"])


def test_research_minimal_restrictions():
    """Test research template has minimal restrictions"""
    template = PolicyTemplateLibrary.get_research_template()
    
    assert template.metadata["restrictions"] == "minimal"
    assert template.rules["quality_gates"]["min_quality_score"] == 50


def test_all_templates_have_required_fields():
    """Test that all templates have required fields"""
    for template_id in PolicyTemplateLibrary.list_templates():
        template = PolicyTemplateLibrary.get_template(template_id)
        
        assert template.template_id
        assert template.name
        assert template.description
        assert isinstance(template.rules, dict)
        assert isinstance(template.metadata, dict)


def test_all_templates_serialize():
    """Test that all templates can be serialized"""
    for template_id in PolicyTemplateLibrary.list_templates():
        template = PolicyTemplateLibrary.get_template(template_id)
        
        # to_dict
        data = template.to_dict()
        assert "template_id" in data
        
        # to_json
        json_str = template.to_json()
        parsed = json.loads(json_str)
        assert parsed["template_id"] == template_id
