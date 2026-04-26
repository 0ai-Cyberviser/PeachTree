# Code Quality

Standards and tools for maintaining PeachTree code quality.

## Tools

- **ruff**: Linting and code style
- **mypy**: Type checking
- **pytest**: Testing
- **coverage**: Test coverage

## Checks

```bash
# Lint
python -m ruff check src/

# Auto-fix
python -m ruff check --fix src/

# Type check
python -m mypy src/peachtree/ --strict

# Tests
python -m pytest tests/ --cov=src/peachtree

# Coverage report
python -m coverage report
```

## Standards

- Python 3.10+ with type hints
- 90%+ test coverage required
- 0 ruff linting violations
- 0 mypy type errors
- Clear docstrings for public APIs

## See Also

- [Testing](testing.md)
- [Development](development.md)
