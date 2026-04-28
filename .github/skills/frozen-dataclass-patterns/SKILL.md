---
name: frozen-dataclass-patterns
description: "Use when: creating or modifying dataclasses, working with SourceDocument/DatasetRecord/LearningNode models, encountering 'can't set attribute' errors, need to update frozen dataclass fields, working with immutable models, using dataclasses.replace(). Provides correct patterns for PeachTree's frozen dataclass architecture."
---

# Frozen Dataclass Patterns Skill

## Purpose
Prevent the most common error in PeachTree: attempting to modify frozen dataclass instances. All core models use `@dataclass(frozen=True)` for immutability, provenance safety, and hash stability.

## When to Use This Skill
- Creating new dataclass models in PeachTree
- Modifying fields on SourceDocument, DatasetRecord, LearningNode instances
- Encountering `AttributeError: can't set attribute` errors
- Implementing builder patterns for dataset records
- Working with collections in frozen dataclasses
- Converting between different model types
- Debugging frozen dataclass-related test failures

## Core Concepts

### Why Frozen Dataclasses?

**PeachTree uses frozen dataclasses for:**
1. **Provenance immutability**: Records can't be silently modified after creation
2. **Hash stability**: Models can be used in sets and as dict keys
3. **Thread safety**: Immutable objects are inherently thread-safe
4. **Debugging**: Field values never change after construction
5. **Type safety**: Prevents accidental mutation bugs

### Frozen Dataclass Rules

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class SourceDocument:
    repo_name: str
    path: str
    content: str
    source_type: str = "local-file"
    license_id: str = "unknown"
    commit_sha: str | None = None
    
    # Computed properties are allowed (read-only)
    @property
    def digest(self) -> str:
        """SHA256 hash computed on-demand"""
        return sha256_text(self.content)
```

**CANNOT do after creation:**
- ❌ `doc.content = "new content"`  → `AttributeError: can't set attribute`
- ❌ `doc.repo_name = "new-repo"`  → `AttributeError: can't set attribute`
- ❌ `del doc.path`  → `AttributeError: can't delete attribute`

**CAN do:**
- ✅ Read any field: `content = doc.content`
- ✅ Call property methods: `digest = doc.digest`
- ✅ Create new instance: `new_doc = SourceDocument(...)`
- ✅ Use `replace()`: `new_doc = replace(doc, content="new")`

## Common Patterns

### ✅ Pattern 1: Create New Instance with replace()

**Use when**: You need to update one or more fields on an existing instance

```python
from dataclasses import replace

# Original instance
record = DatasetRecord(
    instruction="Explain this code",
    input="def hello(): pass",
    output="A simple function",
    source_repo="owner/repo",
    source_path="main.py",
    source_digest="abc123",
    quality_score=0.75
)

# ❌ WRONG - will fail
record.quality_score = 0.90

# ✅ CORRECT - create new instance
updated_record = replace(record, quality_score=0.90)

# ✅ ALSO CORRECT - multiple fields
updated_record = replace(
    record,
    quality_score=0.90,
    safety_score=1.0
)
```

### ✅ Pattern 2: Collections Must Be Tuples

**Use when**: Defining fields that hold multiple values

```python
from dataclasses import dataclass, field

# ❌ WRONG - list is mutable
@dataclass(frozen=True)
class BadRecord:
    tags: list[str] = []  # Mutable default, shared across instances!

# ❌ ALSO WRONG - list field
@dataclass(frozen=True)
class StillBad:
    tags: list[str] = field(default_factory=list)  # Mutable in frozen class

# ✅ CORRECT - tuple with factory
@dataclass(frozen=True)
class GoodRecord:
    tags: tuple[str, ...] = field(default_factory=tuple)

# ✅ USAGE
record = GoodRecord(tags=("security", "training", "ml"))
# or
record = GoodRecord()  # empty tuple by default
```

### ✅ Pattern 3: Builder Pattern for Complex Construction

**Use when**: Building records step-by-step with validation

```python
class DatasetRecordBuilder:
    """Builder for DatasetRecord with validation"""
    
    def __init__(self):
        self._instruction: str | None = None
        self._input: str | None = None
        self._output: str | None = None
        # ... other fields
    
    def with_instruction(self, instruction: str) -> "DatasetRecordBuilder":
        """Set instruction (validates non-empty)"""
        if not instruction.strip():
            raise ValueError("Instruction cannot be empty")
        self._instruction = instruction
        return self
    
    def with_source(self, repo: str, path: str, digest: str) -> "DatasetRecordBuilder":
        """Set source provenance"""
        self._source_repo = repo
        self._source_path = path
        self._source_digest = digest
        return self
    
    def build(self) -> DatasetRecord:
        """Create immutable DatasetRecord"""
        if not all([self._instruction, self._source_repo, self._source_path]):
            raise ValueError("Missing required fields")
        
        # ✅ Create frozen instance once
        return DatasetRecord(
            instruction=self._instruction,
            input=self._input or "",
            output=self._output or "",
            source_repo=self._source_repo,
            source_path=self._source_path,
            source_digest=self._source_digest,
            # ... defaults for other fields
        )

# Usage
record = (DatasetRecordBuilder()
    .with_instruction("Explain the code")
    .with_source("owner/repo", "main.py", "abc123")
    .build())
```

