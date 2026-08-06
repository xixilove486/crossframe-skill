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
POST_PROMOTION_TAMPER_CASES = (
    (
        "before",
        "skills/crossframe-ultra/SKILL.md",
        "Post-promotion skill tree verification failed",
    ),
    (
        "after",
        "scripts/check_crossframe_ultra_artifacts.py",
        "Post-promotion Ultra root wrapper verification failed",
    ),
    (
        "after",
        "skills/crossframe-ultra/scripts/ultra_runtime/validation.py",
        "Post-promotion validator-set verification failed",
    ),
    (
        "after",
        "skills/crossframe-ultra/templates/ultra-article-output.md",
        "Post-promotion release manifest verification failed",
    ),
)


def _assert_installed(source: Path, destination: Path) -> None:
    installed = tuple(sorted(path.parent.name for path in destination.glob("*/SKILL.md")))
    assert installed == tuple(sorted(EXPECTED_SKILLS))
    for skill in EXPECTED_SKILLS:
        assert same_tree(source / "skills" / skill, destination / skill), skill
    digest_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            (
                "from pathlib import Path\n"
                "import sys\n"
                "canonical_scripts = "
                "Path(sys.argv[1]).resolve(strict=True) / "
                "'skills/crossframe-ultra/scripts'\n"
                "sys.path.insert(0, str(canonical_scripts))\n"
                "from ultra_runtime.validation import validator_set_sha256\n"
                "print(validator_set_sha256(Path(sys.argv[2])))\n"
                "print(validator_set_sha256(Path(sys.argv[3])))\n"
            ),
            str(source),
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

    source_wrapper = source / "scripts/check_crossframe_ultra_artifacts.py"
    installed_wrapper = destination.parent / "scripts/check_crossframe_ultra_artifacts.py"
    assert installed_wrapper.read_bytes() == source_wrapper.read_bytes()

    manifest_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(
                source
                / "skills/crossframe-ultra/scripts/build_crossframe_ultra_release_manifest.py"
            ),
            "--repo",
            str(destination.parent),
            "--check",
        ],
        cwd=destination.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr
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
    manifest_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(
                ROOT
                / "skills/crossframe-ultra/scripts/build_crossframe_ultra_release_manifest.py"
            ),
            "--repo",
            str(candidate),
            "--write",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr
    return candidate


def _arm_post_promotion_tamper(
    candidate: Path,
    *,
    destination: Path,
    install_root: Path,
    relative_target: str,
    timing: str,
) -> dict[str, str]:
    wrapper = candidate / "scripts/sync_skill_mirrors.py"
    wrapper.write_text(
        """from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


arguments = sys.argv[1:]
mirrors = [
    Path(arguments[index + 1]).resolve()
    for index, value in enumerate(arguments[:-1])
    if value == "--mirror"
]
target_mirror = Path(os.environ["TEST_POST_PROMOTION_MIRROR"]).resolve()
is_post_promotion = target_mirror in mirrors and "--check" in arguments
timing = os.environ["TEST_POST_PROMOTION_TAMPER_TIMING"]
target = Path(os.environ["TEST_POST_PROMOTION_TAMPER_PATH"])

if is_post_promotion and timing == "before":
    target.write_bytes(b"post-promotion tamper\\n")

completed = subprocess.run(
    [sys.executable, os.environ["TEST_REAL_SYNC_SKILL_MIRRORS"], *arguments],
    check=False,
)

if completed.returncode == 0 and is_post_promotion and timing == "after":
    target.write_bytes(b"post-promotion tamper\\n")

raise SystemExit(completed.returncode)
""",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "TEST_POST_PROMOTION_MIRROR": str(destination),
            "TEST_POST_PROMOTION_TAMPER_PATH": str(install_root / relative_target),
            "TEST_POST_PROMOTION_TAMPER_TIMING": timing,
            "TEST_REAL_SYNC_SKILL_MIRRORS": str(ROOT / "scripts/sync_skill_mirrors.py"),
        }
    )
    return environment


def _seed_preexisting_installation(
    install_root: Path,
) -> tuple[Path, Path, bytes, Path, bytes]:
    destination = install_root / "skills"
    existing = destination / "crossframe-ultra"
    existing.mkdir(parents=True)
    skill_sentinel = b"preexisting Ultra must survive\n"
    (existing / "SKILL.md").write_bytes(skill_sentinel)
    wrapper = install_root / "scripts/check_crossframe_ultra_artifacts.py"
    wrapper.parent.mkdir(parents=True)
    wrapper_sentinel = b"preexisting wrapper must survive\n"
    wrapper.write_bytes(wrapper_sentinel)
    return destination, existing, skill_sentinel, wrapper, wrapper_sentinel


def _assert_preexisting_installation_restored(
    destination: Path,
    existing: Path,
    skill_sentinel: bytes,
    wrapper: Path,
    wrapper_sentinel: bytes,
) -> None:
    assert (existing / "SKILL.md").read_bytes() == skill_sentinel
    assert wrapper.read_bytes() == wrapper_sentinel
    assert tuple(path.name for path in destination.iterdir()) == ("crossframe-ultra",)
    assert not list(destination.glob(".crossframe-install-*"))


def _assert_post_promotion_tamper_rolls_back(
    command_prefix: list[str],
    *,
    repo_option: str,
    destination_option: str,
    timing: str,
    relative_target: str,
    expected_error: str,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        install_root = Path(temporary)
        candidate = _make_local_candidate(install_root)
        (
            destination,
            existing,
            skill_sentinel,
            wrapper,
            wrapper_sentinel,
        ) = _seed_preexisting_installation(install_root / "destination")
        environment = _arm_post_promotion_tamper(
            candidate,
            destination=destination,
            install_root=destination.parent,
            relative_target=relative_target,
            timing=timing,
        )
        result = subprocess.run(
            [
                *command_prefix,
                repo_option,
                str(candidate),
                destination_option,
                str(destination),
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert result.returncode != 0, result.stdout + result.stderr
        assert expected_error in result.stdout + result.stderr
        _assert_preexisting_installation_restored(
            destination,
            existing,
            skill_sentinel,
            wrapper,
            wrapper_sentinel,
        )


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


@pytest.mark.parametrize(
    ("timing", "relative_target", "expected_error"),
    POST_PROMOTION_TAMPER_CASES,
)
def test_powershell_rolls_back_when_post_promotion_authority_is_tampered(
    timing: str,
    relative_target: str,
    expected_error: str,
) -> None:
    powershell = _powershell()
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    _assert_post_promotion_tamper_rolls_back(
        [
            powershell,
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/install-codex.ps1"),
        ],
        repo_option="-Repo",
        destination_option="-DestinationRoot",
        timing=timing,
        relative_target=relative_target,
        expected_error=expected_error,
    )


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


@pytest.mark.skipif(os.name == "nt", reason="Bash end-to-end runs on POSIX CI")
@pytest.mark.parametrize(
    ("timing", "relative_target", "expected_error"),
    POST_PROMOTION_TAMPER_CASES,
)
def test_bash_rolls_back_when_post_promotion_authority_is_tampered(
    timing: str,
    relative_target: str,
    expected_error: str,
) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")
    _assert_post_promotion_tamper_rolls_back(
        [bash, str(ROOT / "scripts/install-codex.sh")],
        repo_option="--repo",
        destination_option="--dest",
        timing=timing,
        relative_target=relative_target,
        expected_error=expected_error,
    )
