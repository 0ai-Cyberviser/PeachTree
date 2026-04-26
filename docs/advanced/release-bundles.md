# Release Bundles

Package datasets with SBOM, signatures, and documentation for distribution.

## Creating Release Bundles

```bash
peachtree bundle dataset.jsonl \
  --output release/ \
  --sign \
  --include-sbom \
  --model-card model-card.md
```

## Bundle Contents

```
release/
├── dataset.jsonl          # Training JSONL
├── manifest.json          # Metadata
├── sbom.json              # Supply chain
├── sbom.md                # SBOM markdown
├── signatures.json        # Cryptographic signatures
├── model-card.md          # Model documentation
└── registry.json          # Artifact registry
```

## Verification

```bash
peachtree sbom release/sbom.json --verify
```

## See Also

- [Policy Compliance](policy-compliance.md)
- [Model Cards](model-cards.md)
- [Training Handoff](trainer-handoff.md)
