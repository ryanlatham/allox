from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from allox.cli import main
from allox.core.layout import project_layout
from allox.core.subprocesses import resolve_binary

from tests.helpers import create_executable


class ProjectRuntimeTests(unittest.TestCase):
    def _create_project(self, root: Path) -> None:
        exit_code = main(["new", str(root), "--skip-doctor"])
        self.assertEqual(0, exit_code)

    def _init_git_repo(self, root: Path) -> str:
        git = resolve_binary("git")
        if not git:
            self.skipTest("git is required for runtime packet tests")
        subprocess.run([git, "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run([git, "config", "user.email", "tests@example.com"], cwd=root, check=True)
        subprocess.run([git, "config", "user.name", "Runtime Tests"], cwd=root, check=True)
        return git

    def _commit_all(self, root: Path, git: str, message: str) -> None:
        subprocess.run([git, "add", "."], cwd=root, check=True)
        subprocess.run([git, "commit", "-m", message], cwd=root, check=True, capture_output=True, text=True)

    def test_runtime_packets_and_closeout_cover_full_three_gate_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "demo"
            layout = project_layout(root)
            self._create_project(root)
            git = self._init_git_repo(root)
            tracked = root / "story.txt"
            tracked.write_text("Initial story.\n", encoding="utf-8")
            self._commit_all(root, git, "initial scaffold")

            tracked.write_text("api_key = SECRET123\nUpdated story.\n", encoding="utf-8")

            reviewer_script = create_executable(
                Path(temp_dir) / "reviewer.py",
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "name = sys.argv[1] if len(sys.argv) > 1 else 'reviewer'\n"
                "print(json.dumps({'summary': f'{name} ok', 'findings': []}))\n",
            )
            checker_script = create_executable(
                Path(temp_dir) / "checker.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print(f'{sys.argv[1]} checks ok')\n",
            )

            config_path = layout.project_commands_file
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["checks"] = {
                "milestone_gate": [{"command": [sys.executable, str(checker_script), "milestone"]}],
                "final_gate": [{"command": [sys.executable, str(checker_script), "final"]}],
            }
            config["reviewers"]["plan_gate"] = [
                {
                    "name": "fake-plan",
                    "enabled": True,
                    "command": [sys.executable, str(reviewer_script), "plan"],
                }
            ]
            config["reviewers"]["milestone_gate"] = [
                {
                    "name": "fake-milestone",
                    "enabled": True,
                    "command": [sys.executable, str(reviewer_script), "milestone"],
                }
            ]
            config["reviewers"]["final_gate"] = [
                {
                    "name": "fake-final",
                    "enabled": True,
                    "command": [sys.executable, str(reviewer_script), "final"],
                }
            ]
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            self.assertEqual(0, main(["project", "bootstrap-task", "--project", str(root), "--title", "Test runtime"]))
            task_id = sorted(layout.tasks_root.glob("*.md"))[-1].stem
            self.assertEqual(0, main(["project", "plan-gate", "--project", str(root), "--task-id", task_id]))
            self.assertEqual(0, main(["project", "milestone-gate", "--project", str(root), "--task-id", task_id]))

            milestone_packet = layout.packet_file(task_id, "milestone_gate").read_text(encoding="utf-8")
            self.assertIn("## Progress", milestone_packet)
            self.assertIn("### git diff --stat", milestone_packet)
            self.assertIn("### git diff --unified=3", milestone_packet)
            self.assertIn("api_key = [REDACTED]", milestone_packet)
            self.assertIn("milestone checks ok", milestone_packet)

            tmp_file = layout.tmp_root / "scratch.txt"
            tmp_file.write_text("scratch", encoding="utf-8")
            self.assertEqual(0, main(["project", "closeout", "--project", str(root), "--task-id", task_id]))

            final_packet = layout.packet_file(task_id, "final_gate").read_text(encoding="utf-8")
            self.assertIn("## Prior Reviews", final_packet)
            self.assertIn("fake-milestone", final_packet)
            self.assertIn("final checks ok", final_packet)
            self.assertTrue(layout.review_normalized_file(task_id, "final_gate", "fake-final").exists())
            self.assertTrue(layout.review_checks_file(task_id, "final_gate").exists())
            self.assertTrue(layout.archived_closeout_file(task_id).exists())
            self.assertTrue(layout.archived_adjudication_file(task_id).exists())
            self.assertFalse(tmp_file.exists())

    def test_closeout_uses_legacy_top_level_checks_and_records_skipped_final_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "demo"
            layout = project_layout(root)
            self._create_project(root)
            checker_script = create_executable(
                Path(temp_dir) / "checker.py",
                "#!/usr/bin/env python3\nprint('legacy checks ok')\n",
            )

            config_path = layout.project_commands_file
            config = {
                "schema_version": 1,
                "notes": [],
                "checks": [{"command": [sys.executable, str(checker_script)]}],
                "reviewers": {
                    "plan_gate": [],
                    "milestone_gate": [],
                },
            }
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            self.assertEqual(0, main(["project", "bootstrap-task", "--project", str(root), "--title", "Legacy closeout"]))
            task_id = sorted(layout.tasks_root.glob("*.md"))[-1].stem
            self.assertEqual(0, main(["project", "closeout", "--project", str(root), "--task-id", task_id]))

            checks_output = layout.review_checks_file(task_id, "final_gate").read_text(encoding="utf-8")
            skip_note = layout.review_skip_file(task_id, "final_gate").read_text(encoding="utf-8")
            self.assertIn("legacy checks ok", checks_output)
            self.assertIn("No final_gate reviewers are enabled", skip_note)
            self.assertTrue(layout.archived_closeout_file(task_id).exists())

    def test_generated_shim_calls_installed_allox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "demo"
            self._create_project(root)
            record_path = Path(temp_dir) / "record.json"
            fake_allox = create_executable(
                Path(temp_dir) / "fake-allox",
                "#!/usr/bin/env python3\n"
                "import json, os, pathlib, sys\n"
                "pathlib.Path(os.environ['RECORD_PATH']).write_text(json.dumps(sys.argv[1:]))\n",
            )
            env = dict(os.environ)
            env["ALLOX_BIN"] = str(fake_allox)
            env["RECORD_PATH"] = str(record_path)
            subprocess.run(
                [sys.executable, str(root / ".allox" / "scripts" / "bootstrap_task.py"), "--title", "Shim test"],
                cwd=root,
                env=env,
                check=True,
            )
            args = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(["project", "bootstrap-task"], args[:2])
            self.assertEqual("--project", args[2])
            self.assertEqual(str(root.resolve()), args[3])
            self.assertEqual("--title", args[4])

    def test_auto_enabled_reviewers_use_allox_binary_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "demo"
            layout = project_layout(root)
            self._create_project(root)

            gemini_dir = Path(temp_dir) / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            create_executable(
                gemini_dir / "fake-node",
                f"#!{shutil.which('python3')}\n"
                "import json, sys\n"
                "args = sys.argv\n"
                "if '--version' in args:\n"
                "    print('gemini 0.37.1')\n"
                "elif '-p' in args or '--prompt' in args:\n"
                "    print(json.dumps({'summary': 'gemini ok', 'findings': []}))\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(gemini_dir / "gemini", "#!/usr/bin/env fake-node\n")

            config_path = layout.project_commands_file
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["reviewers"]["plan_gate"] = [
                {
                    "name": "gemini-plan-critic",
                    "provider": "gemini",
                    "enabled": "auto",
                    "command": ["gemini", "-p", "{prompt}"],
                }
            ]
            config["reviewers"]["milestone_gate"] = []
            config["reviewers"]["final_gate"] = []
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            with patch.dict(os.environ, {"HOME": temp_dir, "PATH": "/usr/bin:/bin"}, clear=False):
                self.assertEqual(
                    0,
                    main(["project", "bootstrap-task", "--project", str(root), "--title", "Auto reviewers"]),
                )
                task_id = sorted(layout.tasks_root.glob("*.md"))[-1].stem
                self.assertEqual(0, main(["project", "plan-gate", "--project", str(root), "--task-id", task_id]))

            review_path = layout.review_normalized_file(task_id, "plan_gate", "gemini-plan-critic")
            self.assertTrue(review_path.exists())
            payload = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual("gemini ok", payload["summary"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
