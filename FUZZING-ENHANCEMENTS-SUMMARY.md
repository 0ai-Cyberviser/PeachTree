# Enhanced Fuzzing and Learning Tree Features - Complete Summary

## Overview

Successfully enhanced PeachTree with comprehensive fuzzing dataset enrichment, PeachFuzz harness integration, training/inference learning tree pathways, security-focused quality scoring, and advanced corpus optimization.

## What Was Built

### 1. Fuzzing Dataset Enrichment Module
**File:** `src/peachtree/fuzzing_enrichment.py` (365 lines)

**Key Features:**
- **CrashSignature Detection**: Automatically identifies crash types (segfault, heap-overflow, use-after-free, assertions, timeouts)
- **Coverage Metrics Extraction**: Parses coverage reports for blocks, edges, and functions
- **Fuzzing Relevance Scoring**: Calculates 0.0-1.0 relevance score based on crash info, coverage, and keywords
- **Automatic Tagging**: Generates tags for crash types, sanitizers (ASAN/MSAN/UBSAN), and fuzzing frameworks
- **Quality Score Boosting**: Increases quality scores for high-severity crashes

**API:**
```python
from peachtree import FuzzingEnrichment, enrich_fuzzing_corpus

# Enrich entire dataset
summary = enrich_fuzzing_corpus(
    source_path="data/raw/crashes.jsonl",
    output_path="data/enriched/crashes.jsonl"
)
```

### 2. PeachFuzz Harness Integration
**File:** `src/peachtree/peachfuzz_harness.py` (420 lines)

**Key Features:**
- **FuzzTarget Configuration**: Define fuzzing targets with binaries, args, dictionaries, timeouts
- **Corpus Generation**: Extract crash reproducers and seed inputs from datasets
- **Corpus Optimization**: Minimize and deduplicate corpus items
- **Harness Config Export**: Generate JSON/YAML configuration files
- **Corpus Directory Export**: Write corpus files with manifest

**API:**
```python
from peachtree import build_peachfuzz_harness

summary = build_peachfuzz_harness(
    dataset_path="data/enriched.jsonl",
    output_config="harness.json",
    output_corpus_dir="corpus/"
)
```

### 3. Enhanced Learning Tree with Training/Inference Paths
**File:** `src/peachtree/enhanced_planner.py` (450 lines)

**Key Features:**
- **Specialized Modes**: Fuzzing, security, training, inference branch specialization
- **Training Pathways**: Generate optimal training execution paths
- **Inference Pathways**: Generate optimal inference execution paths
- **Complexity Scoring**: Estimate path complexity (0.0-1.0)
- **Workflow Export**: Export training/inference workflows as JSON

**Specialized Branches:**
- **Fuzzing**: crash-triage, corpus-generation, harness-design, sanitizer-integration, coverage-analysis
- **Security**: vulnerability-patterns, exploit-techniques, defense-mechanisms, threat-modeling
- **Training**: dataset-curation, quality-validation, safety-gates, deduplication, augmentation
- **Inference**: prompt-engineering, context-optimization, output-validation, reasoning-chains

**API:**
```python
from peachtree import build_fuzzing_learning_tree

tree = build_fuzzing_learning_tree(
    project="PeachFuzz",
    goal="Build fuzzing infrastructure",
    max_depth=2
)

nodes, train_paths, infer_paths = tree.build_with_pathways()
optimal_path = tree.get_optimal_training_path()
tree.export_training_workflow("workflow.json")
```

### 4. Security-Focused Quality Scoring
**File:** `src/peachtree/security_quality.py` (340 lines)

**Key Features:**
- **SecurityQualityMetrics**: 6 security-specific metric types
  - Vulnerability indicators (keyword counting)
  - Exploit complexity (technical detail assessment)
  - Defensive value (mitigation information)
  - Crash reproducibility (POC availability)
  - Sanitizer quality (ASAN/MSAN output completeness)
  - Triage completeness (severity, impact, mitigation)
- **Weighted Scoring**: Combines base quality with security metrics
- **Security Statistics**: Aggregates vulnerability indicators, crash reproducibility, sanitizer coverage

