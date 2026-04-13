#!/usr/bin/env python3
import os
import pathlib
import subprocess


def main() -> int:
    project_root = pathlib.Path(__file__).resolve().parents[2]
    command = [
        os.environ.get("ALLOX_BIN", "allox"),
        "doctor",
        "--project",
        str(project_root),
    ]
    return subprocess.call(command, cwd=project_root)


if __name__ == "__main__":
    raise SystemExit(main())
