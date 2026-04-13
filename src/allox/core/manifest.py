from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ManagedFileRecord:
    path: str
    ownership: str
    file_hash: str
    managed_hash: str | None = None
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "path": self.path,
            "ownership": self.ownership,
            "file_hash": self.file_hash,
            "updated_at": self.updated_at,
        }
        if self.managed_hash is not None:
            data["managed_hash"] = self.managed_hash
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ManagedFileRecord":
        return cls(
            path=str(data["path"]),
            ownership=str(data["ownership"]),
            file_hash=str(data["file_hash"]),
            managed_hash=str(data["managed_hash"]) if data.get("managed_hash") else None,
            updated_at=str(data.get("updated_at") or utc_now()),
        )


@dataclass
class ProjectManifest:
    framework_name: str
    framework_version: str
    template: str
    template_version: str
    stack: str
    project_name: str
    generated_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    managed_files: dict[str, ManagedFileRecord] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "framework_name": self.framework_name,
            "framework_version": self.framework_version,
            "template": self.template,
            "template_version": self.template_version,
            "stack": self.stack,
            "project_name": self.project_name,
            "generated_at": self.generated_at,
            "updated_at": self.updated_at,
            "managed_files": {
                path: record.to_dict()
                for path, record in sorted(self.managed_files.items())
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProjectManifest":
        managed_files = {
            path: ManagedFileRecord.from_dict(record)
            for path, record in dict(data.get("managed_files") or {}).items()
        }
        return cls(
            framework_name=str(data["framework_name"]),
            framework_version=str(data["framework_version"]),
            template=str(data["template"]),
            template_version=str(data["template_version"]),
            stack=str(data.get("stack") or "generic"),
            project_name=str(data.get("project_name") or ""),
            generated_at=str(data.get("generated_at") or utc_now()),
            updated_at=str(data.get("updated_at") or utc_now()),
            managed_files=managed_files,
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "ProjectManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def manifest_path(project_root: Path) -> Path:
    return project_root / ".allox" / "manifest.json"
