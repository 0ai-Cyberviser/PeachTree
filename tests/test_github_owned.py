from pathlib import Path
import json

from peachtree.cli import main
from peachtree.github_owned import OwnedGitHubConnector, OwnedRepo


SAMPLE = json.dumps([
    {
        "nameWithOwner": "0ai-Cyberviser/PeachTree",
        "url": "https://github.com/0ai-Cyberviser/PeachTree",
        "isPrivate": False,
        "isArchived": False,
        "defaultBranchRef": {"name": "main"},
        "licenseInfo": {"spdxId": "Apache-2.0"},
        "diskUsage": 12,
    },
    {
        "nameWithOwner": "0ai-Cyberviser/PrivateDemo",
        "url": "https://github.com/0ai-Cyberviser/PrivateDemo",
        "isPrivate": True,
        "isArchived": False,
        "defaultBranchRef": {"name": "main"},
        "licenseInfo": None,
        "diskUsage": 3,
    },
    {
        "nameWithOwner": "0ai-Cyberviser/Archived",
        "url": "https://github.com/0ai-Cyberviser/Archived",
        "isPrivate": False,
        "isArchived": True,
        "defaultBranchRef": {"name": "main"},
        "licenseInfo": {"spdxId": "MIT"},
        "diskUsage": 1,
    },
])


def test_from_gh_json_parses_repositories():
    repos = OwnedGitHubConnector().from_gh_json(SAMPLE)
    assert len(repos) == 3
    assert repos[0].full_name == "0ai-Cyberviser/PeachTree"
    assert repos[0].clone_url.endswith(".git")
    assert repos[0].visibility == "public"


def test_filter_repos_excludes_archived_by_default():
    repos = OwnedGitHubConnector().from_gh_json(SAMPLE)
    filtered = OwnedGitHubConnector().filter_repos(repos)
    assert all(not repo.archived for repo in filtered)


def test_filter_repos_can_exclude_private():
    repos = OwnedGitHubConnector().from_gh_json(SAMPLE)
    filtered = OwnedGitHubConnector().filter_repos(repos, include_private=False)
    assert all(repo.visibility != "private" for repo in filtered)


def test_write_and_read_inventory(tmp_path: Path):
    connector = OwnedGitHubConnector()
    repos = connector.filter_repos(connector.from_gh_json(SAMPLE))
    path = connector.write_inventory(repos, tmp_path / "owned.jsonl")
    loaded = connector.read_inventory(path)
    assert [repo.full_name for repo in loaded] == [repo.full_name for repo in repos]


def test_write_scripts(tmp_path: Path):
    connector = OwnedGitHubConnector()
    repos = [OwnedRepo("0ai-Cyberviser/PeachTree", "https://github.com/0ai-Cyberviser/PeachTree.git", license_id="apache-2.0")]
    plan = connector.write_scripts(
        repos,
        tmp_path / "repos",
        tmp_path / "scripts" / "clone.sh",
        tmp_path / "scripts" / "datasets.sh",
    )
    assert plan.repo_count == 1
    assert "gh repo clone" in (tmp_path / "scripts" / "clone.sh").read_text(encoding="utf-8")
    assert "peachtree ingest-local" in (tmp_path / "scripts" / "datasets.sh").read_text(encoding="utf-8")


def test_cli_github_owned_from_json(tmp_path: Path, capsys):
    sample = tmp_path / "repos.json"
    sample.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "owned.jsonl"
    rc = main(["github-owned", "--from-json", str(sample), "--output", str(out)])
    assert rc == 0
    assert out.exists()
    assert '"repositories": 2' in capsys.readouterr().out


def test_cli_github_plan(tmp_path: Path, capsys):
    connector = OwnedGitHubConnector()
    inv = connector.write_inventory(
        [OwnedRepo("0ai-Cyberviser/PeachTree", "https://github.com/0ai-Cyberviser/PeachTree.git", license_id="apache-2.0")],
        tmp_path / "owned.jsonl",
    )
    rc = main([
        "github-plan",
        "--inventory", str(inv),
        "--clone-root", str(tmp_path / "repos"),
        "--clone-script", str(tmp_path / "clone.sh"),
        "--dataset-script", str(tmp_path / "datasets.sh"),
    ])
    assert rc == 0
    assert '"repo_count": 1' in capsys.readouterr().out
    assert (tmp_path / "clone.sh").exists()
    assert (tmp_path / "datasets.sh").exists()


def test_write_scripts_preserves_clone_root_expansion(tmp_path: Path):
    connector = OwnedGitHubConnector()
    repos = [OwnedRepo("0ai-Cyberviser/PeachTree", "https://github.com/0ai-Cyberviser/PeachTree.git", license_id="apache-2.0")]
    connector.write_scripts(repos, tmp_path / "repos", tmp_path / "clone.sh", tmp_path / "datasets.sh")
    clone_text = (tmp_path / "clone.sh").read_text(encoding="utf-8")
    dataset_text = (tmp_path / "datasets.sh").read_text(encoding="utf-8")
    assert "'${CLONE_ROOT}" not in clone_text
    assert "'${CLONE_ROOT}" not in dataset_text
    assert '"${CLONE_ROOT}/0ai-Cyberviser__PeachTree"' in clone_text
    assert '"${CLONE_ROOT}/0ai-Cyberviser__PeachTree"' in dataset_text
