# Installation & Setup

## System Requirements

- **Python**: 3.10 or later
- **OS**: Linux, macOS, or Windows
- **Disk**: Minimum 1GB for dependencies and datasets

## Installation

### Via pip (Recommended)

```bash
pip install peachtree-ai
```

### From Source

```bash
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree
pip install -e .
```

### Development Installation

For contributing or local development:

```bash
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree
pip install -e ".[dev]"
```

This installs development dependencies:
- `pytest` and `pytest-cov` for testing
- `ruff` for linting
- `mypy` for type checking

## Verification

Verify installation:

```bash
peachtree --version
peachtree --help
```

## Configuration

### Environment Variables

- `PEACHTREE_DATA_DIR`: Default directory for dataset outputs (default: `./data`)
- `PEACHTREE_LOG_LEVEL`: Logging level (default: `INFO`)
- `PEACHTREE_CACHE_DIR`: Cache directory for temporary files (default: `/tmp/peachtree`)

### Configuration File

Create a `.peachtreerc` file in your project root:

```yaml
data_dir: ./data
log_level: INFO
safety_gates:
  filter_secrets: true
  check_licenses: true
  allowed_licenses:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
```

## Getting Help

### CLI Help

```bash
# Main help
peachtree --help

# Command-specific help
peachtree build --help
```

### Documentation

- [Quick Start Guide](quickstart.md)
- [CLI Reference](../user-guide/cli.md)
- [Architecture Guide](../architecture/design.md)

## Troubleshooting

### Import Errors

If you encounter import errors:

```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Verify installation
python -c "from peachtree import cli; print(cli.__version__)"
```

### Permission Errors

If you see permission errors during installation:

```bash
# Use --break-system-packages (Linux/macOS)
pip install --break-system-packages peachtree-ai

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install peachtree-ai
```

### Memory Issues

For large datasets, increase Python's memory:

```bash
python -m peachtree build large-dataset.jsonl --memory-limit 8g
```

## Next Steps

- [Quick Start Tutorial](quickstart.md)
- [CLI Commands Reference](../user-guide/cli.md)
- [Building Your First Dataset](../user-guide/building.md)
