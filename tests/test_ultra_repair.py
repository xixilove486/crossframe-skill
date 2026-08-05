from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys
from typing import Iterable

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
RUN_ID = "20260804T120000Z-abcdef123456"
STAMP = datetime(2026, 8, 4, 4, 0, tzinfo=timezone.utc)
REPORT_NAME = "ultra-validator-report.json"
PLAN_NAME = "ultra-repair-plan.json"
ARTICLE_PATH = "work/authoring/article.partial.md"


def load_runtime():
    scripts = str(ULTRA_SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module("ultra_runtime.repair")


def _runtime_module(name: str):
    load_runtime()
    return importlib.import_module(f"ultra_runtime.{name}")


def _layout(tmp_path: Path):
    paths = _runtime_module("paths")
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)
    layout.validation_attempts_dir.mkdir(parents=True)
    layout.validation_current_dir.mkdir(parents=True)
    layout.artifacts_dir.mkdir(parents=True)
    layout.authoring_dir.mkdir(parents=True)
    return layout


def _seal(value: dict[str, object]) -> dict[str, object]:
    schemas = _runtime_module("schemas")
    sealed = copy.deepcopy(value)
    sealed["content_sha256"] = schemas.compute_artifact_content_sha256(sealed)
    return sealed


def _envelope(schema_id: str, generated_at: datetime) -> dict[str, object]:
    constants = _runtime_module("constants")
    return {
        "schema_id": schema_id,
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": constants.current_version_binding(),
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "phase_id": "U12",
    }


def _write_artifact(layout, relative_path: str, payload: bytes) -> str:
    target = layout.run_dir / Path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _manifest(layout) -> tuple[dict[str, object], list[str]]:
    entries: list[dict[str, object]] = []
    upstream_hashes: list[str] = []
    specifications = (
        (
            "artifacts/U00-U03-evidence/evidence.json",
            "U3",
            b"frozen-evidence\n",
        ),
        (
            "artifacts/U09-U10-verdict/verdict.json",
            "U9",
            b"frozen-verdict\n",
        ),
        (
            "artifacts/U09-U10-verdict/output-plan.json",
            "U10",
            b"invalidated-output-plan\n",
        ),
        (ARTICLE_PATH, "U11", b"partial article\n"),
    )
    for index, (path, phase_id, payload) in enumerate(specifications, start=1):
        digest = _write_artifact(layout, path, payload)
        entries.append(
            {
                "path": path,
                "sha256": digest,
                "schema_id": f"crossframe.ultra.v82.fixture-{index}",
                "phase_id": phase_id,
                "media_type": (
                    "text/markdown" if path.endswith(".md") else "application/json"
                ),
            }
        )
        if phase_id in {"U3", "U9"}:
            upstream_hashes.append(digest)

    manifest = _seal(
        {
            **_envelope("crossframe.ultra.v82.artifact-manifest", STAMP),
            "phase_chain_head_sha256": "a" * 64,
            "validator_set_sha256": "b" * 64,
            "artifacts": entries,
            "delivery_artifacts": [],
            "official_delivery_published": False,
        }
    )
    jsonio = _runtime_module("jsonio")
    manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
    jsonio.atomic_write_json(manifest_path, manifest)
    return manifest, sorted(upstream_hashes)


def _report(
    layout,
    *,
    attempt_id: str,
    error_codes: Iterable[str],
    generated_at: datetime,
) -> dict[str, object]:
    jsonio = _runtime_module("jsonio")
    manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
    report = _seal(
        {
            **_envelope("crossframe.ultra.v82.validator-report", generated_at),
            "attempt_id": attempt_id,
            "manifest_sha256": jsonio.sha256_bytes(manifest_path.read_bytes()),
            "validator_set_sha256": "b" * 64,
            "checks": [
                {
                    "validator_id": "semantic-coverage",
                    "status": "fail",
                    "error_codes": list(error_codes),
                    "artifact_refs": [ARTICLE_PATH],
                }
            ],
            "overall_status": "fail",
            "validated_at": generated_at.isoformat().replace("+00:00", "Z"),
            "fresh_context": True,
        }
    )
    attempt_dir = layout.validation_attempts_dir / attempt_id
    attempt_dir.mkdir(parents=True)
    jsonio.atomic_write_json(attempt_dir / REPORT_NAME, report)
    jsonio.atomic_write_json(layout.validation_current_dir / REPORT_NAME, report)
    return report


def _prepare_attempt(
    tmp_path: Path,
    *,
    attempt_id: str = "VALIDATION-1",
    error_codes: Iterable[str] = (
        "ULTRA-COVERAGE-MISSING",
        "ULTRA-ARTICLE-REVIEW-FAILED",
    ),
    generated_at: datetime = STAMP,
):
    layout = _layout(tmp_path)
    _, upstream_hashes = _manifest(layout)
    _report(
        layout,
        attempt_id=attempt_id,
        error_codes=error_codes,
        generated_at=generated_at,
    )
    return layout, upstream_hashes


