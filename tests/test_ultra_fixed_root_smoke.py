from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "tests/run_ultra_fixed_root_smoke.py"
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"


def _load_runner():
    assert RUNNER_PATH.is_file(), RUNNER_PATH
    spec = importlib.util.spec_from_file_location(
        "task17_ultra_fixed_root_smoke", RUNNER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root_policy(tmp_path: Path):
    import sys

    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from ultra_runtime.paths import RootPolicy

    return RootPolicy(tmp_path / "production", tmp_path / "test")


def test_task17_repository_owned_fixed_root_runner_executes_full_closed_smoke(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    policy = _root_policy(tmp_path)
    policy.production_root.mkdir(parents=True)
    (policy.production_root / "START-HERE.md").write_bytes(b"production-start\n")
    (policy.production_root / "index").mkdir()
    (policy.production_root / "index/runs.jsonl").write_bytes(
        b'{"production":"index"}\n'
    )
    legacy_run = policy.test_root / "runs/2025/01/legacy"
    legacy = legacy_run / "user-output.bin"
    legacy_start_here = legacy_run / "START-HERE.md"
    legacy_run.mkdir(parents=True)
    legacy.write_bytes(b"preserve-existing-test-output\n")
    legacy_start_here_bytes = b"preserve-existing-run-navigation\n"
    legacy_start_here.write_bytes(legacy_start_here_bytes)

    existing_run_outputs = runner._existing_run_outputs(policy.test_root)
    assert existing_run_outputs.get("2025/01/legacy/START-HERE.md") == (
        hashlib.sha256(legacy_start_here_bytes).hexdigest()
    )

    result = runner.run_fixed_root_smoke(
        root_policy=policy,
        started_at=datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc),
        run_entropy=b"task17-fixed-root-run",
        transaction_entropy=b"task17-fixed-root-transaction",
    )

    assert result["status"] == "complete"
    assert result["phase_ids"] == [f"U{number}" for number in range(13)]
    assert result["phase_checkpoint_ids"] == [
        f"U{number}" for number in range(13)
    ]
    assert result["pre_u12_official_absent"] is True
    assert result["validator_overall_status"] == "pass"
    assert result["validator_fresh_context"] is True
    assert result["manifest_official_delivery_published"] is True
    assert set(result["delivery_sha256"]) == {
        "CrossFrame-Ultra-完整文章.md",
        "完整推演档案.md",
        "工件索引.md",
    }
    assert result["latest_complete_run_id"] == result["run_id"]
    assert result["start_here_resolved"] is True
    assert result["staging_clean"] is True
    assert result["existing_test_outputs_preserved"] is True
    assert result["production_surface_before_sha256"] == result[
        "production_surface_after_sha256"
    ]
    assert legacy.read_bytes() == b"preserve-existing-test-output\n"
    assert legacy_start_here.read_bytes() == legacy_start_here_bytes
    assert Path(result["run_dir"]).is_relative_to(policy.test_root)
    assert Path(result["canonical_skill_root"]) == (
        REPO_ROOT / "skills/crossframe-ultra"
    ).resolve()


def test_task17_formal_entry_rejects_arbitrary_root_arguments(
    tmp_path: Path,
) -> None:
    runner = _load_runner()

    assert runner.main(["--root", str(tmp_path)]) == 2
