# Troubleshooting

Common issues and solutions.

## Installation Issues

### ImportError: No module named peachtree

Reinstall in development mode:

```bash
pip install -e ".[dev]"
```

### Permission denied

Use `--break-system-packages` or virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install peachtree-ai
```

## Dataset Building

### Dataset is too slow

- Use `content-hash` deduplication instead of `semantic`
- Run on machine with more CPU
- Stream process large files

### Secrets still included

Ensure `--filter-secrets` flag:

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-secrets
```

### License validation fails

Check detected licenses:

```bash
peachtree audit dataset.jsonl
```

Then specify allowed licenses:

```bash
peachtree build sources.jsonl \
  --allowed-licenses MIT,Apache-2.0
```

## Testing

### Tests failing locally

```bash
# Reinstall dev dependencies
pip install -e ".[dev]"

# Run tests with verbose output
python -m pytest tests/ -v --tb=short
```

### Coverage below 90%

Add tests for uncovered code:

```bash
python -m coverage report --fail-under=90
```

See [Testing Guide](../contributing/testing.md) for patterns.

## Performance

### Out of memory for large datasets

Stream process instead of loading all at once:

```python
with open("large.jsonl") as f:
    for line in f:
        record = json.loads(line)
        # Process one record at a time
```

### Build is slow

Check system resources:
- CPU: Use multi-core when available
- Memory: Stream processing for large files
- Disk: Ensure SSD if possible

## General Issues

### Can't find command

Ensure PeachTree is installed and in PATH:

```bash
which peachtree  # Linux/macOS
where peachtree  # Windows
```

### Cryptic error messages

Enable verbose logging:

```bash
peachtree --verbose build dataset.jsonl
```

## Getting Help

- [FAQ](faq.md) - Common questions
- [Documentation](../index.md) - Full guides
- [GitHub Issues](https://github.com/0ai-Cyberviser/PeachTree/issues) - Bug reports
- [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions) - Questions
