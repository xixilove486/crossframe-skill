from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys
from threading import Event
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
            "active_generation": 0,
            "article_sha256": hashlib.sha256(
                (layout.run_dir / ARTICLE_PATH).read_bytes()
            ).hexdigest(),
            "semantic_review_artifact_sha256": "c" * 64,
            "checks": [
                {
                    "validator_id": "semantic-coverage",
                    "status": "fail",
                    "error_codes": list(error_codes),
                    "artifact_refs": [ARTICLE_PATH],
                }
            ],
            "layers": [
                {
                    "layer_id": layer_id,
                    "status": "fail" if layer_id == "fresh-semantic" else "pass",
                    "artifact_refs": [ARTICLE_PATH],
                }
                for layer_id in (
                    "deterministic",
                    "adversarial",
                    "fresh-semantic",
                )
            ],
            "overall_status": "fail",
            "publication_allowed": False,
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


def _phase_output_hashes(
    phase_id: str,
    *,
    run_contract_sha256: str,
    overrides: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if phase_id == "U0":
        return (run_contract_sha256,)
    counts = {
        "U1": 3,
        "U4": 1,
        "U5": 2,
        "U6": 1,
        "U7": 2,
        "U8": 2,
        "U9": 3,
        "U10": 2,
        "U11": 6,
        "U12": 5,
    }
    count = counts.get(phase_id, 1)
    selected = list(overrides.get(phase_id, ()))
    while len(selected) < count:
        selected.append(
            hashlib.sha256(f"{phase_id}-output-{len(selected)}".encode()).hexdigest()
        )
    return tuple(selected[:count])


def _write_recovery_chain(
    layout,
    *,
    through_phase: str,
    output_overrides: dict[str, tuple[str, ...]] | None = None,
) -> tuple[dict[str, object], ...]:
    constants = _runtime_module("constants")
    jsonio = _runtime_module("jsonio")
    recovery = _runtime_module("recovery")
    schemas = _runtime_module("schemas")
    state_machine = _runtime_module("state_machine")
    request_path = layout.input_dir / "request.bin"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_bytes(b"repair-parent-request\n")
    request_sha256 = hashlib.sha256(request_path.read_bytes()).hexdigest()
    run_contract_sha256 = hashlib.sha256(b"sealed run contract\n").hexdigest()
    authority = {
        "schema_id": "crossframe.ultra.v82.recovery-authority",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": constants.current_version_binding(),
        "source_sha256": "2" * 64,
        "input_artifact_hashes": [request_sha256],
        "input_snapshot_sha256": request_sha256,
        "evidence_cutoff": "2026-08-04T04:00:00Z",
        "run_contract_sha256": run_contract_sha256,
        "input_refs": [
            {
                "path": "input/request.bin",
                "sha256": request_sha256,
                "media_type": "application/octet-stream",
            }
        ],
        "content_sha256": "0" * 64,
    }
    authority["content_sha256"] = schemas.compute_artifact_content_sha256(authority)
    recovery_dir = layout.recovery_dir
    recovery_dir.mkdir(parents=True, exist_ok=True)
    jsonio.atomic_write_json(recovery_dir / "run-authority.json", authority)

    overrides = output_overrides or {}
    phases = constants.PHASES[: constants.PHASES.index(through_phase) + 1]
    parent = "0" * 64
    events = []
    for ordinal, phase_id in enumerate(phases):
        timestamp = (STAMP + timedelta(seconds=ordinal)).isoformat().replace(
            "+00:00", "Z"
        )
        event = {
            "schema_id": state_machine.PHASE_EVENT_SCHEMA_ID,
            "schema_version": 1,
            "run_id": layout.run_dir.name,
            "version_binding": constants.current_version_binding(),
            "generated_at": timestamp,
            "content_sha256": "0" * 64,
            "phase_id": phase_id,
            "event_type": "phase-completed",
            "parent_event_sha256": parent,
            "input_artifact_hashes": [request_sha256],
            "output_artifact_hashes": list(
                _phase_output_hashes(
                    phase_id,
                    run_contract_sha256=run_contract_sha256,
                    overrides=overrides,
                )
            ),
            "source_sha256": "2" * 64,
            "evidence_cutoff": "2026-08-04T04:00:00Z",
            "run_contract_sha256": run_contract_sha256,
            "timestamp": timestamp,
            "status": "complete",
            "failure_code": None,
            "invalidated_phases": [],
            "event_sha256": "0" * 64,
        }
        event["content_sha256"] = state_machine._compute_event_content_sha256(event)
        event["event_sha256"] = state_machine.compute_event_sha256(event)
        events.append(event)
        parent = str(event["event_sha256"])
    (recovery_dir / "phase-events.jsonl").write_bytes(
        b"".join(jsonio.canonical_json_bytes(event) for event in events)
    )
    recovery._read_events(layout, authority, compatibility="resume")
    return tuple(events)


def _write_article_packet_checkpoint(
    layout,
    *,
    u10_event: dict[str, object],
    generation: int,
    generated_at: datetime,
    partial_path: Path,
    packet_path: Path,
) -> dict[str, object]:
    jsonio = _runtime_module("jsonio")
    schemas = _runtime_module("schemas")
    checkpoint = {
        "schema_id": "crossframe.ultra.v82.recovery-checkpoint",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": _runtime_module("constants").current_version_binding(),
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "content_sha256": "0" * 64,
        "phase_id": "U11",
        "boundary_kind": "article-packet",
        "boundary_id": packet_path.stem,
        "boundary_ordinal": 1,
        "generation": generation,
        "phase_event_sha256": u10_event["event_sha256"],
        "artifact_hashes": [
            {
                "path": partial_path.relative_to(layout.run_dir).as_posix(),
                "sha256": hashlib.sha256(partial_path.read_bytes()).hexdigest(),
                "media_type": "text/markdown",
            },
            {
                "path": packet_path.relative_to(layout.run_dir).as_posix(),
                "sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                "media_type": "text/markdown",
            },
        ],
        "evidence_cutoff": "2026-08-04T04:00:00Z",
        "completed_boundary": True,
        "resumable": True,
    }
    checkpoint["content_sha256"] = schemas.compute_artifact_content_sha256(
        checkpoint
    )
    raw = jsonio.canonical_json_bytes(checkpoint)
    target = layout.recovery_dir / "checkpoints" / (
        f"{hashlib.sha256(raw).hexdigest()}.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return checkpoint


def _prepare_u11_repair(tmp_path: Path):
    repair = load_runtime()
    jsonio = _runtime_module("jsonio")
    status_module = _runtime_module("status")
    layout, _ = _prepare_attempt(
        tmp_path,
        error_codes=("ULTRA-ARTICLE-REVIEW-FAILED",),
    )
    manifest = jsonio.load_json_object(
        layout.artifacts_dir / "ultra-artifact-manifest.json"
    )
    by_phase = {
        str(item["phase_id"]): str(item["sha256"])
        for item in manifest["artifacts"]
    }
    events = _write_recovery_chain(
        layout,
        through_phase="U11",
        output_overrides={
            "U3": (by_phase["U3"],),
            "U9": (by_phase["U9"],),
            "U10": (by_phase["U10"],),
            "U11": (by_phase["U11"],),
        },
    )
    statuses = status_module.RunStatusStore(layout)
    created = statuses.create(STAMP - timedelta(minutes=2))
    statuses.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    repair.commit_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        plan=plan,
    )
    return repair, layout, events, plan


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


def test_apply_repair_plan_is_append_only_and_generation_bound(tmp_path: Path) -> None:
    repair = load_runtime()
    jsonio = _runtime_module("jsonio")
    schemas = _runtime_module("schemas")
    layout, _ = _prepare_attempt(tmp_path)
    manifest = jsonio.load_json_object(
        layout.artifacts_dir / "ultra-artifact-manifest.json"
    )
    by_phase = {
        str(item["phase_id"]): str(item["sha256"])
        for item in manifest["artifacts"]
    }
    before_events = _write_recovery_chain(
        layout,
        through_phase="U11",
        output_overrides={
            "U3": (by_phase["U3"],),
            "U9": (by_phase["U9"],),
            "U10": (by_phase["U10"],),
            "U11": (by_phase["U11"],),
        },
    )
    status = _runtime_module("status").RunStatusStore(layout)
    created = status.create(STAMP - timedelta(minutes=2))
    status.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    repair.commit_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        plan=plan,
    )
    before_artifacts = {
        Path(str(item["path"])): (layout.run_dir / str(item["path"])).read_bytes()
        for item in manifest["artifacts"]
    }

    result = repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    repeated = repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=3),
    )
    application_path = (
        layout.recovery_dir
        / "repair-attempts"
        / "VALIDATION-1"
        / "repair-application.json"
    )
    application_bytes = application_path.read_bytes()
    application_path.unlink()
    recovered = repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=4),
    )

    event_rows = [
        jsonio.load_json_object_bytes(row, source="repair event")
        for row in (layout.recovery_dir / "phase-events.jsonl").read_bytes().splitlines(
            keepends=True
        )
    ]
    assert event_rows[: len(before_events)] == list(before_events)
    assert len(event_rows) == len(before_events) + 1
    invalidation = event_rows[-1]
    assert invalidation["event_type"] == "repair-invalidation"
    assert invalidation["generation"] == 1
    assert invalidation["reset_from_phase"] == "U10"
    assert invalidation["repair_plan_sha256"] == hashlib.sha256(
        jsonio.canonical_json_bytes(plan)
    ).hexdigest()
    assert invalidation["superseded_event_sha256s"] == [
        before_events[10]["event_sha256"],
        before_events[11]["event_sha256"],
    ]
    schemas.validate_instance("ultra-phase-event.schema.json", invalidation)
    assert result == repeated
    assert result == recovered
    assert application_path.read_bytes() == application_bytes
    assert result["reopened_phase"] == "U10"
    assert result["active_generation"] == 1
    assert result["next_action"]["relative_path"] == "U10-output-plan.json"
    reopened = status.read()
    assert reopened.status == "running"
    assert reopened.current_phase == "U10"
    assert reopened.last_complete_phase == "U9"
    assert reopened.validation_passed is False
    attempt_root = layout.recovery_dir / "repair-attempts" / "VALIDATION-1"
    snapshot = jsonio.load_json_object(attempt_root / "superseded-snapshot.json")
    preserved = {
        Path(str(item["original_path"])): Path(str(item["snapshot_path"]))
        for item in snapshot["artifacts"]
    }
    for relative, payload in before_artifacts.items():
        assert (layout.run_dir / relative).read_bytes() == payload
        if relative in {
            Path("artifacts/U09-U10-verdict/output-plan.json"),
            Path(ARTICLE_PATH),
        }:
            snapshot_path = layout.run_dir / preserved[relative]
            assert len(str(snapshot_path)) <= 240
            assert snapshot_path.read_bytes() == payload


