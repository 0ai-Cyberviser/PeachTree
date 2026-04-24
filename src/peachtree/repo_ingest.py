from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import SourceDocument

DEFAULT_INCLUDE_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".graphql"
}
DEFAULT_EXCLUDE_PARTS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", ".mypy_cache", ".ruff_cache",
}


def iter_local_documents(
    repo: str | Path,
    repo_name: str,
    suffixes: Iterable[str] | None = None,
    license_id: str = "unknown",
    max_file_bytes: int = 256_000,
) -> list[SourceDocument]:
    root = Path(repo)
    allowed = set(suffixes or DEFAULT_INCLUDE_SUFFIXES)
    docs: list[SourceDocument] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in DEFAULT_EXCLUDE_PARTS for part in rel.parts):
            continue
        if path.suffix.lower() not in allowed:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        docs.append(SourceDocument(repo_name=repo_name, path=str(rel), content=content, license_id=license_id))
    return docs
