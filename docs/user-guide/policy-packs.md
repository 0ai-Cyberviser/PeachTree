# Policy Packs

Policy packs are composable safety and quality policies for dataset validation and compliance.

## Built-In Packs

### commercial-ready
Enterprise compliance for commercial model training:
- Verified licenses only (MIT, Apache-2.0)
- Quality score >= 0.85
- Requires security review
- Full provenance required

```bash
peachtree readiness dataset.jsonl --policy-pack commercial-ready
```

### open-safe
Public license compatibility:
- Permissive licenses only
- Quality score >= 0.80
- No proprietary content
- Attribution required

### internal-review
Internal projects requiring approval:
- Custom license policies
- Manual review gate
- Audit trail required

## Creating Custom Packs

Define in `peachtree.yaml`:

```yaml
policy_packs:
  security-focused:
    quality_threshold: 0.90
    required_metadata:
      - security_reviewed
    allowed_licenses:
      - MIT
      - Apache-2.0
    blocked_patterns:
      - "TODO"
      - "FIXME"
```

## Evaluation

```bash
peachtree policy-pack dataset.jsonl \
  --pack security-focused \
  --output policy-report.json
```

## See Also

- [CLI Reference](../user-guide/cli.md)
- [Advanced: Policy Compliance](../advanced/policy-compliance.md)
