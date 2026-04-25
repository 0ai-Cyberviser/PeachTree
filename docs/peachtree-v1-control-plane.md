# PeachTree v1 Control Plane

This change promotes PeachTree from a dataset-builder CLI into the local control plane for Peach datasets and PeachFuzz seed handoffs.

## New commands

```bash
peachtree doctor
peachtree doctor --dataset data/datasets/hancock-instruct.jsonl --format json

peachtree workspace init
peachtree workspace validate --config peach.json
peachtree workspace build --config peach.json
peachtree workspace report --config peach.json --output reports/peach-workspace.md

peachtree seeds \
  --dataset data/datasets/peachfuzz-instruct.jsonl \
  --target graphql \
  --output ../peachfuzz/corpus/peachtree/graphql \
  --manifest reports/seeds/graphql-seeds.json \
  --write
```

## Safety model

- All commands are local-only.
- `doctor` never contacts GitHub, uploads datasets, launches training, or runs fuzzing targets.
- `workspace` requires review before training and keeps public GitHub collection disabled by default.
- `seeds` is dry-run by default and only writes local corpus files with `--write`.
- Seed manifests include source dataset digest, source record IDs, and policy fields declaring no network and no execution.

## Maintainer workflow

1. Run `peachtree doctor` before dataset work.
2. Create or validate `peach.json`.
3. Build local raw sources, datasets, and manifests through `peachtree workspace build`.
4. Run quality, deduplication, license, and readiness gates.
5. Export reviewed seed corpora for PeachFuzz through `peachtree seeds`.
6. Open a pull request containing manifests, reports, and docs for human review.
