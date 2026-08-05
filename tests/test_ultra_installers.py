from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from tests.pytest_import_guard import pytest

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
    installed_scripts = destination / "crossframe-ultra/scripts"
    digest_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            (
                "from pathlib import Path\n"
                "import sys\n"
                "installed_scripts = Path(sys.argv[1]).resolve(strict=True)\n"
                "sys.path.insert(0, str(installed_scripts))\n"
                "from ultra_runtime.validation import validator_set_sha256\n"
                "print(validator_set_sha256(Path(sys.argv[2])))\n"
                "print(validator_set_sha256(Path(sys.argv[3])))\n"
            ),
            str(installed_scripts),
            str(source),
            str(destination.parent),
        ],
        cwd=destination.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert digest_result.returncode == 0, digest_result.stdout + digest_result.stderr
    candidate_digest, installed_digest = digest_result.stdout.splitlines()
    assert re.fullmatch(r"[0-9a-f]{64}", installed_digest)
    assert installed_digest == candidate_digest

    wrapper_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(destination.parent / "scripts/check_crossframe_ultra_artifacts.py"),
            "--help",
        ],
        cwd=destination.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert wrapper_result.returncode == 0, wrapper_result.stdout + wrapper_result.stderr
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
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_artifacts.py", scripts)
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
        unowned_script = destination.parent / "scripts/unowned.py"
        unowned_script.parent.mkdir(parents=True)
        unowned_script.write_bytes(b"preexisting destination script\n")
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
        assert unowned_script.read_bytes() == b"preexisting destination script\n"


def test_powershell_restores_preexisting_ultra_on_staging_failure() -> None:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        install_root = Path(temporary)
        destination = install_root / "skills"
        existing = destination / "crossframe-ultra"
        existing.mkdir(parents=True)
        sentinel = b"preexisting Ultra must survive\n"
        (existing / "SKILL.md").write_bytes(sentinel)
        wrapper = install_root / "scripts/check_crossframe_ultra_artifacts.py"
        wrapper.parent.mkdir(parents=True)
        wrapper_sentinel = b"preexisting wrapper must survive\n"
        wrapper.write_bytes(wrapper_sentinel)
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
        assert wrapper.read_bytes() == wrapper_sentinel
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
        unowned_script = destination.parent / "scripts/unowned.py"
        unowned_script.parent.mkdir(parents=True)
        unowned_script.write_bytes(b"preexisting destination script\n")
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
        assert unowned_script.read_bytes() == b"preexisting destination script\n"


@pytest.mark.skipif(os.name == "nt", reason="Bash end-to-end runs on POSIX CI")
def test_bash_restores_preexisting_ultra_on_staging_failure() -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")
    with tempfile.TemporaryDirectory() as temporary:
        install_root = Path(temporary)
        destination = install_root / "skills"
        existing = destination / "crossframe-ultra"
        existing.mkdir(parents=True)
        sentinel = b"preexisting Ultra must survive\n"
        (existing / "SKILL.md").write_bytes(sentinel)
        wrapper = install_root / "scripts/check_crossframe_ultra_artifacts.py"
        wrapper.parent.mkdir(parents=True)
        wrapper_sentinel = b"preexisting wrapper must survive\n"
        wrapper.write_bytes(wrapper_sentinel)
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
        assert wrapper.read_bytes() == wrapper_sentinel
        assert not list(destination.glob(".crossframe-install-*"))
