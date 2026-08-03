from __future__ import annotations

import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from tests.test_ultra_claim_mechanism import make_evidence_ledger
from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import compute_artifact_content_sha256


PUBLIC_FUNCTIONS = (
    "validate_forecast",
    "load_original_forecast",
    "append_resolution",
)


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
        "ledger_path",
        "resolution",
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
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    ledger_path = tmp_path / "forecast-ledger.json"
    original_bytes = canonical_json_bytes(ledger)
    ledger_path.write_bytes(original_bytes)

    runtime().append_resolution(ledger_path, resolution)

    assert ledger_path.read_bytes() == original_bytes
    sidecar = ledger_path.with_name("forecast-ledger.resolution-events.jsonl")
    assert sidecar.exists()
    assert not ledger_path.with_name(
        "forecast-ledger.json.resolution-events.jsonl"
    ).exists()
    assert json.loads(sidecar.read_text(encoding="utf-8")) == resolution
    assert canonical_json_bytes(
        runtime().load_original_forecast(
            ledger_path, resolution["forecast_id"]
        )
    ) == canonical_json_bytes(
        forecast_by_id(ledger, resolution["forecast_id"])
    )


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
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution[field] = value
    resolution = rehash_artifact(resolution)
    ledger_path = tmp_path / "forecast-ledger.json"
    original_bytes = canonical_json_bytes(ledger)
    ledger_path.write_bytes(original_bytes)

    with pytest.raises(ValueError):
        runtime().append_resolution(ledger_path, resolution)
    assert ledger_path.read_bytes() == original_bytes
    assert not ledger_path.with_name(
        "forecast-ledger.resolution-events.jsonl"
    ).exists()


@pytest.mark.parametrize(
    ("binary_outcome", "score"),
    ((0, 0.0729), (1, 0.5)),
)
def test_brier_inputs_and_score_are_recomputed_from_the_original(
    tmp_path: Path, binary_outcome: int, score: float
) -> None:
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution["brier_inputs"]["binary_outcome"] = binary_outcome
    resolution["brier_score"] = score
    resolution = rehash_artifact(resolution)
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))
    with pytest.raises(ValueError):
        runtime().append_resolution(ledger_path, resolution)


def test_outside_window_correct_direction_is_partial_and_scores_zero_outcome(
    tmp_path: Path,
) -> None:
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution["observation_time"] = "2026-11-03T00:00:00Z"
    resolution["resolution_time"] = "2026-11-04T00:00:00Z"
    resolution["time_window_covered"] = False
    resolution["outcome"] = "partial"
    resolution["brier_inputs"]["binary_outcome"] = 0
    resolution["brier_score"] = 0.5329
    resolution = rehash_artifact(resolution)
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))

    runtime().append_resolution(ledger_path, resolution)
    sidecar = ledger_path.with_name("forecast-ledger.resolution-events.jsonl")
    assert json.loads(sidecar.read_text(encoding="utf-8"))["outcome"] == "partial"


def test_unresolved_event_is_indeterminate_and_never_scored(tmp_path: Path) -> None:
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    resolution["indicator_resolved"] = False
    resolution["direction_correct"] = None
    resolution["outcome"] = "indeterminate"
    resolution["observed_value"] = None
    resolution["brier_inputs"] = None
    resolution["brier_score"] = None
    resolution = rehash_artifact(resolution)
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))

    runtime().append_resolution(ledger_path, resolution)
    sidecar = ledger_path.with_name("forecast-ledger.resolution-events.jsonl")
    appended = json.loads(sidecar.read_text(encoding="utf-8"))
    assert appended["outcome"] == "indeterminate"
    assert appended["brier_score"] is None


def test_branch_resolution_uses_the_structural_branch_predicate(tmp_path: Path) -> None:
    ledger = load_fixture("forecast-valid.json")
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
    resolution = rehash_artifact(resolution)
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))

    runtime().append_resolution(ledger_path, resolution)
    sidecar = ledger_path.with_name("forecast-ledger.resolution-events.jsonl")
    assert json.loads(sidecar.read_text(encoding="utf-8"))[
        "direction_correct"
    ] is True


def test_duplicate_resolution_event_id_is_not_appended_twice(tmp_path: Path) -> None:
    ledger = load_fixture("forecast-valid.json")
    resolution = load_fixture("forecast-resolution-event-valid.json")
    ledger_path = tmp_path / "forecast-ledger.json"
    ledger_path.write_bytes(canonical_json_bytes(ledger))
    runtime().append_resolution(ledger_path, resolution)
    sidecar = ledger_path.with_name("forecast-ledger.resolution-events.jsonl")
    before = sidecar.read_bytes()

    with pytest.raises(ValueError):
        runtime().append_resolution(ledger_path, resolution)
    assert sidecar.read_bytes() == before
