# Security Policy

PeachTree is a dataset-generation, lineage, and provenance tool for CyberViser / 0AI projects.

## Hard Safety Rules

- **Do not ingest secrets** — Credentials, keys, tokens, or private personal data must be blocked
- **Do not collect public repos blindly** — Requires license review and explicit authorization
- **Do not train on unknown code** — Provenance, policy review, and full audit trail required
- **Do not generate offensive datasets** — Exploits require authorization and security review
- **Keep all manifests** — Document lineage, policies, and decisions for all datasets
- **Treat outputs as untrusted** — Enforce safety, license, deduplication, and readiness gates before use

## Reporting Vulnerabilities

**Do not open public issues for security vulnerabilities.**

Report privately to CyberViser / 0AI maintainers:

1. Email: security@cyberviser.io
2. Subject: `[PeachTree] Security Vulnerability`
3. Include:
   - Summary and affected component
   - Exact command, dataset, manifest, or policy pack
   - Minimal safe reproduction steps
   - Expected vs. observed behavior
   - Whether secrets, licenses, or third-party data involved

Expected response: Acknowledgment within 48 hours, fix within 72 hours.

## Dataset and model-training safety

PeachTree outputs may be used downstream for model training or evaluation. Before training:

- Review manifests and lineage reports.
- Run license-gate, readiness, deduplication, and policy-pack checks.
- Remove records containing secrets, private personal data, or unclear provenance.
- Version datasets, policy packs, evaluation sets, and model cards.
- Preserve audit trails for generated datasets, prompts, model outputs, and human approvals.

## Continuous security baseline

This repository should maintain:

- CodeQL code scanning.
- Dependabot alerts and security updates.
- Dependency auditing with pip-audit and OSV Scanner.
- Semgrep SAST.
- Checkov scanning for GitHub Actions, Dockerfile, Terraform, and Kubernetes assets.
- GitHub secret scanning and push protection enabled in repository settings.
- Branch protection requiring pull requests, review, passing checks, and signed commits where possible.

## Human-in-the-Loop Rule

Automated dataset builders and self-learning assistants may propose new records, policy updates, evaluations, and model-card changes. They must not publish datasets, train downstream models, bypass license checks, or merge high-impact changes without human review.

## Configuration Security

1. **Use `.peachtree.yaml`** — Store policies in version control
2. **Use environment variables** — For API keys and credentials (never in code)
3. **Use pre-commit hooks** — Catch secrets before commit
4. **Use `.gitignore`** — Exclude logs and temporary files
5. **Review policies** — Audit policy packs before deployment
6. **Test locally** — Validate datasets in sandbox before production

### Environment Variables

Never commit to version control:

```bash
# Good: Store in environment or .env (add to .gitignore)
export PEACHTREE_POLICY_KEY=secret
export GITHUB_TOKEN=ghp_...
export PYPI_TOKEN=pypi_...

# Bad: Never do this
api_key = "secret-key-in-code"  # DON'T COMMIT
```

## Data Handling

- **Treat datasets as sensitive** — Control access and distribution
- **Encrypt at rest** — JSONL files contain training data
- **Track provenance** — Full audit trail for compliance
- **Version control** — Tag releases for reproducibility
- **Archive releases** — Preserve historical datasets

## Dependency Security

PeachTree has minimal dependencies:

| Package | Purpose | Security |
|---------|---------|----------|
| pydantic | Data validation | Actively maintained |
| pyyaml | Configuration | Actively maintained |
| pytest | Testing | Actively maintained |
| mkdocs | Documentation | Actively maintained |

All dependencies are:

- Pinned to specific versions
- Regularly updated for security patches
- Scanned by Dependabot
- Audited with pip-audit

## Vulnerability Scanning

PeachTree uses multiple scanning tools:

1. **Ruff** — Fast Python linting
2. **MyPy** — Type checking
3. **Pre-commit hooks** — Automated quality checks
4. **GitHub Actions** — Continuous testing and scanning
5. **Dependabot** — Dependency updates
6. **CodeQL** — Code analysis

## Compliance

### Standards

- **Python 3.10+** — Supported versions only
- **Semantic Versioning** — Clear version numbering
- **SBOM** — Software bill of materials for releases
- **Provenance** — Full dataset lineage tracking

### Audit Trails

- Git history tracks all code changes
- Commit messages document decisions
- Release tags mark production versions
- Policy evaluations logged

## Incident Response

If a security issue is discovered:

1. **Acknowledge** — Respond within 48 hours
2. **Assess** — Evaluate severity and impact
3. **Fix** — Develop and test patch
4. **Release** — Publish security update
5. **Announce** — Notify users and maintainers
6. **Document** — Update this policy and CHANGELOG

## Severity Levels

| Level | Impact | Response |
|-------|--------|----------|
| Critical | Data breach, secret leak | Immediate patch + notification |
| High | Policy bypass, unauthorized access | 24-hour patch |
| Medium | Safety gate bypass, feature misuse | 72-hour patch |
| Low | Minor issues, edge cases | Next regular release |

## Version Support

| Version | Status | Security Updates Until |
|---------|--------|------------------------|
| 0.10.x  | Current | Latest release |
| 0.9.x   | LTS | 2027-04-26 |
| 0.8.x   | EOL | 2026-04-26 |

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [National Vulnerability Database](https://nvd.nist.gov/)

## Questions?

- **Security concerns** → security@cyberviser.io
- **General questions** → GitHub Discussions
- **Bug reports** → GitHub Issues
- **Contributing** → See CONTRIBUTING.md

---

**Last Updated:** 2026-04-27 | **Policy Version:** 1.1
