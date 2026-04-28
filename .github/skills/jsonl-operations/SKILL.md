---
name: jsonl-operations
description: "Use when: reading/writing JSONL dataset files, working with dataset records, handling JSONL format errors, parsing training data, serializing DatasetRecord instances, or encountering JSONL vs JSON array confusion. Provides correct JSONL format, encoding requirements, and provenance tracking patterns."
---

# JSONL Operations Skill

## Purpose
Document correct JSONL (JSON Lines) format for PeachTree datasets. JSONL is the core data format for all training datasets, manifests, and record storage in PeachTree.

## When to Use This Skill
- Reading dataset files from disk
- Writing dataset records to files
- Parsing JSONL format data
- Serializing DatasetRecord instances
- Debugging "JSONDecodeError" or malformed dataset files
- Converting between JSON arrays and JSONL format
- Working with training data handoffs
- Implementing dataset builders or processors

## Core Concepts

### What is JSONL?

**JSONL (JSON Lines)** is a text format where:
- Each line contains exactly **one complete JSON object**
- Lines are separated by newline characters (`\n`)
- The file is **NOT** a JSON array

**✅ CORRECT JSONL Format:**
```jsonl
{"id": "abc123", "instruction": "Explain this code", "output": "This code...", "source_repo": "owner/repo"}
{"id": "def456", "instruction": "What is this?", "output": "This is...", "source_repo": "owner/repo"}
{"id": "ghi789", "instruction": "Describe the function", "output": "The function...", "source_repo": "owner/repo"}
```

**❌ WRONG - JSON Array:**
```json
[
  {"id": "abc123", "instruction": "...", "output": "..."},
  {"id": "def456", "instruction": "...", "output": "..."}
]
```

### Why JSONL?

1. **Streaming**: Can read line-by-line without loading entire file into memory
2. **Append-friendly**: Easy to add records without rewriting entire file
3. **Fault-tolerant**: One corrupted line doesn't break the entire dataset
4. **Tool compatibility**: Works with standard line-based tools (grep, sed, wc -l)
5. **Large datasets**: Efficient for multi-GB training datasets

### Mandatory Fields (Provenance)

**Every JSONL record MUST include:**
- `source_repo` - Repository name (e.g., "0ai-Cyberviser/PeachTree")
- `source_path` - File path within repo (e.g., "src/main.py")
- `source_digest` - SHA256 hash of source content
- `license_id` - License identifier (e.g., "apache-2.0", "mit")
- `created_at` - ISO 8601 timestamp (auto-generated)

**Example complete record:**
```json
{
  "id": "abc123",
  "instruction": "Explain this code",
  "input": "Repository: owner/repo\nPath: main.py\n\ndef hello():\n    pass",
  "output": "This is a simple function that does nothing",
  "domain": "python",
  "source_repo": "owner/repo",
  "source_path": "main.py",
  "source_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "license_id": "mit",
  "quality_score": 0.85,
  "safety_score": 1.0,
  "created_at": "2026-04-27T12:00:00Z"
}
```

## Reading JSONL Files

### ✅ Pattern 1: Read All Records

**Use when**: Loading entire dataset into memory is acceptable

```python
from pathlib import Path
import json

def read_jsonl(path: Path) -> list[dict]:
    """Read all records from JSONL file"""
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():  # Skip empty lines
            records.append(json.loads(line))
    return records

# Usage
dataset_path = Path("datasets/training.jsonl")
records = read_jsonl(dataset_path)
print(f"Loaded {len(records)} records")
```

### ✅ Pattern 2: Stream Records (Memory-Efficient)

**Use when**: Working with large datasets (GB+) that don't fit in memory

```python
from pathlib import Path
import json

def stream_jsonl(path: Path):
    """Stream records one at a time"""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)

# Usage
dataset_path = Path("datasets/large-training.jsonl")
for record in stream_jsonl(dataset_path):
    # Process one record at a time
    quality_score = record.get("quality_score", 0.0)
    if quality_score >= 0.80:
        print(f"High-quality record: {record['id']}")
```

