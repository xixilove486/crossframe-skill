from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from scripts.sync_skill_mirrors import CROSSFRAME_SKILLS, same_tree
from scripts import check_crossframe_skill_integrity as integrity


ROOT = Path(__file__).resolve().parents[1]
MAX_SCRIPT_NAMES = (
    "build_crossframe_max_repair_plan.py",
    "check_crossframe_max_artifacts.py",
    "check_crossframe_max_read_ledger.py",
    "check_crossframe_max_route_ledgers.py",
    "check_crossframe_max_v6_full_source.py",
    "check_crossframe_max_v6_registry_anchors.py",
    "crossframe_max_runtime_contract.py",
    "generate_crossframe_max_v6_full_source.py",
)
PROMAX_SCRIPT_NAMES = (
    "build_crossframe_promax_repair_plan.py",
    "check_crossframe_promax_artifacts.py",
    "check_crossframe_promax_v8_full_source.py",
    "check_crossframe_promax_v8_knowledge.py",
    "crossframe_promax_fixture_factory.py",
    "crossframe_promax_runtime.py",
    "generate_crossframe_promax_v8_full_source.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MirrorIntegrityTests(unittest.TestCase):
    def test_mirror_inventory_has_sixteen_skills_and_exact_promax_tree(self) -> None:
        self.assertEqual(len(CROSSFRAME_SKILLS), 16)
        self.assertEqual(len(set(CROSSFRAME_SKILLS)), 16)
        self.assertIn("crossframe-promax", CROSSFRAME_SKILLS)
        self.assertTrue(
            same_tree(
                ROOT / "skills/crossframe-promax",
                ROOT / ".claude/skills/crossframe-promax",
            )
        )

    def test_integrity_inventory_includes_promax_but_legacy_scans_exclude_it(self) -> None:
        self.assertEqual(len(integrity.CURRENT_CROSSFRAME_SKILLS), 16)
        self.assertIn("crossframe-promax", integrity.CURRENT_CROSSFRAME_SKILLS)
        self.assertNotIn("crossframe-promax", integrity.LEGACY_CROSSFRAME_SKILLS)
        self.assertNotIn("crossframe-promax", integrity.CLAIM_LEDGER_DELTA_SKILLS)
        self.assertNotIn("crossframe-promax", integrity.SIBLING_CLAIM_BRIDGE_SKILLS)
        integrity.check_crossframe_promax_skill(ROOT / "skills", "test")

    def test_same_tree_detects_same_metadata_different_content(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            left = Path(td) / "left"
            right = Path(td) / "right"
            left.mkdir()
            right.mkdir()
            (left / "x.txt").write_text("AAAA", encoding="utf-8")
            (right / "x.txt").write_text("BBBB", encoding="utf-8")
            stamp = 1_700_000_000
            os.utime(left / "x.txt", (stamp, stamp))
            os.utime(right / "x.txt", (stamp, stamp))
            self.assertFalse(same_tree(left, right))

    def test_root_and_skill_max_executables_have_identical_bytes(self) -> None:
        root_scripts = ROOT / "scripts"
        skill_scripts = ROOT / "skills/crossframe-max/scripts"
        for name in MAX_SCRIPT_NAMES:
            root_path = root_scripts / name
            skill_path = skill_scripts / name
            self.assertTrue(root_path.is_file(), root_path.as_posix())
            self.assertTrue(skill_path.is_file(), skill_path.as_posix())
            self.assertEqual(sha256(root_path), sha256(skill_path), name)

    def test_root_promax_executables_are_thin_canonical_wrappers(self) -> None:
        root_scripts = ROOT / "scripts"
        skill_scripts = ROOT / "skills/crossframe-promax/scripts"
        for name in PROMAX_SCRIPT_NAMES:
            root_path = root_scripts / name
            skill_path = skill_scripts / name
            self.assertTrue(root_path.is_file(), root_path.as_posix())
            self.assertTrue(skill_path.is_file(), skill_path.as_posix())
            text = root_path.read_text(encoding="utf-8")
            self.assertIn("crossframe-promax", text, name)
            self.assertIn(name, text, name)
            self.assertTrue(
                "runpy.run_path" in text or "spec_from_file_location" in text,
                name,
            )


if __name__ == "__main__":
    unittest.main()
