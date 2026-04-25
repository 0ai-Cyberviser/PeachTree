# Security Policy

PeachTree is a dataset-generation, lineage, and provenance tool for CyberViser / 0AI projects.

## Hard safety rules

- Do not ingest secrets, credentials, keys, tokens, or private personal data.
- Do not collect public repositories without license review.
- Do not train on unknown public code without provenance and policy review.
- Do not generate offensive exploit datasets for unauthorized use.
- Keep dataset manifests with all generated outputs.
- Treat generated datasets as untrusted until policy, license, deduplication, and readiness gates pass.

## Reporting vulnerabilities

Report vulnerabilities privately to CyberViser / 0AI maintainers. Include:

1. Summary and affected component.
2. Exact command, dataset, manifest, or policy pack involved.
3. Minimal safe reproduction steps.
4. Expected and observed behavior.
5. Whether private data, secrets, licenses, or third-party repositories were involved.

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

## Human-in-the-loop rule

Automated dataset builders and self-learning assistants may propose new records, policy updates, evaluations, and model-card changes. They must not publish datasets, train downstream models, bypass license checks, or merge high-impact changes without human review.
