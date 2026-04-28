# PeachTree Trainer Handoff Manifest

- Model name: `hancock-comprehensive-v1`
- Base model: `mistralai/Mistral-7B-Instruct-v0.3`
- Trainer profile: `unsloth`
- Dataset: `data/hancock/comprehensive-training.jsonl`
- Dataset format: `chatml`
- Created: `2026-04-28T07:32:52.069267+00:00`

## Artifacts

| Name | Kind | Required | Size | SHA-256 | Path |
|---|---|---|---:|---|---|
| `comprehensive-training.jsonl` | `dataset` | `yes` | 1062498 | `9170d08ea8a04ec3...` | `data/hancock/comprehensive-training.jsonl` |

## Safety

- dry_run_only: `True`
- does_not_train_models: `True`
- does_not_upload_datasets: `True`
- does_not_call_training_apis: `True`
- requires_human_approval_before_training: `True`