def test_materialization_applies_one_pending_failed_validation_repair(
    tmp_path: Path,
) -> None:
    jsonio = _runtime_module("jsonio")
    locks = _runtime_module("locks")
    materialization = _runtime_module("materialization")
    status_module = _runtime_module("status")
    layout, _ = _prepare_attempt(tmp_path)
    manifest = jsonio.load_json_object(
        layout.artifacts_dir / "ultra-artifact-manifest.json"
    )
    by_phase = {
        str(item["phase_id"]): str(item["sha256"])
        for item in manifest["artifacts"]
    }
    _write_recovery_chain(
        layout,
        through_phase="U11",
        output_overrides={
            "U3": (by_phase["U3"],),
            "U9": (by_phase["U9"],),
            "U10": (by_phase["U10"],),
            "U11": (by_phase["U11"],),
        },
    )
    statuses = status_module.RunStatusStore(layout)
    created = statuses.create(STAMP - timedelta(minutes=2))
    statuses.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    now = STAMP + timedelta(minutes=2)
    lease = locks.acquire_run_lease(layout, now, timedelta(minutes=5))
    try:
        result = materialization._apply_pending_validation_repair(
            layout,
            now=now,
            lease=lease,
        )
        repeated = materialization._apply_pending_validation_repair(
            layout,
            now=now + timedelta(minutes=1),
            lease=lease,
        )
    finally:
        locks.release_run_lease(layout, lease)

    assert result is not None
    assert result.outcome == "repair-applied"
    assert result.status == "running"
    assert result.reopened_phase == "U10"
    assert result.active_generation == 1
    assert result.next_action["relative_path"] == "U10-output-plan.json"
    assert repeated is None
    attempt_root = layout.recovery_dir / "repair-attempts" / "VALIDATION-1"
    assert (
        layout.validation_attempts_dir
        / "VALIDATION-1"
        / "ultra-repair-plan.json"
    ).is_file()
    assert (attempt_root / "repair-application.json").is_file()


