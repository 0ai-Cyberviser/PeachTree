# PeachTree Roadmap

This document outlines the planned development direction for PeachTree. Priorities and timelines may shift based on community feedback and project needs.

## Vision

Build the most trusted, transparent, and auditable dataset engine for AI/ML training in cybersecurity and beyond.

## Core Principles

1. **Provenance First** — Every record tracks its origins
2. **Safety by Default** — Security gates built in, not bolted on
3. **Local-First** — No blind public data collection
4. **Human-in-the-Loop** — Always require approval for important decisions
5. **Transparent** — Full audit trails for compliance

## Current Version: 0.9.0

### ✅ Completed

- ✅ Core JSONL dataset engine
- ✅ Safety gates (secrets, licenses, content)
- ✅ Policy pack evaluation
- ✅ Deduplication (3 methods)
- ✅ Quality scoring
- ✅ Release bundles with SBOM
- ✅ Trainer handoff manifests
- ✅ Comprehensive documentation (42 markdown files)
- ✅ 129 unit tests (91% coverage)
- ✅ CI/CD infrastructure
- ✅ GitHub Pages deployment

---

## Roadmap

### Phase 1: Foundation (2026 Q2)

**Focus:** Stability, documentation, and community

- [ ] **Code coverage** → 95%+
- [ ] **Performance benchmarking** → Baseline metrics
- [ ] **API documentation** → Interactive API docs
- [ ] **Example datasets** → 5+ real-world examples
- [ ] **Community feedback** → Gathering and prioritization
- [ ] **Release v0.10.0** → Stable API guarantee

**Estimated:** Q2 2026

### Phase 2: Advanced Deduplication (2026 Q3)

**Focus:** Improving dataset quality through smarter deduplication

- [ ] **Vector-based deduplication** → Using embeddings for similarity
- [ ] **ML-powered deduplication** → Learning from past datasets
- [ ] **Benchmark dedup methods** → Comparing effectiveness
- [ ] **Dedup visualization** → Show clustering and removal
- [ ] **Cross-dataset deduplication** → Remove duplicates across multiple datasets

**Estimated:** Q3 2026

### Phase 3: Web UI & Dashboard (2026 Q4)

**Focus:** Making PeachTree accessible to non-CLI users

- [ ] **Web dashboard** → Visual dataset building
- [ ] **Dataset explorer** → Browse and filter JSONL records
- [ ] **Policy pack editor** — Visual policy composition
- [ ] **Real-time audit** → Live status during building
- [ ] **Export & download** → Package datasets for sharing
- [ ] **Docker image** → Containerized web UI

**Estimated:** Q4 2026

### Phase 4: LoRA Fine-Tuning (2027 Q1)

**Focus:** Direct integration with training workflows

- [ ] **LoRA adapter generation** → Optimized for different models
- [ ] **Dataset-to-training pipeline** → One-click training
- [ ] **Model card generation** → Automated documentation
- [ ] **Weights & Biases integration** → Track training runs
- [ ] **Evaluation metrics** → Quality and safety metrics

**Estimated:** Q1 2027

### Phase 5: Ecosystem Integration (2027 Q2)

**Focus:** Tighter integration with CyberViser ecosystem

- [ ] **Hancock integration** → Cybersecurity LLM agent datasets
- [ ] **PeachFuzz integration** → Fuzzing corpus preparation
- [ ] **0AI hub integration** → Public dataset sharing
- [ ] **CyberViser integration** → Project documentation pipeline
- [ ] **API endpoints** → REST API for dataset operations

**Estimated:** Q2 2027

---

## Feature Requests by Priority

### High Priority (Next 2 quarters)

1. **Dataset versioning** — Track dataset changes over time
   - Version control for datasets
   - Reproducible builds
   - Rollback capability

2. **Advanced filtering** — More powerful query language
   - Semantic search
   - Custom filters
   - Composite rules

3. **Batch operations** — Process multiple datasets
   - Batch building
   - Batch auditing
   - Batch publishing

### Medium Priority (2-4 quarters)

