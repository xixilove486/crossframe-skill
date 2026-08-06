from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
import copy
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from . import concept_closure
from .constants import current_version_binding
from .errors import UltraRuntimeError
from .host_handshake import (
    HostActionSeal,
    HostResultSeal,
    _load_bound_result_document,
    _seal_action,
    _seal_result,
    issue_host_action,
    load_pending_action,
)
from .jsonio import (
    atomic_write_json,
    canonical_json_bytes,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import RunLayout, assert_safe_descendant
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


SEMANTIC_REVIEW_DIMENSIONS = (
    "direct-answer",
    "evidence-boundary",
    "current-judgment",
    "mechanism-competition",
    "recursive-expansion",
    "residuals",
    "reversal-conditions",
    "action-comparison",
    "concept-fidelity",
)
_ACTION_KIND = "semantic-review"
_ACTION_DIRECTORY = "u11-semantic-review"
_HOST_RESULT_SCHEMA_ID = "crossframe.ultra.v82.host-semantic-review-result"
_HOST_RESULT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "action_sha256",
        "reviewed_at",
        "reviewer",
        "dimension_reviews",
    }
)
_REVIEWER_FIELDS = frozenset(
    {
        "reviewer_id",
        "host_id",
        "provider_id",
        "model",
        "execution_id",
        "proof_grade",
    }
)
_DIMENSION_FIELDS = frozenset(
    {
        "dimension_id",
        "status",
        "rationale",
        "article_spans",
        "authority_refs",
    }
)
_AUTHORITY_HASH_FIELDS = (
    "article_sha256",
    "output_plan_artifact_sha256",
    "coverage_artifact_sha256",
    "article_review_artifact_sha256",
    "evidence_ledger_artifact_sha256",
    "concept_disposition_artifact_sha256",
)


class SemanticReviewError(UltraRuntimeError, ValueError):
    """Raised when semantic-review host or runtime authority is invalid."""


def _sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise SemanticReviewError(f"{label} must be a lowercase SHA-256")
    return value