def test_build_repair_plan_resets_only_from_earliest_phase_and_preserves_upstream(
    tmp_path: Path,
) -> None:
    repair = load_runtime()
    schemas = _runtime_module("schemas")
    layout, upstream_hashes = _prepare_attempt(tmp_path)

    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )

    assert plan["reset_from_phase"] == "U10"
    assert plan["preserved_artifact_hashes"] == upstream_hashes
    assert [failure["affected_phase"] for failure in plan["failures"]] == [
        "U10",
        "U11",
    ]
    assert plan["failures"][0] == {
        "error_code": "ULTRA-COVERAGE-MISSING",
        "artifact": ARTICLE_PATH,
        "affected_phase": "U10",
        "downstream_reset": ["U10", "U11", "U12"],
        "retryable": True,
        "repair_action": "regenerate_missing_semantic_unit_packet",
    }
    assert plan["repair_actions"] == [
        "regenerate_missing_semantic_unit_packet",
        "regenerate_article_from_frozen_packets",
    ]
    assert plan["manifest_regeneration_required"] is True
    assert plan["revalidation_required"] is True
    assert plan["status"] == "planned"
    schemas.validate_instance("ultra-repair-plan.schema.json", plan)


def test_build_repair_plan_refuses_non_retryable_and_stale_failures(
    tmp_path: Path,
) -> None:
    repair = load_runtime()
    layout, _ = _prepare_attempt(
        tmp_path,
        error_codes=("ULTRA-SOURCE-HASH-MISMATCH",),
    )

    with pytest.raises(repair.NonRetryableFailureError):
        repair.build_repair_plan(
            layout,
            attempt_id="VALIDATION-1",
            attempt_number=1,
            now=STAMP + timedelta(minutes=1),
        )

    layout, _ = _prepare_attempt(
        tmp_path / "stale",
        error_codes=("ULTRA-COVERAGE-MISSING",),
    )
    current = _runtime_module("jsonio").load_json_object(
        layout.validation_current_dir / REPORT_NAME
    )
    current["generated_at"] = "2026-08-04T04:02:00Z"
    current = _seal(current)
    _runtime_module("jsonio").atomic_write_json(
        layout.validation_current_dir / REPORT_NAME, current
    )

    with pytest.raises(repair.StaleValidationAttemptError):
        repair.build_repair_plan(
            layout,
            attempt_id="VALIDATION-1",
            attempt_number=1,
            now=STAMP + timedelta(minutes=2),
        )


def test_build_repair_plan_refuses_a_fourth_attempt(tmp_path: Path) -> None:
    repair = load_runtime()
    layout, _ = _prepare_attempt(
        tmp_path,
        error_codes=("ULTRA-COVERAGE-MISSING",),
    )

    with pytest.raises(repair.RepairAttemptLimitError):
        repair.build_repair_plan(
            layout,
            attempt_id="VALIDATION-1",
            attempt_number=4,
            now=STAMP + timedelta(minutes=1),
        )


def test_repeated_failure_marks_plan_and_run_needs_attention(
    tmp_path: Path,
) -> None:
    repair = load_runtime()
    jsonio = _runtime_module("jsonio")
    status = _runtime_module("status")
    layout, _ = _prepare_attempt(
        tmp_path,
        error_codes=("ULTRA-COVERAGE-MISSING",),
    )
    store = status.RunStatusStore(layout)
    created = store.create(STAMP - timedelta(minutes=2))
    store.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    first = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    jsonio.atomic_write_json(
        layout.validation_attempts_dir / "VALIDATION-1" / PLAN_NAME,
        first,
    )
    _report(
        layout,
        attempt_id="VALIDATION-2",
        error_codes=("ULTRA-COVERAGE-MISSING",),
        generated_at=STAMP + timedelta(minutes=2),
    )

    second = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-2",
        attempt_number=2,
        now=STAMP + timedelta(minutes=3),
    )

    assert second["status"] == "needs_attention"
    authority = store.read()
    assert authority.status == "needs_attention"
    assert authority.validation_passed is False
    assert authority.current_phase == "U12"
    assert authority.last_complete_phase == "U11"


@pytest.mark.parametrize(
    "relative_script",
    (
        "skills/crossframe-ultra/scripts/build_crossframe_ultra_repair_plan.py",
        "scripts/build_crossframe_ultra_repair_plan.py",
    ),
)
def test_repair_plan_cli_exposes_only_fixed_root_arguments(
    relative_script: str,
) -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT / relative_script), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    for option in ("--repo", "--mode", "--run-id"):
        assert option in completed.stdout
    for option in (
        "--run-dir",
        "--authoring-dir",
        "--output-root",
        "--destination",
        "--fallback",
        "--attempt-id",
        "--attempt-number",
    ):
        assert option not in completed.stdout
