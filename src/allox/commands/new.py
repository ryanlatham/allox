from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..core.assets import load_project_template_bundle
from ..core.doctoring import collect_doctor_report, format_doctor_report
from ..core.manifest import ProjectManifest, manifest_path
from ..core.subprocesses import resolve_binary, run_command
from ..core.upgrade import ScaffoldConflictError, scaffold_bundle
from ..version import __version__

_DRY_RUN_VERBS = {
    "appended": "append",
    "created": "create",
    "initialized": "initialize",
}


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("new", help="Create a new allox-managed project")
    parser.add_argument("path", help="Target project path")
    parser.add_argument("--project-name", help="Human-readable project name")
    parser.add_argument("--template", default="default")
    parser.add_argument("--stack", default="generic")
    parser.add_argument("--init-git", action="store_true")
    parser.add_argument("--skip-doctor", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    project_name = args.project_name or target.name
    if manifest_path(target).exists():
        print(
            f"Target is already an allox-managed project: {target}\nUse `allox upgrade` instead.",
            file=sys.stderr,
        )
        return 1

    bundle = load_project_template_bundle(args.template)
    context = {
        "project_name": project_name,
        "framework_version": __version__,
        "template_name": bundle.name,
    }
    try:
        records, written = scaffold_bundle(target, bundle, context, dry_run=args.dry_run)
    except ScaffoldConflictError as exc:
        print(f"Cannot initialize allox in {target} because conflicts were detected:", file=sys.stderr)
        for conflict in exc.conflicts:
            print(f"- {conflict.path}: {conflict.reason}", file=sys.stderr)
        print("Resolve the conflicts and rerun `allox new`.", file=sys.stderr)
        return 1

    actions = list(written)
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    manifest = ProjectManifest(
        framework_name="allox",
        framework_version=__version__,
        template=bundle.name,
        template_version=bundle.version,
        stack=args.stack,
        project_name=project_name,
        managed_files=records,
    )
    actions.append(f"created {manifest_path(target).relative_to(target).as_posix()}")
    if not args.dry_run:
        manifest.write(manifest_path(target))

    git = None
    if args.init_git:
        git = resolve_binary("git")
        if git:
            actions.append("initialized .git")
            if not args.dry_run:
                run_command([git, "init"], cwd=target)
        else:
            print(
                "Git initialization was requested, but `git` could not be resolved.",
                file=sys.stderr,
            )

    if args.dry_run:
        print(f"Dry run for allox project at {target}")
    else:
        print(f"Created allox project at {target}")
    for action in actions:
        print(_format_action(action, dry_run=args.dry_run))
    if args.dry_run:
        print("")
        print("No files were written.")
        return 0

    if not args.skip_doctor:
        print("")
        print(format_doctor_report(collect_doctor_report(project_path=target)))

    print("")
    print("Next steps:")
    print(f"1. Open {target} in Codex.")
    print("2. Read AGENTS.md and docs/ai-workflow.md.")
    print("3. Start with PROMPTS/CODEX_PROJECT_START.md and bootstrap the first task.")
    return 0


def _format_action(action: str, dry_run: bool) -> str:
    if not dry_run:
        return f"- {action}"
    verb, _, detail = action.partition(" ")
    present_tense = _DRY_RUN_VERBS.get(verb, verb)
    return f"- would {present_tense} {detail}".rstrip()
