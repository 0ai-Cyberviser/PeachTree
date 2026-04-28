#!/usr/bin/env python3
"""
Complete Enhanced PeachTree Fuzzing Pipeline

Demonstrates the full workflow of dataset enhancement, fuzzing corpus generation,
learning tree optimization, and quality scoring for security-focused ML training.

Usage:
    python examples/enhanced_fuzzing_pipeline.py \
        --dataset data/raw/fuzzing-reports.jsonl \
        --output-dir data/enhanced/
"""

import argparse
import json
from pathlib import Path
import sys

from peachtree.fuzzing_enrichment import (
    FuzzingEnrichment,
    enrich_fuzzing_corpus,
)
from peachtree.peachfuzz_harness import (
    PeachFuzzHarness,
    FuzzTarget,
    build_peachfuzz_harness,
)
from peachtree.enhanced_planner import (
    build_fuzzing_learning_tree,
    build_security_learning_tree,
)
from peachtree.security_quality import (
    SecurityQualityScorer,
    score_fuzzing_dataset,
)
from peachtree.corpus_optimization import (
    optimize_fuzzing_corpus,
)
from peachtree.dataset_builder import DatasetBuilder
from peachtree.safety import SafetyGate


def create_sample_dataset(output_path: Path) -> None:
    """Create a sample fuzzing dataset for demonstration."""
    print(f"📝 Creating sample dataset at {output_path}...")
    
    sample_records = [
        {
            "id": "crash-001",
            "text": """
            AddressSanitizer: heap-buffer-overflow on address 0x60200000eff4
            READ of size 4 at 0x60200000eff4 thread T0
            SIGSEGV signal 11
            
            Stack trace:
            #0 0x7f8a3c in parse_input /src/parser.c:142
            #1 0x7f8b2d in main /src/main.c:89
            
            Reproducer: POC-crash-001.txt
            Severity: Critical
            Impact: Remote code execution via malformed input
            Mitigation: Add bounds checking in parse_input()
            """,
            "source_repo": "0ai-Cyberviser/vulnerable-parser",
            "source_path": "crash-reports/crash-001.md",
            "source_digest": "abc123...",
            "quality_score": 0.85,
            "metadata": {
                "tags": ["crash", "heap-overflow", "critical"],
            },
        },
        {
            "id": "fuzz-seed-001",
            "text": """
            Fuzzing seed file for PNG parser coverage.
            
            Coverage metrics:
            2456/5000 blocks (49.1%)
            1234/2000 edges (61.7%)
            78/150 functions (52.0%)
            
            File content:
            ```
            89 50 4E 47 0D 0A 1A 0A  // PNG signature
            00 00 00 0D 49 48 44 52  // IHDR chunk
            ```
            
            This seed achieves unique coverage in the IHDR chunk parsing logic.
            """,
            "source_repo": "0ai-Cyberviser/fuzzing-corpus",
            "source_path": "seeds/png/seed-001.txt",
            "source_digest": "def456...",
            "quality_score": 0.72,
            "metadata": {
                "tags": ["seed", "coverage", "png"],
            },
        },
        {
            "id": "vuln-report-001",
            "text": """
            Vulnerability Report: Use-after-free in libxml2
            
            CVE-2023-XXXXX
            Severity: High
            
            Description:
            A use-after-free vulnerability exists in the XML parser when processing
            malformed DOCTYPE declarations. The parser frees a buffer but continues
            to reference it during error handling.
            
            Detection:
            - AddressSanitizer: heap-use-after-free
            - Discovered via fuzzing with AFL++
            
            Exploit:
            An attacker can craft a malicious XML file to trigger arbitrary code execution.
            
            Fix:
            Set freed pointers to NULL and add existence checks before dereferencing.
            """,
            "source_repo": "0ai-Cyberviser/security-research",
            "source_path": "vulnerabilities/libxml2-uaf.md",
            "source_digest": "ghi789...",
            "quality_score": 0.92,
            "metadata": {
                "tags": ["vulnerability", "use-after-free", "CVE"],
            },
        },
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in sample_records) + "\n",
        encoding="utf-8",
    )
    
    print(f"✅ Created {len(sample_records)} sample records")


