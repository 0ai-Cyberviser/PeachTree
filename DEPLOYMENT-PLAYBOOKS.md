# Deployment Playbooks

Step-by-step guides for deploying PeachTree in different scenarios.

## Playbook 1: Deploy to PyPI (Package Registry)

### Prerequisites

- PyPI account: https://pypi.org/account/register/
- API token from PyPI account settings
- GitHub repository with push access

### Steps

1. **Create PyPI Token**
   ```
   - Go to https://pypi.org/account/
   - Click "Add API Token"
   - Scope: Entire account or specific project
   - Copy token (format: pypi-xxxxx...)
   ```

2. **Add GitHub Secret**
   ```
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: PYPI_API_TOKEN
   - Value: [paste token]
   - Click "Add secret"
   ```

3. **Update Version**
   ```bash
   # In pyproject.toml or setup.py
   version = "0.10.0"
   
   # Commit change
   git add pyproject.toml
   git commit -m "chore: bump version to 0.10.0"
   git push
   ```

4. **Create Git Tag**
   ```bash
   git tag v0.10.0
   git push origin v0.10.0
   ```

5. **Monitor Release**
   - Go to Actions tab → release workflow
   - Watch for completion (2-5 minutes)
   - Verify on PyPI: https://pypi.org/project/peachtree-ai/

6. **Verify Installation**
   ```bash
   pip install peachtree-ai==0.10.0
   peachtree --version
   ```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid token" | Verify token in GitHub Secrets, check expiration |
| "Upload failed" | Check package name matches PyPI project |
| "Version already exists" | Use new version number, don't reuse |

---

## Playbook 2: Deploy to GitHub Pages (Documentation Site)

### Prerequisites

- GitHub repository with GitHub Pages enabled
- mkdocs.yml configured
- Markdown files in docs/ directory

### Steps

1. **Enable GitHub Pages**
   ```
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages (or main with /docs folder)
   - Save
   ```

2. **Trigger Deployment**
   ```bash
   # Merge PR or push to main
   git push origin main
   
   # Or manually trigger workflow
   - Go to Actions → pages workflow
   - Click "Run workflow"
   ```

3. **Wait for Deployment**
   - Check Actions tab for workflow completion
   - First deployment may take 1-2 minutes
   - Subsequent deployments: 30 seconds

4. **Verify Site**
   - Visit: https://[owner].github.io/[repo-name]/
   - Check for correct theme and navigation
   - Test search functionality

5. **Custom Domain (Optional)**
   ```
   - Settings → Pages
   - Custom domain: your-domain.com
   - CNAME record: [owner].github.io
   ```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "404 Not Found" | Check Pages enabled, branch correct |
| "Site not updating" | Clear browser cache, wait 5 minutes |
| "Wrong theme" | Verify mkdocs.yml theme setting |

---

## Playbook 3: Deploy to Docker Hub

### Prerequisites

- Docker installed locally
- Docker Hub account: https://hub.docker.com/signup
- Docker CLI authenticated: `docker login`

### Steps

1. **Build Docker Image**
   ```bash
   docker build -t peachtree:0.10.0 .
   docker tag peachtree:0.10.0 peachtree:latest
   ```

2. **Tag for Docker Hub**
   ```bash
   docker tag peachtree:0.10.0 username/peachtree:0.10.0
   docker tag peachtree:latest username/peachtree:latest
   ```

3. **Push to Docker Hub**
   ```bash
   docker push username/peachtree:0.10.0
   docker push username/peachtree:latest
   ```

4. **Verify on Docker Hub**
   - Go to hub.docker.com/r/username/peachtree
   - Check tags appear (may take 1-2 minutes)
   - Pull and test locally

5. **Test Pull from Registry**
   ```bash
   docker run username/peachtree:0.10.0 peachtree --version
   ```

### Automate with GitHub Actions

Add to `.github/workflows/docker.yml`:

```yaml
name: Build and Push Docker Image
on:
  push:
    tags: ['v*']

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v2
      - uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: |
            username/peachtree:${{ github.ref_name }}
            username/peachtree:latest
```

---

## Playbook 4: Deploy to Kubernetes

### Prerequisites

- Kubernetes cluster (minikube, EKS, GKE, etc.)
- kubectl installed and configured
- Docker image already built and pushed

### Steps

