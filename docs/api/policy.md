# API Reference - Policy

Policy pack and evaluation API.

## PolicyPackEvaluator

```python
from peachtree.policy_packs import PolicyPackEvaluator

evaluator = PolicyPackEvaluator()
result = evaluator.evaluate(dataset, pack_name="commercial-ready")
```

## Built-In Packs

- commercial-ready
- open-safe
- internal-review

See [Policy Packs](../user-guide/policy-packs.md) for details.
