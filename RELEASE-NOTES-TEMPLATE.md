# Release Notes Template

Use this template when creating GitHub releases.

---

## v0.10.0 - [Release Date]

### 🎉 Highlights

Brief summary of the most important changes in this release.

### ✨ New Features

- **Feature 1** — Description of what it does and why it matters
- **Feature 2** — Key capability added
- **Feature 3** — Integration or workflow improvement

### 🐛 Bug Fixes

- **Fix for Issue #123** — Description of the bug and how it's fixed
- **Performance fix** — What was slow and how we improved it
- **Error handling** — What error case was addressed

### 📚 Documentation

- Added guide for new feature
- Updated API reference
- Improved troubleshooting section

### 🔧 Internal Changes

- Refactored internal modules
- Improved test coverage
- Updated dependencies

### ⚠️ Breaking Changes

If there are breaking changes, list them with migration guide:

```bash
# Before
peachtree build --old-option value

# After
peachtree build --new-option value
```

### 📦 Dependency Updates

- `pydantic` 2.0 → 2.1
- `pytest` 7.4 → 8.0

### 🚀 Performance

- Dataset building **2x faster** for large repositories
- Memory usage **reduced by 30%**
- CLI startup time **improved by 500ms**

### 🔒 Security

- Fixed potential secret leak in logs
- Updated vulnerable dependencies
- Added secret scanning to CI/CD

### 📋 Contributors

Thanks to all contributors who made this release possible:

- @contributor1
- @contributor2
- And X more...

### 📝 Changelog

Full list of changes in [CHANGELOG.md](CHANGELOG.md).

### 🔗 Links

- [GitHub Release](https://github.com/0ai-Cyberviser/PeachTree/releases/tag/v0.10.0)
- [PyPI Package](https://pypi.org/project/peachtree-ai/0.10.0/)
- [Documentation](https://0ai-cyberviser.github.io/PeachTree/)
- [Upgrade Guide](docs/getting-started/upgrade.md)

### 🙏 Support

- Questions? → [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)
- Issues? → [GitHub Issues](https://github.com/0ai-Cyberviser/PeachTree/issues)
- Security? → security@cyberviser.io

---

## Template Sections

### Required

- **Highlights** — What's important in this release
- **New Features** — What's new
- **Bug Fixes** — What's fixed
- **Contributors** — Who helped

### Recommended

- **Breaking Changes** — If any exist
- **Performance** — If significantly improved
- **Security** — If security updates included
- **Links** — Relevant documentation and tools

### Optional

- **Migration Guide** — For breaking changes
- **Statistics** — Download counts, stars, etc.
- **Roadmap** — What's coming next
- **Acknowledgments** — Special thanks

## Creating a Release

1. **Draft Release**
   - Go to [Releases](https://github.com/0ai-Cyberviser/PeachTree/releases)
   - Click "Draft a new release"
   - Tag version: `v0.10.0`
   - Target: `main`

2. **Write Release Notes**
   - Use template above
   - Check for accuracy
   - Verify links work

3. **Attach Artifacts**
   - SBOM file
   - Signatures
   - Release bundle

4. **Publish**
   - Mark as latest (if applicable)
   - Note if pre-release
   - Click "Publish release"

5. **Announce**
   - Post to GitHub Discussions
   - Update website if needed
   - Share with community

## Automated Release Process

GitHub Actions automatically:

1. Runs tests
2. Builds packages
3. Creates GitHub release
4. Publishes to PyPI
5. Deploys documentation

See `.github/workflows/release.yml` for details.

---

**Last Updated:** 2026-04-27

See [CHANGELOG.md](CHANGELOG.md) for historical releases.
