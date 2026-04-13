from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources


@dataclass(frozen=True)
class AssetSpec:
    path: str
    ownership: str
    render: bool = False
    marker_start: str | None = None
    marker_end: str | None = None
    fingerprint: str = "file"
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AssetSpec":
        return cls(
            path=str(data["path"]),
            ownership=str(data["ownership"]),
            render=bool(data.get("render", False)),
            marker_start=str(data["marker_start"]) if data.get("marker_start") else None,
            marker_end=str(data["marker_end"]) if data.get("marker_end") else None,
            fingerprint=str(data.get("fingerprint") or "file"),
            description=str(data.get("description") or ""),
        )


@dataclass(frozen=True)
class AssetBundle:
    name: str
    version: str
    package_root: tuple[str, ...]
    assets: tuple[AssetSpec, ...]
    create_directories: tuple[str, ...] = field(default_factory=tuple)

    def read_text(self, asset: AssetSpec) -> str:
        traversable = resources.files("allox").joinpath(*self.package_root, *asset.path.split("/"))
        return traversable.read_text(encoding="utf-8")


def _load_bundle(*package_root: str) -> AssetBundle:
    manifest_file = resources.files("allox").joinpath(*package_root, "manifest.json")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assets = tuple(AssetSpec.from_dict(item) for item in manifest["assets"])
    create_directories = tuple(manifest.get("create_directories") or [])
    return AssetBundle(
        name=str(manifest["bundle_name"]),
        version=str(manifest["bundle_version"]),
        package_root=package_root,
        assets=assets,
        create_directories=create_directories,
    )


def load_project_template_bundle(template: str = "default") -> AssetBundle:
    return _load_bundle("assets", "project_template", template)
