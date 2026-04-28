"""Integration tests for enhanced fuzzing and learning tree features.

Tests the fuzzing enrichment, PeachFuzz harness, enhanced planner,
security quality scorer, and corpus optimization modules.
"""

from pathlib import Path
import json
import tempfile
import pytest

from peachtree.fuzzing_enrichment import (
    FuzzingEnrichment,
    CrashSignature,
    CoverageMetrics,
    enrich_fuzzing_corpus,
)
from peachtree.peachfuzz_harness import (
    PeachFuzzHarness,
    FuzzTarget,
    CorpusItem,
    build_peachfuzz_harness,
)
from peachtree.enhanced_planner import (
    EnhancedLearningTree,
    TrainingInferencePath,
    build_fuzzing_learning_tree,
    build_security_learning_tree,
)
from peachtree.security_quality import (
    SecurityQualityScorer,
    SecurityQualityMetrics,
    score_fuzzing_dataset,
)
from peachtree.corpus_optimization import (
    CorpusOptimizer,
    CorpusSeed,
    optimize_fuzzing_corpus,
)


class TestFuzzingEnrichment:
    """Test fuzzing dataset enrichment functionality."""
    
    def test_crash_signature_detection(self):
        """Test crash signature detection from content."""
        enricher = FuzzingEnrichment()
        
        text = """
        AddressSanitizer: heap-buffer-overflow on address 0x60200000eff4
        SIGSEGV signal 11
        Stack trace:
        #0 0x7f1234 in vulnerable_function
        """
        
        record = {"text": text, "metadata": {}}
        enriched = enricher.enrich_record(record)
        
        assert "crash_signature" in enriched["metadata"]
        assert enriched["metadata"]["crash_type"] == "heap-overflow"
        assert enriched["metadata"]["crash_severity"] == "critical"
        assert enriched["metadata"]["crash_signal"] == "SIGSEGV"
    
    def test_coverage_extraction(self):
        """Test coverage metrics extraction."""
        enricher = FuzzingEnrichment()
        
        text = """
        Coverage report:
        1234/5678 blocks (21.7%)
        567/890 edges (63.7%)
        45/100 functions (45.0%)
        """
        
        record = {"text": text, "metadata": {}}
        enriched = enricher.enrich_record(record)
        
        assert "coverage_metrics" in enriched["metadata"]
        metrics = enriched["metadata"]["coverage_metrics"]
        assert "block_coverage" in metrics
        assert metrics["block_coverage"] > 0
    
    def test_fuzzing_relevance_scoring(self):
        """Test fuzzing relevance score calculation."""
        enricher = FuzzingEnrichment()
        
        high_relevance_text = """
        Fuzzing with AFL++ found a crash in libpng.
        SIGSEGV in png_read_data. Reproducible with the attached POC.
        AddressSanitizer detected heap-buffer-overflow.
        """
        
        record = {"text": high_relevance_text, "metadata": {}}
        enriched = enricher.enrich_record(record)
        
        assert enriched["metadata"]["fuzzing_relevance"] >= 0.7
    
    def test_enrich_dataset(self, tmp_path):
        """Test enriching a complete dataset."""
        dataset = tmp_path / "test_dataset.jsonl"
        output = tmp_path / "enriched.jsonl"
        
        records = [
            {
                "id": "test1",
                "text": "SIGSEGV crash in function foo()",
                "metadata": {},
            },
            {
                "id": "test2",
                "text": "Normal fuzzing log entry with coverage data",
                "metadata": {},
            },
        ]
        
        dataset.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )
        
        enricher = FuzzingEnrichment()
        summary = enricher.enrich_dataset(dataset, output)
        
        assert summary["total_records"] == 2
        assert summary["enriched_records"] == 2
        assert output.exists()


