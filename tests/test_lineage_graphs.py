from pathlib import Path
import json

from peachtree.cli import main
from peachtree.dependency_graph import DependencyGraphBuilder
from peachtree.lineage import DatasetLineageBuilder


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    inventory = tmp_path / "owned.jsonl"
    inventory.write_text(
        "\n".join([
            json.dumps({
                "full_name": "0ai-Cyberviser/PeachTree",
                "clone_url": "https://github.com/0ai-Cyberviser/PeachTree.git",
                "visibility": "public",
                "default_branch": "main",
                "archived": False,
                "license_id": "unknown",
                "size_kb": 1,
            }),
            json.dumps({
                "full_name": "0ai-Cyberviser/peachfuzz",
                "clone_url": "https://github.com/0ai-Cyberviser/peachfuzz.git",
                "visibility": "public",
                "default_branch": "main",
                "archived": False,
                "license_id": "unknown",
                "size_kb": 1,
            }),
            json.dumps({
                "full_name": "0ai-Cyberviser/Hancock",
                "clone_url": "https://github.com/0ai-Cyberviser/Hancock.git",
                "visibility": "public",
                "default_branch": "main",
                "archived": False,
                "license_id": "unknown",
                "size_kb": 1,
            }),
        ]) + "\n",
        encoding="utf-8",
    )
    dataset_dir = tmp_path / "datasets"
    manifest_dir = tmp_path / "manifests"
    dataset_dir.mkdir()
    manifest_dir.mkdir()
    dataset = dataset_dir / "0ai-Cyberviser__peachfuzz-instruct.jsonl"
    records = [
        {
            "id": "r1",
            "instruction": "Explain",
            "input": "x",
            "output": "y",
            "source_repo": "0ai-Cyberviser/peachfuzz",
            "source_path": "README.md",
            "source_digest": "digest-a",
        },
        {
            "id": "r2",
            "instruction": "Explain",
            "input": "x",
            "output": "y",
            "source_repo": "0ai-Cyberviser/peachfuzz",
            "source_path": "src/peachfuzz_ai/cli.py",
            "source_digest": "digest-b",
        },
    ]
    dataset.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    manifest = manifest_dir / "0ai-Cyberviser__peachfuzz.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset_path": str(dataset),
                "record_count": 2,
                "source_count": 2,
                "domain": "0ai-Cyberviser__peachfuzz",
            }
        ),
        encoding="utf-8",
    )
    return inventory, dataset_dir, manifest_dir


def test_dependency_graph_builds_repo_nodes(tmp_path: Path):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    graph = DependencyGraphBuilder().from_inputs(inventory, dataset_dir, manifest_dir)
    assert "repo:0ai-Cyberviser/PeachTree" in graph.nodes
    assert "repo:0ai-Cyberviser/peachfuzz" in graph.nodes
    assert graph.edges


def test_dependency_graph_json_has_counts(tmp_path: Path):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    graph = DependencyGraphBuilder().from_inputs(inventory, dataset_dir, manifest_dir)
    data = json.loads(graph.to_json())
    assert data["node_count"] >= 4
    assert data["edge_count"] >= 3


def test_dependency_graph_mermaid_mentions_relation(tmp_path: Path):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    mermaid = DependencyGraphBuilder().from_inputs(inventory, dataset_dir, manifest_dir).to_mermaid()
    assert "flowchart TD" in mermaid
    assert "generates_training_datasets_for" in mermaid


def test_dependency_graph_dot_valid_shape(tmp_path: Path):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    dot = DependencyGraphBuilder().from_inputs(inventory, dataset_dir, manifest_dir).to_dot()
    assert dot.startswith("digraph PeachTree")
    assert "->" in dot


def test_dataset_lineage_counts_sources(tmp_path: Path):
    _inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    lineage = DatasetLineageBuilder().from_dataset(
        dataset_dir / "0ai-Cyberviser__peachfuzz-instruct.jsonl",
        manifest_dir / "0ai-Cyberviser__peachfuzz.json",
    )
    assert lineage.record_count == 2
    assert lineage.source_repo_count == 1
    assert lineage.source_file_count == 2


def test_dataset_lineage_markdown_has_table(tmp_path: Path):
    _inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    lineage = DatasetLineageBuilder().from_dataset(
        dataset_dir / "0ai-Cyberviser__peachfuzz-instruct.jsonl",
        manifest_dir / "0ai-Cyberviser__peachfuzz.json",
    )
    markdown = lineage.to_markdown()
    assert "# PeachTree Dataset Lineage" in markdown
    assert "| Source Repo | Source Path | Records | Digest |" in markdown


def test_lineage_directory_summary(tmp_path: Path):
    _inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    summary = DatasetLineageBuilder().summarize_directory(dataset_dir, manifest_dir)
    assert summary["dataset_count"] == 1
    assert summary["total_records"] == 2
    assert summary["source_repositories"] == 1


def test_cli_graph_json(tmp_path: Path, capsys):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    rc = main([
        "graph",
        "--inventory", str(inventory),
        "--dataset-dir", str(dataset_dir),
        "--manifest-dir", str(manifest_dir),
        "--format", "json",
    ])
    assert rc == 0
    assert '"node_count"' in capsys.readouterr().out


def test_cli_graph_mermaid_output_file(tmp_path: Path):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    out = tmp_path / "graph.mmd"
    rc = main([
        "graph",
        "--inventory", str(inventory),
        "--dataset-dir", str(dataset_dir),
        "--manifest-dir", str(manifest_dir),
        "--format", "mermaid",
        "--output", str(out),
    ])
    assert rc == 0
    assert out.exists()
    assert "flowchart TD" in out.read_text(encoding="utf-8")


def test_cli_lineage_markdown_output_file(tmp_path: Path):
    _inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    out = tmp_path / "lineage.md"
    rc = main([
        "lineage",
        "--dataset", str(dataset_dir / "0ai-Cyberviser__peachfuzz-instruct.jsonl"),
        "--manifest", str(manifest_dir / "0ai-Cyberviser__peachfuzz.json"),
        "--format", "markdown",
        "--output", str(out),
    ])
    assert rc == 0
    assert out.exists()
    assert "Dataset Lineage" in out.read_text(encoding="utf-8")


def test_cli_ecosystem_json(tmp_path: Path, capsys):
    inventory, dataset_dir, manifest_dir = _write_fixture(tmp_path)
    rc = main([
        "ecosystem",
        "--inventory", str(inventory),
        "--dataset-dir", str(dataset_dir),
        "--manifest-dir", str(manifest_dir),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"lineage_summary"' in out
    assert '"public_github_collection": "disabled by default"' in out
