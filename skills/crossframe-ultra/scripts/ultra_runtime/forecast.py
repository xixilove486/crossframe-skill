from __future__ import annotations

from collections.abc import Mapping
import copy
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .jsonio import (
    append_jsonl_locked,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .schemas import (
    build_schema_registry,
    compute_artifact_content_sha256,
    validate_phase_artifact,
)


__all__ = (
    "validate_forecast",
    "load_original_forecast",
    "append_resolution",
)


_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CALIBRATION_FIELDS = frozenset(
    {
        "probability",
        "reference_class",
        "calibration_basis",
        "probability_admissible",
    }
)
_DIRECTION_OPERATORS = {
    "increase": frozenset({"gt", "gte"}),
    "decrease": frozenset({"lt", "lte"}),
    "stable": frozenset({"eq", "within"}),
    "threshold-crossing": frozenset({"gt", "gte", "lt", "lte", "neq"}),
    "branch-dependent": frozenset({"branch-equals"}),
}
_FORECAST_RECORD_VALIDATOR = Draft202012Validator(
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": (
            "https://crossframe.local/schemas/"
            "ultra-forecast-ledger.schema.json#/$defs/forecast"
        ),
    },
    registry=build_schema_registry(),
    format_checker=FormatChecker(),
)


class ForecastError(ValueError):
    """Raised when a forecast or resolution changes a frozen U9 contract."""


class UncalibratedProbabilityError(ForecastError):
    """Raised when a numeric probability lacks an admissible calibration basis."""


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ForecastError(f"{label} has a non-native JSON object key")
            _require_native_json(item, label=label)
        return
    if value_type is list:
        for item in value:
            _require_native_json(item, label=label)
        return
    if value_type in {str, int, float, bool, type(None)}:
        return
    raise ForecastError(f"{label} contains a non-native JSON value")


