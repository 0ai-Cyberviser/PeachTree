---
name: peachtree-deployment
description: "Instructions for working with PeachTree ML dataset control plane during April 26-May 3 deployment. Use when developing dataset pipelines, safety gates, policy compliance, or deployment automation."
applyTo:
  - "**/*peachtree*/**"
  - "**/peachtree-*"
  - "/tmp/peachtree/**"
  - "**/*dataset*/**"
  - "**/*JSONL*"
---

# PeachTree Deployment Instructions

## Project Overview
PeachTree is a dataset control plane for building safe, traceable, high-quality ML training datasets from owned repositories. It enforces safety gates, policy compliance, and provenance tracking before datasets are used for model training.

## Critical Context
**Deployment Window**: April 26 - May 3, 2026
**Current Status**: Pre-deployment preparation (Apr 26)
**Next Milestone**: Stakeholder communications (Apr 26, 14:00-18:00 UTC)

## Project Structure
```
/tmp/peachtree/
├── src/peachtree/          # Core dataset building logic
│   ├── core/               # Provenance, manifests, records
│   ├── gates/              # Safety gates (secrets, licenses, etc.)
│   ├── quality/            # Quality scoring, deduplication
│   └── integrations/       # Hancock, PeachFuzz integrations
├── tests/                  # 129 tests (all passing)
├── data/
│   ├── raw/                # Raw JSONL before safety gates
│   ├── datasets/           # Processed datasets ready for training
│   └── manifests/          # Dataset metadata and provenance
├── reports/                # Compliance reports, model cards, SBOMs
├── policies/               # Policy packs (open-safe, commercial-ready, etc.)
├── scripts/                # Automation scripts (pre-flight, email generation)
├── .github/
│   ├── skills/             # VS Code agent skills
│   └── agents/             # VS Code agent definitions
└── docs/                   # Documentation
```

## Core Principles

### 1. Safety-First
- **NEVER skip safety gates** - Always run secret filtering, license compliance, provenance tracking
- **Local-only by default** - No automatic public GitHub scraping without explicit allow-list
- **Review-first** - Generate manifests, diffs, model cards before any release

### 2. Provenance Tracking
- **Every record must have provenance** - source repo, source path, SHA256 digest
- **Maintain audit trail** - Log all dataset operations
- **Versioning** - Keep dataset versions with associated manifests

### 3. Quality Standards
- **Minimum quality score**: 0.70 for open-safe, 0.80 for commercial-ready
- **Zero duplicates** required for commercial deployment
- **Continuous validation** - Run tests frequently during development

### 4. Human Approval
- **No automatic training launches** - Require explicit approval before model training
- **Policy compliance** - Validate against policy packs before release
- **Legal/compliance review** - Obtain sign-offs before production deployment

## Development Workflow

### Before Making Changes
```bash
# Activate virtual environment
source venv/bin/activate

# Verify current state
python -m pytest tests/ -v  # Should be 129/129 passing
ruff check src/ tests/      # Should be 0 violations

# Check git status
git status  # Should be clean
```

### Adding New Safety Gate
```python
# 1. Create gate implementation
# File: src/peachtree/gates/new_gate.py

from peachtree.core.base_gate import SafetyGate

class NewSafetyGate(SafetyGate):
    """
    Description of what this gate checks.
    """
    def validate(self, record):
        # Implementation
        pass
    
    def filter(self, dataset):
        # Implementation
        pass

# 2. Add tests
# File: tests/gates/test_new_gate.py

import pytest
from peachtree.gates.new_gate import NewSafetyGate

def test_new_gate_validates_correctly():
    gate = NewSafetyGate()
    # Test cases
    assert gate.validate(valid_record) == True
    assert gate.validate(invalid_record) == False

# 3. Run tests
python -m pytest tests/gates/test_new_gate.py -v

# 4. Integrate into pipeline
# File: src/peachtree/core/pipeline.py
# Add gate to safety_gates list
```

