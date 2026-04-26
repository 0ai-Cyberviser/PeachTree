# API Reference - Models

Core data models for PeachTree.

## SourceDocument

Raw document from sources.

```python
@dataclass
class SourceDocument:
    id: str
    content: str
    source_repo: str
    source_path: str
    source_digest: str
```

## DatasetRecord

Training-ready record with provenance.

```python
@dataclass
class DatasetRecord:
    id: str  # SHA-256 digest
    text: str
    source_repo: str
    source_path: str
    source_digest: str
    quality_score: float
    license: str
    metadata: dict
```

## DatasetManifest

Metadata for datasets.

```python
@dataclass
class DatasetManifest:
    name: str
    version: str
    created_at: str
    record_count: int
    dataset_path: str
    builder_version: str
```

See source code for full details.