def test_superseded_checkpoint_uses_preserved_bytes_after_fixed_path_reuse(
    tmp_path: Path,
) -> None:
    repair = load_runtime()
    jsonio = _runtime_module("jsonio")
    recovery = _runtime_module("recovery")
    schemas = _runtime_module("schemas")
    status_module = _runtime_module("status")
    layout, _ = _prepare_attempt(tmp_path)
    manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
    manifest = jsonio.load_json_object(manifest_path)
    gap_path = layout.run_dir / "artifacts/U09-U10-verdict/framework-gap.json"
    gap_sha256 = _write_artifact(
        layout,
        gap_path.relative_to(layout.run_dir).as_posix(),
        b"invalidated-framework-gap\n",
    )
    manifest["artifacts"].append(
        {
            "path": gap_path.relative_to(layout.run_dir).as_posix(),
            "sha256": gap_sha256,
            "schema_id": "crossframe.ultra.v82.fixture-gap",
            "phase_id": "U10",
            "media_type": "application/json",
        }
    )
    manifest = _seal(manifest)
    jsonio.atomic_write_json(manifest_path, manifest)
    report_path = layout.validation_current_dir / REPORT_NAME
    report = jsonio.load_json_object(report_path)
    report["manifest_sha256"] = jsonio.sha256_bytes(manifest_path.read_bytes())
    report = _seal(report)
    jsonio.atomic_write_json(report_path, report)
    jsonio.atomic_write_json(
        layout.validation_attempts_dir / "VALIDATION-1" / REPORT_NAME,
        report,
    )
    output_plan_path = layout.run_dir / "artifacts/U09-U10-verdict/output-plan.json"
    output_plan_sha256 = hashlib.sha256(output_plan_path.read_bytes()).hexdigest()
    evidence_path = layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    verdict_path = layout.run_dir / "artifacts/U09-U10-verdict/verdict.json"
    article_path = layout.run_dir / ARTICLE_PATH
    events = _write_recovery_chain(
        layout,
        through_phase="U11",
        output_overrides={
            "U3": (hashlib.sha256(evidence_path.read_bytes()).hexdigest(),),
            "U9": (hashlib.sha256(verdict_path.read_bytes()).hexdigest(),),
            "U10": (gap_sha256, output_plan_sha256),
            "U11": (hashlib.sha256(article_path.read_bytes()).hexdigest(),),
        },
    )
    checkpoint = {
        "schema_id": "crossframe.ultra.v82.recovery-checkpoint",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": _runtime_module("constants").current_version_binding(),
        "generated_at": (STAMP + timedelta(seconds=30)).isoformat().replace(
            "+00:00", "Z"
        ),
        "content_sha256": "0" * 64,
        "phase_id": "U10",
        "boundary_kind": "phase",
        "boundary_id": "U10",
        "boundary_ordinal": 0,
        "generation": 0,
        "phase_event_sha256": events[10]["event_sha256"],
        "artifact_hashes": [
            {
                "path": gap_path.relative_to(layout.run_dir).as_posix(),
                "sha256": gap_sha256,
                "media_type": "application/json",
            },
            {
                "path": output_plan_path.relative_to(layout.run_dir).as_posix(),
                "sha256": output_plan_sha256,
                "media_type": "application/json",
            },
        ],
        "evidence_cutoff": "2026-08-04T04:00:00Z",
        "completed_boundary": True,
        "resumable": True,
    }
    checkpoint["content_sha256"] = schemas.compute_artifact_content_sha256(
        checkpoint
    )
    checkpoint_raw = jsonio.canonical_json_bytes(checkpoint)
    checkpoint_path = layout.recovery_dir / "checkpoints" / (
        f"{hashlib.sha256(checkpoint_raw).hexdigest()}.json"
    )
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_bytes(checkpoint_raw)
    statuses = status_module.RunStatusStore(layout)
    created = statuses.create(STAMP - timedelta(minutes=2))
    statuses.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    repair.commit_repair_plan(layout, attempt_id="VALIDATION-1", plan=plan)
    repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    gap_path.write_bytes(b"replacement-framework-gap\n")
    output_plan_path.write_bytes(b"replacement-output-plan\n")

    assert recovery.load_checkpoints(layout) == (checkpoint,)


