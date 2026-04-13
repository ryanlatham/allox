from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from allox.cli import build_parser, main


class CliNewTests(unittest.TestCase):
    def test_install_user_is_not_exposed_in_cli(self) -> None:
        parser = build_parser()
        self.assertNotIn("install-user", parser.format_help())

    def test_new_creates_scaffold_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "demo"
            exit_code = main(["new", str(project_root), "--skip-doctor"])
            self.assertEqual(0, exit_code)
            self.assertTrue((project_root / ".allox" / "manifest.json").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertTrue((project_root / "scripts" / "ai" / "bootstrap_task.py").exists())

    def test_new_defaults_to_current_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = Path.cwd()
            try:
                os.chdir(project_root)
                exit_code = main(["new", "--skip-doctor"])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(0, exit_code)
            self.assertTrue((project_root / ".allox" / "manifest.json").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertTrue((project_root / "scripts" / "ai" / "bootstrap_task.py").exists())

    def test_new_dry_run_reports_planned_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "demo"
            project_root.mkdir(parents=True, exist_ok=True)
            existing = project_root / "CLAUDE.md"
            original = "# Existing Claude Notes\n\nKeep this content.\n"
            existing.write_text(original, encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["new", str(project_root), "--skip-doctor", "--dry-run"])

            self.assertEqual(0, exit_code)
            output = stdout.getvalue()
            self.assertIn("Dry run for allox project", output)
            self.assertIn("- would create AGENTS.md", output)
            self.assertIn("- would append CLAUDE.md", output)
            self.assertIn("- would create .allox/manifest.json", output)
            self.assertIn("No files were written.", output)
            self.assertEqual(original, existing.read_text(encoding="utf-8"))
            self.assertFalse((project_root / ".allox" / "manifest.json").exists())
            self.assertFalse((project_root / "AGENTS.md").exists())

    def test_new_appends_to_existing_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "demo"
            project_root.mkdir(parents=True, exist_ok=True)
            existing = project_root / "CLAUDE.md"
            existing.write_text("# Existing Claude Notes\n\nKeep this content.\n", encoding="utf-8")

            exit_code = main(["new", str(project_root), "--skip-doctor"])

            self.assertEqual(0, exit_code)
            content = existing.read_text(encoding="utf-8")
            self.assertIn("Keep this content.", content)
            self.assertIn("Claude Wrapper For demo", content)
            self.assertIn("<!-- allox:begin managed -->", content)
            self.assertTrue((project_root / ".allox" / "manifest.json").exists())

    def test_new_detects_conflicts_before_writing_anything(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "demo"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / "ai").write_text("this blocks a required directory\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["new", str(project_root), "--skip-doctor"])

            self.assertEqual(1, exit_code)
            self.assertIn("conflicts were detected", stderr.getvalue())
            self.assertFalse((project_root / ".allox" / "manifest.json").exists())
            self.assertFalse((project_root / "CLAUDE.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
