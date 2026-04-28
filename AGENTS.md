# PeachTree AI Agent System

Specialized AI agents, skills, and instructions for the PeachTree dataset control plane and deployment workflows.

## Quick Start for AI Agents

### Essential Commands
```bash
# Setup
pip install -e ".[dev]"

# Testing (129+ tests must pass)
pytest tests/ -v
pytest tests/ --cov=src/peachtree --cov-report=html

# Code Quality (must be 0 violations)
ruff check src/ tests/
ruff check --fix src/ tests/
mypy src/peachtree/ --strict

# CLI Commands (15 available)
peachtree plan|ingest|build|audit|policy|quality|dedup|export|card|handoff|health|dashboard|hancock-discover|hancock-ingest|hancock-workflow
```

### Core Principles (CRITICAL)
1. **Safety-First**: NEVER skip safety gates (secrets, licenses, provenance). Local-only by default - no automatic public GitHub scraping
2. **Provenance Tracking**: Every record MUST have source repo, source path, SHA256 digest. Use frozen dataclasses
3. **Quality Standards**: Min score 0.70 (open-safe) or 0.80 (commercial). Zero duplicates for production
4. **Human Approval**: No automatic training launches. Require explicit approval + policy compliance validation

### Common Pitfalls
- Frozen dataclasses cannot be modified (create new instances)
- JSONL format: each line is complete JSON object with provenance, not JSON array
- Python 3.10+ required (uses modern type hints: `str | None`)
- All 129+ tests must pass before commit

### Quick Reference
- **Project structure**: `src/peachtree/` (80+ modules), `tests/` (74+ test files mirroring src)
- **Entry point**: `src/peachtree/cli.py` (12 commands)
- **Core models**: `SourceDocument`, `DatasetRecord`, `LearningNode` in `models.py`
- **Documentation**: See [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md), [docs/](docs/) for details

---

## Development Guide (Critical API Knowledge)

### Frozen Dataclass Constraints ⚠️

**ALL core models use `@dataclass(frozen=True)` - they are IMMUTABLE**

```python
# ❌ WRONG - AttributeError: can't set attribute
record.quality_score = 0.9

# ✅ CORRECT - create new instance with dataclasses.replace()
from dataclasses import replace
new_record = replace(record, quality_score=0.9)
```

**Key Rules:**
- **Cannot modify** fields after creation
- Use **tuples** for collections: `tuple[str, ...]` not `list[str]`
- Computed values via **@property** methods (e.g., `digest`, `id`)
- Use `field(default_factory=tuple)` for mutable defaults

### JSONL Format (NOT JSON Arrays)

**Each line is a complete, independent JSON object:**

```jsonl
{"id": "abc123", "instruction": "...", "source_repo": "..."}
{"id": "def456", "instruction": "...", "source_repo": "..."}
```

**Reading JSONL:**
```python
records = []
for line in path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        records.append(json.loads(line))
```

**Writing JSONL:**
```python
path.write_text(
    "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
    encoding="utf-8"
)
```

### Critical API Signatures

**DatasetDeduplicator** (most common error):
```python
# ✅ CORRECT method name
deduplicator = DatasetDeduplicator()
report = deduplicator.deduplicate(
    source_path="dataset.jsonl",
    output_path="deduped.jsonl",
    write_output=True
)

# ❌ WRONG - does not exist
deduplicator.deduplicate_dataset(...)  # NO SUCH METHOD
```

**SourceDocument constructor**:
```python
# ✅ CORRECT - uses repo_name, path (digest computed via @property)
doc = SourceDocument(
    repo_name="0ai-Cyberviser/PeachTree",
    path="README.md",
    content="...",
    source_type="local-file"
)

# ❌ WRONG - old API (source_repo, source_path, sha256_digest params don't exist)
doc = SourceDocument(source_repo="...", sha256_digest="...")
```

**TrainerHandoffBuilder**:
```python
# ✅ CORRECT method name
handoff = handoff_builder.build()

# ❌ WRONG - does not exist
handoff = handoff_builder.create_handoff()
```

### Provenance Requirements (Mandatory)

**Every DatasetRecord MUST have:**
- `source_repo` - Repository name
- `source_path` - File path within repo
- `source_digest` - SHA256 hash (use `sha256_text()` from models)
- `license_id` - License identifier
- `created_at` - ISO timestamp (auto-generated)

