from pathlib import Path

from peachtree.workspace import PeachWorkspace, default_workspace, write_default_workspace, workspace_report


def test_default_workspace_is_safe() -> None:
    workspace = default_workspace()
    validation = workspace.validate()

    assert validation["ok"]
    assert validation["safety"]["public_github_collection"] is False
    assert validation["safety"]["review_required_before_training"] is True


def test_workspace_rejects_public_collection() -> None:
    workspace = PeachWorkspace.from_dict(
        {
            "workspace": "unsafe",
            "repos": [],
            "policy": {
                "public_github_collection": True,
                "review_required_before_training": True,
            },
        }
    )

    validation = workspace.validate()

    assert not validation["ok"]
    assert any("public_github_collection" in item["message"] for item in validation["findings"])


def test_write_default_workspace_and_report(tmp_path: Path) -> None:
    path = tmp_path / "peach.json"
    write_default_workspace(path)

    assert path.exists()
    report = workspace_report(path)
    assert "Peach Workspace Report" in report
    assert "hancock" in report
