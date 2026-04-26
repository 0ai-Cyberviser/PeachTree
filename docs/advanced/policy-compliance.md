# Policy Compliance

Evaluate datasets against policy packs and compliance requirements.

## Policy Evaluation

```bash
peachtree readiness dataset.jsonl \
  --policy-pack commercial-ready \
  --output readiness.json
```

## Built-In Policies

- **commercial-ready**: Enterprise compliance
- **open-safe**: Public license compatible
- **internal-review**: Requires human approval

## Custom Policies

Define in configuration files or code.

## Reports

Generate compliance reports:

```bash
peachtree policy-pack dataset.jsonl --pack commercial-ready --output report.json
```

## See Also

- [Policy Packs](../user-guide/policy-packs.md)
- [License Gates](license-gates.md)