### ✅ Pattern 4: Property Methods for Computed Values

**Use when**: Values need to be computed from other fields

```python
@dataclass(frozen=True)
class SourceDocument:
    repo_name: str
    path: str
    content: str
    
    @property
    def digest(self) -> str:
        """SHA256 computed on-demand (not stored)"""
        return sha256_text(self.content)
    
    @property
    def id(self) -> str:
        """Stable ID from repo + path"""
        return f"{self.repo_name}::{self.path}"
    
    @property
    def size_bytes(self) -> int:
        """Content size in bytes"""
        return len(self.content.encode("utf-8"))

# ✅ Usage - computed properties work like fields
doc = SourceDocument(repo_name="owner/repo", path="main.py", content="code")
print(doc.digest)      # Computed each access
print(doc.id)          # Computed each access
print(doc.size_bytes)  # Computed each access

# ❌ Cannot assign to properties
doc.digest = "new-hash"  # AttributeError
```

## Critical API Signatures

### SourceDocument Constructor

```python
# ✅ CORRECT - actual signature
doc = SourceDocument(
    repo_name="0ai-Cyberviser/PeachTree",  # NOT source_repo
    path="README.md",                       # NOT source_path
    content="# PeachTree\n...",
    source_type="local-file",
    license_id="apache-2.0",
    commit_sha="abc123def"                  # optional
)
# digest is computed via @property, don't pass it
# metadata is NOT a parameter (frozen dataclass doesn't accept arbitrary kwargs)

# ❌ WRONG - old/incorrect API
doc = SourceDocument(
    source_repo="...",      # NO - parameter doesn't exist
    source_path="...",      # NO - parameter doesn't exist
    sha256_digest="...",    # NO - computed via property
    metadata={...}          # NO - not a field
)
```

### DatasetRecord Constructor

```python
# ✅ CORRECT
record = DatasetRecord(
    instruction="Explain this code",
    input="Repository: demo\nPath: main.py\n\n...",
    output="This code demonstrates...",
    domain="security",
    source_repo="0ai-Cyberviser/demo",
    source_path="main.py",
    source_digest=sha256_text(content),
    license_id="apache-2.0",
    quality_score=0.85,
    safety_score=1.0,
    created_at=utc_now()  # ISO timestamp
)
```

### DatasetDeduplicator Methods

```python
from peachtree.dedup import DatasetDeduplicator

deduplicator = DatasetDeduplicator()

# ✅ CORRECT method names
report = deduplicator.deduplicate(
    source_path="dataset.jsonl",
    output_path="deduped.jsonl",
    write_output=True
)

# For analysis only (no output file)
report = deduplicator.analyze(source_path="dataset.jsonl")

# ❌ WRONG - does not exist
report = deduplicator.deduplicate_dataset(...)  # NO SUCH METHOD
```

### TrainerHandoffBuilder Methods

```python
from peachtree.trainer_handoff import TrainerHandoffBuilder

builder = TrainerHandoffBuilder(
    dataset_path=Path("dataset.jsonl"),
    model_name="security-model-v1"
)

# ✅ CORRECT method name
handoff = builder.build()

# ❌ WRONG - does not exist
handoff = builder.create_handoff()  # NO SUCH METHOD
```

## Step-by-Step Procedures

### Procedure 1: Updating a Frozen Dataclass Field

**Scenario**: You have a `DatasetRecord` and need to update the `quality_score`

```python
from dataclasses import replace

# 1. Start with existing record
record = DatasetRecord(
    instruction="Explain code",
    # ... all required fields
    quality_score=0.70
)

# 2. Create new instance with updated field
updated_record = replace(record, quality_score=0.85)

# 3. Verify the change
assert updated_record.quality_score == 0.85
assert record.quality_score == 0.70  # Original unchanged

# 4. Use updated record in downstream code
return updated_record
```

### Procedure 2: Creating Model with Collections

**Scenario**: Create `SourceDocument` with tags/categories

```python
from dataclasses import dataclass, field

# 1. Define frozen dataclass with tuple field
@dataclass(frozen=True)
class TaggedDocument:
    repo_name: str
    path: str
    content: str
    tags: tuple[str, ...] = field(default_factory=tuple)

# 2. Create instance with tags
doc = TaggedDocument(
    repo_name="owner/repo",
    path="main.py",
    content="code",
    tags=("python", "security", "ml")
)

# 3. Access tags (immutable)
for tag in doc.tags:
    print(tag)

# 4. Create new doc with different tags (cannot modify existing)
new_doc = replace(doc, tags=("python", "security"))
```

