"""
Tests for Hancock cybersecurity dataset integration
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from peachtree.hancock_integration import (
    HancockSource,
    HancockIngestionConfig,
    HancockDataIngester,
    hancock_ingestion_workflow,
)
from peachtree.models import SourceDocument, DatasetManifest


@pytest.fixture
def mock_hancock_data_dir(tmp_path):
    """Create mock Hancock data directory with sample files"""
    data_dir = tmp_path / "hancock_data"
    data_dir.mkdir()
    
    # Create sample MITRE data
    mitre_data = [
        {
            "name": "Phishing",
            "description": "Adversaries may send phishing messages to gain access",
            "external_references": [{"external_id": "T1566"}],
            "kill_chain_phases": [{"phase_name": "initial-access"}],
            "x_mitre_platforms": ["Windows", "Linux"],
            "x_mitre_detection": "Monitor for suspicious emails"
        }
    ]
    (data_dir / "raw_mitre.json").write_text(json.dumps(mitre_data))
    
    # Create sample CVE data
    cve_data = [
        {
            "id": "CVE-2024-12345",
            "published": "2024-01-01T00:00:00Z",
            "descriptions": [{"lang": "en", "value": "Critical remote code execution"}],
            "metrics": {
                "cvssMetricV31": [{
                    "cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}
                }]
            }
        }
    ]
    (data_dir / "raw_cve.json").write_text(json.dumps(cve_data))
    
    # Create sample KEV data
    kev_data = [
        {
            "cveID": "CVE-2024-54321",
            "vendorProject": "Microsoft",
            "product": "Exchange Server",
            "vulnerabilityName": "ProxyShell",
            "dateAdded": "2024-01-15",
            "shortDescription": "Remote code execution vulnerability",
            "requiredAction": "Apply patches immediately",
            "dueDate": "2024-02-01"
        }
    ]
    (data_dir / "raw_kev.json").write_text(json.dumps(kev_data))
    
    # Create sample KB data
    kb_data = [
        {
            "question": "What is SQL injection?",
            "answer": "SQL injection is a code injection technique...",
            "category": "Web Security",
            "difficulty": "Beginner"
        }
    ]
    (data_dir / "raw_pentest_kb.json").write_text(json.dumps(kb_data))
    
    # Create consolidated v3 JSONL
    v3_records = [
        {"instruction": "Explain CVE-2024-12345", "response": "Critical RCE vulnerability", "source": "cve"},
        {"instruction": "What is T1566?", "response": "Phishing technique", "source": "mitre"}
    ]
    (data_dir / "hancock_v3.jsonl").write_text("\n".join(json.dumps(r) for r in v3_records))
    
    return data_dir


def test_hancock_source_creation():
    """Test HancockSource dataclass creation"""
    source = HancockSource(
        name="test_source",
        source_type="mitre",
        file_path=Path("/tmp/test.json"),
        record_count=100,
        metadata={"version": "1.0"}
    )
    
    assert source.name == "test_source"
    assert source.source_type == "mitre"
    assert source.record_count == 100
    assert source.metadata["version"] == "1.0"


def test_hancock_ingestion_config_defaults():
    """Test HancockIngestionConfig default values"""
    config = HancockIngestionConfig()
    
    assert config.min_quality_score == 0.70
    assert config.commercial_quality_score == 0.80
    assert config.filter_secrets is True
    assert config.require_provenance is True
    assert "mitre" in config.include_sources
    assert "cve" in config.include_sources


def test_hancock_ingestion_config_custom():
    """Test HancockIngestionConfig with custom values"""
    config = HancockIngestionConfig(
        min_quality_score=0.85,
        commercial_quality_score=0.90,
        include_sources=["mitre", "cve"],
        allow_unknown_license=True
    )
    
    assert config.min_quality_score == 0.85
    assert config.commercial_quality_score == 0.90
    assert len(config.include_sources) == 2
    assert config.allow_unknown_license is True


def test_discover_sources(mock_hancock_data_dir):
    """Test discovering Hancock data sources"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    
    sources = ingester.discover_sources()
    
    assert len(sources) >= 4  # mitre, cve, kev, kb, v3
    source_types = {s.source_type for s in sources}
    assert "mitre" in source_types
    assert "cve" in source_types
    assert "kev" in source_types
    assert "kb" in source_types


def test_discover_sources_filtered(mock_hancock_data_dir):
    """Test discovering sources with filtering"""
    config = HancockIngestionConfig(
        hancock_data_dir=mock_hancock_data_dir,
        include_sources=["mitre", "cve"]
    )
    ingester = HancockDataIngester(config)
    
    sources = ingester.discover_sources()
    
    source_types = {s.source_type for s in sources if s.source_type != "consolidated"}
    assert source_types == {"mitre", "cve"}


