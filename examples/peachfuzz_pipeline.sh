#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$HOME/peachfuzz}"

peachtree plan --goal "Build PeachFuzz defensive fuzzing training dataset" --project peachfuzz --output data/manifests/peachfuzz-tree.json
peachtree ingest-local --repo "$REPO" --repo-name peachfuzz --output data/raw/peachfuzz.jsonl
peachtree build --source data/raw/peachfuzz.jsonl --dataset data/datasets/peachfuzz-instruct.jsonl --manifest data/manifests/peachfuzz.json --domain peachfuzz
peachtree audit --dataset data/datasets/peachfuzz-instruct.jsonl --domain peachfuzz
