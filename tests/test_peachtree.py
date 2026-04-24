from pathlib import Path
import json
import pytest

from peachtree.builder import DatasetBuilder
from peachtree.cli import main
from peachtree.github_policy import GitHubCollectionPolicy
from peachtree.models import DatasetRecord, SourceDocument, sha256_text
from peachtree.planner import RecursiveLearningTree
from peachtree.repo_ingest import iter_local_documents
from peachtree.safety import SafetyGate


def test_sha256_text_length():
    assert len(sha256_text("x")) == 64


def test_source_document_digest_stable():
    assert SourceDocument("r", "a.md", "x").digest == SourceDocument("r", "a.md", "x").digest


def test_dataset_record_jsonl_has_id():
    record = DatasetRecord("i", "in", "out", "d", "r", "p", "digest", "mit")
    assert "id" in json.loads(record.to_jsonl())


def test_safety_allows_normal_doc():
    assert SafetyGate().check_document(SourceDocument("r", "README.md", "safe docs")).allowed


def test_safety_rejects_secret_like_doc():
    doc = SourceDocument("r", ".env", "API_KEY='abcdefghijklmnopqrstuvwxyz123456'")
    assert not SafetyGate().check_document(doc).allowed


def test_safety_sanitizes_email():
    assert "[REDACTED_EMAIL]" in SafetyGate().sanitize("a@example.com")


def test_tree_builds_nodes():
    assert len(RecursiveLearningTree("p", "goal", max_depth=1).build()) > 1


def test_tree_json_valid():
    assert isinstance(json.loads(RecursiveLearningTree("p", "goal", max_depth=1).to_json()), list)


def test_ingest_reads_markdown(tmp_path: Path):
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    assert iter_local_documents(tmp_path, "repo")[0].path == "README.md"


def test_ingest_skips_bin(tmp_path: Path):
    (tmp_path / "x.bin").write_bytes(b"x")
    assert not iter_local_documents(tmp_path, "repo")


def test_builder_creates_records():
    docs = [SourceDocument("repo", "README.md", "Safety docs. Example usage.")]
    assert DatasetBuilder("demo").records_from_documents(docs)


def test_builder_writes_and_audits(tmp_path: Path):
    docs = [SourceDocument("repo", "README.md", "Safety docs. Example usage.")]
    builder = DatasetBuilder("demo")
    records = builder.records_from_documents(docs)
    builder.write_jsonl(records, tmp_path / "d.jsonl", tmp_path / "m.json", docs)
    assert builder.audit_jsonl(tmp_path / "d.jsonl")["records"] == len(records)


def test_public_collection_disabled_by_default():
    with pytest.raises(PermissionError):
        GitHubCollectionPolicy().validate_public_collection()


def test_public_collection_requires_license_allowlist():
    with pytest.raises(ValueError):
        GitHubCollectionPolicy(allow_public_github=True, allowed_licenses=()).validate_public_collection()


def test_public_collection_safe_policy_passes():
    GitHubCollectionPolicy(allow_public_github=True).validate_public_collection()


def test_cli_policy(capsys):
    assert main(["policy"]) == 0
    assert "public_github_default" in capsys.readouterr().out


def test_cli_plan(capsys):
    assert main(["plan", "--goal", "build", "--project", "peachfuzz", "--depth", "1"]) == 0
    assert "learn architecture" in capsys.readouterr().out


def test_cli_ingest_build_audit(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("Safety docs. Example usage.", encoding="utf-8")
    raw = tmp_path / "raw.jsonl"
    dataset = tmp_path / "dataset.jsonl"
    manifest = tmp_path / "manifest.json"
    assert main(["ingest-local", "--repo", str(repo), "--repo-name", "demo", "--output", str(raw)]) == 0
    assert main(["build", "--source", str(raw), "--dataset", str(dataset), "--manifest", str(manifest), "--domain", "demo"]) == 0
    assert main(["audit", "--dataset", str(dataset), "--domain", "demo"]) == 0
    assert '"records"' in capsys.readouterr().out
