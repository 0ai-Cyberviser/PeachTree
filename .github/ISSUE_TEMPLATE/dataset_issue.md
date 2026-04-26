---
name: Dataset/Config Issue
about: Report issues with dataset building, policy packs, or configurations
title: "[DATASET] "
labels: ["dataset", "config", "needs-triage"]
assignees: []
---

## Description

Describe the issue with your dataset or configuration.

## Dataset Information

- **Dataset name**: 
- **Source repositories**: 
- **Records count**: 
- **Size**: 

## Configuration

Share your `.peachtree.yaml` (remove sensitive data):

```yaml
# Your config here
```

## Command Run

What command did you run?

```bash
peachtree build --input data/ --output dataset.jsonl
```

## Error Message

```
Paste the full error message and stack trace here
```

## Expected vs Actual

**Expected:** What should happen

**Actual:** What actually happened

## Policy/Safety Context

- **Policy packs used**: 
- **Safety gates enabled**: 
- **License validation**: 

## Audit Report

If available, share relevant parts of:
- `peachtree audit --dataset dataset.jsonl`
- `peachtree policy --dataset dataset.jsonl`

```
Audit output here
```

## Reproduction

Provide minimal steps to reproduce:

1. Create dataset
2. Run command
3. See error

## Environment

- **OS**: 
- **Python Version**: 
- **PeachTree Version**: 

## Checklist

- [ ] I've verified the error with `peachtree audit`
- [ ] I've checked policy compliance
- [ ] I've removed sensitive data from configs/logs
- [ ] The issue is reproducible
