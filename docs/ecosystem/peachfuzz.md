# PeachFuzz Integration

PeachTree prepares fuzzing corpora for PeachFuzz.

## Workflow

```
PeachTree Dataset
        ↓
Trainer Handoff (peachfuzz workflow)
        ↓
PeachFuzz Corpus
```

## Prepare Corpus

```bash
peachtree handoff dataset.jsonl \
  --workflow peachfuzz \
  --output fuzz-corpus.json
```

See [Trainer Handoff](../advanced/trainer-handoff.md) for details.
