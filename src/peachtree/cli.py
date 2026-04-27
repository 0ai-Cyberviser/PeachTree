from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import DatasetBuilder
from .models import SourceDocument
from .planner import RecursiveLearningTree
from .repo_ingest import iter_local_documents
from .safety import SafetyGate
from .github_owned import OwnedGitHubConnector
from .dependency_graph import DependencyGraphBuilder
from .lineage import DatasetLineageBuilder
from .exporters import ModelExporter, export_format_names
from .diff_review import DatasetDiffReviewer
from .scheduler import UpdatePlanBuilder
from .quality import DatasetQualityScorer
from .dedup import DatasetDeduplicator
from .license_gate import LicenseGate
from .policy_packs import PolicyPackEvaluator
from .model_card import ModelCardGenerator
from .registry import DatasetRegistryBuilder
from .signing import ArtifactSigner
from .sbom import SBOMGenerator
from .release_bundle import ReleaseBundleBuilder
from .trainer_handoff import TrainerHandoffBuilder
from .lora_job import LoraJobCardBuilder, LoraHyperparameters
from .training_plan import DryRunTrainingPlanner
from .health_monitor import DatasetHealthMonitor
from .optimizer import DatasetOptimizer
from .batch_processor import BatchHealthMonitor, BatchOptimizer, BatchQualityScorer
from .status_dashboard import StatusDashboard
from .dataset_comparison import DatasetComparator
from .dataset_versions import DatasetVersionManager
from .workflows import WorkflowEngine, create_standard_pipeline
from .quality_trends import QualityTrendAnalyzer
from .dataset_operations import DatasetMerger, DatasetSplitter
from .smart_sampling import SmartSampler
from .performance import PerformanceProfiler
from .dataset_validation import DatasetValidator, RequiredFieldRule, FieldTypeRule, ContentLengthRule
from .incremental_update import IncrementalUpdater, ChangeTracker
from .dataset_catalog import DatasetCatalog
from .security_scanner import DatasetSecurityScanner
from .advanced_exporters import AdvancedExporters, get_advanced_format_names
from .lineage_visualizer import LineageVisualizer
from .dataset_diff import DatasetDiffEngine
from .policy_templates import PolicyTemplateLibrary
from .dataset_analytics import DatasetAnalyticsEngine
from .dataset_migration import DatasetMigrationEngine, MigrationPlan, MigrationRule
from .quality_enhancement import QualityEnhancementEngine
from .dataset_metrics import DatasetMetricsDashboard
from .backup_restore import DatasetBackupRestore, BackupMetadata
from .export_formats_v2 import ExportFormatsV2
from .quality_gates import QualityGateEngine, QualityGateConfig, GateRule
from .dataset_profiler import DatasetProfiler
from .dataset_testing import DatasetTestFramework, TestSuite, SchemaValidator, PropertyTester
from .dataset_monitoring import DatasetMonitor, MonitoringConfig, HealthStatus
from .dataset_sync import DatasetSynchronizer, SyncState, ConflictResolution
from .dataset_transform import DatasetTransformer, TransformationPipeline, TransformationStep
from .dataset_recommend import DatasetRecommender
from .dataset_collaboration import DatasetCollaborationEngine, CollaboratorInfo, DatasetChange, ChangeType, ReviewStatus
from .dataset_compliance import DatasetComplianceTracker, ComplianceRegulation, ComplianceStatus
from .dataset_cache import DatasetCacheOptimizer, CacheStrategy
from .dataset_scheduler import DatasetScheduler, ScheduleType, TaskType
from .dataset_notifications import DatasetNotificationSystem, NotificationType, EventType, NotificationChannel
from .dataset_webhooks import DatasetWebhookManager, WebhookEvent


def run_plan(args: argparse.Namespace) -> int:
    tree = RecursiveLearningTree(args.project, args.goal, max_depth=args.depth)
    output = tree.to_json()
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


def run_ingest_local(args: argparse.Namespace) -> int:
    docs = iter_local_documents(args.repo, args.repo_name, license_id=args.license)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(doc.to_dict(), sort_keys=True) for doc in docs) + ("\n" if docs else ""), encoding="utf-8")
    print(json.dumps({"output": str(out), "documents": len(docs)}, indent=2, sort_keys=True))
    return 0


def _read_sources(path: str | Path) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            docs.append(SourceDocument(**json.loads(line)))
    return docs


def run_build(args: argparse.Namespace) -> int:
    docs = _read_sources(args.source)
    builder = DatasetBuilder(args.domain, SafetyGate(allow_unknown_license=args.allow_unknown_license))
    records = builder.records_from_documents(docs)
    manifest = builder.write_jsonl(records, args.dataset, args.manifest, docs)
    print(manifest.to_json())
    return 0


def run_audit(args: argparse.Namespace) -> int:
    print(json.dumps(DatasetBuilder(args.domain).audit_jsonl(args.dataset), indent=2, sort_keys=True))
    return 0


def run_policy(args: argparse.Namespace) -> int:
    print(json.dumps({
        "public_github_default": "disabled",
        "owned_local_repos_default": "enabled",
        "license_allowlist_required_for_public": True,
        "secret_filtering": True,
        "provenance_required": True,
        "constant_updates": "configure GitHub Actions; PeachTree itself does not run background jobs",
    }, indent=2, sort_keys=True))
    return 0



def run_github_owned(args: argparse.Namespace) -> int:
    connector = OwnedGitHubConnector()
    if args.from_json:
        repos = connector.from_gh_json(Path(args.from_json).read_text(encoding="utf-8"))
    else:
        repos = connector.list_with_gh(owner=args.owner, limit=args.limit)
    repos = connector.filter_repos(
        repos,
        include_private=args.include_private,
        include_archived=args.include_archived,
    )
    inventory = connector.write_inventory(repos, args.output)
    print(json.dumps({"output": str(inventory), "repositories": len(repos)}, indent=2, sort_keys=True))
    return 0


def run_github_plan(args: argparse.Namespace) -> int:
    connector = OwnedGitHubConnector()
    repos = connector.read_inventory(args.inventory)
    plan = connector.write_scripts(repos, args.clone_root, args.clone_script, args.dataset_script)
    print(plan.to_json())
    return 0




def _print_or_write(content: str, output: str | None) -> None:
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(content + "\n", encoding="utf-8")
    print(content)


def run_graph(args: argparse.Namespace) -> int:
    graph = DependencyGraphBuilder().from_inputs(
        inventory_path=args.inventory,
        dataset_dir=args.dataset_dir,
        manifest_dir=args.manifest_dir,
    )
    if args.format == "json":
        content = graph.to_json()
    elif args.format == "mermaid":
        content = graph.to_mermaid()
    else:
        content = graph.to_dot()
    _print_or_write(content, args.output)
    return 0


def run_lineage(args: argparse.Namespace) -> int:
    lineage = DatasetLineageBuilder().from_dataset(args.dataset, args.manifest)
    if args.format == "json":
        content = lineage.to_json()
    else:
        content = lineage.to_markdown()
    _print_or_write(content, args.output)
    return 0


def run_ecosystem(args: argparse.Namespace) -> int:
    graph = DependencyGraphBuilder().from_inputs(
        inventory_path=args.inventory,
        dataset_dir=args.dataset_dir,
        manifest_dir=args.manifest_dir,
    )
    summary = DatasetLineageBuilder().summarize_directory(args.dataset_dir, args.manifest_dir)
    content = json.dumps(
        {
            "graph": graph.to_dict(),
            "lineage_summary": summary,
            "policy": {
                "local_only": True,
                "public_github_collection": "disabled by default",
                "review_required_before_training": True,
            },
        },
        indent=2,
        sort_keys=True,
    )
    _print_or_write(content, args.output)
    return 0



def run_export_formats(args: argparse.Namespace) -> int:
    print(json.dumps({"formats": list(export_format_names())}, indent=2, sort_keys=True))
    return 0


def run_export(args: argparse.Namespace) -> int:
    exporter = ModelExporter(system_prompt=args.system_prompt, include_metadata=not args.no_metadata)
    stats = exporter.export_file(args.source, args.output, args.format, limit=args.limit)
    print(stats.to_json())
    return 0 if stats.records_written > 0 else 1


def run_validate_export(args: argparse.Namespace) -> int:
    report = ModelExporter().validate_export(args.path, args.format)
    print(report.to_json())
    return 0 if report.ok else 1



def run_diff(args: argparse.Namespace) -> int:
    reviewer = DatasetDiffReviewer()
    diff = reviewer.compare(args.baseline, args.candidate)
    if args.json_output or args.markdown_output:
        reviewer.write_reports(
            diff,
            args.json_output or "reports/dataset-diff.json",
            args.markdown_output or "reports/dataset-diff.md",
        )
    if args.format == "markdown":
        print(diff.to_markdown())
    else:
        print(diff.to_json())
    return 0 if not args.fail_on_review or not diff.review_required else 2


def run_update_plan(args: argparse.Namespace) -> int:
    builder = UpdatePlanBuilder()
    plan = builder.default_plan(args.repo, args.repo_name, name=args.name)
    if args.output or args.markdown_output:
        builder.write_plan(plan, args.output or "data/manifests/update-plan.json", args.markdown_output)
    if args.format == "markdown":
        print(plan.to_markdown())
    else:
        print(plan.to_json())
    return 0


def run_review_report(args: argparse.Namespace) -> int:
    builder = UpdatePlanBuilder()
    plan = builder.read_plan(args.plan)
    commands = builder.command_preview(plan)
    report = {
        "plan": plan.to_dict(),
        "commands": commands,
        "safety": {
            "review_required": plan.review_required,
            "opens_pull_request": plan.open_pull_request,
            "does_not_train_models": True,
            "does_not_upload_datasets": True,
        },
    }
    content = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(content + "\n", encoding="utf-8")
    print(content)
    return 0



def run_score(args: argparse.Namespace) -> int:
    scorer = DatasetQualityScorer(
        min_record_score=args.min_record_score,
        min_average_score=args.min_average_score,
        max_failed_ratio=args.max_failed_ratio,
        min_records=args.min_records,
    )
    report = scorer.score_dataset(args.dataset)
    if args.json_output or args.markdown_output:
        scorer.write_report(
            report,
            args.json_output or "reports/quality-score.json",
            args.markdown_output,
        )
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json(include_records=not args.summary_only))
    return 0 if not args.fail_on_gate or report.gate_passed else 2


def run_dedup(args: argparse.Namespace) -> int:
    deduplicator = DatasetDeduplicator()
    report = deduplicator.deduplicate(args.source, args.output, write_output=True)
    if args.report_json or args.report_markdown:
        deduplicator.write_report(
            report,
            args.report_json or "reports/dedup.json",
            args.report_markdown,
        )
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    return 0


def run_readiness(args: argparse.Namespace) -> int:
    scorer = DatasetQualityScorer(
        min_record_score=args.min_record_score,
        min_average_score=args.min_average_score,
        max_failed_ratio=args.max_failed_ratio,
        min_records=args.min_records,
    )
    quality_report = scorer.score_dataset(args.dataset)
    dedup_report = DatasetDeduplicator().analyze(args.dataset)
    readiness = {
        "dataset": args.dataset,
        "ready": quality_report.gate_passed and dedup_report.duplicate_ratio <= args.max_duplicate_ratio,
        "quality": quality_report.to_dict(include_records=False),
        "deduplication": dedup_report.to_dict(),
        "gates": {
            "quality_gate_passed": quality_report.gate_passed,
            "max_duplicate_ratio": args.max_duplicate_ratio,
            "actual_duplicate_ratio": dedup_report.duplicate_ratio,
            "duplicate_gate_passed": dedup_report.duplicate_ratio <= args.max_duplicate_ratio,
        },
        "safety": {
            "does_not_train_models": True,
            "does_not_upload_datasets": True,
            "requires_human_review": True,
        },
    }
    content = json.dumps(readiness, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(content + "\n", encoding="utf-8")
    print(content)
    return 0 if readiness["ready"] or not args.fail_on_gate else 2




def _split_csv(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def run_policy_pack(args: argparse.Namespace) -> int:
    evaluator = PolicyPackEvaluator()
    if args.list:
        packs = {"packs": [pack.to_dict() for pack in evaluator.list_packs()]}
        print(json.dumps(packs, indent=2, sort_keys=True))
        return 0
    if args.show:
        pack = evaluator.get_pack(args.show)
        if args.format == "markdown":
            print(f"# PeachTree Policy Pack\n\n```json\n{json.dumps(pack.to_dict(), indent=2, sort_keys=True)}\n```")
        else:
            print(json.dumps(pack.to_dict(), indent=2, sort_keys=True))
        return 0

    if not args.dataset:
        raise SystemExit("policy-pack requires --dataset unless --list or --show is used")

    evaluation = evaluator.evaluate(args.dataset, args.pack)
    if args.json_output or args.markdown_output:
        evaluator.write_report(
            evaluation,
            args.json_output or "reports/policy-pack.json",
            args.markdown_output,
        )
    if args.format == "markdown":
        print(evaluation.to_markdown())
    else:
        print(evaluation.to_json())
    return 0 if evaluation.passed or not args.fail_on_gate else 2


def run_license_gate(args: argparse.Namespace) -> int:
    gate = LicenseGate(
        allowed_licenses=_split_csv(args.allow),
        denied_licenses=_split_csv(args.deny),
        allow_unknown=args.allow_unknown,
    )
    report = gate.evaluate(args.dataset)
    if args.json_output or args.markdown_output:
        gate.write_report(
            report,
            args.json_output or "reports/license-gate.json",
            args.markdown_output,
        )
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json(include_findings=not args.summary_only))
    return 0 if report.passed or not args.fail_on_gate else 2


def run_model_card(args: argparse.Namespace) -> int:
    generator = ModelCardGenerator()
    card = generator.generate(
        dataset_path=args.dataset,
        model_name=args.model_name,
        manifest_path=args.manifest,
        quality_report_path=args.quality_report,
        license_report_path=args.license_report,
        policy_report_path=args.policy_report,
        intended_use=args.intended_use,
    )
    generator.write(card, args.output, args.format)
    print(json.dumps({"output": args.output, "format": args.format, "model_name": args.model_name}, indent=2, sort_keys=True))
    return 0





def run_registry(args: argparse.Namespace) -> int:
    builder = DatasetRegistryBuilder()
    roots = args.paths or []
    registry = builder.discover(roots, name=args.name, version=args.version)
    if args.output or args.markdown_output:
        builder.write(registry, args.output or "reports/registry.json", args.markdown_output)
    if args.format == "markdown":
        print(registry.to_markdown())
    else:
        print(registry.to_json())
    return 0


def run_sign(args: argparse.Namespace) -> int:
    signer = ArtifactSigner()
    if args.verify:
        verification = signer.verify_file(args.artifact, args.signature, key=args.key)
        print(verification.to_json())
        return 0 if verification.valid else 2
    envelope = signer.sign_file(args.artifact, key=args.key, key_id=args.key_id)
    if args.output:
        signer.write_signature(envelope, args.output)
    print(envelope.to_json())
    return 0


def run_sbom(args: argparse.Namespace) -> int:
    generator = SBOMGenerator()
    if args.registry:
        registry = generator.read_registry(args.registry)
        sbom = generator.from_registry(registry, source_registry=args.registry)
    else:
        sbom = generator.from_paths(args.paths or [], name=args.name, version=args.version)
    if args.output or args.markdown_output:
        generator.write(sbom, args.output or "reports/sbom.json", args.markdown_output)
    if args.format == "markdown":
        print(sbom.to_markdown())
    else:
        print(sbom.to_json())
    return 0


def run_bundle(args: argparse.Namespace) -> int:
    builder = ReleaseBundleBuilder()
    report = builder.build(
        artifact_paths=args.artifacts,
        output_path=args.output,
        name=args.name,
        version=args.version,
        signing_key=args.signing_key,
        signing_key_id=args.signing_key_id,
    )
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report.to_json() + "\n", encoding="utf-8")
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    return 0





