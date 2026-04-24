# Scheduled Dataset Update PR Workflow

PeachTree v0.5.0 adds review-first scheduled dataset update tooling.

The goal is to keep datasets fresh without silently changing model training inputs.

## New CLI

```bash
peachtree update-plan
peachtree diff
peachtree review-report
```

## Create an update plan

```bash
peachtree update-plan \
  --repo ~/peachfuzz \
  --repo-name 0ai-Cyberviser/peachfuzz \
  --output data/manifests/update-plan.json \
  --markdown-output reports/update-plan.md
```

## Compare datasets

```bash
peachtree diff \
  --baseline data/baseline/peachfuzz-instruct.jsonl \
  --candidate data/datasets/peachfuzz-instruct.jsonl \
  --format markdown \
  --json-output reports/dataset-diff.json \
  --markdown-output reports/dataset-diff.md
```

## Generate a review report

```bash
peachtree review-report \
  --plan data/manifests/update-plan.json \
  --output reports/update-review.json
```

## CI workflow behavior

`.github/workflows/peachtree-dataset-update.yml` is intentionally PR-based:

1. Checkout repository.
2. Install PeachTree.
3. Generate update plan.
4. Build/update datasets.
5. Generate diff and review reports.
6. Upload reports as artifacts.
7. Open a pull request for human review.

## Safety model

- no model training
- no dataset upload
- no direct push to `main`
- no public GitHub scraping
- all changes are reviewed through pull requests
- reports include added, removed, changed records and provenance warnings
