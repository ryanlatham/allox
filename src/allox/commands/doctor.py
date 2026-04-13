from __future__ import annotations

import argparse
from pathlib import Path

from ..core.doctoring import collect_doctor_report, doctor_report_json, format_doctor_report


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("doctor", help="Check local allox prerequisites")
    parser.add_argument("--project", help="Explicit project path")
    parser.add_argument("--online", action="store_true", help="Run provider-authenticated readiness checks")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    project_path = Path(args.project).expanduser() if args.project else None
    report = collect_doctor_report(project_path=project_path, online=args.online)
    if args.json:
        print(doctor_report_json(report))
    else:
        print(format_doctor_report(report))

    has_binary_issues = any(
        (not item["found"]) or item.get("status") not in {"ok", None}
        for item in report["binaries"].values()
    )
    has_online_issues = args.online and any(
        item.get("online_ready") is False for name, item in report["binaries"].items() if name in {"codex", "claude", "gemini"}
    )
    if not report["python"]["supported"]:
        return 1
    return 1 if (has_binary_issues or has_online_issues) else 0
