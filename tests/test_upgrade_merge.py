from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from allox.core.assets import AssetSpec
from allox.core.manifest import ProjectManifest
from allox.core.upgrade import scaffold_bundle, upgrade_project

from helpers import FakeBundle


class UpgradeMergeTests(unittest.TestCase):
    def _manifest(self, records) -> ProjectManifest:
        return ProjectManifest(
            framework_name="allox",
            framework_version="0.1.0",
            template="default",
            template_version="0.1.0",
            stack="generic",
            project_name="demo",
            managed_files=records,
        )

    def test_upgrade_updates_unchanged_managed_files(self) -> None:
        asset = AssetSpec(path="CLAUDE.md", ownership="managed")
        bundle_v1 = FakeBundle("default", "0.1.0", (asset,), {"CLAUDE.md": "v1\n"})
        bundle_v2 = FakeBundle("default", "0.2.0", (asset,), {"CLAUDE.md": "v2\n"})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            records, _ = scaffold_bundle(root, bundle_v1, {}, dry_run=False)
            manifest = self._manifest(records)
            updated_manifest, result = upgrade_project(
                root,
                bundle_v2,
                {"framework_version": "0.2.0"},
                manifest,
                dry_run=False,
                write_conflicts=True,
            )
            self.assertEqual("v2\n", (root / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn("CLAUDE.md", result.updated)
            self.assertEqual("0.2.0", updated_manifest.framework_version)

    def test_upgrade_conflicts_on_locally_modified_section_file(self) -> None:
        asset = AssetSpec(
            path="AGENTS.md",
            ownership="section",
            marker_start="<!-- allox:begin managed -->",
            marker_end="<!-- allox:end managed -->",
        )
        bundle_v1 = FakeBundle(
            "default",
            "0.1.0",
            (asset,),
            {"AGENTS.md": "x\n<!-- allox:begin managed -->\nold\n<!-- allox:end managed -->\n"},
        )
        bundle_v2 = FakeBundle(
            "default",
            "0.2.0",
            (asset,),
            {"AGENTS.md": "x\n<!-- allox:begin managed -->\nnew\n<!-- allox:end managed -->\n"},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            records, _ = scaffold_bundle(root, bundle_v1, {}, dry_run=False)
            manifest = self._manifest(records)
            (root / "AGENTS.md").write_text(
                "x\n<!-- allox:begin managed -->\nlocally edited\n<!-- allox:end managed -->\n",
                encoding="utf-8",
            )
            _, result = upgrade_project(
                root,
                bundle_v2,
                {"framework_version": "0.2.0"},
                manifest,
                dry_run=False,
                write_conflicts=True,
            )
            self.assertIn("AGENTS.md", result.conflicts)
            conflict = root / ".allox" / "conflicts" / "AGENTS.md.allox.new"
            self.assertTrue(conflict.exists())
            self.assertIn("new", conflict.read_text(encoding="utf-8"))

    def test_project_owned_files_are_preserved(self) -> None:
        asset = AssetSpec(path="allox/config/project_commands.json", ownership="project")
        bundle_v1 = FakeBundle("default", "0.1.0", (asset,), {"allox/config/project_commands.json": "{\"a\": 1}\n"})
        bundle_v2 = FakeBundle("default", "0.2.0", (asset,), {"allox/config/project_commands.json": "{\"a\": 2}\n"})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, _ = scaffold_bundle(root, bundle_v1, {}, dry_run=False)
            original = (root / "allox" / "config" / "project_commands.json").read_text(encoding="utf-8")
            manifest = self._manifest({})
            _, result = upgrade_project(
                root,
                bundle_v2,
                {"framework_version": "0.2.0"},
                manifest,
                dry_run=False,
                write_conflicts=True,
            )
            self.assertIn("allox/config/project_commands.json", result.skipped)
            self.assertEqual(original, (root / "allox" / "config" / "project_commands.json").read_text(encoding="utf-8"))

    def test_upgrade_preserves_existing_markdown_bootstrapped_via_append(self) -> None:
        asset = AssetSpec(path="CLAUDE.md", ownership="managed")
        bundle_v1 = FakeBundle("default", "0.1.0", (asset,), {"CLAUDE.md": "# Framework v1\n"})
        bundle_v2 = FakeBundle("default", "0.2.0", (asset,), {"CLAUDE.md": "# Framework v2\n"})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "CLAUDE.md"
            target.write_text("# Existing Notes\n", encoding="utf-8")

            records, _ = scaffold_bundle(root, bundle_v1, {}, dry_run=False)
            manifest = self._manifest(records)
            self.assertEqual("section", manifest.managed_files["CLAUDE.md"].ownership)

            _, result = upgrade_project(
                root,
                bundle_v2,
                {"framework_version": "0.2.0"},
                manifest,
                dry_run=False,
                write_conflicts=True,
            )

            content = target.read_text(encoding="utf-8")
            self.assertIn("# Existing Notes", content)
            self.assertIn("# Framework v2", content)
            self.assertIn("CLAUDE.md", result.updated)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
