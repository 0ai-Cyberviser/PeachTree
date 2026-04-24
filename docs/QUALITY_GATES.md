# Dataset Quality Scoring, Deduplication, and Training Readiness Gates

PeachTree v0.6.0 adds local-only data governance gates before model training.

## New CLI

```bash
peachtree score
peachtree dedup
peachtree readiness
```

## Score a dataset

```bash
peachtree score \
  --dataset data/datasets/peachfuzz-instruct.jsonl \
  --format markdown \
  --json-output reports/quality.json \
  --markdown-output reports/quality.md
```

Quality scoring checks:

- instruction presence and useful length
- output presence and useful length
- source repository provenance
- source path provenance
- source digest
- license metadata
- safety score
- builder quality score

## Deduplicate a dataset

```bash
peachtree dedup \
  --source data/datasets/peachfuzz-instruct.jsonl \
  --output data/datasets/peachfuzz-instruct-deduped.jsonl \
  --report-json reports/dedup.json \
  --report-markdown reports/dedup.md
```

Deduplication uses a deterministic normalized signature over:

- instruction
- input
- output

## Readiness gates

```bash
peachtree readiness \
  --dataset data/datasets/peachfuzz-instruct-deduped.jsonl \
  --output reports/readiness.json \
  --fail-on-gate
```

Readiness combines:

- quality score gate
- failed-record ratio gate
- provenance gate
- duplicate-ratio gate
- minimum record count gate

## Safety model

- local-only
- no model training
- no dataset upload
- no public GitHub scraping
- reports are designed for human review before downstream training
