# Deduplication

Remove duplicate and similar records from datasets.

## Methods

### Content Hash (Exact)
```bash
peachtree dedup dataset.jsonl \
  --method content-hash \
  --output dedup.jsonl
```

### Semantic (Similarity)
```bash
peachtree dedup dataset.jsonl \
  --method semantic \
  --similarity-threshold 0.95 \
  --output dedup.jsonl
```

### Fuzzy Matching
```bash
peachtree dedup dataset.jsonl \
  --method fuzzy \
  --output dedup.jsonl
```

## See Also

- [CLI Reference](cli.md)
- [Architecture](../architecture/design.md)
