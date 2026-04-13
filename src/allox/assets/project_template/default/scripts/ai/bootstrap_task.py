#!/usr/bin/env python3
import os
import pathlib
import subprocess
import sys


def main() -> int:
    project_root = pathlib.Path(__file__).resolve().parents[2]
    command = [os.environ.get("ALLOX_BIN", "allox"), "project", "bootstrap-task", "--project", str(project_root)]
    command.extend(sys.argv[1:])
    return subprocess.call(command, cwd=project_root)


if __name__ == "__main__":
    raise SystemExit(main())
