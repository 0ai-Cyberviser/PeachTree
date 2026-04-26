# Testing

Guide to writing and running tests for PeachTree.

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific file
python -m pytest tests/test_builder.py -v

# With coverage
python -m pytest tests/ --cov=src/peachtree --cov-report=html
```

## Testing Patterns

- Fixture-based with pytest
- Provenance validation
- Safety gate testing
- CLI integration tests
- JSON/Markdown validation

## Coverage

Current coverage: 91%

Target: >= 90%

## See Also

- [Development Guide](development.md)
- [Code Quality](code-quality.md)
