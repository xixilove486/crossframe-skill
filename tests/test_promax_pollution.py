from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
SKILL = ROOT / "skills/crossframe-promax"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.pollution import (
    VersionPollutionError,
    pollution_errors_for_text,
    scan_version_pollution,
    validate_version_isolation,
)


class ProMaxRuntimePollutionTests(unittest.TestCase):
    def test_runtime_scanner_accepts_the_committed_v8_only_skill(self) -> None:
        self.assertEqual(scan_version_pollution(SKILL), [])
        summary = validate_version_isolation(SKILL)
        self.assertGreater(summary["scanned_file_count"], 0)
        self.assertEqual(summary["pollution_count"], 0)

    def test_text_scanner_reuses_exact_v8_isolation_rules(self) -> None:
        self.assertEqual(
            pollution_errors_for_text(
                "CrossFrame ProMax 使用 v8.0、V8-P0001 与 V8-CANON-U01。",
                "references/clean.md",
            ),
            [],
        )
        errors = pollution_errors_for_text(
            "v8 " * 1000 + "知识来源为 framework version 7.0",
            "references/stuffed.md",
        )
        self.assertTrue(any("non-v8" in error.lower() for error in errors), errors)

    def test_tree_scanner_rejects_one_polluted_file_despite_clean_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "crossframe-promax"
            root.mkdir()
            (root / "clean.md").write_text(
                "v8-only V8-P0001 V8-T117\n" * 200,
                encoding="utf-8",
            )
            (root / "polluted.md").write_text(
                "从 knowledge.v6.json 继承概念定义",
                encoding="utf-8",
            )
            errors = scan_version_pollution(root)
            self.assertTrue(any("pre-v8" in error.lower() for error in errors), errors)
            with self.assertRaises(VersionPollutionError):
                validate_version_isolation(root)


if __name__ == "__main__":
    unittest.main()
