# Safety Gates

Learn about PeachTree's built-in safety mechanisms for filtering secrets, validating licenses, and ensuring content safety.

## Overview

Safety gates protect your training datasets by filtering:

- **Secrets & Credentials**: API keys, passwords, tokens
- **License Violations**: Incompatible licenses
- **Unsafe Content**: Patterns or harmful material
- **Low Quality**: Records below quality threshold

## Secret Filtering

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-secrets
```

### Detected Patterns

- AWS keys, GCP credentials
- API tokens (GitHub, OpenAI, etc.)
- Private SSH keys
- Database passwords
- OAuth tokens
- Generic password patterns

### Custom Patterns

```yaml
safety_gates:
  secret_patterns:
    - pattern: "SECRET_KEY.*=.*"
      type: "custom_secret"
```

## License Gates

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --allowed-licenses MIT,Apache-2.0,BSD-3-Clause
```

Compatible licenses include:
- MIT
- Apache-2.0
- BSD-3-Clause
- CC-BY-4.0
- ISC

## Content Safety

Filter unsafe or inappropriate content:

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-unsafe-content
```

## See Also

- [Policy Packs](policy-packs.md) - Composable safety policies
- [License Gates](../advanced/license-gates.md) - License compliance
- [Quality Scoring](quality.md) - Content quality metrics
