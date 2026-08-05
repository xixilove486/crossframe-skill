from __future__ import annotations

import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from tests.test_ultra_claim_mechanism import make_evidence_ledger
from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.locks import Lease, LeaseOwnershipError, acquire_run_lease
from ultra_runtime.paths import RootPolicy, RunLayout, RunMode, build_run_layout
from ultra_runtime.schemas import compute_artifact_content_sha256


PUBLIC_FUNCTIONS = (
    "validate_forecast",
    "load_original_forecast",
    "append_resolution",
)
RUN_ID = "20260804T000000Z-0123456789ab"
SIBLING_RUN_ID = "20260804T000001Z-abcdefabcdef"


def load_fixture(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def rehash_artifact(value: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(value))
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return snapshot


def bind_ledger_to_run(ledger: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(ledger))
    snapshot["run_id"] = RUN_ID
    return rehash_artifact(snapshot)


def bind_resolution_to_ledger(
    resolution: Mapping[str, object], ledger: Mapping[str, object]
) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(resolution))
    snapshot["run_id"] = RUN_ID
    snapshot["forecast_ledger_artifact_sha256"] = canonical_sha256(ledger)
    return rehash_artifact(snapshot)


def prepare_resolution_run(
    tmp_path: Path,
    ledger: Mapping[str, object],
    *,
    with_lease: bool = True,
) -> tuple[RunLayout, Lease | None, Path, Path]:
    layout = build_run_layout(
        RunMode.TEST,
        RUN_ID,
        RootPolicy(tmp_path / "production", tmp_path / "test"),
    )
    ledger_path = (
        layout.artifacts_dir
        / "U09-U10-verdict"
        / "U09-forecast-ledger.json"
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_bytes(canonical_json_bytes(ledger))
    lease = (
        acquire_run_lease(
            layout,
            datetime(2026, 8, 4, tzinfo=timezone.utc),
            timedelta(minutes=5),
        )
        if with_lease
        else None
    )
    sidecar = ledger_path.with_name(
        "U09-forecast-ledger.resolution-events.jsonl"
    )
    return layout, lease, ledger_path, sidecar


def runtime():
    return importlib.import_module("ultra_runtime.forecast")


def forecast_by_id(
    ledger: Mapping[str, Any], forecast_id: str = "FORECAST-REVIEW-INCREASE"
) -> dict[str, Any]:
    return next(
        copy.deepcopy(item)
        for item in ledger["forecasts"]
        if item["forecast_id"] == forecast_id
    )


def validate_ledger(
    ledger: Mapping[str, object],
    **overrides: object,
) -> dict[str, Any]:
    verdict = load_fixture("verdict-valid.json")
    evidence = make_evidence_ledger()
    lineage = load_fixture("recursive-lineage-valid.json")
    kwargs: dict[str, object] = {
        "verdict": verdict,
        "evidence": evidence,
        "lineage": lineage,
        "expected_verdict_artifact_sha256": canonical_sha256(verdict),
    }
    kwargs.update(overrides)
    return runtime()._validate_forecast_ledger(ledger, **kwargs)


def test_forecast_public_surface_and_signatures_are_exact() -> None:
    module = runtime()
    assert module.__all__ == PUBLIC_FUNCTIONS
    assert tuple(inspect.signature(module.validate_forecast).parameters) == (
        "forecast",
    )
    assert tuple(inspect.signature(module.load_original_forecast).parameters) == (
        "ledger_path",
        "forecast_id",
    )
    assert tuple(inspect.signature(module.append_resolution).parameters) == (
        "layout",
        "resolution",
        "lease",
    )
    assert (
        inspect.signature(module.append_resolution).parameters["lease"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )


def test_each_frozen_original_forecast_validates_without_mutation() -> None:
    ledger = load_fixture("forecast-valid.json")
    originals = copy.deepcopy(ledger["forecasts"])
    for forecast in ledger["forecasts"]:
        assert runtime().validate_forecast(forecast) is None
    assert ledger["forecasts"] == originals


def test_ledger_is_sealed_only_after_the_bound_verdict() -> None:
    ledger = load_fixture("forecast-valid.json")
    assert validate_ledger(ledger) == ledger

    unsealed = copy.deepcopy(ledger)
    unsealed.pop("content_sha256")
    verdict = load_fixture("verdict-valid.json")
    evidence = make_evidence_ledger()
    lineage = load_fixture("recursive-lineage-valid.json")
    sealed = runtime()._seal_forecast_ledger(
        unsealed,
        verdict=verdict,
        evidence=evidence,
        lineage=lineage,
        expected_verdict_artifact_sha256=canonical_sha256(verdict),
    )
    assert sealed == ledger


def test_ledger_rejects_stale_or_self_selected_verdict_authority() -> None:
    ledger = load_fixture("forecast-valid.json")
    with pytest.raises(ValueError):
        validate_ledger(
            ledger,
            expected_verdict_artifact_sha256="f" * 64,
        )

    ledger["verdict_artifact_sha256"] = "e" * 64
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)


def test_prediction_lock_branch_and_node_refs_must_resolve() -> None:
    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][0]["prediction_verdict_id"] = "VERDICT-FACT"
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)

    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][0]["branch_refs"] = ["BRANCH-NOT-SEALED"]
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)

    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][0]["node_refs"] = ["NODE-NOT-SEALED"]
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)


