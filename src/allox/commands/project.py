from __future__ import annotations

import argparse
from pathlib import Path

from ..core.pathing import find_project_root
from ..core.runtime import bootstrap_task, cleanup, closeout, milestone_gate, plan_gate, worktree_setup


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("project", help="Internal project runtime commands")
    project_subparsers = parser.add_subparsers(dest="project_command")

    bootstrap = project_subparsers.add_parser("bootstrap-task", help="Create task artifacts")
    bootstrap.add_argument("--project", help="Project root path")
    bootstrap.add_argument("--title", help="Task title")
    bootstrap.set_defaults(handler=run_bootstrap)

    planning = project_subparsers.add_parser("plan-gate", help="Run the plan review gate")
    planning.add_argument("--project", help="Project root path")
    planning.add_argument("--task-id", help="Existing task ID")
    planning.set_defaults(handler=run_plan_gate)

    milestone = project_subparsers.add_parser("milestone-gate", help="Run deterministic checks and reviewer lanes")
    milestone.add_argument("--project", help="Project root path")
    milestone.add_argument("--task-id", help="Existing task ID")
    milestone.set_defaults(handler=run_milestone_gate)

    finishing = project_subparsers.add_parser("closeout", help="Run the final gate and write closeout artifacts")
    finishing.add_argument("--project", help="Project root path")
    finishing.add_argument("--task-id", help="Existing task ID")
    finishing.set_defaults(handler=run_closeout)

    cleaning = project_subparsers.add_parser("cleanup", help="Clean temporary artifacts")
    cleaning.add_argument("--project", help="Project root path")
    cleaning.set_defaults(handler=run_cleanup)

    worktree = project_subparsers.add_parser("worktree-setup", help="Prepare worktree metadata")
    worktree.add_argument("--project", help="Project root path")
    worktree.set_defaults(handler=run_worktree_setup)


def _resolve_project_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    detected = find_project_root(Path.cwd())
    if not detected:
        raise SystemExit("no allox project found; pass --project explicitly")
    return detected


def _print_result(result) -> int:
    print(result.message)
    for path in result.paths:
        print(f"- {path}")
    return 0


def run_bootstrap(args: argparse.Namespace) -> int:
    return _print_result(bootstrap_task(_resolve_project_root(args.project), title=args.title))


def run_plan_gate(args: argparse.Namespace) -> int:
    return _print_result(plan_gate(_resolve_project_root(args.project), task_id=args.task_id))


def run_milestone_gate(args: argparse.Namespace) -> int:
    return _print_result(milestone_gate(_resolve_project_root(args.project), task_id=args.task_id))


def run_closeout(args: argparse.Namespace) -> int:
    return _print_result(closeout(_resolve_project_root(args.project), task_id=args.task_id))


def run_cleanup(args: argparse.Namespace) -> int:
    return _print_result(cleanup(_resolve_project_root(args.project)))


def run_worktree_setup(args: argparse.Namespace) -> int:
    return _print_result(worktree_setup(_resolve_project_root(args.project)))
