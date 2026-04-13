from __future__ import annotations

import unittest

from allox.core.markers import MarkerError, extract_managed_body, replace_managed_block


class MarkerTests(unittest.TestCase):
    def test_replace_managed_block_preserves_user_content(self) -> None:
        current = "before\n<!-- allox:begin managed -->\nold\n<!-- allox:end managed -->\nafter\n"
        candidate = "<!-- allox:begin managed -->\nnew\n<!-- allox:end managed -->"
        updated = replace_managed_block(
            current,
            candidate,
            "<!-- allox:begin managed -->",
            "<!-- allox:end managed -->",
        )
        self.assertIn("before", updated)
        self.assertIn("after", updated)
        self.assertIn("new", updated)
        self.assertNotIn("old", updated)

    def test_extract_raises_when_markers_are_malformed(self) -> None:
        with self.assertRaises(MarkerError):
            extract_managed_body("no markers here", "<!-- a -->", "<!-- b -->")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