class TestPeachFuzzHarness:
    """Test PeachFuzz harness generation."""
    
    def test_add_target(self):
        """Test adding fuzzing targets."""
        harness = PeachFuzzHarness()
        
        target = FuzzTarget(
            name="test_parser",
            target_binary="./bin/parser",
            target_args=("-f", "@@"),
            max_len=4096,
        )
        
        harness.add_target(target)
        
        assert len(harness.targets) == 1
        assert harness.targets[0].name == "test_parser"
    
    def test_add_corpus_item(self):
        """Test adding corpus items."""
        harness = PeachFuzzHarness()
        
        item = harness.add_corpus_item(
            content="test input data",
            source="manual-seed",
            crash_signature="segfault-001",
        )
        
        assert len(harness.corpus_items) == 1
        assert item.crash_signature == "segfault-001"
        assert item.interesting is True
    
    def test_corpus_from_dataset(self, tmp_path):
        """Test building corpus from dataset."""
        dataset = tmp_path / "dataset.jsonl"
        
        records = [
            {
                "id": "crash1",
                "text": "Crash reproducer: POC input here",
                "metadata": {"crash_signature": "heap-overflow-001"},
            },
            {
                "id": "seed1",
                "text": "```seed content here```",
                "metadata": {"fuzzing_relevance": 0.8},
            },
        ]
        
        dataset.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )
        
        harness = PeachFuzzHarness()
        added = harness.from_dataset(dataset)
        
        assert added >= 1
        assert len(harness.corpus_items) >= 1
    
    def test_optimize_corpus(self):
        """Test corpus optimization."""
        harness = PeachFuzzHarness()
        
        # Add duplicate items
        for i in range(5):
            harness.add_corpus_item(
                content=f"test {i}",
                source=f"source-{i}",
            )
        # Add duplicate
        harness.add_corpus_item(content="test 0", source="duplicate")
        
        stats = harness.optimize_corpus(deduplicate=True, minimize=True)
        
        assert stats["original_count"] == 6
        assert stats["optimized_count"] == 5  # One duplicate removed
    
    def test_generate_harness_config(self, tmp_path):
        """Test harness configuration generation."""
        harness = PeachFuzzHarness()
        
        target = FuzzTarget(name="test", target_binary="./test")
        harness.add_target(target)
        harness.add_corpus_item(content="test", source="test")
        
        config_path = tmp_path / "harness.json"
        result = harness.generate_harness_config(config_path)
        
        assert result.exists()
        config = json.loads(result.read_text())
        assert config["version"] == "1.0"
        assert len(config["targets"]) == 1


class TestEnhancedLearningTree:
    """Test enhanced learning tree with training/inference paths."""
    
    def test_fuzzing_specialization(self):
        """Test fuzzing-specialized tree."""
        tree = build_fuzzing_learning_tree(
            project="test-fuzzer",
            goal="Build fuzzing infrastructure",
            max_depth=2,
        )
        
        nodes, train_paths, infer_paths = tree.build_with_pathways()
        
        assert len(nodes) > 0
        assert tree.specialized_mode == "fuzzing"
        # Should have fuzzing-specific branches
        assert any("crash-triage" in str(node.tags) for node in nodes)
    
    def test_security_specialization(self):
        """Test security-specialized tree."""
        tree = build_security_learning_tree(
            project="test-security",
            goal="Learn security patterns",
            max_depth=2,
        )
        
        nodes, train_paths, infer_paths = tree.build_with_pathways()
        
        assert len(nodes) > 0
        assert tree.specialized_mode == "security"
        # Should have security-specific branches
        assert any("vulnerability-patterns" in str(node.tags) for node in nodes)
    
    def test_training_path_generation(self):
        """Test training path generation."""
        tree = EnhancedLearningTree(
            project="test",
            goal="test goal",
            specialized_mode="training",
            max_depth=2,
        )
        
        nodes, train_paths, infer_paths = tree.build_with_pathways()
        
        assert len(train_paths) > 0
        for path in train_paths:
            assert path.path_type == "training"
            assert len(path.nodes) > 0
    
    def test_optimal_path_selection(self):
        """Test optimal path selection."""
        tree = EnhancedLearningTree(
            project="test",
            goal="test goal",
            specialized_mode="training",
            max_depth=2,
        )
        
        tree.build_with_pathways()
        
        optimal = tree.get_optimal_training_path()
        
        if tree.training_paths:
            assert optimal is not None
            assert optimal in tree.training_paths
    
    def test_export_workflows(self, tmp_path):
        """Test workflow export."""
        tree = EnhancedLearningTree(
            project="test",
            goal="test goal",
            specialized_mode="training",
            max_depth=1,
        )
        
        tree.build_with_pathways()
        
        train_path = tmp_path / "training.json"
        result = tree.export_training_workflow(str(train_path))
        
        if tree.training_paths:
            assert train_path.exists()
            workflow = json.loads(train_path.read_text())
            assert workflow["workflow_type"] == "training"


class TestSecurityQualityScorer:
    """Test security-focused quality scoring."""
    
    def test_security_metrics_calculation(self):
        """Test security metrics calculation."""
        scorer = SecurityQualityScorer()
        
        record = {
            "text": """
            Critical heap-buffer-overflow vulnerability found.
            AddressSanitizer detected the issue with full stack trace.
            Reproducible with provided POC. Impact: remote code execution.
            Mitigation: bounds checking required.
            """,
            "metadata": {},
        }
        
        score = scorer.score_record(record, 0)
        
        assert score.total >= 60  # Should score reasonably high
        assert "security_metrics" in record["metadata"]
        
        metrics = record["metadata"]["security_metrics"]
        assert metrics["vulnerability_indicators"] > 0
        assert metrics["crash_reproducibility"] > 0
        assert metrics["defensive_value"] > 0
    
    def test_score_dataset_with_security(self, tmp_path):
        """Test scoring dataset with security metrics."""
        dataset = tmp_path / "security_dataset.jsonl"
        
        records = [
            {
                "id": "vuln1",
                "text": "Critical heap overflow with ASAN report and reproducer",
                "metadata": {},
                "quality_score": 0.8,
            },
            {
                "id": "vuln2",
                "text": "Medium severity null pointer dereference",
                "metadata": {},
                "quality_score": 0.6,
            },
        ]
        
        dataset.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )
        
        scorer = SecurityQualityScorer(security_weight=0.6)
        report = scorer.score_dataset(dataset)
        
        assert report.total_records == 2
        assert "security_statistics" in report.metadata
        
        stats = report.metadata["security_statistics"]
        assert "total_vulnerability_indicators" in stats
        assert stats["total_vulnerability_indicators"] > 0


