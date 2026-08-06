from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Mapping, Sequence

from .constants import PHASES, current_version_binding
from .errors import UltraRuntimeError
from .jsonio import (
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .paths import RunLayout, assert_safe_descendant
from .schemas import (
    compute_artifact_content_sha256,
    validate_phase_artifact,
)
from .status import RunStatusStore


REPORT_FILENAME = "ultra-validator-report.json"
REPAIR_PLAN_FILENAME = "ultra-repair-plan.json"
MANIFEST_FILENAME = "ultra-artifact-manifest.json"
ARTICLE_PARTIAL_PATH = "work/authoring/article.partial.md"
MAX_REPAIR_ATTEMPTS = 3

_REPORT_SCHEMA = "ultra-validator-report.schema.json"
_REPORT_SCHEMA_ID = "crossframe.ultra.v82.validator-report"
_MANIFEST_SCHEMA = "ultra-artifact-manifest.schema.json"
_MANIFEST_SCHEMA_ID = "crossframe.ultra.v82.artifact-manifest"
_REPAIR_SCHEMA = "ultra-repair-plan.schema.json"
_REPAIR_SCHEMA_ID = "crossframe.ultra.v82.repair-plan"
_ATTEMPT_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class RepairError(UltraRuntimeError, RuntimeError):
    """Base error for bounded Ultra repair planning."""


class InvalidFailureRecordError(RepairError, ValueError):
    """A validator result cannot authorize a deterministic repair."""


class NonRetryableFailureError(RepairError):
    """A verified failure requires attention rather than automatic repair."""


class StaleValidationAttemptError(RepairError):
    """The selected validation attempt is no longer current or hash-bound."""


class RepairAttemptLimitError(RepairError):
    """The bounded three-attempt repair window has been exhausted."""


class RepairPlanConflictError(RepairError):
    """An immutable attempt already contains different repair-plan bytes."""


@dataclass(frozen=True, slots=True)
class _FailurePolicy:
    affected_phase: str
    retryable: bool
    repair_action: str
    fixed_artifact: str | None = None


_FAILURE_POLICIES = {
    "ULTRA-COVERAGE-MISSING": _FailurePolicy(
        affected_phase="U10",
        retryable=True,
        repair_action="regenerate_missing_semantic_unit_packet",
        fixed_artifact=ARTICLE_PARTIAL_PATH,
    ),
    "ULTRA-ARTICLE-REVIEW-FAILED": _FailurePolicy(
        affected_phase="U11",
        retryable=True,
        repair_action="regenerate_article_from_frozen_packets",
        fixed_artifact=ARTICLE_PARTIAL_PATH,
    ),
    "ULTRA-SOURCE-HASH-MISMATCH": _FailurePolicy(
        affected_phase="U3",
        retryable=False,
        repair_action="inspect_source_authority_violation",
    ),
}


def _require_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")


def _require_attempt_id(attempt_id: object) -> str:
    if not isinstance(attempt_id, str) or _ATTEMPT_ID_RE.fullmatch(attempt_id) is None:
        raise ValueError("attempt_id must be a safe validation identifier")
    return attempt_id


def _require_attempt_number(attempt_number: object) -> int:
    if isinstance(attempt_number, bool) or not isinstance(attempt_number, int):
        raise TypeError("attempt_number must be an integer")
    if attempt_number < 1:
        raise ValueError("attempt_number must be positive")
    if attempt_number > MAX_REPAIR_ATTEMPTS:
        raise RepairAttemptLimitError("a fourth repair attempt is not allowed")
    return attempt_number


def _require_utc(value: datetime, label: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be timezone-aware UTC")


def _iso_utc(value: datetime) -> str:
    _require_utc(value, "now")
    return value.isoformat(
        timespec="microseconds" if value.microsecond else "seconds"
    ).replace("+00:00", "Z")


def _parse_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise StaleValidationAttemptError(f"{label} is not a canonical UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise StaleValidationAttemptError(f"{label} is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise StaleValidationAttemptError(f"{label} must be UTC")
    return parsed


def _attempt_report_path(layout: RunLayout, attempt_id: str) -> Path:
    path = layout.validation_attempts_dir / attempt_id / REPORT_FILENAME
    return assert_safe_descendant(layout.root, path)


def _attempt_plan_path(layout: RunLayout, attempt_id: str) -> Path:
    path = layout.validation_attempts_dir / attempt_id / REPAIR_PLAN_FILENAME
    return assert_safe_descendant(layout.root, path)


def _current_report_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.validation_current_dir / REPORT_FILENAME,
    )


def _current_plan_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.validation_current_dir / REPAIR_PLAN_FILENAME,
    )


def _manifest_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / MANIFEST_FILENAME,
    )


