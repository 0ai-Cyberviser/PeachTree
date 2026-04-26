# Contributing to PeachTree

Thank you for your interest in contributing to PeachTree! This guide explains how to contribute code, documentation, or bug reports.

## Ways to Contribute

1. **Report bugs** — Use [Bug Report](/.github/ISSUE_TEMPLATE/bug_report.md)
2. **Request features** — Use [Feature Request](/.github/ISSUE_TEMPLATE/feature_request.md)
3. **Fix bugs** — Submit PRs for open issues
4. **Add features** — Implement requested features
5. **Improve documentation** — Enhance docs, guides, examples
6. **Review PRs** — Provide constructive feedback
7. **Improve tests** — Increase coverage or add edge cases

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Assume good intentions
- Report violations to maintainers

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR-USERNAME/PeachTree.git
cd PeachTree
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
python -m pytest tests/
```

### 3. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

Branch naming conventions:
- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation
- `refactor/` — Code refactoring
- `test/` — Test improvements

## Development Workflow

### 1. Make Changes

Edit code and create tests:

```python
# Add tests in tests/
def test_my_feature():
    from peachtree import MyFeature
    result = MyFeature().run()
    assert result == expected
```

### 2. Check Quality

```bash
# Run tests
python -m pytest tests/ -v --cov=src/peachtree

# Check linting
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/

# Pre-commit hooks will run automatically on commit
```

### 3. Update Documentation

Add docs for new features:

```bash
# Edit or create markdown files in docs/
# Example: docs/user-guide/my-feature.md

# Build and preview docs
python -m mkdocs serve
# Visit http://localhost:8000
```

### 4. Commit Changes

Write clear commit messages:

```bash
# Good commit messages
git commit -m "feat: add dataset deduplication support

- Implement content-hash deduplication method
- Add semantic deduplication with embeddings
- Add fuzzy matching for similar records
- Closes #123"

# Format: type: brief description
# Types: feat, fix, docs, refactor, test, chore
```

### 5. Push and Create PR

```bash
git push origin feature/my-feature
# Create PR on GitHub
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass: `python -m pytest tests/`
- [ ] Code is formatted: `ruff format src/`
- [ ] Linting passes: `ruff check src/`
- [ ] Type checking passes: `mypy src/`
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages are clear

### PR Description

Use the [Pull Request Template](/.github/pull_request_template.md):

- Describe changes clearly
- Reference issue (Closes #123)
- List breaking changes
- Provide examples if relevant

### Review Process

1. **Automated checks** — CI/CD runs tests, linting, coverage
2. **Code review** — Maintainers review for correctness and quality
3. **Feedback** — Address review comments
4. **Approval** — PR approved and ready to merge
5. **Merge** — Squash and merge to main branch

## Code Standards

### Style

Follow [PEP 8](https://pep8.org/) with ruff enforcement:

```python
# Good
def build_dataset(source_path: str, output_path: str) -> Dataset:
    """Build a dataset from source path."""
    records = ingest_records(source_path)
    cleaned = apply_safety_gates(records)
    return Dataset(cleaned)

# Bad
def build(s, o):
    r = ingest_records(s)
    c = apply_safety_gates(r)
    return Dataset(c)
```

### Type Hints

Always include type hints:

```python
from typing import Optional, List
from pathlib import Path

def process_files(
    paths: List[Path],
    filter_fn: Optional[Callable[[str], bool]] = None,
) -> int:
    """Process files and return count."""
    count = 0
    for path in paths:
        if filter_fn is None or filter_fn(path.name):
            count += 1
    return count
```

### Tests

Write tests for new code:

```python
import pytest
from peachtree import MyFeature

class TestMyFeature:
    def test_basic_usage(self):
        feature = MyFeature()
        result = feature.run()
        assert result is not None
    
    def test_with_options(self):
        feature = MyFeature(option=True)
        result = feature.run()
        assert result.success

    def test_error_handling(self):
        with pytest.raises(ValueError):
            MyFeature().invalid_method()
```

### Documentation

Document public APIs:

```python
def build_dataset(source: str, policy: Optional[PolicyPack] = None) -> Dataset:
    """
    Build a JSONL dataset from source repository.
    
    This function:
    1. Ingests source files
    2. Applies safety gates
    3. Deduplicates records
    4. Applies policy pack if provided
    
    Args:
        source: Path to source repository
        policy: Optional policy pack for filtering
    
    Returns:
        Dataset object with JSONL records
    
    Raises:
        FileNotFoundError: If source path doesn't exist
        ValueError: If policy pack is invalid
    
    Example:
        >>> dataset = build_dataset("/path/to/repo")
        >>> dataset.save("output.jsonl")
    """
    ...
```

## Issue Guidelines

### Reporting Bugs

Use [Bug Report Template](/.github/ISSUE_TEMPLATE/bug_report.md):

1. Search for existing issues first
2. Use the template provided
3. Include reproduction steps
4. Provide environment details
5. Remove sensitive data

### Requesting Features

Use [Feature Request Template](/.github/ISSUE_TEMPLATE/feature_request.md):

1. Describe the use case clearly
2. Explain why it's needed
3. Provide examples or pseudocode
4. Consider alternatives

### Dataset/Config Issues

Use [Dataset Issue Template](/.github/ISSUE_TEMPLATE/dataset_issue.md):

1. Share configuration (without secrets)
2. Include audit report
3. Describe reproducible steps
4. Share error messages

## Security

- **Report vulnerabilities privately** — security@cyberviser.io
- **Never commit secrets** — Use `.gitignore` and environment variables
- **Use pre-commit hooks** — Catch secrets before commit

## Questions?

- **Documentation** — https://0ai-cyberviser.github.io/PeachTree/
- **Discussions** — GitHub Discussions
- **Issues** — GitHub Issues
- **Email** — contact@cyberviser.io

## Recognition

Contributors are recognized in:
- Git commit history
- GitHub contributors page
- Release notes
- Project README (for significant contributions)

---

**Last Updated:** 2026-04-27

Thank you for contributing to PeachTree! 🍑
