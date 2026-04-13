from __future__ import annotations

import argparse
from pathlib import Path

from ..core.assets import load_project_template_bundle
from ..core.manifest import ProjectManifest, manifest_path
from ..core.upgrade import upgrade_project
from ..version import __version__


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("upgrade", help="Upgrade an existing allox project")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--project", help="Explicit project path override")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--write-conflicts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write conflict copies under .allox/conflicts (default: true)",
    )
    parser.add_argument("--yes", action="store_true", help="Reserved for non-interactive parity")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    raw_target = args.project or args.path
    project_root = Path(raw_target).expanduser().resolve()
    manifest_file = manifest_path(project_root)
    if not manifest_file.exists():
        raise SystemExit(f"not an allox project: {project_root}")
    manifest = ProjectManifest.read(manifest_file)
    bundle = load_project_template_bundle(manifest.template)
    context = {
        "project_name": manifest.project_name or project_root.name,
        "framework_version": __version__,
        "template_name": bundle.name,
    }
    updated_manifest, result = upgrade_project(
        project_root=project_root,
        bundle=bundle,
        context=context,
        manifest=manifest,
        dry_run=args.dry_run,
        write_conflicts=args.write_conflicts,
    )
    if not args.dry_run:
        updated_manifest.write(manifest_file)

    print(f"Upgraded {project_root}")
    for label, items in (
        ("created", result.created),
        ("updated", result.updated),
        ("skipped", result.skipped),
        ("conflicts", result.conflicts),
    ):
        print(f"{label}: {len(items)}")
        for item in items:
            print(f"- {item}")
    return 1 if result.conflicts else 0