def _canonical_artifact(
    path: Path,
    *,
    schema_name: str,
    schema_id: str,
    run_id: str,
) -> tuple[bytes, dict[str, object]]:
    raw = path.read_bytes()
    artifact = load_json_object(path)
    validated = validate_phase_artifact(
        schema_name,
        artifact,
        expected_schema_id=schema_id,
        expected_run_id=run_id,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    if raw != canonical_json_bytes(validated):
        raise StaleValidationAttemptError(f"non-canonical control artifact: {path.name}")
    return raw, validated


def _validated_report_at(
    layout: RunLayout,
    path: Path,
) -> tuple[bytes, dict[str, object]]:
    return _canonical_artifact(
        path,
        schema_name=_REPORT_SCHEMA,
        schema_id=_REPORT_SCHEMA_ID,
        run_id=layout.run_dir.name,
    )


def _load_current_attempt(
    layout: RunLayout,
    attempt_id: str,
    *,
    now: datetime,
) -> tuple[bytes, dict[str, object]]:
    attempt_raw, report = _validated_report_at(
        layout,
        _attempt_report_path(layout, attempt_id),
    )
    current_raw, current_report = _validated_report_at(
        layout,
        _current_report_path(layout),
    )
    if report.get("attempt_id") != attempt_id:
        raise StaleValidationAttemptError("attempt directory and report identity differ")
    if current_report.get("attempt_id") != attempt_id or current_raw != attempt_raw:
        raise StaleValidationAttemptError(
            "repair requires the byte-identical current committed validation attempt"
        )
    validated_at = _parse_timestamp(report.get("validated_at"), "validated_at")
    if validated_at > now:
        raise StaleValidationAttemptError("validation attempt is dated after repair time")
    if report.get("overall_status") != "fail":
        raise InvalidFailureRecordError("only a failed validator report can be repaired")
    return attempt_raw, report


def _failure_records(report: Mapping[str, object]) -> list[dict[str, object]]:
    checks = report.get("checks")
    if not isinstance(checks, list):
        raise InvalidFailureRecordError("validator report checks are invalid")
    failures: list[dict[str, object]] = []
    fingerprints: set[tuple[str, str, str]] = set()
    for check in checks:
        if not isinstance(check, Mapping):
            raise InvalidFailureRecordError("validator check is not structured")
        status = check.get("status")
        if status == "pass":
            continue
        if status != "fail":
            raise NonRetryableFailureError("blocked validation is not retryable repair")
        error_codes = check.get("error_codes")
        artifact_refs = check.get("artifact_refs")
        if not isinstance(error_codes, list) or not error_codes:
            raise InvalidFailureRecordError("failed check has no error code")
        if not isinstance(artifact_refs, list) or not artifact_refs:
            raise InvalidFailureRecordError("failed check has no affected artifact")
        for error_code in error_codes:
            if not isinstance(error_code, str):
                raise InvalidFailureRecordError("failure error_code is invalid")
            policy = _FAILURE_POLICIES.get(error_code)
            if policy is None:
                raise InvalidFailureRecordError(
                    f"unknown validator failure policy: {error_code}"
                )
            if policy.fixed_artifact is not None:
                if policy.fixed_artifact not in artifact_refs:
                    raise InvalidFailureRecordError(
                        f"{error_code} does not reference its fixed artifact"
                    )
                artifact = policy.fixed_artifact
            else:
                artifact = artifact_refs[0]
                if not isinstance(artifact, str) or not artifact:
                    raise InvalidFailureRecordError("failure artifact is invalid")
            phase_index = PHASES.index(policy.affected_phase)
            failure = {
                "error_code": error_code,
                "artifact": artifact,
                "affected_phase": policy.affected_phase,
                "downstream_reset": list(PHASES[phase_index:]),
                "retryable": policy.retryable,
                "repair_action": policy.repair_action,
            }
            fingerprint = (error_code, artifact, policy.affected_phase)
            if fingerprint in fingerprints:
                raise InvalidFailureRecordError("validator failure record is duplicated")
            fingerprints.add(fingerprint)
            failures.append(failure)
    if not failures:
        raise InvalidFailureRecordError("failed report has no machine failure record")
    failures.sort(
        key=lambda failure: (
            PHASES.index(str(failure["affected_phase"])),
            str(failure["artifact"]),
            str(failure["error_code"]),
        )
    )
    if any(failure["retryable"] is not True for failure in failures):
        raise NonRetryableFailureError(
            "validation attempt contains a non-retryable failure"
        )
    return failures


def _load_manifest(
    layout: RunLayout,
    report: Mapping[str, object],
) -> dict[str, object]:
    path = _manifest_path(layout)
    raw, manifest = _canonical_artifact(
        path,
        schema_name=_MANIFEST_SCHEMA,
        schema_id=_MANIFEST_SCHEMA_ID,
        run_id=layout.run_dir.name,
    )
    if report.get("manifest_sha256") != sha256_bytes(raw):
        raise StaleValidationAttemptError("failed report does not bind the current manifest")
    if report.get("validator_set_sha256") != manifest.get("validator_set_sha256"):
        raise StaleValidationAttemptError(
            "failed report and manifest validator-set hashes differ"
        )
    return manifest


def _preserved_upstream_hashes(
    layout: RunLayout,
    manifest: Mapping[str, object],
    reset_from_phase: str,
) -> list[str]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise StaleValidationAttemptError("manifest artifact inventory is invalid")
    reset_index = PHASES.index(reset_from_phase)
    preserved: set[str] = set()
    for entry in artifacts:
        if not isinstance(entry, Mapping):
            raise StaleValidationAttemptError("manifest artifact entry is invalid")
        phase_id = entry.get("phase_id")
        if phase_id not in PHASES:
            raise StaleValidationAttemptError("manifest artifact phase is invalid")
        if PHASES.index(str(phase_id)) >= reset_index:
            continue
        relative = entry.get("path")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected_sha256, str):
            raise StaleValidationAttemptError("manifest upstream hash entry is invalid")
        artifact_path = assert_safe_descendant(
            layout.root,
            layout.run_dir / Path(relative),
        )
        if sha256_bytes(artifact_path.read_bytes()) != expected_sha256:
            raise StaleValidationAttemptError(
                f"upstream artifact hash changed: {relative}"
            )
        preserved.add(expected_sha256)
    return sorted(preserved)


