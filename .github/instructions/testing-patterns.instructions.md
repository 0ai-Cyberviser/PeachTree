---
applyTo:
  - "tests/**/*.py"
  - "**/test_*.py"
description: "Testing patterns and conventions for PeachTree test suite. Use when writing tests, creating test fixtures, mocking frozen dataclasses, or debugging test failures. Provides pytest patterns, fixture usage, frozen dataclass testing, and JSONL test data creation."
---

# PeachTree Testing Patterns

## Test File Structure

**Mirror source structure:**
```
src/peachtree/
├── hancock_integration.py
└── dedup.py

tests/
├── test_hancock_integration.py  # Mirrors hancock_integration.py
└── test_dedup.py                # Mirrors dedup.py
```

**One test file per source module.** Test file name: `test_<module_name>.py`

## Essential Imports

```python
import json
from pathlib import Path
from dataclasses import replace
import pytest
from peachtree.models import SourceDocument, DatasetRecord
from peachtree.<module> import <ClassUnderTest>
```

## Pytest Fixtures

### tmp_path Fixture (Most Common)

**Use for**: Creating temporary files and directories

```python
def test_read_dataset(tmp_path: Path):
    """Test reading JSONL dataset"""
    # tmp_path is automatically created and cleaned up
    dataset_file = tmp_path / "test.jsonl"
    
    # Write test data
    dataset_file.write_text(
        '{"id": "1", "instruction": "test"}\n',
        encoding="utf-8"
    )
    
    # Test your function
    records = read_dataset(dataset_file)
    assert len(records) == 1
```

### Fixture Patterns for PeachTree

```python
@pytest.fixture
def sample_source_document() -> SourceDocument:
    """Reusable SourceDocument for tests"""
    return SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content="test content",
        source_type="local-file",
        license_id="mit"
    )

@pytest.fixture
def sample_dataset_record() -> DatasetRecord:
    """Reusable DatasetRecord for tests"""
    return DatasetRecord(
        instruction="Test instruction",
        input="Test input",
        output="Test output",
        source_repo="test/repo",
        source_path="test.py",
        source_digest="abc123",
        license_id="mit"
    )

@pytest.fixture
def test_jsonl_file(tmp_path: Path) -> Path:
    """Create test JSONL file"""
    file = tmp_path / "test.jsonl"
    records = [
        {"id": "1", "instruction": "First"},
        {"id": "2", "instruction": "Second"}
    ]
    file.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8"
    )
    return file
```

## Testing Frozen Dataclasses

### ✅ Test Immutability

```python
def test_source_document_immutability():
    """Verify SourceDocument fields cannot be modified"""
    doc = SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content="code"
    )
    
    # Should raise AttributeError
    with pytest.raises(AttributeError, match="can't set attribute"):
        doc.content = "new code"
```

### ✅ Test replace() Pattern

```python
def test_dataset_record_replace():
    """Verify replace() creates new instance correctly"""
    original = DatasetRecord(
        instruction="test",
        input="input",
        output="output",
        source_repo="repo",
        source_path="path",
        source_digest="abc",
        quality_score=0.70
    )
    
    # Use replace() to update field
    updated = replace(original, quality_score=0.90)
    
    # Verify new instance
    assert updated.quality_score == 0.90
    
    # Verify original unchanged
    assert original.quality_score == 0.70
    
    # Verify other fields copied
    assert updated.instruction == original.instruction
```

### ✅ Test Property Methods

```python
def test_source_document_digest_property():
    """Verify digest property is computed correctly"""
    from peachtree.models import sha256_text
    
    content = "test content"
    doc = SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content=content
    )
    
    # Digest is computed via property
    assert doc.digest == sha256_text(content)
    
    # Cannot be set directly
    with pytest.raises(AttributeError):
        doc.digest = "custom-hash"
```

## Creating Test JSONL Data

### Pattern 1: Write Test Dataset

```python
def test_read_jsonl_dataset(tmp_path: Path):
    """Test JSONL reading"""
    # Create test JSONL file
    dataset_file = tmp_path / "dataset.jsonl"
    
    test_records = [
        {
            "id": "rec1",
            "instruction": "Explain this",
            "output": "This is...",
            "source_repo": "test/repo",
            "source_path": "file.py",
            "source_digest": "abc123",
            "license_id": "mit"
        },
        {
            "id": "rec2",
            "instruction": "What is this?",
            "output": "This is...",
            "source_repo": "test/repo",
            "source_path": "other.py",
            "source_digest": "def456",
            "license_id": "apache-2.0"
        }
    ]
    
    # Write JSONL (one JSON object per line)
    dataset_file.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in test_records) + "\n",
        encoding="utf-8"
    )
    
    # Test your function
    result = process_dataset(dataset_file)
    assert len(result) == 2
```

