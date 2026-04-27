# Add PeachTree to 0AI Portfolio Page

This document provides the exact HTML/Markdown snippet to add PeachTree to the 0AI portfolio page at https://0ai-cyberviser.github.io/0ai/

---

## Portfolio Card for "Core Projects" Section

Add this card alongside Hancock, MrClean, and CyberViser ViserHub:

```html
### PeachTree

Dataset control plane with provenance tracking, safety gates, and policy-first
automation for AI/ML training workflows. Integrates with Hancock for cybersecurity
model training.

[OPEN PEACHTREE SITE](https://0ai-cyberviser.github.io/PeachTree/)
```

---

## Full Project Description (Extended)

If there's a detailed projects page, use this fuller description:

```markdown
### PeachTree

**Provenance-first dataset control plane for safe, traceable AI/ML training workflows**

PeachTree is the training data infrastructure layer for the 0AI portfolio, providing:

- **Provenance tracking** - Every dataset record traced from source repository to training
- **Safety gates** - Built-in secret filtering, license compliance, unsafe content detection
- **Policy-first automation** - Composable policy packs for quality, deduplication, and compliance
- **Local-first operation** - No automatic public data scraping, owned repositories only
- **Hancock integration** - Purpose-built for cybersecurity LLM training datasets

**Key features:**
- RecursiveLearningTree for intelligent data planning
- JSONL dataset building with deterministic deduplication
- SBOM/provenance generation and digital signatures
- Model card creation and trainer handoff manifests
- Distributed processing with controller-worker architecture

**Integration points:**
- Hancock (cybersecurity LLM) - primary training consumer
- PeachFuzz (fuzzing data) - vulnerability pattern ingestion
- MrClean (repo cleanup) - quality gate provider
- web3-blockchain-node - distributed infrastructure

[OPEN PEACHTREE SITE](https://0ai-cyberviser.github.io/PeachTree/)
[OPEN REPOSITORY](https://github.com/0ai-Cyberviser/PeachTree)
```

---

## Portfolio Statistics Update

Update the portfolio stats section:

**Current (before PeachTree):**
- OPERATING ACCOUNTS: 3
- FLAGSHIP PROJECTS: 4

**Updated (with PeachTree):**
- OPERATING ACCOUNTS: 3
- FLAGSHIP PROJECTS: 5

---

## Suggested Portfolio Order

Recommended order for "Core Projects" section:

1. **Hancock** - AI-powered cybersecurity workflows (flagship)
2. **PeachTree** - Dataset control plane for AI/ML training (new)
3. **MrClean** - Policy-first automation for PR cleanup
4. **CyberViser ViserHub** - AI-assisted cybersecurity tooling
5. **0AI Profile Layer** - Public profile repositories

**Rationale:** PeachTree directly supports Hancock (feeds training data), so positioning it second makes the portfolio flow logical: Hancock (consumer) → PeachTree (data provider) → supporting tools.

---

## GitHub Topics/Tags for PeachTree Repo

Ensure the PeachTree repository has these topics for portfolio discoverability:

```
0ai
cyberviser
dataset
machine-learning
training-data
provenance
safety-gates
policy-automation
hancock-integration
jsonl
```

---

## Cross-Linking

### From Hancock Documentation
Add link to PeachTree in Hancock's documentation:

```markdown
## Training Data Pipeline

Hancock training datasets are built using [PeachTree](https://0ai-cyberviser.github.io/PeachTree/),
the 0AI dataset control plane. PeachTree provides provenance tracking, safety gates,
and policy-first automation for building compliant training datasets.
```

### From PeachTree Documentation
Already included in PeachTree docs under "Integration" section.

---

## Repository Settings

Ensure PeachTree repository settings are configured:

**Homepage URL:** https://0ai-cyberviser.github.io/PeachTree/  
**Description:** Dataset control plane with provenance tracking, safety gates, and policy-first automation for AI/ML training workflows  
**Topics:** 0ai, cyberviser, dataset, machine-learning, training-data, provenance, safety-gates  
**GitHub Pages:** Enabled, deploying from `gh-pages` branch

---

## Verification Checklist

Before announcing PeachTree on the portfolio:

- [x] GitHub Pages deployed and accessible
- [x] Documentation complete (100+ pages)
- [x] Tests passing (129 tests, 91% coverage)
- [x] Repository homepage URL set
- [x] Repository description added
- [x] Topics/tags configured
- [ ] Added to 0AI portfolio page (pending)
- [ ] Cross-links to Hancock added (pending)
- [ ] Portfolio statistics updated (pending)
- [ ] Announced on 0AI channels (pending)

---

## Implementation Steps

1. **Update 0AI portfolio page source**
   - Clone/edit the repository hosting https://0ai-cyberviser.github.io/0ai/
   - Add PeachTree card to "Core Projects" section
   - Update portfolio statistics
   - Commit and deploy

2. **Update PeachTree repository settings**
   - Set homepage URL
   - Add description
   - Configure topics

3. **Add cross-links**
   - Update Hancock documentation to reference PeachTree
   - Verify PeachTree documentation links to Hancock

4. **Announce**
   - Update README files
   - Social media/channels (if applicable)
   - Internal team notification

---

## Contact for Portfolio Updates

**Portfolio Owner:** Johnny Watters / 0ai-Cyberviser  
**Email:** 0ai@cyberviserai.com, cyberviser@proton.me  
**GitHub:** https://github.com/0ai-Cyberviser

---

**Document Status:** Ready for implementation  
**Date:** April 27, 2026  
**Action Required:** Update 0AI portfolio page HTML/Markdown
