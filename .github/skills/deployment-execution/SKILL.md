---
name: deployment-execution
description: "Use when: executing deployment procedures, running stakeholder communications, managing Go/No-Go decisions, or automating deployment workflows for Apr 26-May 3 timeline. Provides step-by-step execution guidance, email generation, pre-flight checks, and decision framework automation."
---

# Deployment Execution Skill

## Purpose
Automate and guide execution of the April 26-May 3 dual-project deployment (PeachTree ML + web3-blockchain-node).

## When to Use This Skill
- Executing stakeholder communications (Apr 26, 14:00-18:00 UTC)
- Running pre-flight checks before deployment
- Generating personalized emails with contact information
- Managing Go/No-Go decision checkpoints
- Coordinating simultaneous deployments
- Tracking deployment progress and metrics
- Troubleshooting deployment issues

## Capabilities
1. **Pre-Flight Automation** - Run `scripts/pre-flight-check.sh` to verify readiness
2. **Email Generation** - Run `scripts/generate-emails.py` to create personalized stakeholder emails
3. **Decision Framework** - Guide through Go/No-Go decision criteria
4. **Progress Tracking** - Monitor deployment milestones and success criteria
5. **Troubleshooting** - Quick access to incident response procedures

## Quick Start

### Before Stakeholder Communications (Apr 26, before 14:00 UTC)
```bash
# 1. Run pre-flight check
cd /tmp/peachtree
bash scripts/pre-flight-check.sh

# 2. Generate personalized emails
python3 scripts/generate-emails.py

# 3. Review generated emails
ls -la generated-emails/
cat generated-emails/README.txt
```

### During Execution (Apr 26, 14:00-18:00 UTC)
1. Open MASTER-EXECUTION-CHECKLIST.md
2. Follow COUNTDOWN-EXECUTION-REFERENCE.md for real-time guidance
3. Use EMAIL-DISTRIBUTION-TEMPLATES.md to copy email text
4. Track progress in spreadsheet

### Deployment Days (Apr 27-28)
1. blockchain-node: Follow PHASE3-QUICK-START.md
2. PeachTree: Follow PHASE-3-VALIDATION-STAGING.md
3. Both: Monitor DUAL-PROJECT-COORDINATION-APRIL-27-28.md

## Available Scripts

### Pre-Flight Check (`scripts/pre-flight-check.sh`)
**Purpose**: Validate all execution prerequisites before starting
**Usage**: `bash scripts/pre-flight-check.sh`
**Checks**:
- All execution documents present
- Tests passing (129/129 PeachTree, 8/8 blockchain-node)
- Code quality clean (ruff, go vet)
- Git repositories clean
- Email templates complete
- Supporting documentation present

**Exit Codes**:
- 0: All checks passed, ready for execution
- 1: Some checks failed, fix issues before proceeding

### Email Generator (`scripts/generate-emails.py`)
**Purpose**: Generate all 5 stakeholder emails with your contact information
**Usage**: `python3 scripts/generate-emails.py`
**Interactive**: Prompts for contact information, then generates:
- `generated-emails/email1-legal.txt`
- `generated-emails/email2-compliance.txt`
- `generated-emails/email3-stakeholders.txt`
- `generated-emails/email4-executive.txt`
- `generated-emails/email5-team.txt`
- `generated-emails/README.txt` (summary)

## Execution Workflow

### Apr 26 (TODAY) - 6.5-Hour Window
```
13:55 → Pre-flight check
14:00 → Preparation phase (30 min)
14:30 → Email 1: Legal (5 min)
14:45 → Email 2: Compliance (5 min)
15:00 → Email 3: Stakeholders (5 min)
15:15 → Email 4: Executive + Calendar (5 min) ⚠️ CALENDAR CRITICAL
15:30 → Email 5: Team (5 min)
15:45 → Verification (45 min)
16:30 → Track responses (60 min)
17:30 → Final report (30 min)
18:00 → DEADLINE ✅
```

### Apr 27 - Staging Deployments
```
blockchain-node:
06:00 → Team standup
08:00 → Deployment begins
14:00 → Go/No-Go Decision #1

PeachTree:
08:00 → Staging deployment
08:00-Apr 28 08:00 → 24-hour validation
```

