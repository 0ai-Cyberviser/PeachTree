# Contributing to PeachTree

We welcome contributions! This guide helps you get started.

## Code of Conduct

Be respectful, inclusive, and collaborative. We're building a safe, professional community.

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR-USERNAME/PeachTree.git
cd PeachTree
```

### 2. Create Development Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Code Standards

- **Python 3.10+** - Use modern syntax and type hints
- **Type Hints**: Use `mypy --strict` for all new code
- **Linting**: Run `ruff check` and fix issues
- **Tests**: 90%+ coverage required (currently 91%)
- **Documentation**: Update docs for new features

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/peachtree --cov-report=html

# Run specific test file
python -m pytest tests/test_builder.py -v

# Run with markers
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

# Coverage
python -m coverage run -m pytest
python -m coverage report
```

### Before Committing

```bash
# Run full quality check
python -m ruff check --fix src/ tests/
python -m mypy src/peachtree/ --strict
python -m pytest tests/ --cov=src/peachtree

# Verify documentation builds
python -m mkdocs build
```

## Making Changes

### Adding a Feature

1. **Plan**: Discuss in an issue first
2. **Branch**: Create feature branch
3. **Code**: Implement with tests
4. **Test**: Ensure 90%+ coverage
5. **Document**: Update README/docs
6. **PR**: Submit for review

### File Structure

```
src/peachtree/
├── feature_name.py      # Implementation
├── __init__.py          # Export public API
tests/
├── test_feature_name.py # Unit tests
docs/
├── feature_name.md      # Documentation
```

### Testing Patterns

**Fixture-based tests:**

```python
def test_builder_creates_record(tmp_path):
    """Test that DatasetBuilder creates valid records."""
    builder = DatasetBuilder()
    source = SourceDocument(
        id="test-1",
        content="test content",
        source_repo="test/repo",
        source_path="test.py",
        source_digest="abc123"
    )
    record = builder._build_record(source)
    assert record.id == "sha256-..."
    assert record.source_repo == "test/repo"
```

**Provenance validation:**

```python
def test_provenance_preserved():
    """Verify provenance metadata in output."""
    dataset = builder.build_dataset(sources)
    for record in dataset:
        assert record.source_repo
        assert record.source_path
        assert record.source_digest
```

**CLI integration tests:**

```python
def test_cli_build_command(tmp_path):
    """Test full CLI build workflow."""
    result = runner.invoke(cli, [
        "build",
        "sources.jsonl",
        "--output", str(tmp_path / "output.jsonl")
    ])
    assert result.exit_code == 0
```

### Documentation

Write documentation for:
- Public APIs (docstrings)
- CLI commands (help text)
- Features (user guide)
- Examples (getting started)

**Docstring format:**

```python
def build_dataset(self, sources: list[SourceDocument]) -> list[DatasetRecord]:
    """Build training dataset from source documents.
    
    Args:
        sources: List of SourceDocument records to process
        
    Returns:
        List of DatasetRecord with full provenance
        
    Raises:
        ValueError: If sources are invalid or empty
        
    Example:
        >>> builder = DatasetBuilder()
        >>> dataset = builder.build_dataset(sources)
        >>> len(dataset) > 0
        True
    """
```

## Commit Messages

Use clear, descriptive messages:

```
feat: add semantic deduplication method
  - Implement similarity-based duplicate detection
  - Add configurable threshold parameter
  - Add tests for edge cases

fix: handle missing provenance in legacy records
  - Add validation for source_repo field
  - Set sensible defaults for missing metadata
  - Update migration guide

docs: expand CLI reference with examples
  - Add example workflows
  - Document all 28 commands
  - Add troubleshooting section

chore: upgrade dependencies
  - pytest 7.0 → 7.4
  - mkdocs 1.4 → 1.5
```

## Pull Request Process

### Before Submitting

1. **Rebase on main**: `git rebase origin/main`
2. **Run tests**: `pytest tests/ -v`
3. **Check coverage**: `coverage report --fail-under=90`
4. **Lint**: `ruff check --fix src/ tests/`
5. **Type check**: `mypy src/peachtree/ --strict`
6. **Build docs**: `mkdocs build`

### PR Description

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123

## Changes
- Specific change 1
- Specific change 2
- Specific change 3

## Testing
- Added test cases for new functionality
- Verified existing tests pass
- Tested with large datasets (>10k records)

## Documentation
- Updated README.md
- Added CLI examples
- Updated architecture docs

## Checklist
- [x] Tests pass locally
- [x] Coverage >= 90%
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] Documentation updated
- [x] Commit messages clear
```

### Review Process

1. **Automated checks**: Tests, linting, coverage
2. **Code review**: 1-2 maintainers review
3. **Feedback**: Address review comments
4. **Approval**: Merge when approved
5. **Release**: Included in next version

## Project Governance

### Maintainers

Core team reviews PRs and merges releases:
- Decision authority on architecture
- Final approval for merges
- Release coordination

### Issue Triage

- **bug**: Something broken
- **feature**: New functionality
- **enhancement**: Improvement to existing feature
- **documentation**: Docs/guides
- **question**: User questions

### Release Schedule

- **Patch** (0.9.1): Bug fixes, urgent fixes (~weekly)
- **Minor** (0.10.0): Features, non-breaking (~monthly)
- **Major** (1.0.0): Breaking changes (as needed)

## Areas for Contribution

- [ ] **Documentation**: Expand guides, add examples
- [ ] **Tests**: Improve coverage, edge cases
- [ ] **Performance**: Optimize deduplication
- [ ] **Features**: New policy packs, exporters
- [ ] **Bug fixes**: Issues labeled "help wanted"
- [ ] **Tools**: CI/CD improvements
- [ ] **Examples**: Real-world workflow samples

## Getting Help

- **Questions**: Use GitHub Discussions
- **Bugs**: Open GitHub Issue
- **Security**: See SECURITY.md
- **Chat**: Join Discord (see README)

## License

By contributing, you agree that your contributions will be licensed under PeachTree's MIT License.

---

**Thank you for contributing to PeachTree! 🍑**
