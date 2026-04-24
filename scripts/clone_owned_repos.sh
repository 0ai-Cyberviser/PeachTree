#!/usr/bin/env bash
set -euo pipefail
CLONE_ROOT="data/repos"
mkdir -p "$CLONE_ROOT"

if [ ! -d "${CLONE_ROOT}/0ai-Cyberviser__PeachTree/.git" ]; then
  gh repo clone 0ai-Cyberviser/PeachTree '${CLONE_ROOT}/0ai-Cyberviser__PeachTree' -- --depth 1
else
  git -C "${CLONE_ROOT}/0ai-Cyberviser__PeachTree" pull --ff-only
fi
