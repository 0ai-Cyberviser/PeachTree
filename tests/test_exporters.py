from pathlib import Path
import json

from peachtree.cli import main
from peachtree.exporters import ModelExporter, export_format_names


def _dataset(tmp_path: Path) -> Path:
    path = tmp_path / "dataset.jsonl"
    records = [
        {
            "id": "rec-1",
            "instruction": "Explain this source.",
            "input": "Repository: demo\nPath: README.md\n\nSafe usage docs.",
            "output": "This source documents safe usage.",
            "domain": "demo",
            "source_repo": "0ai-Cyberviser/demo",
            "source_path": "README.md",
            "source_digest": "abc123",
            "license_id": "apache-2.0",
            "quality_score": 0.9,
            "safety_score": 1.0,
        },
        {
            "id": "rec-2",
            "instruction": "Summarize this test.",
            "input": "Path: tests/test_demo.py",
            "output": "This test validates the demo behavior.",
            "domain": "demo",
            "source_repo": "0ai-Cyberviser/demo",
            "source_path": "tests/test_demo.py",
            "source_digest": "def456",
            "license_id": "apache-2.0",
        },
    ]
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_export_format_names():
    assert set(export_format_names()) == {"chatml", "alpaca", "sharegpt"}


def test_chatml_convert_record_has_messages(tmp_path: Path):
    record = _read_jsonl(_dataset(tmp_path))[0]
    converted = ModelExporter().convert_record(record, "chatml")
    assert converted["messages"][0]["role"] == "system"
    assert converted["messages"][1]["role"] == "user"
    assert converted["messages"][2]["role"] == "assistant"


def test_alpaca_convert_record_has_fields(tmp_path: Path):
    record = _read_jsonl(_dataset(tmp_path))[0]
    converted = ModelExporter().convert_record(record, "alpaca")
    assert converted["instruction"] == "Explain this source."
    assert "input" in converted
    assert converted["output"]


def test_sharegpt_convert_record_has_conversations(tmp_path: Path):
    record = _read_jsonl(_dataset(tmp_path))[0]
    converted = ModelExporter().convert_record(record, "sharegpt")
    assert converted["conversations"][1]["from"] == "human"
    assert converted["conversations"][2]["from"] == "gpt"


def test_export_chatml_file(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "chatml.jsonl"
    stats = ModelExporter().export_file(source, out, "chatml")
    assert stats.ok
    assert len(_read_jsonl(out)) == 2
    assert "messages" in _read_jsonl(out)[0]


def test_export_alpaca_file(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "alpaca.jsonl"
    stats = ModelExporter().export_file(source, out, "alpaca")
    assert stats.ok
    assert "instruction" in _read_jsonl(out)[0]


def test_export_sharegpt_file(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "sharegpt.jsonl"
    stats = ModelExporter().export_file(source, out, "sharegpt")
    assert stats.ok
    assert "conversations" in _read_jsonl(out)[0]


def test_export_limit(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "limited.jsonl"
    stats = ModelExporter().export_file(source, out, "alpaca", limit=1)
    assert stats.records_written == 1
    assert len(_read_jsonl(out)) == 1


def test_export_without_metadata(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "plain.jsonl"
    ModelExporter(include_metadata=False).export_file(source, out, "alpaca")
    assert "metadata" not in _read_jsonl(out)[0]


def test_invalid_record_reports_issue(tmp_path: Path):
    source = tmp_path / "bad.jsonl"
    source.write_text(json.dumps({"instruction": "x", "output": ""}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    stats = ModelExporter().export_file(source, out, "chatml")
    assert not stats.ok
    assert stats.issues


def test_validate_chatml_export(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "chatml.jsonl"
    ModelExporter().export_file(source, out, "chatml")
    report = ModelExporter().validate_export(out, "chatml")
    assert report.ok
    assert report.records == 2


def test_validate_alpaca_export(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "alpaca.jsonl"
    ModelExporter().export_file(source, out, "alpaca")
    assert ModelExporter().validate_export(out, "alpaca").ok


def test_validate_sharegpt_export(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "sharegpt.jsonl"
    ModelExporter().export_file(source, out, "sharegpt")
    assert ModelExporter().validate_export(out, "sharegpt").ok


def test_validate_bad_chatml_export(tmp_path: Path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"messages": [{"role": "user"}]}) + "\n", encoding="utf-8")
    report = ModelExporter().validate_export(bad, "chatml")
    assert not report.ok
    assert report.issues


def test_cli_export_formats(capsys):
    rc = main(["export-formats"])
    assert rc == 0
    assert "chatml" in capsys.readouterr().out


def test_cli_export_chatml(tmp_path: Path, capsys):
    source = _dataset(tmp_path)
    out = tmp_path / "chatml.jsonl"
    rc = main(["export", "--source", str(source), "--format", "chatml", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    assert '"records_written": 2' in capsys.readouterr().out


def test_cli_export_alpaca_no_metadata(tmp_path: Path):
    source = _dataset(tmp_path)
    out = tmp_path / "alpaca.jsonl"
    rc = main(["export", "--source", str(source), "--format", "alpaca", "--output", str(out), "--no-metadata"])
    assert rc == 0
    assert "metadata" not in _read_jsonl(out)[0]


def test_cli_validate_export(tmp_path: Path, capsys):
    source = _dataset(tmp_path)
    out = tmp_path / "sharegpt.jsonl"
    main(["export", "--source", str(source), "--format", "sharegpt", "--output", str(out)])
    rc = main(["validate-export", "--format", "sharegpt", "--path", str(out)])
    assert rc == 0
    assert '"ok": true' in capsys.readouterr().out
