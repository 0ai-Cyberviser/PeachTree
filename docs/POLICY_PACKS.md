# Dataset Policy Packs, License Gates, and Model Cards

PeachTree v0.7.0 adds review-first compliance tooling for dataset training pipelines.

## New CLI

```bash
peachtree policy-pack
peachtree license-gate
peachtree model-card
```

## Built-in policy packs

```bash
peachtree policy-pack --list
peachtree policy-pack --show open-safe
peachtree policy-pack --show commercial-ready
peachtree policy-pack --show internal-review
```

Policy packs compose:

- quality gates
- duplicate-ratio gates
- license allow/deny gates
- human-review requirements

## Evaluate a policy pack

```bash
peachtree policy-pack \
  --dataset data/datasets/peachfuzz-instruct-deduped.jsonl \
  --pack open-safe \
  --json-output reports/policy-pack.json \
  --markdown-output reports/policy-pack.md
```

## Run license/compliance gates

```bash
peachtree license-gate \
  --dataset data/datasets/peachfuzz-instruct-deduped.jsonl \
  --json-output reports/license-gate.json \
  --markdown-output reports/license-gate.md
```

Custom license policy:

```bash
peachtree license-gate \
  --dataset data/datasets/peachfuzz-instruct-deduped.jsonl \
  --allow apache-2.0,mit,bsd-3-clause \
  --deny agpl-3.0,gpl-3.0,proprietary,unknown \
  --fail-on-gate
```

## Generate a model card

```bash
peachtree model-card \
  --dataset data/datasets/peachfuzz-instruct-deduped.jsonl \
  --model-name PeachFuzz-Dataset-v1 \
  --manifest data/manifests/peachfuzz.json \
  --quality-report reports/quality.json \
  --license-report reports/license-gate.json \
  --policy-report reports/policy-pack.json \
  --output reports/model-card.md
```

## Safety model

- local-only
- no model training
- no dataset upload
- no public GitHub scraping
- policy reports are review inputs, not automatic legal approval
- human review remains mandatory before downstream training
