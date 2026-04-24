# Dataset Registry, Artifact Signing, SBOM/Provenance, and Release Bundles

PeachTree v0.8.0 adds local release-governance tooling for reviewed datasets.

## New CLI

```bash
peachtree registry
peachtree sign
peachtree sbom
peachtree bundle
```

## Build a registry

```bash
peachtree registry data/datasets data/exports reports \
  --name PeachFuzz-Dataset-v1 \
  --version 2026.04.24 \
  --output reports/registry.json \
  --markdown-output reports/registry.md
```

## Sign an artifact

```bash
peachtree sign \
  --artifact reports/registry.json \
  --key "$PEACHTREE_SIGNING_KEY" \
  --key-id local-ci-key \
  --output reports/registry.sig.json
```

Verify:

```bash
peachtree sign \
  --verify \
  --artifact reports/registry.json \
  --signature reports/registry.sig.json \
  --key "$PEACHTREE_SIGNING_KEY"
```

PeachTree signatures use dependency-free HMAC-SHA256 metadata. For production distribution, verify with organization key management and consider Sigstore, GPG, or PKI.

## Generate SBOM/provenance

```bash
peachtree sbom \
  --registry reports/registry.json \
  --output reports/sbom.json \
  --markdown-output reports/sbom.md
```

## Build a release bundle

```bash
peachtree bundle \
  data/datasets/peachfuzz-instruct-deduped.jsonl \
  reports/quality.json \
  reports/license-gate.json \
  reports/policy-pack.json \
  reports/model-card.md \
  --name PeachFuzz-Dataset-v1 \
  --version 2026.04.24 \
  --output dist/peachfuzz-dataset-v1.zip \
  --signing-key "$PEACHTREE_SIGNING_KEY" \
  --report reports/release-bundle.json
```

## Safety model

- local-only
- no model training
- no dataset upload
- no public GitHub scraping
- release artifacts are for human review and reproducibility
- HMAC signatures are integrity metadata, not legal or cryptographic attestation by themselves