def _nonempty(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticReviewError(f"{label} must be a nonempty string")
    return value


def _timestamp(value: object, *, label: str) -> datetime:
    text = _nonempty(value, label=label)
    try:
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text
        )
    except ValueError as error:
        raise SemanticReviewError(f"{label} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SemanticReviewError(f"{label} must include a timezone")
    return parsed


def _generation(value: object) -> int:
    if type(value) is not int or value < 0:
        raise SemanticReviewError(
            "semantic review active generation must be a nonnegative integer"
        )
    return value


def _required_units(values: Collection[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(
        values, Collection
    ):
        raise SemanticReviewError(
            "semantic review required concept units must be a collection"
        )
    snapshot = tuple(values)
    if not snapshot or any(
        not isinstance(unit, str) or not unit for unit in snapshot
    ):
        raise SemanticReviewError(
            "semantic review required concept units must be identified"
        )
    if len(snapshot) != len(set(snapshot)):
        raise SemanticReviewError(
            "semantic review required concept units contain duplicates"
        )
    return tuple(sorted(snapshot))


def required_units_sha256(values: Collection[str]) -> str:
    return sha256_bytes(canonical_json_bytes(list(_required_units(values))))


def validate_required_concept_units(
    concept_disposition: Mapping[str, object],
    required_concept_semantic_unit_ids: Collection[str],
) -> tuple[str, ...]:
    try:
        return concept_closure.validate_required_concept_semantic_units(
            concept_disposition,
            required_concept_semantic_unit_ids,
        )
    except (TypeError, ValueError) as error:
        raise SemanticReviewError(
            f"semantic review concept unit authority: {error}"
        ) from error


def _semantic_payload(
    *,
    request_intake_authority_sha256: str,
    active_generation: int,
    article_sha256: str,
    output_plan_artifact_sha256: str,
    coverage_artifact_sha256: str,
    article_review_artifact_sha256: str,
    evidence_ledger_artifact_sha256: str,
    concept_disposition_artifact_sha256: str,
    required_concept_semantic_unit_ids: Collection[str],
) -> dict[str, object]:
    units = _required_units(required_concept_semantic_unit_ids)
    values = {
        "article_sha256": article_sha256,
        "output_plan_artifact_sha256": output_plan_artifact_sha256,
        "coverage_artifact_sha256": coverage_artifact_sha256,
        "article_review_artifact_sha256": article_review_artifact_sha256,
        "evidence_ledger_artifact_sha256": evidence_ledger_artifact_sha256,
        "concept_disposition_artifact_sha256": (
            concept_disposition_artifact_sha256
        ),
    }
    return {
        "request_intake_authority_sha256": _sha256(
            request_intake_authority_sha256,
            label="request intake authority SHA-256",
        ),
        "active_generation": _generation(active_generation),
        **{
            field: _sha256(value, label=field.replace("_", " "))
            for field, value in values.items()
        },
        "required_concept_semantic_unit_ids": list(units),
        "required_concept_semantic_units_sha256": required_units_sha256(units),
        "requested_dimensions": list(SEMANTIC_REVIEW_DIMENSIONS),
        "allowed_provider_kinds": ["model", "service", "local"],
        "allowed_proof_grades": ["host-attested"],
        "requested_result_fields": [
            "dimension_reviews",
            "reviewed_at",
            "reviewer",
        ],
    }


def semantic_review_action_path(layout: RunLayout, active_generation: int) -> Path:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    generation = _generation(active_generation)
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / _ACTION_DIRECTORY
        / "actions"
        / f"generation-{generation:06d}.json",
    )


def semantic_review_result_relative_path(active_generation: int) -> str:
    generation = _generation(active_generation)
    return (
        "work/host/"
        f"U11-semantic-review-generation-{generation:06d}-result.json"
    )


def _accepted_path(layout: RunLayout, action: HostActionSeal) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json",
    )


def _validate_action_authority(
    layout: RunLayout,
    action: HostActionSeal,
    *,
    request_sha256: str,
    u10_parent_event_sha256: str,
    expected_payload: Mapping[str, object],
) -> HostActionSeal:
    expected_request = _sha256(request_sha256, label="request SHA-256")
    expected_parent = _sha256(
        u10_parent_event_sha256,
        label="U10 parent event SHA-256",
    )
    if (
        action.document.get("run_id") != layout.run_dir.name
        or action.document.get("version_binding") != current_version_binding()
        or action.document.get("phase_id") != "U11"
        or action.document.get("action_kind") != _ACTION_KIND
        or action.document.get("parent_event_sha256") != expected_parent
        or action.document.get("request_sha256") != expected_request
        or action.document.get("result_relative_path")
        != semantic_review_result_relative_path(
            int(expected_payload["active_generation"])
        )
        or action.document.get("payload") != dict(expected_payload)
    ):
        raise SemanticReviewError(
            "persisted semantic review action authority, parent, article, or "
            "generation differs"
        )
    return action


def _persist_action(
    layout: RunLayout,
    action: HostActionSeal,
    *,
    active_generation: int,
) -> None:
    path = semantic_review_action_path(layout, active_generation)
    if path.exists():
        try:
            raw = path.read_bytes()
            existing = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise SemanticReviewError(
                "persisted semantic review action is unreadable"
            ) from error
        if raw != canonical_json_bytes(existing) or existing != action.document:
            raise SemanticReviewError("persisted semantic review action changed")
        return
    atomic_write_json(path, action.document)


def load_semantic_review_action(
    layout: RunLayout,
    active_generation: int,
) -> HostActionSeal | None:
    path = semantic_review_action_path(layout, active_generation)
    if not path.exists():
        return None
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
        if raw != canonical_json_bytes(document):
            raise ValueError("action is not canonical")
        action = _seal_action(layout, document)
    except Exception as error:
        if isinstance(error, SemanticReviewError):
            raise
        raise SemanticReviewError(
            "persisted semantic review action is invalid"
        ) from error
    payload = action.document.get("payload")
    if (
        action.document.get("phase_id") != "U11"
        or action.document.get("action_kind") != _ACTION_KIND
        or action.document.get("result_relative_path")
        != semantic_review_result_relative_path(active_generation)
        or not isinstance(payload, Mapping)
        or payload.get("active_generation") != active_generation
    ):
        raise SemanticReviewError(
            "persisted semantic review action generation authority differs"
        )
    return action


def ensure_semantic_review_action(
    layout: RunLayout,
    *,
    request_sha256: str,
    request_intake_authority_sha256: str,
    u10_parent_event_sha256: str,
    active_generation: int,
    article_sha256: str,
    output_plan_artifact_sha256: str,
    coverage_artifact_sha256: str,
    article_review_artifact_sha256: str,
    evidence_ledger_artifact_sha256: str,
    concept_disposition_artifact_sha256: str,
    required_concept_semantic_unit_ids: Collection[str],
    now: datetime,
) -> HostActionSeal:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    payload = _semantic_payload(
        request_intake_authority_sha256=request_intake_authority_sha256,
        active_generation=active_generation,
        article_sha256=article_sha256,
        output_plan_artifact_sha256=output_plan_artifact_sha256,
        coverage_artifact_sha256=coverage_artifact_sha256,
        article_review_artifact_sha256=article_review_artifact_sha256,
        evidence_ledger_artifact_sha256=evidence_ledger_artifact_sha256,
        concept_disposition_artifact_sha256=concept_disposition_artifact_sha256,
        required_concept_semantic_unit_ids=required_concept_semantic_unit_ids,
    )
    persisted = load_semantic_review_action(layout, active_generation)
    pending = load_pending_action(layout)
    if persisted is not None:
        action = _validate_action_authority(
            layout,
            persisted,
            request_sha256=request_sha256,
            u10_parent_event_sha256=u10_parent_event_sha256,
            expected_payload=payload,
        )
        if pending is not None and pending != action:
            raise SemanticReviewError(
                "pending host action differs from semantic review authority"
            )
        if pending is None and not _accepted_path(layout, action).is_file():
            raise SemanticReviewError(
                "persisted semantic review action has neither pending nor accepted result"
            )
        return action
    if pending is not None:
        action = _validate_action_authority(
            layout,
            pending,
            request_sha256=request_sha256,
            u10_parent_event_sha256=u10_parent_event_sha256,
            expected_payload=payload,
        )
        _persist_action(
            layout,
            action,
            active_generation=active_generation,
        )
        return action
    action = issue_host_action(
        layout,
        action_kind=_ACTION_KIND,
        phase_id="U11",
        parent_event_sha256=_sha256(
            u10_parent_event_sha256,
            label="U10 parent event SHA-256",
        ),
        request_sha256=_sha256(request_sha256, label="request SHA-256"),
        payload=payload,
        result_relative_path=semantic_review_result_relative_path(
            active_generation
        ),
        now=now,
    )
    _persist_action(
        layout,
        action,
        active_generation=active_generation,
    )
    return action


def validate_semantic_review_action(
    layout: RunLayout,
    action: HostActionSeal,
    *,
    request_sha256: str,
    request_intake_authority_sha256: str,
    u10_parent_event_sha256: str,
    active_generation: int,
    article_sha256: str,
    output_plan_artifact_sha256: str,
    coverage_artifact_sha256: str,
    article_review_artifact_sha256: str,
    evidence_ledger_artifact_sha256: str,
    concept_disposition_artifact_sha256: str,
    required_concept_semantic_unit_ids: Collection[str],
) -> HostActionSeal:
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    payload = _semantic_payload(
        request_intake_authority_sha256=request_intake_authority_sha256,
        active_generation=active_generation,
        article_sha256=article_sha256,
        output_plan_artifact_sha256=output_plan_artifact_sha256,
        coverage_artifact_sha256=coverage_artifact_sha256,
        article_review_artifact_sha256=article_review_artifact_sha256,
        evidence_ledger_artifact_sha256=evidence_ledger_artifact_sha256,
        concept_disposition_artifact_sha256=concept_disposition_artifact_sha256,
        required_concept_semantic_unit_ids=required_concept_semantic_unit_ids,
    )
    return _validate_action_authority(
        layout,
        action,
        request_sha256=request_sha256,
        u10_parent_event_sha256=u10_parent_event_sha256,
        expected_payload=payload,
    )


def load_accepted_semantic_review_result(
    layout: RunLayout,
    action: HostActionSeal,
) -> HostResultSeal | None:
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    path = _accepted_path(layout, action)
    if not path.exists():
        return None
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
        if raw != canonical_json_bytes(document):
            raise ValueError("accepted receipt is not canonical")
        return _seal_result(layout, action=action, receipt=document)
    except Exception as error:
        raise SemanticReviewError(
            "accepted semantic review receipt is invalid"
        ) from error


def load_host_semantic_review_result(
    layout: RunLayout,
    action: HostActionSeal,
) -> dict[str, object]:
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    try:
        accepted = load_accepted_semantic_review_result(layout, action)
        if accepted is None:
            raise SemanticReviewError(
                "accepted semantic review receipt is unavailable"
            )
        result, raw = _load_bound_result_document(
            layout,
            action=action,
            receipt=accepted.document,
        )
    except Exception as error:
        if isinstance(error, SemanticReviewError):
            raise
        raise SemanticReviewError(
            "host semantic review result is unreadable"
        ) from error
    if raw != canonical_json_bytes(result):
        raise SemanticReviewError(
            "host semantic review result is not canonical"
        )
    return result


def _string_array(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise SemanticReviewError(f"{label} must be a nonempty string array")
    if len(value) != len(set(value)):
        raise SemanticReviewError(f"{label} contains duplicates")
    return copy.deepcopy(value)


def _dimension_rows(
    dimensions: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if not isinstance(dimensions, Sequence) or isinstance(
        dimensions,
        (str, bytes, bytearray),
    ):
        raise SemanticReviewError("semantic review dimensions must be a sequence")
    rows = copy.deepcopy(list(dimensions))
    identifiers = tuple(
        row.get("dimension_id") if isinstance(row, Mapping) else None
        for row in rows
    )
    if identifiers != SEMANTIC_REVIEW_DIMENSIONS:
        raise SemanticReviewError(
            "semantic review dimensions differ from the frozen nine-dimension contract"
        )
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != _DIMENSION_FIELDS:
            raise SemanticReviewError(
                "semantic review dimension contains unknown or runtime-owned fields"
            )
        if row.get("status") not in {"pass", "fail", "blocked"}:
            raise SemanticReviewError("semantic review dimension status is invalid")
        _nonempty(row.get("rationale"), label="semantic review rationale")
        _string_array(row.get("article_spans"), label="article spans")
        _string_array(row.get("authority_refs"), label="authority refs")
    return [dict(row) for row in rows]


def _validate_host_result(
    action: HostActionSeal,
    accepted_result: HostResultSeal,
    host_result: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    if set(host_result) != _HOST_RESULT_FIELDS:
        raise SemanticReviewError(
            "host semantic result contains unknown or runtime-owned fields"
        )
    if (
        host_result.get("schema_id") != _HOST_RESULT_SCHEMA_ID
        or host_result.get("schema_version") != 1
        or host_result.get("action_sha256") != action.action_sha256
    ):
        raise SemanticReviewError("host semantic result action authority differs")
    receipt = accepted_result.document
    if (
        accepted_result.action_sha256 != action.action_sha256
        or receipt.get("action_sha256") != action.action_sha256
        or receipt.get("action_kind") != _ACTION_KIND
        or receipt.get("phase_id") != "U11"
        or receipt.get("execution_status") != "complete"
        or receipt.get("result_sha256")
        != sha256_bytes(canonical_json_bytes(dict(host_result)))
    ):
        raise SemanticReviewError("accepted semantic receipt authority differs")
    provider = receipt.get("provider")
    tool = receipt.get("tool")
    if not isinstance(provider, Mapping) or not isinstance(tool, Mapping):
        raise SemanticReviewError(
            "accepted semantic receipt lacks provider or tool identity"
        )
    payload = action.document.get("payload")
    if not isinstance(payload, Mapping):
        raise SemanticReviewError("semantic review action payload is invalid")
    if (
        provider.get("provider_kind")
        not in payload.get("allowed_provider_kinds", ())
        or tool.get("provider_id") != provider.get("provider_id")
    ):
        raise SemanticReviewError(
            "semantic receipt provider or tool exceeds action authority"
        )
    attempts = receipt.get("attempts")
    if (
        not isinstance(attempts, list)
        or not attempts
        or [item.get("attempt") for item in attempts if isinstance(item, Mapping)]
        != list(range(1, len(attempts) + 1))
        or not isinstance(attempts[-1], Mapping)
        or attempts[-1].get("status") != "success"
    ):
        raise SemanticReviewError(
            "semantic receipt execution attempts are not a completed sequence"
        )
    reviewer = host_result.get("reviewer")
    if not isinstance(reviewer, Mapping) or set(reviewer) != _REVIEWER_FIELDS:
        raise SemanticReviewError("semantic reviewer identity fields are invalid")
    reviewer_snapshot = copy.deepcopy(dict(reviewer))
    for field in ("reviewer_id", "host_id", "provider_id", "model", "execution_id"):
        _nonempty(reviewer_snapshot.get(field), label=f"reviewer {field}")
    if (
        reviewer_snapshot.get("provider_id") != provider.get("provider_id")
        or reviewer_snapshot.get("execution_id") != receipt.get("execution_id")
        or reviewer_snapshot.get("proof_grade")
        not in payload.get("allowed_proof_grades", ())
    ):
        raise SemanticReviewError(
            "semantic reviewer identity differs from accepted host execution"
        )
    reviewed_at = _nonempty(
        host_result.get("reviewed_at"),
        label="semantic review timestamp",
    )
    issued_at = _timestamp(
        action.document.get("issued_at"),
        label="semantic action issue time",
    )
    reviewed_time = _timestamp(
        reviewed_at,
        label="semantic review timestamp",
    )
    completed_at = _timestamp(
        receipt.get("completed_at"),
        label="semantic receipt completion time",
    )
    if not issued_at <= reviewed_time <= completed_at:
        raise SemanticReviewError(
            "semantic review timestamp is outside its issued action execution"
        )
    rows = _dimension_rows(host_result.get("dimension_reviews", []))
    host_snapshot = copy.deepcopy(dict(host_result))
    host_snapshot["reviewed_at"] = reviewed_at
    return host_snapshot, reviewer_snapshot, rows


def project_semantic_review_artifact(
    *,
    action: HostActionSeal,
    accepted_result: HostResultSeal,
    host_result: Mapping[str, object],
    version_binding: Mapping[str, object],
    generated_at: str,
    deterministic_status: str,
    adversarial_status: str,
) -> dict[str, Any]:
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    if not isinstance(accepted_result, HostResultSeal):
        raise TypeError("accepted_result must be a HostResultSeal")
    if not isinstance(host_result, Mapping):
        raise TypeError("host_result must be a mapping")
    if deterministic_status not in {"pass", "fail"} or adversarial_status not in {
        "pass",
        "fail",
    }:
        raise SemanticReviewError("semantic review layer status must be pass or fail")
    host_snapshot, reviewer, rows = _validate_host_result(
        action,
        accepted_result,
        host_result,
    )
    payload = action.document.get("payload")
    provider = accepted_result.document.get("provider")
    tool = accepted_result.document.get("tool")
    if not isinstance(payload, Mapping) or not isinstance(provider, Mapping) or not isinstance(
        tool,
        Mapping,
    ):
        raise SemanticReviewError("semantic review authority projection is invalid")
    semantic_passed = all(row.get("status") == "pass" for row in rows)
    passed = bool(
        deterministic_status == "pass"
        and adversarial_status == "pass"
        and semantic_passed
    )
    artifact: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.semantic-review",
        "schema_version": 1,
        "run_id": str(action.document["run_id"]),
        "version_binding": copy.deepcopy(dict(version_binding)),
        "generated_at": generated_at,
        "phase_id": "U11",
        "request_sha256": str(action.document["request_sha256"]),
        "request_intake_authority_sha256": str(
            payload["request_intake_authority_sha256"]
        ),
        "u10_parent_event_sha256": str(
            action.document["parent_event_sha256"]
        ),
        "active_generation": int(payload["active_generation"]),
        **{
            field: str(payload[field]) for field in _AUTHORITY_HASH_FIELDS
        },
        "required_concept_semantic_unit_ids": copy.deepcopy(
            payload["required_concept_semantic_unit_ids"]
        ),
        "required_concept_semantic_units_sha256": str(
            payload["required_concept_semantic_units_sha256"]
        ),
        "host_action_sha256": action.action_sha256,
        "host_receipt_sha256": accepted_result.receipt_sha256,
        "host_result_sha256": str(accepted_result.document["result_sha256"]),
        "host_execution": {
            "provider": copy.deepcopy(dict(provider)),
            "tool": copy.deepcopy(dict(tool)),
            "execution_id": str(accepted_result.document["execution_id"]),
            "completed_at": str(accepted_result.document["completed_at"]),
        },
        "reviewer": reviewer,
        "dimension_reviews": rows,
        "deterministic_status": deterministic_status,
        "adversarial_status": adversarial_status,
        "overall_status": "pass" if passed else "fail",
        "publication_allowed": passed,
        "reviewed_at": str(host_snapshot["reviewed_at"]),
    }
    artifact["content_sha256"] = compute_artifact_content_sha256(artifact)
    try:
        return validate_phase_artifact(
            "ultra-semantic-review.schema.json",
            artifact,
            expected_schema_id="crossframe.ultra.v82.semantic-review",
            expected_run_id=str(action.document["run_id"]),
            expected_version_binding=version_binding,
            expected_phase_id="U11",
        )
    except (UltraRuntimeError, ValidationError, TypeError, ValueError) as error:
        raise SemanticReviewError(f"invalid semantic review projection: {error}") from error


def validate_host_semantic_result_for_acceptance(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
    result_document: Mapping[str, object] | None = None,
) -> None:
    if result_document is None:
        try:
            host_result, _ = _load_bound_result_document(
                layout,
                action=action,
                receipt=result.document,
            )
        except Exception as error:
            raise SemanticReviewError(
                "host semantic review result is unreadable"
            ) from error
    else:
        host_result = copy.deepcopy(dict(result_document))
    _validate_host_result(action, result, host_result)


def validate_semantic_review(
    document: Mapping[str, object],
    *,
    action: HostActionSeal,
    accepted_result: HostResultSeal,
    host_result: Mapping[str, object],
    version_binding: Mapping[str, object],
    expected_deterministic_status: str,
    expected_adversarial_status: str,
) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise TypeError("semantic review document must be a mapping")
    generated_at = document.get("generated_at")
    if not isinstance(generated_at, str):
        raise SemanticReviewError("semantic review generated_at is unavailable")
    expected = project_semantic_review_artifact(
        action=action,
        accepted_result=accepted_result,
        host_result=host_result,
        version_binding=version_binding,
        generated_at=generated_at,
        deterministic_status=expected_deterministic_status,
        adversarial_status=expected_adversarial_status,
    )
    snapshot = copy.deepcopy(dict(document))
    if snapshot != expected:
        raise SemanticReviewError(
            "semantic review artifact differs from accepted host receipt or current authority"
        )
    return expected


__all__ = (
    "SEMANTIC_REVIEW_DIMENSIONS",
    "SemanticReviewError",
    "ensure_semantic_review_action",
    "load_accepted_semantic_review_result",
    "load_host_semantic_review_result",
    "load_semantic_review_action",
    "project_semantic_review_artifact",
    "required_units_sha256",
    "semantic_review_action_path",
    "semantic_review_result_relative_path",
    "validate_required_concept_units",
    "validate_host_semantic_result_for_acceptance",
    "validate_semantic_review",
    "validate_semantic_review_action",
)
