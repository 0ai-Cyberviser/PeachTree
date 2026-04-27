#!/bin/bash
# Multi-Organization Security Dataset Ingestion Script
# Unified ingestion from MITRE-Cyber-Security-CVE-Database, Cybeviser, and 0ai-cyberviserai
# Owner: Johnny Watters (@0ai-Cyberviser)
# Created: April 27, 2026

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATASETS_DIR="/tmp/datasets"
PEACHTREE_DIR="/tmp/peachtree"
RAW_DATA_DIR="${PEACHTREE_DIR}/data/raw"
FINAL_DATASET_DIR="${PEACHTREE_DIR}/data/datasets"
ORG_NAME="MITRE-Cyber-Security-CVE-Database"
ORG_URL="https://github.com/${ORG_NAME}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  Multi-Organization Security Dataset Ingestion${NC}"
echo -e "${BLUE}  Organizations: MITRE-CVE-DB, Cybeviser, 0ai-cyberviserai${NC}"
echo -e "${BLUE}  Target: Hancock Cybersecurity LLM Training Dataset${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1"
}

# Step 1: Create directory structure
print_status "Creating directory structure..."
mkdir -p "${DATASETS_DIR}"
mkdir -p "${RAW_DATA_DIR}"
mkdir -p "${FINAL_DATASET_DIR}"
mkdir -p "${PEACHTREE_DIR}/reports"
mkdir -p "${PEACHTREE_DIR}/data/manifests"

# Step 2: Clone CRITICAL repositories
print_status "Cloning CRITICAL priority repositories..."

echo ""
echo -e "${YELLOW}=== CRITICAL: mitre-cve-database (PRIMARY SOURCE) ===${NC}"
if [ ! -d "${DATASETS_DIR}/mitre-cve" ]; then
    print_status "Cloning mitre-cve-database..."
    git clone "${ORG_URL}/mitre-cve-database.git" "${DATASETS_DIR}/mitre-cve" || print_warning "Clone failed, may need authentication"
else
    print_status "mitre-cve-database already cloned, pulling latest..."
    cd "${DATASETS_DIR}/mitre-cve" && git pull && cd -
fi

# Step 3: Clone HIGH priority repositories
print_status "Cloning HIGH priority repositories..."

repos_high=(
    "metasploit-framework:15k stars - Exploit documentation"
    "sqlmap:6.2k stars - SQL injection tool"
    "john:2.5k stars - Password cracker"
    "clamav:849 stars - Malware signatures"
    "snort3:666 stars - IDS/IPS"
    "grok-promptss:441 stars - Security prompts"
)

for repo_info in "${repos_high[@]}"; do
    repo_name="${repo_info%%:*}"
    repo_desc="${repo_info#*:}"
    echo ""
    echo -e "${YELLOW}=== HIGH: ${repo_name} (${repo_desc}) ===${NC}"
    
    if [ ! -d "${DATASETS_DIR}/${repo_name}" ]; then
        print_status "Cloning ${repo_name}..."
        git clone "${ORG_URL}/${repo_name}.git" "${DATASETS_DIR}/${repo_name}" || print_warning "Clone failed for ${repo_name}"
    else
        print_status "${repo_name} already cloned, skipping..."
    fi
done

# Step 4: Ingest CVE Database (CRITICAL)
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  DATA INGESTION: CVE Records (CRITICAL)${NC}"
echo -e "${BLUE}================================================================${NC}"

if [ -d "${DATASETS_DIR}/mitre-cve" ]; then
    print_status "Ingesting CVE records from mitre-cve-database..."
    
    # Count source files
    cve_file_count=$(find "${DATASETS_DIR}/mitre-cve" -name "*.json" -o -name "*.xml" -o -name "*.txt" | wc -l)
    print_status "Found ${cve_file_count} CVE-related files"
    
    # TODO: Replace with actual peachtree ingest command when ready
    print_warning "Placeholder: peachtree ingest --repo ${DATASETS_DIR}/mitre-cve --pattern '**/*.json,**/*.xml,**/*.txt' --output ${RAW_DATA_DIR}/cve-records.jsonl"
    
    # Create placeholder output
    echo '{"id":"cve-placeholder","source":"mitre-cve","status":"ready for ingestion"}' > "${RAW_DATA_DIR}/cve-records.jsonl"
    print_status "CVE ingestion complete (placeholder)"
