from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .assets import AssetBundle, AssetSpec
from .hashing import sha256_text
from .manifest import ManagedFileRecord, ProjectManifest, utc_now
from .markers import MarkerError, extract_managed_block, extract_managed_body, replace_managed_block
from .pathing import ensure_directory
from .templating import render_text


@dataclass
class UpgradeResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScaffoldOperation:
    path: str
    action: str
    content: str
    ownership: str


@dataclass(frozen=True)
class ScaffoldConflict:
    path: str
    reason: str


class ScaffoldConflictError(ValueError):
    def __init__(self, conflicts: list[ScaffoldConflict]) -> None:
        self.conflicts = conflicts
        message = "\n".join(f"{item.path}: {item.reason}" for item in conflicts)
        super().__init__(message)


def render_bundle(bundle: AssetBundle, context: dict[str, object]) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for asset in bundle.assets:
        raw = bundle.read_text(asset)
        rendered[asset.path] = render_text(raw, context) if asset.render else raw
    return rendered


def record_for_asset(
    asset: AssetSpec,
    content: str,
    ownership_override: str | None = None,
) -> ManagedFileRecord | None:
    ownership = ownership_override or asset.ownership
    if ownership == "project":
        return None
    managed_hash = None
    marker_start, marker_end = _markers_for_asset(asset, ownership)
    if ownership == "section" and marker_start and marker_end:
        managed_hash = sha256_text(extract_managed_body(content, marker_start, marker_end))
    return ManagedFileRecord(
        path=asset.path,
        ownership=ownership,
        file_hash=sha256_text(content),
        managed_hash=managed_hash,
    )


def scaffold_bundle(
    target_root: Path,
    bundle: AssetBundle,
    context: dict[str, object],
    dry_run: bool = False,
) -> tuple[dict[str, ManagedFileRecord], list[str]]:
    rendered = render_bundle(bundle, context)
    operations = plan_scaffold_bundle(target_root, bundle, rendered)
    records: dict[str, ManagedFileRecord] = {}
    actions: list[str] = []

    for directory in bundle.create_directories:
        if not dry_run:
            ensure_directory(target_root / directory)

    for operation in operations:
        target_file = target_root / operation.path
        if not dry_run:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(operation.content, encoding="utf-8")
        asset = next(asset for asset in bundle.assets if asset.path == operation.path)
        record = record_for_asset(asset, operation.content, ownership_override=operation.ownership)
        if record:
            records[asset.path] = record
        actions.append(f"{operation.action} {operation.path}")

    return records, actions


def plan_scaffold_bundle(
    target_root: Path,
    bundle: AssetBundle,
    rendered: dict[str, str],
) -> list[ScaffoldOperation]:
    conflicts: list[ScaffoldConflict] = []
    operations: list[ScaffoldOperation] = []

    for directory in bundle.create_directories:
        conflicts.extend(_directory_conflicts(target_root, Path(directory)))

    for asset in bundle.assets:
        relative = Path(asset.path)
        target_file = target_root / relative
        conflicts.extend(_parent_directory_conflicts(target_root, relative))
        if target_file.exists():
            if target_file.is_dir():
                conflicts.append(
                    ScaffoldConflict(
                        path=asset.path,
                        reason="expected a file here, but found an existing directory",
                    )
                )
                continue
            if target_file.suffix.lower() != ".md":
                conflicts.append(
                    ScaffoldConflict(
                        path=asset.path,
                        reason="existing file would be overwritten",
                    )
                )
                continue
            ownership = "section"
            candidate = _prepare_scaffold_content(asset, rendered[asset.path], ownership)
            current = target_file.read_text(encoding="utf-8")
            marker_start, marker_end = _markers_for_asset(asset, ownership)
            if marker_start and marker_end and (marker_start in current or marker_end in current):
                conflicts.append(
                    ScaffoldConflict(
                        path=asset.path,
                        reason="existing markdown file already contains allox-managed markers",
                    )
                )
                continue
            operations.append(
                ScaffoldOperation(
                    path=asset.path,
                    action="appended",
                    content=_append_markdown(current, candidate),
                    ownership=ownership,
                )
            )
            continue

        ownership = asset.ownership
        candidate = _prepare_scaffold_content(asset, rendered[asset.path], ownership)
        operations.append(
            ScaffoldOperation(
                path=asset.path,
                action="created",
                content=candidate,
                ownership=ownership,
            )
        )

    if conflicts:
        raise ScaffoldConflictError(conflicts)

    return operations