### Pattern 2: Helper Function

```python
def write_test_dataset(path: Path, records: list[dict]) -> Path:
    """Helper to write test JSONL datasets"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8"
    )
    return path

def test_with_helper(tmp_path: Path):
    """Test using helper function"""
    records = [{"id": "1", "data": "test"}]
    dataset = write_test_dataset(tmp_path / "data.jsonl", records)
    
    result = load_dataset(dataset)
    assert len(result) == 1
```

## Mocking Patterns

### Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock_manifest(tmp_path: Path):
    """Test with mocked manifest"""
    # Create mock manifest
    mock_manifest = Mock()
    mock_manifest.dataset_path = str(tmp_path / "dataset.jsonl")
    mock_manifest.record_count = 100
    mock_manifest.domain = "security"
    
    # Use in test
    result = process_manifest(mock_manifest)
    assert result is not None
```

### Mock File Operations

```python
@patch('pathlib.Path.read_text')
def test_read_with_mock(mock_read):
    """Test with mocked file read"""
    # Setup mock
    mock_read.return_value = '{"id": "1"}\n{"id": "2"}\n'
    
    # Test
    records = read_jsonl(Path("fake.jsonl"))
    assert len(records) == 2
```

## Parametrized Tests

### Test Multiple Inputs

```python
@pytest.mark.parametrize("score,expected", [
    (0.90, "high"),
    (0.75, "medium"),
    (0.50, "low"),
    (0.20, "very-low"),
])
def test_quality_classification(score, expected):
    """Test quality score classification"""
    result = classify_quality(score)
    assert result == expected
```

### Test Multiple Scenarios

```python
@pytest.mark.parametrize("source_type,expected_pattern", [
    ("local-file", r"^file://.*"),
    ("github", r"^https://github\.com/.*"),
    ("remote-url", r"^https://.*"),
])
def test_source_uri_patterns(source_type, expected_pattern):
    """Test URI generation for different source types"""
    import re
    uri = generate_source_uri(source_type, "test.py")
    assert re.match(expected_pattern, uri)
```

## Error Testing

### Test Expected Exceptions

```python
def test_invalid_jsonl_raises_error(tmp_path: Path):
    """Test that invalid JSONL raises JSONDecodeError"""
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text("not json\n", encoding="utf-8")
    
    with pytest.raises(json.JSONDecodeError):
        read_jsonl(bad_file)
```

### Test Validation Errors

```python
def test_missing_provenance_raises_error():
    """Test that records without provenance raise ValueError"""
    invalid_record = {
        "instruction": "test",
        "output": "test"
        # Missing: source_repo, source_path, source_digest
    }
    
    with pytest.raises(ValueError, match="Missing provenance"):
        validate_record(invalid_record)
```

## Testing CLI Commands

### Test CLI Functions

```python
from peachtree.cli import run_quality_check

def test_quality_cli(tmp_path: Path):
    """Test quality CLI command"""
    # Create test dataset
    dataset = tmp_path / "dataset.jsonl"
    write_test_dataset(dataset, [
        {"id": "1", "instruction": "test", "quality_score": 0.85}
    ])
    
    # Mock args
    class Args:
        input = str(dataset)
        output = str(tmp_path / "report.json")
        min_score = 0.70
    
    # Run CLI function
    result = run_quality_check(Args())
    assert result == 0  # Exit code 0 = success
    
    # Verify output
    report = json.loads((tmp_path / "report.json").read_text())
    assert "summary" in report
```

## Coverage Patterns

### Ensure Key Paths Tested

```python
def test_all_branches_covered():
    """Test both success and failure paths"""
    # Test success path
    result = process_with_validation(valid_input)
    assert result.success is True
    
    # Test failure path
    result = process_with_validation(invalid_input)
    assert result.success is False
    assert "error" in result.message
