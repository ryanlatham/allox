from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path


def create_executable(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@dataclass(frozen=True)
class FakeBundle:
    name: str
    version: str
    assets: tuple[object, ...]
    file_map: dict[str, str]
    create_directories: tuple[str, ...] = ()

    def read_text(self, asset) -> str:
        return self.file_map[asset.path]
