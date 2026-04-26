# Status Badges

Repository status and quality badges for PeachTree.

## Build & CI/CD

- [![Tests](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml) — Automated test suite
- [![Docs](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml) — Documentation building
- [![Release](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/release.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/release.yml) — Release automation
- [![Pages](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/pages.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/pages.yml) — GitHub Pages deployment

## Code Quality

- ![Tests: 129](https://img.shields.io/badge/tests-129-brightgreen) — Unit test count
- ![Coverage: 91%](https://img.shields.io/badge/coverage-91%25-brightgreen) — Code coverage
- ![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) — Python version requirement
- ![Status: Stable](https://img.shields.io/badge/status-stable-brightgreen) — Project stability

## Package & Distribution

- [![PyPI](https://img.shields.io/pypi/v/peachtree-ai?color=blue)](https://pypi.org/project/peachtree-ai/) — Package version
- [![PyPI Downloads](https://img.shields.io/pypi/dm/peachtree-ai?color=blue)](https://pypi.org/project/peachtree-ai/) — Download statistics
- [![Docker](https://img.shields.io/docker/v/0aicyberviser/peachtree?color=blue)](https://hub.docker.com/r/0aicyberviser/peachtree) — Docker image version

## Security & Compliance

- [![Security: Enabled](https://img.shields.io/badge/security-enabled-brightgreen)](SECURITY.md) — Security scanning
- [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE) — License type
- [![Dependabot: Active](https://img.shields.io/badge/dependabot-active-brightgreen)](https://github.com/0ai-Cyberviser/PeachTree/security/dependabot) — Dependency updates

## Documentation & Community

- [![Docs](https://img.shields.io/badge/docs-available-brightgreen)](https://0ai-cyberviser.github.io/PeachTree/) — Online documentation
- [![Issues](https://img.shields.io/github/issues/0ai-Cyberviser/PeachTree?color=blue)](https://github.com/0ai-Cyberviser/PeachTree/issues) — Issue tracking
- [![Discussions](https://img.shields.io/github/discussions/0ai-Cyberviser/PeachTree?color=blue)](https://github.com/0ai-Cyberviser/PeachTree/discussions) — Community discussions

## Markdown Snippets

### Quick Status Row

```markdown
[![Tests](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml)
[![Docs](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml)
[![Codecov](https://codecov.io/gh/0ai-Cyberviser/PeachTree/branch/main/graph/badge.svg)](https://codecov.io/gh/0ai-Cyberviser/PeachTree)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
```

### Detailed Status Table

```markdown
| Metric | Badge | Status |
|--------|-------|--------|
| Tests | [![Tests](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/tests.yml) | Passing |
| Coverage | ![91%](https://img.shields.io/badge/coverage-91%25-brightgreen) | High |
| Docs | [![Docs](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml/badge.svg)](https://github.com/0ai-Cyberviser/PeachTree/actions/workflows/docs.yml) | Built |
| Version | ![0.9.0](https://img.shields.io/badge/version-0.9.0-blue) | Stable |
```

## External Services

### Codecov

Track code coverage over time:

```markdown
[![codecov](https://codecov.io/gh/0ai-Cyberviser/PeachTree/branch/main/graph/badge.svg)](https://codecov.io/gh/0ai-Cyberviser/PeachTree)
```

Setup:
1. Connect GitHub repository to [codecov.io](https://codecov.io)
2. Add `CODECOV_TOKEN` to GitHub repository secrets
3. Upload coverage reports from CI/CD

### ReadTheDocs

Alternate documentation hosting:

```markdown
[![ReadTheDocs](https://readthedocs.org/projects/peachtree/badge/?version=latest)](https://peachtree.readthedocs.io/)
```

### Shields.io

Generate custom badges:

```markdown
![Custom Badge](https://img.shields.io/badge/custom-value-blue)
```

Parameters:
- `label` — Left side text
- `message` — Right side text
- `color` — Color (blue, green, red, yellow, etc.)

## Badge Colors

- **brightgreen** — Passing, good status
- **green** — Success, complete
- **yellowgreen** — Mostly passing
- **yellow** — Warning, needs attention
- **orange** — Important, needs action
- **red** — Failure, error
- **lightgrey** — Inactive, unknown
- **blue** — Info, general status

## Adding Badges to README

Place badges near the top of README.md, typically after the project title:

```markdown
# PeachTree

[![Tests](badge-url)](link-to-tests)
[![Docs](badge-url)](link-to-docs)
[![License](badge-url)](LICENSE)

**Your project description here...**
```

## Maintaining Badges

- **Keep URLs updated** — When CI/CD URLs change, update badge URLs
- **Remove broken badges** — Delete if service discontinues
- **Use consistent styling** — Match colors and text across all badges
- **Document badge meanings** — Explain what each badge represents
- **Test badge URLs** — Verify they render correctly on GitHub

---

**Last Updated:** 2026-04-27

See [BADGES.md](BADGES.md) for badge documentation and snippets.