def test_forecast_ids_and_indicator_ids_are_unique_in_a_ledger() -> None:
    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][1]["forecast_id"] = ledger["forecasts"][0]["forecast_id"]
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)

    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][1]["indicator_id"] = ledger["forecasts"][0][
        "indicator_id"
    ]
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)


@pytest.mark.parametrize(
    ("direction", "operator", "baseline", "target"),
    (
        ("increase", "lt", 8, 7),
        ("decrease", "gt", 8, 10),
        ("stable", "gt", 8, 10),
        ("threshold-crossing", "within", 8, 8),
    ),
)
def test_direction_and_structural_predicate_must_be_compatible(
    direction: str,
    operator: str,
    baseline: int,
    target: int,
) -> None:
    forecast = forecast_by_id(load_fixture("forecast-valid.json"))
    forecast["direction"] = direction
    forecast["resolution_predicate"] = {
        "operator": operator,
        "baseline_value": baseline,
        "target_value": target,
        "tolerance": 0,
    }
    with pytest.raises(ValueError):
        runtime().validate_forecast(forecast)


def test_branch_predicate_target_must_belong_to_branch_refs() -> None:
    forecast = forecast_by_id(
        load_fixture("forecast-valid.json"), "FORECAST-BRANCH-SELECTION"
    )
    forecast["resolution_predicate"]["target_value"] = "BRANCH-NOT-SEALED"
    with pytest.raises(ValueError):
        runtime().validate_forecast(forecast)


@pytest.mark.parametrize(
    ("cutoff", "start", "end"),
    (
        (
            "2026-08-04T00:00:00Z",
            "2026-08-03T00:00:00Z",
            "2026-11-02T00:00:00Z",
        ),
        (
            "2026-08-02T00:00:00Z",
            "2026-11-03T00:00:00Z",
            "2026-11-02T00:00:00Z",
        ),
    ),
)
def test_evidence_cutoff_precedes_the_ordered_forecast_window(
    cutoff: str, start: str, end: str
) -> None:
    forecast = forecast_by_id(load_fixture("forecast-valid.json"))
    forecast["evidence_cutoff"] = cutoff
    forecast["window_start"] = start
    forecast["window_end"] = end
    with pytest.raises(ValueError):
        runtime().validate_forecast(forecast)


@pytest.mark.parametrize(
    "mutation",
    (
        {"probability": 0.73, "calibration_basis": None},
        {"probability": 0.73, "reference_class": None},
        {"probability": 0.73, "probability_admissible": False},
    ),
)
def test_probability_without_admissible_calibration_is_rejected(
    mutation: Mapping[str, object],
) -> None:
    forecast = forecast_by_id(load_fixture("forecast-valid.json"))
    forecast.update(mutation)
    with pytest.raises(runtime().UncalibratedProbabilityError):
        runtime().validate_forecast(forecast)