### Testing Patterns

**Test file structure mirrors source:**
```
tests/
├── test_hancock_integration.py  # Mirror of hancock_integration.py
├── test_dedup.py                # Mirror of dedup.py
└── [74+ test files]
```

**Common test helpers:**
```python
def test_example(tmp_path: Path):  # pytest provides tmp_path
    # Create test JSONL
    (tmp_path / "dataset.jsonl").write_text(
        '\n'.join(json.dumps(r) for r in records) + '\n',
        encoding="utf-8"
    )
    
    # Test with path
    result = process_dataset(tmp_path / "dataset.jsonl")
```

### Code Quality Checklist

**Before every commit:**
```bash
# 1. All tests pass (129+ tests)
pytest tests/ -v

# 2. Zero lint violations
ruff check src/ tests/

# 3. Zero type errors
mypy src/peachtree/ --strict

# 4. CLI smoke test
peachtree policy
```

### Hancock Integration (New)

**Module**: `src/peachtree/hancock_integration.py`

**CLI commands:**
```bash
# Discover available sources
peachtree hancock-discover --hancock-dir ~/Hancock/data

# Run complete workflow (ingest + quality + dedup + handoff)
peachtree hancock-workflow \
  --hancock-dir ~/Hancock/data \
  --output-dir data/hancock \
  --min-quality-score 0.70
```

**Python API:**
```python
from peachtree.hancock_integration import hancock_ingestion_workflow

summary = hancock_ingestion_workflow(
    hancock_data_dir=Path("~/Hancock/data"),
    output_dir=Path("data/hancock"),
    min_quality_score=0.70
)
```

**Supported sources:** MITRE ATT&CK, NVD CVE, CISA KEV, GHSA, Atomic Red Team, KB, SOC-KB, v3 consolidated

### Quick Debugging

```bash
# ModuleNotFoundError
pip install -e ".[dev]"

# Test specific file
pytest tests/test_hancock_integration.py -v --tb=short

# Verify installation
python -c "import peachtree; print(peachtree.__file__)"
peachtree --version
```

**For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**  
**For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)**

---

## Bug Bounty & Security Research

### Cryptocurrency Exchange Vulnerability Patterns

**Supported Platforms**: HackerOne, Bugcrowd (Crypto.com, OKX, Robinhood, Bitstamp, Coinbase, Binance)

**Multi-Platform Assessment**:
- **Web2**: Traditional web vulnerabilities (RCE, SQLi, XSS, CSRF, SSRF)
- **Web3**: Wallet, smart contract, blockchain-specific issues
- **Mobile**: iOS/Android app vulnerabilities (report once per vuln type)
- **Desktop**: Windows/macOS executable security
- **Browser Extensions**: Chrome/Edge/Safari wallet extensions

**Severity Classification** (Crypto Exchanges):
```
Extreme: $30K-$1M+ (fund theft >$1M, mass account takeover, KYC breach)
Critical: $5K-$30K (RCE, SQLi core DB, admin takeover, wallet compromise)
High: $2K-$5K (stored XSS, CSRF on critical actions, auth bypass)
Medium: $600-$2K (reflected XSS, CSRF non-critical, limited auth bypass)
Low: $50-$600 (open redirects, info leaks, common CSRF)
```

**Business Risk Multipliers** (OKX model):
- Static pages: 1.0× | Auth dashboard: 1.2× | Fund actions: 1.4× | Admin: 1.5×
- Wallet UI: 1.0× | Signature hijack: 1.5× | Smart contract: 1.4×

**Key Patterns**:
1. **IDOR**: Must demonstrate ID discovery path (not brute force)
2. **Cross-Platform**: Same vuln across iOS/Android = 1 report
3. **Wallet Extensions**: Same vuln across Chrome/Edge/Safari = 1 report
4. **AI Disclosure**: Must disclose AI tool usage in discovery/reporting
5. **Leaked Credentials**: Report immediately, authenticate once only
6. **Tier-Based Rewards**: Robinhood uses 3-tier system (Tier 1: $100-$25K, Tier 2/3: lower)
7. **Financial Limits**: Robinhood $1K USD cap on unbounded loss testing
8. **Mandatory Headers**: Robinhood requires X-Bug-Bounty and X-Test-Account-Email