**API:**
```python
from peachtree import score_fuzzing_dataset

report = score_fuzzing_dataset(
    dataset_path="data/enriched.jsonl",
    output_json="quality.json",
    output_markdown="quality.md"
)

# Access security statistics
stats = report.metadata["security_statistics"]
print(f"Vulnerability indicators: {stats['total_vulnerability_indicators']}")
```

### 5. Corpus Optimization Utilities
**File:** `src/peachtree/corpus_optimization.py` (400 lines)

**Key Features:**
- **CorpusSeed Model**: Priority, coverage, crash potential, quality scoring
- **4 Optimization Strategies**:
  - **Balanced**: Quality-based (default)
  - **Coverage**: Maximize code coverage
  - **Crashes**: Maximize crash potential
  - **Diverse**: Maximize input diversity (Jaccard distance)
- **Deduplication**: Content-hash based duplicate removal
- **Minimization**: Remove unnecessary content (comments, whitespace)
- **Export**: Corpus directory with manifest

**API:**
```python
from peachtree import optimize_fuzzing_corpus

summary = optimize_fuzzing_corpus(
    dataset_path="data/enriched.jsonl",
    output_dir="corpus/optimized/",
    target_size=1000,
    strategy="balanced"  # or "coverage", "crashes", "diverse"
)
```

### 6. Comprehensive Integration Tests
**File:** `tests/test_fuzzing_enhancements.py` (380 lines)

**Test Coverage:**
- Crash signature detection (heap-overflow, segfault, etc.)
- Coverage metrics extraction
- Fuzzing relevance scoring
- Corpus generation and optimization
- Learning tree pathway generation
- Security quality metrics calculation
- Complete end-to-end pipeline integration

**Run Tests:**
```bash
pytest tests/test_fuzzing_enhancements.py -v
```

### 7. Complete Example Pipeline
**File:** `examples/enhanced_fuzzing_pipeline.py` (350 lines)

**5-Step Workflow:**
1. **Fuzzing Dataset Enrichment**: Add crash signatures and coverage metrics
2. **Security Quality Scoring**: Score with security-focused metrics
3. **Enhanced Learning Tree Generation**: Build fuzzing and security trees
4. **PeachFuzz Harness Generation**: Create harness config and corpus
5. **Corpus Optimization**: Optimize with multiple strategies

**Run Example:**
```bash
python examples/enhanced_fuzzing_pipeline.py \
  --dataset data/raw/fuzzing-reports.jsonl \
  --output-dir data/enhanced/
```

## Statistics

- **5 new modules**: 2,075 lines of production code
- **1 test module**: 380 lines of test coverage
- **1 example pipeline**: 350 lines of demonstration code
- **Total**: 2,805+ lines of new code
- **7 new classes**: FuzzingEnrichment, PeachFuzzHarness, EnhancedLearningTree, SecurityQualityScorer, CorpusOptimizer, and supporting dataclasses
- **15+ new functions**: Convenience wrappers and utilities
- **Zero breaking changes**: All enhancements are additive

## Integration Points

### With PeachFuzz
- Corpus generation from crash reports
- Harness configuration export
- Crash reproducer extraction
- Corpus optimization for fuzzing campaigns

### With Hancock (Cybersecurity LLM)
- Security-focused dataset quality scoring
- Vulnerability pattern learning trees
- Training workflow generation
- Security metrics for model evaluation

### With Existing PeachTree
- Seamless integration with DatasetBuilder
- Compatible with SafetyGate and policy packs
- Works with existing quality scoring (extends it)
- Maintains provenance tracking throughout

## Usage Examples

### Basic Fuzzing Enrichment
```python
from peachtree import enrich_fuzzing_corpus

summary = enrich_fuzzing_corpus(
    "data/raw/crashes.jsonl",
    "data/enriched/crashes.jsonl"
)

print(f"Crash signatures detected: {summary['crash_signatures_detected']}")
print(f"High relevance records: {summary['high_relevance_records']}")
```