### ✅ Pattern 3: Read with Error Handling

**Use when**: Dataset might have malformed lines

```python
from pathlib import Path
import json
from typing import Iterator

def read_jsonl_safe(path: Path) -> Iterator[dict]:
    """Read JSONL with error handling for malformed lines"""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        
        try:
            record = json.loads(line)
            yield record
        except json.JSONDecodeError as e:
            print(f"Warning: Skipping malformed line {line_number}: {e}")
            continue

# Usage
dataset_path = Path("datasets/possibly-corrupted.jsonl")
valid_records = list(read_jsonl_safe(dataset_path))
print(f"Loaded {len(valid_records)} valid records")
```

### ✅ Pattern 4: Read and Validate Provenance

**Use when**: Ensuring all records have required provenance fields

```python
from pathlib import Path
import json

REQUIRED_FIELDS = {"source_repo", "source_path", "source_digest", "license_id"}

def read_jsonl_validated(path: Path) -> list[dict]:
    """Read JSONL and validate provenance fields"""
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        
        record = json.loads(line)
        
        # Validate provenance fields
        missing = REQUIRED_FIELDS - set(record.keys())
        if missing:
            raise ValueError(
                f"Line {line_number}: Missing provenance fields: {missing}"
            )
        
        records.append(record)
    
    return records

# Usage
dataset_path = Path("datasets/training.jsonl")
validated_records = read_jsonl_validated(dataset_path)
```

## Writing JSONL Files

### ✅ Pattern 1: Write DatasetRecord Instances

**Use when**: Writing PeachTree DatasetRecord objects

```python
from pathlib import Path
from peachtree.models import DatasetRecord

def write_dataset_records(records: list[DatasetRecord], output_path: Path):
    """Write DatasetRecord instances to JSONL file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use to_jsonl() method on each record
    output_path.write_text(
        "\n".join(record.to_jsonl() for record in records) + 
        ("\n" if records else ""),
        encoding="utf-8"
    )

# Usage
records = [
    DatasetRecord(
        instruction="Explain this code",
        input="...",
        output="...",
        source_repo="owner/repo",
        source_path="main.py",
        source_digest="abc123",
        # ... other fields
    )
]
write_dataset_records(records, Path("datasets/output.jsonl"))
```

### ✅ Pattern 2: Write Dictionary Records

**Use when**: Working with raw dictionaries (not DatasetRecord objects)

```python
from pathlib import Path
import json

def write_jsonl_dicts(records: list[dict], output_path: Path):
    """Write dictionary records to JSONL file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use sort_keys=True for consistent ordering
    # Use ensure_ascii=False to preserve UTF-8 characters
    output_path.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True, ensure_ascii=False) 
            for record in records
        ) + ("\n" if records else ""),
        encoding="utf-8"
    )

# Usage
records = [
    {
        "id": "abc123",
        "instruction": "What is this?",
        "output": "This is...",
        "source_repo": "owner/repo",
        "source_path": "file.py",
        "source_digest": "digest123",
        "license_id": "mit"
    }
]
write_jsonl_dicts(records, Path("datasets/output.jsonl"))
```

### ✅ Pattern 3: Append to Existing JSONL

**Use when**: Adding records to existing dataset without rewriting

```python
from pathlib import Path
import json

def append_to_jsonl(records: list[dict], output_path: Path):
    """Append records to existing JSONL file"""
    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open in append mode
    with output_path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")

# Usage
new_records = [{"id": "new123", "instruction": "...", ...}]
append_to_jsonl(new_records, Path("datasets/training.jsonl"))
```

### ✅ Pattern 4: Write with Progress Tracking

**Use when**: Writing large datasets and want progress feedback

