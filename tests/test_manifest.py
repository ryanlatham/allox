from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from allox.core.manifest import ManagedFileRecord, ProjectManifest


class ManifestTests(unittest.TestCase):
    def test_manifest_round_trip(self) -> None:
        manifest = ProjectManifest(
            framework_name="allox",
            framework_version="0.1.0",
            template="default",
            template_version="0.1.0",
            stack="generic",
            project_name="demo",
            managed_files={
                "AGENTS.md": ManagedFileRecord(
                    path="AGENTS.md",
                    ownership="section",
                    file_hash="abc",
                    managed_hash="def",
                )
            },
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            manifest.write(path)
            loaded = ProjectManifest.read(path)

        self.assertEqual("allox", loaded.framework_name)
        self.assertEqual("demo", loaded.project_name)
        self.assertEqual("def", loaded.managed_files["AGENTS.md"].managed_hash)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
