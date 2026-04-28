# Training Dataset Handoff: Hancock-BugBounty-Complete-v1

**Dataset**: unified-bugbounty-training.jsonl  
**Model**: Hancock-BugBounty-Complete-v1  
**Base**: mistralai/Mistral-7B-Instruct-v0.3  
**Records**: 10  
**Quality**: 39/100  

## Status: ⚠️ CONDITIONAL APPROVAL

### Coverage
- HackerOne (5): Crypto exchanges, IDOR, CSRF, Web3, disclosure
- Enterprise (5): Apple ($1M), Google ($1.5M), Microsoft ($300K), Bugcrowd

### Files
- dataset.jsonl (37K) - Training data
- trainer-handoff.json - Parameters
- sbom.json - Bill of Materials
- model-card.md - Full model card
- quality-report.json - Metrics
- SHA256SUMS - Checksums

### Training
- Trainer: Unsloth
- GPU: A100 (40GB) or 2x RTX 4090
- Time: 15-30 min
- Batch: 32, LR: 0.0001, Epochs: 10

### Conditions
1. Internal use only
2. Expand to 100+ before production
3. Human oversight required
4. Follow responsible disclosure

### Verify
```bash
sha256sum -c SHA256SUMS
jq . dataset.jsonl > /dev/null && echo "OK"
```

**Ready**: Seed training ✅ | Production ⏳ (expand first)
