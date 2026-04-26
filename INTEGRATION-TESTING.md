# Integration Testing Guide

Guide for testing PeachTree datasets and workflows end-to-end.

## Why Integration Testing?

- **Unit tests** verify individual functions
- **Integration tests** verify complete workflows
- **End-to-end tests** verify production scenarios

PeachTree needs all three to ensure reliability.

## Setting Up Integration Tests

### Test Data Preparation

```bash
# Create test repository structure
mkdir -p test-repo/{src,docs,tests}

# Add sample files
echo "def hello(): pass" > test-repo/src/main.py
echo "# Documentation" > test-repo/docs/readme.md
echo "def test_sample(): assert True" > test-repo/tests/test.py

# Initialize git (if needed)
cd test-repo && git init && git add . && git commit -m "initial"
cd ..
```

### Test Configuration

```bash
# Create test peachtree config
cat > test-config.yaml << 'EOF'
source:
  path: ./test-repo
  type: git

dataset:
  name: test-dataset
  version: 1.0.0

safety_gates:
  secret_filter: true
  license_gate: false  # Disabled for tests

deduplication:
  method: content_hash
  similarity_threshold: 0.95

quality:
  min_score: 0.5
EOF
```

## Basic Integration Test Examples

### Test 1: Simple Build Workflow

```python
# tests/integration/test_build_workflow.py
import json
import tempfile
from pathlib import Path
import pytest
from peachtree import PeachTree

def test_simple_build_workflow():
    """Test basic dataset build workflow."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        repo_path = Path(tmpdir) / "repo"
        repo_path.mkdir()
        (repo_path / "file.txt").write_text("Sample content")
        
        output_path = Path(tmpdir) / "dataset.jsonl"
        
        # Execute
        peachtree = PeachTree()
        peachtree.ingest(source=repo_path, output=repo_path / "data")
        peachtree.build(
            input_dir=repo_path / "data",
            output_path=output_path
        )
        
        # Verify
        assert output_path.exists(), "Output dataset not created"
        
        with open(output_path) as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) > 0, "No records in dataset"
        assert all("content" in r for r in records), "Missing content field"
```

### Test 2: Policy Pack Validation

```python
def test_policy_pack_compliance():
    """Test dataset complies with policy pack."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Build dataset
        dataset_path = Path(tmpdir) / "dataset.jsonl"
        # ... build dataset ...
        
        # Apply policy pack
        peachtree = PeachTree()
        results = peachtree.evaluate_policy(
            dataset_path=dataset_path,
            policy_name="safety"
        )
        
        # Verify
        assert results["passed"], "Policy evaluation failed"
        assert results["violations"] == 0, "Found policy violations"
        assert results["quality_score"] >= 0.7, "Quality too low"
```

### Test 3: Deduplication Effectiveness

```python
def test_deduplication_reduces_duplicates():
    """Test that deduplication removes duplicate records."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "dataset.jsonl"
        dedup_path = Path(tmpdir) / "dedup.jsonl"
        
        # Create dataset with duplicates
        records = [
            {"id": "1", "content": "A"},
            {"id": "2", "content": "A"},  # Duplicate
            {"id": "3", "content": "B"},
            {"id": "4", "content": "B"},  # Duplicate
        ]
        
        with open(dataset_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
        
        # Deduplicate
        peachtree = PeachTree()
        peachtree.dedup(
            input_path=dataset_path,
            output_path=dedup_path,
            method="content_hash"
        )
        
        # Verify
        with open(dedup_path) as f:
            dedup_records = [json.loads(line) for line in f]
        
        original_count = len(records)
        dedup_count = len(dedup_records)
        
        assert dedup_count < original_count, "No deduplication occurred"
        assert dedup_count == 2, "Expected 2 unique records"
```

### Test 4: End-to-End Workflow

```python
def test_end_to_end_workflow():
    """Test complete dataset pipeline from source to release."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Step 1: Create test repository
        repo_path = tmpdir / "repo"
        repo_path.mkdir()
        (repo_path / "code.py").write_text("# Code\ndef func(): pass")
        (repo_path / "docs.md").write_text("# Documentation")
        
        # Step 2: Ingest
        peachtree = PeachTree()
        peachtree.ingest(source=repo_path, output=tmpdir / "ingested")
        
        # Step 3: Build
        dataset_path = tmpdir / "dataset.jsonl"
        peachtree.build(
            input_dir=tmpdir / "ingested",
            output_path=dataset_path
        )
        
        # Step 4: Audit
        audit_results = peachtree.audit(dataset_path=dataset_path)
        assert audit_results["status"] == "passed"
        
        # Step 5: Deduplicate
        dedup_path = tmpdir / "dedup.jsonl"
        peachtree.dedup(input_path=dataset_path, output_path=dedup_path)
        
        # Step 6: Validate policy
        policy_results = peachtree.evaluate_policy(
            dataset_path=dedup_path,
            policy_name="safety"
        )
        assert policy_results["passed"]
        
        # Step 7: Create release
        release_path = tmpdir / "release"
        peachtree.create_release(
            dataset_path=dedup_path,
            output_dir=release_path
        )
        
        # Verify final artifacts
        assert (release_path / "dataset.jsonl").exists()
        assert (release_path / "manifest.json").exists()
        assert (release_path / "model-card.md").exists()
        assert (release_path / "sbom.json").exists()
```

