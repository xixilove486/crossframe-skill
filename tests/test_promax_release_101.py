from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProMaxRelease101Tests(unittest.TestCase):
    def test_readme_presents_the_reader_first_101_runtime(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("ProMax-1.0.1%20%7C%20v8.0", text)
        self.assertIn("50 张", text)
        self.assertIn("九种体裁", text)
        self.assertIn("prose review", text)
        self.assertIn("六个角色", text)
        self.assertNotIn("用五道结构约束限制", text)

    def test_changelog_records_compatibility_and_prose_contract(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        heading = "## CrossFrame ProMax 1.0.1 - 2026-07-25"

        self.assertIn(heading, text)
        self.assertLess(
            text.index(heading),
            text.index("## CrossFrame ProMax 1.0.0 - 2026-07-24"),
        )
        for required in (
            "50 张",
            "九种",
            "六角色",
            "11 个",
            "run-contract schema v2",
            "v1",
            "promax-prose-review.json",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