def _committed_reports(
    layout: RunLayout,
    *,
    now: datetime,
) -> list[tuple[str, bytes, dict[str, object]]]:
    reports: list[tuple[str, bytes, dict[str, object]]] = []
    if not layout.validation_attempts_dir.is_dir():
        raise StaleValidationAttemptError("validation attempts directory is missing")
    for child in layout.validation_attempts_dir.iterdir():
        if not child.is_dir() or _ATTEMPT_ID_RE.fullmatch(child.name) is None:
            continue
        path = assert_safe_descendant(layout.root, child / REPORT_FILENAME)
        if not path.is_file():
            continue
        raw, report = _validated_report_at(layout, path)
        if report.get("attempt_id") != child.name:
            raise StaleValidationAttemptError(
                "validation attempt directory and report identity differ"
            )
        validated_at = _parse_timestamp(report.get("validated_at"), "validated_at")
        if validated_at > now:
            raise StaleValidationAttemptError("validation history contains a future attempt")
        reports.append((child.name, raw, report))
    reports.sort(
        key=lambda item: (
            _parse_timestamp(item[2].get("validated_at"), "validated_at"),
            item[0],
        )
    )
    return reports


def _validated_prior_plan(
    layout: RunLayout,
    *,
    attempt_id: str,
    current_attempt_number: int,
    report_raw: bytes,
) -> dict[str, object] | None:
    path = _attempt_plan_path(layout, attempt_id)
    if not path.exists():
        return None
    _, plan = _canonical_artifact(
        path,
        schema_name=_REPAIR_SCHEMA,
        schema_id=_REPAIR_SCHEMA_ID,
        run_id=layout.run_dir.name,
    )
    prior_attempt_number = plan.get("attempt_number")
    if (
        isinstance(prior_attempt_number, bool)
        or not isinstance(prior_attempt_number, int)
        or prior_attempt_number < 1
        or prior_attempt_number >= current_attempt_number
    ):
        raise StaleValidationAttemptError("prior repair plan attempt number is stale")
    if plan.get("failed_report_sha256") != sha256_bytes(report_raw):
        raise StaleValidationAttemptError("prior repair plan is bound to another report")
    return plan


