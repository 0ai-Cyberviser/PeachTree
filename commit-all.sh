#!/bin/bash
# Commit GitHub Actions dependency updates - simple version

cd /tmp/peachtree || exit 1

git add .github/workflows/*.yml
git add MODEL-CARD-SECURITY-DATASET.md MULTI-ORG-DATASET-README.md ECOSYSTEM-ENHANCEMENTS-SUMMARY.md
git add config/policy-packs/security-domain-compliance.json
git add examples/hancock_integration.py

git commit -m "ci(deps): bump GitHub Actions and add ecosystem enhancements

DEPENDENCY UPDATES:
- actions/checkout: v4 → v6 (5 workflows)
- actions/setup-python: v4/v5 → v6 (5 workflows)  
- actions/upload-artifact: v4 → v7 (1 workflow)
- peter-evans/create-pull-request: v8 (already latest)

Addresses Dependabot PRs #12-17 with consolidated updates.

ECOSYSTEM ENHANCEMENTS ADDED:
- MODEL-CARD-SECURITY-DATASET.md: Complete dataset specification
- MULTI-ORG-DATASET-README.md: User-friendly dataset guide
- config/policy-packs/security-domain-compliance.json: Security policy pack
- examples/hancock_integration.py: Training pipeline integration
- ECOSYSTEM-ENHANCEMENTS-SUMMARY.md: Complete enhancement summary

PeachTree v1.0 production-ready with modern CI/CD and comprehensive
security dataset infrastructure for Hancock cybersecurity LLM training."

echo "✅ Commit created"
git log --oneline -3