def test_original_ledger_rejects_nested_or_mutable_resolution_state() -> None:
    ledger = load_fixture("forecast-valid.json")
    ledger["forecasts"][0]["resolution"] = {
        "outcome": "correct",
    }
    ledger = rehash_artifact(ledger)
    with pytest.raises(ValueError):
        validate_ledger(ledger)


def test_multiple_originals_are_loaded_uniquely_by_forecast_id(tmp_path: Path) -> None:
    ledger = load_fixture("forecast-valid.json")
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))

    first = runtime().load_original_forecast(
        ledger_path, "FORECAST-REVIEW-INCREASE"
    )
    second = runtime().load_original_forecast(
        ledger_path, "FORECAST-BRANCH-SELECTION"
    )
    assert first["forecast_id"] != second["forecast_id"]
    with pytest.raises(ValueError):
        runtime().load_original_forecast(ledger_path, "FORECAST-NOT-PRESENT")


def test_resolution_appends_to_fixed_sidecar_without_rewriting_prediction(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, sidecar = prepare_resolution_run(tmp_path, ledger)
    original_bytes = canonical_json_bytes(ledger)

    runtime().append_resolution(layout, resolution, lease=lease)

    assert ledger_path.read_bytes() == original_bytes
    assert sidecar.exists()
    assert not ledger_path.with_name(
        "U09-forecast-ledger.json.resolution-events.jsonl"
    ).exists()
    assert json.loads(sidecar.read_text(encoding="utf-8")) == resolution
    assert canonical_json_bytes(
        runtime().load_original_forecast(
            ledger_path, resolution["forecast_id"]
        )
    ) == canonical_json_bytes(
        forecast_by_id(ledger, resolution["forecast_id"])
    )


def test_resolution_rejects_an_absolute_path_outside_the_selected_root(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, legitimate_sidecar = prepare_resolution_run(
        tmp_path, ledger
    )
    outside_artifacts = tmp_path / "outside-controlled"
    outside_ledger = (
        outside_artifacts
        / "U09-U10-verdict"
        / "U09-forecast-ledger.json"
    )
    outside_ledger.parent.mkdir(parents=True)
    outside_ledger.write_bytes(canonical_json_bytes(ledger))
    sentinel = outside_artifacts / "sentinel.bin"
    sentinel.write_bytes(b"outside-sentinel")
    outside_sidecar = outside_ledger.with_name(
        "U09-forecast-ledger.resolution-events.jsonl"
    )
    tampered = replace(layout, artifacts_dir=outside_artifacts)

    with pytest.raises(ValueError):
        runtime().append_resolution(tampered, resolution, lease=lease)

    assert ledger_path.read_bytes() == canonical_json_bytes(ledger)
    assert sentinel.read_bytes() == b"outside-sentinel"
    assert not outside_sidecar.exists()
    assert not legitimate_sidecar.exists()


def test_resolution_rejects_a_sibling_run_artifact_directory(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, legitimate_sidecar = prepare_resolution_run(
        tmp_path, ledger
    )
    sibling = build_run_layout(
        RunMode.TEST,
        SIBLING_RUN_ID,
        RootPolicy(tmp_path / "production", tmp_path / "test"),
    )
    sibling_ledger = (
        sibling.artifacts_dir
        / "U09-U10-verdict"
        / "U09-forecast-ledger.json"
    )
    sibling_ledger.parent.mkdir(parents=True, exist_ok=True)
    sibling_ledger.write_bytes(canonical_json_bytes(ledger))
    sibling_sentinel = sibling.run_dir / "sentinel.bin"
    sibling_sentinel.write_bytes(b"sibling-sentinel")
    sibling_sidecar = sibling_ledger.with_name(
        "U09-forecast-ledger.resolution-events.jsonl"
    )
    tampered = replace(layout, artifacts_dir=sibling.artifacts_dir)

    with pytest.raises(ValueError):
        runtime().append_resolution(tampered, resolution, lease=lease)

    assert ledger_path.read_bytes() == canonical_json_bytes(ledger)
    assert sibling_sentinel.read_bytes() == b"sibling-sentinel"
    assert not sibling_sidecar.exists()
    assert not legitimate_sidecar.exists()


def test_resolution_rejects_a_noncanonical_phase_artifact_slot(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, legitimate_sidecar = prepare_resolution_run(
        tmp_path, ledger
    )
    wrong_phase_artifacts = layout.artifacts_dir / "U06-U08-inference"
    wrong_phase_ledger = (
        wrong_phase_artifacts
        / "U09-U10-verdict"
        / "U09-forecast-ledger.json"
    )
    wrong_phase_ledger.parent.mkdir(parents=True, exist_ok=True)
    wrong_phase_ledger.write_bytes(canonical_json_bytes(ledger))
    sentinel = wrong_phase_artifacts / "sentinel.bin"
    sentinel.write_bytes(b"wrong-phase-sentinel")
    wrong_phase_sidecar = wrong_phase_ledger.with_name(
        "U09-forecast-ledger.resolution-events.jsonl"
    )
    tampered = replace(layout, artifacts_dir=wrong_phase_artifacts)

    with pytest.raises(ValueError):
        runtime().append_resolution(tampered, resolution, lease=lease)

    assert ledger_path.read_bytes() == canonical_json_bytes(ledger)
    assert sentinel.read_bytes() == b"wrong-phase-sentinel"
    assert not wrong_phase_sidecar.exists()
    assert not legitimate_sidecar.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_resolution_rejects_a_reparse_redirected_u9_directory(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, legitimate_sidecar = prepare_resolution_run(
        tmp_path, ledger
    )
    verdict_dir = ledger_path.parent
    ledger_path.unlink()
    verdict_dir.rmdir()
    outside = tmp_path / "reparse-target"
    outside.mkdir()
    outside_ledger = outside / "U09-forecast-ledger.json"
    outside_ledger.write_bytes(canonical_json_bytes(ledger))
    sentinel = outside / "sentinel.bin"
    sentinel.write_bytes(b"reparse-sentinel")
    outside_sidecar = outside / "U09-forecast-ledger.resolution-events.jsonl"
    linked = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(verdict_dir), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if linked.returncode != 0:
        pytest.skip(f"junction creation unavailable: {linked.stderr or linked.stdout}")

    try:
        with pytest.raises(ValueError):
            runtime().append_resolution(layout, resolution, lease=lease)

        assert sentinel.read_bytes() == b"reparse-sentinel"
        assert not outside_sidecar.exists()
        assert not legitimate_sidecar.exists()
    finally:
        verdict_dir.rmdir()


def test_resolution_requires_an_active_run_lease(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, _, ledger_path, sidecar = prepare_resolution_run(
        tmp_path, ledger, with_lease=False
    )
    original_bytes = ledger_path.read_bytes()

    with pytest.raises(LeaseOwnershipError):
        runtime().append_resolution(layout, resolution, lease=None)

    assert ledger_path.read_bytes() == original_bytes
    assert not sidecar.exists()


def test_resolution_requires_the_matching_lease_owner(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, sidecar = prepare_resolution_run(tmp_path, ledger)
    wrong_lease = replace(lease, owner_nonce="wrong-owner-nonce-000000000000")
    original_bytes = ledger_path.read_bytes()

    with pytest.raises(LeaseOwnershipError):
        runtime().append_resolution(layout, resolution, lease=wrong_lease)

    assert ledger_path.read_bytes() == original_bytes
    assert not sidecar.exists()


def test_resolution_rejects_a_ledger_owned_by_another_run(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    ledger["run_id"] = SIBLING_RUN_ID
    ledger = rehash_artifact(ledger)
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    resolution["run_id"] = SIBLING_RUN_ID
    resolution = rehash_artifact(resolution)
    layout, lease, ledger_path, sidecar = prepare_resolution_run(tmp_path, ledger)
    original_bytes = ledger_path.read_bytes()

    with pytest.raises(ValueError):
        runtime().append_resolution(layout, resolution, lease=lease)

    assert ledger_path.read_bytes() == original_bytes
    assert not sidecar.exists()


def test_resolution_rejects_a_ledger_from_the_wrong_phase(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    ledger["phase_id"] = "U8"
    ledger = rehash_artifact(ledger)
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, ledger_path, sidecar = prepare_resolution_run(tmp_path, ledger)
    original_bytes = ledger_path.read_bytes()

    with pytest.raises(ValueError):
        runtime().append_resolution(layout, resolution, lease=lease)

    assert ledger_path.read_bytes() == original_bytes
    assert not sidecar.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("forecast_ledger_artifact_sha256", "f" * 64),
        ("indicator_id", "INDICATOR-NOT-ORIGINAL"),
        ("original_forecast_record_sha256", "e" * 64),
        ("indicator_resolved", False),
        ("direction_correct", False),
        ("time_window_covered", False),
        ("outcome", "incorrect"),
        ("original_probability_admissible", False),
        ("brier_score", 0.5),
    ),
)
def test_resolution_rejects_every_caller_declared_mismatch(
    tmp_path: Path, field: str, value: object
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    resolution[field] = value
    resolution = rehash_artifact(resolution)
    layout, lease, ledger_path, sidecar = prepare_resolution_run(tmp_path, ledger)
    original_bytes = canonical_json_bytes(ledger)

    with pytest.raises(ValueError):
        runtime().append_resolution(layout, resolution, lease=lease)
    assert ledger_path.read_bytes() == original_bytes
    assert not sidecar.exists()


@pytest.mark.parametrize(
    ("binary_outcome", "score"),
    ((0, 0.0729), (1, 0.5)),
)
def test_brier_inputs_and_score_are_recomputed_from_the_original(
    tmp_path: Path, binary_outcome: int, score: float
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    resolution["brier_inputs"]["binary_outcome"] = binary_outcome
    resolution["brier_score"] = score
    resolution = rehash_artifact(resolution)
    layout, lease, _, _ = prepare_resolution_run(tmp_path, ledger)
    with pytest.raises(ValueError):
        runtime().append_resolution(layout, resolution, lease=lease)


def test_outside_window_correct_direction_is_partial_and_scores_zero_outcome(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution["observation_time"] = "2026-11-03T00:00:00Z"
    resolution["resolution_time"] = "2026-11-04T00:00:00Z"
    resolution["time_window_covered"] = False
    resolution["outcome"] = "partial"
    resolution["brier_inputs"]["binary_outcome"] = 0
    resolution["brier_score"] = 0.5329
    resolution = bind_resolution_to_ledger(resolution, ledger)
    layout, lease, _, sidecar = prepare_resolution_run(tmp_path, ledger)

    runtime().append_resolution(layout, resolution, lease=lease)
    assert json.loads(sidecar.read_text(encoding="utf-8"))["outcome"] == "partial"


def test_unresolved_event_is_indeterminate_and_never_scored(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution["indicator_resolved"] = False
    resolution["direction_correct"] = None
    resolution["outcome"] = "indeterminate"
    resolution["observed_value"] = None
    resolution["brier_inputs"] = None
    resolution["brier_score"] = None
    resolution = bind_resolution_to_ledger(resolution, ledger)
    layout, lease, _, sidecar = prepare_resolution_run(tmp_path, ledger)

    runtime().append_resolution(layout, resolution, lease=lease)
    appended = json.loads(sidecar.read_text(encoding="utf-8"))
    assert appended["outcome"] == "indeterminate"
    assert appended["brier_score"] is None


def test_branch_resolution_uses_the_structural_branch_predicate(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    forecast = forecast_by_id(ledger, "FORECAST-BRANCH-SELECTION")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution.update(
        resolution_event_id="RESOLUTION-BRANCH-1",
        forecast_id=forecast["forecast_id"],
        indicator_id=forecast["indicator_id"],
        original_forecast_record_sha256=canonical_sha256(forecast),
        observed_value="BRANCH-MAIN",
        original_probability_admissible=False,
        brier_inputs=None,
        brier_score=None,
    )
    resolution = bind_resolution_to_ledger(resolution, ledger)
    layout, lease, _, sidecar = prepare_resolution_run(tmp_path, ledger)

    runtime().append_resolution(layout, resolution, lease=lease)
    assert json.loads(sidecar.read_text(encoding="utf-8"))[
        "direction_correct"
    ] is True


def test_duplicate_resolution_event_id_is_not_appended_twice(tmp_path: Path) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, _, sidecar = prepare_resolution_run(tmp_path, ledger)
    runtime().append_resolution(layout, resolution, lease=lease)
    before = sidecar.read_bytes()

    with pytest.raises(ValueError):
        runtime().append_resolution(layout, resolution, lease=lease)
    assert sidecar.read_bytes() == before


def test_two_processes_append_the_same_resolution_id_exactly_once(
    tmp_path: Path,
) -> None:
    ledger = bind_ledger_to_run(load_fixture("forecast-valid.json"))
    resolution = bind_resolution_to_ledger(
        load_fixture("forecast-resolution-event-valid.json"), ledger
    )
    layout, lease, _, sidecar = prepare_resolution_run(tmp_path, ledger)
    sidecar.write_bytes(
        b"".join(
            canonical_json_bytes(
                rehash_artifact(
                    {
                        **resolution,
                        "resolution_event_id": f"RESOLUTION-SEED-{index:05d}",
                    }
                )
            )
            for index in range(5_000)
        )
    )
    resolution_path = tmp_path / "resolution.json"
    resolution_path.write_bytes(canonical_json_bytes(resolution))
    lease_path = tmp_path / "lease.json"
    lease_path.write_text(
        json.dumps(
            {
                "run_id": lease.run_id,
                "owner_pid": lease.owner_pid,
                "owner_nonce": lease.owner_nonce,
                "acquired_at": lease.acquired_at,
                "heartbeat_at": lease.heartbeat_at,
                "expires_at": lease.expires_at,
            }
        ),
        encoding="utf-8",
    )
    gate = tmp_path / "append.gate"
    gate.write_text("blocked", encoding="utf-8")
    ready_paths = [tmp_path / f"worker-{index}.ready" for index in range(2)]
    worker = r"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, sys.argv[1])

from ultra_runtime.forecast import ForecastError, append_resolution
from ultra_runtime.locks import Lease
from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

layout = build_run_layout(
    RunMode.TEST,
    sys.argv[4],
    RootPolicy(Path(sys.argv[2]), Path(sys.argv[3])),
)
lease = Lease(**json.loads(Path(sys.argv[5]).read_text(encoding="utf-8")))
resolution = json.loads(Path(sys.argv[6]).read_text(encoding="utf-8"))
gate = Path(sys.argv[7])
Path(sys.argv[8]).write_text("ready", encoding="utf-8")
deadline = time.monotonic() + 20
while gate.exists():
    if time.monotonic() >= deadline:
        raise TimeoutError("append gate was not released")
    time.sleep(0.01)
try:
    append_resolution(layout, resolution, lease=lease)
except ForecastError as error:
    if "already been appended" not in str(error):
        raise
    print("duplicate")
else:
    print("appended")
"""
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                worker,
                str(RUNTIME_SCRIPTS),
                str(tmp_path / "production"),
                str(tmp_path / "test"),
                RUN_ID,
                str(lease_path),
                str(resolution_path),
                str(gate),
                str(ready_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for ready_path in ready_paths
    ]
    outputs: list[tuple[str, str, int]] = []
    try:
        deadline = time.monotonic() + 20
        while not all(path.exists() for path in ready_paths):
            if any(process.poll() is not None for process in processes):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("subprocesses did not reach the append gate")
            time.sleep(0.01)
        assert all(path.exists() for path in ready_paths)
        gate.unlink()
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            outputs.append((stdout.strip(), stderr.strip(), process.returncode))
    finally:
        gate.unlink(missing_ok=True)
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()

    assert [returncode for _, _, returncode in outputs] == [0, 0], outputs
    assert sorted(stdout for stdout, _, _ in outputs) == ["appended", "duplicate"]
    entries = [
        json.loads(line)
        for line in sidecar.read_text(encoding="utf-8").splitlines()
    ]
    assert sum(
        entry.get("resolution_event_id") == resolution["resolution_event_id"]
        for entry in entries
    ) == 1
