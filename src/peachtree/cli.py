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

    policy = sub.add_parser("policy", help="show collection safety policy")
    policy.set_defaults(func=run_policy)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