def step1_enrich_dataset(input_path: Path, output_dir: Path) -> Path:
    """Step 1: Enrich dataset with fuzzing metadata."""
    print("\n" + "="*60)
    print("STEP 1: Fuzzing Dataset Enrichment")
    print("="*60)
    
    enriched_path = output_dir / "enriched.jsonl"
    
    print(f"📊 Enriching dataset from {input_path}...")
    summary = enrich_fuzzing_corpus(input_path, enriched_path)
    
    print(f"\n✅ Enrichment complete:")
    print(f"   - Total records: {summary['total_records']}")
    print(f"   - Crash signatures detected: {summary['crash_signatures_detected']}")
    print(f"   - Coverage metrics extracted: {summary['coverage_metrics_extracted']}")
    print(f"   - High relevance records: {summary['high_relevance_records']}")
    print(f"   - Output: {enriched_path}")
    
    return enriched_path


def step2_score_quality(enriched_path: Path, output_dir: Path) -> None:
    """Step 2: Score dataset with security-focused quality metrics."""
    print("\n" + "="*60)
    print("STEP 2: Security Quality Scoring")
    print("="*60)
    
    json_report = output_dir / "quality-report.json"
    md_report = output_dir / "quality-report.md"
    
    print(f"📈 Scoring security quality...")
    report = score_fuzzing_dataset(enriched_path, json_report, md_report)
    
    print(f"\n✅ Quality scoring complete:")
    print(f"   - Total records: {report.total_records}")
    print(f"   - Average score: {report.avg_score:.1f}")
    print(f"   - Passed records: {report.passed}/{report.total_records}")
    
    if "security_statistics" in report.metadata:
        stats = report.metadata["security_statistics"]
        print(f"\n📊 Security Statistics:")
        print(f"   - Vulnerability indicators: {stats['total_vulnerability_indicators']}")
        print(f"   - Crash reproducible: {stats['crash_reproducible_count']}")
        print(f"   - Sanitizer coverage: {stats['sanitizer_coverage_count']}")
    
    print(f"\n   - JSON report: {json_report}")
    print(f"   - Markdown report: {md_report}")


def step3_build_learning_tree(output_dir: Path) -> None:
    """Step 3: Build fuzzing and security learning trees."""
    print("\n" + "="*60)
    print("STEP 3: Enhanced Learning Tree Generation")
    print("="*60)
    
    # Build fuzzing learning tree
    print("🌳 Building fuzzing learning tree...")
    fuzz_tree = build_fuzzing_learning_tree(
        project="PeachFuzz",
        goal="Build defensive fuzzing infrastructure with crash triage",
        max_depth=2,
    )
    
    nodes, train_paths, infer_paths = fuzz_tree.build_with_pathways()
    
    print(f"\n✅ Fuzzing tree built:")
    print(f"   - Total nodes: {len(nodes)}")
    print(f"   - Training paths: {len(train_paths)}")
    print(f"   - Inference paths: {len(infer_paths)}")
    
    # Export training workflow
    train_workflow = output_dir / "fuzzing-training-workflow.json"
    fuzz_tree.export_training_workflow(str(train_workflow))
    print(f"   - Training workflow: {train_workflow}")
    
    # Export full tree
    tree_path = output_dir / "fuzzing-learning-tree.json"
    tree_path.write_text(fuzz_tree.to_json_with_paths(), encoding="utf-8")
    print(f"   - Full tree: {tree_path}")
    
    # Build security learning tree
    print("\n🔒 Building security learning tree...")
    sec_tree = build_security_learning_tree(
        project="Hancock",
        goal="Learn vulnerability patterns and defensive techniques",
        max_depth=2,
    )
    
    sec_nodes, sec_train, sec_infer = sec_tree.build_with_pathways()
    
    print(f"✅ Security tree built:")
    print(f"   - Total nodes: {len(sec_nodes)}")
    print(f"   - Training paths: {len(sec_train)}")
    
    sec_tree_path = output_dir / "security-learning-tree.json"
    sec_tree_path.write_text(sec_tree.to_json_with_paths(), encoding="utf-8")
    print(f"   - Full tree: {sec_tree_path}")


