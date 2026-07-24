from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_crossframe_skill.py"


def load_packager():
    spec = importlib.util.spec_from_file_location("package_crossframe_skill", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("package script is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CrossFramePackageHygieneTests(unittest.TestCase):
    def test_package_excludes_runs_drafts_caches_builds_and_local_environments(self) -> None:
        packager = load_packager()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            skill = repo / "skills" / "crossframe-promax"
            allowed = skill / "references" / "prose-techniques" / "card.md"
            excluded = (
                skill / "runs" / "run.md",
                skill / "drafts" / "draft.md",
                skill / "artifacts" / "manifest.json",
                skill / "build" / "generated.json",
                skill / "dist" / "bundle.zip",
                skill / ".venv" / "secret.txt",
                skill / ".ruff_cache" / "cache",
                skill / "__pycache__" / "module.pyc",
                skill / "loose.pyc",
                skill / ".env",
            )
            for path in (allowed, *excluded):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")

            packaged = {
                path.relative_to(repo).as_posix()
                for path in packager.iter_package_files(repo)
            }

        self.assertIn(
            "skills/crossframe-promax/references/prose-techniques/card.md",
            packaged,
        )
        for path in excluded:
            with self.subTest(path=path.name):
                self.assertNotIn(path.relative_to(repo).as_posix(), packaged)


if __name__ == "__main__":
    unittest.main()