```python
from pathlib import Path
import json

def write_jsonl_with_progress(records: list[dict], output_path: Path):
    """Write JSONL with progress tracking"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    total = len(records)
    lines = []
    
    for i, record in enumerate(records, start=1):
        lines.append(json.dumps(record, sort_keys=True, ensure_ascii=False))
        
        # Print progress every 1000 records
        if i % 1000 == 0:
            print(f"Processed {i}/{total} records ({i*100//total}%)")
    
    output_path.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8"
    )
    
    print(f"✅ Wrote {total} records to {output_path}")

# Usage
records = [...]  # Large list of records
write_jsonl_with_progress(records, Path("datasets/large.jsonl"))
```

## Converting Between Formats

### ✅ JSON Array → JSONL

**Use when**: Converting from JSON array format to JSONL

```python
from pathlib import Path
import json

def json_array_to_jsonl(input_path: Path, output_path: Path):
    """Convert JSON array file to JSONL format"""
    # Read JSON array
    data = json.loads(input_path.read_text(encoding="utf-8"))
    
    if not isinstance(data, list):
        raise ValueError("Input file is not a JSON array")
    
    # Write as JSONL
    output_path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in data) + "\n",
        encoding="utf-8"
    )
    
    print(f"✅ Converted {len(data)} records from JSON array to JSONL")

# Usage
json_array_to_jsonl(
    input_path=Path("data/input.json"),
    output_path=Path("data/output.jsonl")
)
```

### ✅ JSONL → JSON Array

**Use when**: Need JSON array format for compatibility (not recommended for large datasets)

```python
from pathlib import Path
import json

def jsonl_to_json_array(input_path: Path, output_path: Path):
    """Convert JSONL to JSON array (NOT recommended for large files)"""
    # Read all records
    records = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    
    # Write as JSON array
    output_path.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    print(f"⚠️  Converted {len(records)} records to JSON array")
    print("Warning: JSON arrays are not memory-efficient for large datasets")

# Usage
jsonl_to_json_array(
    input_path=Path("data/input.jsonl"),
    output_path=Path("data/output.json")
)
```

## Common Operations

### Count Records

```python
from pathlib import Path

def count_jsonl_records(path: Path) -> int:
    """Count records in JSONL file (fast - no parsing)"""
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

# Usage
count = count_jsonl_records(Path("datasets/training.jsonl"))
print(f"Dataset contains {count} records")
```

### Filter Records

```python
from pathlib import Path
import json

def filter_jsonl(
    input_path: Path,
    output_path: Path,
    predicate: callable
):
    """Filter JSONL records based on predicate function"""
    filtered = []
    
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        
        record = json.loads(line)
        if predicate(record):
            filtered.append(record)
    
    output_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in filtered) + "\n",
        encoding="utf-8"
    )
    
    print(f"✅ Filtered {len(filtered)} records (from {count_jsonl_records(input_path)})")

# Usage - keep only high-quality records
filter_jsonl(
    input_path=Path("datasets/all.jsonl"),
    output_path=Path("datasets/high-quality.jsonl"),
    predicate=lambda r: r.get("quality_score", 0) >= 0.80
)
```

### Merge Multiple JSONL Files

```python
from pathlib import Path
import json

def merge_jsonl_files(input_paths: list[Path], output_path: Path):
    """Merge multiple JSONL files into one"""
    all_records = []
    
    for path in input_paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                all_records.append(json.loads(line))
    
    output_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in all_records) + "\n",
        encoding="utf-8"
    )
    
    print(f"✅ Merged {len(all_records)} records from {len(input_paths)} files")

# Usage
merge_jsonl_files(
    input_paths=[
        Path("datasets/part1.jsonl"),
        Path("datasets/part2.jsonl"),
        Path("datasets/part3.jsonl")
    ],
    output_path=Path("datasets/merged.jsonl")
)
```

### Sample Random Records

```python
from pathlib import Path
import json
import random

def sample_jsonl(input_path: Path, output_path: Path, sample_size: int):
    """Sample random records from JSONL file"""
    # Read all records
    records = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    
    # Sample random subset
    if sample_size >= len(records):
        sampled = records
    else:
        sampled = random.sample(records, sample_size)
    
    # Write sampled records
    output_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in sampled) + "\n",
        encoding="utf-8"
    )
    
    print(f"✅ Sampled {len(sampled)} records from {len(records)} total")

# Usage
sample_jsonl(
    input_path=Path("datasets/full.jsonl"),
    output_path=Path("datasets/sample-1000.jsonl"),
    sample_size=1000
)
```

