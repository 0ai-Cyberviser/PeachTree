# Deploying PeachTree

Guide for deploying PeachTree documentation and releases.

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages on every push to `main`.

### Setup

1. **Enable GitHub Pages in repository settings:**
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages
   - Folder: / (root)

2. **Workflows are automatic:**
   - `.github/workflows/pages.yml` deploys documentation
   - Accessible at: `https://0ai-Cyberviser.github.io/PeachTree/`

### Manual Deployment

Deploy documentation manually:

```bash
pip install mkdocs mkdocs-material
python -m mkdocs gh-deploy
```

## Docker Registry Deployment

Push Docker image to registry:

```bash
# Build image
docker build -t peachtree:latest .
docker tag peachtree:latest 0aicyberviser/peachtree:latest

# Push to Docker Hub
docker push 0aicyberviser/peachtree:latest
```

## PyPI Release

Releases are automated via GitHub Actions:

1. Create a git tag:
   ```bash
   git tag v0.10.0
   git push origin v0.10.0
   ```

2. GitHub Actions workflow `.github/workflows/release.yml` will:
   - Run tests
   - Build distribution packages
   - Create GitHub Release
   - Upload to PyPI

## Environment Variables

Set these secrets in GitHub repository settings:

- `PYPI_API_TOKEN`: PyPI authentication token

## Deployment Checklist

Before releasing:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Ensure all tests pass
- [ ] Ensure documentation builds
- [ ] Create git tag: `git tag v<version>`
- [ ] Push tag: `git push origin v<version>`
- [ ] Monitor GitHub Actions for deployment
- [ ] Verify deployment at https://github.com/0ai-Cyberviser/PeachTree/releases

## Monitoring Deployments

- **GitHub Actions:** https://github.com/0ai-Cyberviser/PeachTree/actions
- **GitHub Pages:** https://0ai-Cyberviser.github.io/PeachTree/
- **PyPI:** https://pypi.org/project/peachtree-ai/
- **Docker Hub:** https://hub.docker.com/r/0aicyberviser/peachtree
