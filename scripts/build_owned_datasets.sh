#!/usr/bin/env bash
set -euo pipefail
CLONE_ROOT="data/repos"
mkdir -p data/raw data/datasets data/manifests

peachtree ingest-local --repo "${CLONE_ROOT}/0ai-Cyberviser__PeachTree" --repo-name 0ai-Cyberviser/PeachTree --license apache-2.0 --output data/raw/0ai-Cyberviser__PeachTree.jsonl
peachtree build --source data/raw/0ai-Cyberviser__PeachTree.jsonl --dataset data/datasets/0ai-Cyberviser__PeachTree-instruct.jsonl --manifest data/manifests/0ai-Cyberviser__PeachTree.json --domain 0ai-Cyberviser__PeachTree
peachtree audit --dataset data/datasets/0ai-Cyberviser__PeachTree-instruct.jsonl
