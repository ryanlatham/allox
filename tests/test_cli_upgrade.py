from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from allox.cli import main
from allox.core.assets import AssetSpec
from allox.core.manifest import ProjectManifest, manifest_path
from allox.core.upgrade import scaffold_bundle

from helpers import FakeBundle


class CliUpgradeTests(unittest.TestCase):
    def test_upgrade_command_updates_managed_file(self) -> None:
        asset = AssetSpec(path="CLAUDE.md", ownership="managed")
        bundle_v1 = FakeBundle("default", "0.1.0", (asset,), {"CLAUDE.md": "old\n"})
        bundle_v2 = FakeBundle("default", "0.2.0", (asset,), {"CLAUDE.md": "new\n"})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            records, _ = scaffold_bundle(root, bundle_v1, {}, dry_run=False)
            ProjectManifest(
                framework_name="allox",
                framework_version="0.1.0",
                template="default",
                template_version="0.1.0",
                stack="generic",
                project_name="demo",
                managed_files=records,
            ).write(manifest_path(root))
            with patch("allox.commands.upgrade.load_project_template_bundle", return_value=bundle_v2):
                exit_code = main(["upgrade", str(root)])
            self.assertEqual(0, exit_code)
            self.assertEqual("new\n", (root / "CLAUDE.md").read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
