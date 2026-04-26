#!/bin/bash
# PeachTree Development Environment Setup Script

set -e

echo "=== PeachTree Development Setup ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Error: Python 3.10+ required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install development dependencies
echo "Installing PeachTree in development mode..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

# Run initial tests
echo "Running tests..."
python -m pytest tests/ -q

# Build documentation
echo "Building documentation..."
pip install mkdocs mkdocs-material
python -m mkdocs build

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Development environment is ready!"
echo ""
echo "Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. View docs: python -m mkdocs serve"
echo "3. Run tests: python -m pytest tests/ -v"
echo "4. Run linting: python -m ruff check src/"
echo "5. Run type checking: python -m mypy src/peachtree/ --strict"
echo ""
