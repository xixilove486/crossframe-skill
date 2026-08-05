from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, timezone
import importlib
import os
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
PATHS_FILE = RUNTIME_DIR / "paths.py"


def _runtime_module(name: str):
    module_file = RUNTIME_DIR / f"{name}.py"
    if not module_file.is_file():
        pytest.skip(f"runtime module not implemented yet: {module_file}")
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def paths_module():
    return _runtime_module("paths")


def test_paths_module_exists_for_red_gate() -> None:
    assert PATHS_FILE.is_file(), f"Task 6 path runtime is missing: {PATHS_FILE}"


def test_fixed_roots_modes_and_dataclass_shapes(paths_module) -> None:
    assert paths_module.PRODUCTION_ROOT == Path(r"E:\世界模型\output\crossframe-ultra")
    assert paths_module.TEST_ROOT == Path(r"E:\世界模型\output\crossframe-ultra-tests")
    assert paths_module.RunMode.PRODUCTION.value == "production"
    assert paths_module.RunMode.TEST.value == "test"
    assert [item.name for item in fields(paths_module.RootPolicy)] == [
        "production_root",
        "test_root",
    ]
    assert [item.name for item in fields(paths_module.RunLayout)] == [
        "root",
        "root_staging_dir",
        "run_dir",
        "input_dir",
        "authoring_dir",
        "artifacts_dir",
        "delivery_dir",
        "validation_dir",
        "validation_current_dir",
        "validation_attempts_dir",
        "recovery_dir",
        "logs_dir",
    ]
    assert paths_module.default_root_policy() == paths_module.RootPolicy(
        production_root=paths_module.PRODUCTION_ROOT,
        test_root=paths_module.TEST_ROOT,
    )


def test_create_run_id_uses_utc_timestamp_and_entropy_digest(paths_module) -> None:
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert (
        paths_module.create_run_id(now, b"worker-b")
        == "20260802T030405Z-0482c4aea1af"
    )


@pytest.mark.parametrize(
    ("now", "entropy"),
    [
        (datetime(2026, 8, 2, 3, 4, 5), b"entropy"),
        (
            datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=8))),
            b"entropy",
        ),
        (datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc), "entropy"),
    ],
)
def test_create_run_id_rejects_non_utc_or_non_bytes(paths_module, now, entropy) -> None:
    with pytest.raises((TypeError, ValueError)):
        paths_module.create_run_id(now, entropy)


def test_build_run_layout_selects_fixed_mode_root_and_exact_paths(
    paths_module, tmp_path: Path
) -> None:
    production_root = tmp_path / "production"
    test_root = tmp_path / "test"
    policy = paths_module.RootPolicy(production_root, test_root)
    run_id = "20260802T030405Z-0123456789ab"

    production = paths_module.build_run_layout(
        paths_module.RunMode.PRODUCTION, run_id, policy
    )
    test = paths_module.build_run_layout(paths_module.RunMode.TEST, run_id, policy)

    assert production.root == production_root
    assert test.root == test_root
    expected_run = production_root / "runs/2026/08" / run_id
    assert production == paths_module.RunLayout(
        root=production_root,
        root_staging_dir=production_root / ".staging",
        run_dir=expected_run,
        input_dir=expected_run / "input",
        authoring_dir=expected_run / "work/authoring",
        artifacts_dir=expected_run / "artifacts",
        delivery_dir=expected_run / "delivery",
        validation_dir=expected_run / "validation",
        validation_current_dir=expected_run / "validation/current",
        validation_attempts_dir=expected_run / "validation/attempts",
        recovery_dir=expected_run / "recovery",
        logs_dir=expected_run / "logs",
    )
    assert not production_root.exists()
    assert not test_root.exists()


def test_artifact_subdirectories_are_frozen(paths_module) -> None:
    assert paths_module.ARTIFACT_SUBDIRECTORIES == (
        "U00-U03-evidence",
        "U04-U05-world-volume",
        "U06-U08-inference",
        "U09-U10-verdict",
    )


@pytest.mark.parametrize(
    "run_id",
    [
        r"..\outside",
        r"E:\outside",
        r"\\server\share\run",
        "CON",
        "aux.txt",
        "name.",
        "name ",
        "a" * 241,
        "20260802T030405Z-0123456789AB",
        "20260802T030405-0123456789ab",
        "20260802T030405Z-0123456789ab/child",
        "",
    ],
)
def test_build_run_layout_rejects_malicious_or_malformed_run_ids(
    paths_module, tmp_path: Path, run_id: str
) -> None:
    policy = paths_module.RootPolicy(tmp_path / "production", tmp_path / "test")
    with pytest.raises((TypeError, ValueError, OSError)):
        paths_module.build_run_layout(paths_module.RunMode.TEST, run_id, policy)


def test_build_run_layout_rejects_mode_strings_and_swapped_fixed_roots(
    paths_module, tmp_path: Path
) -> None:
    run_id = "20260802T030405Z-0123456789ab"
    policy = paths_module.RootPolicy(tmp_path / "production", tmp_path / "test")
    with pytest.raises((TypeError, ValueError)):
        paths_module.build_run_layout("test", run_id, policy)

    swapped = paths_module.RootPolicy(
        paths_module.TEST_ROOT, paths_module.PRODUCTION_ROOT
    )
    with pytest.raises((TypeError, ValueError)):
        paths_module.build_run_layout(paths_module.RunMode.PRODUCTION, run_id, swapped)


