from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

from scripts.sync_skill_mirrors import same_tree


ROOT = Path(__file__).resolve().parents[1]
FAKE_INSTALLER = ROOT / "tests/fixtures/fake_skill_installer.py"
EXPECTED_SKILLS = (
    "crossframe",
    "crossframe-suite",
    "crossframe-essay",
    "crossframe-critical",
    "crossframe-review",
    "crossframe-dialogue",
    "crossframe-casebook",
    "crossframe-history",
    "crossframe-inquiry",
    "crossframe-max",
    "crossframe-promax",
    "crossframe-public",
    "crossframe-org",
    "crossframe-teach",
    "crossframe-debate",
    "crossframe-notebook",
    "crossframe-ultra",
)


def _assert_installed(source: Path, destination: Path) -> None:
    installed = tuple(sorted(path.parent.name for path in destination.glob("*/SKILL.md")))
    assert installed == tuple(sorted(EXPECTED_SKILLS))
    for skill in EXPECTED_SKILLS:
        assert same_tree(source / "skills" / skill, destination / skill), skill
    assert not list(destination.glob(".crossframe-install-*"))


def _make_local_candidate(parent: Path) -> Path:
    candidate = parent / "clean-local-candidate"
    shutil.copytree(
        ROOT / "skills",
        candidate / "skills",
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".v8-full-source.lock"),
    )
    scripts = candidate / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/sync_skill_mirrors.py", scripts)
    sentinel = candidate / "skills/crossframe-ultra/LOCAL-CANDIDATE-SENTINEL.txt"
    sentinel.write_text("installed from the explicit local candidate\n", encoding="utf-8")
    return candidate


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def test_powershell_real_mode_installs_from_explicit_local_candidate() -> None:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        candidate = _make_local_candidate(temp)
        destination = temp / "destination" / "skills"
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-File",
                str(ROOT / "scripts/install-codex.ps1"),
                "-Repo",
                str(candidate),
                "-DestinationRoot",
                str(destination),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_installed(candidate, destination)
        assert (
            destination / "crossframe-ultra/LOCAL-CANDIDATE-SENTINEL.txt"
        ).is_file()


def test_powershell_restores_preexisting_ultra_on_staging_failure() -> None:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary) / "skills"
        existing = destination / "crossframe-ultra"
        existing.mkdir(parents=True)
        sentinel = b"preexisting Ultra must survive\n"
        (existing / "SKILL.md").write_bytes(sentinel)
        environment = os.environ.copy()
        environment["FAKE_SKILL_INSTALLER_FAIL_SKILL"] = "crossframe-ultra"
        result = subprocess.run(
            [
                powershell,
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
        assert result.returncode != 0
        assert (existing / "SKILL.md").read_bytes() == sentinel
        assert not list(destination.glob(".crossframe-install-*"))

@pytest.mark.skipif(os.name == "nt", reason="Bash end-to-end runs on POSIX CI")
def test_bash_real_mode_installs_from_explicit_local_candidate() -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        candidate = _make_local_candidate(temp)
        destination = temp / "destination" / "skills"
        result = subprocess.run(
            [
                bash,
                str(ROOT / "scripts/install-codex.sh"),
                "--repo",
                str(candidate),
                "--dest",
                str(destination),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_installed(candidate, destination)
        assert (
            destination / "crossframe-ultra/LOCAL-CANDIDATE-SENTINEL.txt"
        ).is_file()


@pytest.mark.skipif(os.name == "nt", reason="Bash end-to-end runs on POSIX CI")
def test_bash_restores_preexisting_ultra_on_staging_failure() -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary) / "skills"
        existing = destination / "crossframe-ultra"
        existing.mkdir(parents=True)
        sentinel = b"preexisting Ultra must survive\n"
        (existing / "SKILL.md").write_bytes(sentinel)
        environment = os.environ.copy()
        environment["FAKE_SKILL_INSTALLER_FAIL_SKILL"] = "crossframe-ultra"
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
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert result.returncode != 0
        assert (existing / "SKILL.md").read_bytes() == sentinel
        assert not list(destination.glob(".crossframe-install-*"))