def step4_build_harness(enriched_path: Path, output_dir: Path) -> None:
    """Step 4: Build PeachFuzz harness and corpus."""
    print("\n" + "="*60)
    print("STEP 4: PeachFuzz Harness Generation")
    print("="*60)
    
    harness_config = output_dir / "peachfuzz-harness.json"
    corpus_dir = output_dir / "fuzzing-corpus"
    
    print("🔧 Building PeachFuzz harness...")
    summary = build_peachfuzz_harness(
        enriched_path,
        harness_config,
        corpus_dir,
    )
    
    print(f"\n✅ Harness generation complete:")
    print(f"   - Corpus items extracted: {summary['corpus_items_extracted']}")
    print(f"   - Optimization: {summary['optimization']['reduction_ratio']:.1%} reduction")
    print(f"   - Config: {harness_config}")
    print(f"   - Corpus directory: {corpus_dir}")


def step5_optimize_corpus(enriched_path: Path, output_dir: Path) -> None:
    """Step 5: Optimize fuzzing corpus."""
    print("\n" + "="*60)
    print("STEP 5: Corpus Optimization")
    print("="*60)
    
    optimized_dir = output_dir / "optimized-corpus"
    
    strategies = ["balanced", "coverage", "crashes"]
    
    for strategy in strategies:
        print(f"\n📊 Optimizing with '{strategy}' strategy...")
        strategy_dir = optimized_dir / strategy
        
        summary = optimize_fuzzing_corpus(
            enriched_path,
            strategy_dir,
            target_size=100,
            strategy=strategy,
        )
        
        opt = summary["optimization"]
        print(f"   ✅ {strategy.capitalize()} optimization:")
        print(f"      - Seeds: {opt['original_count']} → {opt['optimized_count']}")
        print(f"      - Size: {opt['original_size_bytes']} → {opt['optimized_size_bytes']} bytes")
        print(f"      - Output: {strategy_dir}")


def main():
    """Main execution pipeline."""
    parser = argparse.ArgumentParser(
        description="Enhanced PeachTree fuzzing pipeline demonstration"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Path to input JSONL dataset (creates sample if not provided)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/enhanced-fuzzing"),
        help="Output directory for all generated files",
    )
    parser.add_argument(
        "--skip-sample",
        action="store_true",
        help="Skip sample dataset creation",
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🌳 PeachTree Enhanced Fuzzing Pipeline")
    print("="*60)
    print()
    print("This pipeline demonstrates:")
    print("  1. Fuzzing dataset enrichment with crash signatures")
    print("  2. Security-focused quality scoring")
    print("  3. Enhanced learning trees with training/inference paths")
    print("  4. PeachFuzz harness generation")
    print("  5. Corpus optimization strategies")
    print()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine input dataset
    if args.dataset and args.dataset.exists():
        input_dataset = args.dataset
        print(f"📂 Using provided dataset: {input_dataset}")
    elif not args.skip_sample:
        input_dataset = args.output_dir / "sample-dataset.jsonl"
        create_sample_dataset(input_dataset)
    else:
        print("❌ Error: No dataset provided and sample creation skipped")
        sys.exit(1)
    
    # Execute pipeline steps
    try:
        # Step 1: Enrich dataset
        enriched_path = step1_enrich_dataset(input_dataset, args.output_dir)
        
        # Step 2: Score quality
        step2_score_quality(enriched_path, args.output_dir)
        
        # Step 3: Build learning trees
        step3_build_learning_tree(args.output_dir)
        
        # Step 4: Build harness
        step4_build_harness(enriched_path, args.output_dir)
        
        # Step 5: Optimize corpus
        step5_optimize_corpus(enriched_path, args.output_dir)
        
        # Summary
        print("\n" + "="*60)
        print("✅ Pipeline Complete!")
        print("="*60)
        print(f"\nAll outputs saved to: {args.output_dir}")
        print("\nKey files:")
        print(f"  - Enriched dataset: enriched.jsonl")
        print(f"  - Quality report: quality-report.json")
        print(f"  - Fuzzing tree: fuzzing-learning-tree.json")
        print(f"  - Security tree: security-learning-tree.json")
        print(f"  - Harness config: peachfuzz-harness.json")
        print(f"  - Optimized corpus: optimized-corpus/")
        print()
        print("Next steps:")
        print("  1. Review quality report for dataset health")
        print("  2. Use training workflow for model fine-tuning")
        print("  3. Deploy PeachFuzz harness with optimized corpus")
        print("  4. Integrate with Hancock for security LLM training")
        print()
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
