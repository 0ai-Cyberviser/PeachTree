from pathlib import Path
import json

from peachtree.cli import main
from peachtree.lora_job import LoraHyperparameters, LoraJobCardBuilder
from peachtree.trainer_handoff import TrainerHandoffBuilder
from peachtree.training_plan import DryRunTrainingPlanner


def _dataset(tmp_path: Path) -> Path:
    path = tmp_path / "dataset.jsonl"
    path.write_text(json.dumps({"id": "a", "instruction": "Explain safely.", "output": "Safe answer."}) + "\n", encoding="utf-8")
    return path


def _artifact(tmp_path: Path, name: str, content: str = "{}") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")
    return path


def test_handoff_manifest_includes_required_dataset(tmp_path: Path):
    dataset = _dataset(tmp_path)
    manifest = TrainerHandoffBuilder().build(
        dataset,
        model_name="DemoModel",
        base_model="mistralai/Mistral-7B-Instruct-v0.3",
    )
    assert manifest.artifact_count == 1
    assert manifest.artifacts[0].required
    assert manifest.safety["does_not_train_models"] is True


def test_handoff_manifest_optional_artifacts(tmp_path: Path):
    dataset = _dataset(tmp_path)
    registry = _artifact(tmp_path, "registry.json")
    sbom = _artifact(tmp_path, "sbom.json")
    manifest = TrainerHandoffBuilder().build(
        dataset,
        model_name="DemoModel",
        base_model="base",
        registry_path=registry,
        sbom_path=sbom,
    )
    kinds = {artifact.kind for artifact in manifest.artifacts}
    assert {"dataset", "registry", "sbom"} <= kinds


def test_handoff_write_reports(tmp_path: Path):
    dataset = _dataset(tmp_path)
    manifest = TrainerHandoffBuilder().build(dataset, "DemoModel", "base")
    out, md = TrainerHandoffBuilder().write(manifest, tmp_path / "handoff.json", tmp_path / "handoff.md")
    assert out.exists()
    assert md is not None and md.exists()


def test_lora_card_defaults(tmp_path: Path):
    dataset = _dataset(tmp_path)
    card = LoraJobCardBuilder().build(
        dataset,
        job_name="demo-lora",
        base_model="base",
        output_dir="outputs/demo",
    )
    assert card.trainer_profile == "unsloth"
    assert card.hyperparameters.rank == 16
    assert card.safety["dry_run_only"] is True


def test_lora_card_custom_hyperparameters(tmp_path: Path):
    dataset = _dataset(tmp_path)
    hp = LoraHyperparameters(rank=8, alpha=16, learning_rate=1e-4)
    card = LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo", hyperparameters=hp)
    assert card.hyperparameters.rank == 8
    assert card.hyperparameters.learning_rate == 1e-4


def test_lora_card_write_reports(tmp_path: Path):
    dataset = _dataset(tmp_path)
    card = LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo")
    out, md = LoraJobCardBuilder().write(card, tmp_path / "job.json", tmp_path / "job.md")
    assert out.exists()
    assert md is not None and md.exists()


def test_training_plan_from_card(tmp_path: Path):
    dataset = _dataset(tmp_path)
    card = LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo")
    plan = DryRunTrainingPlanner().build(card)
    assert plan.safety["does_not_execute_shell"] is True
    assert "DRY RUN ONLY" in plan.command_preview[0]


def test_training_plan_write_reports(tmp_path: Path):
    dataset = _dataset(tmp_path)
    card = LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo")
    plan = DryRunTrainingPlanner().build(card)
    out, md = DryRunTrainingPlanner().write(plan, tmp_path / "plan.json", tmp_path / "plan.md")
    assert out.exists()
    assert md is not None and md.exists()


def test_training_plan_read_job_card(tmp_path: Path):
    dataset = _dataset(tmp_path)
    card = LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo")
    out, _ = LoraJobCardBuilder().write(card, tmp_path / "job.json")
    loaded = DryRunTrainingPlanner().read_job_card(out)
    assert loaded.job_name == "demo"


def test_cli_handoff(tmp_path: Path, capsys):
    dataset = _dataset(tmp_path)
    rc = main([
        "handoff",
        "--dataset", str(dataset),
        "--model-name", "DemoModel",
        "--base-model", "base",
    ])
    assert rc == 0
    assert '"does_not_train_models": true' in capsys.readouterr().out


def test_cli_lora_card(tmp_path: Path, capsys):
    dataset = _dataset(tmp_path)
    rc = main([
        "lora-card",
        "--dataset", str(dataset),
        "--job-name", "demo",
        "--base-model", "base",
        "--output-dir", "outputs/demo",
    ])
    assert rc == 0
    assert '"job_name": "demo"' in capsys.readouterr().out


def test_cli_lora_card_writes_output(tmp_path: Path):
    dataset = _dataset(tmp_path)
    rc = main([
        "lora-card",
        "--dataset", str(dataset),
        "--job-name", "demo",
        "--base-model", "base",
        "--output-dir", "outputs/demo",
        "--output", str(tmp_path / "job.json"),
        "--markdown-output", str(tmp_path / "job.md"),
    ])
    assert rc == 0
    assert (tmp_path / "job.json").exists()
    assert (tmp_path / "job.md").exists()


def test_cli_train_plan_from_job_card(tmp_path: Path, capsys):
    dataset = _dataset(tmp_path)
    main([
        "lora-card",
        "--dataset", str(dataset),
        "--job-name", "demo",
        "--base-model", "base",
        "--output-dir", "outputs/demo",
        "--output", str(tmp_path / "job.json"),
    ])
    rc = main(["train-plan", "--job-card", str(tmp_path / "job.json")])
    assert rc == 0
    assert "DRY RUN ONLY" in capsys.readouterr().out


def test_cli_train_plan_direct(tmp_path: Path):
    dataset = _dataset(tmp_path)
    rc = main([
        "train-plan",
        "--dataset", str(dataset),
        "--job-name", "demo",
        "--base-model", "base",
        "--output-dir", "outputs/demo",
        "--output", str(tmp_path / "plan.json"),
        "--markdown-output", str(tmp_path / "plan.md"),
    ])
    assert rc == 0
    assert (tmp_path / "plan.json").exists()
    assert (tmp_path / "plan.md").exists()


def test_lora_card_rejects_bad_profile(tmp_path: Path):
    dataset = _dataset(tmp_path)
    try:
        LoraJobCardBuilder().build(dataset, "demo", "base", "outputs/demo", trainer_profile="bad")
    except ValueError as exc:
        assert "unsupported trainer profile" in str(exc)
    else:
        raise AssertionError("expected ValueError")