def _has_repeated_failure(
    layout: RunLayout,
    *,
    current_attempt_id: str,
    attempt_number: int,
    failures: Sequence[Mapping[str, object]],
    now: datetime,
) -> bool:
    reports = _committed_reports(layout, now=now)
    if not reports or reports[-1][0] != current_attempt_id:
        raise StaleValidationAttemptError("selected validation attempt is not latest")
    current = {
        (
            str(failure.get("error_code")),
            str(failure.get("artifact")),
            str(failure.get("affected_phase")),
        )
        for failure in failures
    }
    seen_attempt_numbers: set[int] = set()
    for prior_id, prior_raw, _ in reports[:-1]:
        prior_plan = _validated_prior_plan(
            layout,
            attempt_id=prior_id,
            current_attempt_number=attempt_number,
            report_raw=prior_raw,
        )
        if prior_plan is None:
            continue
        prior_attempt_number = int(prior_plan["attempt_number"])
        if prior_attempt_number in seen_attempt_numbers:
            raise StaleValidationAttemptError(
                "validation history repeats a repair attempt number"
            )
        seen_attempt_numbers.add(prior_attempt_number)
        prior_failures = prior_plan.get("failures")
        if not isinstance(prior_failures, list):
            raise StaleValidationAttemptError("prior repair failure records are invalid")
        prior = {
            (
                str(failure.get("error_code")),
                str(failure.get("artifact")),
                str(failure.get("affected_phase")),
            )
            for failure in prior_failures
            if isinstance(failure, Mapping)
        }
        if current & prior:
            return True
    return False


