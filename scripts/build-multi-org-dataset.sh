#!/bin/bash
# Step-by-step PeachTree dataset build from cloned repositories
# This replaces the placeholder commands from the ingestion script

set -e

cd /tmp/peachtree

echo "================================================================"
echo "  PeachTree Dataset Build - Multi-Organization Security Dataset"
echo "================================================================"
echo ""

# Create output directories
mkdir -p data/raw data/datasets data/manifests reports

echo "[Step 1/5] Ingesting CVE records from mitre-cve-database..."
peachtree ingest-local \
  --repo /tmp/datasets/mitre-cve \
  --repo-name "mitre-cve-database" \
  --license MIT \
  --output data/raw/cve-records.jsonl

echo ""
echo "[Step 2/5] Ingesting Metasploit framework modules..."
peachtree ingest-local \
  --repo /tmp/datasets/metasploit-framework \
  --repo-name "metasploit-framework" \
  --license BSD-3-Clause \
  --output data/raw/metasploit-modules.jsonl

echo ""
echo "[Step 3/5] Ingesting additional security repositories..."

# Ingest other repos
peachtree ingest-local \
  --repo /tmp/datasets/sqlmap \
  --repo-name "sqlmap" \
  --license GPL-2.0 \
  --output data/raw/sqlmap-docs.jsonl

peachtree ingest-local \
  --repo /tmp/datasets/john \
  --repo-name "john" \
  --license GPL-2.0 \
  --output data/raw/john-docs.jsonl

peachtree ingest-local \
  --repo /tmp/datasets/clamav \
  --repo-name "clamav" \
  --license GPL-2.0 \
  --output data/raw/clamav-docs.jsonl

peachtree ingest-local \
  --repo /tmp/datasets/snort3 \
  --repo-name "snort3" \
  --license GPL-2.0 \
  --output data/raw/snort3-docs.jsonl

peachtree ingest-local \
  --repo /tmp/datasets/grok-promptss \
  --repo-name "grok-promptss" \
  --license AGPL-3.0 \
  --output data/raw/grok-prompts.jsonl

echo ""
echo "[Step 4/5] Combining all source documents into single file..."

# Combine all JSONL files into one
cat data/raw/cve-records.jsonl \
    data/raw/metasploit-modules.jsonl \
    data/raw/sqlmap-docs.jsonl \
    data/raw/john-docs.jsonl \
    data/raw/clamav-docs.jsonl \
    data/raw/snort3-docs.jsonl \
    data/raw/grok-prompts.jsonl \
    > data/raw/multi-org-combined-sources.jsonl

echo "✓ Combined $(wc -l < data/raw/multi-org-combined-sources.jsonl) source documents"

echo ""
echo "[Step 5/5] Building final dataset with safety gates..."

# Build the dataset from combined sources
peachtree build \
  --source data/raw/multi-org-combined-sources.jsonl \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --manifest data/manifests/multi-org-build-manifest.json \
  --domain security

echo ""
echo "================================================================"
echo "  Dataset Build Complete!"
echo "================================================================"
echo ""

# Show results
echo "Output files:"
echo "  Dataset: data/datasets/multi-org-security-training.jsonl"
echo "  Manifest: data/manifests/multi-org-build-manifest.json"
echo ""

if [ -f data/datasets/multi-org-security-training.jsonl ]; then
    RECORD_COUNT=$(wc -l < data/datasets/multi-org-security-training.jsonl)
    echo "  Records created: $RECORD_COUNT"
fi

echo ""
echo "Next steps:"
echo "1. Run audit: peachtree audit --dataset data/datasets/multi-org-security-training.jsonl"
echo "2. Export for Hancock: peachtree export --source data/datasets/multi-org-security-training.jsonl --output data/manifests/hancock-handoff.json --format chatml"
echo ""
