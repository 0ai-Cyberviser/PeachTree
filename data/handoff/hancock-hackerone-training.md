# PeachTree Trainer Handoff Manifest

- Model name: `Hancock-BugBounty-v1`
- Base model: `mistralai/Mistral-7B-Instruct-v0.3`
- Trainer profile: `unsloth`
- Dataset: `data/hancock/hackerone-enriched.jsonl`
- Dataset format: `jsonl`
- Created: `2026-04-28T06:09:31.945496+00:00`

## Artifacts

| Name | Kind | Required | Size | SHA-256 | Path |
|---|---|---|---:|---|---|
| `hackerone-enriched.jsonl` | `dataset` | `yes` | 13187 | `f7abe8c0bdd44e90...` | `data/hancock/hackerone-enriched.jsonl` |

## Safety

- dry_run_only: `True`
- does_not_train_models: `True`
- does_not_upload_datasets: `True`
- does_not_call_training_apis: `True`
- requires_human_approval_before_training: `True`
