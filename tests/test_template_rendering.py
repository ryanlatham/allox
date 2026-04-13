from __future__ import annotations

import json
import unittest

from allox.core.assets import load_project_template_bundle
from allox.core.upgrade import render_bundle


class TemplateRenderingTests(unittest.TestCase):
    def test_default_bundle_renders_expected_files(self) -> None:
        bundle = load_project_template_bundle()
        rendered = render_bundle(
            bundle,
            {
                "project_name": "demo-project",
                "framework_version": "9.9.9",
                "template_name": bundle.name,
            },
        )

        self.assertIn("AGENTS.md", rendered)
        self.assertIn("scripts/ai/bootstrap_task.py", rendered)
        self.assertIn(".codex/README.md", rendered)
        self.assertIn("demo-project", rendered["AGENTS.md"])
        self.assertIn("9.9.9", rendered["AGENTS.md"])
        self.assertNotIn("PROMPTS/CODEX_PROJECT_START.md", rendered)
        self.assertIn("Do not require a dedicated kickoff prompt file.", rendered["AGENTS.md"])
        self.assertIn("Opening the repo in Codex is enough", rendered[".codex/README.md"])
        self.assertIn("Codex-facing operational guidance", rendered["docs/ai-workflow.md"])
        self.assertIn("allox project milestone-gate --project .", rendered["docs/ai-workflow.md"])
        self.assertIn("allox project closeout --project .", rendered["docs/ai-workflow.md"])
        self.assertIn("allox project ...", rendered["AGENTS.md"])
        self.assertIn("ai/tasks", bundle.create_directories)
        project_commands = json.loads(rendered["ai/config/project_commands.json"])
        self.assertIsInstance(project_commands["checks"], dict)
        self.assertIn("milestone_gate", project_commands["checks"])
        self.assertIn("final_gate", project_commands["checks"])
        self.assertIn("final_gate", project_commands["reviewers"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
