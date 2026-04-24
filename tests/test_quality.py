from pathlib import Path
import json

from peachtree.cli import main
from peachtree.dedup import DatasetDeduplicator, record_signature
from peachtree.quality import DatasetQualityScorer


def _write_dataset(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def _good_record(record_id: str = "r1") -> dict:
    return {
        "id": record_id,
        "instruction": "Explain the purpose of this source file for training.",
        "input": "Repository: demo\nPath: README.md\n\nThis project contains safe dataset tooling.",
        "output": "This source provides safe, provenance-backed training knowledge.",
        "domain": "demo",
        "source_repo": "0ai-Cyberviser/demo",
        "source_path": "README.md",
        "source_digest": "abc123",
        "license_id": "apache-2.0",
        "quality_score": 0.9,
        "safety_score": 1.0,
    }


def test_score_good_record_passes():
    score = DatasetQualityScorer().score_record(_good_record(), 1)
    assert score.passed
    assert score.score >= 90


def test_score_bad_record_fails():
    score = DatasetQualityScorer().score_record({"id": "bad", "instruction": "", "output": ""}, 1)
    assert not score.passed
    assert score.score < 70
    assert any(issue.code == "missing_instruction" for issue in score.issues)


def test_score_dataset_report_passes(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    report = DatasetQualityScorer().score_dataset(dataset)
    assert report.gate_passed
    assert report.record_count == 2
    assert report.readiness_level in {"ready", "excellent"}


def test_score_dataset_missing_provenance_fails(tmp_path: Path):
    record = _good_record("a")
    record.pop("source_repo")
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [record])
    report = DatasetQualityScorer().score_dataset(dataset)
    assert not report.gate_passed
    assert report.failed_records == 1


def test_quality_markdown_contains_gates(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    markdown = DatasetQualityScorer().score_dataset(dataset).to_markdown()
    assert "Dataset Quality Report" in markdown
    assert "min_average_score" in markdown


def test_quality_write_report(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    report = DatasetQualityScorer().score_dataset(dataset)
    json_path, md_path = DatasetQualityScorer.write_report(report, tmp_path / "quality.json", tmp_path / "quality.md")
    assert json_path.exists()
    assert md_path is not None and md_path.exists()


def test_record_signature_normalizes_whitespace():
    a = {"instruction": "Hello   World", "input": "X", "output": "Y"}
    b = {"instruction": "hello world", "input": "x", "output": "y"}
    assert record_signature(a) == record_signature(b)


def test_dedup_removes_duplicate_records(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    out = tmp_path / "deduped.jsonl"
    report = DatasetDeduplicator().deduplicate(dataset, out)
    assert report.input_count == 2
    assert report.output_count == 1
    assert report.duplicate_count == 1
    assert out.exists()


def test_dedup_analyze_does_not_write_output(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    report = DatasetDeduplicator().analyze(dataset)
    assert report.duplicate_count == 1
    assert report.output_path == ""


def test_dedup_write_report(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    report = DatasetDeduplicator().deduplicate(dataset, tmp_path / "deduped.jsonl")
    json_path, md_path = DatasetDeduplicator().write_report(report, tmp_path / "dedup.json", tmp_path / "dedup.md")
    assert json_path.exists()
    assert md_path is not None and md_path.exists()


def test_cli_score(tmp_path: Path, capsys):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    rc = main(["score", "--dataset", str(dataset), "--summary-only"])
    assert rc == 0
    assert '"gate_passed": true' in capsys.readouterr().out


def test_cli_score_writes_reports(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    rc = main([
        "score",
        "--dataset", str(dataset),
        "--json-output", str(tmp_path / "quality.json"),
        "--markdown-output", str(tmp_path / "quality.md"),
    ])
    assert rc == 0
    assert (tmp_path / "quality.json").exists()
    assert (tmp_path / "quality.md").exists()


def test_cli_dedup(tmp_path: Path, capsys):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    rc = main(["dedup", "--source", str(dataset), "--output", str(tmp_path / "deduped.jsonl")])
    assert rc == 0
    assert '"duplicate_count": 1' in capsys.readouterr().out


def test_cli_readiness_ready(tmp_path: Path, capsys):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), {**_good_record("b"), "input": "different context"}])
    rc = main(["readiness", "--dataset", str(dataset), "--max-duplicate-ratio", "0.6"])
    assert rc == 0
    assert '"ready": true' in capsys.readouterr().out


def test_cli_readiness_fail_on_gate(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [{"id": "bad", "instruction": "", "output": ""}])
    rc = main(["readiness", "--dataset", str(dataset), "--fail-on-gate"])
    assert rc == 2
