from pathlib import Path

from peachtree.doctor import PeachTreeDoctor


def test_doctor_reports_project_layout(tmp_path: Path) -> None:
    (tmp_path / "src" / "peachtree").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='peachtree-ai'\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("data/raw\ndata/datasets\ndata/exports\ndist\n", encoding="utf-8")

    report = PeachTreeDoctor(tmp_path).run(command_names=PeachTreeDoctor.EXPECTED_COMMANDS)

    assert report.ok
    assert "PeachTree Doctor" in report.to_markdown()


def test_doctor_fails_missing_project_layout(tmp_path: Path) -> None:
    report = PeachTreeDoctor(tmp_path).run(command_names=set())

    assert not report.ok
    assert any(check.name == "project-layout" and check.status == "fail" for check in report.checks)


def test_doctor_dataset_check_warns_on_missing_provenance(tmp_path: Path) -> None:
    (tmp_path / "src" / "peachtree").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='peachtree-ai'\n", encoding="utf-8")
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id":"1","instruction":"x"}\n', encoding="utf-8")

    report = PeachTreeDoctor(tmp_path).run(dataset=dataset, command_names=PeachTreeDoctor.EXPECTED_COMMANDS)

    dataset_check = next(check for check in report.checks if check.name == "dataset")
    assert dataset_check.status == "warn"
    assert dataset_check.detail["missing_provenance"] == 1