class TestCorpusOptimization:
    """Test corpus optimization utilities."""
    
    def test_add_seed_from_record(self):
        """Test adding seeds from records."""
        optimizer = CorpusOptimizer(target_corpus_size=10)
        
        record = {
            "text": "```test seed content```",
            "source_path": "test.txt",
            "metadata": {
                "fuzzing_relevance": 0.8,
                "crash_signature": "crash-001",
                "crash_severity": "high",
            },
            "quality_score": 0.85,
        }
        
        seed = optimizer.add_seed_from_record(record)
        
        assert seed is not None
        assert len(optimizer.seeds) == 1
        assert seed.crash_potential > 0.5
    
    def test_deduplication(self):
        """Test corpus deduplication."""
        optimizer = CorpusOptimizer()
        
        # Add duplicates
        for i in range(3):
            record = {
                "text": "duplicate content",
                "source_path": f"source-{i}.txt",
                "metadata": {},
                "quality_score": 0.5 + i * 0.1,
            }
            optimizer.add_seed_from_record(record)
        
        stats = optimizer.optimize(deduplicate=True, minimize=False)
        
        assert stats["original_count"] == 3
        assert stats["optimized_count"] == 1  # Deduplicated to 1
    
    def test_optimization_strategies(self):
        """Test different optimization strategies."""
        strategies = ["balanced", "coverage", "crashes", "diverse"]
        
        for strategy in strategies:
            optimizer = CorpusOptimizer(target_corpus_size=5)
            
            # Add varied seeds
            for i in range(10):
                record = {
                    "text": f"seed content {i}" * 10,
                    "source_path": f"seed-{i}.txt",
                    "metadata": {
                        "fuzzing_relevance": i / 10.0,
                        "coverage_metrics": {"block_coverage": i * 10},
                    },
                    "quality_score": i / 10.0,
                }
                optimizer.add_seed_from_record(record)
            
            stats = optimizer.optimize(strategy=strategy)
            
            assert stats["optimized_count"] <= 5
            assert stats["strategy"] == strategy
    
    def test_export_optimized_corpus(self, tmp_path):
        """Test exporting optimized corpus."""
        optimizer = CorpusOptimizer(target_corpus_size=5)
        
        for i in range(3):
            record = {
                "text": f"seed {i}",
                "source_path": f"seed-{i}.txt",
                "metadata": {},
                "quality_score": 0.7,
            }
            optimizer.add_seed_from_record(record)
        
        optimizer.optimize()
        
        output_dir = tmp_path / "corpus"
        stats = optimizer.export_optimized_corpus(output_dir)
        
        assert output_dir.exists()
        assert (output_dir / "corpus_manifest.json").exists()
        assert stats["seeds_exported"] == 3


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""
    
    def test_complete_fuzzing_pipeline(self, tmp_path):
        """Test complete fuzzing dataset pipeline."""
        # Create test dataset
        dataset = tmp_path / "raw_dataset.jsonl"
        records = [
            {
                "id": "crash1",
                "text": """
                AddressSanitizer: heap-buffer-overflow
                SIGSEGV at 0x12345678
                Reproducer: POC input here
                """,
                "metadata": {},
                "quality_score": 0.75,
            },
        ]
        dataset.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
            encoding="utf-8",
        )
        
        # 1. Enrich dataset
        enriched = tmp_path / "enriched.jsonl"
        enricher = FuzzingEnrichment()
        enricher.enrich_dataset(dataset, enriched)
        
        # 2. Score quality
        scorer = SecurityQualityScorer()
        report = scorer.score_dataset(enriched)
        
        assert report.total_records > 0
        
        # 3. Build harness
        harness_config = tmp_path / "harness.json"
        corpus_dir = tmp_path / "corpus"
        build_peachfuzz_harness(enriched, harness_config, corpus_dir)
        
        assert harness_config.exists()
        assert corpus_dir.exists()
        
        # 4. Optimize corpus
        optimized_corpus = tmp_path / "optimized"
        optimize_fuzzing_corpus(enriched, optimized_corpus, target_size=10)
        
        assert optimized_corpus.exists()
        assert (optimized_corpus / "corpus_manifest.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
