from __future__ import annotations

import argparse

from ..core.assets import load_project_template_bundle
from ..version import __version__


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("version", help="Print the allox version")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    template_bundle = load_project_template_bundle()
    print(f"allox {__version__}")
    print(f"template {template_bundle.name} {template_bundle.version}")
    return 0
