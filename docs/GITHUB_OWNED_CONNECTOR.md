# Owned GitHub Repository Connector

PeachTree v0.2.0 adds a safe owned/access-authorized GitHub connector.

## Safety model

The connector inventories repositories the operator can already access. It does not scrape all of GitHub and does not bypass access controls.

Workflow:

1. Generate inventory.
2. Review inventory.
3. Generate clone/build scripts.
4. Run scripts locally when approved.
5. Review datasets before training.

## Commands

Using live GitHub CLI:

```bash
peachtree github-owned --owner 0ai-Cyberviser --limit 25 --output data/manifests/owned.jsonl
peachtree github-plan --inventory data/manifests/owned.jsonl --clone-root data/repos
```

Using saved JSON from `gh repo list`:

```bash
gh repo list 0ai-Cyberviser --limit 25 --json nameWithOwner,url,isPrivate,isArchived,defaultBranchRef,licenseInfo,diskUsage > repos.json
peachtree github-owned --from-json repos.json --output data/manifests/owned.jsonl
peachtree github-plan --inventory data/manifests/owned.jsonl
```

Then review and run:

```bash
cat data/manifests/owned.jsonl
bash scripts/clone_owned_repos.sh
bash scripts/build_owned_datasets.sh
```

## Public GitHub

Public GitHub-wide discovery remains disabled by default. Future public search must be explicit, license-aware, rate-limited, provenance-preserving, and reviewable.


## v0.2.1 compatibility note

GitHub CLI uses `isPrivate`, not `visibility`, for `gh repo list --json`. Generated scripts now preserve `${CLONE_ROOT}` expansion correctly and should be reviewed before running.
