# API Reference - Builder

Main API for building JSONL datasets.

## DatasetBuilder

```python
from peachtree import DatasetBuilder, SourceDocument

builder = DatasetBuilder()

# Create records from documents
records = builder.build_records(sources)

# Write JSONL
builder.write_jsonl(records, "output.jsonl")
```

## Key Methods

- `build_records(sources)` - Convert documents to records
- `write_jsonl(records, path)` - Export to JSONL
- `validate_provenance(record)` - Verify metadata

See architecture documentation for details.
