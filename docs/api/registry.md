# API Reference - Registry

Artifact registry and discovery API.

## DatasetRegistryBuilder

```python
from peachtree.registry import DatasetRegistryBuilder

builder = DatasetRegistryBuilder()
registry = builder.discover(
    roots=["data/", "reports/"],
    name="MyProject"
)
```

See [Architecture](../architecture/design.md) for details.