1. **Create Deployment Manifest**
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: peachtree
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: peachtree
     template:
       metadata:
         labels:
           app: peachtree
       spec:
         containers:
         - name: peachtree
           image: username/peachtree:latest
           ports:
           - containerPort: 8000
           env:
           - name: PEACHTREE_LOG_LEVEL
             value: INFO
   ```

2. **Create Service**
   ```yaml
   # k8s/service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: peachtree-service
   spec:
     selector:
       app: peachtree
     ports:
     - protocol: TCP
       port: 8000
       targetPort: 8000
     type: LoadBalancer
   ```

3. **Deploy to Cluster**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

4. **Monitor Deployment**
   ```bash
   # Check pods
   kubectl get pods -l app=peachtree
   
   # Check service
   kubectl get service peachtree-service
   
   # Check logs
   kubectl logs -l app=peachtree
   ```

5. **Access Service**
   ```bash
   # Get external IP
   kubectl get service peachtree-service
   
   # Access via IP:PORT
   curl http://[EXTERNAL-IP]:8000
   ```

---

## Playbook 5: Deploy to AWS Lambda

### Prerequisites

- AWS account
- AWS CLI configured
- SAM CLI installed: `pip install aws-sam-cli`

### Steps

1. **Create SAM Template**
   ```yaml
   # template.yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Transform: AWS::Serverless-2016-10-31
   
   Resources:
     PeachTreeFunction:
       Type: AWS::Serverless::Function
       Properties:
         CodeUri: src/
         Handler: lambda_handler.handler
         Runtime: python3.10
         Timeout: 60
         MemorySize: 512
   ```

2. **Create Lambda Handler**
   ```python
   # src/lambda_handler.py
   from peachtree import PeachTree
   
   def handler(event, context):
       try:
           peachtree = PeachTree()
           result = peachtree.build(
               input_dir=event['input_dir'],
               output_path=event['output_path']
           )
           return {
               'statusCode': 200,
               'body': result
           }
       except Exception as e:
           return {
               'statusCode': 500,
               'error': str(e)
           }
   ```

3. **Build and Deploy**
   ```bash
   sam build
   sam deploy --guided
   ```

4. **Invoke Function**
   ```bash
   aws lambda invoke \
     --function-name PeachTree \
     --payload '{"input_dir": "s3://bucket/data"}' \
     response.json
   ```

---

## Playbook 6: Deploy to Google Cloud Run

### Prerequisites

- Google Cloud account
- gcloud CLI configured
- Docker image pushed to Google Container Registry

### Steps

1. **Build and Push to GCR**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/peachtree:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy peachtree \
     --image gcr.io/PROJECT-ID/peachtree:latest \
     --platform managed \
     --region us-central1 \
     --memory 2Gi \
     --timeout 3600
   ```

3. **Get Service URL**
   ```bash
   gcloud run services list --platform managed
   ```

4. **Test Service**
   ```bash
   curl https://peachtree-xxx.run.app/
   ```

---

## Playbook 7: Deploy to Self-Hosted Server

### Prerequisites

- Linux server (Ubuntu 20.04+)
- SSH access
- Python 3.10+

### Steps

1. **Connect to Server**
   ```bash
   ssh user@server-ip
   ```

2. **Install Dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.10 python3-pip git
   ```

3. **Clone Repository**
   ```bash
   cd /opt
   sudo git clone https://github.com/0ai-Cyberviser/PeachTree.git
   cd PeachTree
   ```

4. **Setup Environment**
   ```bash
   sudo python3 -m venv venv
   sudo source venv/bin/activate
   sudo pip install -e .
   ```

5. **Create Systemd Service**
   ```ini
   # /etc/systemd/system/peachtree.service
   [Unit]
   Description=PeachTree Service
   After=network.target

   [Service]
   Type=simple
   User=peachtree
   WorkingDirectory=/opt/PeachTree
   ExecStart=/opt/PeachTree/venv/bin/peachtree serve --port 8000
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start peachtree
   sudo systemctl enable peachtree  # Auto-start on reboot
   ```

7. **Monitor Service**
   ```bash
   sudo systemctl status peachtree
   sudo journalctl -u peachtree -f  # Follow logs
   ```

---

## Rollback Procedures

### PyPI Rollback

```bash
# Remove problematic version from PyPI (admin only)
pip index versions peachtree-ai

# Users must downgrade manually
pip install peachtree-ai==0.9.0

# Or remove package from PyPI and yanked it
```

### GitHub Pages Rollback

```bash
# Revert commit that caused issue
git revert <commit-hash>
git push origin main

# Site automatically redeploys
```

### Docker Rollback

```bash
# Redeploy previous image
docker run username/peachtree:0.9.0

# Or re-tag latest
docker tag username/peachtree:0.9.0 username/peachtree:latest
docker push username/peachtree:latest
```

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/peachtree

# Rollback to previous version
kubectl rollout undo deployment/peachtree

# Rollback to specific revision
kubectl rollout undo deployment/peachtree --to-revision=2
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing (129/129)
- [ ] Coverage maintained (≥91%)
- [ ] Documentation updated
- [ ] CHANGELOG updated with version
- [ ] Version bumped in code
- [ ] Git tag created
- [ ] Security checks passed
- [ ] Performance benchmarks acceptable
- [ ] Staging deployment tested
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Monitoring configured
- [ ] Incident response ready

---

**Last Updated:** 2026-04-27

See [DEPLOYMENT.md](DEPLOYMENT.md) for general deployment overview.