## Advanced Integration Tests

### Test 5: Large Dataset Handling

```python
def test_large_dataset_processing():
    """Test handling of large datasets without memory issues."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create large dataset (1M records)
        dataset_path = tmpdir / "large.jsonl"
        with open(dataset_path, "w") as f:
            for i in range(1_000_000):
                record = {
                    "id": f"record-{i}",
                    "content": f"Content {i}" * 10
                }
                f.write(json.dumps(record) + "\n")
        
        # Process large dataset
        peachtree = PeachTree()
        
        # Should handle without memory errors
        audit_results = peachtree.audit(
            dataset_path=dataset_path,
            chunk_size=10000  # Process in chunks
        )
        
        assert audit_results["status"] == "passed"
        assert audit_results["total_records"] == 1_000_000
```

### Test 6: Multi-Repository Dataset

```python
def test_multi_repository_dataset():
    """Test building dataset from multiple repositories."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        peachtree = PeachTree()
        
        # Create multiple test repositories
        repos = []
        for i in range(3):
            repo = tmpdir / f"repo-{i}"
            repo.mkdir()
            (repo / f"code-{i}.py").write_text(f"# Repo {i}")
            repos.append(repo)
        
        # Ingest all repositories
        for repo in repos:
            peachtree.ingest(source=repo, output=tmpdir / "ingested" / repo.name)
        
        # Build combined dataset
        dataset_path = tmpdir / "combined.jsonl"
        peachtree.build(
            input_dir=tmpdir / "ingested",
            output_path=dataset_path
        )
        
        # Verify all repositories represented
        with open(dataset_path) as f:
            records = [json.loads(line) for line in f]
        
        sources = set(r["source_repo"] for r in records)
        assert len(sources) >= 3, "Not all repositories represented"
```

## Performance Integration Tests

### Test 7: Build Performance Benchmark

```python
def test_build_performance():
    """Benchmark dataset build performance."""
    import time
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test data
        repo = tmpdir / "repo"
        repo.mkdir()
        for i in range(1000):
            (repo / f"file-{i}.py").write_text(f"# File {i}\ncode here")
        
        peachtree = PeachTree()
        
        # Benchmark ingest
        start = time.time()
        peachtree.ingest(source=repo, output=tmpdir / "ingested")
        ingest_time = time.time() - start
        
        # Benchmark build
        start = time.time()
        peachtree.build(
            input_dir=tmpdir / "ingested",
            output_path=tmpdir / "dataset.jsonl"
        )
        build_time = time.time() - start
        
        # Verify performance
        assert ingest_time < 10, "Ingest too slow"
        assert build_time < 30, "Build too slow"
        
        print(f"Ingest: {ingest_time:.2f}s, Build: {build_time:.2f}s")
```

## Running Integration Tests

### Using pytest

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test
pytest tests/integration/test_build_workflow.py::test_simple_build_workflow

# Run with verbose output
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src/peachtree

# Run with performance markers
pytest tests/integration/ -m performance
```

### Using GitHub Actions

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v
```

## Best Practices

### DO ✅

- Use temporary directories for test data
- Clean up resources after tests
- Test both success and failure cases
- Include performance benchmarks
- Document test scenarios
- Use fixtures for common setup
- Test with realistic data sizes

### DON'T ❌

- Use actual production data
- Leave test files in repository
- Hardcode paths
- Skip error case tests
- Commit large test data
- Run integration tests in isolation
- Test implementation details

## Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/integration/ -vv

# Show print statements
pytest tests/integration/ -s

# Stop on first failure
pytest tests/integration/ -x

# Run last failed tests
pytest tests/integration/ --lf

# Show local variables on failure
pytest tests/integration/ -l

# Generate HTML report
pytest tests/integration/ --html=report.html
```

---

**Last Updated:** 2026-04-27

See [DEVELOPMENT.md](DEVELOPMENT.md) for testing setup and guidelines.
