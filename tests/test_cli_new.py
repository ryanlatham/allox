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
            self.assertTrue((project_root / ".allox" / "scripts" / "bootstrap_task.py").exists())

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
            self.assertTrue((project_root / ".allox" / "scripts" / "bootstrap_task.py").exists())

    def test_new_prints_human_minimal_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "demo"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["new", str(project_root), "--skip-doctor"])

            self.assertEqual(0, exit_code)
            output = stdout.getvalue()
            self.assertIn(f"1. Open {project_root.resolve()} in Codex.", output)
            self.assertIn("2. Work with Codex normally from your task, issue, or spec.", output)
            self.assertIn(
                "3. Let the generated project contract handle task bootstrap and managed review orchestration.",
                output,
            )
            self.assertNotIn("PROMPTS/CODEX_PROJECT_START.md", output)
            self.assertNotIn("Read AGENTS.md and allox/README.md.", output)

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
            (project_root / "allox").write_text("this blocks a required directory\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["new", str(project_root), "--skip-doctor"])

            self.assertEqual(1, exit_code)
            self.assertIn("conflicts were detected", stderr.getvalue())
            self.assertFalse((project_root / ".allox" / "manifest.json").exists())
            self.assertFalse((project_root / "CLAUDE.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