@pytest.mark.parametrize(
    ("mode", "policy_factory"),
    [
        (
            "production",
            lambda paths, temporary: paths.RootPolicy(
                paths.TEST_ROOT, temporary / "normal-test"
            ),
        ),
        (
            "test",
            lambda paths, temporary: paths.RootPolicy(
                temporary / "normal-production", paths.PRODUCTION_ROOT
            ),
        ),
    ],
)
def test_fixed_roots_are_rejected_individually_in_the_wrong_policy_slot(
    paths_module, tmp_path: Path, mode: str, policy_factory
) -> None:
    policy = policy_factory(paths_module, tmp_path)
    selected_mode = (
        paths_module.RunMode.PRODUCTION
        if mode == "production"
        else paths_module.RunMode.TEST
    )
    with pytest.raises((TypeError, ValueError), match="root|production|test|slot|exchange"):
        paths_module.build_run_layout(
            selected_mode,
            "20260802T030405Z-0123456789ab",
            policy,
        )


@pytest.mark.parametrize("slot", ["production", "test"])
@pytest.mark.parametrize(
    "unsafe_root",
    [
        Path(r"\\server\share\ultra"),
        Path(r"\\?\E:\ultra"),
        Path(r"\\.\E:\ultra"),
    ],
)
def test_root_policy_rejects_unc_and_windows_device_roots_in_either_slot(
    paths_module, tmp_path: Path, slot: str, unsafe_root: Path
) -> None:
    normal_production = tmp_path / "normal-production"
    normal_test = tmp_path / "normal-test"
    policy = paths_module.RootPolicy(
        unsafe_root if slot == "production" else normal_production,
        unsafe_root if slot == "test" else normal_test,
    )
    with pytest.raises((TypeError, ValueError), match="UNC|device|root|anchor"):
        paths_module._validate_policy(policy)


@pytest.mark.parametrize(
    "candidate_factory",
    [
        lambda root: root / ".." / "outside",
        lambda root: Path(r"E:\outside"),
        lambda root: Path(r"\\server\share\run"),
        lambda root: root / "CON",
        lambda root: root / "aux.txt",
        lambda root: root / "name.",
        lambda root: root / "name ",
        lambda root: root / ("a" * 241),
        lambda root: root / "bad<name",
        lambda root: root / "bad|name",
    ],
)
def test_assert_safe_descendant_rejects_escape_and_illegal_components(
    paths_module, tmp_path: Path, candidate_factory
) -> None:
    root = tmp_path / "root"
    candidate = candidate_factory(root)
    with pytest.raises((TypeError, ValueError, OSError)):
        paths_module.assert_safe_descendant(root, candidate)


@pytest.mark.parametrize(
    "device_name",
    [
        "CONIN$",
        "conin$.txt",
        "CONOUT$",
        "conout$.log",
        "COM¹",
        "com².txt",
        "CoM³.log",
        "LPT¹",
        "lpt².txt",
        "LpT³.log",
    ],
)
def test_assert_safe_descendant_rejects_extended_win32_dos_device_names(
    paths_module, tmp_path: Path, device_name: str
) -> None:
    root = tmp_path / "root"
    with pytest.raises((TypeError, ValueError, OSError), match="reserved|device|Windows"):
        paths_module.assert_safe_descendant(root, root / device_name)


def test_assert_safe_descendant_uses_path_semantics_not_string_prefix(
    paths_module, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    sibling = tmp_path / "root-evil" / "run"
    safe = root / "runs" / "2026" / "08"
    assert paths_module.assert_safe_descendant(root, safe) == safe
    with pytest.raises((TypeError, ValueError, OSError)):
        paths_module.assert_safe_descendant(root, sibling)


def test_assert_safe_descendant_normalizes_system_generated_extended_prefix(
    paths_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    candidate = root / "runs" / "2026" / "08"
    real_resolve = Path.resolve

    def resolve_with_extended_candidate(path: Path, strict: bool = False) -> Path:
        resolved = real_resolve(path, strict=strict)
        if path == candidate:
            return Path("\\\\?\\" + str(resolved))
        return resolved

    monkeypatch.setattr(Path, "resolve", resolve_with_extended_candidate)
    assert paths_module.assert_safe_descendant(root, candidate) == candidate


def test_assert_safe_descendant_rejects_conservative_total_path_overflow(
    paths_module, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    candidate = root
    while len(str(candidate)) <= 260:
        candidate = candidate / "abcdefghijklmnopqrst"
    with pytest.raises((TypeError, ValueError, OSError)):
        paths_module.assert_safe_descendant(root, candidate)


def test_existing_reparse_ancestor_is_checked_before_resolution(
    paths_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    reparse_parent = root / "runs"
    reparse_parent.mkdir(parents=True)
    visited: list[Path] = []

    def fake_is_reparse_point(path: Path) -> bool:
        visited.append(Path(path))
        return Path(path) == reparse_parent

    monkeypatch.setattr(paths_module, "_is_reparse_point", fake_is_reparse_point)
    with pytest.raises((ValueError, OSError), match="reparse|symlink|junction"):
        paths_module.assert_safe_descendant(root, reparse_parent / "run")
    assert reparse_parent in visited


def test_symlink_parent_traversal_is_rejected_when_os_allows_creation(
    paths_module, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "linked-parent"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(
            "directory symlink creation unavailable; simulated reparse-attribute "
            f"coverage remains active ({type(error).__name__}: {error})"
        )

    with pytest.raises((ValueError, OSError), match="reparse|symlink|junction"):
        paths_module.assert_safe_descendant(root, link / "escaped")
