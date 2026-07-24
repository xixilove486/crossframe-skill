from __future__ import annotations

import copy
import re
from typing import Mapping, Sequence

from .paths import validate_relative_artifact_path
from .schemas import validate_instance
from .state_machine import PHASES, downstream_phases


MACHINE_FAILURE_FIELDS = frozenset(
    {
        "error_type",
        "artifact",
        "affected_phase",
        "downstream_reset",
        "repair_action",
    }
)
_LEGACY_FAILURE_FIELDS = frozenset(
    {
        "failure_code",
        "affected_artifact_paths",
        "affected_phase",
        "evidence",
    }
)
_ERROR_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_LEGACY_ERROR_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


def _normalize_machine_failure(
    failure: Mapping[str, object],
    *,
    index: int,
) -> dict[str, object]:
    if set(failure) != MACHINE_FAILURE_FIELDS:
        raise ValueError(
            f"failure {index} must contain exactly the machine-readable fields "
            f"{sorted(MACHINE_FAILURE_FIELDS)}"
        )
    error_type = failure.get("error_type")
    if not isinstance(error_type, str) or _ERROR_TYPE_RE.fullmatch(error_type) is None:
        raise ValueError(f"failure {index}.error_type is not a stable identifier")
    artifact = validate_relative_artifact_path(failure.get("artifact"))
    affected_phase = failure.get("affected_phase")
    if affected_phase not in PHASES:
        raise ValueError(f"failure {index} has an unknown affected phase")
    expected_reset = list(downstream_phases(affected_phase))
    downstream_reset = failure.get("downstream_reset")
    if downstream_reset != expected_reset:
        raise ValueError(
            f"failure {index}.downstream_reset must equal {expected_reset}"
        )
    repair_action = failure.get("repair_action")
    if not isinstance(repair_action, str) or not repair_action.strip():
        raise ValueError(f"failure {index}.repair_action must be non-empty text")
    return {
        "error_type": error_type,
        "artifact": artifact,
        "affected_phase": affected_phase,
        "downstream_reset": expected_reset,
        "repair_action": repair_action.strip(),
    }


def _normalize_legacy_failure(
    failure: Mapping[str, object],
    *,
    index: int,
) -> list[dict[str, object]]:
    if set(failure) != _LEGACY_FAILURE_FIELDS:
        raise ValueError(f"failure {index} has an unsupported repair shape")
    failure_code = failure.get("failure_code")
    if (
        not isinstance(failure_code, str)
        or _LEGACY_ERROR_TYPE_RE.fullmatch(failure_code) is None
    ):
        raise ValueError(f"failure {index}.failure_code is not a stable identifier")
    affected_phase = failure.get("affected_phase")
    if affected_phase not in PHASES:
        raise ValueError(f"failure {index} has an unknown affected phase")
    paths = failure.get("affected_artifact_paths")
    evidence = failure.get("evidence")
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"failure {index} has no affected artifact")
    if not isinstance(evidence, list) or not evidence or any(
        not isinstance(item, str) or not item.strip() for item in evidence
    ):
        raise ValueError(f"failure {index} has no usable evidence")
    error_type = failure_code.casefold()
    expected_reset = list(downstream_phases(affected_phase))
    return [
        {
            "error_type": error_type,
            "artifact": validate_relative_artifact_path(path),
            "affected_phase": affected_phase,
            "downstream_reset": expected_reset,
            "repair_action": f"repair_{error_type}_and_revalidate",
        }
        for path in paths
    ]


def normalize_machine_failures(
    failures: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Return deterministic five-field failures suitable for local repair."""

    if not isinstance(failures, Sequence) or isinstance(failures, (str, bytes)):
        raise ValueError("failures must be a structured sequence")
    if not failures:
        raise ValueError("a repair plan requires at least one failure")
    normalized: list[dict[str, object]] = []
    for index, raw_failure in enumerate(failures, start=1):
        if not isinstance(raw_failure, Mapping):
            raise ValueError(f"failure {index} must be a structured object")
        failure = copy.deepcopy(dict(raw_failure))
        if set(failure) == MACHINE_FAILURE_FIELDS:
            normalized.append(_normalize_machine_failure(failure, index=index))
        elif set(failure) == _LEGACY_FAILURE_FIELDS:
            normalized.extend(_normalize_legacy_failure(failure, index=index))
        else:
            raise ValueError(f"failure {index} has an unsupported repair shape")

    path_spellings: dict[str, str] = {}
    fingerprints: set[tuple[str, str, str]] = set()
    for index, failure in enumerate(normalized, start=1):
        artifact = failure["artifact"]
        assert isinstance(artifact, str)
        folded = artifact.casefold()
        prior = path_spellings.get(folded)
        if prior is not None and prior != artifact:
            raise ValueError(
                "repair failures contain casefold artifact aliases: "
                f"{prior!r} and {artifact!r}"
            )
        path_spellings[folded] = artifact
        fingerprint = (
            str(failure["error_type"]),
            artifact,
            str(failure["affected_phase"]),
        )
        if fingerprint in fingerprints:
            raise ValueError(f"repair failure {index} is duplicated")
        fingerprints.add(fingerprint)

    return sorted(
        normalized,
        key=lambda failure: (
            PHASES.index(str(failure["affected_phase"])),
            str(failure["artifact"]),
            str(failure["error_type"]),
        ),
    )


def build_repair_plan(
    failed_report: Mapping[str, object],
    failures: Sequence[Mapping[str, object]],
    *,
    created_at: str,
) -> dict[str, object]:
    if not isinstance(failed_report, Mapping):
        raise ValueError("failed_report must be a structured object")
    normalized = normalize_machine_failures(failures)
    earliest = min(
        (str(record["affected_phase"]) for record in normalized),
        key=PHASES.index,
    )
    expected_paths = sorted({str(record["artifact"]) for record in normalized})
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("created_at must be a non-empty timestamp")
    plan: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.repair-plan",
        "schema_version": 1,
        "run_id": failed_report.get("run_id"),
        "source_snapshot_sha256": failed_report.get("source_snapshot_sha256"),
        "failed_report_sha256": failed_report.get("report_sha256"),
        "failures": normalized,
        "reset_from_phase": earliest,
        "invalidated_phases": list(downstream_phases(earliest)),
        "repair_actions": [
            {
                "action_id": "REPAIR-1",
                "phase_id": earliest,
                "description": (
                    f"Reset {earliest} and its descendants, rebuild the affected "
                    "artifacts, regenerate the manifest, reset validation to "
                    "not_run, and execute the full frozen validator set"
                ),
                "expected_output_paths": expected_paths,
            }
        ],
        "validation_state": "not_run",
        "manifest_regeneration_required": True,
        "revalidation_required": True,
        "revalidation_scope": "full-validator-set",
        "created_at": created_at.strip(),
    }
    validate_instance("promax-repair-plan.schema.json", plan)
    return plan
