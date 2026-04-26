# Trainer Handoff

Prepare datasets for downstream training workflows.

## Handoff Manifest

```bash
peachtree handoff dataset.jsonl \
  --workflow hancock \
  --output trainer-handoff.json
```

## Workflows

- **hancock**: Cybersecurity LLM training
- **peachfuzz**: Fuzzing corpus preparation
- **custom**: User-defined workflows

## Manifest Contents

- Dataset metadata
- Training recommendations
- Quality metrics
- License information
- Compliance verification

## See Also

- [Release Bundles](release-bundles.md)
- [Ecosystem: Hancock](../ecosystem/hancock.md)
