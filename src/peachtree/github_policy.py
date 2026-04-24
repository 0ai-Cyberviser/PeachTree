from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubCollectionPolicy:
    allow_public_github: bool = False
    allow_owned_repos: bool = True
    allowed_licenses: tuple[str, ...] = ("apache-2.0", "mit", "bsd-2-clause", "bsd-3-clause", "mpl-2.0")
    max_repos_per_run: int = 25
    max_files_per_repo: int = 500

    def validate_public_collection(self) -> None:
        if not self.allow_public_github:
            raise PermissionError("public GitHub collection is disabled; pass explicit opt-in policy")
        if not self.allowed_licenses:
            raise ValueError("public GitHub collection requires a license allowlist")
        if self.max_repos_per_run > 100:
            raise ValueError("max_repos_per_run too high for safe/rate-limited operation")
