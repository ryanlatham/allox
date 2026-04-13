from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".allox" / "manifest.json").exists():
            return candidate
    return None
