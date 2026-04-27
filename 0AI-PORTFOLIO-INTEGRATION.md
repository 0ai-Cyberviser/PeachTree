# PeachTree Integration with 0AI Portfolio

**Status:** Production Ready  
**Portfolio:** 0AI / CyberViser  
**Company Site:** https://cyberviserai.com/  
**Documentation:** https://0ai-cyberviser.github.io/PeachTree/  
**Repository:** https://github.com/0ai-Cyberviser/PeachTree  
**Date:** April 27, 2026

---

## Overview

**PeachTree** is the dataset control plane for the [CyberViser AI](https://cyberviserai.com/) portfolio, providing provenance-first, safety-aware dataset building infrastructure for AI/ML training workflows.

As showcased on [cyberviserai.com](https://cyberviserai.com/#stack), PeachTree is the third component of the CyberViser stack:
- 🍑 **PeachFuzz** - Defensive fuzzing
- 🌵 **CactusFuzz** - Authorized adversarial testing  
- 🌳 **PeachTree** - Dataset engine with provenance

### Position in 0AI Portfolio

PeachTree serves as the **training data infrastructure** layer, integrating with:

- **Hancock** - Cybersecurity LLM (primary training consumer)
- **PeachFuzz** - Fuzzing data source
- **MrClean** - Repository cleanup and quality gates
- **CyberViser ViserHub** - Orchestration and tooling

---

## Portfolio Integration Points

### 1. Hancock Integration (Cybersecurity LLM)

**Data Flow:**
```
PeachFuzz Fuzzing Reports
    ↓
PeachTree Ingestion
    ↓
Safety Gates + Policy Packs
    ↓
JSONL Training Dataset
    ↓
Hancock Model Training
```

**Capabilities:**
- Ingest security-relevant source code and documentation
- Filter secrets, unsafe content, unknown licenses
- Build provenance-tracked JSONL datasets
- Generate model cards and trainer handoff manifests
- Release bundles with SBOM/signatures

### 2. MrClean Integration (Policy Automation)

**Data Flow:**
```
MrClean Repo Analysis
    ↓
PeachTree Quality Gates
    ↓
Policy Pack Evaluation
    ↓
Approved Dataset Records
```

**Capabilities:**
- Policy-first dataset building
- License compliance checking
- Quality scoring and deduplication
- Review gates before training launch

### 3. Distributed Infrastructure (web3-blockchain-node)

**Deployment:**
```
Primary Machine (Controller)
    ↓
ChromeOS Flex Workers (Distributed Processing)
    ↓
Parallel Dataset Building
```

**Capabilities:**
- Multi-node dataset processing
- Worker coordination and load balancing
- Distributed safety gate execution
- Result aggregation

---

## Key Features for 0AI Portfolio

### Provenance-First Architecture
Every dataset record tracks:
- Source repository and commit hash
- Source file path and digest
- Transformation history
- License and safety status

### Safety-Aware Pipeline
Built-in gates for:
- Secret filtering (API keys, tokens, credentials)
- License compliance (unknown/incompatible licenses)
- Unsafe content detection
- Quality scoring

### Local-First Operation
- No automatic public GitHub scraping
- Owned repository ingestion only
- Explicit allow-lists for external sources
- Human approval required before training

### Compliance & Traceability
- SBOM/provenance generation
- Model card creation
- Trainer handoff manifests
- Release bundle signing

---

## Public Documentation

**GitHub Pages Site:** https://0ai-cyberviser.github.io/PeachTree/

Comprehensive documentation includes:
- Quick start guide
- CLI reference (`peachtree plan`, `ingest`, `build`, `audit`, `policy`)
- Architecture overview
- Integration guides
- Troubleshooting
- API reference
- Deployment guide

---

## Portfolio Positioning

### Tagline
**"Provenance-first dataset control plane for safe, traceable AI/ML training workflows"**

### Description for 0AI Portfolio Page
```
PeachTree

Dataset control plane with provenance tracking, safety gates, and policy-first
automation for AI/ML training workflows. Integrates with Hancock for cybersecurity
model training.

[OPEN PEACHTREE SITE](https://0ai-cyberviser.github.io/PeachTree/)
```

### Key Differentiators
- **Provenance-first**: Every record tracked from source to training
- **Safety-aware**: Built-in secret filtering and license compliance
- **Local-first**: No automatic external data collection
- **Compliance-ready**: SBOM, model cards, signatures
- **Hancock-integrated**: Purpose-built for cybersecurity LLM training

---

## Technical Specifications

### Language & Stack
- Python 3.9+
- CLI built with Click
- JSONL for dataset records
- YAML for manifests
- MkDocs for documentation

### Architecture
- Controller-worker model for distributed processing
- RecursiveLearningTree for intelligent data planning
- Safety gates and policy packs as composable primitives
- Deterministic deduplication and quality scoring

### Deployment Options
1. **Single machine** - CLI + local processing
2. **Distributed** - Controller + multiple workers
3. **ChromeOS Flex** - Integrated with web3-blockchain-node

### Testing
- 129 tests passing
- 91% code coverage
- Integration tests for all workflows
- Policy pack validation

---

## Release Status

**Version:** 0.1.0 (Pre-release)  
**Status:** Production-ready for internal use  
**Public Release:** Pending final documentation review

### Current Capabilities
✅ Repository ingestion  
✅ JSONL dataset building  
✅ Safety gates (secrets, licenses, unsafe content)  
✅ Policy packs (quality, dedup, license, review)  
✅ Model card generation  
✅ Trainer handoff manifests  
✅ Release bundles with SBOM  
✅ Distributed worker coordination  

### Roadmap
- [ ] Public dataset registry
- [ ] Enhanced quality scoring algorithms
- [ ] Additional safety gate types
- [ ] Cloud deployment guides (AWS, GCP, Azure)
- [ ] Hancock training integration automation

---

## Usage in 0AI Workflows

### Example: Hancock Training Dataset

```bash
# 1. Plan dataset from owned repositories
peachtree plan --source-repos="cyberviser/Hancock,0ai-Cyberviser/PeachFuzz"

# 2. Ingest with safety gates
peachtree ingest --apply-safety-gates

# 3. Build JSONL dataset
peachtree build --quality-threshold=0.8

# 4. Audit provenance
peachtree audit --check-provenance

# 5. Evaluate policy compliance
peachtree policy --pack=commercial-ready

# 6. Generate trainer handoff
peachtree export --format=trainer-handoff

# 7. Create release bundle
peachtree release --include-sbom --sign
```

### Example: Distributed Processing

```bash
# Primary machine (controller)
peachtree controller --api-listen=0.0.0.0:8000

# ChromeOS workers (1-N)
peachtree worker --controller=http://192.168.1.100:8000 --roles=build,audit

# Automatic load balancing and result aggregation
```

---

## Security & Compliance

### Security Model
- Local-first data processing (no cloud upload by default)
- Secret filtering before any storage
- License compliance validation
- Human review gates before training

### Compliance Features
- SBOM generation (software bill of materials)
- Provenance tracking (source → training)
- Model cards (dataset documentation)
- Digital signatures for releases

### Support Contact
- **Security:** 0ai@cyberviserai.com
- **Support:** cyberviser@proton.me
- **Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues

---

## Integration with Other 0AI Projects

### Hancock (Cybersecurity LLM)
- **Role:** Primary training data consumer
- **Integration:** Trainer handoff manifests → LoRA jobs
- **Data Sources:** Security code, fuzzing reports, documentation

### PeachFuzz (Fuzzing Infrastructure)
- **Role:** Data source provider
- **Integration:** Fuzz results → PeachTree ingestion
- **Use Case:** Training on vulnerability patterns

### MrClean (PR Cleanup Automation)
- **Role:** Quality gate provider
- **Integration:** Repo analysis → PeachTree policy packs
- **Use Case:** Dataset quality enforcement

### CyberViser ViserHub (Orchestration)
- **Role:** Workflow orchestration
- **Integration:** PeachTree CLI commands → automated pipelines
- **Use Case:** End-to-end training workflows

---

## Portfolio Statistics

**Repository:**
- Total commits: 95+
- Total lines: 8,000+ (Python)
- Documentation: 100+ pages
- Tests: 129 passing (91% coverage)

**Components:**
- CLI commands: 15+
- Safety gates: 3 built-in
- Policy packs: 4 reference implementations
- Skills: 3 (dataset release, policy compliance, distributed ops)
- Agents: 1 (PeachTreeAI for VS Code)

**Integration:**
- Hancock: Training pipeline ready
- web3-blockchain-node: Distributed deployment ready
- GitHub Pages: Documentation deployed
- GitHub Actions: CI/CD workflows active

---

## Next Steps for Portfolio Integration

1. **Add to 0AI Portfolio Page**
   - Update https://0ai-cyberviser.github.io/0ai/
   - Add PeachTree card under "Core Projects"
   - Link to documentation site

2. **Cross-Link Documentation**
   - Link Hancock docs → PeachTree
   - Link PeachTree docs → Hancock
   - Create integration guides

3. **Public Release**
   - Final documentation review
   - Release v1.0.0
   - Announce on 0AI channels

4. **Continuous Integration**
   - Hancock training automation
   - Scheduled dataset builds
   - Quality metrics dashboard

---

## Conclusion

PeachTree is **production-ready** and positioned to serve as the dataset control plane for the entire 0AI portfolio. Its provenance-first, safety-aware architecture makes it ideal for building compliant, traceable training datasets for Hancock and future AI/ML projects.

**Status:** Ready for 0AI portfolio integration  
**Documentation:** Published at https://0ai-cyberviser.github.io/PeachTree/  
**Next Action:** Add to 0AI portfolio page

---

**Document Version:** 1.0  
**Last Updated:** April 27, 2026  
**Owner:** Johnny Watters / 0ai-Cyberviser
