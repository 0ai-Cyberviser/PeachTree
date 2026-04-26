# Changelog

All notable changes to the PeachTree project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation website with Material Design theme
- GitHub Actions CI/CD workflows for testing, deployment, and releases
- Docker support with Dockerfile and docker-compose
- Pre-commit hooks for code quality enforcement
- Automated development environment setup
- Deployment guide for GitHub Pages and releases

### Changed
- Fixed 4 ruff linting violations (unused imports)
- Fixed mypy type variance issue in registry.py
- Improved documentation structure and organization

### Fixed
- Removed minify plugin from mkdocs.yml (dependency issue)
- Type checking errors in DatasetRegistryBuilder

## [0.9.0] - 2026-04-26

### Added
- Initial comprehensive documentation (42 markdown files)
- Static website generation with mkdocs (43 HTML pages)
- CLI reference documentation (28+ commands)
- Architecture documentation with diagrams
- API reference for core modules
- Ecosystem integration guides (Hancock, PeachFuzz, CyberViser)
- Contributing guidelines and development guide
- FAQ with 20+ common questions
- Troubleshooting guide

### Features
- Recursive learning-tree dataset engine
- SafetyGate for secrets and license filtering
- Policy packs for compliance validation
- JSONL dataset format with full provenance
- Dataset deduplication and quality scoring
- Release bundle generation with SBOM
- Trainer handoff manifests for model training
- Registry and artifact management

### Quality
- 129 unit tests with 91% code coverage
- Type checking with mypy (0 errors)
- Linting with ruff (0 violations)
- Pre-commit hooks for continuous quality
- Automated testing in CI/CD

### Infrastructure
- GitHub Actions workflows for CI/CD
- Docker containerization support
- Automated development setup
- Pre-commit hooks configuration
- Documentation auto-deployment

## [0.8.0] - Previous Release

Refer to git history for details on previous releases.

---

## Release Process

1. **Update Version**
   ```bash
   # In pyproject.toml
   version = "0.10.0"
   ```

2. **Update Changelog**
   - Add new version header with date
   - Document changes in appropriate sections

3. **Create Release**
   ```bash
   git tag v0.10.0
   git push origin v0.10.0
   ```

4. **Monitor Deployment**
   - GitHub Actions will automatically run
   - Release artifacts will be created
   - Documentation will be deployed
   - Package will be published to PyPI

## Semantic Versioning

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.10.0): Features, non-breaking
- **PATCH** (0.9.1): Bug fixes, urgent fixes

## Future Plans

- [ ] LoRA fine-tuning support
- [ ] Dataset versioning system
- [ ] Web UI for dataset management
- [ ] Integration with Weights & Biases
- [ ] Advanced deduplication algorithms
- [ ] Performance benchmarking
- [ ] Extended ecosystem integrations
