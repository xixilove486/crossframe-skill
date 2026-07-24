from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from scripts.sync_skill_mirrors import CROSSFRAME_SKILLS, same_tree


ROOT = Path(__file__).resolve().parents[1]
FAKE_INSTALLER = ROOT / "tests/fixtures/fake_skill_installer.py"
EXPECTED_SKILLS = set(CROSSFRAME_SKILLS)


class ProMaxInstallerContractTests(unittest.TestCase):
    def test_installers_expose_real_destination_and_installer_seams(self) -> None:
        powershell = (ROOT / "scripts/install-codex.ps1").read_text(encoding="utf-8")
        bash = (ROOT / "scripts/install-codex.sh").read_text(encoding="utf-8")
        self.assertIn("[string]$DestinationRoot", powershell)
        self.assertIn("[string]$InstallerPath", powershell)
        self.assertIn("--dest $resolvedSkillsRoot", powershell)
        self.assertIn("--dest)", bash)
        self.assertIn("--installer)", bash)
        self.assertIn('--dest "$resolved_skills_root"', bash)
        for skill in EXPECTED_SKILLS:
            self.assertIn(f"skills/{skill}", powershell)
            self.assertIn(f"skills/{skill}", bash)

    def _assert_install(self, destination: Path) -> None:
        installed = {
            path.parent.name for path in destination.glob("*/SKILL.md")
        }
        self.assertEqual(installed, EXPECTED_SKILLS)
        for skill in EXPECTED_SKILLS:
            self.assertTrue(
                same_tree(ROOT / "skills" / skill, destination / skill),
                skill,
            )

    def test_powershell_installer_copies_all_sixteen_skills_to_temp_root(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if pwsh is None:
            self.skipTest("PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "skills"
            result = subprocess.run(
                [
                    pwsh,
                    "-NoProfile",
                    "-File",
                    str(ROOT / "scripts/install-codex.ps1"),
                    "-Repo",
                    str(ROOT),
                    "-DestinationRoot",
                    str(destination),
                    "-InstallerPath",
                    str(FAKE_INSTALLER),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self._assert_install(destination)

    def test_powershell_installer_restores_existing_skill_on_failure(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if pwsh is None:
            self.skipTest("PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "skills"
            existing = destination / "crossframe-promax"
            existing.mkdir(parents=True)
            sentinel = b"preexisting-skill\n"
            (existing / "SKILL.md").write_bytes(sentinel)
            environment = os.environ.copy()
            environment["FAKE_SKILL_INSTALLER_FAIL_SKILL"] = "crossframe-promax"
            result = subprocess.run(
                [
                    pwsh,
                    "-NoProfile",
                    "-File",
                    str(ROOT / "scripts/install-codex.ps1"),
                    "-Repo",
                    str(ROOT),
                    "-DestinationRoot",
                    str(destination),
                    "-InstallerPath",
                    str(FAKE_INSTALLER),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((existing / "SKILL.md").read_bytes(), sentinel)

    @unittest.skipIf(os.name == "nt", "Bash end-to-end smoke runs on POSIX CI")
    def test_bash_installer_copies_all_sixteen_skills_to_temp_root(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "skills"
            result = subprocess.run(
                [
                    bash,
                    str(ROOT / "scripts/install-codex.sh"),
                    "--repo",
                    str(ROOT),
                    "--dest",
                    str(destination),
                    "--installer",
                    str(FAKE_INSTALLER),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self._assert_install(destination)


if __name__ == "__main__":
    unittest.main()
