"""Tests for export_formats_v2 module"""
import json
import pytest

from peachtree.export_formats_v2 import (
    ExportFormatsV2,
    ExportFormatResult,
)


@pytest.fixture
def exporter():
    return ExportFormatsV2()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {
            "id": "1",
            "content": "Test content 1",
            "quality_score": 85.0,
            "metadata": {"source": "test"},
        },
        {
            "id": "2",
            "content": "Test content 2",
            "prompt": "What is AI?",
            "response": "AI is artificial intelligence",
            "quality_score": 90.0,
        },
        {
            "id": "3",
            "content": "Test content 3",
            "instruction": "Explain ML",
            "input": "",
            "output": "ML is machine learning",
        },
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_get_supported_formats(exporter):
    formats = exporter.get_supported_formats()
    assert len(formats) == 6
    assert "pytorch" in formats
    assert "tensorflow" in formats
    assert "huggingface" in formats
    assert "alpaca" in formats
    assert "sharegpt" in formats
    assert "openai-finetune" in formats


def test_export_pytorch(exporter, sample_dataset, tmp_path):
    output = tmp_path / "pytorch.jsonl"
    
    result = exporter.export_pytorch(sample_dataset, output)
    
    assert result.format_name == "pytorch"
    assert result.records_exported == 3
    assert result.output_size_bytes > 0
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "text" in records[0]
    assert "label" in records[0]
    assert "metadata" in records[0]


def test_export_tensorflow(exporter, sample_dataset, tmp_path):
    output = tmp_path / "tensorflow.jsonl"
    
    result = exporter.export_tensorflow(sample_dataset, output)
    
    assert result.format_name == "tensorflow"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "features" in records[0]
    assert "label" in records[0]
    assert "text" in records[0]["features"]
    assert "quality_score" in records[0]["features"]


def test_export_huggingface(exporter, sample_dataset, tmp_path):
    output = tmp_path / "huggingface.jsonl"
    
    result = exporter.export_huggingface(sample_dataset, output)
    
    assert result.format_name == "huggingface"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "text" in records[0]
    assert "meta" in records[0]
    assert "quality_score" in records[0]["meta"]


def test_export_alpaca(exporter, sample_dataset, tmp_path):
    output = tmp_path / "alpaca.jsonl"
    
    result = exporter.export_alpaca(sample_dataset, output)
    
    assert result.format_name == "alpaca"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "instruction" in records[0]
    assert "input" in records[0]
    assert "output" in records[0]
    
    # Check record with instruction field
    assert records[2]["instruction"] == "Explain ML"
    assert records[2]["output"] == "ML is machine learning"


def test_export_sharegpt(exporter, sample_dataset, tmp_path):
    output = tmp_path / "sharegpt.jsonl"
    
    result = exporter.export_sharegpt(sample_dataset, output)
    
    assert result.format_name == "sharegpt"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "conversations" in records[0]
    assert "id" in records[0]
    assert isinstance(records[0]["conversations"], list)
    
    # Check record with prompt/response
    assert len(records[1]["conversations"]) == 2
    assert records[1]["conversations"][0]["from"] == "human"
    assert records[1]["conversations"][1]["from"] == "gpt"
    assert records[1]["conversations"][0]["value"] == "What is AI?"
    assert records[1]["conversations"][1]["value"] == "AI is artificial intelligence"


def test_export_openai_finetune(exporter, sample_dataset, tmp_path):
    output = tmp_path / "openai.jsonl"
    
    result = exporter.export_openai_finetune(sample_dataset, output, system_prompt="You are helpful.")
    
    assert result.format_name == "openai-finetune"
    assert result.records_exported == 3
    assert output.exists()
    
    # Verify output format
    with open(output) as f:
        records = [json.loads(line) for line in f]
    
    assert len(records) == 3
    assert "messages" in records[0]
    assert isinstance(records[0]["messages"], list)
    
    # Check system message
    assert records[0]["messages"][0]["role"] == "system"
    assert records[0]["messages"][0]["content"] == "You are helpful."
    
    # Check record with prompt/response
    assert records[1]["messages"][1]["role"] == "user"
    assert records[1]["messages"][2]["role"] == "assistant"


