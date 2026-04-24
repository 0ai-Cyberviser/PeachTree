from pathlib import Path
import json

from peachtree.cli import main
from peachtree.diff_review import DatasetDiffReviewer
from peachtree.scheduler import UpdatePlanBuilder


def _write_dataset(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def test_dataset_fingerprint_counts_records(tmp_path: Path):
    dataset = _write_dataset(
        tmp_path / "dataset.jsonl",
        [{"id": "a", "source_repo": "repo", "source_path": "README.md", "source_digest": "d"}],
    )
    fp = DatasetDiffReviewer().fingerprint(dataset)
    assert fp.record_count == 1
    assert fp.source_repos == ("repo",)


def test_dataset_diff_detects_added_removed_changed(tmp_path: Path):
    baseline = _write_dataset(
        tmp_path / "old.jsonl",
        [
            {"id": "same", "instruction": "i", "output": "o", "source_repo": "repo", "source_path": "a.md"},
            {"id": "removed", "instruction": "i", "output": "o", "source_repo": "repo", "source_path": "b.md"},
            {"id": "changed", "instruction": "i", "output": "old", "source_repo": "repo", "source_path": "c.md"},
        ],
    )
    candidate = _write_dataset(
        tmp_path / "new.jsonl",
        [
            {"id": "same", "instruction": "i", "output": "o", "source_repo": "repo", "source_path": "a.md"},
            {"id": "changed", "instruction": "i", "output": "new", "source_repo": "repo", "source_path": "c.md"},
            {"id": "added", "instruction": "i", "output": "o", "source_repo": "new/repo", "source_path": "d.md"},
        ],
    )
    diff = DatasetDiffReviewer().compare(baseline, candidate)
    assert diff.added_ids == ("added",)
    assert diff.removed_ids == ("removed",)
    assert diff.changed_ids == ("changed",)
    assert diff.new_source_repos == ("new/repo",)
    assert diff.review_required


def test_dataset_diff_markdown_contains_summary(tmp_path: Path):
    baseline = _write_dataset(tmp_path / "old.jsonl", [{"id": "a", "output": "old", "source_repo": "repo"}])
    candidate = _write_dataset(tmp_path / "new.jsonl", [{"id": "a", "output": "new", "source_repo": "repo"}])
    markdown = DatasetDiffReviewer().compare(baseline, candidate).to_markdown()
    assert "PeachTree Dataset Diff Review" in markdown
    assert "Changed records" in markdown


def test_dataset_diff_writes_reports(tmp_path: Path):
    baseline = _write_dataset(tmp_path / "old.jsonl", [{"id": "a", "output": "old", "source_repo": "repo"}])
    candidate = _write_dataset(tmp_path / "new.jsonl", [{"id": "a", "output": "new", "source_repo": "repo"}])
    reviewer = DatasetDiffReviewer()
    diff = reviewer.compare(baseline, candidate)
    json_path, md_path = reviewer.write_reports(diff, tmp_path / "diff.json", tmp_path / "diff.md")
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["review_required"] is True


def test_update_plan_default_shape():
    plan = UpdatePlanBuilder().default_plan("~/peachfuzz", "0ai-Cyberviser/peachfuzz")
    assert plan.targets[0].repo_name == "0ai-Cyberviser/peachfuzz"
    assert plan.review_required
    assert "0ai-Cyberviser__peachfuzz" in plan.targets[0].dataset_output


def test_update_plan_markdown_mentions_targets():
    plan = UpdatePlanBuilder().default_plan("~/peachfuzz", "0ai-Cyberviser/peachfuzz")
    markdown = plan.to_markdown()
    assert "Scheduled Dataset Update Plan" in markdown
    assert "0ai-Cyberviser/peachfuzz" in markdown


def test_update_plan_write_and_read(tmp_path: Path):
    builder = UpdatePlanBuilder()
    plan = builder.default_plan("~/peachfuzz", "0ai-Cyberviser/peachfuzz")
    path, md = builder.write_plan(plan, tmp_path / "plan.json", tmp_path / "plan.md")
    loaded = builder.read_plan(path)
    assert loaded.name == plan.name
    assert md is not None and md.exists()


def test_update_plan_command_preview():
    plan = UpdatePlanBuilder().default_plan("~/peachfuzz", "0ai-Cyberviser/peachfuzz")
    commands = UpdatePlanBuilder.command_preview(plan)
    assert any("peachtree ingest-local" in command for command in commands)
    assert any("validate-export" in command for command in commands)


def test_cli_diff_json(tmp_path: Path, capsys):
    baseline = _write_dataset(tmp_path / "old.jsonl", [{"id": "a", "output": "old", "source_repo": "repo"}])
    candidate = _write_dataset(tmp_path / "new.jsonl", [{"id": "b", "output": "new", "source_repo": "repo"}])
    rc = main(["diff", "--baseline", str(baseline), "--candidate", str(candidate)])
    assert rc == 0
    assert '"review_required": true' in capsys.readouterr().out


def test_cli_diff_markdown_outputs_files(tmp_path: Path):
    baseline = _write_dataset(tmp_path / "old.jsonl", [{"id": "a", "output": "old", "source_repo": "repo"}])
    candidate = _write_dataset(tmp_path / "new.jsonl", [{"id": "b", "output": "new", "source_repo": "repo"}])
    rc = main([
        "diff",
        "--baseline", str(baseline),
        "--candidate", str(candidate),
        "--format", "markdown",
        "--json-output", str(tmp_path / "diff.json"),
        "--markdown-output", str(tmp_path / "diff.md"),
    ])
    assert rc == 0
    assert (tmp_path / "diff.json").exists()
    assert (tmp_path / "diff.md").exists()


def test_cli_update_plan(tmp_path: Path, capsys):
    rc = main([
        "update-plan",
        "--repo", "~/peachfuzz",
        "--repo-name", "0ai-Cyberviser/peachfuzz",
        "--output", str(tmp_path / "plan.json"),
        "--markdown-output", str(tmp_path / "plan.md"),
    ])
    assert rc == 0
    assert (tmp_path / "plan.json").exists()
    assert '"review_required": true' in capsys.readouterr().out


def test_cli_review_report(tmp_path: Path, capsys):
    plan_path = tmp_path / "plan.json"
    main([
        "update-plan",
        "--repo", "~/peachfuzz",
        "--repo-name", "0ai-Cyberviser/peachfuzz",
        "--output", str(plan_path),
    ])
    rc = main(["review-report", "--plan", str(plan_path), "--output", str(tmp_path / "review.json")])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"does_not_train_models": true' in out
    assert (tmp_path / "review.json").exists()
