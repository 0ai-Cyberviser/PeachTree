# JSONL Dataset Format

PeachTree uses JSONL (JSON Lines) format for datasets, where each line is a valid JSON object.

## Format Specification

### DatasetRecord Structure

Each line in a PeachTree JSONL file is a `DatasetRecord`:

```json
{
  "id": "sha256-abc123def456789",
  "text": "The actual document content goes here...",
  "source_repo": "owner/repository-name",
  "source_path": "path/to/source/file.py",
  "source_digest": "abc123def456",
  "quality_score": 0.92,
  "license": "MIT",
  "metadata": {
    "document_type": "code",
    "language": "python",
    "lines": 45,
    "created_at": "2026-04-26T10:30:00Z"
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SHA-256 digest of content (deterministic) |
| `text` | string | Complete document/record content |
| `source_repo` | string | Source repository identifier (owner/repo) |
| `source_path` | string | Path within repository to source file |
| `source_digest` | string | Git commit hash or version identifier |
| `quality_score` | float | Quality metric (0.0 - 1.0) |
| `license` | string | License identifier (e.g., "MIT", "Apache-2.0") |
| `metadata` | object | Custom metadata dictionary |

## Example Records

### Python Code

```json
{
  "id": "sha256-f1e2d3c4b5a69f8e7d6c5b4a3f2e1d0c",
  "text": "def analyze_security(code: str) -> dict:\n    \"\"\"Analyze code for security issues.\"\"\"\n    return {\"vulnerabilities\": 0}",
  "source_repo": "0ai-Cyberviser/SecurityAnalyzer",
  "source_path": "src/analyzer.py",
  "source_digest": "abc123def456789",
  "quality_score": 0.95,
  "license": "MIT",
  "metadata": {
    "document_type": "code",
    "language": "python",
    "lines": 3
  }
}
```

### Documentation

```json
{
  "id": "sha256-a1b2c3d4e5f6789abcdef123456789ab",
  "text": "# Security Best Practices\n\nAlways validate user input...",
  "source_repo": "0ai-Cyberviser/Handbook",
  "source_path": "docs/security.md",
  "source_digest": "def789abc123",
  "quality_score": 0.88,
  "license": "CC-BY-4.0",
  "metadata": {
    "document_type": "documentation",
    "format": "markdown",
    "sections": ["overview", "best-practices", "examples"]
  }
}
```

## File Format

### Valid JSONL File

Each line must be valid JSON:

```jsonl
{"id": "sha256-abc...", "text": "content1", ...}
{"id": "sha256-def...", "text": "content2", ...}
{"id": "sha256-ghi...", "text": "content3", ...}
```

### Invalid Formats

These are NOT valid JSONL:

```
# Multi-line JSON (invalid)
{
  "id": "sha256-abc",
  "text": "content"
}

# Trailing comma (invalid)
{"id": "sha256-abc", "text": "content",}

# Comments (invalid)
{"id": "sha256-abc"} // This is a comment
```

## Reading/Writing JSONL

### Python

```python
import json

# Reading
with open("dataset.jsonl") as f:
    for line in f:
        record = json.loads(line)
        print(record["id"], record["text"][:50])

# Writing
with open("dataset.jsonl", "w") as f:
    for record in records:
        f.write(json.dumps(record) + "\n")
```

### Command Line

```bash
# Count records
wc -l dataset.jsonl

# Pretty print first record
head -1 dataset.jsonl | python -m json.tool

# Filter by quality score
jq 'select(.quality_score >= 0.9)' dataset.jsonl > filtered.jsonl

# Extract text only
jq -r '.text' dataset.jsonl > texts.txt
```

## Compatibility

- **Size**: No theoretical limit, tested up to 10M records
- **Encoding**: UTF-8 (strict)
- **Line endings**: LF or CRLF supported
- **Parsers**: Standard JSON parsers work (streaming recommended for large files)

## Best Practices

1. **Always include provenance** - Never omit source_repo, source_path
2. **Deterministic IDs** - Use SHA-256 of content (PeachTree does this automatically)
3. **Quality scores** - Run quality checks before training
4. **License compliance** - Verify all licenses are compatible
5. **Validate before use** - Use `peachtree audit` before training
6. **Stream processing** - Don't load entire file into memory for large datasets