def test_export_to_format_pytorch(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(sample_dataset, output, "pytorch")
    
    assert result.format_name == "pytorch"
    assert result.records_exported == 3


def test_export_to_format_tensorflow(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(sample_dataset, output, "tensorflow")
    
    assert result.format_name == "tensorflow"
    assert result.records_exported == 3


def test_export_to_format_huggingface(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(sample_dataset, output, "huggingface")
    
    assert result.format_name == "huggingface"
    assert result.records_exported == 3


def test_export_to_format_alpaca(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(sample_dataset, output, "alpaca")
    
    assert result.format_name == "alpaca"
    assert result.records_exported == 3


def test_export_to_format_sharegpt(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(sample_dataset, output, "sharegpt")
    
    assert result.format_name == "sharegpt"
    assert result.records_exported == 3


def test_export_to_format_openai(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    result = exporter.export_to_format(
        sample_dataset,
        output,
        "openai-finetune",
        system_prompt="Test prompt",
    )
    
    assert result.format_name == "openai-finetune"
    assert result.records_exported == 3


def test_export_to_format_invalid(exporter, sample_dataset, tmp_path):
    output = tmp_path / "output.jsonl"
    
    with pytest.raises(ValueError, match="Unsupported export format"):
        exporter.export_to_format(sample_dataset, output, "invalid_format")


def test_batch_export(exporter, sample_dataset, tmp_path):
    output_dir = tmp_path / "exports"
    formats = ["pytorch", "tensorflow", "huggingface"]
    
    results = exporter.batch_export(sample_dataset, output_dir, formats)
    
    assert len(results) == 3
    assert "pytorch" in results
    assert "tensorflow" in results
    assert "huggingface" in results
    
    # Verify all files created
    for format_name in formats:
        output_file = output_dir / f"sample_{format_name}.jsonl"
        assert output_file.exists()


def test_batch_export_with_invalid_format(exporter, sample_dataset, tmp_path):
    output_dir = tmp_path / "exports"
    formats = ["pytorch", "invalid", "tensorflow"]
    
    results = exporter.batch_export(sample_dataset, output_dir, formats)
    
    # Should only export valid formats
    assert len(results) == 2
    assert "pytorch" in results
    assert "tensorflow" in results
    assert "invalid" not in results


def test_export_format_result_creation():
    result = ExportFormatResult(
        source_path="/path/to/source.jsonl",
        output_path="/path/to/output.jsonl",
        format_name="pytorch",
        records_exported=100,
        output_size_bytes=5000,
    )
    
    assert result.format_name == "pytorch"
    assert result.records_exported == 100


def test_export_format_result_to_dict():
    result = ExportFormatResult(
        source_path="/path/to/source.jsonl",
        output_path="/path/to/output.jsonl",
        format_name="tensorflow",
        records_exported=50,
        output_size_bytes=2500,
    )
    
    d = result.to_dict()
    assert d["format_name"] == "tensorflow"
    assert d["records_exported"] == 50
    assert d["output_size_bytes"] == 2500


def test_export_empty_dataset(exporter, tmp_path):
    empty_dataset = tmp_path / "empty.jsonl"
    empty_dataset.touch()
    
    output = tmp_path / "output.jsonl"
    result = exporter.export_pytorch(empty_dataset, output)
    
    assert result.records_exported == 0


def test_export_with_conversations_field(exporter, tmp_path):
    dataset = tmp_path / "conversations.jsonl"
    record = {
        "id": "1",
        "conversations": [
            {"from": "human", "value": "Hello"},
            {"from": "gpt", "value": "Hi there!"},
        ],
    }
    with open(dataset, 'w') as f:
        f.write(json.dumps(record) + "\n")
    
    output = tmp_path / "sharegpt.jsonl"
    result = exporter.export_sharegpt(dataset, output)
    
    assert result.records_exported == 1
    
    with open(output) as f:
        exported = json.loads(f.readline())
    
    assert exported["conversations"][0]["value"] == "Hello"
    assert exported["conversations"][1]["value"] == "Hi there!"


def test_export_with_messages_field(exporter, tmp_path):
    dataset = tmp_path / "messages.jsonl"
    record = {
        "id": "1",
        "messages": [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ],
    }
    with open(dataset, 'w') as f:
        f.write(json.dumps(record) + "\n")
    
    output = tmp_path / "openai.jsonl"
    result = exporter.export_openai_finetune(dataset, output)
    
    assert result.records_exported == 1
    
    with open(output) as f:
        exported = json.loads(f.readline())
    
    # Should have system message + original messages
    assert len(exported["messages"]) == 3
    assert exported["messages"][0]["role"] == "system"
    assert exported["messages"][1]["role"] == "user"
    assert exported["messages"][2]["role"] == "assistant"
