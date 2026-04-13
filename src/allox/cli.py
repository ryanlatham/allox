from __future__ import annotations

import argparse
import sys

from .commands import doctor, new, project, self_test, upgrade, version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="allox",
        description="Bootstrap and maintain Codex-led framework projects.",
    )
    subparsers = parser.add_subparsers(dest="command")

    new.build_parser(subparsers)
    doctor.build_parser(subparsers)
    upgrade.build_parser(subparsers)
    version.build_parser(subparsers)
    self_test.build_parser(subparsers)
    project.build_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help(sys.stderr)
        return 1
    return int(args.handler(args) or 0)