def _snapshot(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ForecastError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ForecastError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ForecastError(f"value is not bounded canonical JSON: {error}") from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ForecastError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ForecastError(f"invalid RFC 3339 timestamp {value!r}") from error
    if parsed.tzinfo is None:
        raise ForecastError("forecast timestamp must include an explicit timezone")
    return parsed


def _validate_probability_admission(forecast: Mapping[str, Any]) -> None:
    present = _CALIBRATION_FIELDS.intersection(forecast)
    if not present:
        return
    probability = forecast.get("probability")
    reference_class = forecast.get("reference_class")
    calibration_basis = forecast.get("calibration_basis")
    admissible = forecast.get("probability_admissible")
    if (
        type(probability) not in {int, float}
        or not 0 <= probability <= 1
        or type(reference_class) is not str
        or not reference_class.strip()
        or type(calibration_basis) is not str
        or not calibration_basis.strip()
        or admissible is not True
    ):
        raise UncalibratedProbabilityError(
            "numeric probability requires a reference class, calibration basis, and admissibility result"
        )


def _validate_direction_contract(forecast: Mapping[str, Any]) -> None:
    direction = forecast["direction"]
    predicate = forecast["resolution_predicate"]
    operator = predicate["operator"]
    if operator not in _DIRECTION_OPERATORS[direction]:
        raise ForecastError(
            f"forecast direction {direction!r} is incompatible with operator {operator!r}"
        )
    if direction == "branch-dependent":
        if predicate["target_value"] not in forecast["branch_refs"]:
            raise ForecastError(
                "branch-equals target must resolve one of the forecast branch_refs"
            )
        return

    baseline = predicate["baseline_value"]
    target = predicate["target_value"]
    if direction == "increase" and not target > baseline:
        raise ForecastError("increase direction requires target greater than baseline")
    if direction == "decrease" and not target < baseline:
        raise ForecastError("decrease direction requires target less than baseline")
    if direction == "stable" and target != baseline:
        raise ForecastError("stable direction requires target equal to baseline")
    if (
        direction == "threshold-crossing"
        and operator != "neq"
        and target == baseline
    ):
        raise ForecastError(
            "threshold crossing requires a target distinct from the baseline"
        )


def _validated_forecast_record(forecast: Mapping[str, object]) -> dict[str, Any]:
    snapshot = _snapshot(forecast, label="frozen original forecast")
    _validate_probability_admission(snapshot)
    try:
        _FORECAST_RECORD_VALIDATOR.validate(snapshot)
    except ValidationError as error:
        raise ForecastError(f"invalid frozen original forecast: {error.message}") from error
    cutoff = _timestamp(snapshot["evidence_cutoff"])
    start = _timestamp(snapshot["window_start"])
    end = _timestamp(snapshot["window_end"])
    if not cutoff <= start <= end:
        raise ForecastError(
            "forecast requires evidence_cutoff <= window_start <= window_end"
        )
    _validate_direction_contract(snapshot)
    return snapshot


def validate_forecast(forecast: Mapping[str, object]) -> None:
    _validated_forecast_record(forecast)


def _validate_ledger_records(
    ledger: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    forecasts = tuple(_validated_forecast_record(item) for item in ledger["forecasts"])
    forecast_ids = [item["forecast_id"] for item in forecasts]
    indicator_ids = [item["indicator_id"] for item in forecasts]
    if len(forecast_ids) != len(set(forecast_ids)):
        raise ForecastError("forecast IDs must be unique within the immutable ledger")
    if len(indicator_ids) != len(set(indicator_ids)):
        raise ForecastError("indicator IDs must be unique within the immutable ledger")
    if set(forecast_ids).intersection(indicator_ids):
        raise ForecastError("forecast and indicator identity roles must remain distinct")
    return forecasts


def _validate_forecast_ledger(
    ledger: Mapping[str, object],
    *,
    verdict: Mapping[str, object],
    evidence: Mapping[str, object],
    lineage: Mapping[str, object],
    expected_verdict_artifact_sha256: str,
) -> dict[str, Any]:
    from .judgment import _validated_public_verdict_inputs

    verdict_snapshot, evidence_snapshot, lineage_snapshot = (
        _validated_public_verdict_inputs(verdict, evidence, lineage)
    )
    expected_verdict_hash = _require_sha256(
        expected_verdict_artifact_sha256,
        label="expected sealed U9 verdict artifact hash",
    )
    if _canonical_sha256(verdict_snapshot) != expected_verdict_hash:
        raise ForecastError(
            "sealed verdict full artifact hash differs from external authority"
        )
    try:
        ledger_snapshot = validate_phase_artifact(
            "ultra-forecast-ledger.schema.json",
            _snapshot(ledger, label="U9 immutable forecast ledger"),
            expected_schema_id="crossframe.ultra.v82.forecast-ledger",
            expected_run_id=verdict_snapshot["run_id"],
            expected_version_binding=verdict_snapshot["version_binding"],
            expected_phase_id="U9",
        )
    except (ValidationError, TypeError, ValueError) as error:
        raise ForecastError(f"invalid U9 immutable forecast ledger: {error}") from error

    authority_hashes = (
        _canonical_sha256(evidence_snapshot),
        _canonical_sha256(lineage_snapshot),
        expected_verdict_hash,
    )
    if len(set(authority_hashes)) != 3:
        raise ForecastError("forecast U3/U7/U9 authority roles require distinct hashes")
    if (
        ledger_snapshot["evidence_ledger_artifact_sha256"],
        ledger_snapshot["recursive_lineage_artifact_sha256"],
        ledger_snapshot["verdict_artifact_sha256"],
    ) != authority_hashes:
        raise ForecastError(
            "forecast ledger authority fields do not match sealed evidence, lineage, and verdict"
        )

    forecasts = _validate_ledger_records(ledger_snapshot)
    prediction_id = next(
        item["verdict_id"]
        for item in verdict_snapshot["five_verdicts"]
        if item["kind"] == "prediction"
    )
    branch_ids = {item["branch_id"] for item in lineage_snapshot["branches"]}
    node_ids = {item["node_id"] for item in lineage_snapshot["nodes"]}
    upstream_ids = branch_ids | node_ids | {
        item["verdict_id"] for item in verdict_snapshot["five_verdicts"]
    }
    for forecast in forecasts:
        if forecast["prediction_verdict_id"] != prediction_id:
            raise ForecastError(
                "forecast prediction_verdict_id must resolve the prediction lock"
            )
        if not set(forecast["branch_refs"]).issubset(branch_ids):
            raise ForecastError("forecast branch_refs do not resolve the sealed U7 lineage")
        if not set(forecast["node_refs"]).issubset(node_ids):
            raise ForecastError("forecast node_refs do not resolve the sealed U7 lineage")
        if forecast["forecast_id"] in upstream_ids or forecast["indicator_id"] in upstream_ids:
            raise ForecastError(
                "forecast and indicator identities must remain distinct from upstream identity roles"
            )
    return ledger_snapshot


def _seal_forecast_ledger(
    ledger: Mapping[str, object],
    **authority: object,
) -> dict[str, Any]:
    snapshot = _snapshot(ledger, label="unsealed U9 forecast ledger")
    if "content_sha256" in snapshot:
        raise ForecastError(
            "U9 producer accepts an unsealed forecast ledger without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_forecast_ledger(snapshot, **authority)


def _load_ledger(ledger_path: Path) -> dict[str, Any]:
    if not isinstance(ledger_path, Path):
        raise TypeError("ledger_path must be a pathlib.Path")
    try:
        ledger = load_json_object(ledger_path)
    except (OSError, TypeError, ValueError) as error:
        raise ForecastError(f"cannot load immutable forecast ledger: {error}") from error
    run_id = ledger.get("run_id")
    binding = ledger.get("version_binding")
    if type(run_id) is not str or not isinstance(binding, Mapping):
        raise ForecastError("forecast ledger must expose run and version authority")
    try:
        validated = validate_phase_artifact(
            "ultra-forecast-ledger.schema.json",
            ledger,
            expected_schema_id="crossframe.ultra.v82.forecast-ledger",
            expected_run_id=run_id,
            expected_version_binding=binding,
            expected_phase_id="U9",
        )
    except (ValidationError, TypeError, ValueError) as error:
        raise ForecastError(f"invalid immutable forecast ledger: {error}") from error
    authority_hashes = (
        validated["evidence_ledger_artifact_sha256"],
        validated["recursive_lineage_artifact_sha256"],
        validated["verdict_artifact_sha256"],
    )
    if len(set(authority_hashes)) != 3:
        raise ForecastError("forecast ledger authority roles require distinct hashes")
    _validate_ledger_records(validated)
    return validated


def load_original_forecast(ledger_path: Path, forecast_id: str) -> dict[str, object]:
    if type(forecast_id) is not str or not forecast_id:
        raise ForecastError("forecast_id must be explicit")
    ledger = _load_ledger(ledger_path)
    matches = [
        item for item in ledger["forecasts"] if item["forecast_id"] == forecast_id
    ]
    if len(matches) != 1:
        raise ForecastError(
            "forecast_id must resolve exactly one immutable original record"
        )
    return copy.deepcopy(matches[0])


def _predicate_result(forecast: Mapping[str, Any], observed: object) -> bool:
    predicate = forecast["resolution_predicate"]
    operator = predicate["operator"]
    target = predicate["target_value"]
    tolerance = predicate["tolerance"]
    if operator == "branch-equals":
        if type(observed) is not str:
            raise ForecastError("branch-dependent forecast requires a branch identifier")
        return observed == target
    if type(observed) not in {int, float}:
        raise ForecastError("numeric forecast requires a numeric observed value")
    if operator == "gt":
        return observed > target
    if operator == "gte":
        return observed >= target
    if operator == "lt":
        return observed < target
    if operator == "lte":
        return observed <= target
    if operator == "eq":
        return abs(observed - target) <= tolerance
    if operator == "neq":
        return abs(observed - target) > tolerance
    if operator == "within":
        return abs(observed - target) <= tolerance
    raise ForecastError(f"unsupported frozen resolution operator {operator!r}")


def _expected_resolution_fields(
    forecast: Mapping[str, Any], resolution: Mapping[str, Any]
) -> dict[str, object]:
    observation_time = _timestamp(resolution["observation_time"])
    resolution_time = _timestamp(resolution["resolution_time"])
    if resolution_time < observation_time:
        raise ForecastError("resolution_time cannot precede observation_time")
    covered = (
        _timestamp(forecast["window_start"])
        <= observation_time
        <= _timestamp(forecast["window_end"])
    )
    observed = resolution["observed_value"]
    indicator_resolved = observed is not None
    direction_correct: bool | None
    if indicator_resolved:
        direction_correct = _predicate_result(forecast, observed)
        if direction_correct:
            outcome = "correct" if covered else "partial"
        else:
            outcome = "incorrect"
    else:
        direction_correct = None
        outcome = "indeterminate"

    probability_admissible = (
        "probability" in forecast and forecast.get("probability_admissible") is True
    )
    if probability_admissible and outcome != "indeterminate":
        probability = forecast["probability"]
        binary_outcome = 1 if outcome == "correct" else 0
        brier_inputs: dict[str, object] | None = {
            "probability": probability,
            "binary_outcome": binary_outcome,
        }
        brier_score: float | None = (probability - binary_outcome) ** 2
    else:
        brier_inputs = None
        brier_score = None
    return {
        "indicator_resolved": indicator_resolved,
        "direction_correct": direction_correct,
        "time_window_covered": covered,
        "outcome": outcome,
        "original_probability_admissible": probability_admissible,
        "brier_inputs": brier_inputs,
        "brier_score": brier_score,
    }


def _validate_resolution_event(
    ledger: Mapping[str, Any],
    forecast: Mapping[str, Any],
    resolution: Mapping[str, object],
) -> dict[str, Any]:
    try:
        snapshot = validate_phase_artifact(
            "ultra-forecast-resolution-event.schema.json",
            _snapshot(resolution, label="U9 forecast resolution event"),
            expected_schema_id="crossframe.ultra.v82.forecast-resolution-event",
            expected_run_id=ledger["run_id"],
            expected_version_binding=ledger["version_binding"],
            expected_phase_id="U9",
        )
    except (ValidationError, TypeError, ValueError) as error:
        raise ForecastError(f"invalid U9 forecast resolution event: {error}") from error
    if snapshot["forecast_ledger_artifact_sha256"] != _canonical_sha256(ledger):
        raise ForecastError("resolution event does not bind the immutable forecast ledger")
    if snapshot["forecast_id"] != forecast["forecast_id"]:
        raise ForecastError("resolution event forecast_id does not match the original")
    if snapshot["indicator_id"] != forecast["indicator_id"]:
        raise ForecastError("resolution event indicator_id does not match the original")
    if snapshot["original_forecast_record_sha256"] != _canonical_sha256(forecast):
        raise ForecastError("resolution event does not bind the exact original record")

    expected = _expected_resolution_fields(forecast, snapshot)
    for field in (
        "indicator_resolved",
        "direction_correct",
        "time_window_covered",
        "outcome",
        "original_probability_admissible",
        "brier_inputs",
    ):
        if snapshot[field] != expected[field]:
            raise ForecastError(
                f"resolution caller-declared {field} differs from recomputed result"
            )
    actual_score = snapshot["brier_score"]
    expected_score = expected["brier_score"]
    if expected_score is None:
        if actual_score is not None:
            raise ForecastError("unscored resolution cannot carry a Brier score")
    elif type(actual_score) not in {int, float} or not math.isclose(
        actual_score, expected_score, rel_tol=0.0, abs_tol=1e-12
    ):
        raise ForecastError("resolution Brier score differs from recomputed result")
    return snapshot


def _resolution_event_ids(sidecar: Path) -> set[str]:
    if not sidecar.exists():
        return set()
    try:
        lines = sidecar.read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in lines if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ForecastError(f"cannot read resolution-event sidecar: {error}") from error
    if any(not isinstance(entry, dict) for entry in entries):
        raise ForecastError("resolution-event sidecar contains a non-object entry")
    identifiers = [entry.get("resolution_event_id") for entry in entries]
    if any(type(identifier) is not str for identifier in identifiers):
        raise ForecastError("resolution-event sidecar contains an invalid event identity")
    if len(set(identifiers)) != len(identifiers):
        raise ForecastError("resolution-event sidecar already contains duplicate IDs")
    return set(identifiers)


def append_resolution(
    ledger_path: Path, resolution: Mapping[str, object]
) -> None:
    ledger = _load_ledger(ledger_path)
    resolution_snapshot = _snapshot(resolution, label="U9 forecast resolution event")
    forecast_id = resolution_snapshot.get("forecast_id")
    if type(forecast_id) is not str or not forecast_id:
        raise ForecastError("resolution event forecast_id must be explicit")
    matches = [
        item for item in ledger["forecasts"] if item["forecast_id"] == forecast_id
    ]
    if len(matches) != 1:
        raise ForecastError(
            "resolution event must resolve exactly one immutable original forecast"
        )
    validated = _validate_resolution_event(ledger, matches[0], resolution_snapshot)
    sidecar = ledger_path.with_name(f"{ledger_path.stem}.resolution-events.jsonl")
    if validated["resolution_event_id"] in _resolution_event_ids(sidecar):
        raise ForecastError("resolution_event_id has already been appended")
    append_jsonl_locked(sidecar, validated)