def _ordered_actions(failures: Sequence[Mapping[str, object]]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for failure in failures:
        action = str(failure["repair_action"])
        if action not in seen:
            seen.add(action)
            actions.append(action)
    return actions


def _mark_needs_attention(
    layout: RunLayout,
    *,
    now: datetime,
    lease: object | None,
) -> None:
    store = RunStatusStore(layout)
    if not store.path.exists():
        return
    current = store.read()
    if current.status == "needs_attention":
        return
    store.transition(
        current,
        "needs_attention",
        now,
        reason="repeated validator failure requires human attention",
        validation_passed=False,
        lease=lease,
    )


def build_repair_plan(
    layout: RunLayout,
    *,
    attempt_id: str,
    attempt_number: int,
    now: datetime,
    lease: object | None = None,
) -> dict[str, object]:
    """Build one hash-bound repair plan from the current committed attempt."""

    _require_layout(layout)
    checked_attempt_id = _require_attempt_id(attempt_id)
    checked_attempt_number = _require_attempt_number(attempt_number)
    _require_utc(now, "now")
    report_raw, report = _load_current_attempt(
        layout,
        checked_attempt_id,
        now=now,
    )
    failures = _failure_records(report)
    reset_from_phase = min(
        (str(failure["affected_phase"]) for failure in failures),
        key=PHASES.index,
    )
    manifest = _load_manifest(layout, report)
    preserved = _preserved_upstream_hashes(
        layout,
        manifest,
        reset_from_phase,
    )
    repeated = _has_repeated_failure(
        layout,
        current_attempt_id=checked_attempt_id,
        attempt_number=checked_attempt_number,
        failures=failures,
        now=now,
    )
    plan: dict[str, object] = {
        "schema_id": _REPAIR_SCHEMA_ID,
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": _iso_utc(now),
        "phase_id": "U12",
        "failed_report_sha256": sha256_bytes(report_raw),
        "attempt_number": checked_attempt_number,
        "failures": failures,
        "reset_from_phase": reset_from_phase,
        "preserved_artifact_hashes": preserved,
        "repair_actions": _ordered_actions(failures),
        "manifest_regeneration_required": True,
        "revalidation_required": True,
        "status": "needs_attention" if repeated else "planned",
    }
    plan["content_sha256"] = compute_artifact_content_sha256(plan)
    validated = validate_phase_artifact(
        _REPAIR_SCHEMA,
        plan,
        expected_schema_id=_REPAIR_SCHEMA_ID,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    if repeated:
        _mark_needs_attention(layout, now=now, lease=lease)
    return validated


def current_attempt_identity(
    layout: RunLayout,
    *,
    now: datetime,
) -> tuple[str, int]:
    """Return the current committed attempt ID and its one-based ordinal."""

    _require_layout(layout)
    _require_utc(now, "now")
    _, current = _validated_report_at(layout, _current_report_path(layout))
    attempt_id = _require_attempt_id(current.get("attempt_id"))
    reports = _committed_reports(layout, now=now)
    if not reports or reports[-1][0] != attempt_id:
        raise StaleValidationAttemptError("current validation report is not latest")
    attempt_number = len(reports)
    _require_attempt_number(attempt_number)
    return attempt_id, attempt_number


def commit_repair_plan(
    layout: RunLayout,
    *,
    attempt_id: str,
    plan: Mapping[str, object],
) -> dict[str, object]:
    """Persist immutable attempt bytes and replace the current projection."""

    _require_layout(layout)
    checked_attempt_id = _require_attempt_id(attempt_id)
    validated = validate_phase_artifact(
        _REPAIR_SCHEMA,
        plan,
        expected_schema_id=_REPAIR_SCHEMA_ID,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    report_raw, report = _validated_report_at(
        layout,
        _attempt_report_path(layout, checked_attempt_id),
    )
    if report.get("attempt_id") != checked_attempt_id:
        raise StaleValidationAttemptError("repair plan attempt identity is stale")
    if validated.get("failed_report_sha256") != sha256_bytes(report_raw):
        raise StaleValidationAttemptError("repair plan is bound to another report")
    attempt_path = _attempt_plan_path(layout, checked_attempt_id)
    encoded = canonical_json_bytes(validated)
    if attempt_path.exists() and attempt_path.read_bytes() != encoded:
        raise RepairPlanConflictError(
            "immutable validation attempt already has different repair-plan bytes"
        )
    if not attempt_path.exists():
        atomic_write_json(attempt_path, validated)
    atomic_write_json(_current_plan_path(layout), validated)
    return validated


__all__ = [
    "ARTICLE_PARTIAL_PATH",
    "InvalidFailureRecordError",
    "MAX_REPAIR_ATTEMPTS",
    "NonRetryableFailureError",
    "RepairAttemptLimitError",
    "RepairError",
    "RepairPlanConflictError",
    "StaleValidationAttemptError",
    "build_repair_plan",
    "commit_repair_plan",
    "current_attempt_identity",
]
