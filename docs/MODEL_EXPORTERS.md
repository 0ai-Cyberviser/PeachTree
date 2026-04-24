# Model Exporter Profiles

PeachTree v0.4.0 adds local-only model dataset exporters for common fine-tuning schemas:

- ChatML
- Alpaca
- ShareGPT

The exporters convert reviewed PeachTree dataset JSONL into model-specific training JSONL. They do **not** train models, upload data, contact APIs, or mutate source datasets.

## Commands

```bash
peachtree export-formats

peachtree export \
  --source data/datasets/0ai-Cyberviser__peachfuzz-instruct.jsonl \
  --format chatml \
  --output data/exports/peachfuzz-chatml.jsonl

peachtree export \
  --source data/datasets/0ai-Cyberviser__peachfuzz-instruct.jsonl \
  --format alpaca \
  --output data/exports/peachfuzz-alpaca.jsonl

peachtree export \
  --source data/datasets/0ai-Cyberviser__peachfuzz-instruct.jsonl \
  --format sharegpt \
  --output data/exports/peachfuzz-sharegpt.jsonl
```

## Validate exports

```bash
peachtree validate-export --format chatml --path data/exports/peachfuzz-chatml.jsonl
peachtree validate-export --format alpaca --path data/exports/peachfuzz-alpaca.jsonl
peachtree validate-export --format sharegpt --path data/exports/peachfuzz-sharegpt.jsonl
```

## Safety model

Exporters are local-only:

- no network calls
- no training execution
- no background jobs
- no shell execution
- preserves source provenance metadata by default
- supports `--no-metadata` only when a downstream trainer requires plain schema

Review exported datasets before model training.
