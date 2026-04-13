from __future__ import annotations

import unittest

from allox.core.redaction import is_excluded, redact_text


class RedactionTests(unittest.TestCase):
    def test_excluded_paths_match_default_patterns(self) -> None:
        config = {"excluded_globs": [".env", "node_modules/**"], "max_file_bytes": 100}
        self.assertTrue(is_excluded(".env", config))
        self.assertTrue(is_excluded("node_modules/pkg/index.js", config))
        self.assertFalse(is_excluded("src/app.py", config))

    def test_redact_text_masks_obvious_secrets(self) -> None:
        text = "api_key=secret-value\npassword = hunter2\n"
        redacted = redact_text(text)
        self.assertNotIn("secret-value", redacted)
        self.assertNotIn("hunter2", redacted)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