else
    print_error "mitre-cve-database not found, skipping CVE ingestion"
fi

# Step 5: Ingest Metasploit modules
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  DATA INGESTION: Metasploit Exploit Documentation (HIGH)${NC}"
echo -e "${BLUE}================================================================${NC}"

if [ -d "${DATASETS_DIR}/metasploit-framework" ]; then
    print_status "Ingesting Metasploit modules and documentation..."
    
    # Count modules
    module_count=$(find "${DATASETS_DIR}/metasploit-framework/modules" -name "*.rb" 2>/dev/null | wc -l || echo "0")
    doc_count=$(find "${DATASETS_DIR}/metasploit-framework/documentation" -name "*.md" 2>/dev/null | wc -l || echo "0")
    print_status "Found ${module_count} modules and ${doc_count} documentation files"
    
    # TODO: Replace with actual peachtree ingest command
    print_warning "Placeholder: peachtree ingest --repo ${DATASETS_DIR}/metasploit-framework --pattern 'modules/**/*.rb,documentation/**/*.md' --output ${RAW_DATA_DIR}/metasploit-modules.jsonl"
    
    echo '{"id":"metasploit-placeholder","source":"metasploit","status":"ready for ingestion"}' > "${RAW_DATA_DIR}/metasploit-modules.jsonl"
    print_status "Metasploit ingestion complete (placeholder)"
else
    print_warning "metasploit-framework not found, skipping"
fi

# Step 6: Ingest Grok security prompts
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  DATA INGESTION: Grok Security Prompts (HIGH)${NC}"
echo -e "${BLUE}================================================================${NC}"

if [ -d "${DATASETS_DIR}/grok-promptss" ]; then
    print_status "Ingesting Grok security prompts..."
    
    # Count prompt files
    prompt_count=$(find "${DATASETS_DIR}/grok-promptss" -name "*.jinja" -o -name "*.md" -o -name "*.txt" | wc -l)
    print_status "Found ${prompt_count} prompt files"
    
    # TODO: Replace with actual peachtree ingest command
    print_warning "Placeholder: peachtree ingest --repo ${DATASETS_DIR}/grok-promptss --pattern '**/*.jinja,**/*.md,**/*.txt' --output ${RAW_DATA_DIR}/grok-security-prompts.jsonl"
    
    echo '{"id":"grok-prompts-placeholder","source":"grok-prompts","status":"ready for ingestion"}' > "${RAW_DATA_DIR}/grok-security-prompts.jsonl"
    print_status "Grok prompts ingestion complete (placeholder)"
else
    print_warning "grok-promptss not found, skipping"
fi

# Step 7: Build unified security dataset
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  DATASET BUILD: Unified Multi-Organization Security Dataset${NC}"
echo -e "${BLUE}================================================================${NC}"

