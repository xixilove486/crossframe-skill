from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import re
from typing import Mapping, Sequence

from .constants import PHASES, current_version_binding
from .errors import UltraRuntimeError
from .jsonio import (
    _exclusive_path_lock,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import RunLayout, assert_safe_descendant
from .schemas import (
    compute_artifact_content_sha256,
    validate_instance,
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
    lease: object | None = None,
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
    from .locks import (
        acquire_run_lease,
        release_run_lease,
        require_run_lease_owner,
    )

    if lease is None:
        owned = acquire_run_lease(
            layout,
            _parse_timestamp(validated.get("generated_at"), "plan generated_at"),
            timedelta(minutes=5),
        )
        try:
            return commit_repair_plan(
                layout,
                attempt_id=attempt_id,
                plan=validated,
                lease=owned,
            )
        finally:
            release_run_lease(layout, owned)
    require_run_lease_owner(layout, lease)
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


def _committed_plan_identity(
    layout: RunLayout,
    plan: Mapping[str, object],
) -> tuple[str, dict[str, object], str]:
    validated = validate_phase_artifact(
        _REPAIR_SCHEMA,
        plan,
        expected_schema_id=_REPAIR_SCHEMA_ID,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    current_raw, current_report = _validated_report_at(
        layout,
        _current_report_path(layout),
    )
    attempt_id = _require_attempt_id(current_report.get("attempt_id"))
    attempt_raw, attempt_report = _validated_report_at(
        layout,
        _attempt_report_path(layout, attempt_id),
    )
    if (
        attempt_report.get("attempt_id") != attempt_id
        or current_raw != attempt_raw
        or validated.get("failed_report_sha256") != sha256_bytes(attempt_raw)
    ):
        raise StaleValidationAttemptError(
            "repair application requires the byte-identical current failed report"
        )
    expected = canonical_json_bytes(validated)
    for path in (_attempt_plan_path(layout, attempt_id), _current_plan_path(layout)):
        try:
            if path.read_bytes() != expected:
                raise StaleValidationAttemptError(
                    "repair application requires the committed current plan bytes"
                )
        except OSError as error:
            raise StaleValidationAttemptError(
                "repair application plan authority is unavailable"
            ) from error
    plan_sha256 = hashlib.sha256(expected).hexdigest()
    return attempt_id, validated, plan_sha256


def _repair_attempt_root(layout: RunLayout, attempt_id: str) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "repair-attempts" / attempt_id,
    )


def _active_events(
    events: Sequence[Mapping[str, object]],
) -> tuple[int, list[dict[str, object]]]:
    generation = 0
    active: list[dict[str, object]] = []
    for raw in events:
        event = copy.deepcopy(dict(raw))
        if event.get("status") == "complete":
            active.append(event)
        elif event.get("status") == "invalidated":
            reset = str(event.get("reset_from_phase"))
            generation = int(event.get("generation", generation + 1))
            active = active[: PHASES.index(reset)]
    return generation, active


def _preserve_superseded_artifacts(
    layout: RunLayout,
    *,
    attempt_id: str,
    manifest: Mapping[str, object],
    checkpoints: Sequence[Mapping[str, object]],
    active_event_sha256s: frozenset[str],
    generation: int,
    reset_from_phase: str,
    now: datetime,
) -> tuple[dict[str, object], str]:
    root = _repair_attempt_root(layout, attempt_id)
    superseded_root = root / "superseded"
    candidates: dict[str, dict[str, str]] = {}

    def add_candidate(value: Mapping[str, object]) -> None:
        relative = value.get("path")
        digest = value.get("sha256")
        media_type = value.get("media_type")
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not isinstance(media_type, str)
            or not media_type
        ):
            raise StaleValidationAttemptError(
                "superseded artifact inventory entry is invalid"
            )
        candidate = {
            "path": relative,
            "sha256": digest,
            "media_type": media_type,
        }
        prior = candidates.get(relative)
        if prior is not None and prior != candidate:
            raise StaleValidationAttemptError(
                f"superseded artifact authority conflicts: {relative}"
            )
        candidates[relative] = candidate

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise StaleValidationAttemptError("manifest artifact inventory is invalid")
    reset_index = PHASES.index(reset_from_phase)
    for item in artifacts:
        if not isinstance(item, Mapping) or item.get("phase_id") not in PHASES:
            raise StaleValidationAttemptError("manifest artifact entry is invalid")
        if PHASES.index(str(item["phase_id"])) < reset_index:
            continue
        add_candidate(item)
    for checkpoint in checkpoints:
        phase_id = checkpoint.get("phase_id")
        boundary_kind = checkpoint.get("boundary_kind")
        event_sha256 = checkpoint.get("phase_event_sha256")
        checkpoint_generation = checkpoint.get("generation")
        if (
            phase_id not in PHASES
            or PHASES.index(str(phase_id)) < reset_index
            or event_sha256 not in active_event_sha256s
            or (
                boundary_kind == "article-packet"
                and checkpoint_generation != generation
            )
        ):
            continue
        refs = checkpoint.get("artifact_hashes")
        if not isinstance(refs, list) or not refs:
            raise StaleValidationAttemptError(
                "active checkpoint artifact inventory is invalid"
            )
        for item in refs:
            if not isinstance(item, Mapping):
                raise StaleValidationAttemptError(
                    "active checkpoint artifact entry is invalid"
                )
            add_candidate(item)

    records: list[dict[str, str]] = []
    for candidate in sorted(candidates.values(), key=lambda item: item["path"]):
        relative = Path(candidate["path"])
        source = assert_safe_descendant(layout.root, layout.run_dir / relative)
        snapshot_name = f"ART-{len(records) + 1:04d}.bin"
        target = assert_safe_descendant(layout.root, superseded_root / snapshot_name)
        try:
            payload = source.read_bytes()
        except OSError as error:
            raise StaleValidationAttemptError(
                f"superseded artifact is unavailable: {relative.as_posix()}"
            ) from error
        digest = hashlib.sha256(payload).hexdigest()
        if digest != candidate["sha256"]:
            raise StaleValidationAttemptError(
                f"superseded artifact changed: {relative.as_posix()}"
            )
        if target.exists() and target.read_bytes() != payload:
            raise RepairPlanConflictError(
                f"superseded artifact snapshot differs: {relative.as_posix()}"
            )
        if not target.exists():
            atomic_write_bytes(target, payload)
        records.append(
            {
                "original_path": relative.as_posix(),
                "snapshot_path": target.relative_to(layout.run_dir).as_posix(),
                "sha256": digest,
                "media_type": candidate["media_type"],
            }
        )
    if not records:
        raise StaleValidationAttemptError("repair has no affected artifact snapshot")
    snapshot: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.repair-superseded-snapshot",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": _iso_utc(now),
        "phase_id": reset_from_phase,
        "repair_attempt_id": attempt_id,
        "artifacts": records,
        "content_sha256": "0" * 64,
    }
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    snapshot_path = root / "superseded-snapshot.json"
    raw = canonical_json_bytes(snapshot)
    if snapshot_path.exists() and snapshot_path.read_bytes() != raw:
        raise RepairPlanConflictError("superseded snapshot authority differs")
    if not snapshot_path.exists():
        atomic_write_bytes(snapshot_path, raw)
    return snapshot, hashlib.sha256(raw).hexdigest()


