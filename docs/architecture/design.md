# Architecture

## High-Level Design

PeachTree is organized around a pipeline architecture:

```
Raw Sources → Ingestion → Processing → Safety Gates → Building → Dataset
```

### Pipeline Stages

#### 1. **Ingestion** (`repo_ingest.py`)
- Discovers and extracts source documents from repositories
- Collects code, documentation, tests, configuration files
- Generates SourceDocument records with metadata

#### 2. **Planning** (`planner.py`, `RecursiveLearningTree`)
- Hierarchical planning of learning objectives
- Branching exploration strategies
- Scope and coverage analysis

#### 3. **Safety Gates** (`safety.py`, `license_gate.py`)
- Secret/token/key detection and filtering
- License compatibility checking
- Content safety validation
- Unsafe pattern detection

#### 4. **Building** (`builder.py`, `DatasetBuilder`)
- Converts SourceDocuments to DatasetRecords
- Applies deterministic record generation
- Maintains provenance metadata
- Writes JSONL format

#### 5. **Quality Processing** (`quality.py`)
- Score records by quality metrics
- Identify low-quality or incomplete records
- Filter based on scoring policies

#### 6. **Deduplication** (`dedup.py`)
- Detect duplicate or similar records
- Deterministic reduction algorithms
- Similarity-based filtering

#### 7. **Release Management** (`release_bundle.py`, `sbom.py`, `signing.py`)
- Generate SBOM for supply chain transparency
- Create cryptographic signatures
- Package into release bundles
- Generate model cards for transparency

## Data Models

### SourceDocument
Raw document extracted from sources:

```python
@dataclass
class SourceDocument:
    id: str  # Unique identifier
    content: str  # Document text
    source_repo: str  # Repository identifier
    source_path: str  # Path within repository
    source_digest: str  # Commit/version digest
    document_type: str  # "code", "doc", "test", etc.
    metadata: dict[str, Any]  # Custom metadata
```

### DatasetRecord
Training-ready record with full provenance:

```python
@dataclass
class DatasetRecord:
    id: str  # SHA-256 digest
    text: str  # Content
    source_repo: str  # Origin repository
    source_path: str  # Source file path
    source_digest: str  # Commit hash
    quality_score: float  # Quality (0.0 - 1.0)
    license: str  # License identifier
    metadata: dict[str, Any]  # Provenance
```

### DatasetManifest
Metadata and summary:

```python
@dataclass
class DatasetManifest:
    name: str
    version: str
    created_at: str
    record_count: int
    dataset_path: str
    builder_version: str
    policy_applied: str
    metadata: dict[str, Any]
```

## Core Components

### RecursiveLearningTree (`planner.py`)
Hierarchical planning system for data collection:

- **Root objective**: High-level training goal
- **Branches**: Exploration strategies
- **Leaves**: Specific data collection tactics
- Supports iterative refinement and coverage analysis

### SafetyGate (`safety.py`)
Multi-layer filtering:

```python
class SafetyGate:
    - filter_secrets: Regex-based detection
    - filter_unsafe_content: Pattern matching
    - filter_unknown_licenses: License validation
    - custom_filters: User-defined rules
```

### DatasetBuilder (`builder.py`)
Main building engine:

```python
class DatasetBuilder:
    - build_records: SourceDocument → DatasetRecord
    - validate_provenance: Verify metadata
    - apply_policies: Run quality/safety rules
    - export_jsonl: Write training format
```

### PolicyPackEvaluator (`policy_packs.py`)
Composable policy engine:

```python
class PolicyPackEvaluator:
    - evaluate: Run policy checks
    - compose: Combine multiple policies
    - report: Generate compliance reports
```

### RegistryBuilder (`registry.py`)
Artifact discovery and indexing:

```python
class DatasetRegistryBuilder:
    - discover: Find all artifacts
    - build: Create registry manifest
    - sign: Add signatures
```

### ReleaseBundle (`release_bundle.py`)
Package for distribution:

