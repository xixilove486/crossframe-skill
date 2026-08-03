from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_crossframe_skill.py"
ULTRA_PACKAGE_REQUIRED = {
    ".claude/commands/crossframe-ultra.md",
    ".claude/skills/crossframe-ultra/SKILL.md",
    "skills/crossframe-ultra/SKILL.md",
    "skills/crossframe-ultra/references/source-manifest.json",
    "skills/crossframe-ultra/references/v8.2-full-source/00-index.md",
    "skills/crossframe-ultra/schemas/ultra-run-contract.schema.json",
    "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py",
    "skills/crossframe-ultra/templates/ultra-article-output.md",
}


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

    def test_built_package_contains_the_ultra_release_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(ROOT),
                    "--version",
                    "ultra-contract",
                    "--output-dir",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            packages = list(output.glob("crossframe-skill-suite-ultra-contract-*.zip"))
            self.assertEqual(len(packages), 1)
            with zipfile.ZipFile(packages[0]) as archive:
                names = set(archive.namelist())
        self.assertFalse(ULTRA_PACKAGE_REQUIRED - names)


if __name__ == "__main__":
    unittest.main()
