# PeachTree Dataset Compliance Framework

**Version**: 1.0.0  
**Last Updated**: 2026-04-28  
**Status**: ACTIVE

## Overview

This document defines the compliance framework for all PeachTree datasets, ensuring ethical AI development, responsible security research, and legal compliance.

## Required Conditions

All datasets must meet these 6 conditions before deployment:

### 1. Internal Use Only (No Public Deployment Without Expansion)

**Requirement**: Datasets with < 100 records are SEED TRAINING ONLY

**Enforcement**:
- Automated gate in CI/CD pipeline
- Production deployment blocked until record count >= 100
- Clear labeling in handoff documentation

**Verification**:
```bash
python scripts/compliance-check.py --dataset <path> --min-records 100
```

**Status Levels**:
- ✅ **Seed Training**: 10-99 records, internal use only
- ✅ **Production**: 100+ records, approved for deployment
- ❌ **Blocked**: < 10 records, insufficient for any training

### 2. License Compliance (MIT)

**Requirement**: All training records must be MIT licensed

**Enforcement**:
- Every `DatasetRecord` requires `license_id` field
- Automated validation in quality gates
- SBOM generation includes license verification

**Verification**:
```python
# All records must have:
{
    "license_id": "MIT",
    "source_repo": "0ai-Cyberviser/PeachTree",
    ...
}
```

**Violations**: Records with missing or non-MIT licenses rejected

### 3. No Automated Exploitation Without Human Oversight

**Requirement**: Safety gates prevent autonomous training/deployment

**Enforcement**:
- `requires_human_approval_before_training: true`
- `does_not_train_models: true`
- `dry_run_only: true`

**Handoff Manifest**:
```json
{
  "safety": {
    "requires_human_approval_before_training": true,
    "does_not_train_models": true,
    "does_not_upload_datasets": true,
    "dry_run_only": true
  }
}
```

**Violations**: Missing safety gates = deployment blocked

### 4. Follow Responsible Disclosure Policies

**Requirement**: Training data includes responsible disclosure guidance

**Enforcement**:
- Bug bounty training data must reference disclosure timelines
- No real vulnerability details without anonymization
- Platform-specific disclosure policies documented

**Required Content**:
- Disclosure timelines (e.g., "90-day coordinated disclosure")
- Platform-specific processes
- Ethical hacking guidelines
- Legal compliance requirements

**Verification**: Compliance checker validates disclosure markers

### 5. Expand to 100+ Records Before Production

**Requirement**: Production deployment requires dataset expansion

**Current Status**:
- Seed datasets: 5-10 records each ✅
- Unified dataset: 10 records (SEED ONLY) ✅
- Production requirement: 100+ records ⏳

**Action Required**:
1. Add 90+ additional training examples
2. Expand platform coverage
3. Include multi-turn dialogues
4. Add real-world case studies (anonymized)
5. Re-run compliance checks

**Roadmap**:
- **Phase 1** (Current): 10 records, seed training
- **Phase 2**: 50 records, expanded coverage
- **Phase 3**: 100 records, production-ready
- **Phase 4**: 500+ records, comprehensive training

### 6. Implement Ethical Monitoring

**Requirement**: Continuous monitoring for ethical compliance

**Documentation Required**:
- Model card with ethical considerations
- Bias and fairness analysis
- Prohibited use cases
- Monitoring strategy

**Model Card Sections**:
1. Intended use cases
2. Out-of-scope uses
3. Known limitations
4. Bias mitigation strategies
5. Privacy considerations
6. Deployment recommendations

**Monitoring Plan**:
- Log all model outputs
- Flag policy violations
- Human review of security recommendations
- Regular ethical audits

## Compliance Checking

### Automated CI/CD

Compliance checks run automatically on:
- Push to `main` or `dev` branches
- Pull requests to `main`
- Dataset file changes in `data/hancock/`
- Handoff bundle updates

**Workflow**: `.github/workflows/compliance.yml`

### Manual Validation

```bash
# Check single dataset
python scripts/compliance-check.py \
  --dataset data/hancock/unified-bugbounty-training.jsonl \
  --min-records 10

# Strict mode (warnings = errors)
python scripts/compliance-check.py \
  --dataset data/hancock/unified-bugbounty-training.jsonl \
  --min-records 100 \
  --strict

# Verify handoff bundle
tar -xzf handoff-bundle.tar.gz
cd handoff-bundle
sha256sum -c SHA256SUMS
```

### Compliance Report

Generate compliance report:

```bash
# View current status
cat handoff-bundle/SIGNOFF.md

# Generate fresh report
python scripts/compliance-check.py \
  --dataset data/hancock/unified-bugbounty-training.jsonl \
  --min-records 100 > compliance-report.txt
```

## Approval Workflow

### Pre-Training Approvals

Required before seed training begins:

- [ ] **Dataset Curator**: Verify quality and provenance
- [ ] **ML Lead**: Review training parameters
- [ ] **Security Officer**: Validate safety gates

### Pre-Deployment Approvals

Required before production deployment:

- [ ] **Legal Review**: License compliance, usage rights
- [ ] **Ethics Review**: Bias analysis, ethical considerations
- [ ] **Production Approval**: Final authorization from VP/CTO

## Violations and Remediation

### Severity Levels

**CRITICAL** (Deployment Blocked):
- Missing safety gates
- License violations
- < 10 records for any use

**HIGH** (Production Blocked):
- < 100 records for production
- Missing provenance
- No ethical documentation

**MEDIUM** (Warnings):
- Incomplete model card
- Missing disclosure guidance
- Low quality scores

### Remediation Steps

1. **Identify**: Run compliance checker
2. **Document**: Record violations in issue tracker
3. **Fix**: Address violations per severity
4. **Verify**: Re-run compliance checks
5. **Approve**: Obtain required sign-offs

## Audit Trail

All compliance checks logged in:
- CI/CD workflow artifacts
- `compliance-report.md` in workflow runs
- Git commit history for dataset changes
- Handoff bundle audit trail

## Contact

**Compliance Questions**: See [CONTRIBUTING.md](CONTRIBUTING.md)  
**Security Issues**: See [SECURITY.md](SECURITY.md)  
**Dataset Curator**: PeachTree ML Dataset Control Plane

---

**Last Audit**: 2026-04-28  
**Next Review**: 2026-07-28 (90 days)  
**Compliance Status**: ✅ SEED TRAINING APPROVED
