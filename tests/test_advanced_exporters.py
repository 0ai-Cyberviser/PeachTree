"""
Tests for advanced_exporters module
"""
from pathlib import Path
import pytest
import json
from peachtree.advanced_exporters import (
    AdvancedExporters,
    ExportResult,
    get_advanced_format_names,
)


@pytest.fixture
def test_dataset(tmp_path):
    """Create test dataset"""
    dataset = tmp_path / "test.jsonl"
    records = [
        {
            "id": "1",
            "content": "First record",
            "source_repo": "test/repo",
            "source_path": "file1.txt",
        },
        {
            "id": "2",
            "content": "Second record",
            "source_repo": "test/repo",
            "source_path": "file2.txt",
        },
        {
            "id": "3",
            "content": "Third record",
            "source_repo": "test/repo",
            "source_path": "file3.txt",
        },
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_export_result_creation():
    """Test ExportResult dataclass"""
    result = ExportResult(
        source_dataset="input.jsonl",
        output_path="output.jsonl",
        export_format="llama3",
        records_exported=100,
        metadata={"key": "value"},
    )
    
    assert result.source_dataset == "input.jsonl"
    assert result.export_format == "llama3"
    assert result.to_dict()["records_exported"] == 100


def test_get_advanced_format_names():
    """Test retrieving format names"""
    formats = get_advanced_format_names()
    
    assert isinstance(formats, list)
    assert len(formats) == 8
    assert "llama3" in formats
    assert "gemini" in formats
    assert "claude" in formats
    assert "hancock_cybersecurity" in formats
    assert "mistral" in formats
    assert "qwen" in formats
    assert "unsloth" in formats
    assert "jsonl_conversation" in formats


def test_export_llama3(test_dataset, tmp_path):
    """Test Llama 3 export format"""
    output = tmp_path / "llama3.jsonl"
    
    result = AdvancedExporters.export_llama3(
        test_dataset,
        output,
        system_prompt="Custom system prompt",
    )
    
    assert result.export_format == "llama3"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    assert len(lines) == 3
    
    record = json.loads(lines[0])
    assert "messages" in record
    assert len(record["messages"]) == 2
    assert record["messages"][0]["role"] == "system"
    assert record["messages"][1]["role"] == "user"
    assert "metadata" in record


def test_export_gemini(test_dataset, tmp_path):
    """Test Gemini export format"""
    output = tmp_path / "gemini.jsonl"
    
    result = AdvancedExporters.export_gemini(test_dataset, output)
    
    assert result.export_format == "gemini"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "contents" in record
    assert record["contents"][0]["role"] == "user"
    assert "parts" in record["contents"][0]
    assert "text" in record["contents"][0]["parts"][0]


def test_export_claude(test_dataset, tmp_path):
    """Test Claude export format"""
    output = tmp_path / "claude.jsonl"
    
    result = AdvancedExporters.export_claude(
        test_dataset,
        output,
        system_prompt="Claude system prompt",
    )
    
    assert result.export_format == "claude"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "system" in record
    assert record["system"] == "Claude system prompt"
    assert "messages" in record
    assert record["messages"][0]["role"] == "user"


def test_export_hancock_cybersecurity(test_dataset, tmp_path):
    """Test Hancock cybersecurity export format"""
    output = tmp_path / "hancock.jsonl"
    
    result = AdvancedExporters.export_hancock_cybersecurity(test_dataset, output)
    
    assert result.export_format == "hancock_cybersecurity"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert record["task"] == "cybersecurity_analysis"
    assert "input" in record
    assert "metadata" in record
    assert "security_context" in record
    assert "iocs_present" in record["security_context"]
    assert "mitre_tactics" in record["security_context"]


def test_export_mistral(test_dataset, tmp_path):
    """Test Mistral export format"""
    output = tmp_path / "mistral.jsonl"
    
    result = AdvancedExporters.export_mistral(test_dataset, output)
    
    assert result.export_format == "mistral"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "messages" in record
    assert record["messages"][0]["role"] == "user"


def test_export_qwen(test_dataset, tmp_path):
    """Test Qwen export format"""
    output = tmp_path / "qwen.jsonl"
    
    result = AdvancedExporters.export_qwen(
        test_dataset,
        output,
        system_prompt="Qwen system prompt",
    )
    
    assert result.export_format == "qwen"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "conversations" in record
    assert len(record["conversations"]) == 2
    assert record["conversations"][0]["role"] == "system"
    assert record["conversations"][1]["role"] == "user"


def test_export_unsloth(test_dataset, tmp_path):
    """Test Unsloth export format"""
    output = tmp_path / "unsloth.jsonl"
    
    result = AdvancedExporters.export_unsloth(test_dataset, output)
    
    assert result.export_format == "unsloth"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "text" in record
    assert "metadata" in record
    assert "source_repo" in record["metadata"]


def test_export_jsonl_conversation(test_dataset, tmp_path):
    """Test conversation JSONL export"""
    output = tmp_path / "conversation.jsonl"
    
    result = AdvancedExporters.export_jsonl_with_conversation(test_dataset, output)
    
    assert result.export_format == "jsonl_conversation"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify format
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "conversation" in record
    assert len(record["conversation"]) == 1
    assert record["conversation"][0]["role"] == "user"
    assert "metadata" in record


def test_export_with_custom_conversation_field(test_dataset, tmp_path):
    """Test conversation export with custom field name"""
    output = tmp_path / "custom.jsonl"
    
    result = AdvancedExporters.export_jsonl_with_conversation(
        test_dataset,
        output,
        conversation_field="messages",
    )
    
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "messages" in record
    assert result.metadata["conversation_field"] == "messages"


def test_export_creates_parent_directories(test_dataset, tmp_path):
    """Test that export creates parent directories"""
    output = tmp_path / "nested" / "dir" / "output.jsonl"
    
    AdvancedExporters.export_llama3(test_dataset, output)
    
    assert output.exists()
    assert output.parent.exists()


def test_export_handles_empty_lines(tmp_path):
    """Test exporting dataset with empty lines"""
    dataset = tmp_path / "empty_lines.jsonl"
    dataset.write_text('{"id": "1", "content": "First"}\n\n{"id": "2", "content": "Second"}\n')
    
    output = tmp_path / "output.jsonl"
    result = AdvancedExporters.export_llama3(dataset, output)
    
    assert result.records_exported == 2


def test_export_preserves_provenance(test_dataset, tmp_path):
    """Test that provenance is preserved in exports"""
    output = tmp_path / "provenance.jsonl"
    
    AdvancedExporters.export_llama3(test_dataset, output)
    
    lines = output.read_text().strip().split("\n")
    record = json.loads(lines[0])
    
    assert "metadata" in record
    assert "source_repo" in record["metadata"]
    assert record["metadata"]["source_repo"] == "test/repo"


def test_export_result_to_dict():
    """Test ExportResult to_dict method"""
    result = ExportResult(
        source_dataset="input.jsonl",
        output_path="output.jsonl",
        export_format="llama3",
        records_exported=50,
        metadata={"system_prompt": "Test"},
    )
    
    data = result.to_dict()
    
    assert data["source_dataset"] == "input.jsonl"
    assert data["output_path"] == "output.jsonl"
    assert data["export_format"] == "llama3"
    assert data["records_exported"] == 50
    assert data["metadata"]["system_prompt"] == "Test"


def test_all_formats_export_same_count(test_dataset, tmp_path):
    """Test that all formats export the same number of records"""
    formats = {
        "llama3": AdvancedExporters.export_llama3,
        "gemini": AdvancedExporters.export_gemini,
        "claude": AdvancedExporters.export_claude,
        "hancock": AdvancedExporters.export_hancock_cybersecurity,
        "mistral": AdvancedExporters.export_mistral,
        "qwen": AdvancedExporters.export_qwen,
        "unsloth": AdvancedExporters.export_unsloth,
    }
    
    results = []
    for name, export_fn in formats.items():
        output = tmp_path / f"{name}.jsonl"
        result = export_fn(test_dataset, output)
        results.append(result.records_exported)
    
    assert all(count == 3 for count in results)


def test_export_with_missing_fields(tmp_path):
    """Test exporting records with missing optional fields"""
    dataset = tmp_path / "missing.jsonl"
    records = [
        {"id": "1", "content": "Only content"},
        {"id": "2", "content": "No provenance"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    
    output = tmp_path / "output.jsonl"
    result = AdvancedExporters.export_llama3(dataset, output)
    
    assert result.records_exported == 2
