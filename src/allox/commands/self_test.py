from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from ..core.assets import load_project_template_bundle
from ..core.manifest import ProjectManifest, manifest_path
from ..core.upgrade import scaffold_bundle
from ..version import __version__
from .project import run_bootstrap, run_cleanup, run_closeout, run_milestone_gate, run_plan_gate


REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".codex/config.toml",
    ".codex/README.md",
    "docs/ai-workflow.md",
    "scripts/ai/bootstrap_task.py",
]


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("self-test", help="Run a local allox smoke test")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    bundle = load_project_template_bundle()
    with tempfile.TemporaryDirectory(prefix="allox-self-test-") as temp_dir:
        root = Path(temp_dir) / "sample-project"
        root.mkdir(parents=True, exist_ok=True)
        records, _ = scaffold_bundle(
            root,
            bundle,
            {"project_name": "sample-project", "framework_version": __version__, "template_name": bundle.name},
        )
        manifest = ProjectManifest(
            framework_name="allox",
            framework_version=__version__,
            template=bundle.name,
            template_version=bundle.version,
            stack="generic",
            project_name="sample-project",
            managed_files=records,
        )
        manifest.write(manifest_path(root))

        missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
        if missing:
            print("Self-test failed:")
            for path in missing:
                print(f"- missing {path}")
            return 1

        if _configure_runtime_self_test(root, Path(temp_dir)) != 0:
            return 1

        project_args = argparse.Namespace(project=str(root), task_id=None, title="Test runtime")
        if run_bootstrap(project_args) != 0:
            return 1
        task_id = sorted((root / "ai" / "tasks").glob("*.md"))[-1].stem
        if run_plan_gate(argparse.Namespace(project=str(root), task_id=task_id)) != 0:
            return 1
        if run_milestone_gate(argparse.Namespace(project=str(root), task_id=task_id)) != 0:
            return 1
        if run_closeout(argparse.Namespace(project=str(root), task_id=task_id)) != 0:
            return 1
        if run_cleanup(argparse.Namespace(project=str(root))) != 0:
            return 1

        required_runtime_outputs = [
            root / "ai" / "reviews" / f"{task_id}-plan_gate-fake-plan.json",
            root / "ai" / "reviews" / f"{task_id}-milestone_gate-fake-milestone.json",
            root / "ai" / "archive" / f"{task_id}.md",
            root / "ai" / "archive" / f"{task_id}-adjudication.md",
        ]
        missing_runtime = [path.relative_to(root).as_posix() for path in required_runtime_outputs if not path.exists()]
        if missing_runtime:
            print("Self-test failed:")
            for path in missing_runtime:
                print(f"- missing runtime artifact {path}")
            return 1

        print(f"Self-test passed in {root}")
    return 0


def _configure_runtime_self_test(project_root: Path, temp_root: Path) -> int:
    reviewer = temp_root / "reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "label = sys.argv[1] if len(sys.argv) > 1 else 'reviewer'\n"
        "print(json.dumps({'summary': f'{label} ok', 'findings': []}))\n",
        encoding="utf-8",
    )
    reviewer.chmod(0o755)
    checker = temp_root / "checker.py"
    checker.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print(f'{sys.argv[1]} checks ok')\n",
        encoding="utf-8",
    )
    checker.chmod(0o755)

    config_path = project_root / "ai" / "config" / "project_commands.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["checks"] = {
        "milestone_gate": [{"command": [sys.executable, str(checker), "milestone"]}],
        "final_gate": [{"command": [sys.executable, str(checker), "final"]}],
    }
    config["reviewers"]["plan_gate"] = [
        {"name": "fake-plan", "enabled": True, "command": [sys.executable, str(reviewer), "plan"]}
    ]
    config["reviewers"]["milestone_gate"] = [
        {"name": "fake-milestone", "enabled": True, "command": [sys.executable, str(reviewer), "milestone"]}
    ]
    config["reviewers"]["final_gate"] = [
        {"name": "fake-final", "enabled": True, "command": [sys.executable, str(reviewer), "final"]}
    ]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return 0