```

### Test Edge Cases

```python
def test_edge_cases():
    """Test boundary conditions"""
    # Empty dataset
    assert process_dataset([]) == []
    
    # Single record
    assert len(process_dataset([{"id": "1"}])) == 1
    
    # Very large dataset (performance check)
    large_dataset = [{"id": str(i)} for i in range(10000)]
    result = process_dataset(large_dataset)
    assert len(result) == 10000
```

## Test Organization

### Group Related Tests

```python
class TestDatasetBuilder:
    """Tests for DatasetBuilder class"""
    
    def test_init(self):
        """Test builder initialization"""
        builder = DatasetBuilder()
        assert builder is not None
    
    def test_add_record(self):
        """Test adding record to builder"""
        builder = DatasetBuilder()
        builder.add_record({"id": "1"})
        assert len(builder.records) == 1
    
    def test_build(self, tmp_path: Path):
        """Test building final dataset"""
        builder = DatasetBuilder()
        builder.add_record({"id": "1"})
        output = builder.build(tmp_path / "output.jsonl")
        assert output.exists()
```

## Common Test Patterns

### Test JSONL Reading/Writing

```python
def test_jsonl_roundtrip(tmp_path: Path):
    """Test write then read produces same data"""
    original_records = [
        {"id": "1", "data": "first"},
        {"id": "2", "data": "second"}
    ]
    
    # Write
    file = tmp_path / "test.jsonl"
    write_jsonl(file, original_records)
    
    # Read
    loaded_records = read_jsonl(file)
    
    # Verify
    assert loaded_records == original_records
```

### Test Provenance Tracking

```python
def test_provenance_preserved():
    """Test that provenance is preserved through transformations"""
    source_doc = SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content="code",
        license_id="mit"
    )
    
    # Transform to dataset record
    record = transform_to_record(source_doc)
    
    # Verify provenance preserved
    assert record.source_repo == source_doc.repo_name
    assert record.source_path == source_doc.path
    assert record.source_digest == source_doc.digest
    assert record.license_id == source_doc.license_id
```

## Debugging Failed Tests

### Use pytest -v for Verbose Output

```bash
pytest tests/test_hancock_integration.py -v
```

### Use --tb=short for Concise Tracebacks

```bash
pytest tests/ --tb=short
```

### Run Specific Test

```bash
pytest tests/test_dedup.py::test_deduplicate -v
```

### Use pytest.set_trace() for Debugging

```python
def test_complex_logic():
    """Test with debugging"""
    result = complex_function(input_data)
    
    # Drop into debugger
    import pytest; pytest.set_trace()
    
    assert result == expected
```

## Anti-Patterns to Avoid

❌ **Don't use hardcoded paths**
```python
# Bad
def test_bad():
    data = Path("/tmp/test.jsonl")  # Hardcoded path
```

✅ **Use tmp_path fixture**
```python
# Good
def test_good(tmp_path: Path):
    data = tmp_path / "test.jsonl"  # Temporary path
```

❌ **Don't modify frozen dataclass in tests**
```python
# Bad
def test_bad():
    doc = SourceDocument(...)
    doc.content = "new"  # Will fail!
```

✅ **Use replace() for modifications**
```python
# Good
def test_good():
    doc = SourceDocument(...)
    new_doc = replace(doc, content="new")
```

❌ **Don't forget encoding parameter**
```python
# Bad
path.write_text(content)  # May use wrong encoding
```

✅ **Always specify UTF-8**
```python
# Good
path.write_text(content, encoding="utf-8")
```

## Quick Reference

### Create Test File
```python
def test_example(tmp_path: Path):
    file = tmp_path / "test.jsonl"
    file.write_text('{"id": "1"}\n', encoding="utf-8")
```

### Test Frozen Dataclass
```python
with pytest.raises(AttributeError):
    frozen_obj.field = "value"
```

### Parametrize Test
```python
@pytest.mark.parametrize("input,expected", [(1, 2), (2, 4)])
def test_double(input, expected):
    assert double(input) == expected
```

### Mock Object
```python
from unittest.mock import Mock
mock = Mock()
mock.method.return_value = "value"
```

## Related Documentation

- [pytest documentation](https://docs.pytest.org/)
- [AGENTS.md](../../../AGENTS.md) - Testing requirements
- [frozen-dataclass-patterns skill](../skills/frozen-dataclass-patterns/SKILL.md)
- [jsonl-operations skill](../skills/jsonl-operations/SKILL.md)
