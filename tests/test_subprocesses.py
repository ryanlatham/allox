from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from allox.core.subprocesses import probe_binary, resolve_binary, run_command

from helpers import create_executable


class SubprocessTests(unittest.TestCase):
    def test_env_override_resolves_custom_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            custom = create_executable(
                temp_path / "custom-codex",
                f"#!{shutil.which('python3')}\nprint('Codex 1.2.3')\n",
            )
            env = {"PATH": temp_dir, "ALLOX_CODEX_BIN": str(custom)}
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(str(custom), resolve_binary("codex"))

    def test_probe_binary_reads_version_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake = create_executable(
                temp_path / "claude",
                f"#!{shutil.which('python3')}\nprint('claude 9.9.9')\n",
            )
            env = {"PATH": temp_dir}
            with patch.dict(os.environ, env, clear=False):
                probe = probe_binary("claude")
            self.assertEqual(str(fake), probe["path"])
            self.assertEqual("claude 9.9.9", probe["version"])

    def test_resolve_binary_discovers_nvm_installed_gemini(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            gemini_dir = home / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            create_executable(
                gemini_dir / "gemini",
                "#!/bin/sh\nexit 0\n",
            )
            env = {"HOME": temp_dir, "PATH": "/usr/bin:/bin"}
            with patch.dict(os.environ, env, clear=False):
                resolved = resolve_binary("gemini")
            self.assertEqual(str(gemini_dir / "gemini"), resolved)

    def test_probe_binary_runs_discovered_wrapper_with_sibling_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            gemini_dir = home / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            fake_node = create_executable(
                gemini_dir / "fake-node",
                f"#!{shutil.which('python3')}\nimport sys\nprint('gemini 0.37.1')\n",
            )
            create_executable(
                gemini_dir / "gemini",
                "#!/usr/bin/env fake-node\n",
            )
            env = {"HOME": temp_dir, "PATH": "/usr/bin:/bin"}
            with patch.dict(os.environ, env, clear=False):
                probe = probe_binary("gemini")
            self.assertEqual("ok", probe["status"])
            self.assertEqual("gemini 0.37.1", probe["version"])
            self.assertEqual("discovered", probe["source"])

    def test_run_command_prepends_absolute_binary_directory_to_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tool_dir = Path(temp_dir)
            create_executable(
                tool_dir / "fake-node",
                f"#!{shutil.which('python3')}\nprint('wrapper ok')\n",
            )
            wrapper = create_executable(
                tool_dir / "gemini",
                "#!/usr/bin/env fake-node\n",
            )
            result = run_command([str(wrapper)], env={"PATH": "/usr/bin:/bin"})
            self.assertEqual(0, result.returncode)
            self.assertIn("wrapper ok", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