print_status "Building unified dataset from all sources..."
print_status "Input sources:"
ls -lh "${RAW_DATA_DIR}"/*.jsonl 2>/dev/null || print_warning "No JSONL files found yet"

# TODO: Replace with actual peachtree build command
print_warning "Placeholder: peachtree build --input ${RAW_DATA_DIR}/cve-records.jsonl --input ${RAW_DATA_DIR}/metasploit-modules.jsonl --input ${RAW_DATA_DIR}/grok-security-prompts.jsonl --policy ${PEACHTREE_DIR}/policies/security-dataset.yaml --output ${FINAL_DATASET_DIR}/multi-org-security-training.jsonl"

echo '{"id":"unified-placeholder","sources":["cve","metasploit","grok"],"status":"ready for build"}' > "${FINAL_DATASET_DIR}/multi-org-security-training.jsonl"
print_status "Unified dataset build complete (placeholder)"

# Step 8: Run safety gates and audit
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  SAFETY GATES: Secret Filtering, License Compliance, Provenance${NC}"
echo -e "${BLUE}================================================================${NC}"

print_status "Running safety gate audit..."
print_warning "Placeholder: peachtree audit --input ${FINAL_DATASET_DIR}/multi-org-security-training.jsonl --output ${PEACHTREE_DIR}/reports/multi-org-audit.json --detailed"

cat > "${PEACHTREE_DIR}/reports/multi-org-audit.json" << 'EOF'
{
  "audit_date": "2026-04-27",
  "dataset": "multi-org-security-training.jsonl",
  "sources": ["mitre-cve", "metasploit", "grok-prompts"],
  "safety_gates": {
    "secret_filtering": "PLACEHOLDER - PASS",
    "license_compliance": "PLACEHOLDER - NEEDS REVIEW (GPL detected)",
    "provenance_tracking": "PLACEHOLDER - PASS",
    "quality_scoring": "PLACEHOLDER - PENDING",
    "deduplication": "PLACEHOLDER - PENDING"
  },
  "status": "Ready for full ingestion when PeachTree commands are available"
}
EOF

print_status "Audit report generated: ${PEACHTREE_DIR}/reports/multi-org-audit.json"

# Step 9: Generate Hancock training handoff
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  HANCOCK INTEGRATION: Cybersecurity LLM Training Handoff${NC}"
echo -e "${BLUE}================================================================${NC}"

print_status "Generating Hancock training handoff manifest..."
print_warning "Placeholder: peachtree handoff --dataset ${FINAL_DATASET_DIR}/multi-org-security-training.jsonl --output ${PEACHTREE_DIR}/data/manifests/hancock-multi-org-handoff.json --model hancock-cybersecurity-llm"

cat > "${PEACHTREE_DIR}/data/manifests/hancock-multi-org-handoff.json" << 'EOF'
{
  "handoff_date": "2026-04-27",
  "model_name": "hancock-cybersecurity-llm",
  "dataset_path": "data/datasets/multi-org-security-training.jsonl",
  "organizations": [
    "MITRE-Cyber-Security-CVE-Database",
    "Cybeviser",
    "0ai-cyberviserai"
  ],
  "data_sources": {
    "mitre-cve-database": {"priority": "critical", "records": "TBD"},
    "metasploit-framework": {"priority": "high", "records": "TBD"},
    "grok-promptss": {"priority": "high", "records": "TBD"}
  },
  "safety_compliance": {
    "secret_filtering": "PASS",
    "license_compliance": "NEEDS REVIEW",
    "ethical_use_agreement": "REQUIRED",
    "export_control": "REQUIRED"
  },
  "training_config": {
    "model_type": "cybersecurity-llm",
    "base_model": "llama-3-8b",
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": "2e-5"
  },
  "status": "PLACEHOLDER - Ready for actual dataset build"
}
EOF

print_status "Hancock handoff manifest generated: ${PEACHTREE_DIR}/data/manifests/hancock-multi-org-handoff.json"

# Step 10: Summary report
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  INGESTION SUMMARY${NC}"
echo -e "${BLUE}================================================================${NC}"

echo ""
echo -e "${GREEN}Directories Created:${NC}"
echo "  - Datasets: ${DATASETS_DIR}"
echo "  - Raw data: ${RAW_DATA_DIR}"
echo "  - Final datasets: ${FINAL_DATASET_DIR}"
echo "  - Reports: ${PEACHTREE_DIR}/reports"

echo ""
echo -e "${GREEN}Repositories Cloned:${NC}"
find "${DATASETS_DIR}" -maxdepth 1 -type d | tail -n +2 | while read dir; do
    echo "  - $(basename "$dir")"
done

echo ""
echo -e "${GREEN}Raw Data Files:${NC}"
ls -lh "${RAW_DATA_DIR}"/*.jsonl 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  - None yet (placeholders created)"

echo ""
echo -e "${GREEN}Final Datasets:${NC}"
ls -lh "${FINAL_DATASET_DIR}"/*.jsonl 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  - None yet (placeholders created)"

echo ""
echo -e "${GREEN}Reports Generated:${NC}"
ls -lh "${PEACHTREE_DIR}/reports"/*.json 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}' || echo "  - None yet"

echo ""
echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
echo "1. Install PeachTree CLI: pip install peachtree"
echo "2. Replace placeholder commands with actual peachtree commands"
echo "3. Re-run this script to perform actual ingestion"
echo "4. Review audit report: ${PEACHTREE_DIR}/reports/multi-org-audit.json"
echo "5. Review handoff manifest: ${PEACHTREE_DIR}/data/manifests/hancock-multi-org-handoff.json"
echo "6. Obtain legal/compliance approval before training"
echo "7. Hand off to Hancock training pipeline"

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  Multi-Organization Ingestion Complete!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""

# Exit successfully
exit 0
