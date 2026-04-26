# Hancock Integration

PeachTree integrates with Hancock, the cybersecurity LLM agent.

## Workflow

```
PeachTree Dataset
        ↓
Trainer Handoff
        ↓
Hancock Training
```

## Prepare for Hancock

```bash
peachtree handoff dataset.jsonl \
  --workflow hancock \
  --output trainer-handoff.json
```

See [Trainer Handoff](../advanced/trainer-handoff.md) for details.
