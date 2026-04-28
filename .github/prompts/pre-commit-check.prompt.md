---
description: "Run complete pre-commit validation (tests, linting, type checking) before committing"
agent: "agent"
tools: [execute]
---

# Pre-Commit Validation

Run all required checks before committing changes to PeachTree.

## Required Checks

### 1. Test Suite (REQUIRED: All 129+ tests must pass)
```bash
python -m pytest tests/ -v
```

### 2. Code Linting (REQUIRED: 0 violations)
```bash
python -m ruff check src/ tests/
```

### 3. Type Checking (REQUIRED: No mypy errors)
```bash
python -m mypy src/peachtree/ --strict
```

### 4. Test Coverage (TARGET: >90%)
```bash
python -m pytest tests/ --cov=src/peachtree --cov-report=term-missing
```

## Safety-First Validation

Verify core principles:
- ✅ No secrets or credentials in code
- ✅ Provenance tracking intact
- ✅ Local-only defaults maintained
- ✅ Safety gates not bypassed

## Execution

Run all checks and provide summary:
- ✅ Tests: {passed}/{total}
- ✅ Linting: {violations} violations
- ✅ Type checking: {errors} errors
- ✅ Coverage: {percentage}%

If any checks fail:
1. Display failure details
2. Suggest fixes
3. Block commit recommendation

If all checks pass:
- Display ✅ All checks passed - safe to commit
- Provide commit command suggestion
