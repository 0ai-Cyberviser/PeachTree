# Troubleshooting Playbook

Quick resolution guide for common PeachTree issues.

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'peachtree'`

**Cause:** PeachTree not installed in current Python environment

**Solutions:**

```bash
# Verify Python version
python --version  # Should be 3.10+

# Install from PyPI
pip install peachtree-ai

# Or install from source
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree
pip install -e .

# Verify installation
python -c "import peachtree; print(peachtree.__version__)"
```

### Issue: `Permission denied` when running `peachtree` command

**Cause:** Installation directory not in PATH

**Solutions:**

```bash
# Reinstall with user flag
pip install --user peachtree-ai

# Or use full path
python -m peachtree --help

# Add to PATH if needed
export PATH="$PATH:~/.local/bin"
```

## Dataset Building Issues

### Issue: Dataset build extremely slow

**Cause:** Large repositories, no parallelization, or resource constraints

**Solutions:**

```bash
# Monitor progress
peachtree build --input data/ --output dataset.jsonl --verbose

# Filter repository first
find /path/to/repo -name "*.md" -o -name "*.py" | head -1000 > filtered.txt

# Use smaller subset
peachtree build --input filtered.txt --output small-dataset.jsonl

# Check system resources
free -h  # Memory
df -h    # Disk space
```

### Issue: `FileNotFoundError: Source path not found`

**Cause:** Incorrect path to source repository

**Solutions:**

```bash
# Verify path exists
ls -la /path/to/repo

# Use absolute path
peachtree build --input /absolute/path/to/repo --output dataset.jsonl

# Check current directory
pwd
ls data/
```

### Issue: `ValueError: Invalid policy pack`

**Cause:** Malformed `.peachtree.yaml` or missing policy configuration

**Solutions:**

```yaml
# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('.peachtree.yaml'))"

# Check policy structure
cat .peachtree.yaml

# Example valid config
policies:
  - name: safety
    gates:
      - type: secret_filter
      - type: license_gate
```

## Policy & Safety Issues

### Issue: Records incorrectly flagged as unsafe

**Cause:** Overly aggressive safety gates or incorrect patterns

**Solutions:**

```bash
# Audit with verbose output
peachtree audit --dataset dataset.jsonl --verbose

# Review flagged records
peachtree audit --dataset dataset.jsonl | grep "flagged"

# Adjust safety gates in .peachtree.yaml
# Disable specific gates temporarily for testing
safety_gates:
  secret_filter: true
  license_gate: false  # Disable for testing
  content_filter: true
```

### Issue: All records rejected by policy pack

**Cause:** Policy conditions too restrictive

**Solutions:**

```bash
# Check policy compliance
peachtree policy --dataset dataset.jsonl --pack safety --verbose

# Review policy rules
cat policies/safety-policy.yaml

# Loosen restrictions
# Change: quality_threshold: 0.9
# To: quality_threshold: 0.7
```

## Command & CLI Issues

### Issue: `Command not found: peachtree`

**Cause:** PeachTree not in PATH or not installed

**Solutions:**

```bash
# Check installation
pip show peachtree-ai

# Use module syntax
python -m peachtree --version

# Check PATH
echo $PATH

# Reinstall
pip uninstall peachtree-ai
pip install peachtree-ai
```

### Issue: `Invalid argument` or unclear command syntax

**Cause:** Missing required arguments or wrong option names

**Solutions:**

```bash
# Show help for command
peachtree build --help

# Show all available commands
peachtree --help

# Check for typos
peachtree buld --input data/  # ❌ Wrong
peachtree build --input data/  # ✅ Correct
```

## Configuration Issues

### Issue: `.peachtree.yaml` not being read

**Cause:** File not in correct location or wrong permissions

**Solutions:**

```bash
# Verify file exists and is readable
ls -la .peachtree.yaml
cat .peachtree.yaml

# Check file permissions
chmod 644 .peachtree.yaml

# Use explicit config path
peachtree build --config /path/to/.peachtree.yaml --input data/ --output dataset.jsonl

# Verify YAML syntax
python -c "import yaml; print(yaml.safe_load(open('.peachtree.yaml')))"
```

## Docker Issues

### Issue: Docker image build fails

**Cause:** Missing dependencies or base image issues

**Solutions:**

```bash
# Clean build
docker build --no-cache -t peachtree:latest .

# Check Docker version
docker --version

