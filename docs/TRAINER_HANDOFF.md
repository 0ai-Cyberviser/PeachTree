# Trainer Handoff Manifests, LoRA Job Cards, and Dry-Run Training Plans

PeachTree v0.9.0 adds safe training-prep artifacts.

It does **not** launch training, upload datasets, create cloud jobs, or call external trainer APIs.

## New CLI

```bash
peachtree handoff
peachtree lora-card
peachtree train-plan
```

## Trainer handoff manifest

```bash
peachtree handoff \
  --dataset data/exports/peachfuzz-chatml.jsonl \
  --model-name PeachFuzz-Lora-v1 \
  --base-model mistralai/Mistral-7B-Instruct-v0.3 \
  --trainer-profile unsloth \
  --dataset-format chatml \
  --registry reports/registry.json \
  --sbom reports/sbom.json \
  --model-card reports/model-card.md \
  --quality-report reports/quality.json \
  --policy-report reports/policy-pack.json \
  --license-report reports/license-gate.json \
  --release-bundle dist/peachfuzz-dataset-v1.zip \
  --output reports/trainer-handoff.json \
  --markdown-output reports/trainer-handoff.md
```

## LoRA job card

```bash
peachtree lora-card \
  --dataset data/exports/peachfuzz-chatml.jsonl \
  --job-name peachfuzz-lora-v1 \
  --base-model mistralai/Mistral-7B-Instruct-v0.3 \
  --output-dir outputs/peachfuzz-lora-v1 \
  --trainer-profile unsloth \
  --dataset-format chatml \
  --rank 16 \
  --alpha 32 \
  --learning-rate 0.0002 \
  --epochs 1 \
  --output reports/lora-job-card.json \
  --markdown-output reports/lora-job-card.md
```

## Dry-run training launch plan

```bash
peachtree train-plan \
  --job-card reports/lora-job-card.json \
  --output reports/dry-run-training-plan.json \
  --markdown-output reports/dry-run-training-plan.md
```

## Safety model

- dry-run only
- no shell execution
- no model training
- no dataset upload
- no external training API calls
- human approval required before training