def test_u11_repair_preserves_article_packet_checkpoint_bytes_after_path_reuse(
    tmp_path: Path,
) -> None:
    recovery = _runtime_module("recovery")
    jsonio = _runtime_module("jsonio")
    repair, layout, events, plan = _prepare_u11_repair(tmp_path)
    partial_path = layout.run_dir / ARTICLE_PATH
    packet_path = layout.authoring_dir / "article/packets/packet-01.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_bytes(b"superseded packet\n")
    checkpoint = _write_article_packet_checkpoint(
        layout,
        u10_event=events[10],
        generation=0,
        generated_at=STAMP + timedelta(seconds=20),
        partial_path=partial_path,
        packet_path=packet_path,
    )
    old_partial = partial_path.read_bytes()
    old_packet = packet_path.read_bytes()

    repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    partial_path.write_bytes(b"replacement partial article\n")
    packet_path.write_bytes(b"replacement packet\n")

    assert recovery.load_checkpoints(layout) == (checkpoint,)
    snapshot = jsonio.load_json_object(
        layout.recovery_dir
        / "repair-attempts"
        / "VALIDATION-1"
        / "superseded-snapshot.json"
    )
    preserved = {
        str(item["original_path"]): layout.run_dir / str(item["snapshot_path"])
        for item in snapshot["artifacts"]
    }
    assert preserved[partial_path.relative_to(layout.run_dir).as_posix()].read_bytes() == (
        old_partial
    )
    assert preserved[packet_path.relative_to(layout.run_dir).as_posix()].read_bytes() == (
        old_packet
    )


