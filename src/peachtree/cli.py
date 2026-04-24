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

    policy = sub.add_parser("policy", help="show collection safety policy")
    policy.set_defaults(func=run_policy)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