### Build PeachFuzz Harness
```python
from peachtree import build_peachfuzz_harness

summary = build_peachfuzz_harness(
    dataset_path="data/enriched.jsonl",
    output_config="peachfuzz-harness.json",
    output_corpus_dir="corpus/"
)

print(f"Corpus items: {summary['corpus_items_extracted']}")
print(f"Optimization: {summary['optimization']['reduction_ratio']:.1%}")
```

### Generate Learning Tree with Pathways
```python
from peachtree import build_fuzzing_learning_tree

tree = build_fuzzing_learning_tree(
    project="MyFuzzer",
    goal="Build defensive fuzzing infrastructure",
    max_depth=2
)

nodes, train_paths, infer_paths = tree.build_with_pathways()
optimal = tree.get_optimal_training_path()

print(f"Training paths: {len(train_paths)}")
print(f"Optimal path complexity: {optimal.estimated_complexity:.2f}")

tree.export_training_workflow("training-workflow.json")
```

### Security Quality Scoring
```python
from peachtree import score_fuzzing_dataset

report = score_fuzzing_dataset(
    dataset_path="data/enriched.jsonl",
    output_json="quality.json",
    output_markdown="quality.md"
)

stats = report.metadata["security_statistics"]
print(f"Vulnerability indicators: {stats['total_vulnerability_indicators']}")
print(f"Crash reproducible ratio: {stats['crash_reproducible_ratio']:.1%}")
```

### Corpus Optimization
```python
from peachtree import optimize_fuzzing_corpus

for strategy in ["balanced", "coverage", "crashes", "diverse"]:
    summary = optimize_fuzzing_corpus(
        dataset_path="data/enriched.jsonl",
        output_dir=f"corpus/{strategy}/",
        target_size=100,
        strategy=strategy
    )
    
    opt = summary["optimization"]
    print(f"{strategy}: {opt['original_count']} → {opt['optimized_count']} seeds")
```

## Design Principles Maintained

✅ **Frozen Dataclasses**: All new models use `@dataclass(frozen=True)`  
✅ **Provenance Tracking**: Source repo, path, digest maintained throughout  
✅ **Safety-First**: No automatic training launches, requires human approval  
✅ **JSONL Format**: All datasets use standard JSONL with provenance  
✅ **Local-First**: No automatic public GitHub scraping  
✅ **Type Safety**: Full type hints with Python 3.10+ syntax  

## Next Steps

### Recommended Usage
1. **Enrich existing datasets**: Run `enrich_fuzzing_corpus()` on crash reports
2. **Score quality**: Use `score_fuzzing_dataset()` for security metrics
3. **Generate harness**: Build PeachFuzz configuration with `build_peachfuzz_harness()`
4. **Optimize corpus**: Select optimal strategy with `optimize_fuzzing_corpus()`
5. **Plan training**: Use learning trees to generate training workflows

### Future Enhancements
- Real-time fuzzing integration (libFuzzer, AFL++, Honggfuzz)
- Advanced crash deduplication (stack trace similarity)
- Coverage-guided corpus selection
- Multi-target harness generation
- Distributed fuzzing coordination

## Files Changed

- ✅ `src/peachtree/fuzzing_enrichment.py` (new, 365 lines)
- ✅ `src/peachtree/peachfuzz_harness.py` (new, 420 lines)
- ✅ `src/peachtree/enhanced_planner.py` (new, 450 lines)
- ✅ `src/peachtree/security_quality.py` (new, 340 lines)
- ✅ `src/peachtree/corpus_optimization.py` (new, 400 lines)
- ✅ `tests/test_fuzzing_enhancements.py` (new, 380 lines)
- ✅ `examples/enhanced_fuzzing_pipeline.py` (new, 350 lines)
- ✅ `src/peachtree/__init__.py` (updated, +20 exports)

## Commit

**Commit**: `cefbfd2`  
**Branch**: `claude/update-ci-dependency-versions`  
**Remote**: Pushed to origin (Terminal-Pressure/PeachTree)  
**Status**: ✅ Ready for review in PR #19

---

**Created**: April 27, 2026  
**Author**: PeachTreeAI Agent  
**Project**: PeachTree ML Dataset Control Plane