def test_discover_sources_missing_directory(tmp_path):
    """Test discovering sources when directory doesn't exist"""
    config = HancockIngestionConfig(hancock_data_dir=tmp_path / "nonexistent")
    ingester = HancockDataIngester(config)
    
    sources = ingester.discover_sources()
    
    assert len(sources) == 0


def test_convert_mitre_to_source_documents(mock_hancock_data_dir):
    """Test converting MITRE data to source documents"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    mitre_source = next(s for s in sources if s.source_type == "mitre")
    documents = ingester.convert_to_source_documents(mitre_source)
    
    assert len(documents) > 0
    doc = documents[0]
    assert isinstance(doc, SourceDocument)
    assert "Phishing" in doc.content
    assert "T1566" in doc.content
    assert doc.repo_name.startswith("Hancock/")
    assert doc.license_id == "MIT"


def test_convert_cve_to_source_documents(mock_hancock_data_dir):
    """Test converting CVE data to source documents"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    cve_source = next(s for s in sources if s.source_type == "cve")
    documents = ingester.convert_to_source_documents(cve_source)
    
    assert len(documents) > 0
    doc = documents[0]
    assert "CVE-2024-12345" in doc.content
    assert "CRITICAL" in doc.content or "Critical" in doc.content


def test_convert_kev_to_source_documents(mock_hancock_data_dir):
    """Test converting KEV data to source documents"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    kev_source = next(s for s in sources if s.source_type == "kev")
    documents = ingester.convert_to_source_documents(kev_source)
    
    assert len(documents) > 0
    doc = documents[0]
    assert "CVE-2024-54321" in doc.content
    assert "Microsoft" in doc.content
    assert "ProxyShell" in doc.content


def test_convert_kb_to_source_documents(mock_hancock_data_dir):
    """Test converting knowledge base data to source documents"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    kb_source = next(s for s in sources if s.source_type == "kb")
    documents = ingester.convert_to_source_documents(kb_source)
    
    assert len(documents) > 0
    doc = documents[0]
    assert "SQL injection" in doc.content
    assert "Question:" in doc.content
    assert "Answer:" in doc.content


def test_convert_jsonl_format(mock_hancock_data_dir):
    """Test converting JSONL format (v3 consolidated)"""
    config = HancockIngestionConfig(hancock_data_dir=mock_hancock_data_dir)
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    v3_source = next(s for s in sources if s.name == "hancock_v3")
    documents = ingester.convert_to_source_documents(v3_source)
    
    assert len(documents) == 2


def test_extract_metadata_mitre():
    """Test metadata extraction for MITRE records"""
    ingester = HancockDataIngester()
    record = {
        "external_references": [{"external_id": "T1566"}],
        "kill_chain_phases": [{"phase_name": "initial-access"}],
        "x_mitre_platforms": ["Windows", "Linux"]
    }
    
    metadata = ingester._extract_metadata(record, "mitre")
    
    assert metadata["technique_id"] == "T1566"
    assert "initial-access" in metadata["tactic"]
    assert "Windows" in metadata["platforms"]


def test_extract_metadata_cve():
    """Test metadata extraction for CVE records"""
    ingester = HancockDataIngester()
    record = {
        "id": "CVE-2024-12345",
        "published": "2024-01-01T00:00:00Z",
        "metrics": {
            "cvssMetricV31": [{
                "cvssData": {"baseSeverity": "CRITICAL"}
            }]
        }
    }
    
    metadata = ingester._extract_metadata(record, "cve")
    
    assert metadata["cve_id"] == "CVE-2024-12345"
    assert metadata["severity"] == "CRITICAL"


@patch('peachtree.hancock_integration.DatasetBuilder')
def test_ingest_all(mock_builder_class, mock_hancock_data_dir):
    """Test complete ingestion workflow"""
    config = HancockIngestionConfig(
        hancock_data_dir=mock_hancock_data_dir,
        output_dir=mock_hancock_data_dir / "output"
    )
    ingester = HancockDataIngester(config)
    
    # Mock the builder
    mock_builder = MagicMock()
    mock_builder.records_from_documents.return_value = [{"id": "1"}, {"id": "2"}]
    mock_manifest = Mock()
    mock_manifest.records = [{"id": "1"}, {"id": "2"}]
    mock_builder.write_jsonl.return_value = mock_manifest
    mock_builder_class.return_value = mock_builder
    
    documents, manifest = ingester.ingest_all()
    
    assert len(documents) > 0
    assert mock_builder.records_from_documents.called
    assert mock_builder.write_jsonl.called