def run_handoff(args: argparse.Namespace) -> int:
    builder = TrainerHandoffBuilder()
    manifest = builder.build(
        dataset_path=args.dataset,
        model_name=args.model_name,
        base_model=args.base_model,
        trainer_profile=args.trainer_profile,
        dataset_format=args.dataset_format,
        registry_path=args.registry,
        sbom_path=args.sbom,
        model_card_path=args.model_card,
        quality_report_path=args.quality_report,
        policy_report_path=args.policy_report,
        license_report_path=args.license_report,
        release_bundle_path=args.release_bundle,
        metadata={"generated_for": "trainer_handoff"},
    )
    if args.output or args.markdown_output:
        builder.write(manifest, args.output or "reports/trainer-handoff.json", args.markdown_output)
    if args.format == "markdown":
        print(manifest.to_markdown())
    else:
        print(manifest.to_json())
    return 0


def run_lora_card(args: argparse.Namespace) -> int:
    hp = LoraHyperparameters(
        rank=args.rank,
        alpha=args.alpha,
        dropout=args.dropout,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        max_seq_length=args.max_seq_length,
        warmup_ratio=args.warmup_ratio,
    )
    card = LoraJobCardBuilder().build(
        dataset_path=args.dataset,
        job_name=args.job_name,
        base_model=args.base_model,
        output_dir=args.output_dir,
        trainer_profile=args.trainer_profile,
        dataset_format=args.dataset_format,
        hyperparameters=hp,
        metadata={"generated_for": "lora_job_card"},
    )
    if args.output or args.markdown_output:
        LoraJobCardBuilder().write(card, args.output or "reports/lora-job-card.json", args.markdown_output)
    if args.format == "markdown":
        print(card.to_markdown())
    else:
        print(card.to_json())
    return 0


def run_train_plan(args: argparse.Namespace) -> int:
    planner = DryRunTrainingPlanner()
    if args.job_card:
        card = planner.read_job_card(args.job_card)
    else:
        hp = LoraHyperparameters(
            rank=args.rank,
            alpha=args.alpha,
            dropout=args.dropout,
            learning_rate=args.learning_rate,
            epochs=args.epochs,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            max_seq_length=args.max_seq_length,
            warmup_ratio=args.warmup_ratio,
        )
        card = LoraJobCardBuilder().build(
            dataset_path=args.dataset,
            job_name=args.job_name,
            base_model=args.base_model,
            output_dir=args.output_dir,
            trainer_profile=args.trainer_profile,
            dataset_format=args.dataset_format,
            hyperparameters=hp,
        )
    plan = planner.build(card)
    if args.output or args.markdown_output:
        planner.write(plan, args.output or "reports/dry-run-training-plan.json", args.markdown_output)
    if args.format == "markdown":
        print(plan.to_markdown())
    else:
        print(plan.to_json())
    return 0


def run_health(args: argparse.Namespace) -> int:
    monitor = DatasetHealthMonitor(
        history_dir=args.history_dir,
        quality_warning=args.quality_warning,
        quality_critical=args.quality_critical,
        duplicate_warning=args.duplicate_warning,
        duplicate_critical=args.duplicate_critical,
    )
    
    if args.trend:
        trend = monitor.analyze_trend(args.dataset, days=args.days)
        content = json.dumps(trend.to_dict(), indent=2, sort_keys=True)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(content + "\n", encoding="utf-8")
        print(content)
        return 0 if trend.trend_direction != "degrading" else 2
    else:
        snapshot = monitor.check_health(args.dataset, save_history=not args.no_save)
        if args.json_output or args.markdown_output:
            json_path = Path(args.json_output or "reports/health-snapshot.json")
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(snapshot.to_json() + "\n", encoding="utf-8")
            if args.markdown_output:
                md_path = Path(args.markdown_output)
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(snapshot.to_markdown() + "\n", encoding="utf-8")
        if args.format == "markdown":
            print(snapshot.to_markdown())
        else:
            print(snapshot.to_json())
        return 0 if snapshot.is_healthy else 2


def run_optimize(args: argparse.Namespace) -> int:
    optimizer = DatasetOptimizer()
    
    if args.output:
        output_path = args.output
    else:
        dataset_name = Path(args.dataset).stem
        output_path = str(Path(args.output_dir) / f"{dataset_name}-optimized.jsonl")
    
    report = optimizer.optimize(
        args.dataset,
        output_path=output_path,
        remove_duplicates=not args.skip_dedup,
        filter_low_quality=not args.skip_filter,
        quality_threshold=args.quality_threshold,
    )
    
    if args.report_json or args.report_markdown:
        optimizer.write_report(
            report,
            args.report_json or "reports/optimization.json",
            args.report_markdown,
        )
    
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    
    return 0


