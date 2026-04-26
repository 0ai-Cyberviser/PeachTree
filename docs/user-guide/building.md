# Building Datasets

Comprehensive guide to building JSONL training datasets with PeachTree.

## Basic Workflow

```bash
# 1. Collect sources
peachtree ingest-local src/ --output sources.jsonl

# 2. Build dataset
peachtree build sources.jsonl --output dataset.jsonl

# 3. Validate
peachtree audit dataset.jsonl
```

## See Also

- [Quick Start](../getting-started/quickstart.md)
- [CLI Reference](cli.md)
- [Architecture](../architecture/design.md)
