# PeachTree v0.2.1 Hotfix

Fixes live GitHub CLI compatibility and generated script path handling.

## Fixed

- `gh repo list --json visibility` failed because GitHub CLI exposes `isPrivate`, not `visibility`.
- Generated clone scripts quoted `${CLONE_ROOT}` literally, producing directories named `${CLONE_ROOT}`.
- Generated owned-repo scripts are now ignored by git by default.
- `examples/peachfuzz_pipeline.sh` remains executable.

## Validate

```bash
pytest -q
peachtree github-owned --owner 0ai-Cyberviser --limit 25 --output data/manifests/owned.jsonl
peachtree github-plan --inventory data/manifests/owned.jsonl --clone-root data/repos
cat scripts/clone_owned_repos.sh
cat scripts/build_owned_datasets.sh
```
