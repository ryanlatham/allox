from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import allox.core.doctoring as doctoring
from allox.core.doctoring import collect_doctor_report
from allox.core.manifest import ProjectManifest, manifest_path

from tests.helpers import create_executable


class CliDoctorTests(unittest.TestCase):
    def test_doctor_reports_missing_binaries_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"PATH": temp_dir, "HOME": temp_dir}, clear=False):
                report = collect_doctor_report()
            self.assertFalse(report["binaries"]["codex"]["found"])
            self.assertFalse(report["binaries"]["gemini"]["found"])

    def test_doctor_detects_project_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = ProjectManifest(
                framework_name="allox",
                framework_version="0.0.0",
                template="default",
                template_version="0.0.0",
                stack="generic",
                project_name="demo",
            )
            manifest.write(manifest_path(root))
            report = collect_doctor_report(project_path=root)
            self.assertTrue(report["project"]["managed"])
            self.assertFalse(report["project"]["version_match"])

    def test_doctor_online_reports_provider_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            create_executable(
                temp_path / "codex",
                f"#!{shutil.which('python3')}\n"
                "import sys\n"
                "args = sys.argv[1:]\n"
                "if args == ['--version']:\n"
                "    print('codex 1.2.3')\n"
                "elif args == ['login', 'status']:\n"
                "    print('Logged in using ChatGPT')\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(
                temp_path / "claude",
                f"#!{shutil.which('python3')}\n"
                "import json, sys\n"
                "args = sys.argv[1:]\n"
                "if args == ['--version']:\n"
                "    print('claude 9.9.9')\n"
                "elif args == ['auth', 'status', '--json']:\n"
                "    print(json.dumps({'loggedIn': True, 'authMethod': 'claude.ai'}))\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            gemini_dir = temp_path / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            create_executable(
                gemini_dir / "fake-node",
                f"#!{shutil.which('python3')}\n"
                "import sys\n"
                "args = sys.argv\n"
                "if '--version' in args:\n"
                "    print('gemini 0.37.1')\n"
                "elif '-p' in args or '--prompt' in args:\n"
                "    print('OK')\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(gemini_dir / "gemini", "#!/usr/bin/env fake-node\n")

            with patch.dict(os.environ, {"PATH": temp_dir, "HOME": temp_dir}, clear=False):
                report = collect_doctor_report(online=True)

            self.assertTrue(report["binaries"]["codex"]["online_ready"])
            self.assertEqual("authenticated", report["binaries"]["codex"]["auth_status"])
            self.assertTrue(report["binaries"]["claude"]["online_ready"])
            self.assertEqual("authenticated", report["binaries"]["claude"]["auth_status"])
            self.assertTrue(report["binaries"]["gemini"]["online_ready"])
            self.assertEqual("ready", report["binaries"]["gemini"]["auth_status"])
            self.assertEqual("discovered", report["binaries"]["gemini"]["source"])

    def test_doctor_online_reports_auth_failures_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            create_executable(
                temp_path / "codex",
                f"#!{shutil.which('python3')}\n"
                "import sys\n"
                "args = sys.argv[1:]\n"
                "if args == ['--version']:\n"
                "    print('codex 1.2.3')\n"
                "elif args == ['login', 'status']:\n"
                "    print('Not logged in', file=sys.stderr)\n"
                "    raise SystemExit(1)\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(
                temp_path / "claude",
                f"#!{shutil.which('python3')}\n"
                "import json, sys\n"
                "args = sys.argv[1:]\n"
                "if args == ['--version']:\n"
                "    print('claude 9.9.9')\n"
                "elif args == ['auth', 'status', '--json']:\n"
                "    print(json.dumps({'loggedIn': False}))\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            gemini_dir = temp_path / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            create_executable(
                gemini_dir / "fake-node",
                f"#!{shutil.which('python3')}\n"
                "import sys\n"
                "args = sys.argv\n"
                "if '--version' in args:\n"
                "    print('gemini 0.37.1')\n"
                "elif '-p' in args or '--prompt' in args:\n"
                "    print('probe failed', file=sys.stderr)\n"
                "    raise SystemExit(1)\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(gemini_dir / "gemini", "#!/usr/bin/env fake-node\n")

            with patch.dict(os.environ, {"PATH": temp_dir, "HOME": temp_dir}, clear=False):
                report = collect_doctor_report(online=True)

            self.assertFalse(report["binaries"]["codex"]["online_ready"])
            self.assertEqual("not_authenticated", report["binaries"]["codex"]["auth_status"])
            self.assertFalse(report["binaries"]["claude"]["online_ready"])
            self.assertEqual("not_authenticated", report["binaries"]["claude"]["auth_status"])
            self.assertFalse(report["binaries"]["gemini"]["online_ready"])
            self.assertEqual("probe_failed", report["binaries"]["gemini"]["auth_status"])

    def test_doctor_online_uses_longer_timeout_for_gemini_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            gemini_dir = temp_path / ".nvm" / "versions" / "node" / "v24.14.1" / "bin"
            create_executable(
                gemini_dir / "fake-node",
                f"#!{shutil.which('python3')}\n"
                "import sys, time\n"
                "args = sys.argv\n"
                "if '--version' in args:\n"
                "    print('gemini 0.37.1')\n"
                "elif '-p' in args or '--prompt' in args:\n"
                "    time.sleep(0.1)\n"
                "    print('OK')\n"
                "else:\n"
                "    raise SystemExit(1)\n",
            )
            create_executable(gemini_dir / "gemini", "#!/usr/bin/env fake-node\n")

            with (
                patch.dict(os.environ, {"PATH": temp_dir, "HOME": temp_dir}, clear=False),
                patch.object(doctoring, "ONLINE_TIMEOUT_SECONDS", 0.05),
                patch.object(doctoring, "GEMINI_ONLINE_TIMEOUT_SECONDS", 0.2),
            ):
                report = collect_doctor_report(online=True)

            self.assertTrue(report["binaries"]["gemini"]["online_ready"])
            self.assertEqual("ready", report["binaries"]["gemini"]["auth_status"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