def upgrade_project(
    project_root: Path,
    bundle: AssetBundle,
    context: dict[str, object],
    manifest: ProjectManifest,
    dry_run: bool = False,
    write_conflicts: bool = True,
) -> tuple[ProjectManifest, UpgradeResult]:
    rendered = render_bundle(bundle, context)
    result = UpgradeResult()
    new_records = dict(manifest.managed_files)

    for asset in bundle.assets:
        target_file = project_root / asset.path
        existing_record = manifest.managed_files.get(asset.path)
        ownership = existing_record.ownership if existing_record else asset.ownership
        candidate = _prepare_scaffold_content(asset, rendered[asset.path], ownership)

        if ownership == "project":
            result.skipped.append(asset.path)
            continue

        if not target_file.exists():
            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(candidate, encoding="utf-8")
            new_record = record_for_asset(asset, candidate, ownership_override=ownership)
            if new_record:
                new_records[asset.path] = new_record
            result.created.append(asset.path)
            continue

        current = target_file.read_text(encoding="utf-8")
        if ownership == "managed":
            current_hash = sha256_text(current)
            if existing_record and current_hash != existing_record.file_hash:
                result.conflicts.append(asset.path)
                _write_conflict(project_root, asset.path, candidate, dry_run, write_conflicts)
                continue
            if current != candidate:
                if not dry_run:
                    target_file.write_text(candidate, encoding="utf-8")
                result.updated.append(asset.path)
            else:
                result.skipped.append(asset.path)
            new_record = record_for_asset(asset, candidate, ownership_override=ownership)
            if new_record:
                new_records[asset.path] = new_record
            continue

        marker_start, marker_end = _markers_for_asset(asset, ownership)
        try:
            current_body = extract_managed_body(current, marker_start or "", marker_end or "")
            candidate_block = extract_managed_block(candidate, marker_start or "", marker_end or "")
            current_managed_hash = sha256_text(current_body)
        except MarkerError:
            result.conflicts.append(asset.path)
            _write_conflict(project_root, asset.path, candidate, dry_run, write_conflicts)
            continue

        if existing_record and existing_record.managed_hash and current_managed_hash != existing_record.managed_hash:
            result.conflicts.append(asset.path)
            _write_conflict(project_root, asset.path, candidate, dry_run, write_conflicts)
            continue

        updated = replace_managed_block(current, candidate_block, marker_start or "", marker_end or "")
        if updated != current:
            if not dry_run:
                target_file.write_text(updated, encoding="utf-8")
            result.updated.append(asset.path)
        else:
            result.skipped.append(asset.path)
        new_record = record_for_asset(asset, updated, ownership_override=ownership)
        if new_record:
            new_records[asset.path] = new_record

    manifest.framework_version = context["framework_version"]  # type: ignore[index]
    manifest.template_version = bundle.version
    manifest.updated_at = utc_now()
    manifest.managed_files = new_records
    return manifest, result


def _write_conflict(
    project_root: Path,
    relative_path: str,
    candidate_content: str,
    dry_run: bool,
    write_conflicts: bool,
) -> None:
    if not write_conflicts or dry_run:
        return
    conflict_path = project_root / ".allox" / "conflicts" / f"{relative_path}.allox.new"
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    conflict_path.write_text(candidate_content, encoding="utf-8")


def _directory_conflicts(target_root: Path, relative: Path) -> list[ScaffoldConflict]:
    conflicts = _parent_directory_conflicts(target_root, relative)
    target = target_root / relative
    if target.exists() and not target.is_dir():
        conflicts.append(
            ScaffoldConflict(
                path=relative.as_posix(),
                reason="expected a directory here, but found an existing file",
            )
        )
    return conflicts


def _parent_directory_conflicts(target_root: Path, relative: Path) -> list[ScaffoldConflict]:
    conflicts: list[ScaffoldConflict] = []
    current = target_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() and not current.is_dir():
            conflicts.append(
                ScaffoldConflict(
                    path=current.relative_to(target_root).as_posix(),
                    reason="expected a directory in this path, but found an existing file",
                )
            )
            break
    return conflicts


def _markers_for_asset(asset: AssetSpec, ownership: str) -> tuple[str | None, str | None]:
    if ownership != "section":
        return asset.marker_start, asset.marker_end
    if asset.marker_start and asset.marker_end:
        return asset.marker_start, asset.marker_end
    if asset.path.endswith(".md"):
        return "<!-- allox:begin managed -->", "<!-- allox:end managed -->"
    return asset.marker_start, asset.marker_end


def _prepare_scaffold_content(asset: AssetSpec, content: str, ownership: str) -> str:
    marker_start, marker_end = _markers_for_asset(asset, ownership)
    if ownership != "section" or (asset.marker_start and asset.marker_end):
        return content
    if marker_start and marker_end and asset.path.endswith(".md"):
        return f"{marker_start}\n{content.rstrip()}\n{marker_end}\n"
    return content


def _append_markdown(current: str, addition: str) -> str:
    if not current:
        return addition if addition.endswith("\n") else addition + "\n"
    separator = ""
    if not current.endswith("\n"):
        separator += "\n"
    if not current.endswith("\n\n"):
        separator += "\n"
    appended = current + separator + addition
    return appended if appended.endswith("\n") else appended + "\n"
