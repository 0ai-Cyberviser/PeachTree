from pathlib import Path
import json

from peachtree.cli import main
from peachtree.license_gate import LicenseGate
from peachtree.model_card import ModelCardGenerator
from peachtree.policy_packs import PolicyPackEvaluator


def _good_record(record_id: str = "r1", license_id: str = "apache-2.0") -> dict:
    return {
        "id": record_id,
        "instruction": "Explain the purpose of this source file for training.",
        "input": "Repository: demo\nPath: README.md\n\nThis project contains safe dataset tooling.",
        "output": "This source provides safe, provenance-backed training knowledge.",
        "domain": "demo",
        "source_repo": "0ai-Cyberviser/demo",
        "source_path": "README.md",
        "source_digest": "abc123",
        "license_id": license_id,
        "quality_score": 0.9,
        "safety_score": 1.0,
    }


def _write_dataset(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def test_license_gate_allows_permissive_license(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "apache-2.0")])
    report = LicenseGate().evaluate(dataset)
    assert report.passed
    assert report.allowed_count == 1


def test_license_gate_denies_restricted_license(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "agpl-3.0")])
    report = LicenseGate().evaluate(dataset)
    assert not report.passed
    assert report.denied_count == 1


def test_license_gate_unknown_requires_review(tmp_path: Path):
    record = _good_record("a", "unknown")
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [record])
    report = LicenseGate().evaluate(dataset)
    assert not report.passed
    assert report.unknown_count == 1


def test_license_gate_allow_unknown_override(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "unknown")])
    report = LicenseGate(allow_unknown=True).evaluate(dataset)
    assert report.passed


def test_policy_pack_list_contains_builtin_packs():
    names = {pack.name for pack in PolicyPackEvaluator().list_packs()}
    assert {"open-safe", "commercial-ready", "internal-review"} <= names


def test_policy_pack_open_safe_passes(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), {**_good_record("b"), "input": "different context"}])
    evaluation = PolicyPackEvaluator().evaluate(dataset, "open-safe")
    assert evaluation.passed


def test_policy_pack_fails_on_duplicate_ratio(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), _good_record("b")])
    evaluation = PolicyPackEvaluator().evaluate(dataset, "commercial-ready")
    assert not evaluation.passed
    assert any(gate.name == "duplicate_ratio" and not gate.passed for gate in evaluation.gates)


def test_policy_pack_markdown_contains_gates(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), {**_good_record("b"), "input": "different context"}])
    markdown = PolicyPackEvaluator().evaluate(dataset, "open-safe").to_markdown()
    assert "Policy Pack Evaluation" in markdown
    assert "license_gate" in markdown


def test_policy_pack_write_report(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), {**_good_record("b"), "input": "different context"}])
    evaluation = PolicyPackEvaluator().evaluate(dataset, "open-safe")
    json_path, md_path = PolicyPackEvaluator.write_report(evaluation, tmp_path / "policy.json", tmp_path / "policy.md")
    assert json_path.exists()
    assert md_path is not None and md_path.exists()


def test_model_card_markdown(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"record_count": 1, "source_count": 1, "domain": "demo", "builder_version": "0.7.0"}), encoding="utf-8")
    card = ModelCardGenerator().generate(dataset, "DemoModel", manifest_path=manifest)
    markdown = card.to_markdown()
    assert "Model Card: DemoModel" in markdown
    assert "Dataset Summary" in markdown


def test_model_card_json_contains_review_requirements(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    card = ModelCardGenerator().generate(dataset, "DemoModel")
    data = json.loads(card.to_json())
    assert data["review_requirements"]["human_review_required"] is True


def test_model_card_write_json(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    card = ModelCardGenerator().generate(dataset, "DemoModel")
    output = ModelCardGenerator().write(card, tmp_path / "model-card.json", "json")
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["model_name"] == "DemoModel"


def test_cli_policy_pack_list(capsys):
    rc = main(["policy-pack", "--list"])
    assert rc == 0
    assert "open-safe" in capsys.readouterr().out


def test_cli_policy_pack_evaluate(tmp_path: Path, capsys):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a"), {**_good_record("b"), "input": "different context"}])
    rc = main(["policy-pack", "--dataset", str(dataset), "--pack", "open-safe"])
    assert rc == 0
    assert '"passed": true' in capsys.readouterr().out


def test_cli_policy_pack_fail_on_gate(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "agpl-3.0")])
    rc = main(["policy-pack", "--dataset", str(dataset), "--pack", "open-safe", "--fail-on-gate"])
    assert rc == 2


def test_cli_license_gate(tmp_path: Path, capsys):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "apache-2.0")])
    rc = main(["license-gate", "--dataset", str(dataset), "--summary-only"])
    assert rc == 0
    assert '"passed": true' in capsys.readouterr().out


def test_cli_license_gate_fail_on_denied(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a", "gpl-3.0")])
    rc = main(["license-gate", "--dataset", str(dataset), "--fail-on-gate"])
    assert rc == 2


def test_cli_model_card(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset.jsonl", [_good_record("a")])
    out = tmp_path / "model-card.md"
    rc = main(["model-card", "--dataset", str(dataset), "--model-name", "DemoModel", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    assert "Model Card: DemoModel" in out.read_text(encoding="utf-8")