def _repair_next_action(reset_from_phase: str) -> dict[str, str]:
    relative = {
        "U10": "U10-output-plan.json",
        "U11": "article/packets",
        "U12": "validation",
    }.get(reset_from_phase, f"{reset_from_phase}-authoring")
    return {"phase_id": reset_from_phase, "relative_path": relative}


def _repair_application(
    layout: RunLayout,
    *,
    attempt_id: str,
    plan_sha256: str,
    invalidation: Mapping[str, object],
) -> dict[str, object]:
    reset_from_phase = str(invalidation["reset_from_phase"])
    application: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.repair-application",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": invalidation["generated_at"],
        "phase_id": reset_from_phase,
        "repair_attempt_id": attempt_id,
        "repair_plan_sha256": plan_sha256,
        "invalidation_event_sha256": invalidation["event_sha256"],
        "preserved_snapshot_sha256": invalidation["preserved_snapshot_sha256"],
        "reopened_phase": reset_from_phase,
        "active_generation": invalidation["generation"],
        "next_action": _repair_next_action(reset_from_phase),
        "content_sha256": "0" * 64,
    }
    application["content_sha256"] = compute_artifact_content_sha256(application)
    return application


def _reopen_status_for_repair(
    layout: RunLayout,
    *,
    invalidation: Mapping[str, object],
    now: datetime,
    lease: object,
) -> None:
    reset_from_phase = str(invalidation["reset_from_phase"])
    reset_index = PHASES.index(reset_from_phase)
    expected_last_complete = PHASES[reset_index - 1] if reset_index else None
    store = RunStatusStore(layout)
    current = store.read()
    if (
        current.status == "running"
        and current.current_phase == reset_from_phase
        and current.last_complete_phase == expected_last_complete
        and current.validation_passed is False
    ):
        return
    store.reopen_for_repair(
        current,
        now,
        reset_from_phase=reset_from_phase,
        invalidation_event_sha256=str(invalidation["event_sha256"]),
        generation=int(invalidation["generation"]),
        lease=lease,
    )


