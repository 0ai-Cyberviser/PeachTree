# Repository Settings Guide

Configuration guide for maintaining the PeachTree GitHub repository.

## Access Control

### Branch Protection Rules

**Main Branch (`main`)**

1. Go to **Settings** → **Branches** → **Add rule**
2. Apply to: `main`

Configure:

- ✅ **Require pull request reviews before merging**
  - Required approving reviews: `1`
  - Dismiss stale reviews: ✓
  - Require review from code owners: ✓

- ✅ **Require status checks to pass before merging**
  - Required checks:
    - `tests (3.10)`, `tests (3.11)`, `tests (3.12)`
    - `ruff`
    - `mypy`
    - `docs`
    - `security`

- ✅ **Require branches to be up to date before merging**
- ✅ **Require code reviews**
- ✅ **Restrict who can push to matching branches**
  - Allow push by: Administrators only
- ✅ **Allow force pushes**: No
- ✅ **Allow deletions**: No

### Develop Branch (`develop`)

Similar rules but less strict:

- Require 1 review
- Require status checks
- Allow force pushes by admins

## Security

### Secret Scanning

1. Go to **Settings** → **Security & analysis**
2. Enable:
   - ✅ **Secret scanning** — Push protection enabled
   - ✅ **Dependabot alerts**
   - ✅ **Dependabot security updates**

### Dependabot Configuration

File: `.github/dependabot.yml`

- Python dependencies: Weekly updates
- GitHub Actions: Weekly updates
- Ignore major version bumps temporarily
- Open max 5-10 PRs at a time

### Code Scanning

1. Go to **Settings** → **Code security and analysis**
2. Enable:
   - ✅ **CodeQL analysis** — Default workflow
   - ✅ **Other analysis tools** (Semgrep, Bandit, etc.)

## Workflows & Automation

### GitHub Actions

Workflows in `.github/workflows/`:

- `tests.yml` — Multi-version Python testing
- `docs.yml` — Documentation deployment
- `release.yml` — PyPI release automation
- `pages.yml` — GitHub Pages deployment
- `security.yml` — Security scanning
- `coverage.yml` — Code coverage reporting
- `auto-changelog.yml` — Changelog generation
- `auto-label.yml` — Automatic labeling

### Environment Variables & Secrets

**Settings** → **Environments** → **Environment secrets**

Required secrets:

- `PYPI_API_TOKEN` — PyPI publishing token
- `CODECOV_TOKEN` — Codecov coverage reporting
- `GITHUB_TOKEN` — (Automatic, for actions)

**Repository secrets:**

- `SIGNING_KEY` — For signed releases (optional)

## Collaboration

### Issue Templates

Located in `.github/ISSUE_TEMPLATE/`:

- `bug_report.md` — Bug reporting
- `feature_request.md` — Feature requests
- `dataset_issue.md` — Dataset-specific issues

Configure in **Settings** → **Features** → check "Issues"

### Pull Request Template

File: `.github/pull_request_template.md`

Used automatically for all PRs.

### Discussion Categories

**Settings** → **Discussions**

Create categories:

- **General** — General questions
- **Announcements** — Release and updates
- **Ideas** — Feature suggestions
- **Show and Tell** — Community projects
- **Help** — Getting help
- **Dataset Sharing** — Shared datasets

## Community

### Code of Conduct

File: `CODE_OF_CONDUCT.md`

Report violations to: conduct@cyberviser.io

### Contributing Guide

File: `CONTRIBUTING-ADVANCED.md`

Explains:

- Development setup
- Testing requirements
- Code quality standards
- PR process

## Pages & Documentation

### GitHub Pages

1. Go to **Settings** → **Pages**
2. Configure:
   - Source: **Deploy from a branch**
   - Branch: `gh-pages`
   - Folder: `/` (root)

Automatically deployed by `.github/workflows/pages.yml` on each push to `main`.

Access at: https://0ai-cyberviser.github.io/PeachTree/

### Documentation Site

Built with:

- **mkdocs** — Static site generator
- **Material theme** — Professional theme
- **Config:** `mkdocs.yml`
- **Source:** `docs/` directory

## Collaborators & Teams

### Permission Levels

- **Maintain** — Full admin except deletion
- **Write** — Create branches, merge PRs
- **Triage** — Manage issues, assign reviewers
- **Read** — View and comment

### Recommended Setup

- **Owners** (admin): 2-3 maintainers
- **Core team** (maintain): 3-5 key contributors
- **Contributors** (write): Active contributors
- **Community** (read): Everyone

## Labels

Key labels for organization:

### Priority

- `priority:high` — Urgent
- `priority:medium` — Standard
- `priority:low` — Nice to have

### Type

- `enhancement` — New feature
- `bug` — Bug report
- `documentation` — Documentation
- `testing` — Tests
- `question` — Question

### Area

- `area:api` — API changes
- `area:cli` — CLI interface
- `area:safety` — Safety gates
- `area:policy` — Policy packs
- `area:deduplication` — Dedup logic

### Status

- `needs-triage` — Needs review
- `in-progress` — Being worked on
- `blocked` — Waiting on something
- `wontfix` — Not fixing

## Releases & Versioning

### Version Scheme

- **Semantic Versioning:** MAJOR.MINOR.PATCH
- Current: 0.9.0 (development)
- Format: `v0.10.0` in git tags

### Release Process

1. Update `pyproject.toml` version
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.10.0`
4. Push tag: `git push origin v0.10.0`
5. GitHub Actions automatically:
   - Runs tests
   - Builds packages
   - Creates release
   - Publishes to PyPI

### Release Artifacts

Included in release:

- SBOM (Software Bill of Materials)
- Signatures
- Release notes
- Model cards (if applicable)

## Monitoring

### Analytics

**Settings** → **Code security and analysis**

Monitor:

- CodeQL findings
- Dependabot alerts
- Secret scanning alerts
- Covered lines percentage

### Actions & Insights

- **Actions** tab — Workflow run history
- **Insights** → **Network** — Commit graph
- **Insights** → **Contributors** — Activity stats

## Maintenance Tasks

### Weekly

- [ ] Review and merge dependabot PRs
- [ ] Review new issues and PRs
- [ ] Check CI/CD status

### Monthly

- [ ] Review analytics
- [ ] Update roadmap if needed
- [ ] Community communication
- [ ] Plan next release

### Quarterly

- [ ] Major feature planning
- [ ] Security audit
- [ ] Documentation review
- [ ] Dependency audit

## Emergency Procedures

### Security Vulnerability

1. Email security@cyberviser.io
2. Do NOT open public issue
3. Fix in private fork
4. Deploy patch release
5. Announce after patching

### Major Outage

1. Disable auto-deployment
2. Investigate root cause
3. Fix and test thoroughly
4. Re-enable deployment
5. Document incident

### Dependency Issue

1. Check Dependabot alert
2. Review changelog
3. Test locally
4. Accept or skip PR
5. Document decision

## Resources

- [GitHub Docs](https://docs.github.com/) — Official documentation
- [GitHub CLI](https://cli.github.com/) — Command-line tool
- [About Workflows](https://docs.github.com/en/actions/learn-github-actions) — Actions documentation

---

**Last Updated:** 2026-04-27

**Maintainer Contact:** maintainers@cyberviser.io
