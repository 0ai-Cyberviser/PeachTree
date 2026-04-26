# License Gates

Validate dataset licenses for compatibility and compliance.

## License Validation

```bash
peachtree license-gate dataset.jsonl \
  --allowed-licenses MIT,Apache-2.0,BSD-3-Clause \
  --output license-report.json
```

## Supported Licenses

- MIT
- Apache-2.0
- BSD-3-Clause
- GPL-2.0, GPL-3.0
- CC-BY-4.0
- ISC
- Others via configuration

## Reports

View license compliance:

```bash
peachtree audit dataset.jsonl  # Includes license info
```

## See Also

- [Safety Gates](../user-guide/safety.md)
- [Policy Packs](../user-guide/policy-packs.md)