## Troubleshooting

### Error: `JSONDecodeError: Expecting value`

**Cause**: Empty line or line with whitespace only

```python
# ❌ Problem - doesn't skip empty lines
for line in path.read_text(encoding="utf-8").splitlines():
    record = json.loads(line)  # Fails on empty lines

# ✅ Solution - skip empty/whitespace lines
for line in path.read_text(encoding="utf-8").splitlines():
    if line.strip():  # Skip empty lines
        record = json.loads(line)
```

### Error: `JSONDecodeError: Extra data`

**Cause**: Multiple JSON objects on one line

```python
# ❌ Problem - two objects on one line (invalid JSONL)
{"id": "1"} {"id": "2"}

# ✅ Solution - one object per line
{"id": "1"}
{"id": "2"}
```

### Error: `UnicodeDecodeError`

**Cause**: Missing `encoding="utf-8"` parameter

```python
# ❌ Problem - default encoding (may not be UTF-8)
content = path.read_text()

# ✅ Solution - always specify UTF-8
content = path.read_text(encoding="utf-8")
```

### Error: `TypeError: Object of type X is not JSON serializable`

**Cause**: Trying to serialize non-JSON types (Path, datetime, etc.)

```python
# ❌ Problem - Path object not JSON serializable
record = {"path": Path("file.txt"), "created": datetime.now()}
json.dumps(record)  # Fails

# ✅ Solution - convert to JSON-compatible types
record = {"path": str(Path("file.txt")), "created": utc_now()}  # utc_now returns ISO string
json.dumps(record)  # Works
```

### Error: Missing provenance fields

**Cause**: Record doesn't have required source tracking

```python
# ❌ Problem - missing provenance
record = {
    "instruction": "Explain this",
    "output": "This is..."
}

# ✅ Solution - include all provenance fields
record = {
    "instruction": "Explain this",
    "output": "This is...",
    "source_repo": "owner/repo",
    "source_path": "main.py",
    "source_digest": sha256_text(content),
    "license_id": "apache-2.0",
    "created_at": utc_now()
}
```

## Best Practices

### Do's ✅
- Always use `encoding="utf-8"` for read/write
- Skip empty lines with `if line.strip()`
- Use `sort_keys=True` for consistent output
- Use `ensure_ascii=False` to preserve UTF-8 characters
- Include newline at end of file: `"\n".join(...) + "\n"`
- Validate provenance fields (source_repo, source_path, source_digest)
- Use streaming for large datasets (GB+)
- Handle JSON decode errors gracefully

### Don'ts ❌
- Don't use JSON arrays for datasets (use JSONL)
- Don't forget `encoding="utf-8"` parameter
- Don't write multiple objects on one line
- Don't skip provenance fields
- Don't load entire large dataset into memory
- Don't use `json.dump()` for JSONL (use `json.dumps()` per line)
- Don't forget newline at end of file

## Quick Reference

### Read JSONL
```python
records = [
    json.loads(line) 
    for line in path.read_text(encoding="utf-8").splitlines() 
    if line.strip()
]
```

### Write JSONL (dicts)
```python
path.write_text(
    "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
    encoding="utf-8"
)
```

### Write JSONL (DatasetRecord)
```python
path.write_text(
    "\n".join(record.to_jsonl() for record in records) + "\n",
    encoding="utf-8"
)
```

### Count Records
```python
count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
```

## Related Documentation

- [PeachTree Models](../../../src/peachtree/models.py) - DatasetRecord.to_jsonl() method
- [Dataset Builder](../../../src/peachtree/builder.py) - JSONL writing patterns
- [Deduplication](../../../src/peachtree/dedup.py) - JSONL reading/writing
- [AGENTS.md](../../../AGENTS.md) - Development guide
- [JSONL Specification](http://jsonlines.org/) - Official format documentation