### Apr 28 - Final Decision
```
08:00 → PeachTree validation complete
12:00 → FINAL GO/NO-GO DECISION MEETING
       ├─ Legal approved?
       ├─ Compliance approved?
       ├─ Stakeholder approved?
       ├─ blockchain-node Phase 3 passed?
       ├─ PeachTree validation passed?
       └─ Executive approved?
12:30 → Production authorization (if all YES)
```

### May 1 - Production Deployment
```
10:00 → Deployment begins (both projects)
10:30 → 50% traffic (if metrics healthy)
11:00 → 75% traffic (if no errors)
11:30 → 100% traffic (if all green)
12:00 → Production complete
```

## Decision Criteria

### Go/No-Go Decision #1 (Apr 27, 14:00 UTC)
**Question**: "Is blockchain-node ready for Phase 4?"
**ALL 8 must be YES**:
1. Uptime ≥ 99.9%
2. Error rate < 0.1%
3. Latency P50 < 100ms, P99 < 500ms
4. Database 100% operational
5. All 8 health checks passing
6. Zero critical alerts
7. Load test passed (500+ req/sec)
8. Team consensus achieved

**Outcome**:
- GO → Proceed to Phase 4 (Apr 29-30)
- NO-GO → Rollback, investigate, retry

### Final Go/No-Go Decision (Apr 28, 12:00 UTC)
**Question**: "Authorize production deployment May 1?"
**ALL 6 must be YES**:
1. Legal approval obtained
2. Compliance approval obtained
3. Stakeholder approval obtained
4. blockchain-node Phase 3 passed
5. PeachTree validation complete (accuracy ≥85%, zero incidents)
6. Executive sponsor approved

**Outcome**:
- ALL YES → 🟢 GO for May 1 production
- ANY NO → 🔴 NO-GO: Investigate, timeline adjusts

## Troubleshooting

### If Email Bounces
1. Verify email address is correct
2. Check recipient's spam folder
3. Resend to correct address
4. Update tracking spreadsheet with note

### If No Acknowledgments by 17:00 UTC
1. Send polite follow-up: "Confirming receipt - need response by 18:00 UTC"
2. If no response by 17:45 UTC: Call or urgent message
3. Escalate to ml-lead@company.com or cto@company.com

### If Deployment Fails
1. INCIDENT-RESPONSE-RUNBOOK.md (blockchain-node)
2. INCIDENT-RESPONSE.md (PeachTree)
3. CONTINGENCY-RECOVERY-PROCEDURES.md (disaster recovery)
4. Escalation: On-call Lead → Deployment Lead → CTO

## Success Metrics

### Apr 26 Success
- ✅ All 5 emails sent by 15:30 UTC
- ✅ All recipients acknowledged by 17:00 UTC
- ✅ All review timelines confirmed for Apr 28
- ✅ Final EOD report sent by 18:00 UTC

### Apr 27 Success
- ✅ blockchain-node staging deployment succeeds
- ✅ All 8 success criteria met
- ✅ First Go/No-Go = GO
- ✅ PeachTree staging validation running

### Apr 28 Success
- ✅ All 4 approvals obtained (Legal, Compliance, Stakeholder, Executive)
- ✅ PeachTree validation complete
- ✅ Final Go/No-Go = GO

### May 1 Success
- ✅ Both projects deployed to production
- ✅ Phased traffic migration succeeds
- ✅ Zero critical incidents
- ✅ All metrics within acceptable ranges

## Emergency Contacts
- ML Lead: ml-lead@company.com
- CTO (Escalation): cto@company.com
- On-Call (24/7): oncall@company.com

## Output Format
When assisting with deployment execution:
1. **Current Phase**: Identify where we are in timeline
2. **Next Action**: What to do right now
3. **Success Criteria**: How to know it worked
4. **Fallback Plan**: What to do if issues arise
5. **Time Remaining**: How much time until next checkpoint

## Assets
- `scripts/pre-flight-check.sh` - Automated readiness validation
- `scripts/generate-emails.py` - Interactive email generator
- All execution reference documents in `/tmp/peachtree/`
- All deployment guides in `/home/x/web3-blockchain-node/`
