# PeachTree Cloud Deployment Guide

Deploy PeachTree dataset control plane on major cloud platforms for production use.

## Table of Contents

1. [AWS Deployment](#aws-deployment)
2. [Google Cloud Platform](#google-cloud-platform)
3. [Microsoft Azure](#microsoft-azure)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [CI/CD Integration](#cicd-integration)

---

## AWS Deployment

### Architecture

```
┌─────────────────────────────────────────────────┐
│                   AWS Account                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐      ┌──────────────┐         │
│  │   EC2/ECS    │      │   S3 Bucket  │         │
│  │  PeachTree   │◄────►│   Datasets   │         │
│  │   Workers    │      │              │         │
│  └──────────────┘      └──────────────┘         │
│         │                      │                 │
│         ▼                      ▼                 │
│  ┌──────────────┐      ┌──────────────┐         │
│  │  CloudWatch  │      │     IAM      │         │
│  │  Monitoring  │      │   Roles      │         │
│  └──────────────┘      └──────────────┘         │
└─────────────────────────────────────────────────┘
```

### 1. EC2 Instance Deployment

**Launch EC2 instance:**

```bash
# Create EC2 instance (Ubuntu 22.04 LTS)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type c5.2xlarge \
  --key-name peachtree-key \
  --security-group-ids sg-123456 \
  --subnet-id subnet-123456 \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":500,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PeachTree-Worker}]'
```

**Setup script (user-data.sh):**

```bash
#!/bin/bash

# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.11
add-apt-repository ppa:deadsnakes/ppa -y
apt-get install python3.11 python3.11-venv python3.11-dev -y

# Install dependencies
apt-get install git build-essential -y

# Clone and setup PeachTree
git clone https://github.com/0ai-Cyberviser/PeachTree.git /opt/peachtree
cd /opt/peachtree

python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[prod]"

# Configure AWS CLI
apt-get install awscli -y

# Setup systemd service
cat > /etc/systemd/system/peachtree.service <<EOF
[Unit]
Description=PeachTree Dataset Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/peachtree
Environment="PATH=/opt/peachtree/venv/bin"
ExecStart=/opt/peachtree/venv/bin/python scripts/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable peachtree
systemctl start peachtree

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb
```

### 2. S3 Storage for Datasets

**Create S3 bucket:**

```bash
# Create bucket
aws s3 mb s3://peachtree-datasets --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket peachtree-datasets \
  --versioning-configuration Status=Enabled

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket peachtree-datasets \
  --lifecycle-configuration file://s3-lifecycle.json
```

**s3-lifecycle.json:**

```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    },
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 180,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

**Upload/download datasets:**

```bash
# Upload dataset to S3
aws s3 cp data/datasets/security-training.jsonl \
  s3://peachtree-datasets/v1.0/security-training.jsonl

# Download dataset from S3
aws s3 cp s3://peachtree-datasets/v1.0/security-training.jsonl \
  data/datasets/security-training.jsonl
```

### 3. IAM Roles and Policies

**Create IAM policy for PeachTree:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::peachtree-datasets",
        "arn:aws:s3:::peachtree-datasets/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. CloudWatch Monitoring

**Create CloudWatch dashboard:**

```bash
aws cloudwatch put-dashboard \
  --dashboard-name PeachTree \
  --dashboard-body file://cloudwatch-dashboard.json
```

**cloudwatch-dashboard.json:**

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["PeachTree", "RecordsCreated", {"stat": "Sum"}],
          [".", "BuildDuration", {"stat": "Average"}],
          [".", "QualityScore", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "PeachTree Metrics"
      }
    }
  ]
}
```

---

## Google Cloud Platform

### 1. Compute Engine Deployment

**Create VM instance:**

```bash
gcloud compute instances create peachtree-worker \
  --machine-type=n2-standard-8 \
  --boot-disk-size=500GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --metadata-from-file startup-script=startup.sh \
  --scopes=cloud-platform \
  --zone=us-central1-a
```

**startup.sh:**

```bash
#!/bin/bash

# Install Python and dependencies
apt-get update
apt-get install -y python3.11 python3.11-venv git

# Clone PeachTree
cd /opt
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree

python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[prod]"

# Install Stackdriver logging
apt-get install -y google-fluentd
```

### 2. Cloud Storage for Datasets

**Create bucket:**

```bash
# Create bucket
gsutil mb -c STANDARD -l us-central1 gs://peachtree-datasets

# Set lifecycle policy
gsutil lifecycle set gs-lifecycle.json gs://peachtree-datasets
```

**gs-lifecycle.json:**

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365, "isLive": false}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 90}
      }
    ]
  }
}
```

**Upload/download:**

```bash
# Upload
gsutil cp data/datasets/security-training.jsonl \
  gs://peachtree-datasets/v1.0/security-training.jsonl