def test_repaired_article_packet_checkpoint_uses_active_generation_and_retained_u10(
    tmp_path: Path,
) -> None:
    recovery = _runtime_module("recovery")
    repair, layout, events, plan = _prepare_u11_repair(tmp_path)
    repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    partial_path = layout.run_dir / ARTICLE_PATH
    packet_path = layout.authoring_dir / "article/packets/packet-01.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path.write_bytes(b"replacement partial article\n")
    packet_path.write_bytes(b"replacement packet\n")
    checkpoint = _write_article_packet_checkpoint(
        layout,
        u10_event=events[10],
        generation=1,
        generated_at=STAMP + timedelta(minutes=3),
        partial_path=partial_path,
        packet_path=packet_path,
    )

    assert checkpoint["generation"] == 1
    assert events[10].get("generation", 0) == 0
    assert recovery.load_checkpoints(layout) == (checkpoint,)
    assert recovery.select_resume_checkpoint(layout) == checkpoint


def test_repaired_article_packet_checkpoint_cannot_predate_its_invalidation(
    tmp_path: Path,
) -> None:
    recovery = _runtime_module("recovery")
    repair, layout, events, plan = _prepare_u11_repair(tmp_path)
    repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    partial_path = layout.run_dir / ARTICLE_PATH
    packet_path = layout.authoring_dir / "article/packets/packet-01.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path.write_bytes(b"replacement partial article\n")
    packet_path.write_bytes(b"replacement packet\n")
    _write_article_packet_checkpoint(
        layout,
        u10_event=events[10],
        generation=1,
        generated_at=STAMP + timedelta(seconds=30),
        partial_path=partial_path,
        packet_path=packet_path,
    )

    with pytest.raises(
        recovery.RecoveryIntegrityError,
        match="predates|generation|invalidation",
    ):
        recovery.load_checkpoints(layout)


