from __future__ import annotations

import unittest

from allox.cli import main


class SelfTestSmokeTests(unittest.TestCase):
    def test_self_test_passes(self) -> None:
        self.assertEqual(0, main(["self-test"]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