### Adding New Policy Pack
```yaml
# File: policies/new-policy.yaml

name: "new-policy-pack"
version: "1.0"
description: "Description of this policy pack"

gates:
  - name: "secret-filter"
    required: true
    config:
      strict: true
  
  - name: "license-checker"
    required: true
    config:
      allowed_licenses:
        - MIT
        - Apache-2.0
        - BSD-3-Clause
  
  - name: "quality-scorer"
    required: true
    config:
      minimum_score: 0.75
  
  - name: "deduplicator"
    required: true
    config:
      max_duplicate_rate: 0.05

thresholds:
  quality_score: 0.75
  duplicate_rate: 0.05
  
compliance:
  legal_review: true
  compliance_review: true
  security_review: false
```

### Running Dataset Pipeline
```bash
# 1. Plan dataset from owned repos
peachtree plan --source /path/to/repo --output plan.json

# 2. Ingest raw data
peachtree ingest --repo /path/to/repo --output data/raw/dataset.jsonl

# 3. Build dataset with safety gates
peachtree build \
    --input data/raw/dataset.jsonl \
    --policy policies/commercial-ready.yaml \
    --output data/datasets/final.jsonl

# 4. Audit dataset
peachtree audit \
    --input data/datasets/final.jsonl \
    --output reports/audit-report.json

# 5. Generate model card
peachtree card \
    --dataset data/datasets/final.jsonl \
    --output reports/model-card.md

# 6. Create trainer handoff
peachtree handoff \
    --dataset data/datasets/final.jsonl \
    --output data/manifests/trainer-handoff.json
```

## Testing Requirements

### Run Before Every Commit
```bash
# Full test suite (should complete in < 2 minutes)
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ -v --cov=src/peachtree --cov-report=term-missing

# Linting
ruff check src/ tests/

# Type checking (if using mypy)
mypy src/peachtree/
```

### Current Test Status
- **Total tests**: 129
- **Passing**: 129 (100%)
- **Coverage**: >90% (all core modules)
- **Status**: ✅ ALL PASSING

### Test Organization
- `tests/core/` - Core functionality (provenance, manifests, records)
- `tests/gates/` - Safety gates (secrets, licenses, etc.)
- `tests/quality/` - Quality scoring, deduplication
- `tests/integration/` - End-to-end pipeline tests
- `tests/fixtures/` - Test data and fixtures

## Deployment Automation

### Pre-Flight Check
```bash
# Run before stakeholder communications
bash scripts/pre-flight-check.sh

# Validates:
# - All execution documents present
# - All tests passing
# - Code quality clean
# - Git status clean
# - Email templates complete
```

### Email Generation
```bash
# Interactive email generator
python3 scripts/generate-emails.py

# Generates personalized stakeholder emails in generated-emails/
# - email1-legal.txt
# - email2-compliance.txt
# - email3-stakeholders.txt
# - email4-executive.txt
# - email5-team.txt
```

## Critical Files

### Do NOT Modify Without Review
- `data/datasets/blockchain-node-instruct.jsonl` - Production dataset (5 records, 0.85 quality)
- `data/manifests/blockchain-node.json` - Production manifest
- `reports/model-card.md` - Submitted to legal/compliance
- `reports/policy-compliance-report.json` - Compliance evidence
- `reports/sbom.json` - Software Bill of Materials

### Safe to Modify
- `scripts/` - Automation scripts (pre-flight, email generation)
- `docs/` - Documentation
- `.github/` - Agent skills and configurations
- `tests/` - Test files (always add tests for new features)

## Common Tasks

### Task: Add Training Example
```bash
# 1. Create new source document
cat > data/raw/new-example.jsonl << 'EOF'
{
  "id": "new-1",
  "source_repo": "github.com/owner/repo",
  "source_path": "path/to/file.py",
  "source_digest": "sha256:abc123",
  "license": "MIT",
  "content": "Example content"
}
EOF

# 2. Run through pipeline
peachtree build --input data/raw/new-example.jsonl --output data/datasets/new-dataset.jsonl

# 3. Validate quality
python scripts/validate_model.py --dataset data/datasets/new-dataset.jsonl

# 4. Audit
peachtree audit --input data/datasets/new-dataset.jsonl
```

### Task: Debug Failing Safety Gate
```bash
# 1. Run specific gate tests
python -m pytest tests/gates/test_secret_filter.py -v -s

# 2. Check gate configuration
cat policies/commercial-ready.yaml | grep -A 10 "secret-filter"

# 3. Manually test gate
python -c "from peachtree.gates.secret_filter import SecretFilter; gate = SecretFilter(); print(gate.validate(record))"

# 4. Review logs
tail -f logs/safety-gates.log
```