**Out of Scope** (Common):
- Automated scanner reports | Self-XSS | DoS/DDoS
- Root/jailbreak required | Known vulnerable libraries without PoC
- Certificate pinning bypass on rooted devices
- API keys without demonstrated impact

**Tools**: BugBountyAgent, bug-bounty-workflows skill

---

## Agent Ecosystem Overview

**Created**: April 27, 2026  
**System**: VS Code GitHub Copilot Agent Framework  
**Purpose**: Automate deployment, dataset operations, and multi-organization security integration  

---

## Available Agents

### 1. PeachTreeAI (Base Agent)
**Mode**: `PeachTreeAI`  
**Location**: `.agent.md` (workspace root)  
**Purpose**: Primary agent for PeachTree dataset control plane development  

**Capabilities**:
- Dataset pipeline development
- Safety gate implementation
- Policy pack compliance
- JSONL record management
- Quality scoring and deduplication
- Trainer handoff generation
- Hancock cybersecurity data integration (MITRE ATT&CK, CVE, KEV, GHSA, Atomic Red Team)
- PeachFuzz integration

**Invoke**: Default mode when working with PeachTree codebase

---

### 2. Stakeholder Communications Agent
**File**: `.github/agents/StakeholderCommunicationsAgent.md`  
**Purpose**: Manage stakeholder communications during deployment (Apr 26-May 3)  

**Capabilities**:
- Generate personalized stakeholder emails
- Track email delivery and acknowledgments
- Manage approval routing workflows
- Handle escalations for non-responsive stakeholders
- Prepare status reports

**Timeline**: April 26, 14:00-18:00 UTC (critical window)

**Invoke**: `@StakeholderCommunicationsAgent`

**Tools**:
- `scripts/generate-emails.py` - Interactive email generator
- `scripts/pre-flight-check.sh` - Pre-deployment validation
- Email templates in `EMAIL-DISTRIBUTION-TEMPLATES.md`

---

### 3. Staging Deployment Agent
**File**: `.github/agents/StagingDeploymentAgent.md`  
**Purpose**: Execute and monitor staging deployments (Apr 27-28)  

**Capabilities**:
- Execute blockchain-node Phase 3 staging deployment
- Execute PeachTree staging validation  
- Monitor health metrics and success criteria
- Conduct Go/No-Go Decision #1 (Apr 27, 14:00 UTC)
- Manage rollback procedures if needed

**Success Criteria** (8 required):
1. Uptime ≥ 99.9% (6 hours)
2. Error rate < 0.1%
3. Latency P50 < 100ms, P99 < 500ms
4. Database 100% operational
5. All health checks passing
6. Zero critical alerts
7. Load test passed (500+ req/sec)
8. Team consensus achieved

**Invoke**: `@StagingDeploymentAgent`

---

### 4. Production Deployment Agent
**File**: `.github/agents/ProductionDeploymentAgent.md`  
**Purpose**: Execute production deployments with phased traffic migration (May 1-3)  

**Capabilities**:
- Execute May 1 production deployment (10:00 UTC)
- Manage phased traffic: 0% → 50% → 75% → 100%
- Monitor production health in real-time
- Conduct health checks at each phase
- Execute emergency rollback if needed

**Phased Rollout**:
- 10:00: Deploy (0% traffic) + 15min validation
- 10:30: 50% traffic + 30min monitoring
- 11:00: 75% traffic + 30min monitoring
- 11:30: 100% traffic + 30min validation
- 12:00: Production complete ✅

**Invoke**: `@ProductionDeploymentAgent`

---

### 5. Blockchain Node Operations Agent
**File**: Agent definition in blockchain-node workspace  
**Purpose**: Manage blockchain node operations across distributed network  

**Capabilities**:
- Node deployment and consensus coordination
- P2P networking and RPC endpoints
- Multi-node testing (primary + ChromeOS nodes)
- Health monitoring and incident response

**Invoke**: When working with `/home/x/web3-blockchain-node/`

---

### 6. Network Integration Agent
**File**: Agent definition in workspace  
**Purpose**: Configure local network integration between workspaces  

**Capabilities**:
- Distributed deployment setup
- Network discovery and worker coordination
- ChromeOS Flex mini PC integration
- Multi-node blockchain configuration

---

### 7. Phase Execution Agent
**Purpose**: Execute deployment phases (Apr 26-May 3)  