def test_apply_repair_plan_recovers_after_snapshot_before_event_crash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repair = load_runtime()
    jsonio = _runtime_module("jsonio")
    recovery = _runtime_module("recovery")
    status_module = _runtime_module("status")
    layout, _ = _prepare_attempt(tmp_path)
    manifest = jsonio.load_json_object(
        layout.artifacts_dir / "ultra-artifact-manifest.json"
    )
    by_phase = {
        str(item["phase_id"]): str(item["sha256"])
        for item in manifest["artifacts"]
    }
    _write_recovery_chain(
        layout,
        through_phase="U11",
        output_overrides={
            "U3": (by_phase["U3"],),
            "U9": (by_phase["U9"],),
            "U10": (by_phase["U10"],),
            "U11": (by_phase["U11"],),
        },
    )
    statuses = status_module.RunStatusStore(layout)
    created = statuses.create(STAMP - timedelta(minutes=2))
    statuses.transition(
        created,
        "running",
        STAMP - timedelta(minutes=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    repair.commit_repair_plan(layout, attempt_id="VALIDATION-1", plan=plan)
    real_sync_events = recovery._sync_events

    def crash_before_event(*args, **kwargs):
        raise RuntimeError("injected before invalidation event")

    monkeypatch.setattr(recovery, "_sync_events", crash_before_event)
    with pytest.raises(RuntimeError, match="before invalidation"):
        repair.apply_repair_plan(
            layout,
            plan=plan,
            now=STAMP + timedelta(minutes=2),
        )
    monkeypatch.setattr(recovery, "_sync_events", real_sync_events)

    recovered = repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=3),
    )

    assert recovered["active_generation"] == 1
    assert recovered["reopened_phase"] == "U10"


def test_apply_repair_plan_rejects_a_drifted_current_validation_projection(
    tmp_path: Path,
) -> None:
    repair, layout, _, plan = _prepare_u11_repair(tmp_path)
    jsonio = _runtime_module("jsonio")
    current_path = layout.validation_current_dir / REPORT_NAME
    drifted = jsonio.load_json_object(current_path)
    drifted["validated_at"] = (
        STAMP + timedelta(seconds=1)
    ).isoformat().replace("+00:00", "Z")
    jsonio.atomic_write_json(current_path, _seal(drifted))

    with pytest.raises(
        repair.StaleValidationAttemptError,
        match="current|report|attempt",
    ):
        repair.apply_repair_plan(
            layout,
            plan=plan,
            now=STAMP + timedelta(minutes=2),
        )


def test_non_owner_cannot_commit_repair_plan_while_writer_is_live(
    tmp_path: Path,
) -> None:
    repair = load_runtime()
    locks = _runtime_module("locks")
    layout, _ = _prepare_attempt(tmp_path)
    plan = repair.build_repair_plan(
        layout,
        attempt_id="VALIDATION-1",
        attempt_number=1,
        now=STAMP + timedelta(minutes=1),
    )
    lease = locks.acquire_run_lease(
        layout,
        STAMP + timedelta(minutes=2),
        timedelta(minutes=5),
    )
    try:
        with pytest.raises(locks.LeaseConflictError):
            repair.commit_repair_plan(
                layout,
                attempt_id="VALIDATION-1",
                plan=plan,
            )
    finally:
        locks.release_run_lease(layout, lease)

    assert not (
        layout.validation_attempts_dir
        / "VALIDATION-1"
        / "ultra-repair-plan.json"
    ).exists()