### Task: Update Policy Pack
```bash
# 1. Edit policy pack
vim policies/commercial-ready.yaml

# 2. Validate syntax
python scripts/validate_policy.py policies/commercial-ready.yaml

# 3. Test against dataset
peachtree policy --input data/datasets/blockchain-node-instruct.jsonl --policy-pack policies/commercial-ready.yaml

# 4. Update compliance report
peachtree policy --input data/datasets/blockchain-node-instruct.jsonl --policy-pack policies/commercial-ready.yaml --output reports/policy-compliance-report.json
```

## Error Handling

### If Tests Fail
```bash
# 1. Identify failing test
python -m pytest tests/ -v --tb=short

# 2. Run specific failing test with verbose output
python -m pytest tests/path/to/test_file.py::test_name -v -s

# 3. Check git diff for recent changes
git diff

# 4. Revert if needed
git checkout -- path/to/file.py
```

### If Safety Gate Fails
```bash
# 1. Check which gate failed
python scripts/check_safety_gates.py

# 2. View detailed failure reasons
peachtree audit --input data/datasets/dataset.jsonl --detailed

# 3. Filter problematic records
peachtree build --input data/raw/dataset.jsonl --strict --output data/datasets/clean.jsonl

# 4. Re-validate
peachtree audit --input data/datasets/clean.jsonl
```

### If Quality Score Too Low
```bash
# 1. Identify low-quality records
peachtree quality --input dataset.jsonl --threshold 0.70 --output low-quality-ids.txt

# 2. Review low-quality records
cat low-quality-ids.txt

# 3. Improve data sources or remove low-quality records
peachtree build --input dataset.jsonl --min-quality 0.75 --output high-quality.jsonl

# 4. Re-score
python scripts/calculate_quality_score.py high-quality.jsonl
```

## Git Workflow

### Before Committing
```bash
# 1. Run all checks
python -m pytest tests/ -v
ruff check src/ tests/
git status

# 2. Stage changes
git add [files]

# 3. Commit with descriptive message
git commit -m "feat: Add [feature] with [context]"

# 4. Push
git push origin main
```

### Commit Message Format
```
<type>: <description>

[optional body]

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- test: Test additions or modifications
- refactor: Code refactoring
- chore: Maintenance tasks

Examples:
feat: Add new safety gate for PII detection
fix: Resolve duplicate detection edge case
docs: Update policy pack configuration guide
test: Add integration tests for full pipeline
```

## Deployment Timeline Reference

### Apr 26 (TODAY) - Stakeholder Communications
- **14:00-18:00 UTC**: Execute stakeholder communications
- **Critical**: Send all 5 emails (Legal, Compliance, Stakeholder, Executive, Team)
- **Deadline**: 18:00 UTC - All communications sent and acknowledged

### Apr 27-28 - Staging Deployment
- **Apr 27 08:00**: PeachTree staging deployment begins
- **Apr 27 08:00 - Apr 28 08:00**: 24-hour validation window
- **Apr 28 08:00**: Validation results review
- **Apr 28 12:00**: Final Go/No-Go Decision meeting

### May 1 - Production Deployment
- **10:00**: Production deployment begins
- **10:00-12:00**: Phased traffic migration (0% → 50% → 75% → 100%)
- **12:00**: Production deployment complete

## Emergency Contacts
- **ML Lead**: ml-lead@company.com
- **CTO (Escalation)**: cto@company.com
- **On-Call (24/7)**: oncall@company.com
- **Legal**: legal@company.com
- **Compliance**: compliance@company.com

## Quick Reference
- Execution checklist: `MASTER-EXECUTION-CHECKLIST.md`
- Countdown reference: `COUNTDOWN-EXECUTION-REFERENCE.md`
- Email templates: `EMAIL-DISTRIBUTION-TEMPLATES.md`
- Pre-flight script: `scripts/pre-flight-check.sh`
- Email generator: `scripts/generate-emails.py`
- Visual timeline: `VISUAL-DEPLOYMENT-TIMELINE.md`
