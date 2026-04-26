# PeachTree Development Guide

Complete guide for setting up and developing PeachTree locally.

## Quick Start (5 minutes)

### Option 1: Automated Setup

```bash
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

### Option 2: Manual Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Option 3: Docker

```bash
# Development container
docker-compose run --rm peachtree-dev bash

# Run tests
docker-compose run --rm peachtree-test

# View docs locally
docker-compose up peachtree-docs
# Visit http://localhost:8000
```

## Development Workflow

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_builder.py -v

# Run with coverage
python -m pytest tests/ --cov=src/peachtree --cov-report=html

# Run only fast tests
python -m pytest -m "not slow" -v
```

### Code Quality Checks

```bash
# Linting
python -m ruff check src/ tests/

# Auto-fix linting issues
python -m ruff check --fix src/ tests/

# Type checking
python -m mypy src/peachtree/ --strict

# Full quality check
python -m ruff check --fix src/ tests/
python -m mypy src/peachtree/ --strict
python -m pytest tests/ --cov=src/peachtree
```

### Documentation

```bash
# Build documentation
python -m mkdocs build

# Serve documentation locally
python -m mkdocs serve
# Visit http://localhost:8000

# Deploy documentation
python -m mkdocs gh-deploy
```

## Pre-Commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install hooks (already done by setup script)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

Hooks include:
- Trailing whitespace cleanup
- YAML validation
- Large file detection
- Ruff linting and formatting
- MyPy type checking
- Import cleanup

## Creating a Feature

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit files
vim src/peachtree/feature.py

# Add tests
vim tests/test_feature.py

# Run quality checks
python -m ruff check --fix src/ tests/
python -m mypy src/peachtree/ --strict
python -m pytest tests/ --cov=src/peachtree
```

### 3. Update Documentation

```bash
# Add feature docs
vim docs/user-guide/feature.md

# Build and preview
python -m mkdocs serve
```

### 4. Commit Changes

```bash
# Pre-commit hooks will run automatically
git add -A
git commit -m "feat: add new feature

- Specific change 1
- Specific change 2

See #123"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Project Structure

```
peachtree/
├── src/peachtree/        # Main source code
│   ├── cli.py            # CLI entry point
│   ├── builder.py        # DatasetBuilder
│   ├── safety.py         # SafetyGate
│   ├── policy_packs.py   # Policy evaluation
│   └── ...               # Other modules
├── tests/                # Test suite
│   ├── test_builder.py
│   ├── test_safety.py
│   └── ...
├── docs/                 # Documentation
│   ├── index.md
│   ├── getting-started/
│   ├── user-guide/
│   ├── architecture/
│   └── ...
├── scripts/              # Utility scripts
├── pyproject.toml        # Project metadata
├── mkdocs.yml            # Documentation config
├── Dockerfile            # Container image
└── docker-compose.yml    # Docker development
```

## Debugging

### Enable Verbose Logging

```bash
peachtree --verbose build dataset.jsonl
```

### Debug with Python

```python
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### Inspect Variables in Tests

```python
def test_something(tmp_path):
    result = my_function()
    print(f"Result: {result}")  # Output visible with pytest -s
    assert result == expected
```

Run with: `python -m pytest tests/test_file.py::test_something -s`

## Performance Profiling

```bash
# Profile with cProfile
python -m cProfile -s cumulative -m peachtree build dataset.jsonl > profile.txt

# View results
less profile.txt
```

## Releasing

### Create Release

```bash
# Update version in pyproject.toml
# Create tag
git tag v0.10.0
git push origin v0.10.0

# GitHub Actions will:
# 1. Run tests
# 2. Build distribution
# 3. Create GitHub release
# 4. Deploy to PyPI
# 5. Deploy documentation
```

## Getting Help

- **Tests failing?** Check [Troubleshooting](../docs/resources/troubleshooting.md)
- **Need help?** Check [FAQ](../docs/resources/faq.md)
- **Found a bug?** Open a [GitHub Issue](https://github.com/0ai-Cyberviser/PeachTree/issues)
- **Have a question?** Use [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)

## Advanced Topics

### Running CI/CD Locally

```bash
# Simulate GitHub Actions locally
pip install act
act push  # Run on push events
act pull_request  # Run on PR events
```

### Building Distribution

```bash
pip install build
python -m build

# Outputs:
# dist/peachtree_ai-0.9.0-py3-none-any.whl
# dist/peachtree-ai-0.9.0.tar.gz
```

### Testing Against Multiple Python Versions

```bash
pip install tox

# Test against 3.10, 3.11, 3.12
tox
```

## IDE Setup

### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Mark `src/` as Sources Root
2. Mark `tests/` as Test Sources Root
3. Set Python interpreter to `venv/bin/python`
4. Enable Ruff integration
5. Enable MyPy integration

## Contributing Checklist

Before submitting a PR:

- [ ] Code follows project style (ruff passes)
- [ ] Type hints complete (mypy passes)
- [ ] Tests added and passing (pytest passes, 90%+ coverage)
- [ ] Documentation updated
- [ ] CHANGELOG entry added
- [ ] Commit messages clear and descriptive
- [ ] Branch is up-to-date with main

---

**Happy coding! 🍑**