def apply_repair_plan(
    layout: RunLayout,
    *,
    plan: Mapping[str, object],
    now: datetime,
    lease: object | None = None,
) -> dict[str, object]:
    _require_layout(layout)
    _require_utc(now, "now")
    from . import recovery
    from .locks import (
        CancelledRunError,
        _cancel_intent_lock_path,
        _validation_current_commit_lock_path,
        acquire_run_lease,
        load_cancel_intent,
        release_run_lease,
        require_run_lease_owner,
    )
    from .state_machine import (
        PHASE_EVENT_SCHEMA_ID,
        _compute_event_content_sha256,
        compute_event_sha256,
    )

    owned = None
    if lease is None:
        owned = acquire_run_lease(layout, now, timedelta(minutes=5))
        lease = owned
    def require_repair_write_authority() -> None:
        require_run_lease_owner(layout, lease)
        if load_cancel_intent(layout) is not None:
            raise CancelledRunError("cancel intent blocks repair commit")
        require_run_lease_owner(layout, lease)

    def recheck_repair_commit_fence(
        *,
        expected_attempt_id: str,
        expected_plan_sha256: str,
        expected_authority: Mapping[str, object],
        expected_compatibility: str,
        expected_events: Sequence[Mapping[str, object]],
        expected_manifest: Mapping[str, object],
    ) -> None:
        current_attempt_id, _, current_plan_sha256 = _committed_plan_identity(
            layout,
            plan,
        )
        if (
            current_attempt_id != expected_attempt_id
            or current_plan_sha256 != expected_plan_sha256
        ):
            raise StaleValidationAttemptError(
                "repair inputs changed before invalidation commit"
            )
        current_authority, current_compatibility, _ = recovery._validate_authority_record(
            layout
        )
        current_events = recovery._read_events(
            layout,
            current_authority,
            compatibility=current_compatibility,
        )
        if (
            current_compatibility != expected_compatibility
            or current_authority != expected_authority
            or tuple(current_events) != tuple(expected_events)
        ):
            raise StaleValidationAttemptError(
                "repair recovery authority changed before invalidation commit"
            )
        _, current_report = _validated_report_at(
            layout,
            _current_report_path(layout),
        )
        current_manifest = _load_manifest(layout, current_report)
        if current_manifest != expected_manifest:
            raise StaleValidationAttemptError(
                "repair manifest changed before invalidation commit"
            )

    require_repair_write_authority()
    try:
        attempt_id, validated, plan_sha256 = _committed_plan_identity(layout, plan)
        attempt_root = _repair_attempt_root(layout, attempt_id)
        application_path = attempt_root / "repair-application.json"
        authority, compatibility, _ = recovery._validate_authority_record(layout)
        events = recovery._read_events(layout, authority, compatibility=compatibility)
        matching_invalidations = [
            event
            for event in events
            if event.get("status") == "invalidated"
            and event.get("repair_plan_sha256") == plan_sha256
        ]
        if len(matching_invalidations) > 1:
            raise RepairPlanConflictError("repair plan has multiple invalidation events")
        if matching_invalidations:
            invalidation = matching_invalidations[0]
            if (
                invalidation.get("repair_attempt_id") != attempt_id
                or invalidation.get("failed_report_sha256")
                != validated["failed_report_sha256"]
                or invalidation.get("reset_from_phase")
                != validated["reset_from_phase"]
            ):
                raise RepairPlanConflictError("repair invalidation authority differs")
            snapshot_path = attempt_root / "superseded-snapshot.json"
            try:
                snapshot_raw = snapshot_path.read_bytes()
                snapshot = load_json_object_bytes(
                    snapshot_raw,
                    source=str(snapshot_path),
                )
            except (OSError, TypeError, ValueError) as error:
                raise RepairPlanConflictError(
                    "repair invalidation preserved snapshot is unavailable"
                ) from error
            if (
                hashlib.sha256(snapshot_raw).hexdigest()
                != invalidation["preserved_snapshot_sha256"]
                or snapshot.get("content_sha256")
                != compute_artifact_content_sha256(snapshot)
                or snapshot.get("repair_attempt_id") != attempt_id
            ):
                raise RepairPlanConflictError(
                    "repair invalidation preserved snapshot differs"
                )
            require_repair_write_authority()
            _reopen_status_for_repair(
                layout,
                invalidation=invalidation,
                now=now,
                lease=lease,
            )
            application = _repair_application(
                layout,
                attempt_id=attempt_id,
                plan_sha256=plan_sha256,
                invalidation=invalidation,
            )
            encoded = canonical_json_bytes(application)
            if application_path.exists():
                if application_path.read_bytes() != encoded:
                    raise RepairPlanConflictError("repair application authority differs")
            else:
                require_repair_write_authority()
                atomic_write_bytes(application_path, encoded)
            return copy.deepcopy(application)

        if application_path.exists():
            raise RepairPlanConflictError(
                "repair application exists without its invalidation event"
            )
        generation, active = _active_events(events)
        reset_from_phase = str(validated["reset_from_phase"])
        reset_index = PHASES.index(reset_from_phase)
        if len(active) <= reset_index:
            raise StaleValidationAttemptError(
                "repair reset phase is not currently complete"
            )
        superseded = [str(item["event_sha256"]) for item in active[reset_index:]]
        checkpoints_dir = layout.recovery_dir / "checkpoints"
        checkpoints = (
            recovery.load_checkpoints(layout)
            if checkpoints_dir.is_dir()
            else ()
        )
        _, current_report = _validated_report_at(
            layout,
            _current_report_path(layout),
        )
        manifest = _load_manifest(layout, current_report)
        snapshot_time = _parse_timestamp(
            validated.get("generated_at"),
            "repair plan generated_at",
        )
        _, snapshot_sha256 = _preserve_superseded_artifacts(
            layout,
            attempt_id=attempt_id,
            manifest=manifest,
            checkpoints=checkpoints,
            active_event_sha256s=frozenset(
                str(item["event_sha256"]) for item in active
            ),
            generation=generation,
            reset_from_phase=reset_from_phase,
            now=snapshot_time,
        )
        require_repair_write_authority()
        timestamp = _iso_utc(now)
        invalidation: dict[str, object] = {
            "schema_id": PHASE_EVENT_SCHEMA_ID,
            "schema_version": 1,
            "run_id": layout.run_dir.name,
            "version_binding": copy.deepcopy(authority["version_binding"]),
            "generated_at": timestamp,
            "content_sha256": "0" * 64,
            "phase_id": reset_from_phase,
            "event_type": "repair-invalidation",
            "parent_event_sha256": events[-1]["event_sha256"],
            "input_artifact_hashes": copy.deepcopy(authority["input_artifact_hashes"]),
            "output_artifact_hashes": [],
            "source_sha256": authority["source_sha256"],
            "evidence_cutoff": authority["evidence_cutoff"],
            "run_contract_sha256": authority["run_contract_sha256"],
            "timestamp": timestamp,
            "status": "invalidated",
            "failure_code": f"repair:{attempt_id}",
            "invalidated_phases": list(PHASES[reset_index:]),
            "generation": generation + 1,
            "reset_from_phase": reset_from_phase,
            "repair_attempt_id": attempt_id,
            "repair_plan_sha256": plan_sha256,
            "failed_report_sha256": validated["failed_report_sha256"],
            "preserved_snapshot_sha256": snapshot_sha256,
            "superseded_event_sha256s": superseded,
            "event_sha256": "0" * 64,
        }
        invalidation["content_sha256"] = _compute_event_content_sha256(invalidation)
        invalidation["event_sha256"] = compute_event_sha256(invalidation)
        validate_instance("ultra-phase-event.schema.json", invalidation)
        recovery._validate_event_chain(
            (*events, invalidation),
            authority,
            compatibility=compatibility,
        )
        _, _, _, events_path, lock_path = recovery._paths(layout)
        with _exclusive_path_lock(_validation_current_commit_lock_path(layout)):
            recheck_repair_commit_fence(
                expected_attempt_id=attempt_id,
                expected_plan_sha256=plan_sha256,
                expected_authority=authority,
                expected_compatibility=compatibility,
                expected_events=events,
                expected_manifest=manifest,
            )
            with _exclusive_path_lock(_cancel_intent_lock_path(layout)):
                require_repair_write_authority()
                with recovery._exclusive_path_lock(lock_path):
                    recovery._sync_events(events_path, (*events, invalidation))
        require_repair_write_authority()
        _reopen_status_for_repair(
            layout,
            invalidation=invalidation,
            now=now,
            lease=lease,
        )
        application = _repair_application(
            layout,
            attempt_id=attempt_id,
            plan_sha256=plan_sha256,
            invalidation=invalidation,
        )
        require_repair_write_authority()
        atomic_write_json(application_path, application)
        return copy.deepcopy(application)
    finally:
        if owned is not None:
            release_run_lease(layout, owned)


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
    "apply_repair_plan",
]