```python
class ReleaseBundleBuilder:
    - create: Build release package
    - add_sbom: Supply chain info
    - sign: Cryptographic signatures
    - verify: Validate release integrity
```

## Data Flow Example

```
Repository: owner/repo
    ↓
Source Discovery:
  - src/main.py
  - README.md
  - tests/test_main.py
    ↓
Ingestion (repo_ingest.py):
  [
    {id: doc1, content: "...", source_repo: "owner/repo", source_path: "src/main.py"},
    {id: doc2, content: "...", source_repo: "owner/repo", source_path: "README.md"},
    {id: doc3, content: "...", source_repo: "owner/repo", source_path: "tests/test_main.py"}
  ]
    ↓
Safety Gate (safety.py):
  - Filter secrets: No API keys found ✓
  - Check licenses: MIT detected ✓
  - Content safety: All good ✓
    ↓
Dataset Builder (builder.py):
  [
    {
      id: "sha256-abc123",
      text: "...",
      source_repo: "owner/repo",
      source_path: "src/main.py",
      source_digest: "abc123def456",
      quality_score: 0.95,
      license: "MIT"
    },
    ...
  ]
    ↓
Quality Scoring (quality.py):
  - All records >= 0.85 ✓
    ↓
Deduplication (dedup.py):
  - 3 records, no duplicates found
    ↓
Release Bundle (release_bundle.py):
  - training.jsonl (3 records)
  - manifest.json (metadata)
  - sbom.json (supply chain)
  - signatures.json (verification)
```

## Module Organization

```
src/peachtree/
├── __init__.py           # Package exports
├── cli.py               # CLI commands
├── models.py            # Data classes
├── builder.py           # DatasetBuilder
├── planner.py           # RecursiveLearningTree
├── safety.py            # SafetyGate
├── quality.py           # Quality scoring
├── dedup.py             # Deduplication
├── repo_ingest.py       # Repository ingestion
├── policy_packs.py      # Policy evaluation
├── license_gate.py      # License validation
├── registry.py          # Registry builder
├── release_bundle.py    # Release packaging
├── sbom.py              # SBOM generation
├── signing.py           # Cryptographic signing
├── trainer_handoff.py   # Training workflow handoff
├── lineage.py           # Provenance tracking
├── github_owned.py      # GitHub repo collection
├── diff_review.py       # Dataset comparison
├── model_card.py        # Model card generation
├── exporters.py         # Format exporters
├── dependency_graph.py  # Dependency analysis
├── github_policy.py     # GitHub access policies
├── lora_job.py          # LoRA fine-tuning
├── scheduler.py         # Task scheduling
└── training_plan.py     # Training workflows
```

## Key Design Decisions

### 1. **Deterministic Record Generation**
Same source always produces same record ID (SHA-256 digest).
Ensures reproducible datasets.

### 2. **Full Provenance Attached**
Every record includes source, path, and commit info.
Enables audit trails and compliance proof.

### 3. **Policy-Driven Safety**
Composable policies instead of hard-coded rules.
Flexible enforcement for different domains.

### 4. **Local-First Approach**
Owned repositories ingested by default.
Public collection requires explicit policy.

### 5. **Review-First Release**
Manifests and diffs generated before publication.
Human review gates enabled by default.

## Performance Characteristics

- **Ingestion**: ~1000 files/second
- **Quality Scoring**: ~500 records/second
- **Deduplication**: ~100 records/second (similarity-based)
- **SBOM Generation**: ~1000 artifacts/second

## Dependencies

- **Python 3.10+**
- **pytest** (testing)
- **ruff** (linting)
- **mypy** (type checking)
- **coverage** (test coverage)

## Testing Strategy

- **Unit tests**: Individual component functionality
- **Integration tests**: End-to-end workflows
- **Fixture-based**: Realistic test data
- **Coverage target**: 90%+ (currently 91%)

## Extensibility Points

- Custom SourceDocument filters
- Custom quality scoring models
- Custom policy pack definitions
- Custom exporters
- Custom GitHub policies
