from __future__ import annotations

import unittest

from allox.core.reviews import ReviewParseError, normalize_review_output


class ReviewNormalizationTests(unittest.TestCase):
    def test_normalizes_plain_json(self) -> None:
        raw = '{"summary":"ok","findings":[{"title":"A","body":"B","severity":"low"}]}'
        normalized = normalize_review_output(raw, reviewer="demo", gate="plan_gate")
        self.assertEqual("ok", normalized.summary)
        self.assertEqual("A", normalized.findings[0]["title"])

    def test_normalizes_fenced_json(self) -> None:
        raw = '```json\n{"summary":"ok","findings":[]}\n```'
        normalized = normalize_review_output(raw, reviewer="demo", gate="milestone_gate")
        self.assertEqual([], normalized.findings)

    def test_rejects_malformed_json(self) -> None:
        with self.assertRaises(ReviewParseError):
            normalize_review_output("not json", reviewer="demo", gate="plan_gate")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