@patch('peachtree.hancock_integration.TrainerHandoffBuilder')
def test_generate_training_handoff(mock_trainer_builder, mock_hancock_data_dir):
    """Test generating trainer handoff package"""
    config = HancockIngestionConfig(output_dir=mock_hancock_data_dir / "output")
    ingester = HancockDataIngester(config)
    
    # Mock the trainer handoff builder
    mock_builder_instance = Mock()
    mock_manifest_obj = Mock()
    mock_manifest_obj.to_dict.return_value = {
        "model_name": "hancock-cybersecurity-llm",
        "base_model": "meta-llama/Llama-3.2-3B",
        "dataset_path": str(mock_hancock_data_dir / "output" / "test_dataset.jsonl")
    }
    mock_builder_instance.build.return_value = mock_manifest_obj
    mock_trainer_builder.return_value = mock_builder_instance
    
    # Create mock manifest
    manifest = Mock()
    manifest.dataset_path = str(mock_hancock_data_dir / "output" / "test_dataset.jsonl")
    manifest.records = [{"id": "1"}, {"id": "2"}]
    manifest.total_records = 2
    manifest.data_sources = ["mitre", "cve"]
    
    handoff = ingester.generate_training_handoff(manifest)
    
    assert isinstance(handoff, dict)
    assert "model_name" in handoff or "base_model" in handoff


@patch('peachtree.hancock_integration.TrainerHandoffBuilder')
@patch('peachtree.hancock_integration.HancockDataIngester.ingest_all')
@patch('peachtree.hancock_integration.DatasetQualityScorer')
@patch('peachtree.hancock_integration.DatasetDeduplicator')
def test_hancock_ingestion_workflow(mock_dedup, mock_scorer, mock_ingest, mock_trainer_builder, tmp_path):
    """Test complete Hancock ingestion workflow"""
    # Setup mocks
    mock_docs = [Mock(spec=SourceDocument)]
    mock_manifest = Mock()
    mock_manifest.dataset_path = str(tmp_path / "output" / "test_dataset.jsonl")
    mock_manifest.records = [{"id": "1"}]
    mock_ingest.return_value = (mock_docs, mock_manifest)
    
    mock_scorer_instance = Mock()
    mock_scorer_instance.score_dataset.return_value = {"overall_quality_score": 0.85}
    mock_scorer.return_value = mock_scorer_instance
    
    mock_dedup_instance = Mock()
    mock_dedup_instance.deduplicate_dataset.return_value = {"removed": 5, "kept": 95}
    mock_dedup.return_value = mock_dedup_instance
    
    # Mock trainer handoff builder
    mock_builder_instance = Mock()
    mock_handoff_manifest = Mock()
    mock_handoff_manifest.to_dict.return_value = {"model_name": "test"}
    mock_builder_instance.build.return_value = mock_handoff_manifest
    mock_trainer_builder.return_value = mock_builder_instance
    
    # Run workflow
    summary = hancock_ingestion_workflow(
        hancock_data_dir=tmp_path / "hancock",
        output_dir=tmp_path / "output",
        min_quality_score=0.70,
        generate_handoff=True
    )
    
    assert summary["total_documents"] == 1
    assert summary["quality_score"] == 0.85
    assert summary["ready_for_training"] is True


def test_invalid_record_handling(tmp_path):
    """Test handling of invalid/malformed records"""
    # Create invalid JSON file
    data_dir = tmp_path / "hancock_data"
    data_dir.mkdir()
    (data_dir / "raw_mitre.json").write_text("not valid json")
    
    config = HancockIngestionConfig(hancock_data_dir=data_dir)
    ingester = HancockDataIngester(config)
    
    sources = ingester.discover_sources()
    
    # Should gracefully handle invalid JSON
    assert len(sources) == 0 or all(s.record_count >= 0 for s in sources)


def test_empty_records_handling(tmp_path):
    """Test handling of empty records"""
    data_dir = tmp_path / "hancock_data"
    data_dir.mkdir()
    (data_dir / "raw_mitre.json").write_text("[]")
    
    config = HancockIngestionConfig(hancock_data_dir=data_dir)
    ingester = HancockDataIngester(config)
    
    sources = ingester.discover_sources()
    
    if sources:
        mitre_source = sources[0]
        assert mitre_source.record_count == 0


def test_provenance_tracking(mock_hancock_data_dir):
    """Test that provenance is properly tracked"""
    config = HancockIngestionConfig(
        hancock_data_dir=mock_hancock_data_dir,
        require_provenance=True
    )
    ingester = HancockDataIngester(config)
    sources = ingester.discover_sources()
    
    for source in sources[:1]:  # Test first source
        documents = ingester.convert_to_source_documents(source)
        for doc in documents:
            assert doc.repo_name
            assert doc.path
            assert doc.digest
            assert doc.license_id


def test_source_type_filtering():
    """Test filtering by source type"""
    config = HancockIngestionConfig(include_sources=["mitre", "cve"])
    
    assert "mitre" in config.include_sources
    assert "cve" in config.include_sources
    assert "ghsa" not in config.include_sources


def test_quality_threshold_validation():
    """Test quality threshold configuration"""
    config = HancockIngestionConfig(
        min_quality_score=0.75,
        commercial_quality_score=0.85
    )
    
    assert config.min_quality_score < config.commercial_quality_score
    assert 0.0 <= config.min_quality_score <= 1.0
    assert 0.0 <= config.commercial_quality_score <= 1.0