# Verify Dockerfile
cat Dockerfile

# Build with verbose output
docker build -t peachtree:latest . --progress=plain
```

### Issue: Container exits immediately

**Cause:** Entrypoint or command fails

**Solutions:**

```bash
# Run interactively to see errors
docker run -it peachtree:latest bash

# Check container logs
docker logs <container-id>

# Verify image
docker inspect peachtree:latest
```

## Testing Issues

### Issue: Tests fail locally but pass in CI/CD

**Cause:** Environment differences, missing dependencies, or random failures

**Solutions:**

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests with verbose output
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_builder.py::test_specific -v

# Check Python version
python --version  # Should match CI/CD version

# Run in isolated environment
python -m venv test-env
source test-env/bin/activate
pip install -e ".[dev]"
python -m pytest tests/
```

### Issue: Coverage report not generated

**Cause:** Coverage package not installed or missing configuration

**Solutions:**

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
python -m pytest tests/ --cov=src/peachtree --cov-report=html

# Check coverage config
cat .coveragerc

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Documentation Issues

### Issue: Documentation website not building

**Cause:** mkdocs not installed, YAML errors, or missing files

**Solutions:**

```bash
# Install mkdocs and theme
pip install mkdocs mkdocs-material

# Validate mkdocs.yml syntax
python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"

# Check for missing files
grep -r "docs/" mkdocs.yml | grep -v "^#"

# Build with verbose output
mkdocs build -v

# Serve locally for testing
mkdocs serve  # Visit http://localhost:8000
```

### Issue: Links in documentation are broken

**Cause:** Incorrect file paths or moved files

**Solutions:**

```bash
# Check for broken links
grep -r "\[.*\](.*)" docs/ | grep -E "\.(md|html)"

# Verify file exists
ls docs/user-guide/cli.md

# Fix relative paths in links
# Change: [CLI](../../cli.md)
# To: [CLI](../cli.md)
```

## Performance Issues

### Issue: Memory usage too high

**Cause:** Large datasets, inefficient algorithms, or memory leaks

**Solutions:**

```bash
# Monitor memory
watch -n 1 free -h

# Run with limited memory
ulimit -m 2097152  # 2GB limit

# Process in chunks
peachtree build --input data/ --output dataset.jsonl --chunk-size 1000

# Profile memory usage
python -m memory_profiler src/peachtree/builder.py
```

### Issue: CPU usage maxed out

**Cause:** CPU-intensive operations (hashing, deduplication)

**Solutions:**

```bash
# Check number of CPUs
nproc

# Limit CPU threads (if supported)
export OMP_NUM_THREADS=4

# Run with reduced priority
nice -n 19 peachtree build --input data/ --output dataset.jsonl

# Use simpler deduplication method
# Change: dedup_method: semantic
# To: dedup_method: content_hash
```

## Data Quality Issues

### Issue: Dataset contains unexpected records

**Cause:** Filters not working, data corruption, or logic errors

**Solutions:**

```bash
# Inspect records
head -5 dataset.jsonl | python -m json.tool

# Count records by type
grep -c '"type"' dataset.jsonl

# Find problematic records
grep -n 'unexpected_value' dataset.jsonl

# Validate JSONL format
python -c "
import json
with open('dataset.jsonl') as f:
    for i, line in enumerate(f):
        json.loads(line)
print('Valid JSONL')
"

# Rebuild from source
rm dataset.jsonl
peachtree build --input data/ --output dataset.jsonl --verbose
```

## Getting Help

### Before reporting an issue:

1. **Check documentation** — https://0ai-cyberviser.github.io/PeachTree/
2. **Search existing issues** — GitHub Issues
3. **Check this guide** — You're reading it!
4. **Enable verbose logging** — Add `--verbose` or `--debug` flags

### Report an issue:

1. **Use bug report template** — `.github/ISSUE_TEMPLATE/bug_report.md`
2. **Include:**
   - Command that failed
   - Error message (full output)
   - Environment (OS, Python version)
   - `.peachtree.yaml` (without secrets)
   - Minimal reproduction steps

3. **Post to:**
   - [GitHub Issues](https://github.com/0ai-Cyberviser/PeachTree/issues)
   - [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)

### Security issues:

- **Email:** security@cyberviser.io
- **Don't** open public GitHub issue

---

**Last Updated:** 2026-04-27

See [FAQ](docs/resources/faq.md) for more questions.