def test_cancel_after_repair_invalidation_converges_active_generation(
    tmp_path: Path,
) -> None:
    repair, layout, _, plan = _prepare_u11_repair(tmp_path)
    recovery = _runtime_module("recovery")
    jsonio = _runtime_module("jsonio")
    status_module = _runtime_module("status")

    repair.apply_repair_plan(
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2),
    )
    (layout.recovery_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    cancelled = recovery.cancel_run(
        layout,
        reason="operator cancellation after repair",
        now=STAMP + timedelta(minutes=3),
    )
    repeated = recovery.cancel_run(
        layout,
        reason="ignored repeated cancellation",
        now=STAMP + timedelta(minutes=4),
    )

    events = [
        jsonio.load_json_object_bytes(row, source="repair cancellation event")
        for row in (layout.recovery_dir / "phase-events.jsonl").read_bytes().splitlines(
            keepends=True
        )
    ]
    terminal = events[-1]
    assert cancelled == repeated == status_module.RunStatusStore(layout).read()
    assert cancelled.status == "cancelled"
    assert cancelled.current_phase == "U11"
    assert cancelled.last_complete_phase == "U10"
    assert terminal["event_type"] == "phase-cancelled"
    assert terminal["phase_id"] == "U11"
    assert terminal["generation"] == 1
    assert sum(event["status"] == "cancelled" for event in events) == 1


def test_cancel_after_repair_snapshot_blocks_all_later_repair_commits(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repair, layout, _, plan = _prepare_u11_repair(tmp_path)
    jsonio = _runtime_module("jsonio")
    locks = _runtime_module("locks")
    status_module = _runtime_module("status")
    event_path = layout.recovery_dir / "phase-events.jsonl"
    before_events = event_path.read_bytes()
    before_status = status_module.RunStatusStore(layout).path.read_bytes()
    real_preserve = repair._preserve_superseded_artifacts

    def preserve_then_cancel(*args, **kwargs):
        result = real_preserve(*args, **kwargs)
        locks.request_cancel(
            layout,
            reason="cancel at repair write boundary",
            now=STAMP + timedelta(minutes=2, seconds=1),
        )
        return result

    monkeypatch.setattr(
        repair,
        "_preserve_superseded_artifacts",
        preserve_then_cancel,
    )
    lease = locks.acquire_run_lease(
        layout,
        STAMP + timedelta(minutes=2),
        timedelta(minutes=5),
    )
    try:
        with pytest.raises(locks.CancelledRunError, match="cancel"):
            repair.apply_repair_plan(
                layout,
                plan=plan,
                now=STAMP + timedelta(minutes=2, seconds=2),
                lease=lease,
            )
    finally:
        locks.release_run_lease(layout, lease)

    assert event_path.read_bytes() == before_events
    assert status_module.RunStatusStore(layout).path.read_bytes() == before_status
    assert not (
        layout.recovery_dir
        / "repair-attempts"
        / "VALIDATION-1"
        / "repair-application.json"
    ).exists()
    assert locks.load_cancel_intent(layout) is not None
    assert jsonio.load_json_object(
        layout.recovery_dir
        / "repair-attempts"
        / "VALIDATION-1"
        / "superseded-snapshot.json"
    )["repair_attempt_id"] == "VALIDATION-1"


def test_repair_invalidation_commit_serializes_with_cancel_intent_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repair, layout, _, plan = _prepare_u11_repair(tmp_path)
    recovery = _runtime_module("recovery")
    locks = _runtime_module("locks")
    jsonio = _runtime_module("jsonio")
    invalidation_commit_started = Event()
    allow_invalidation_commit = Event()
    cancel_started = Event()
    cancel_finished = Event()
    original_sync_events = recovery._sync_events

    def pause_invalidation_commit(path: Path, events) -> None:
        if events and events[-1].get("status") == "invalidated":
            invalidation_commit_started.set()
            if not allow_invalidation_commit.wait(timeout=5):
                raise TimeoutError("test did not release repair invalidation commit")
        original_sync_events(path, events)

    def request_cancel():
        cancel_started.set()
        try:
            return locks.request_cancel(
                layout,
                reason="cancel at repair invalidation commit boundary",
                now=STAMP + timedelta(minutes=2, seconds=1),
            )
        finally:
            cancel_finished.set()

    monkeypatch.setattr(recovery, "_sync_events", pause_invalidation_commit)
    lease = locks.acquire_run_lease(
        layout,
        STAMP + timedelta(minutes=2),
        timedelta(minutes=5),
    )
    executor = ThreadPoolExecutor(max_workers=2)
    repair_future = executor.submit(
        repair.apply_repair_plan,
        layout,
        plan=plan,
        now=STAMP + timedelta(minutes=2, seconds=2),
        lease=lease,
    )
    cancel_future = None
    try:
        assert invalidation_commit_started.wait(timeout=2)
        cancel_future = executor.submit(request_cancel)
        assert cancel_started.wait(timeout=2)
        assert not cancel_finished.wait(timeout=0.3), (
            "cancel intent crossed repair invalidation commit in progress"
        )
    finally:
        allow_invalidation_commit.set()
        executor.shutdown(wait=True)
        locks.release_run_lease(layout, lease)

    try:
        repair_future.result()
    except locks.CancelledRunError:
        pass
    assert cancel_future is not None
    assert cancel_future.result().run_id == layout.run_dir.name
    events = [
        jsonio.load_json_object_bytes(row, source="repair invalidation race event")
        for row in (layout.recovery_dir / "phase-events.jsonl").read_bytes().splitlines(
            keepends=True
        )
    ]
    assert events[-1]["status"] == "invalidated"
    assert locks.load_cancel_intent(layout) is not None