# Download
gsutil cp gs://peachtree-datasets/v1.0/security-training.jsonl \
  data/datasets/security-training.jsonl
```

### 3. Cloud Monitoring

**Create custom metrics:**

```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{project_id}"

descriptor = monitoring_v3.MetricDescriptor(
    type_="custom.googleapis.com/peachtree/records_created",
    metric_kind=monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
    value_type=monitoring_v3.MetricDescriptor.ValueType.INT64,
    description="Number of records created by PeachTree"
)

client.create_metric_descriptor(name=project_name, metric_descriptor=descriptor)
```

---

## Microsoft Azure

### 1. Virtual Machine Deployment

**Create VM:**

```bash
az vm create \
  --resource-group peachtree-rg \
  --name peachtree-worker \
  --image Ubuntu2204 \
  --size Standard_D8s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --os-disk-size-gb 500 \
  --custom-data cloud-init.txt
```

**cloud-init.txt:**

```yaml
#cloud-config
package_update: true
package_upgrade: true
packages:
  - python3.11
  - python3.11-venv
  - git
  - build-essential

runcmd:
  - cd /opt
  - git clone https://github.com/0ai-Cyberviser/PeachTree.git
  - cd PeachTree
  - python3.11 -m venv venv
  - /opt/PeachTree/venv/bin/pip install -e ".[prod]"
```

### 2. Azure Blob Storage

**Create storage account:**

```bash
# Create account
az storage account create \
  --name peachtreedatasets \
  --resource-group peachtree-rg \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name datasets \
  --account-name peachtreedatasets
```

**Upload/download:**

```bash
# Upload
az storage blob upload \
  --account-name peachtreedatasets \
  --container-name datasets \
  --name v1.0/security-training.jsonl \
  --file data/datasets/security-training.jsonl

# Download
az storage blob download \
  --account-name peachtreedatasets \
  --container-name datasets \
  --name v1.0/security-training.jsonl \
  --file data/datasets/security-training.jsonl
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy PeachTree
COPY . /app

# Install PeachTree
RUN pip install --no-cache-dir -e ".[prod]"

# Create data directories
RUN mkdir -p /data/datasets /data/manifests /data/raw

# Expose metrics port
EXPOSE 9090

# Run worker
CMD ["python", "scripts/worker.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  peachtree-worker:
    build: .
    container_name: peachtree-worker
    volumes:
      - ./data:/data
      - ./config:/app/config
    environment:
      - PEACHTREE_DATA_DIR=/data
      - PEACHTREE_LOG_LEVEL=INFO
    restart: unless-stopped
    
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9091:9090"
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

**Run with Docker:**

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f peachtree-worker

# Stop
docker-compose down
```

---

## Kubernetes Deployment

### k8s/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: peachtree-worker
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
        image: peachtree:latest
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
        volumeMounts:
        - name: data
          mountPath: /data
        env:
        - name: PEACHTREE_DATA_DIR
          value: "/data"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: peachtree-data-pvc
```

### k8s/pvc.yaml

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: peachtree-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi
  storageClassName: fast-ssd
```

**Deploy to Kubernetes:**

```bash
# Apply configurations
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=peachtree
kubectl logs -f deployment/peachtree-worker
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Deploy PeachTree

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v6
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build Docker image
        run: |
          docker build -t peachtree:${{ github.sha }} .
          docker tag peachtree:${{ github.sha }} peachtree:latest
      
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
          docker push peachtree:${{ github.sha }}
          docker push peachtree:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster peachtree --service peachtree-worker --force-new-deployment
```

---

## Best Practices

1. **Security:**
   - Use IAM roles instead of access keys
   - Enable encryption at rest for storage
   - Use VPC/subnet isolation
   - Implement least privilege access

2. **Monitoring:**
   - Track build duration, quality scores, errors
   - Set up alerts for failures
   - Monitor resource usage (CPU, memory, disk)

3. **Backup:**
   - Regular snapshots of datasets
   - Version control for manifests
   - Offsite backup for critical data

4. **Cost Optimization:**
   - Use spot instances for non-critical workloads
   - Archive old datasets to cheaper storage
   - Right-size compute resources

---

**Deploy PeachTree to production with confidence!**