### Procedure 3: Converting Between Model Types

**Scenario**: Convert `SourceDocument` to `DatasetRecord`

```python
def source_to_dataset_record(
    doc: SourceDocument,
    instruction: str,
    output: str
) -> DatasetRecord:
    """Convert SourceDocument to DatasetRecord"""
    
    # 1. Extract provenance from source doc
    source_repo = doc.repo_name
    source_path = doc.path
    source_digest = doc.digest  # Computed property
    
    # 2. Create input context
    input_text = f"Repository: {source_repo}\nPath: {source_path}\n\n{doc.content}"
    
    # 3. Build new frozen instance
    return DatasetRecord(
        instruction=instruction,
        input=input_text,
        output=output,
        source_repo=source_repo,
        source_path=source_path,
        source_digest=source_digest,
        license_id=doc.license_id,
        # ... other fields
    )
```

## Troubleshooting

### Error: `AttributeError: can't set attribute`

**Cause**: Attempting to modify frozen dataclass field

```python
# ❌ Problem code
record.quality_score = 0.90

# ✅ Solution
record = replace(record, quality_score=0.90)
```

### Error: `TypeError: 'list' object is not hashable`

**Cause**: Using list in frozen dataclass instead of tuple

```python
# ❌ Problem code
@dataclass(frozen=True)
class Bad:
    items: list[str] = field(default_factory=list)

# ✅ Solution
@dataclass(frozen=True)
class Good:
    items: tuple[str, ...] = field(default_factory=tuple)
```

### Error: `TypeError: __init__() got an unexpected keyword argument`

**Cause**: Passing incorrect parameter name to constructor

```python
# ❌ Problem code
doc = SourceDocument(source_repo="...", source_path="...")

# ✅ Solution - use actual field names
doc = SourceDocument(repo_name="...", path="...")
```

### Error: `TypeError: replace() got an unexpected keyword argument`

**Cause**: Trying to set field that doesn't exist

```python
# ❌ Problem code
record = replace(record, sha256_digest="...")

# ✅ Solution - check actual field names
# For SourceDocument, 'digest' is a @property, not a field
# It's computed from content automatically
```

## Testing Patterns

### Test Pattern 1: Verify Immutability

```python
def test_source_document_immutability():
    """Verify SourceDocument cannot be modified after creation"""
    doc = SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content="code"
    )
    
    # Verify fields are frozen
    with pytest.raises(AttributeError, match="can't set attribute"):
        doc.content = "new code"
    
    with pytest.raises(AttributeError, match="can't set attribute"):
        doc.repo_name = "other/repo"
```

### Test Pattern 2: Verify replace() Works

```python
def test_dataset_record_replace():
    """Verify replace() creates new instance correctly"""
    record = DatasetRecord(
        instruction="test",
        input="input",
        output="output",
        source_repo="repo",
        source_path="path",
        source_digest="abc",
        quality_score=0.70
    )
    
    # Create updated instance
    updated = replace(record, quality_score=0.90)
    
    # Verify new instance
    assert updated.quality_score == 0.90
    
    # Verify original unchanged
    assert record.quality_score == 0.70
    
    # Verify other fields copied
    assert updated.instruction == record.instruction
    assert updated.source_repo == record.source_repo
```

### Test Pattern 3: Verify Property Methods

```python
def test_source_document_digest_property():
    """Verify digest is computed correctly"""
    content = "test content"
    doc = SourceDocument(
        repo_name="test/repo",
        path="test.py",
        content=content
    )
    
    # Verify digest is computed
    assert doc.digest == sha256_text(content)
    
    # Verify digest cannot be set
    with pytest.raises(AttributeError):
        doc.digest = "custom-hash"
```

## Quick Reference

### Do's ✅
- Use `replace()` to update fields
- Use tuples for collections
- Use `@property` for computed values
- Use builders for complex construction
- Pass correct parameter names to constructors
- Check actual API signatures before using

### Don'ts ❌
- Don't assign to frozen fields directly
- Don't use lists in frozen dataclasses
- Don't pass `sha256_digest` to SourceDocument (it's computed)
- Don't use old parameter names (`source_repo` → `repo_name`)
- Don't call non-existent methods (`deduplicate_dataset` → `deduplicate`)
- Don't delete fields from frozen instances

## Related Documentation

- [PeachTree Models](../../../src/peachtree/models.py) - Core dataclass definitions
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - Contribution guidelines
- [AGENTS.md](../../../AGENTS.md) - Development guide section
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