**Phases**:
1. Publication (Apr 26-27)
2. Infrastructure (Apr 27-28)
3. Monitoring (Apr 28-29)
4. Community (Apr 29-30)
5. Verification (May 1-3)

**Capabilities**:
- Coordinate phase tasks
- Update checklists and track status
- Manage sign-offs

---

### 8. Hancock Verification Agent
**Purpose**: Final security verification for May 3 GO/NO-GO decision  

**Capabilities**:
- Coordinate Hancock verification layer (4 roles)
- Verify all phases complete
- Calculate health score
- Recommend GO/NO-GO decision

**Authority**: May 3 afternoon, final decision only

---

## Available Skills

### 1. Deployment Execution
**File**: `.github/skills/deployment-execution/SKILL.md`  
**Trigger**: Working with deployment procedures, stakeholder communications, Go/No-Go decisions  

**Provides**:
- Automated deployment procedure execution
- Stakeholder email generation
- Pre-flight check automation
- Decision framework guidance
- Progress tracking

**Scripts**:
- `scripts/pre-flight-check.sh`
- `scripts/generate-emails.py`

---

### 2. PeachTree Dataset Operations
**File**: `.github/skills/peachtree-dataset-operations/SKILL.md`  
**Trigger**: Working with PeachTree datasets, JSONL, safety gates, policy packs  

**Provides**:
- Dataset pipeline guidance
- Safety gate implementation
- Quality scoring and deduplication
- Policy pack compliance
- Trainer handoff workflows

**CLI Commands**:
- `peachtree plan`, `ingest`, `build`, `audit`, `policy`, `quality`, `dedup`, `export`, `card`, `handoff`

---

### 3. Security Dataset Integration
**File**: `.github/skills/security-dataset-integration/SKILL.md`  
**Trigger**: Ingesting CVE databases, vulnerability reports, security corpora  

**Provides**:
- MITRE CVE database integration
- Metasploit/ClamAV/security tool ingestion
- Hancock cybersecurity LLM support
- Security policy pack enforcement
- Ethical use compliance

**Organizations**:
- MITRE-Cyber-Security-CVE-Database (19 repos)
- Cybeviser
- 0ai-cyberviserai

**Primary Repositories**:
- mitre-cve-database (MIT, 37★) - PRIMARY CVE SOURCE
- metasploit-framework (15k★)
- sqlmap (6.2k★), john (2.5k★), clamav (849★), snort3 (666★)
- grok-promptss (441★) - Security prompts

---

### 4. Dataset Release
**File**: `.github/skills/dataset-release/SKILL.md`  
**Purpose**: Build PeachTree release bundles with SBOM/provenance  

**Provides**:
- Release bundle packaging
- SBOM and provenance generation
- Signatures and model cards
- Trainer handoff manifests

---

### 5. Policy Compliance
**File**: `.github/skills/policy-compliance/SKILL.md`  
**Purpose**: Evaluate datasets against policy packs and compliance requirements  

**Provides**:
- Policy pack evaluation
- License gate enforcement
- Compliance report generation
- Safety policy validation

---

### 6. Distributed Config Management
**File**: `.github/skills/distributed-config-management/SKILL.md`  
**Purpose**: Manage configuration across distributed local network infrastructure  

**Provides**:
- Multi-node configuration deployment
- ChromeOS/primary machine config sync
- Network configuration templating
- Environment-specific settings

---

### 7. Local Network Integration
**File**: `.github/skills/local-network-integration/SKILL.md`  
**Purpose**: Integrate web3-blockchain-node and PeachTree with ChromeOS Flex mini PC  

**Provides**:
- Distributed deployment setup
- Local network service configuration
- Cross-workspace communication
- Multi-node blockchain infrastructure

---

## Instructions

### 1. PeachTree Deployment
**File**: `.github/instructions/peachtree-deployment.instructions.md`  
**ApplyTo**: `**/*peachtree*/**`, `/tmp/peachtree/**`, `**/*dataset*/**`  

**Provides**:
- PeachTree development workflow
- Safety-first principles
- Testing requirements
- Deployment timeline context

---

### 2. Blockchain Node Deployment
**File**: `/home/x/web3-blockchain-node/.github/instructions/blockchain-node-deployment.instructions.md`  
**ApplyTo**: `/home/x/web3-blockchain-node/**`, `**/*blockchain*node*/**`, `**/k8s/**`  

