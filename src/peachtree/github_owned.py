"""Owned GitHub repository connector.

This module is intentionally conservative. It supports repository inventory and
reviewable plan generation for repositories the operator can already access.
It does not scrape all of GitHub, bypass access controls, or clone repos unless
the operator explicitly runs the generated script.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any

from .github_policy import GitHubCollectionPolicy


@dataclass(frozen=True)
class OwnedRepo:
    full_name: str
    clone_url: str
    visibility: str = "unknown"
    default_branch: str = "main"
    archived: bool = False
    license_id: str = "unknown"
    size_kb: int = 0

    @property
    def safe_dir_name(self) -> str:
        return self.full_name.replace("/", "__").replace(" ", "_")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OwnedRepoPlan:
    inventory_path: str
    clone_root: str
    clone_script: str
    dataset_script: str
    repo_count: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


class OwnedGitHubConnector:
    """Builds reviewed inventory and dataset scripts for owned GitHub repos."""

    def __init__(self, policy: GitHubCollectionPolicy | None = None) -> None:
        self.policy = policy or GitHubCollectionPolicy(allow_owned_repos=True)

    def list_with_gh(self, owner: str | None = None, limit: int = 100) -> list[OwnedRepo]:
        """List accessible repos using GitHub CLI.

        This requires `gh auth login` locally. Tests should use `from_gh_json`.
        """
        if limit > self.policy.max_repos_per_run:
            raise ValueError("limit exceeds policy max_repos_per_run")

        cmd = [
            "gh",
            "repo",
            "list",
            owner or "",
            "--limit",
            str(limit),
            "--json",
            "nameWithOwner,url,visibility,isArchived,defaultBranchRef,licenseInfo,diskUsage",
        ]
        cmd = [part for part in cmd if part != ""]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "gh repo list failed")
        return self.from_gh_json(proc.stdout)

    def from_gh_json(self, raw: str) -> list[OwnedRepo]:
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("GitHub repository JSON must be a list")
        repos: list[OwnedRepo] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            full_name = item.get("nameWithOwner") or item.get("repository_full_name") or item.get("full_name")
            url = item.get("url") or item.get("clone_url")
            if not full_name or not url:
                continue
            branch = item.get("defaultBranchRef") or {}
            if isinstance(branch, dict):
                default_branch = branch.get("name") or "main"
            else:
                default_branch = str(branch or "main")
            license_info = item.get("licenseInfo") or {}
            if isinstance(license_info, dict):
                license_id = (license_info.get("spdxId") or "unknown").lower()
            else:
                license_id = "unknown"
            repos.append(
                OwnedRepo(
                    full_name=str(full_name),
                    clone_url=str(url) + (".git" if str(url).startswith("https://github.com/") and not str(url).endswith(".git") else ""),
                    visibility=str(item.get("visibility", "unknown")).lower(),
                    default_branch=default_branch,
                    archived=bool(item.get("isArchived", item.get("archived", False))),
                    license_id=license_id,
                    size_kb=int(item.get("diskUsage", item.get("size_kb", 0)) or 0),
                )
            )
        return repos

    def filter_repos(
        self,
        repos: list[OwnedRepo],
        include_private: bool = True,
        include_archived: bool = False,
        allowed_licenses: set[str] | None = None,
    ) -> list[OwnedRepo]:
        allow = {license_id.lower() for license_id in (allowed_licenses or set(self.policy.allowed_licenses) | {"unknown"})}
        output: list[OwnedRepo] = []
        for repo in repos:
            if repo.archived and not include_archived:
                continue
            if repo.visibility == "private" and not include_private:
                continue
            if repo.license_id.lower() not in allow:
                continue
            output.append(repo)
        return output[: self.policy.max_repos_per_run]

    def write_inventory(self, repos: list[OwnedRepo], output: str | Path) -> Path:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(json.dumps(repo.to_dict(), sort_keys=True) for repo in repos) + ("\n" if repos else ""), encoding="utf-8")
        return out

    def read_inventory(self, path: str | Path) -> list[OwnedRepo]:
        repos: list[OwnedRepo] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                repos.append(OwnedRepo(**json.loads(line)))
        return repos

    def write_scripts(
        self,
        repos: list[OwnedRepo],
        clone_root: str | Path,
        clone_script: str | Path,
        dataset_script: str | Path,
    ) -> OwnedRepoPlan:
        clone_root = Path(clone_root)
        clone_script = Path(clone_script)
        dataset_script = Path(dataset_script)
        clone_script.parent.mkdir(parents=True, exist_ok=True)
        dataset_script.parent.mkdir(parents=True, exist_ok=True)

        clone_lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f'CLONE_ROOT="{shlex.quote(str(clone_root))}"',
            'mkdir -p "$CLONE_ROOT"',
            "",
        ]
        dataset_lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f'CLONE_ROOT="{shlex.quote(str(clone_root))}"',
            'mkdir -p data/raw data/datasets data/manifests',
            "",
        ]

        for repo in repos:
            target = f'${{CLONE_ROOT}}/{repo.safe_dir_name}'
            clone_lines += [
                f'if [ ! -d "{target}/.git" ]; then',
                f"  gh repo clone {shlex.quote(repo.full_name)} {shlex.quote(target)} -- --depth 1",
                "else",
                f'  git -C "{target}" pull --ff-only',
                "fi",
                "",
            ]
            raw = f"data/raw/{repo.safe_dir_name}.jsonl"
            dataset = f"data/datasets/{repo.safe_dir_name}-instruct.jsonl"
            manifest = f"data/manifests/{repo.safe_dir_name}.json"
            dataset_lines += [
                f'peachtree ingest-local --repo "{target}" --repo-name {shlex.quote(repo.full_name)} --license {shlex.quote(repo.license_id)} --output {shlex.quote(raw)}',
                f"peachtree build --source {shlex.quote(raw)} --dataset {shlex.quote(dataset)} --manifest {shlex.quote(manifest)} --domain {shlex.quote(repo.safe_dir_name)}",
                f"peachtree audit --dataset {shlex.quote(dataset)}",
                "",
            ]

        clone_script.write_text("\n".join(clone_lines), encoding="utf-8")
        dataset_script.write_text("\n".join(dataset_lines), encoding="utf-8")
        clone_script.chmod(0o755)
        dataset_script.chmod(0o755)

        return OwnedRepoPlan(
            inventory_path="",
            clone_root=str(clone_root),
            clone_script=str(clone_script),
            dataset_script=str(dataset_script),
            repo_count=len(repos),
        )