def run_batch(args: argparse.Namespace) -> int:
    """Run batch operation on multiple datasets"""
    if args.operation == "health":
        monitor = BatchHealthMonitor(
            quality_warning=args.quality_warning,
            quality_critical=args.quality_critical,
            duplicate_warning=args.duplicate_warning,
            duplicate_critical=args.duplicate_critical,
        )
        batch_report = monitor.check_directory(args.directory, args.pattern)
    elif args.operation == "optimize":
        optimizer = BatchOptimizer()
        batch_report = optimizer.optimize_directory(
            args.directory,
            args.output_dir,
            args.pattern,
            skip_on_error=not args.fail_on_error,
            remove_duplicates=not args.skip_dedup,
            filter_low_quality=not args.skip_filter,
            quality_threshold=args.quality_threshold,
        )
    elif args.operation == "score":
        scorer = BatchQualityScorer(
            min_record_score=args.min_record_score,
            min_average_score=args.min_average_score,
            max_failed_ratio=args.max_failed_ratio,
            min_records=args.min_records,
        )
        batch_report = scorer.score_directory(args.directory, args.pattern)
    else:
        print(f"Unknown operation: {args.operation}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(batch_report.to_json() + "\n", encoding="utf-8")
    
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(batch_report.to_markdown() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(batch_report.to_markdown())
    else:
        print(batch_report.to_json())
    
    return 0 if batch_report.failed == 0 else 1


def run_status(args: argparse.Namespace) -> int:
    """Show dataset status dashboard"""
    dashboard = StatusDashboard(
        quality_warning=args.quality_warning,
        quality_critical=args.quality_critical,
        duplicate_warning=args.duplicate_warning,
        duplicate_critical=args.duplicate_critical,
        min_average_score=args.min_average_score,
        max_failed_ratio=args.max_failed_ratio,
    )
    
    if args.all or args.directory:
        directory = args.directory or "data/datasets"
        status = dashboard.get_directory_status(directory, args.pattern)
        
        if args.json_output or args.markdown_output:
            dashboard.write_status(
                status,
                args.json_output,
                args.markdown_output,
            )
        
        if args.format == "markdown":
            print(status.to_markdown())
        else:
            print(status.to_json())
        
        return 0 if status.ready_datasets == status.total_datasets else 2
    else:
        # Single dataset status
        status = dashboard.get_status(args.dataset)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(status.to_json() + "\n", encoding="utf-8")
        
        print(status.to_json())
        return 0 if status.overall_ready else 2


def run_compare(args: argparse.Namespace) -> int:
    """Compare two datasets to analyze improvements"""
    comparator = DatasetComparator()
    
    comparison = comparator.compare(args.baseline, args.candidate)
    
    if args.json_output or args.markdown_output:
        comparator.write_comparison(
            comparison,
            args.json_output,
            args.markdown_output,
        )
    
    if args.format == "markdown":
        print(comparison.to_markdown())
    else:
        print(comparison.to_json())
    
    # Exit code based on whether candidate is an improvement
    if args.fail_on_regression and not comparison.is_improvement:
        return 2
    
    return 0


def run_version(args: argparse.Namespace) -> int:
    """Manage dataset versions"""
    manager = DatasetVersionManager(args.version_dir)
    
    if args.operation == "create":
        version = manager.create_version(
            dataset_path=args.dataset,
            version=args.version,
            message=args.message,
            author=args.author,
            tags=args.tags.split(",") if args.tags else None,
        )
        print(version.to_json())
        return 0
    
    elif args.operation == "list":
        versions = manager.list_versions(args.dataset_name)
        output = {"dataset": args.dataset_name, "versions": [v.to_dict() for v in versions]}
        print(json.dumps(output, indent=2))
        return 0
    
    elif args.operation == "rollback":
        output_path = manager.rollback(args.dataset_name, args.target_version, args.output)
        print(json.dumps({"rolled_back_to": args.target_version, "output": str(output_path)}, indent=2))
        return 0
    
    elif args.operation == "changelog":
        changelog = manager.generate_changelog(args.dataset_name, args.output)
        if not args.output:
            print(changelog)
        return 0
    
    elif args.operation == "tag":
        manager.tag_version(args.dataset_name, args.version, args.tag)
        print(json.dumps({"tagged": args.version, "tag": args.tag}, indent=2))
        return 0
    
    return 1


def run_workflow(args: argparse.Namespace) -> int:
    """Execute automated workflows"""
    engine = WorkflowEngine()
    
    if args.operation == "run":
        # Load and execute workflow
        workflow = engine.load_workflow(args.workflow_file)
        result = engine.execute(workflow)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
        
        if args.markdown_output:
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text(result.to_summary() + "\n", encoding="utf-8")
        
        if args.format == "markdown":
            print(result.to_summary())
        else:
            print(result.to_json())
        
        return 0 if result.success else 1
    
    elif args.operation == "create-standard":
        # Create standard pipeline workflow
        workflow = create_standard_pipeline()
        engine.save_workflow(workflow, args.output or "workflows/standard-pipeline.json")
        print(f"Created standard pipeline workflow at {args.output or 'workflows/standard-pipeline.json'}")
        return 0
    
    return 1


def run_trend(args: argparse.Namespace) -> int:
    """Analyze quality trends"""
    analyzer = QualityTrendAnalyzer(args.trend_dir)
    
    if args.operation == "record":
        snapshot = analyzer.record_snapshot(args.dataset)
        print(json.dumps(snapshot.to_dict(), indent=2))
        return 0
    
    elif args.operation == "analyze":
        report = analyzer.analyze_trend(args.dataset_name)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
        
        if args.markdown_output:
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
        
        if args.format == "markdown":
            print(report.to_markdown())
        else:
            print(report.to_json())
        
        return 0
    
    elif args.operation == "report":
        report = analyzer.generate_report(args.dataset_name, args.output)
        if not args.output:
            print(report)
        return 0
    
    return 1


def run_merge(args: argparse.Namespace) -> int:
    """Merge multiple datasets"""
    merger = DatasetMerger()
    
    result = merger.merge(
        source_datasets=args.sources,
        output_path=args.output,
        remove_duplicates=not args.keep_duplicates,
        preserve_source_metadata=args.preserve_metadata,
    )
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(result.to_summary())
    else:
        print(result.to_json())
    
    return 0


def run_split(args: argparse.Namespace) -> int:
    """Split dataset into parts"""
    splitter = DatasetSplitter()
    
    if args.strategy == "count":
        result = splitter.split_by_count(
            args.dataset,
            args.output_dir,
            args.split_count,
            args.prefix,
        )
    elif args.strategy == "ratio":
        # Parse ratios
        ratios = {}
        for ratio_str in args.ratios:
            name, value = ratio_str.split("=")
            ratios[name] = float(value)
        
        result = splitter.split_by_ratio(
            args.dataset,
            args.output_dir,
            ratios,
            shuffle=args.shuffle,
            seed=args.seed,
        )
    elif args.strategy == "size":
        result = splitter.split_by_size(
            args.dataset,
            args.output_dir,
            args.max_records,
            args.prefix,
        )
    else:
        print(f"Unknown strategy: {args.strategy}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(result.to_summary())
    else:
        print(result.to_json())
    
    return 0


def run_sample(args: argparse.Namespace) -> int:
    """Sample dataset using various strategies"""
    sampler = SmartSampler(seed=args.seed)
    
    if args.strategy == "random":
        result = sampler.random_sample(
            args.dataset,
            args.output,
            sample_size=args.size,
            sample_ratio=args.ratio,
        )
    elif args.strategy == "quality":
        result = sampler.quality_based_sample(
            args.dataset,
            args.output,
            args.size,
            min_quality_score=args.min_quality,
        )
    elif args.strategy == "stratified":
        result = sampler.stratified_sample(
            args.dataset,
            args.output,
            args.ratio,
            stratify_field=args.stratify_field,
        )
    elif args.strategy == "reservoir":
        result = sampler.reservoir_sample(
            args.dataset,
            args.output,
            args.size,
        )
    elif args.strategy == "diversity":
        result = sampler.diversity_sample(
            args.dataset,
            args.output,
            args.size,
            diversity_field=args.diversity_field,
        )
    elif args.strategy == "time":
        result = sampler.time_based_sample(
            args.dataset,
            args.output,
            args.ratio,
            time_field=args.time_field,
            recent_first=args.recent_first,
        )
    else:
        print(f"Unknown strategy: {args.strategy}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(result.to_summary())
    else:
        print(result.to_json())
    
    return 0


def run_profile(args: argparse.Namespace) -> int:
    """Profile dataset processing performance"""
    profiler = PerformanceProfiler()
    
    if args.operation == "pipeline":
        report = profiler.profile_full_pipeline(
            args.dataset,
            include_read=not args.skip_read,
            include_dedup=not args.skip_dedup,
            include_quality=not args.skip_quality,
        )
    elif args.operation == "read":
        profiler.profile_dataset_read(args.dataset)
        report = profiler.generate_report(args.dataset)
    elif args.operation == "dedup":
        profiler.profile_deduplication(args.dataset)
        report = profiler.generate_report(args.dataset)
    elif args.operation == "quality":
        profiler.profile_quality_scoring(args.dataset)
        report = profiler.generate_report(args.dataset)
    else:
        print(f"Unknown operation: {args.operation}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
    
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    
    return 0


def run_validate(args: argparse.Namespace) -> int:
    """Validate dataset with schema and rules"""
    validator = DatasetValidator()
    
    if args.schema:
        # Load schema from file
        with open(args.schema) as f:
            schema = json.load(f)
        report = validator.validate_with_schema(args.dataset, schema)
    else:
        # Use default rules
        if args.required_fields:
            validator.add_rule(RequiredFieldRule(args.required_fields))
        
        report = validator.validate_dataset(args.dataset, stop_on_error=args.stop_on_error)
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
    
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    
    return 0 if report.is_valid() else 1


def run_incremental(args: argparse.Namespace) -> int:
    """Incremental dataset updates"""
    updater = IncrementalUpdater(id_field=args.id_field)
    
    if args.operation == "detect":
        # Detect changes between datasets
        delta = updater.detect_changes(args.baseline, args.updated)
        
        if args.save_delta:
            updater.save_delta(delta, args.save_delta)
        
        print(delta.to_json())
        return 0
    
    elif args.operation == "apply":
        # Apply delta to dataset
        if args.delta_file:
            delta = updater.load_delta(args.delta_file)
        elif args.updated:
            delta = updater.detect_changes(args.baseline, args.updated)
        else:
            print("Error: Must specify --delta-file or --updated for apply operation")
            return 1
        
        result = updater.apply_delta(args.baseline, delta, output_path=args.output)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
        
        if args.format == "markdown":
            print(result.to_summary())
        else:
            print(result.to_json())
        
        return 0
    
    elif args.operation == "history":
        # View change history
        tracker = ChangeTracker(args.history_dir or "data/history")
        
        if args.changelog:
            changelog = tracker.generate_changelog(args.dataset_name, output_path=args.changelog)
            print(changelog)
        else:
            history = tracker.get_history(args.dataset_name)
            print(json.dumps(history, indent=2))
        
        return 0
    
    return 1


def run_catalog(args: argparse.Namespace) -> int:
    """Dataset catalog and discovery"""
    catalog = DatasetCatalog(args.index or "data/catalog.json")
    
    if args.operation == "index":
        # Index a dataset
        entry = catalog.index_dataset(
            args.dataset,
            tags=args.tags,
            metadata=json.loads(args.metadata) if args.metadata else None,
        )
        catalog.save()
        print(json.dumps(entry.to_dict(), indent=2))
        return 0
    
    elif args.operation == "search":
        # Search catalog
        results = catalog.search(
            query=args.query,
            tags=args.tags,
            min_quality=args.min_quality,
            min_records=args.min_records,
            source_repo=args.source_repo,
        )
        
        if args.format == "json":
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print(f"Found {len(results)} dataset(s):\n")
            for result in results:
                entry = result.entry
                print(f"- {entry.dataset_name} ({entry.record_count:,} records, {entry.file_size_mb:.1f} MB)")
                print(f"  Quality: {entry.quality_score or 'N/A'}, Tags: {', '.join(entry.tags)}")
                if result.match_reasons:
                    print(f"  Matches: {', '.join(result.match_reasons)}")
                print()
        
        return 0
    
    elif args.operation == "list":
        # List all datasets
        entries = catalog.list_all(sort_by=args.sort_by)
        
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in entries], indent=2))
        elif args.format == "markdown":
            print(catalog.generate_report())
        else:
            for entry in entries:
                print(f"{entry.dataset_name}: {entry.record_count:,} records, {entry.file_size_mb:.1f} MB")
        
        return 0
    
    elif args.operation == "update":
        # Update catalog entry
        catalog.update_entry(
            args.dataset,
            quality_score=args.quality_score,
            tags=args.tags,
            metadata=json.loads(args.metadata) if args.metadata else None,
        )
        catalog.save()
        print(f"Updated catalog entry for {args.dataset}")
        return 0
    
    return 1


def run_security_scan(args: argparse.Namespace) -> int:
    """Scan dataset for security issues"""
    scanner = DatasetSecurityScanner()
    
    if args.operation == "scan":
        report = scanner.scan_dataset(args.dataset, stop_on_critical=args.stop_on_critical)
    elif args.operation == "scan-field":
        report = scanner.scan_field(args.dataset, args.field)
    elif args.operation == "quick-scan":
        report = scanner.quick_scan(args.dataset, sample_size=args.sample_size)
    else:
        print(f"Unknown operation: {args.operation}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
    
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
    
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    
    # Return error code if critical issues found
    return 0 if report.is_safe() else 1


def run_export_advanced(args: argparse.Namespace) -> int:
    """Export dataset to advanced formats"""
    exporters = AdvancedExporters()
    
    if args.format == "llama3":
        result = exporters.export_llama3(args.source, args.output, system_prompt=args.system_prompt)
    elif args.format == "gemini":
        result = exporters.export_gemini(args.source, args.output)
    elif args.format == "claude":
        result = exporters.export_claude(args.source, args.output, system_prompt=args.system_prompt)
    elif args.format == "hancock_cybersecurity":
        result = exporters.export_hancock_cybersecurity(args.source, args.output)
    elif args.format == "mistral":
        result = exporters.export_mistral(args.source, args.output)
    elif args.format == "qwen":
        result = exporters.export_qwen(args.source, args.output, system_prompt=args.system_prompt)
    elif args.format == "unsloth":
        result = exporters.export_unsloth(args.source, args.output)
    elif args.format == "jsonl_conversation":
        result = exporters.export_jsonl_with_conversation(args.source, args.output)
    else:
        print(f"Unknown format: {args.format}")
        print(f"Available formats: {', '.join(get_advanced_format_names())}")
        return 1
    
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    
    print(f"Exported {result.records_exported} records to {result.output_path}")
    print(f"Format: {result.export_format}")
    
    return 0


def run_lineage(args: argparse.Namespace) -> int:
    """Generate dataset lineage visualizations"""
    visualizer = LineageVisualizer()
    
    if args.source_type == "manifest":
        visualizer.build_from_manifest(args.source)
    elif args.source_type == "catalog":
        visualizer.build_from_catalog(args.source)
    else:
        print(f"Unknown source type: {args.source_type}")
        return 1
    
    # Save in requested formats
    if args.format == "dot" or args.all_formats:
        output = args.output or "lineage.dot"
        visualizer.save_dot(output)
        print(f"Saved DOT format to {output}")
    
    if args.format == "mermaid" or args.all_formats:
        output = args.output or "lineage.mmd"
        visualizer.save_mermaid(output)
        print(f"Saved Mermaid format to {output}")
    
    if args.format == "ascii" or args.all_formats:
        output = args.output or "lineage.txt"
        visualizer.save_ascii(output)
        print(f"Saved ASCII format to {output}")
    
    if args.format == "markdown" or args.all_formats:
        output = args.output or "lineage.md"
        visualizer.save_markdown_with_mermaid(output, title=args.title or "Dataset Lineage")
        print(f"Saved Markdown with Mermaid to {output}")
    
    # Print to console if no output file
    if not args.output and not args.all_formats:
        if args.format == "dot":
            print(visualizer.to_dot())
        elif args.format == "mermaid":
            print(visualizer.to_mermaid())
        elif args.format == "ascii":
            print(visualizer.to_ascii())
        elif args.format == "markdown":
            print(visualizer.generate_markdown_with_mermaid())
    
    return 0


def run_diff(args: argparse.Namespace) -> int:
    """Generate dataset diff report"""
    diff_engine = DatasetDiffEngine()
    
    if args.operation == "diff":
        report = diff_engine.diff(args.base, args.compare, compare_content=not args.no_content_compare)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
        
        if args.markdown_output:
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
        
        if args.format == "markdown":
            print(report.to_markdown())
        else:
            print(report.to_json())
        
        return 0
    
    elif args.operation == "patch":
        # Generate patch file
        op_count = diff_engine.generate_patch(args.base, args.compare, args.output)
        print(f"Generated patch with {op_count} operations: {args.output}")
        return 0
    
    elif args.operation == "apply":
        # Apply patch file
        record_count = diff_engine.apply_patch(args.base, args.patch, args.output)
        print(f"Applied patch, output has {record_count} records: {args.output}")
        return 0
    
    elif args.operation == "find-duplicates":
        # Find duplicates between datasets
        duplicates = diff_engine.find_duplicates_between_datasets(args.base, args.compare)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(duplicates, indent=2) + "\n", encoding="utf-8")
        
        print(f"Found {len(duplicates)} duplicate records between datasets")
        for id1, id2 in duplicates[:10]:  # Show first 10
            print(f"  {id1} <-> {id2}")
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more")
        
        return 0
    
    return 1


def run_policy_template(args: argparse.Namespace) -> int:
    """Manage policy templates"""
    
    if args.operation == "list":
        templates = PolicyTemplateLibrary.list_templates()
        print(f"Available policy templates ({len(templates)}):\n")
        for template_id in templates:
            template = PolicyTemplateLibrary.get_template(template_id)
            print(f"- {template_id}: {template.name}")
            print(f"  {template.description}")
            print()
        return 0
    
    elif args.operation == "get":
        template = PolicyTemplateLibrary.get_template(args.template_id)
        
        if args.output:
            PolicyTemplateLibrary.save_template(template, args.output)
            print(f"Saved template to {args.output}")
        else:
            print(template.to_json())
        
        return 0
    
    elif args.operation == "save":
        template = PolicyTemplateLibrary.get_template(args.template_id)
        PolicyTemplateLibrary.save_template(template, args.output)
        print(f"Saved {args.template_id} to {args.output}")
        return 0
    
    return 1


def run_analytics(args: argparse.Namespace) -> int:
    """Generate dataset analytics reports"""
    analytics = DatasetAnalyticsEngine()
    
    if args.operation == "analyze":
        report = analytics.analyze(args.dataset, compute_quality=not args.skip_quality)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
        
        if args.markdown_output:
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
        
        if args.format == "markdown":
            print(report.to_markdown())
        else:
            print(report.to_json())
        
        return 0
    
    elif args.operation == "compare":
        comparison = analytics.compare_datasets(args.dataset1, args.dataset2)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
        
        print(json.dumps(comparison, indent=2))
        return 0
    
    elif args.operation == "outliers":
        outliers = analytics.find_outliers(args.dataset, threshold=args.threshold)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(outliers, indent=2) + "\n", encoding="utf-8")
        
        print(f"Found {len(outliers)} outlier records:")
        for outlier in outliers[:20]:  # Show first 20
            print(f"  {outlier['record_id']}: {outlier['type']} (z={outlier['z_score']})")
        if len(outliers) > 20:
            print(f"  ... and {len(outliers) - 20} more")
        
        return 0
    
    elif args.operation == "summary":
        summary = analytics.generate_summary_statistics(args.dataset)
        print(json.dumps(summary, indent=2))
        return 0
    
    return 1


def run_migrate(args: argparse.Namespace) -> int:
    engine = DatasetMigrationEngine()
    
    if args.operation == "migrate":
        # Load migration plan
        plan = engine.load_plan(args.plan)
        
        # Validate plan
        errors = engine.validate_plan(plan)
        if errors:
            print("Migration plan validation errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        # Execute migration
        result = engine.migrate_dataset(args.source, args.output, plan)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
        
        print(f"Migration complete: {result.migrated_records}/{result.source_records} records migrated")
        if result.failed_records > 0:
            print(f"  Failed: {result.failed_records} records")
        
        return 0 if result.failed_records == 0 else 1
    
    elif args.operation == "create-plan":
        # Create new migration plan
        plan = engine.create_simple_plan(
            plan_id=args.plan_id,
            source_schema=args.source_schema,
            target_schema=args.target_schema,
        )
        
        # Save plan
        engine.save_plan(plan, args.output)
        print(f"Created migration plan: {args.output}")
        return 0
    
    elif args.operation == "add-rule":
        # Load existing plan
        plan = engine.load_plan(args.plan)
        
        # Add rule
        rule = MigrationRule(
            rule_type=args.rule_type,
            target_field=args.target_field,
            params=json.loads(args.params) if args.params else {},
        )
        plan.add_rule(rule)
        
        # Save updated plan
        engine.save_plan(plan, args.plan)
        print(f"Added {args.rule_type} rule for field '{args.target_field}'")
        return 0
    
    return 1


def run_enhance(args: argparse.Namespace) -> int:
    engine = QualityEnhancementEngine()
    
    if args.operation == "analyze":
        report = engine.analyze_dataset(args.dataset, args.json_output)
        
        if args.markdown_output:
            # Generate markdown report
            lines = [
                f"# Quality Enhancement Report\n",
                f"**Total Records:** {report.total_records}  ",
                f"**Records with Issues:** {report.records_with_issues} ({report.records_with_issues / report.total_records * 100:.1f}%)  ",
                f"**Total Issues:** {report.total_issues}  ",
                f"**Auto-Fixable:** {report.auto_fixable_count} records  \n",
                "## Issue Summary\n",
            ]
            
            # Count by type
            issue_counts: dict[str, int] = {}
            for suggestion in report.suggestions:
                for issue in suggestion.issues:
                    issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{issue_type}**: {count} issues")
            
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text("\n".join(lines) + "\n", encoding="utf-8")
        
        if args.format == "json":
            print(report.to_json())
        else:
            print(f"Total records: {report.total_records}")
            print(f"Records with issues: {report.records_with_issues} ({report.records_with_issues / report.total_records * 100:.1f}%)")
            print(f"Total issues: {report.total_issues}")
            print(f"Auto-fixable: {report.auto_fixable_count} records")
        
        return 0
    
    elif args.operation == "auto-fix":
        fixed_count = engine.apply_auto_fixes(args.dataset, args.output)
        print(f"Applied automatic fixes to {fixed_count} records")
        print(f"Output: {args.output}")
        return 0
    
    return 1


def run_dashboard(args: argparse.Namespace) -> int:
    dashboard_engine = DatasetMetricsDashboard()
    
    if args.operation == "generate":
        dashboard = dashboard_engine.generate_dashboard(
            args.dataset,
            dataset_id=args.dataset_id or Path(args.dataset).stem,
        )
        
        # Save outputs
        if args.json_output:
            dashboard_engine.save_dashboard(dashboard, args.json_output, format="json")
        
        if args.markdown_output:
            dashboard_engine.save_dashboard(dashboard, args.markdown_output, format="markdown")
        
        # Display
        if args.format == "markdown":
            print(dashboard.to_markdown())
        else:
            print(dashboard.to_json())
        
        # Alert summary
        if dashboard.alerts:
            print(f"\n🚨 {len(dashboard.alerts)} alert(s):")
            for alert in dashboard.alerts:
                print(f"  - {alert}")
        
        return 0
    
    elif args.operation == "compare":
        # Generate both dashboards
        dashboard1 = dashboard_engine.generate_dashboard(args.dataset1, dataset_id="dataset1")
        dashboard2 = dashboard_engine.generate_dashboard(args.dataset2, dataset_id="dataset2")
        
        # Compare
        comparison = dashboard_engine.compare_dashboards(dashboard1, dashboard2)
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
        
        print(json.dumps(comparison, indent=2))
        return 0
    
    return 1


def run_backup(args: argparse.Namespace) -> int:
    backup_restore = DatasetBackupRestore(backup_dir=args.backup_dir or "data/backups")
    
    if args.operation == "create":
        # Create full backup
        metadata = backup_restore.create_full_backup(
            args.dataset,
            args.dataset_id,
            tags=json.loads(args.tags) if args.tags else None,
        )
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(metadata.to_json() + "\n", encoding="utf-8")
        
        print(f"Backup created: {metadata.backup_id}")
        print(f"Records: {metadata.record_count}")
        print(f"Size: {metadata.total_bytes} bytes")
        return 0
    
    elif args.operation == "incremental":
        # Create incremental backup
        metadata = backup_restore.create_incremental_backup(
            args.dataset,
            args.dataset_id,
            args.parent_backup_id,
            tags=json.loads(args.tags) if args.tags else None,
        )
        
        print(f"Incremental backup created: {metadata.backup_id}")
        print(f"New/changed records: {metadata.record_count}")
        return 0
    
    elif args.operation == "restore":
        # Restore backup
        result = backup_restore.restore_backup(
            args.backup_id,
            args.dataset_id,
            args.output,
            verify_checksum=not args.skip_checksum,
        )
        
        print(f"Restored {result.records_restored} records to {result.dataset_path}")
        if result.checksum_verified:
            print("✓ Checksum verified")
        return 0
    
    elif args.operation == "list":
        # List backups
        inventory = backup_restore.list_backups(args.dataset_id)
        
        if args.format == "json":
            print(inventory.to_json())
        else:
            print(f"Backups for {inventory.dataset_id}:")
            for backup in inventory.backups:
                print(f"  {backup.backup_id}: {backup.record_count} records, {backup.backup_type}, {backup.timestamp}")
        
        return 0
    
    elif args.operation == "validate":
        # Validate backup
        valid = backup_restore.validate_backup(args.backup_id, args.dataset_id)
        
        if valid:
            print(f"✓ Backup {args.backup_id} is valid")
            return 0
        else:
            print(f"✗ Backup {args.backup_id} is invalid")
            return 1
    
    elif args.operation == "delete":
        # Delete backup
        deleted = backup_restore.delete_backup(args.backup_id, args.dataset_id)
        
        if deleted:
            print(f"Deleted backup {args.backup_id}")
            return 0
        else:
            print(f"Backup {args.backup_id} not found")
            return 1
    
    elif args.operation == "cleanup":
        # Cleanup old backups
        deleted = backup_restore.cleanup_old_backups(args.dataset_id, keep_count=args.keep)
        print(f"Deleted {deleted} old backups")
        return 0
    
    return 1


def run_export_v2(args: argparse.Namespace) -> int:
    exporter = ExportFormatsV2()
    
    if args.operation == "export":
        # Export to single format
        result = exporter.export_to_format(
            args.source,
            args.output,
            args.format,
            system_prompt=args.system_prompt,
        )
        
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
        
        print(f"Exported {result.records_exported} records to {result.format_name} format")
        print(f"Output: {result.output_path}")
        return 0
    
    elif args.operation == "batch":
        # Export to multiple formats
        formats = args.formats.split(",")
        results = exporter.batch_export(args.source, args.output_dir, formats)
        
        print(f"Batch export complete: {len(results)} formats")
        for format_name, result in results.items():
            print(f"  {format_name}: {result.records_exported} records")
        
        return 0
    
    elif args.operation == "list-formats":
        # List supported formats
        formats = exporter.get_supported_formats()
        print("Supported export formats:")
        for fmt in formats:
            print(f"  - {fmt}")
        return 0
    
    return 1


def run_gate(args: argparse.Namespace) -> int:
    gate_engine = QualityGateEngine()
    
    if args.operation == "evaluate":
        # Load gate config
        if args.config:
            config = gate_engine.load_config(args.config)
        elif args.strict:
            config = gate_engine.create_standard_gate(strict=True)
        elif args.ci:
            config = gate_engine.create_ci_gate()
        else:
            config = gate_engine.create_standard_gate(strict=False)
        
        # Evaluate gate
        report = gate_engine.evaluate_gate(config, args.dataset, args.dataset_id or "dataset")
        
        # Save outputs
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(report.to_json() + "\n", encoding="utf-8")
        
        if args.markdown_output:
            Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_output).write_text(report.to_markdown() + "\n", encoding="utf-8")
        
        # Display result
        if args.format == "markdown":
            print(report.to_markdown())
        else:
            print(report.to_json())
        
        # Exit with appropriate code
        return 0 if report.gate_passed else 1
    
    elif args.operation == "create-config":
        # Create gate config
        if args.strict:
            config = gate_engine.create_standard_gate(gate_id=args.gate_id, strict=True)
        elif args.ci:
            config = gate_engine.create_ci_gate()
        else:
            config = gate_engine.create_standard_gate(gate_id=args.gate_id, strict=False)
        
        # Save config
        gate_engine.save_config(config, args.output)
        print(f"Gate config created: {args.output}")
        return 0
    
    return 1


def run_optimize(args: argparse.Namespace) -> int:
    optimizer = DatasetOptimizer(output_dir=args.output_dir)
    report = optimizer.optimize(
        dataset_path=args.dataset,
        remove_duplicates=not args.skip_dedup,
        filter_low_quality=not args.skip_filter,
        quality_threshold=args.quality_threshold,
        output_path=args.output,
    )
    if args.report_json or args.report_markdown:
        json_path = Path(args.report_json or "reports/optimization-report.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.to_json() + "\n", encoding="utf-8")
        if args.report_markdown:
            md_path = Path(args.report_markdown)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
    if args.format == "markdown":
        print(report.to_markdown())
    else:
        print(report.to_json())
    return 0 if report.status == "completed" else 1


def run_profiler(args: argparse.Namespace) -> int:
    """Profile dataset for statistical analysis"""
    profiler = DatasetProfiler()
    
    profile = profiler.profile_dataset(
        Path(args.dataset),
        dataset_id=args.dataset_id or "dataset",
        compute_tokens=args.compute_tokens,
    )
    
    # Save profile
    if args.json_output:
        profiler.save_profile(profile, Path(args.json_output), format="json")
    
    if args.markdown_output:
        profiler.save_profile(profile, Path(args.markdown_output), format="markdown")
    
    # Compare profiles if requested
    if args.compare:
        baseline_profile = profiler.profile_dataset(
            Path(args.compare),
            dataset_id="baseline",
            compute_tokens=args.compute_tokens,
        )
        comparison = profiler.compare_profiles(baseline_profile, profile)
        print(json.dumps(comparison, indent=2))
        return 0
    
    # Display profile
    if args.format == "markdown":
        print(profile.to_markdown())
    else:
        print(profile.to_json())
    
    return 0


def run_test(args: argparse.Namespace) -> int:
    """Run automated dataset tests"""
    framework = DatasetTestFramework()
    
    if args.operation == "generate":
        # Generate synthetic test dataset
        records = framework.generate_test_dataset(
            num_records=args.num_records,
            output_path=Path(args.output),
        )
        print(f"Generated {len(records)} test records: {args.output}")
        return 0
    
    elif args.operation == "validate-schema":
        # Validate schema
        test_case = framework.run_schema_tests(
            Path(args.dataset),
            required_fields=args.required_fields.split(",") if args.required_fields else ["id", "content"],
        )
        
        print(f"Schema validation: {'PASSED' if test_case.passed else 'FAILED'}")
        if not test_case.passed:
            print(f"Error: {test_case.error_message}")
        
        return 0 if test_case.passed else 1
    
    elif args.operation == "regression":
        # Run regression tests
        test_case = framework.run_regression_tests(
            Path(args.baseline),
            Path(args.current),
        )
        
        print(f"Regression test: {'PASSED' if test_case.passed else 'FAILED'}")
        if not test_case.passed:
            print(f"Error: {test_case.error_message}")
        
        return 0 if test_case.passed else 1
    
    elif args.operation == "property":
        # Run property tests
        # Define property function based on property name
        if args.property_name == "has_content":
            prop_func = lambda r: bool(r.get("content", "").strip())
        elif args.property_name == "has_id":
            prop_func = lambda r: "id" in r
        elif args.property_name == "quality_above_threshold":
            threshold = args.property_threshold or 70.0
            prop_func = lambda r: r.get("quality_score", 0.0) >= threshold
        else:
            print(f"Unknown property: {args.property_name}")
            return 1
        
        test_case = framework.run_property_tests(
            Path(args.dataset),
            args.property_name,
            prop_func,
        )
        
        print(f"Property test '{args.property_name}': {'PASSED' if test_case.passed else 'FAILED'}")
        if not test_case.passed:
            print(f"Error: {test_case.error_message}")
        
        return 0 if test_case.passed else 1
    
    return 1


def run_monitor(args: argparse.Namespace) -> int:
    """Monitor dataset health"""
    
    if args.operation == "health":
        # Perform health check
        config = MonitoringConfig(
            dataset_id=args.dataset_id or "dataset",
            quality_threshold=args.quality_threshold,
            min_record_count=args.min_record_count,
            max_age_hours=args.max_age_hours,
        )
        
        monitor = DatasetMonitor(config)
        status = monitor.check_health(Path(args.dataset))
        
        # Save status
        if args.json_output:
            monitor.save_health_status(status, Path(args.json_output))
        
        # Display status
        print(status.to_json())
        
        return 0 if status.overall_status == "healthy" else 1
    
    elif args.operation == "dashboard":
        # Generate monitoring dashboard
        config = MonitoringConfig(
            dataset_id=args.dataset_id or "dataset",
            quality_threshold=args.quality_threshold,
            min_record_count=args.min_record_count,
        )
        
        monitor = DatasetMonitor(config)
        # Perform initial health check to populate metrics
        monitor.check_health(Path(args.dataset))
        
        return 0
    
    return 1


def run_sync(args: argparse.Namespace) -> int:
    """Synchronize datasets across environments"""
    synchronizer = DatasetSynchronizer()
    
    # Determine conflict resolution strategy
    resolution = ConflictResolution.NEWEST_WINS
    if args.conflict_resolution == "source":
        resolution = ConflictResolution.SOURCE_WINS
    elif args.conflict_resolution == "target":
        resolution = ConflictResolution.TARGET_WINS
    
    # Perform sync operation
    if args.bidirectional:
        result = synchronizer.bidirectional_sync(
            Path(args.source),
            Path(args.target),
            resolution=resolution,
        )
    else:
        result = synchronizer.sync(
            Path(args.source),
            Path(args.target),
            resolution=resolution,
        )
    
    # Save report if requested
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
    
    # Display results
    print(f"Sync complete: {result.added_records} added, {result.updated_records} updated, {result.deleted_records} deleted")
    print(f"Conflicts resolved: {result.conflicts_resolved}")
    
    return 0


def run_transform(args: argparse.Namespace) -> int:
    """Transform datasets using ETL pipelines"""
    transformer = DatasetTransformer()
    
    if args.operation == "apply":
        # Load pipeline and apply transformation
        pipeline = transformer.load_pipeline(Path(args.pipeline))
        result = transformer.apply_pipeline(
            Path(args.source),
            Path(args.output),
            pipeline,
        )
        
        # Save report
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(result.to_json() + "\n", encoding="utf-8")
        
        print(f"Transformation complete: {result.input_records} → {result.output_records} records")
        print(f"Filtered: {result.filtered_records}, Transformed fields: {result.transformed_fields}")
        
        return 0 if result.success else 1
    
    elif args.operation == "create-standard":
        # Create standard ETL pipeline
        pipeline = transformer.create_standard_pipeline(args.pipeline_id or "standard_etl")
        transformer.save_pipeline(pipeline, Path(args.output))
        
        print(f"Created standard pipeline: {args.output}")
        return 0
    
    return 1


def run_recommend(args: argparse.Namespace) -> int:
    """Generate dataset configuration recommendations"""
    recommender = DatasetRecommender()
    
    if args.operation == "generate":
        # Generate recommendations
        report = recommender.generate_recommendations(Path(args.dataset))
        
        # Save report
        if args.output:
            recommender.save_recommendations(report, Path(args.output))
        
        # Display summary
        if args.format == "markdown":
            print(f"# Dataset Recommendations for {report.dataset_path}\n")
            print(f"## Summary\n")
            print(f"- Total recommendations: {report.summary['total_recommendations']}")
            print(f"- High impact: {report.summary['high_impact']}")
            print(f"- Medium impact: {report.summary['medium_impact']}")
            print(f"- Low impact: {report.summary['low_impact']}")
            print(f"- Avg confidence: {report.summary['avg_confidence']:.2f}\n")
            print(f"## Recommendations\n")
            for rec in report.recommendations:
                print(f"### {rec.category.title()}: {rec.parameter}")
                print(f"- Current: {rec.current_value}")
                print(f"- Recommended: {rec.recommended_value}")
                print(f"- Impact: {rec.impact}")
                print(f"- Reason: {rec.score.reason}\n")
        else:
            print(report.to_json())
        
        return 0
    
    elif args.operation == "apply":
        # Load and apply recommendations
        report = recommender.load_recommendations(Path(args.report))
        
        # Create config from recommendations
        current_config = json.loads(args.config) if args.config else {}
        new_config = recommender.apply_recommendations(
            report,
            current_config,
            impact_threshold=args.impact_threshold or "medium",
        )
        
        # Save updated config
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(new_config, indent=2) + "\n", encoding="utf-8")
        
        print(f"Applied recommendations with impact >= {args.impact_threshold or 'medium'}")
        print(json.dumps(new_config, indent=2))
        
        return 0
    
    return 1


def run_collaborate(args: argparse.Namespace) -> int:
    """Manage dataset collaboration sessions"""
    engine = DatasetCollaborationEngine()
    
    if args.operation == "create":
        # Create new collaboration session
        owner = CollaboratorInfo(
            user_id=args.user_id or "owner",
            username=args.username or "owner",
            email=args.email or "owner@example.com",
            role="owner",
            joined_at=json.dumps({"timestamp": "now"}),
        )
        
        session = engine.create_session(Path(args.dataset), owner)
        
        # Save session
        if args.output:
            engine.save_session(session.session_id, Path(args.output))
        
        print(f"Created session: {session.session_id}")
        print(session.to_json())
        
        return 0
    
    elif args.operation == "stats":
        # Load session and show stats
        session = engine.load_session(Path(args.session))
        stats = engine.get_collaboration_stats(session.session_id)
        
        print(json.dumps(stats, indent=2))
        
        return 0
    
    return 1


def run_compliance(args: argparse.Namespace) -> int:
    """Check dataset compliance with regulations"""
    tracker = DatasetComplianceTracker()
    
    if args.operation == "check":
        # Parse regulations
        regulations = [ComplianceRegulation(r) for r in args.regulations.split(",")]
        
        # Load metadata if provided
        metadata = {}
        if args.metadata:
            metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
        
        # Run compliance check
        report = tracker.check_compliance(
            Path(args.dataset),
            regulations,
            metadata,
        )
        
        # Save report
        if args.output:
            tracker.save_report(report, Path(args.output))
        
        # Display summary
        print(f"Compliance Score: {report.summary['compliance_score']:.2%}")
        print(f"Total Checks: {report.summary['total_checks']}")
        print(f"Compliant: {report.summary['compliant']}")
        print(f"Non-Compliant: {report.summary['non_compliant']}")
        print(f"Partially Compliant: {report.summary['partially_compliant']}")
        
        if args.json_output:
            print("\nFull Report:")
            print(report.to_json())
        
        return 0 if report.summary['compliance_score'] >= 0.8 else 1
    
    elif args.operation == "remediate":
        # Load report and generate remediation plan
        report = tracker.load_report(Path(args.report))
        plan = tracker.get_remediation_plan(report)
        
        print("Remediation Plan:\n")
        
        if plan["critical"]:
            print("CRITICAL (Must Fix):")
            for item in plan["critical"]:
                print(f"  - {item}")
            print()
        
        if plan["important"]:
            print("IMPORTANT (Should Fix):")
            for item in plan["important"]:
                print(f"  - {item}")
            print()
        
        if plan["recommended"]:
            print("RECOMMENDED (Nice to Fix):")
            for item in plan["recommended"]:
                print(f"  - {item}")
        
        return 0
    
    return 1


def run_cache(args: argparse.Namespace) -> int:
    """Manage dataset caching and performance optimization"""
    optimizer = DatasetCacheOptimizer(
        max_memory_mb=args.max_memory_mb,
        max_disk_mb=args.max_disk_mb,
    )
    
    if args.operation == "enable":
        # Cache dataset
        cache_key = optimizer.cache_dataset(
            Path(args.dataset),
            use_disk=args.use_disk,
        )
        
        print(f"Dataset cached with key: {cache_key}")
        
        return 0
    
    elif args.operation == "stats":
        # Show cache statistics
        stats = optimizer.get_cache_statistics()
        
        print("Cache Statistics:")
        print(json.dumps(stats, indent=2))
        
        return 0
    
    elif args.operation == "clear":
        # Clear cache
        optimizer.clear_all_cache()
        
        print("Cache cleared")
        
        return 0
    
    elif args.operation == "recommend":
        # Recommend cache size
        recommendations = optimizer.recommend_cache_size(
            Path(args.dataset),
            target_hit_rate=args.target_hit_rate,
        )
        
        print("Cache Recommendations:")
        print(json.dumps(recommendations, indent=2))
        
        return 0
    
    return 1


def run_schedule(args: argparse.Namespace) -> int:
    """Manage scheduled dataset tasks"""
    scheduler = DatasetScheduler()
    
    if args.operation == "create":
        # Create scheduled task
        task_type = TaskType(args.task_type)
        schedule_type = ScheduleType(args.schedule_type)
        
        # Parse schedule config
        schedule_config = json.loads(args.schedule_config) if args.schedule_config else {}
        
        # Parse params
        params = json.loads(args.params) if args.params else {}
        
        task = scheduler.create_task(
            task_id=args.task_id,
            task_type=task_type,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            dataset_path=Path(args.dataset),
            params=params,
        )
        
        if args.output:
            scheduler.save_tasks(Path(args.output))
        
        print(f"Created task: {task.task_id}")
        print(json.dumps(task.to_dict(), indent=2))
        
        return 0
    
    elif args.operation == "list":
        # Load and list tasks
        if args.tasks_file:
            scheduler.load_tasks(Path(args.tasks_file))
        
        print("Scheduled Tasks:")
        for task in scheduler.tasks.values():
            status = "Enabled" if task.enabled else "Disabled"
            print(f"  {task.task_id}: {task.task_type.value} ({status})")
            print(f"    Next run: {task.next_run or 'N/A'}")
        
        return 0
    
    elif args.operation == "run":
        # Load tasks and run due tasks
        if args.tasks_file:
            scheduler.load_tasks(Path(args.tasks_file))
        
        executions = scheduler.run_due_tasks()
        
        print(f"Executed {len(executions)} tasks:")
        for execution in executions:
            status = execution.status.value
            print(f"  {execution.task_id}: {status}")
        
        return 0
    
    elif args.operation == "stats":
        # Show task statistics
        if args.tasks_file:
            scheduler.load_tasks(Path(args.tasks_file))
        
        stats = scheduler.get_task_statistics(args.task_id)
        print(json.dumps(stats, indent=2))
        
        return 0
    
    return 1


def run_notify(args: argparse.Namespace) -> int:
    """Manage dataset notifications"""
    notifier = DatasetNotificationSystem()
    
    if args.operation == "create-rule":
        # Create notification rule
        event_type = EventType(args.event_type)
        notification_type = NotificationType(args.notification_type)
        channels = [NotificationChannel(c) for c in args.channels.split(",")]
        recipients = args.recipients.split(",") if args.recipients else []
        
        rule = notifier.create_rule(
            rule_id=args.rule_id,
            event_type=event_type,
            notification_type=notification_type,
            channels=channels,
            recipients=recipients,
        )
        
        if args.output:
            notifier.save_rules(Path(args.output))
        
        print(f"Created rule: {rule.rule_id}")
        print(json.dumps(rule.to_dict(), indent=2))
        
        return 0
    
    elif args.operation == "emit":
        # Emit event
        if args.rules_file:
            notifier.load_rules(Path(args.rules_file))
        
        event_type = EventType(args.event_type)
        metadata = json.loads(args.metadata) if args.metadata else {}
        
        event = notifier.emit_event(
            event_type=event_type,
            dataset_path=Path(args.dataset),
            metadata=metadata,
        )
        
        print(f"Emitted event: {event.event_id}")
        print(f"Type: {event.event_type.value}")
        
        return 0
    
    elif args.operation == "list-events":
        # List recent events
        events = notifier.get_events(limit=args.limit)
        
        print(f"Recent Events ({len(events)}):")
        for event in events:
            print(f"  {event.event_id}: {event.event_type.value} - {event.timestamp}")
        
        return 0
    
    elif args.operation == "stats":
        # Show notification statistics
        stats = notifier.get_statistics()
        print(json.dumps(stats, indent=2))
        
        return 0
    
    return 1


def run_webhook(args: argparse.Namespace) -> int:
    """Manage dataset webhooks"""
    webhook_manager = DatasetWebhookManager()
    
    if args.operation == "create":
        # Create webhook endpoint
        events = [WebhookEvent(e) for e in args.events.split(",")]
        
        endpoint = webhook_manager.create_endpoint(
            endpoint_id=args.endpoint_id,
            url=args.url,
            events=events,
            secret=args.secret,
        )
        
        if args.output:
            webhook_manager.save_endpoints(Path(args.output))
        
        print(f"Created webhook endpoint: {endpoint.endpoint_id}")
        print(json.dumps(endpoint.to_dict(), indent=2))
        
        return 0
    
    elif args.operation == "trigger":
        # Trigger webhook
        if args.endpoints_file:
            webhook_manager.load_endpoints(Path(args.endpoints_file))
        
        event = WebhookEvent(args.event)
        data = json.loads(args.data) if args.data else {}
        
        deliveries = webhook_manager.trigger_webhook(
            event=event,
            dataset_path=Path(args.dataset),
            data=data,
        )
        
        print(f"Triggered {len(deliveries)} webhook(s)")
        for delivery in deliveries:
            print(f"  {delivery.endpoint_id}: {delivery.status.value}")
        
        return 0
    
    elif args.operation == "test":
        # Test webhook endpoint
        if args.endpoints_file:
            webhook_manager.load_endpoints(Path(args.endpoints_file))
        
        delivery = webhook_manager.test_endpoint(args.endpoint_id)
        
        print(f"Test delivery sent: {delivery.status.value}")
        print(json.dumps(delivery.to_dict(), indent=2))
        
        return 0
    
    elif args.operation == "stats":
        # Show webhook statistics
        if args.endpoint_id:
            stats = webhook_manager.get_endpoint_statistics(args.endpoint_id)
        else:
            stats = webhook_manager.get_statistics()
        
        print(json.dumps(stats, indent=2))
        
        return 0
    
    return 1
        
        dashboard = monitor.generate_dashboard()
        print(json.dumps(dashboard, indent=2))
        return 0
    
    elif args.operation == "alerts":
        # Check for alerts
        config = MonitoringConfig(
            dataset_id=args.dataset_id or "dataset",
            quality_threshold=args.quality_threshold,
            min_record_count=args.min_record_count,
        )
        
        monitor = DatasetMonitor(config)
        metrics = monitor._compute_metrics(Path(args.dataset))
        alerts = monitor.check_alerts(metrics)
        
        print(f"Found {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  [{alert.severity.upper()}] {alert.alert_name}: {alert.message}")
        
        return 0 if len(alerts) == 0 else 1
    
    return 1


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="peachtree", description="Recursive learning-tree dataset engine")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="create a recursive learning tree")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--project", required=True)
    plan.add_argument("--depth", type=int, default=2)
    plan.add_argument("--output")
    plan.set_defaults(func=run_plan)

    ingest = sub.add_parser("ingest-local", help="ingest a local repository into source JSONL")
    ingest.add_argument("--repo", required=True)
    ingest.add_argument("--repo-name", required=True)
    ingest.add_argument("--license", default="unknown")
    ingest.add_argument("--output", required=True)
    ingest.set_defaults(func=run_ingest_local)

    build = sub.add_parser("build", help="build training JSONL from source JSONL")
    build.add_argument("--source", required=True)
    build.add_argument("--dataset", required=True)
    build.add_argument("--manifest", required=True)
    build.add_argument("--domain", default="general")
    build.add_argument("--allow-unknown-license", action="store_true", default=True)
    build.set_defaults(func=run_build)

    audit = sub.add_parser("audit", help="audit generated dataset JSONL")
    audit.add_argument("--dataset", required=True)
    audit.add_argument("--domain", default="general")
    audit.set_defaults(func=run_audit)

    github_owned = sub.add_parser("github-owned", help="inventory owned/access-authorized GitHub repositories")
    github_owned.add_argument("--owner", help="GitHub owner/org for gh repo list")
    github_owned.add_argument("--limit", type=int, default=25)
    github_owned.add_argument("--from-json", help="read gh repo list JSON from file instead of calling gh")
    github_owned.add_argument("--output", default="data/manifests/github-owned-repos.jsonl")
    github_owned.add_argument("--include-private", action="store_true", default=True)
    github_owned.add_argument("--include-archived", action="store_true")
    github_owned.set_defaults(func=run_github_owned)

    github_plan = sub.add_parser("github-plan", help="create reviewable clone and dataset scripts from owned repo inventory")
    github_plan.add_argument("--inventory", required=True)
    github_plan.add_argument("--clone-root", default="data/repos")
    github_plan.add_argument("--clone-script", default="scripts/clone_owned_repos.sh")
    github_plan.add_argument("--dataset-script", default="scripts/build_owned_datasets.sh")
    github_plan.set_defaults(func=run_github_plan)

    graph = sub.add_parser("graph", help="build cross-repo dependency graph")
    graph.add_argument("--inventory", help="owned repo inventory JSONL")
    graph.add_argument("--dataset-dir", default="data/datasets")
    graph.add_argument("--manifest-dir", default="data/manifests")
    graph.add_argument("--format", choices=["json", "mermaid", "dot"], default="json")
    graph.add_argument("--output")
    graph.set_defaults(func=run_graph)

    lineage = sub.add_parser("lineage", help="build dataset lineage map")
    lineage.add_argument("--dataset", required=True)
    lineage.add_argument("--manifest")
    lineage.add_argument("--format", choices=["json", "markdown"], default="json")
    lineage.add_argument("--output")
    lineage.set_defaults(func=run_lineage)

    ecosystem = sub.add_parser("ecosystem", help="build combined ecosystem graph and lineage summary")
    ecosystem.add_argument("--inventory", help="owned repo inventory JSONL")
    ecosystem.add_argument("--dataset-dir", default="data/datasets")
    ecosystem.add_argument("--manifest-dir", default="data/manifests")
    ecosystem.add_argument("--output")
    ecosystem.set_defaults(func=run_ecosystem)

    export_formats = sub.add_parser("export-formats", help="list supported model export formats")
    export_formats.set_defaults(func=run_export_formats)

    export = sub.add_parser("export", help="export PeachTree dataset JSONL to a model training schema")
    export.add_argument("--source", required=True, help="PeachTree dataset JSONL")
    export.add_argument("--output", required=True, help="output JSONL path")
    export.add_argument("--format", choices=list(export_format_names()), required=True)
    export.add_argument("--system-prompt", default="You are a helpful, safe, and precise AI assistant.")
    export.add_argument("--limit", type=int)
    export.add_argument("--no-metadata", action="store_true")
    export.set_defaults(func=run_export)

    validate_export = sub.add_parser("validate-export", help="validate exported model JSONL")
    validate_export.add_argument("--path", required=True)
    validate_export.add_argument("--format", choices=list(export_format_names()), required=True)
    validate_export.set_defaults(func=run_validate_export)

    diff = sub.add_parser("diff", help="compare baseline and candidate dataset JSONL files")
    diff.add_argument("--baseline", required=True)
    diff.add_argument("--candidate", required=True)
    diff.add_argument("--format", choices=["json", "markdown"], default="json")
    diff.add_argument("--json-output")
    diff.add_argument("--markdown-output")
    diff.add_argument("--fail-on-review", action="store_true")
    diff.set_defaults(func=run_diff)

    update_plan = sub.add_parser("update-plan", help="create a scheduled dataset update plan")
    update_plan.add_argument("--repo", required=True, help="local repository path used by CI checkout or local run")
    update_plan.add_argument("--repo-name", required=True)
    update_plan.add_argument("--name", default="peachtree-dataset-update")
    update_plan.add_argument("--format", choices=["json", "markdown"], default="json")
    update_plan.add_argument("--output")
    update_plan.add_argument("--markdown-output")
    update_plan.set_defaults(func=run_update_plan)

    review_report = sub.add_parser("review-report", help="render a dataset update review report from a plan")
    review_report.add_argument("--plan", required=True)
    review_report.add_argument("--output")
    review_report.set_defaults(func=run_review_report)

    score = sub.add_parser("score", help="score a PeachTree dataset for quality")
    score.add_argument("--dataset", required=True)
    score.add_argument("--format", choices=["json", "markdown"], default="json")
    score.add_argument("--json-output")
    score.add_argument("--markdown-output")
    score.add_argument("--min-record-score", type=int, default=70)
    score.add_argument("--min-average-score", type=int, default=80)
    score.add_argument("--max-failed-ratio", type=float, default=0.10)
    score.add_argument("--min-records", type=int, default=1)
    score.add_argument("--summary-only", action="store_true")
    score.add_argument("--fail-on-gate", action="store_true")
    score.set_defaults(func=run_score)

    dedup = sub.add_parser("dedup", help="deduplicate a PeachTree dataset")
    dedup.add_argument("--source", required=True)
    dedup.add_argument("--output", required=True)
    dedup.add_argument("--format", choices=["json", "markdown"], default="json")
    dedup.add_argument("--report-json")
    dedup.add_argument("--report-markdown")
    dedup.set_defaults(func=run_dedup)

    readiness = sub.add_parser("readiness", help="evaluate dataset training readiness gates")
    readiness.add_argument("--dataset", required=True)
    readiness.add_argument("--output")
    readiness.add_argument("--min-record-score", type=int, default=70)
    readiness.add_argument("--min-average-score", type=int, default=80)
    readiness.add_argument("--max-failed-ratio", type=float, default=0.10)
    readiness.add_argument("--min-records", type=int, default=1)
    readiness.add_argument("--max-duplicate-ratio", type=float, default=0.05)
    readiness.add_argument("--fail-on-gate", action="store_true")
    readiness.set_defaults(func=run_readiness)

    policy_pack = sub.add_parser("policy-pack", help="list, show, or evaluate dataset policy packs")
    policy_pack.add_argument("--list", action="store_true", help="list built-in policy packs")
    policy_pack.add_argument("--show", help="show one built-in policy pack")
    policy_pack.add_argument("--dataset")
    policy_pack.add_argument("--pack", default="open-safe")
    policy_pack.add_argument("--format", choices=["json", "markdown"], default="json")
    policy_pack.add_argument("--json-output")
    policy_pack.add_argument("--markdown-output")
    policy_pack.add_argument("--fail-on-gate", action="store_true")
    policy_pack.set_defaults(func=run_policy_pack)

    license_gate = sub.add_parser("license-gate", help="evaluate dataset license compliance gates")
    license_gate.add_argument("--dataset", required=True)
    license_gate.add_argument("--allow", help="comma-separated allowed license IDs")
    license_gate.add_argument("--deny", help="comma-separated denied license IDs")
    license_gate.add_argument("--allow-unknown", action="store_true")
    license_gate.add_argument("--format", choices=["json", "markdown"], default="json")
    license_gate.add_argument("--json-output")
    license_gate.add_argument("--markdown-output")
    license_gate.add_argument("--summary-only", action="store_true")
    license_gate.add_argument("--fail-on-gate", action="store_true")
    license_gate.set_defaults(func=run_license_gate)

    model_card = sub.add_parser("model-card", help="generate a dataset model card from PeachTree reports")
    model_card.add_argument("--dataset", required=True)
    model_card.add_argument("--model-name", required=True)
    model_card.add_argument("--output", required=True)
    model_card.add_argument("--format", choices=["markdown", "json"], default="markdown")
    model_card.add_argument("--manifest")
    model_card.add_argument("--quality-report")
    model_card.add_argument("--license-report")
    model_card.add_argument("--policy-report")
    model_card.add_argument("--intended-use", default="Safe downstream AI model training review.")
    model_card.set_defaults(func=run_model_card)

    registry = sub.add_parser("registry", help="build a local dataset/release artifact registry")
    registry.add_argument("paths", nargs="*", help="files or directories to register")
    registry.add_argument("--name", default="peachtree-release")
    registry.add_argument("--version", default="0.8.0")
    registry.add_argument("--format", choices=["json", "markdown"], default="json")
    registry.add_argument("--output")
    registry.add_argument("--markdown-output")
    registry.set_defaults(func=run_registry)

    sign = sub.add_parser("sign", help="sign or verify an artifact using local HMAC-SHA256 metadata")
    sign.add_argument("--artifact", required=True)
    sign.add_argument("--key", required=True, help="local signing key; prefer CI secret or local env var expansion")
    sign.add_argument("--key-id", default="local-dev-key")
    sign.add_argument("--output")
    sign.add_argument("--verify", action="store_true")
    sign.add_argument("--signature")
    sign.set_defaults(func=run_sign)

    sbom = sub.add_parser("sbom", help="generate a PeachTree SBOM/provenance manifest")
    sbom.add_argument("paths", nargs="*", help="files to include when no registry is supplied")
    sbom.add_argument("--registry")
    sbom.add_argument("--name", default="peachtree-release")
    sbom.add_argument("--version", default="0.8.0")
    sbom.add_argument("--format", choices=["json", "markdown"], default="json")
    sbom.add_argument("--output")
    sbom.add_argument("--markdown-output")
    sbom.set_defaults(func=run_sbom)

    bundle = sub.add_parser("bundle", help="create a PeachTree release zip bundle")
    bundle.add_argument("artifacts", nargs="+")
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--name", default="peachtree-release")
    bundle.add_argument("--version", default="0.8.0")
    bundle.add_argument("--signing-key")
    bundle.add_argument("--signing-key-id", default="local-dev-key")
    bundle.add_argument("--report")
    bundle.add_argument("--format", choices=["json", "markdown"], default="json")
    bundle.set_defaults(func=run_bundle)

    handoff = sub.add_parser("handoff", help="create a trainer handoff manifest")
    handoff.add_argument("--dataset", required=True)
    handoff.add_argument("--model-name", required=True)
    handoff.add_argument("--base-model", required=True)
    handoff.add_argument("--trainer-profile", default="unsloth")
    handoff.add_argument("--dataset-format", default="chatml")
    handoff.add_argument("--registry")
    handoff.add_argument("--sbom")
    handoff.add_argument("--model-card")
    handoff.add_argument("--quality-report")
    handoff.add_argument("--policy-report")
    handoff.add_argument("--license-report")
    handoff.add_argument("--release-bundle")
    handoff.add_argument("--format", choices=["json", "markdown"], default="json")
    handoff.add_argument("--output")
    handoff.add_argument("--markdown-output")
    handoff.set_defaults(func=run_handoff)

    lora_card = sub.add_parser("lora-card", help="create a LoRA job card without launching training")
    lora_card.add_argument("--dataset", required=True)
    lora_card.add_argument("--job-name", required=True)
    lora_card.add_argument("--base-model", required=True)
    lora_card.add_argument("--output-dir", required=True)
    lora_card.add_argument("--trainer-profile", default="unsloth")
    lora_card.add_argument("--dataset-format", default="chatml")
    lora_card.add_argument("--rank", type=int, default=16)
    lora_card.add_argument("--alpha", type=int, default=32)
    lora_card.add_argument("--dropout", type=float, default=0.05)
    lora_card.add_argument("--learning-rate", type=float, default=2e-4)
    lora_card.add_argument("--epochs", type=float, default=1.0)
    lora_card.add_argument("--batch-size", type=int, default=2)
    lora_card.add_argument("--gradient-accumulation-steps", type=int, default=4)
    lora_card.add_argument("--max-seq-length", type=int, default=4096)
    lora_card.add_argument("--warmup-ratio", type=float, default=0.03)
    lora_card.add_argument("--format", choices=["json", "markdown"], default="json")
    lora_card.add_argument("--output")
    lora_card.add_argument("--markdown-output")
    lora_card.set_defaults(func=run_lora_card)

    train_plan = sub.add_parser("train-plan", help="create a dry-run training launch plan")
    train_plan.add_argument("--job-card")
    train_plan.add_argument("--dataset")
    train_plan.add_argument("--job-name", default="peachtree-lora-job")
    train_plan.add_argument("--base-model", default="mistralai/Mistral-7B-Instruct-v0.3")
    train_plan.add_argument("--output-dir", default="outputs/lora")
    train_plan.add_argument("--trainer-profile", default="unsloth")
    train_plan.add_argument("--dataset-format", default="chatml")
    train_plan.add_argument("--rank", type=int, default=16)
    train_plan.add_argument("--alpha", type=int, default=32)
    train_plan.add_argument("--dropout", type=float, default=0.05)
    train_plan.add_argument("--learning-rate", type=float, default=2e-4)
    train_plan.add_argument("--epochs", type=float, default=1.0)
    train_plan.add_argument("--batch-size", type=int, default=2)
    train_plan.add_argument("--gradient-accumulation-steps", type=int, default=4)
    train_plan.add_argument("--max-seq-length", type=int, default=4096)
    train_plan.add_argument("--warmup-ratio", type=float, default=0.03)
    train_plan.add_argument("--format", choices=["json", "markdown"], default="json")
    train_plan.add_argument("--output")
    train_plan.add_argument("--markdown-output")
    train_plan.set_defaults(func=run_train_plan)

    health = sub.add_parser("health", help="monitor dataset health and quality trends")
    health.add_argument("--dataset", required=True, help="dataset JSONL file to monitor")
    health.add_argument("--trend", action="store_true", help="analyze trend over time instead of single snapshot")
    health.add_argument("--days", type=int, default=7, help="days of history for trend analysis")
    health.add_argument("--history-dir", default="data/health-history", help="directory for health history storage")
    health.add_argument("--quality-warning", type=float, default=75.0, help="quality score warning threshold")
    health.add_argument("--quality-critical", type=float, default=60.0, help="quality score critical threshold")
    health.add_argument("--duplicate-warning", type=float, default=0.15, help="duplicate ratio warning threshold")
    health.add_argument("--duplicate-critical", type=float, default=0.30, help="duplicate ratio critical threshold")
    health.add_argument("--no-save", action="store_true", help="do not save snapshot to history")
    health.add_argument("--format", choices=["json", "markdown"], default="json")
    health.add_argument("--output", help="output file (for trend analysis)")
    health.add_argument("--json-output", help="JSON output file (for snapshot)")
    health.add_argument("--markdown-output", help="markdown output file (for snapshot)")
    health.set_defaults(func=run_health)

    optimize = sub.add_parser("optimize", help="optimize dataset by removing duplicates and low-quality records")
    optimize.add_argument("--dataset", required=True, help="source dataset JSONL file")
    optimize.add_argument("--output", help="output optimized dataset file")
    optimize.add_argument("--output-dir", default="data/optimized", help="output directory for optimized datasets")
    optimize.add_argument("--skip-dedup", action="store_true", help="skip duplicate removal")
    optimize.add_argument("--skip-filter", action="store_true", help="skip quality filtering")
    optimize.add_argument("--quality-threshold", type=int, default=60, help="minimum quality score to keep records")
    optimize.add_argument("--format", choices=["json", "markdown"], default="json")
    optimize.add_argument("--report-json", help="JSON report output file")
    optimize.add_argument("--report-markdown", help="markdown report output file")
    optimize.set_defaults(func=run_optimize)

    batch = sub.add_parser("batch", help="batch process multiple datasets in directory")
    batch.add_argument("operation", choices=["health", "optimize", "score"], help="batch operation to perform")
    batch.add_argument("--directory", required=True, help="directory containing datasets")
    batch.add_argument("--pattern", default="*.jsonl", help="file pattern to match (default: *.jsonl)")
    batch.add_argument("--output-dir", default="data/batch-output", help="output directory for batch operations")
    batch.add_argument("--quality-warning", type=float, default=75.0, help="quality score warning threshold")
    batch.add_argument("--quality-critical", type=float, default=60.0, help="quality score critical threshold")
    batch.add_argument("--duplicate-warning", type=float, default=0.15, help="duplicate ratio warning threshold")
    batch.add_argument("--duplicate-critical", type=float, default=0.30, help="duplicate ratio critical threshold")
    batch.add_argument("--skip-dedup", action="store_true", help="skip duplicate removal (optimize only)")
    batch.add_argument("--skip-filter", action="store_true", help="skip quality filtering (optimize only)")
    batch.add_argument("--quality-threshold", type=int, default=60, help="minimum quality score (optimize/score)")
    batch.add_argument("--min-record-score", type=int, default=60, help="minimum record score (score only)")
    compare = sub.add_parser("compare", help="compare two datasets to analyze improvements")
    compare.add_argument("--baseline", required=True, help="baseline dataset for comparison")
    compare.add_argument("--candidate", required=True, help="candidate dataset to compare")
    compare.add_argument("--format", choices=["json", "markdown"], default="json")
    compare.add_argument("--json-output", help="JSON output file")
    compare.add_argument("--markdown-output", help="markdown output file")
    compare.add_argument("--fail-on-regression", action="store_true", help="exit code 2 if no improvement")
    compare.set_defaults(func=run_compare)

    version = sub.add_parser("version", help="manage dataset versions with snapshots and rollback")
    version.add_argument("operation", choices=["create", "list", "rollback", "changelog", "tag"])
    version.add_argument("--dataset", help="dataset file path (for create)")
    version.add_argument("--dataset-name", help="dataset name (for list/rollback/changelog/tag)")
    version.add_argument("--version", help="version string (e.g., v1.0.0)")
    version.add_argument("--message", help="version commit message (for create)")
    version.add_argument("--author", default="peachtree", help="version author")
    version.add_argument("--tags", help="comma-separated tags (e.g., stable,production)")
    version.add_argument("--tag", help="single tag to add (for tag operation)")
    version.add_argument("--target-version", help="version to rollback to")
    version.add_argument("--output", help="output file path")
    version.add_argument("--version-dir", default=".peachtree/versions", help="version storage directory")
    version.set_defaults(func=run_version)

    workflow = sub.add_parser("workflow", help="execute automated dataset processing workflows")
    workflow.add_argument("operation", choices=["run", "create-standard"])
    workflow.add_argument("--workflow-file", help="workflow definition JSON file (for run)")
    workflow.add_argument("--output", help="output workflow file (for create-standard)")
    workflow.add_argument("--format", choices=["json", "markdown"], default="json")
    workflow.add_argument("--json-output", help="JSON execution report output")
    workflow.add_argument("--markdown-output", help="markdown execution report output")
    workflow.set_defaults(func=run_workflow)

    trend = sub.add_parser("trend", help="analyze dataset quality trends over time")
    trend.add_argument("operation", choices=["record", "analyze", "report"])
    trend.add_argument("--dataset", help="dataset file path (for record)")
    trend.add_argument("--dataset-name", help="dataset name (for analyze/report)")
    trend.add_argument("--trend-dir", default=".peachtree/trends", help="trend data storage directory")
    trend.add_argument("--format", choices=["json", "markdown"], default="json")
    trend.add_argument("--json-output", help="JSON analysis output")
    trend.add_argument("--markdown-output", help="markdown analysis output")
    trend.add_argument("--output", help="output file path")
    trend.set_defaults(func=run_trend)

    merge = sub.add_parser("merge", help="merge multiple datasets into one")
    merge.add_argument("--sources", nargs="+", required=True, help="source datasets to merge")
    merge.add_argument("--output", required=True, help="output merged dataset path")
    merge.add_argument("--keep-duplicates", action="store_true", help="do not remove duplicates during merge")
    merge.add_argument("--preserve-metadata", action="store_true", default=True, help="add source metadata to records")
    merge.add_argument("--format", choices=["json", "markdown"], default="json")
    merge.add_argument("--json-output", help="JSON report output")
    merge.set_defaults(func=run_merge)

    split = sub.add_parser("split", help="split dataset into multiple parts")
    split.add_argument("--dataset", required=True, help="source dataset to split")
    split.add_argument("--output-dir", required=True, help="output directory for splits")
    split.add_argument("--strategy", required=True, choices=["count", "ratio", "size"], help="split strategy")
    split.add_argument("--split-count", type=int, help="number of splits (for count strategy)")
    split.add_argument("--ratios", nargs="+", help="split ratios as name=value (e.g., train=0.8 val=0.1 test=0.1)")
    split.add_argument("--max-records", type=int, help="max records per split (for size strategy)")
    split.add_argument("--prefix", default="split", help="prefix for output filenames")
    split.add_argument("--shuffle", action="store_true", help="shuffle before splitting (ratio strategy)")
    split.add_argument("--seed", type=int, help="random seed for reproducibility")
    split.add_argument("--format", choices=["json", "markdown"], default="json")
    split.add_argument("--json-output", help="JSON report output")
    split.set_defaults(func=run_split)

    sample = sub.add_parser("sample", help="intelligently sample dataset subsets")
    sample.add_argument("--dataset", required=True, help="source dataset to sample")
    sample.add_argument("--output", required=True, help="output sample path")
    sample.add_argument("--strategy", required=True, choices=["random", "quality", "stratified", "reservoir", "diversity", "time"], help="sampling strategy")
    sample.add_argument("--size", type=int, help="number of records to sample")
    sample.add_argument("--ratio", type=float, help="ratio of records to sample (0.0-1.0)")
    sample.add_argument("--min-quality", type=float, default=0.0, help="minimum quality score (quality strategy)")
    sample.add_argument("--stratify-field", default="source_repo", help="field to stratify on (stratified strategy)")
    sample.add_argument("--diversity-field", default="content", help="field for diversity (diversity strategy)")
    sample.add_argument("--time-field", default="timestamp", help="timestamp field (time strategy)")
    sample.add_argument("--recent-first", action="store_true", default=True, help="sample recent records first (time strategy)")
    sample.add_argument("--seed", type=int, help="random seed for reproducibility")
    sample.add_argument("--format", choices=["json", "markdown"], default="json")
    sample.add_argument("--json-output", help="JSON report output")
    sample.set_defaults(func=run_sample)

    profile = sub.add_parser("profile", help="profile dataset processing performance")
    profile.add_argument("--dataset", required=True, help="dataset to profile")
    profile.add_argument("--operation", required=True, choices=["pipeline", "read", "dedup", "quality"], help="operation to profile")
    profile.add_argument("--skip-read", action="store_true", help="skip read profiling (pipeline only)")
    profile.add_argument("--skip-dedup", action="store_true", help="skip dedup profiling (pipeline only)")
    profile.add_argument("--skip-quality", action="store_true", help="skip quality profiling (pipeline only)")
    profile.add_argument("--format", choices=["json", "markdown"], default="json")
    profile.add_argument("--json-output", help="JSON report output")
    profile.add_argument("--markdown-output", help="markdown report output")
    profile.set_defaults(func=run_profile)

    validate = sub.add_parser("validate", help="validate dataset with schema and rules")
    validate.add_argument("--dataset", required=True, help="dataset to validate")
    validate.add_argument("--schema", help="JSON schema file")
    validate.add_argument("--required-fields", nargs="+", help="required field names")
    validate.add_argument("--stop-on-error", action="store_true", help="stop on first error")
    validate.add_argument("--format", choices=["json", "markdown"], default="json")
    validate.add_argument("--json-output", help="JSON report output")
    validate.add_argument("--markdown-output", help="markdown report output")
    validate.set_defaults(func=run_validate)

    incremental = sub.add_parser("incremental", help="incremental dataset updates")
    incremental.add_argument("--operation", required=True, choices=["detect", "apply", "history"], help="incremental operation")
    incremental.add_argument("--baseline", help="baseline dataset")
    incremental.add_argument("--updated", help="updated dataset (for detect/apply)")
    incremental.add_argument("--delta-file", help="delta file (for apply)")
    incremental.add_argument("--save-delta", help="save delta to file (detect only)")
    incremental.add_argument("--output", help="output dataset path (apply only)")
    incremental.add_argument("--id-field", default="id", help="record ID field")
    incremental.add_argument("--history-dir", help="history directory (history only)")
    incremental.add_argument("--dataset-name", help="dataset name (history only)")
    incremental.add_argument("--changelog", help="generate changelog (history only)")
    incremental.add_argument("--format", choices=["json", "markdown"], default="json")
    incremental.add_argument("--json-output", help="JSON output")
    incremental.set_defaults(func=run_incremental)

    catalog = sub.add_parser("catalog", help="dataset catalog and discovery")
    catalog.add_argument("--operation", required=True, choices=["index", "search", "list", "update"], help="catalog operation")
    catalog.add_argument("--dataset", help="dataset path (index/update)")
    catalog.add_argument("--index", help="catalog index file path")
    catalog.add_argument("--tags", nargs="+", help="dataset tags")
    catalog.add_argument("--metadata", help="JSON metadata string")
    catalog.add_argument("--query", help="search query (search only)")
    catalog.add_argument("--min-quality", type=float, help="minimum quality score filter")
    catalog.add_argument("--min-records", type=int, help="minimum record count filter")
    catalog.add_argument("--source-repo", help="source repository filter")
    catalog.add_argument("--sort-by", choices=["modified", "created", "name", "size", "records", "quality"], default="modified", help="sort order (list only)")
    catalog.add_argument("--quality-score", type=float, help="quality score to set (update only)")
    catalog.add_argument("--format", choices=["json", "markdown", "text"], default="text")
    catalog.set_defaults(func=run_catalog)

    security_scan = sub.add_parser("security-scan", help="scan datasets for security issues")
    security_scan.add_argument("--dataset", required=True, help="dataset to scan")
    security_scan.add_argument("--operation", required=True, choices=["scan", "scan-field", "quick-scan"], help="scan operation")
    security_scan.add_argument("--field", help="field to scan (scan-field only)")
    security_scan.add_argument("--sample-size", type=int, default=100, help="sample size (quick-scan only)")
    security_scan.add_argument("--stop-on-critical", action="store_true", help="stop on first critical issue")
    security_scan.add_argument("--format", choices=["json", "markdown"], default="json")
    security_scan.add_argument("--json-output", help="JSON report output")
    security_scan.add_argument("--markdown-output", help="markdown report output")
    security_scan.set_defaults(func=run_security_scan)

    export_advanced = sub.add_parser("export-advanced", help="export to advanced ML framework formats")
    export_advanced.add_argument("--source", required=True, help="source dataset")
    export_advanced.add_argument("--output", required=True, help="output file path")
    export_advanced.add_argument("--format", required=True, choices=get_advanced_format_names(), help="export format")
    export_advanced.add_argument("--system-prompt", default="You are a helpful AI assistant.", help="system prompt (llama3/claude/qwen)")
    export_advanced.add_argument("--json-output", help="JSON export result output")
    export_advanced.set_defaults(func=run_export_advanced)

    lineage = sub.add_parser("lineage", help="generate dataset lineage visualizations")
    lineage.add_argument("--source", required=True, help="source manifest or catalog")
    lineage.add_argument("--source-type", required=True, choices=["manifest", "catalog"], help="source type")
    lineage.add_argument("--format", choices=["dot", "mermaid", "ascii", "markdown"], default="mermaid", help="output format")
    lineage.add_argument("--output", help="output file path")
    lineage.add_argument("--all-formats", action="store_true", help="generate all formats")
    lineage.add_argument("--title", help="diagram title (markdown only)")
    lineage.set_defaults(func=run_lineage)

    diff = sub.add_parser("diff", help="compare datasets with detailed change tracking")
    diff.add_argument("operation", choices=["diff", "patch", "apply", "find-duplicates"])
    diff.add_argument("--base", help="base dataset")
    diff.add_argument("--compare", help="compare dataset (for diff/find-duplicates)")
    diff.add_argument("--patch", help="patch file (for apply)")
    diff.add_argument("--output", help="output file path")
    diff.add_argument("--no-content-compare", action="store_true", help="skip content comparison")
    diff.add_argument("--format", choices=["json", "markdown"], default="json")
    diff.add_argument("--json-output", help="JSON output file")
    diff.add_argument("--markdown-output", help="markdown output file")
    diff.set_defaults(func=run_diff)

    policy_template = sub.add_parser("policy-template", help="manage pre-built compliance policy templates")
    policy_template.add_argument("operation", choices=["list", "get", "save"])
    policy_template.add_argument("--template-id", help="template ID (gdpr_compliance_v1, hipaa_compliance_v1, soc2_compliance_v1, commercial_ready_v1, open_safe_v1, research_v1, hancock_cybersecurity_v1)")
    policy_template.add_argument("--output", help="output file path")
    policy_template.set_defaults(func=run_policy_template)

    analytics = sub.add_parser("analytics", help="generate dataset analytics and statistics")
    analytics.add_argument("operation", choices=["analyze", "compare", "outliers", "summary"])
    analytics.add_argument("--dataset", help="dataset to analyze")
    analytics.add_argument("--dataset1", help="first dataset (for compare)")
    analytics.add_argument("--dataset2", help="second dataset (for compare)")
    analytics.add_argument("--skip-quality", action="store_true", help="skip quality analysis")
    analytics.add_argument("--threshold", type=float, default=3.0, help="z-score threshold for outliers")
    analytics.add_argument("--format", choices=["json", "markdown"], default="json")
    analytics.add_argument("--json-output", help="JSON output file")
    analytics.add_argument("--markdown-output", help="markdown output file")
    analytics.set_defaults(func=run_analytics)

    migrate = sub.add_parser("migrate", help="migrate datasets between formats and schemas")
    migrate.add_argument("operation", choices=["migrate", "create-plan", "add-rule"])
    migrate.add_argument("--source", help="source dataset (for migrate)")
    migrate.add_argument("--output", help="output file path")
    migrate.add_argument("--plan", help="migration plan file")
    migrate.add_argument("--plan-id", help="plan ID (for create-plan)")
    migrate.add_argument("--source-schema", default="v1", help="source schema version")
    migrate.add_argument("--target-schema", default="v2", help="target schema version")
    migrate.add_argument("--rule-type", choices=["rename_field", "add_field", "remove_field", "transform_field", "change_type"], help="rule type (for add-rule)")
    migrate.add_argument("--target-field", help="target field name (for add-rule)")
    migrate.add_argument("--params", help="JSON params for rule (for add-rule)")
    migrate.add_argument("--json-output", help="JSON output file")
    migrate.set_defaults(func=run_migrate)

    enhance = sub.add_parser("enhance", help="analyze and improve dataset quality")
    enhance.add_argument("operation", choices=["analyze", "auto-fix"])
    enhance.add_argument("--dataset", required=True, help="dataset to analyze")
    enhance.add_argument("--output", help="output file path (for auto-fix)")
    enhance.add_argument("--format", choices=["json", "text"], default="json")
    enhance.add_argument("--json-output", help="JSON report output")
    enhance.add_argument("--markdown-output", help="markdown report output")
    enhance.set_defaults(func=run_enhance)

    dashboard = sub.add_parser("dashboard", help="generate dataset metrics dashboard")
    dashboard.add_argument("operation", choices=["generate", "compare"])
    dashboard.add_argument("--dataset", help="dataset to analyze (for generate)")
    dashboard.add_argument("--dataset1", help="first dataset (for compare)")
    dashboard.add_argument("--dataset2", help="second dataset (for compare)")
    dashboard.add_argument("--dataset-id", help="dataset identifier")
    dashboard.add_argument("--format", choices=["json", "markdown"], default="json")
    dashboard.add_argument("--json-output", help="JSON output file")
    dashboard.add_argument("--markdown-output", help="markdown output file")
    dashboard.set_defaults(func=run_dashboard)

    batch.add_argument("--min-average-score", type=int, default=70, help="minimum average score (score only)")
    batch.add_argument("--max-failed-ratio", type=float, default=0.1, help="max failed ratio (score only)")
    batch.add_argument("--min-records", type=int, default=100, help="minimum records (score only)")
    batch.add_argument("--fail-on-error", action="store_true", help="fail immediately on first error")
    batch.add_argument("--format", choices=["json", "markdown"], default="json")
    batch.add_argument("--json-output", help="JSON report output file")
    batch.add_argument("--markdown-output", help="markdown report output file")
    batch.set_defaults(func=run_batch)

    status = sub.add_parser("status", help="show dataset status dashboard with unified metrics")
    status.add_argument("--dataset", help="single dataset to check")
    status.add_argument("--all", action="store_true", help="check all datasets in default directory")
    status.add_argument("--directory", help="directory containing datasets")
    status.add_argument("--pattern", default="*.jsonl", help="file pattern to match (default: *.jsonl)")
    status.add_argument("--quality-warning", type=float, default=75.0, help="quality score warning threshold")
    status.add_argument("--quality-critical", type=float, default=60.0, help="quality score critical threshold")
    status.add_argument("--duplicate-warning", type=float, default=0.15, help="duplicate ratio warning threshold")
    status.add_argument("--duplicate-critical", type=float, default=0.30, help="duplicate ratio critical threshold")
    status.add_argument("--min-average-score", type=int, default=70, help="minimum average quality score")
    status.add_argument("--max-failed-ratio", type=float, default=0.1, help="maximum failed record ratio")
    status.add_argument("--format", choices=["json", "markdown"], default="json")
    status.add_argument("--json-output", help="JSON output file")
    status.add_argument("--markdown-output", help="markdown output file")
    status.set_defaults(func=run_status)

    backup = sub.add_parser("backup", help="backup and restore datasets")
    backup.add_argument("operation", choices=["create", "incremental", "restore", "list", "validate", "delete", "cleanup"])
    backup.add_argument("--dataset", help="dataset to backup")
    backup.add_argument("--dataset-id", required=True, help="dataset identifier")
    backup.add_argument("--backup-id", help="backup ID (for restore/validate/delete)")
    backup.add_argument("--parent-backup-id", help="parent backup ID (for incremental)")
    backup.add_argument("--output", help="restore output path")
    backup.add_argument("--backup-dir", help="backup directory (default: data/backups)")
    backup.add_argument("--tags", help="JSON tags for backup")
    backup.add_argument("--skip-checksum", action="store_true", help="skip checksum verification")
    backup.add_argument("--keep", type=int, default=10, help="number of backups to keep (cleanup only)")
    backup.add_argument("--format", choices=["json", "text"], default="text")
    backup.add_argument("--json-output", help="JSON output file")
    backup.set_defaults(func=run_backup)

    export_v2 = sub.add_parser("export-v2", help="export to ML framework formats (PyTorch, TensorFlow, HuggingFace, Alpaca, ShareGPT)")
    export_v2.add_argument("operation", choices=["export", "batch", "list-formats"])
    export_v2.add_argument("--source", help="source dataset")
    export_v2.add_argument("--output", help="output file path (for export)")
    export_v2.add_argument("--output-dir", help="output directory (for batch)")
    export_v2.add_argument("--format", choices=["pytorch", "tensorflow", "huggingface", "alpaca", "sharegpt", "openai-finetune"], help="export format (for export)")
    export_v2.add_argument("--formats", help="comma-separated formats (for batch)")
    export_v2.add_argument("--system-prompt", default="You are a helpful AI assistant.", help="system prompt (openai-finetune)")
    export_v2.add_argument("--json-output", help="JSON output file")
    export_v2.set_defaults(func=run_export_v2)

    gate = sub.add_parser("gate", help="quality gates for dataset validation")
    gate.add_argument("operation", choices=["evaluate", "create-config"])
    gate.add_argument("--dataset", help="dataset to evaluate")
    gate.add_argument("--dataset-id", help="dataset identifier")
    gate.add_argument("--config", help="gate config file (for evaluate)")
    gate.add_argument("--strict", action="store_true", help="use strict thresholds")
    gate.add_argument("--ci", action="store_true", help="use CI/CD gate")
    gate.add_argument("--gate-id", default="custom_gate", help="gate ID (for create-config)")
    gate.add_argument("--output", help="output file path (for create-config)")
    gate.add_argument("--format", choices=["json", "markdown"], default="json")
    gate.add_argument("--json-output", help="JSON output file")
    gate.add_argument("--markdown-output", help="markdown output file")
    gate.set_defaults(func=run_gate)

    profiler = sub.add_parser("profiler", help="profile dataset for statistical analysis")
    profiler.add_argument("--dataset", required=True, help="dataset to profile")
    profiler.add_argument("--dataset-id", help="dataset identifier")
    profiler.add_argument("--compute-tokens", action="store_true", help="compute token counts (slower)")
    profiler.add_argument("--compare", help="baseline dataset to compare against")
    profiler.add_argument("--format", choices=["json", "markdown"], default="json")
    profiler.add_argument("--json-output", help="JSON output file")
    profiler.add_argument("--markdown-output", help="markdown output file")
    profiler.set_defaults(func=run_profiler)

    test = sub.add_parser("test", help="automated dataset testing framework")
    test.add_argument("operation", choices=["generate", "validate-schema", "regression", "property"])
    test.add_argument("--dataset", help="dataset to test")
    test.add_argument("--baseline", help="baseline dataset (for regression)")
    test.add_argument("--current", help="current dataset (for regression)")
    test.add_argument("--num-records", type=int, default=100, help="number of records (for generate)")
    test.add_argument("--output", help="output file path (for generate)")
    test.add_argument("--required-fields", help="comma-separated required fields")
    test.add_argument("--property-name", choices=["has_content", "has_id", "quality_above_threshold"], help="property to test")
    test.add_argument("--property-threshold", type=float, default=70.0, help="threshold for property tests")
    test.set_defaults(func=run_test)

    monitor = sub.add_parser("monitor", help="real-time dataset monitoring")
    monitor.add_argument("operation", choices=["health", "dashboard", "alerts"])
    monitor.add_argument("--dataset", required=True, help="dataset to monitor")
    monitor.add_argument("--dataset-id", help="dataset identifier")
    monitor.add_argument("--quality-threshold", type=float, default=70.0, help="quality score threshold")
    monitor.add_argument("--min-record-count", type=int, default=100, help="minimum record count")
    monitor.add_argument("--max-age-hours", type=int, default=24, help="maximum file age in hours")
    monitor.add_argument("--json-output", help="JSON output file")
    monitor.set_defaults(func=run_monitor)

    sync = sub.add_parser("sync", help="synchronize datasets across environments")
    sync.add_argument("--source", required=True, help="source dataset path")
    sync.add_argument("--target", required=True, help="target dataset path")
    sync.add_argument("--bidirectional", action="store_true", help="perform bidirectional sync")
    sync.add_argument("--conflict-resolution", choices=["source", "target", "newest"], default="newest", help="conflict resolution strategy")
    sync.add_argument("--json-output", help="JSON output file for sync report")
    sync.set_defaults(func=run_sync)

    transform = sub.add_parser("transform", help="transform datasets using ETL pipelines")
    transform.add_argument("operation", choices=["apply", "create-standard"])
    transform.add_argument("--source", help="source dataset (for apply)")
    transform.add_argument("--output", required=True, help="output file path")
    transform.add_argument("--pipeline", help="pipeline file path (for apply)")
    transform.add_argument("--pipeline-id", help="pipeline ID (for create-standard)")
    transform.add_argument("--json-output", help="JSON output file for transformation report")
    transform.set_defaults(func=run_transform)

    recommend = sub.add_parser("recommend", help="generate dataset configuration recommendations")
    recommend.add_argument("operation", choices=["generate", "apply"])
    recommend.add_argument("--dataset", help="dataset to analyze (for generate)")
    recommend.add_argument("--report", help="recommendations report file (for apply)")
    recommend.add_argument("--config", help="current config as JSON string (for apply)")
    recommend.add_argument("--impact-threshold", choices=["low", "medium", "high"], help="minimum impact level to apply")
    recommend.add_argument("--output", help="output file path")
    recommend.add_argument("--format", choices=["json", "markdown"], default="json")
    recommend.set_defaults(func=run_recommend)

    collaborate = sub.add_parser("collaborate", help="manage dataset collaboration sessions")
    collaborate.add_argument("operation", choices=["create", "stats"])
    collaborate.add_argument("--dataset", help="dataset path (for create)")
    collaborate.add_argument("--session", help="session file path (for stats)")
    collaborate.add_argument("--user-id", help="user ID (for create)")
    collaborate.add_argument("--username", help="username (for create)")
    collaborate.add_argument("--email", help="email (for create)")
    collaborate.add_argument("--output", help="output file path")
    collaborate.set_defaults(func=run_collaborate)

    compliance = sub.add_parser("compliance", help="check dataset compliance with regulations")
    compliance.add_argument("operation", choices=["check", "remediate"])
    compliance.add_argument("--dataset", help="dataset to check (for check)")
    compliance.add_argument("--regulations", help="comma-separated regulations: gdpr,ccpa,ai_act,hipaa,soc2,iso27001 (for check)")
    compliance.add_argument("--metadata", help="metadata JSON file (for check)")
    compliance.add_argument("--report", help="compliance report file (for remediate)")
    compliance.add_argument("--output", help="output file path")
    compliance.add_argument("--json-output", action="store_true", help="show full JSON output")
    compliance.set_defaults(func=run_compliance)

    cache = sub.add_parser("cache", help="manage dataset caching and performance optimization")
    cache.add_argument("operation", choices=["enable", "stats", "clear", "recommend"])
    cache.add_argument("--dataset", help="dataset path")
    cache.add_argument("--max-memory-mb", type=int, default=1024, help="max memory cache size in MB")
    cache.add_argument("--max-disk-mb", type=int, default=10240, help="max disk cache size in MB")
    cache.add_argument("--use-disk", action="store_true", help="use disk cache instead of memory")
    cache.add_argument("--target-hit-rate", type=float, default=0.8, help="target hit rate (for recommend)")
    cache.set_defaults(func=run_cache)

    schedule = sub.add_parser("schedule", help="manage scheduled dataset tasks")
    schedule.add_argument("operation", choices=["create", "list", "run", "stats"])
    schedule.add_argument("--task-id", help="task identifier")
    schedule.add_argument("--task-type", choices=["backup", "quality_check", "compliance_check", "sync", "export", "cleanup"], help="type of task")
    schedule.add_argument("--schedule-type", choices=["once", "hourly", "daily", "weekly", "monthly"], help="schedule type")
    schedule.add_argument("--schedule-config", help="schedule configuration JSON")
    schedule.add_argument("--dataset", help="dataset path")
    schedule.add_argument("--params", help="task parameters JSON")
    schedule.add_argument("--tasks-file", help="tasks file path")
    schedule.add_argument("--output", help="output file path")
    schedule.set_defaults(func=run_schedule)

    notify = sub.add_parser("notify", help="manage dataset notifications")
    notify.add_argument("operation", choices=["create-rule", "emit", "list-events", "stats"])
    notify.add_argument("--rule-id", help="rule identifier")
    notify.add_argument("--event-type", choices=["dataset_created", "dataset_updated", "dataset_deleted", "quality_score_changed", "compliance_check_failed", "build_completed", "build_failed", "sync_completed", "sync_failed", "backup_completed", "backup_failed", "threshold_exceeded"], help="event type")
    notify.add_argument("--notification-type", choices=["info", "warning", "error", "success", "critical"], help="notification type")
    notify.add_argument("--channels", help="comma-separated channels: email,slack,webhook,log,console,sms")
    notify.add_argument("--recipients", help="comma-separated recipients")
    notify.add_argument("--dataset", help="dataset path")
    notify.add_argument("--metadata", help="event metadata JSON")
    notify.add_argument("--rules-file", help="rules file path")
    notify.add_argument("--output", help="output file path")
    notify.add_argument("--limit", type=int, default=100, help="limit for list operations")
    notify.set_defaults(func=run_notify)

    webhook = sub.add_parser("webhook", help="manage dataset webhooks")
    webhook.add_argument("operation", choices=["create", "trigger", "test", "stats"])
    webhook.add_argument("--endpoint-id", help="endpoint identifier")
    webhook.add_argument("--url", help="webhook URL")
    webhook.add_argument("--events", help="comma-separated events: dataset.created,dataset.updated,build.completed,quality_check.passed,etc")
    webhook.add_argument("--secret", help="webhook secret for HMAC signatures")
    webhook.add_argument("--event", help="event to trigger")
    webhook.add_argument("--dataset", help="dataset path")
    webhook.add_argument("--data", help="webhook data JSON")
    webhook.add_argument("--endpoints-file", help="endpoints file path")
    webhook.add_argument("--output", help="output file path")
    webhook.set_defaults(func=run_webhook)

    policy = sub.add_parser("policy", help="show collection safety policy")
    policy.set_defaults(func=run_policy)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