**Provides**:
- Kubernetes deployment procedures
- Go testing and build workflows
- Phased rollout guidance
- Monitoring and incident response

---

## Multi-Organization Integration

### Configuration
**File**: `config/multi-org-security-datasets.yaml`  

**Organizations**:
1. **MITRE-Cyber-Security-CVE-Database** (Primary)
   - 19 repositories
   - 7 members across 3 teams (hakinsacks, tismchism, flux)
   - Owner: HackinSacks

2. **Cybeviser** (Johnny Watters)
3. **0ai-cyberviserai** (Johnny Watters)

### Ingestion Script
**File**: `scripts/ingest-multi-org-security.sh`  

**Process**:
1. Clone critical repositories
2. Ingest CVE records, Metasploit docs, Grok prompts
3. Build unified security dataset
4. Run safety gates and audit
5. Generate Hancock training handoff

### Documentation
**File**: `docs/multi-org-integration/README.md`  
**File**: `MULTI-ORG-INTEGRATION.md` (quick reference)

---

## Usage Examples

### Invoke Agent
```
"@StakeholderCommunicationsAgent Generate emails for Apr 26 deployment"
"@StagingDeploymentAgent Execute Phase 3 staging deployment"
"@ProductionDeploymentAgent Begin May 1 production rollout"
```

### Trigger Skill
Skills activate automatically based on `applyTo` patterns:
- Editing `.github/skills/*/SKILL.md` → `agent-customization` skill
- Editing `/tmp/peachtree/**` → `peachtree-deployment` instructions
- Working with CVE data → `security-dataset-integration` skill

### Run Automation
```bash
# Pre-flight check before deployment
bash scripts/pre-flight-check.sh

# Generate stakeholder emails
python3 scripts/generate-emails.py

# Multi-org security ingestion
bash scripts/ingest-multi-org-security.sh
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VS Code Workspace                        │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │  /tmp/peachtree      │  │  /home/x/web3-blockchain │    │
│  │  (PeachTree ML)      │  │  (Blockchain Node)       │    │
│  └──────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Framework (.github/)                 │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐           │
│  │ Skills   │  │  Agents  │  │  Instructions  │           │
│  └──────────┘  └──────────┘  └────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-Organization Data Sources                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │  MITRE-Cyber-Security-CVE-Database (19 repos)   │       │
│  │  ├─ mitre-cve-database (CRITICAL)               │       │
│  │  ├─ metasploit-framework (15k★)                 │       │
│  │  ├─ sqlmap, john, clamav, snort3, grok-prompts  │       │
│  │  └─ 12 more security tools                      │       │
│  └─────────────────────────────────────────────────┘       │
│  Cybeviser, 0ai-cyberviserai                                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              PeachTree Dataset Control Plane                 │
│  Safety Gates → Quality Checks → Policy Compliance          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│             Hancock Cybersecurity LLM Training               │
└─────────────────────────────────────────────────────────────┘
```

---

## Timeline Integration

### April 26 (YESTERDAY) - Stakeholder Communications
- **Agent**: StakeholderCommunicationsAgent
- **Skill**: deployment-execution
- **Status**: ✅ Templates and automation ready

### April 27 (TODAY) - Staging Deployment
- **Agent**: StagingDeploymentAgent
- **Skill**: deployment-execution
- **Status**: 🔄 IN PROGRESS (06:00-14:00 UTC)

### April 27-28 - 24-Hour Validation
- **Agents**: StagingDeploymentAgent, PeachTreeAI
- **Status**: 🔄 Monitoring period

### April 28 - Final Go/No-Go Decision
- **Agent**: Phase Execution Agent
- **Status**: ⏳ PENDING (12:00 UTC)

### May 1-3 - Production Deployment
- **Agent**: ProductionDeploymentAgent
- **Skill**: deployment-execution
- **Status**: ⏳ SCHEDULED

---

## Contact & Support

**Owner**: Johnny Watters  
**GitHub**: @0ai-Cyberviser, @cyberviser, @cyberviser-dotcom  
**Organization**: MITRE-Cyber-Security-CVE-Database (HackinSacks)  
**Email**: hackinsacks@proton.me  

**Last Updated**: April 27, 2026  
**Status**: ✅ All systems committed and operational