4. **Integration with ML frameworks** — PyTorch, TensorFlow
   - Direct dataset loading
   - Streaming support
   - Format conversion

5. **Cloud storage support** — S3, GCS, Azure
   - Remote dataset storage
   - Distributed building
   - Multi-region support

6. **Notification system** — Alerts and webhooks
   - Build completion
   - Policy violations
   - Security alerts

### Lower Priority (4+ quarters)

7. **GraphQL API** — Alternative to REST API
8. **Dataset marketplace** — Share and discover datasets
9. **Collaborative editing** — Multi-user dataset building
10. **Mobile app** — Track datasets on the go

---

## Technology & Infrastructure

### Testing & Quality

- [ ] Increase coverage → 95%+
- [ ] Add performance tests → Benchmarking
- [ ] Add security tests → Vulnerability scanning
- [ ] Improve CI/CD → Parallel testing
- [ ] Code quality gates → Stricter standards

### Documentation

- [ ] Interactive tutorials → Jupyter notebooks
- [ ] Video walkthroughs → Building datasets step-by-step
- [ ] Case studies → Real-world examples
- [ ] Blog posts → Technical deep dives
- [ ] Architecture diagrams → Visual documentation

### Community

- [ ] GitHub Discussions → Active Q&A
- [ ] Monthly updates → Community calls
- [ ] Contribution guide → Lower barriers to entry
- [ ] Code examples → Real-world templates
- [ ] Security scanning → Continuous updates

---

## Known Limitations

### Current

- **CLI-only interface** — No GUI yet (Phase 3 roadmap)
- **Single-threaded building** — Could parallelize
- **Limited filtering** — Basic query support
- **No API** — Will be added in Phase 5
- **No version control** — Coming in Phase 2

### Accepted

- **Not for streaming** — Batch-oriented tool
- **Not for real-time** — Asynchronous builds only
- **Not for small devices** — Requires reasonable compute

---

## Dependencies & Constraints

### External Dependencies

- **Python 3.10+** — Minimum version requirement
- **pydantic** — Data validation framework
- **pyyaml** — Configuration parsing
- **pytest** — Testing framework

### Infrastructure

- **GitHub Actions** — CI/CD platform
- **Docker** — Containerization
- **mkdocs** — Documentation generation
- **PyPI** — Package distribution

---

## How to Contribute to the Roadmap

### Suggest Features

1. Check if idea exists in [Issues](https://github.com/0ai-Cyberviser/PeachTree/issues)
2. Open [Feature Request](/.github/ISSUE_TEMPLATE/feature_request.md)
3. Join discussion in [Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)

### Vote on Priorities

1. Upvote issues you care about 👍
2. Comment with your use cases
3. Share in community calls
4. Help with implementation

### Implement Features

1. Check roadmap for planned work
2. Review [Contributing Guide](CONTRIBUTING-ADVANCED.md)
3. Start feature branch: `git checkout -b feature/my-feature`
4. Open PR and reference roadmap item

---

## Timeline & Versioning

### Version Scheme

- **0.9.x** — Current stable (LTS until 2027-04-26)
- **0.10.x** → Foundation phase (2026 Q2)
- **0.11.x** → Advanced dedup phase (2026 Q3)
- **0.12.x** → Web UI phase (2026 Q4)
- **1.0.0** → Production ready (2027 Q1+)

### Release Schedule

- **Minor releases** — Every 6 weeks (minor features, fixes)
- **Patch releases** — As needed (bug fixes, security)
- **Major releases** — As planned (breaking changes, major phases)

---

## Feedback & Communication

- **Roadmap discussions** → [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)
- **Monthly updates** → Blog posts on GitHub
- **Community calls** → TBD (quarterly)
- **Feature requests** → [GitHub Issues](https://github.com/0ai-Cyberviser/PeachTree/issues)
- **Contact** → roadmap@cyberviser.io

---

**Last Updated:** 2026-04-27

**Next Update:** 2026-05-27

Thank you for following PeachTree's development! 🍑📊
