from __future__ import annotations

import copy
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
from typing import Callable, Mapping, Sequence, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jsonschema import ValidationError

from .jsonio import (
    atomic_write_json,
    canonical_json_bytes,
    load_json_object_bytes,
    sha256_bytes,
)
from .schemas import validate_instance


_T = TypeVar("_T")
_SENSITIVITIES = frozenset({"public", "internal", "private", "restricted"})
_OUTBOUND_PERMISSIONS = frozenset({"allowed", "deidentified-only", "denied"})
_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "url",
        "event_date",
        "publication_date",
        "interest",
        "upstream_lineage",
        "supported_claim",
        "cannot_prove",
    }
)
_HOSTILE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"override\s+(?:the\s+)?(?:system|developer|tool)\s+(?:prompt|policy)",
        r"change\s+(?:the\s+)?(?:root|version|phase|tool\s+policy)",
        r"execute\s+(?:this\s+)?(?:script|macro|command)",
        r"download\s+and\s+(?:run|execute)",
    )
)


class RetrievalPolicyError(ValueError):
    """Raised when retrieval qualification or privacy policy is incomplete."""


class RateLimitError(RuntimeError):
    """A retryable retrieval rate limit."""


class RetrievalTimeoutError(RuntimeError):
    """A retryable retrieval timeout."""


@dataclass(frozen=True, init=False)
class RetrievalDecision:
    status: str
    reason: str
    decision_sha256: str
    _document: dict[str, object]
    _boundary: dict[str, object]
    _issuer_token: str
    _seal_sha256: str

    @property
    def document(self) -> dict[str, object]:
        return copy.deepcopy(self._document)


@dataclass(frozen=True, init=False)
class PureLogicEligibilityAuthority:
    _document: dict[str, object]
    _boundary: dict[str, object]
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class RetrievalAuthorization:
    status: str
    reason: str
    decision_sha256: str
    authorization_sha256: str
    block_result: dict[str, str] | None
    network_available: bool
    outbound_authorized: bool
    _boundary: dict[str, object]
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class RetrievalLedgerSeal:
    run_id: str
    version_binding: dict[str, object]
    u1_parent_event_sha256: str
    request_sha256: str
    decision_sha256: str
    authorization_sha256: str | None
    content_sha256: str
    artifact_sha256: str
    retrieval_status: str
    completion_authorized: bool
    disposition_sha256: str
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class PreparedQuery:
    eligibility_status: str
    redacted_query: str
    query_sha256: str
    eligibility_decision_sha256: str
    authorization_sha256: str
    u1_parent_event_sha256: str
    request_sha256: str
    run_id: str
    version_binding: dict[str, object]
    _document: dict[str, object]
    _boundary: dict[str, object]
    _issuer_token: str
    _seal_sha256: str

    @property
    def document(self) -> dict[str, object]:
        return copy.deepcopy(self._document)

    def __getitem__(self, key: str) -> object:
        return copy.deepcopy(self._document[key])


@dataclass(frozen=True, init=False)
class RetrievalResult:
    status: str
    attempts: tuple[dict[str, object], ...]
    value: object | None = None
    _boundary: dict[str, object]
    _authorization_sha256: str
    _query_key: tuple[str, str, str, str, str, str]
    _round_state: dict[str, object] | None
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class ResourceStatus:
    status: str
    checkpoint: dict[str, object]
    deleted: bool
    _boundary: dict[str, object]
    _authorization_sha256: str
    _query_key: tuple[str, str, str, str, str, str]
    _measured_root: str
    _free_bytes: int | None
    _reserve_bytes: int
    _issuer_token: str
    _seal_sha256: str


_ISSUED_DECISIONS: dict[str, str] = {}
_ISSUED_PURE_LOGIC_AUTHORITIES: dict[str, str] = {}
_ISSUED_AUTHORIZATIONS: dict[str, str] = {}
_ISSUED_QUERIES: dict[str, str] = {}
_ISSUED_LEDGER_SEALS: dict[str, str] = {}
_ISSUED_RETRIEVAL_RESULTS: dict[str, str] = {}
_ISSUED_RESOURCE_STATUSES: dict[str, str] = {}
_DECISION_AUTHORITIES: dict[str, dict[str, object]] = {}
_AUTHORIZATION_AUTHORITIES: dict[str, dict[str, object]] = {}
_QUERY_AUTHORITIES: dict[
    tuple[str, str, str, str, str, str], dict[str, object]
] = {}
_LEDGER_DISPOSITIONS: dict[str, dict[str, dict[str, object]]] = {}
_TRIGGER_KINDS = frozenset(
    {
        "real-world",
        "time-sensitive",
        "legal",
        "medical",
        "financial",
        "political",
        "product",
        "policy",
        "institutional",
        "current-fact",
    }
)
_SUBAGENT_CANDIDATE_ROLES = frozenset(
    {
        "source-discovery",
        "counterexample",
        "affected-position",
        "source-lineage",
        "calibration",
    }
)
_RETRIEVAL_ACTION_RELATIVE_PATH = "u2-authority/retrieval-action.json"
_RETRIEVAL_RESULT_RELATIVE_PATH = "work/host/U02-retrieval-result.json"
_ADMITTED_HOST_RESULT_RELATIVE_PATH = "u2-authority/admitted-host-result.json"


def _hash_without(value: Mapping[str, object], field: str) -> str:
    payload = copy.deepcopy(dict(value))
    payload.pop(field, None)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _snapshot_sha256(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(copy.deepcopy(dict(value)))).hexdigest()


def _issue_snapshot(registry: dict[str, str], value: Mapping[str, object]) -> tuple[str, str]:
    token = hashlib.sha256(os.urandom(32)).hexdigest()
    seal_sha256 = _snapshot_sha256(value)
    registry[token] = seal_sha256
    return token, seal_sha256


def _boundary_document(phase_store: object) -> dict[str, object]:
    from .state_machine import (
        PhaseIntegrityError,
        PhaseStore,
        PhaseTransitionError,
        RetrievalBoundary,
        verify_retrieval_boundary,
    )

    if not isinstance(phase_store, PhaseStore):
        raise RetrievalPolicyError("retrieval requires a sealed PhaseStore U1 authority")
    if phase_store.terminal:
        raise RetrievalPolicyError("terminal run cannot produce or consume retrieval authority")
    if phase_store.current_phase != "U1" or not phase_store.has_valid_u1_source_coverage:
        raise RetrievalPolicyError("retrieval requires completed sealed U1 authority")
    try:
        boundary = verify_retrieval_boundary(phase_store.retrieval_boundary)
    except (PhaseIntegrityError, PhaseTransitionError) as error:
        raise RetrievalPolicyError("retrieval boundary authority is invalid") from error
    if not isinstance(boundary, RetrievalBoundary):
        raise RetrievalPolicyError("retrieval boundary is not issuer-produced")
    return {
        "run_id": boundary.run_id,
        "version_binding": copy.deepcopy(boundary.version_binding),
        "u1_parent_event_sha256": boundary.u1_parent_event_sha256,
        "request_sha256": boundary.request_sha256,
        "run_contract_sha256": boundary.run_contract_sha256,
        "network_available": boundary.network_available,
        "outbound_permission": boundary.outbound_permission,
        "sensitivity": boundary.sensitivity,
        "acl_status": boundary.acl_status,
        "run_mode": boundary.run_mode,
        "input_snapshot_sha256": boundary.input_snapshot_sha256,
        "input_artifact_hashes": list(boundary.input_artifact_hashes),
        "inputs": copy.deepcopy(list(boundary.inputs)),
        "input_root": str(boundary.input_root.resolve()),
        "maximum_tool_retries": boundary.maximum_tool_retries,
        "maximum_retrieval_rounds_without_material_novelty": (
            boundary.maximum_retrieval_rounds_without_material_novelty
        ),
        "expected_eligibility_basis_sha256": (
            boundary.expected_eligibility_basis_sha256
        ),
        "boundary_seal_sha256": boundary._seal_sha256,
    }


def _decision_snapshot(
    decision: RetrievalDecision,
) -> dict[str, object]:
    return {
        "status": decision.status,
        "reason": decision.reason,
        "decision_sha256": decision.decision_sha256,
        "document": copy.deepcopy(decision._document),
        "boundary": copy.deepcopy(decision._boundary),
    }


def _issue_decision(
    document: Mapping[str, object], boundary: Mapping[str, object]
) -> RetrievalDecision:
    decision = object.__new__(RetrievalDecision)
    object.__setattr__(decision, "status", str(document["status"]))
    object.__setattr__(decision, "reason", str(document["reason"]))
    object.__setattr__(decision, "decision_sha256", str(document["decision_sha256"]))
    object.__setattr__(decision, "_document", copy.deepcopy(dict(document)))
    object.__setattr__(decision, "_boundary", copy.deepcopy(dict(boundary)))
    token, seal_sha256 = _issue_snapshot(_ISSUED_DECISIONS, _decision_snapshot(decision))
    object.__setattr__(decision, "_issuer_token", token)
    object.__setattr__(decision, "_seal_sha256", seal_sha256)
    _DECISION_AUTHORITIES[decision.decision_sha256] = _decision_snapshot(decision)
    return decision


def _valid_decision(decision: object) -> bool:
    if not isinstance(decision, RetrievalDecision):
        return False
    try:
        document = decision._document
        basis = document["eligibility_basis"]
        issued = _ISSUED_DECISIONS.get(decision._issuer_token)
        computed = _snapshot_sha256(_decision_snapshot(decision))
        return bool(
            issued
            and decision._seal_sha256 == issued == computed
            and decision.status == document.get("status")
            and decision.reason == document.get("reason")
            and decision.decision_sha256 == document.get("decision_sha256")
            and decision.decision_sha256
            == _hash_without(document, "decision_sha256")
            and isinstance(basis, Mapping)
            and document.get("basis_sha256") == basis.get("basis_sha256")
            and basis.get("basis_sha256") == _hash_without(basis, "basis_sha256")
            and document.get("claim_sha256") == basis.get("claim_sha256")
            and basis.get("claim_sha256")
            == hashlib.sha256(str(basis.get("claim", "")).encode("utf-8")).hexdigest()
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def _authorization_snapshot(
    authorization: RetrievalAuthorization,
) -> dict[str, object]:
    return {
        "status": authorization.status,
        "reason": authorization.reason,
        "decision_sha256": authorization.decision_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "block_result": copy.deepcopy(authorization.block_result),
        "network_available": authorization.network_available,
        "outbound_authorized": authorization.outbound_authorized,
        "boundary": copy.deepcopy(authorization._boundary),
    }


def _valid_authorization(authorization: object) -> bool:
    if not isinstance(authorization, RetrievalAuthorization):
        return False
    try:
        issued = _ISSUED_AUTHORIZATIONS.get(authorization._issuer_token)
        computed = _snapshot_sha256(_authorization_snapshot(authorization))
        return bool(
            issued
            and authorization._seal_sha256 == issued == computed
            and authorization.status in {"authorized", "blocked"}
            and authorization.outbound_authorized
            == (authorization.status == "authorized")
            and (authorization.block_result is None)
            == (authorization.status == "authorized")
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _issue_authorization(
    decision: RetrievalDecision,
    boundary: Mapping[str, object],
    *,
    status: str,
    reason: str,
    block_result: dict[str, str] | None,
) -> RetrievalAuthorization:
    payload = {
        "authorization_type": "crossframe.ultra.v82.retrieval-authorization",
        "decision_sha256": decision.decision_sha256,
        "run_id": boundary["run_id"],
        "version_binding": copy.deepcopy(boundary["version_binding"]),
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "run_contract_sha256": boundary["run_contract_sha256"],
        "acl_status": boundary["acl_status"],
        "network_available": boundary["network_available"],
        "outbound_permission": boundary["outbound_permission"],
        "status": status,
        "reason": reason,
        "block_result": block_result,
    }
    authorization_sha256 = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    authorization = object.__new__(RetrievalAuthorization)
    object.__setattr__(authorization, "status", status)
    object.__setattr__(authorization, "reason", reason)
    object.__setattr__(authorization, "decision_sha256", decision.decision_sha256)
    object.__setattr__(authorization, "authorization_sha256", authorization_sha256)
    object.__setattr__(authorization, "block_result", copy.deepcopy(block_result))
    object.__setattr__(authorization, "network_available", bool(boundary["network_available"]))
    object.__setattr__(
        authorization,
        "outbound_authorized",
        status == "authorized",
    )
    object.__setattr__(authorization, "_boundary", copy.deepcopy(dict(boundary)))
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_AUTHORIZATIONS, _authorization_snapshot(authorization)
    )
    object.__setattr__(authorization, "_issuer_token", token)
    object.__setattr__(authorization, "_seal_sha256", seal_sha256)
    _AUTHORIZATION_AUTHORITIES[
        authorization.authorization_sha256
    ] = _authorization_snapshot(authorization)
    return authorization


def _nonempty(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrievalPolicyError(f"{field} must be a non-empty string")
    return value


def _pure_logic_authority_snapshot(
    authority: PureLogicEligibilityAuthority,
) -> dict[str, object]:
    return {
        "document": copy.deepcopy(authority._document),
        "boundary": copy.deepcopy(authority._boundary),
    }


def _valid_pure_logic_authority(authority: object) -> bool:
    if not isinstance(authority, PureLogicEligibilityAuthority):
        return False
    try:
        issued = _ISSUED_PURE_LOGIC_AUTHORITIES.get(authority._issuer_token)
        computed = _snapshot_sha256(_pure_logic_authority_snapshot(authority))
        return bool(issued and authority._seal_sha256 == issued == computed)
    except (AttributeError, TypeError, ValueError):
        return False


def validate_pure_logic_eligibility_basis(
    basis: Mapping[str, object],
    *,
    phase_store: object,
) -> PureLogicEligibilityAuthority:
    boundary = _boundary_document(phase_store)
    expected_sha256 = boundary.get("expected_eligibility_basis_sha256")
    if not isinstance(expected_sha256, str) or re.fullmatch(
        r"[0-9a-f]{64}", expected_sha256
    ) is None:
        raise RetrievalPolicyError(
            "pure-logic basis requires independent control-plane authority"
        )
    if not isinstance(basis, Mapping):
        raise RetrievalPolicyError("pure-logic eligibility basis must be an object")
    document = copy.deepcopy(dict(basis))
    required = {
        "analysis_kind",
        "claim",
        "claim_sha256",
        "run_id",
        "u1_parent_event_sha256",
        "request_sha256",
        "version_binding",
        "material_inventory",
        "material_universe_sha256",
        "basis_sha256",
    }
    claim = document.get("claim")
    if set(document) != required or not isinstance(claim, str) or not claim.strip():
        raise RetrievalPolicyError("pure-logic eligibility basis fields are not closed")
    recomputed = _hash_without(document, "basis_sha256")
    if (
        document.get("analysis_kind") != "pure-logic"
        or document.get("claim_sha256")
        != hashlib.sha256(claim.encode("utf-8")).hexdigest()
        or document.get("run_id") != boundary["run_id"]
        or document.get("u1_parent_event_sha256")
        != boundary["u1_parent_event_sha256"]
        or document.get("request_sha256") != boundary["request_sha256"]
        or document.get("version_binding") != boundary["version_binding"]
        or document.get("material_inventory") != []
        or document.get("material_universe_sha256") is not None
        or document.get("basis_sha256") != recomputed
        or recomputed != expected_sha256
    ):
        raise RetrievalPolicyError(
            "pure-logic basis differs from expected control-plane authority"
        )
    authority = object.__new__(PureLogicEligibilityAuthority)
    object.__setattr__(authority, "_document", document)
    object.__setattr__(authority, "_boundary", copy.deepcopy(boundary))
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_PURE_LOGIC_AUTHORITIES,
        _pure_logic_authority_snapshot(authority),
    )
    object.__setattr__(authority, "_issuer_token", token)
    object.__setattr__(authority, "_seal_sha256", seal_sha256)
    return authority


def assess_retrieval_eligibility(
    claim: str,
    *,
    phase_store: object,
    analysis_kind: str | None = None,
    trigger_kinds: Sequence[str] | None = None,
    pure_logic: bool = False,
    material_inventory: Sequence[Mapping[str, object]] | None = None,
    material_universe_sha256: str | None = None,
    eligibility_basis_authority: PureLogicEligibilityAuthority | None = None,
) -> RetrievalDecision:
    boundary = _boundary_document(phase_store)
    claim_text = _nonempty(claim, field="claim")
    if not isinstance(pure_logic, bool):
        raise RetrievalPolicyError("pure_logic must be boolean")
    claim_sha256 = hashlib.sha256(claim_text.encode("utf-8")).hexdigest()
    if eligibility_basis_authority is not None:
        if (
            pure_logic
            or trigger_kinds
            or material_inventory is not None
            or material_universe_sha256 is not None
            or not _valid_pure_logic_authority(eligibility_basis_authority)
        ):
            raise RetrievalPolicyError("pure-logic authority cannot be caller-selected")
        assert isinstance(eligibility_basis_authority, PureLogicEligibilityAuthority)
        if (
            eligibility_basis_authority._boundary != boundary
            or eligibility_basis_authority._document.get("claim") != claim_text
            or eligibility_basis_authority._document.get("claim_sha256")
            != claim_sha256
        ):
            raise RetrievalPolicyError("pure-logic authority differs from the claim or run")
        basis = copy.deepcopy(eligibility_basis_authority._document)
        status = "not-applicable"
        reason = "pure-logic"
    elif pure_logic and boundary["run_mode"] == "test":
        if trigger_kinds or material_inventory or material_universe_sha256 is not None:
            raise RetrievalPolicyError("pure logic cannot carry retrieval or material authority")
        basis: dict[str, object] = {
            "analysis_kind": "pure-logic",
            "claim": claim_text,
            "claim_sha256": claim_sha256,
            "run_id": boundary["run_id"],
            "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
            "request_sha256": boundary["request_sha256"],
            "version_binding": copy.deepcopy(boundary["version_binding"]),
            "material_inventory": [],
            "material_universe_sha256": None,
        }
        status = "not-applicable"
        reason = "pure-logic"
    else:
        contract = getattr(phase_store, "run_contract", None)
        expected_analysis_kind = (
            contract.get("analysis_kind") if isinstance(contract, Mapping) else None
        )
        selected_analysis_kind = analysis_kind or expected_analysis_kind
        if (
            expected_analysis_kind not in {"open-world", "closed-input"}
            or selected_analysis_kind != expected_analysis_kind
        ):
            raise RetrievalPolicyError(
                "retrieval analysis kind differs from the sealed run contract"
            )
        has_material_authority = (
            material_inventory is not None or material_universe_sha256 is not None
        )
        normalized_inventory: list[dict[str, object]] = []
        if has_material_authority:
            if (
                not material_inventory
                or not isinstance(material_universe_sha256, str)
                or not re.fullmatch(r"[0-9a-f]{64}", material_universe_sha256)
                or any(not isinstance(item, Mapping) for item in material_inventory)
            ):
                raise RetrievalPolicyError(
                    "material authority requires a complete sealed inventory"
                )
            normalized_inventory = [
                copy.deepcopy(dict(item)) for item in material_inventory
            ]
            boundary_inputs = boundary["inputs"]
            paths = [item.get("path") for item in normalized_inventory]
            if (
                len(paths) != len(set(paths))
                or any(item not in boundary_inputs for item in normalized_inventory)
                or hashlib.sha256(canonical_json_bytes(normalized_inventory)).hexdigest()
                != material_universe_sha256
            ):
                raise RetrievalPolicyError(
                    "material authority is not a sealed U1 input subset"
                )
        if selected_analysis_kind == "closed-input":
            if not has_material_authority:
                raise RetrievalPolicyError(
                    "closed input requires complete material authority"
                )
            if trigger_kinds:
                raise RetrievalPolicyError(
                    "closed input cannot carry external retrieval triggers"
                )
            basis = {
                "analysis_kind": "closed-input",
                "claim": claim_text,
                "claim_sha256": claim_sha256,
                "run_id": boundary["run_id"],
                "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
                "request_sha256": boundary["request_sha256"],
                "version_binding": copy.deepcopy(boundary["version_binding"]),
                "material_inventory": normalized_inventory,
                "material_universe_sha256": material_universe_sha256,
            }
            status = "not-applicable"
            reason = "closed-input"
        else:
            kinds = tuple(trigger_kinds or ("real-world",))
            if (
                not kinds
                or len(kinds) != len(set(kinds))
                or any(kind not in _TRIGGER_KINDS for kind in kinds)
            ):
                raise RetrievalPolicyError("retrieval trigger kinds are invalid")
            basis = {
                "trigger_kinds": list(kinds),
                "claim": claim_text,
                "claim_sha256": claim_sha256,
                "run_id": boundary["run_id"],
                "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
                "request_sha256": boundary["request_sha256"],
                "version_binding": copy.deepcopy(boundary["version_binding"]),
            }
            status = "required"
            reason = "explicit-trigger"
    basis["basis_sha256"] = _hash_without(basis, "basis_sha256")
    document: dict[str, object] = {
        "status": status,
        "reason": reason,
        "run_id": boundary["run_id"],
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "version_binding": copy.deepcopy(boundary["version_binding"]),
        "claim_sha256": claim_sha256,
        "basis_sha256": basis["basis_sha256"],
        "eligibility_basis": basis,
    }
    document["decision_sha256"] = _hash_without(document, "decision_sha256")
    return _issue_decision(document, boundary)


def gate_retrieval(
    decision: RetrievalDecision,
    *,
    phase_store: object,
) -> RetrievalDecision | RetrievalAuthorization:
    boundary = _boundary_document(phase_store)
    if not _valid_decision(decision):
        raise RetrievalPolicyError("retrieval eligibility must be recorded first")
    if decision._boundary != boundary:
        raise RetrievalPolicyError("retrieval decision differs from current sealed boundary")
    for field in ("run_id", "version_binding", "u1_parent_event_sha256", "request_sha256"):
        if decision._document.get(field) != boundary[field]:
            raise RetrievalPolicyError("retrieval decision differs from sealed U1 authority")
    if decision.status == "not-applicable":
        return decision
    if decision.status != "required":
        raise RetrievalPolicyError("retrieval decision has an unknown status")
    if boundary["sensitivity"] not in _SENSITIVITIES or boundary["outbound_permission"] not in _OUTBOUND_PERMISSIONS:
        raise RetrievalPolicyError("run context has an invalid outbound policy")
    if not boundary["network_available"]:
        return _issue_authorization(
            decision,
            boundary,
            status="blocked",
            reason="required-network-unavailable",
            block_result={"block_class": "network-unavailable", "detail": "network capability is unavailable"},
        )
    if boundary["outbound_permission"] == "denied" or boundary["acl_status"] != "verified-current-user":
        return _issue_authorization(
            decision,
            boundary,
            status="blocked",
            reason="required-outbound-disallowed",
            block_result={"block_class": "outbound-denied", "detail": "sealed U1 privacy authority denies outbound retrieval"},
        )
    return _issue_authorization(
        decision,
        boundary,
        status="authorized",
        reason=decision.reason,
        block_result=None,
    )


def redact_query(query: str) -> str:
    redacted = _nonempty(query, field="query")
    redacted = re.sub(r"(?i)(?:[a-z]:\\|\\\\)[^\s,;]+", "[REDACTED-PATH]", redacted)
    redacted = re.sub(r"(?<![A-Za-z0-9._-])/(?!/)[^\s,;]+", "[REDACTED-PATH]", redacted)
    redacted = re.sub(r"(?<!\w)~/[^\s,;]+", "[REDACTED-PATH]", redacted)
    redacted = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED-EMAIL]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "[REDACTED-NAME]", redacted)
    redacted = re.sub(r"\b(?:secret|token|api[_-]?key|password|authorization)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+", "[REDACTED-SECRET]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\b(?:sk|ghp|glpat|xox[baprs])[-_][A-Za-z0-9_-]{12,}\b", "[REDACTED-SECRET]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\b(?:ID|SSN|customer[-_ ]?id)\s*[-:=]?\s*[A-Za-z0-9-]{4,}\b", "[REDACTED-ID]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"(?<!\d)\d{17}[\dXx](?![\dXx])", "[REDACTED-CHINA-ID]", redacted)
    redacted = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[REDACTED-PHONE]", redacted)
    redacted = re.sub(r"\b[\w .-]+\.(?:pdf|docx|xlsx|pptx|txt|csv|zip)\b", "[REDACTED-FILE]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"[^。！？\n]*(?:私人|私密|保密|机密)[^。！？\n]*", "[REDACTED-PRIVATE-TEXT]", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    return redacted or "[REDACTED]"


def prepare_query(
    authorization: RetrievalAuthorization | None,
    query: str,
    *,
    phase_store: object,
) -> PreparedQuery:
    boundary = _boundary_document(phase_store)
    if not _valid_authorization(authorization):
        raise RetrievalPolicyError("retrieval authorization is required before a query")
    assert isinstance(authorization, RetrievalAuthorization)
    if authorization._boundary != boundary:
        raise RetrievalPolicyError("retrieval authorization differs from current authority")
    if authorization.status != "authorized":
        raise RetrievalPolicyError("blocked retrieval authorization cannot prepare a query")
    if hostile_instruction_detected(query):
        raise RetrievalPolicyError("query contains a hostile instruction")
    redacted = redact_query(query)
    document: dict[str, object] = {
        "eligibility_status": "required",
        "redacted_query": redacted,
        "query_sha256": hashlib.sha256(redacted.encode("utf-8")).hexdigest(),
        "eligibility_decision_sha256": authorization.decision_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "run_id": boundary["run_id"],
        "version_binding": copy.deepcopy(boundary["version_binding"]),
    }
    prepared = object.__new__(PreparedQuery)
    for field, value in document.items():
        object.__setattr__(prepared, field, copy.deepcopy(value))
    object.__setattr__(prepared, "_document", copy.deepcopy(document))
    object.__setattr__(prepared, "_boundary", copy.deepcopy(boundary))
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_QUERIES, _prepared_query_snapshot(prepared)
    )
    object.__setattr__(prepared, "_issuer_token", token)
    object.__setattr__(prepared, "_seal_sha256", seal_sha256)
    _QUERY_AUTHORITIES[_prepared_query_authority_key(prepared)] = (
        _prepared_query_snapshot(prepared)
    )
    return prepared


def _prepared_query_authority_key(
    query: PreparedQuery | Mapping[str, object],
) -> tuple[str, str, str, str, str, str]:
    getter = query.get if isinstance(query, Mapping) else lambda field: getattr(query, field)
    return tuple(
        str(getter(field))
        for field in (
            "run_id",
            "u1_parent_event_sha256",
            "request_sha256",
            "eligibility_decision_sha256",
            "authorization_sha256",
            "query_sha256",
        )
    )


def _prepared_query_snapshot(query: PreparedQuery) -> dict[str, object]:
    return {
        "eligibility_status": query.eligibility_status,
        "redacted_query": query.redacted_query,
        "query_sha256": query.query_sha256,
        "eligibility_decision_sha256": query.eligibility_decision_sha256,
        "authorization_sha256": query.authorization_sha256,
        "u1_parent_event_sha256": query.u1_parent_event_sha256,
        "request_sha256": query.request_sha256,
        "run_id": query.run_id,
        "version_binding": copy.deepcopy(query.version_binding),
        "document": copy.deepcopy(query._document),
        "boundary": copy.deepcopy(query._boundary),
    }


def _valid_prepared_query(query: object) -> bool:
    if not isinstance(query, PreparedQuery):
        return False
    try:
        issued = _ISSUED_QUERIES.get(query._issuer_token)
        computed = _snapshot_sha256(_prepared_query_snapshot(query))
        public = {
            field: copy.deepcopy(getattr(query, field))
            for field in (
                "eligibility_status",
                "redacted_query",
                "query_sha256",
                "eligibility_decision_sha256",
                "authorization_sha256",
                "u1_parent_event_sha256",
                "request_sha256",
                "run_id",
                "version_binding",
            )
        }
        return bool(
            issued
            and query._seal_sha256 == issued == computed
            and query._document == public
            and query.eligibility_status == "required"
            and query.query_sha256
            == hashlib.sha256(query.redacted_query.encode("utf-8")).hexdigest()
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _validate_execution_authority(
    authorization: object,
    prepared_query: object,
    *,
    phase_store: object,
) -> tuple[RetrievalAuthorization, PreparedQuery, dict[str, object]]:
    boundary = _boundary_document(phase_store)
    if not _valid_authorization(authorization):
        raise RetrievalPolicyError("issuer-verified retrieval authorization is required")
    if not isinstance(authorization, RetrievalAuthorization) or authorization.status != "authorized":
        raise RetrievalPolicyError("blocked retrieval authorization cannot execute")
    if authorization._boundary != boundary:
        raise RetrievalPolicyError("retrieval authorization is stale")
    if not _valid_prepared_query(prepared_query):
        raise RetrievalPolicyError("issuer-verified prepared query is required")
    assert isinstance(prepared_query, PreparedQuery)
    if prepared_query._boundary != boundary:
        raise RetrievalPolicyError("prepared query is stale")
    if (
        prepared_query.authorization_sha256 != authorization.authorization_sha256
        or prepared_query.eligibility_decision_sha256 != authorization.decision_sha256
        or prepared_query.run_id != boundary["run_id"]
        or prepared_query.version_binding != boundary["version_binding"]
        or prepared_query.u1_parent_event_sha256
        != boundary["u1_parent_event_sha256"]
        or prepared_query.request_sha256 != boundary["request_sha256"]
    ):
        raise RetrievalPolicyError("prepared query differs from retrieval authorization")
    return authorization, prepared_query, boundary


def hostile_instruction_detected(content: str) -> bool:
    if not isinstance(content, str):
        raise RetrievalPolicyError("external content must be text")
    return any(pattern.search(content) is not None for pattern in _HOSTILE_PATTERNS)


def store_external_content(content: str) -> dict[str, object]:
    if not isinstance(content, str):
        raise RetrievalPolicyError("external content must be text")
    return {
        "trust": "untrusted",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "hostile_instruction": hostile_instruction_detected(content),
    }


def apply_external_content_policy(
    record: Mapping[str, object],
    *,
    phase: str | None = None,
    control: Mapping[str, object] | None = None,
) -> object:
    if not isinstance(record, Mapping) or record.get("trust") != "untrusted":
        raise RetrievalPolicyError("external content must be stored as untrusted data")
    if (phase is None) == (control is None):
        raise RetrievalPolicyError("provide exactly one host-owned control value")
    if phase is not None:
        return _nonempty(phase, field="phase")
    if not isinstance(control, Mapping):
        raise RetrievalPolicyError("control must be an object")
    return copy.deepcopy(dict(control))


def _retrieval_result_snapshot(result: RetrievalResult) -> dict[str, object]:
    return {
        "status": result.status,
        "attempts": copy.deepcopy(list(result.attempts)),
        "value": copy.deepcopy(result.value),
        "boundary": copy.deepcopy(result._boundary),
        "authorization_sha256": result._authorization_sha256,
        "query_key": list(result._query_key),
        "round_state": copy.deepcopy(result._round_state),
    }


def _issue_retrieval_result(
    *,
    status: str,
    attempts: Sequence[Mapping[str, object]],
    value: object | None,
    boundary: Mapping[str, object],
    authorization: RetrievalAuthorization,
    query: PreparedQuery,
    round_state: Mapping[str, object] | None,
) -> RetrievalResult:
    result = object.__new__(RetrievalResult)
    object.__setattr__(result, "status", status)
    object.__setattr__(
        result,
        "attempts",
        tuple(copy.deepcopy(dict(attempt)) for attempt in attempts),
    )
    object.__setattr__(result, "value", copy.deepcopy(value))
    object.__setattr__(result, "_boundary", copy.deepcopy(dict(boundary)))
    object.__setattr__(
        result, "_authorization_sha256", authorization.authorization_sha256
    )
    object.__setattr__(result, "_query_key", _prepared_query_authority_key(query))
    object.__setattr__(
        result,
        "_round_state",
        copy.deepcopy(dict(round_state)) if round_state is not None else None,
    )
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_RETRIEVAL_RESULTS,
        _retrieval_result_snapshot(result),
    )
    object.__setattr__(result, "_issuer_token", token)
    object.__setattr__(result, "_seal_sha256", seal_sha256)
    return result


def _valid_retrieval_result(
    result: object,
    *,
    boundary: Mapping[str, object],
    authorization: RetrievalAuthorization,
    query_keys: set[tuple[str, str, str, str, str, str]],
) -> bool:
    if not isinstance(result, RetrievalResult):
        return False
    try:
        issued = _ISSUED_RETRIEVAL_RESULTS.get(result._issuer_token)
        return bool(
            issued
            and result._seal_sha256
            == issued
            == _snapshot_sha256(_retrieval_result_snapshot(result))
            and result.status in {"complete", "blocked", "needs_attention"}
            and result._boundary == boundary
            and result._authorization_sha256
            == authorization.authorization_sha256
            and result._query_key in query_keys
        )
    except (AttributeError, TypeError, ValueError):
        return False


def bounded_retrieve(
    operation: Callable[[str], _T],
    *,
    authorization: RetrievalAuthorization | None,
    prepared_query: PreparedQuery | None,
    phase_store: object,
) -> RetrievalResult:
    if not callable(operation):
        raise TypeError("operation must be callable")
    _, verified_query, boundary = _validate_execution_authority(
        authorization,
        prepared_query,
        phase_store=phase_store,
    )
    from .state_machine import PhaseIntegrityError, PhaseTransitionError

    try:
        if not phase_store.retrieval_round_available():
            return _issue_retrieval_result(
                status="needs_attention",
                attempts=(),
                value=None,
                boundary=boundary,
                authorization=authorization,
                query=verified_query,
                round_state={"needs_attention": True},
            )
    except (PhaseIntegrityError, PhaseTransitionError) as error:
        raise RetrievalPolicyError("retrieval session authority is unavailable") from error
    attempts: list[dict[str, object]] = []
    maximum_attempts = int(boundary["maximum_tool_retries"])
    for attempt_number in range(1, maximum_attempts + 1):
        _, verified_query, current_boundary = _validate_execution_authority(
            authorization,
            prepared_query,
            phase_store=phase_store,
        )
        if current_boundary != boundary:
            raise RetrievalPolicyError("retrieval boundary changed before execution")
        try:
            if not phase_store.retrieval_round_available():
                return _issue_retrieval_result(
                    status="needs_attention",
                    attempts=attempts,
                    value=None,
                    boundary=boundary,
                    authorization=authorization,
                    query=verified_query,
                    round_state={"needs_attention": True},
                )
        except (PhaseIntegrityError, PhaseTransitionError) as error:
            raise RetrievalPolicyError("retrieval session authority is unavailable") from error
        try:
            value = operation(verified_query.redacted_query)
        except RateLimitError:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "reason": "rate-limit",
                    "message": None,
                }
            )
            continue
        except RetrievalTimeoutError:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "reason": "timeout",
                    "message": None,
                }
            )
            continue
        attempts.append(
            {"attempt": attempt_number, "reason": "success", "message": None}
        )
        try:
            material_sha256 = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
            round_state = phase_store.record_retrieval_round(material_sha256)
        except (PhaseIntegrityError, PhaseTransitionError, TypeError, ValueError) as error:
            raise RetrievalPolicyError("retrieval result cannot enter the sealed session") from error
        return _issue_retrieval_result(
            status=(
                "needs_attention" if round_state["needs_attention"] else "complete"
            ),
            attempts=attempts,
            value=value,
            boundary=boundary,
            authorization=authorization,
            query=verified_query,
            round_state=round_state,
        )
    return _issue_retrieval_result(
        status="blocked",
        attempts=attempts,
        value=None,
        boundary=boundary,
        authorization=authorization,
        query=verified_query,
        round_state=None,
    )


def _canonical_date(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    text = _nonempty(value, field=field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as error:
        raise RetrievalPolicyError(f"{field} must be an ISO date") from error
    if parsed.isoformat() != text:
        raise RetrievalPolicyError(f"{field} must be a canonical ISO date")
    return text


_SAFE_URL_QUERY_KEYS = frozenset(
    {"format", "lang", "limit", "locale", "offset", "order", "page", "sort", "version"}
)
_BCP47_RE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
_CANONICAL_INTEGER_RE = re.compile(r"0|[1-9][0-9]*")
_SENSITIVE_QUERY_VALUE_RE = re.compile(
    r"(?:secret|token|api[-_]?key|password|auth(?:orization)?|session|signature|bearer)",
    re.IGNORECASE,
)
_CHINA_ID_RE = re.compile(r"\d{17}[\dXx]")
_CHINA_PHONE_RE = re.compile(r"1[3-9]\d{9}")


def _validate_query_value_safety(value: str) -> None:
    if not value or len(value) > 64 or "%" in value or value.strip() != value:
        raise RetrievalPolicyError("source URL query value is invalid")
    if (
        _SENSITIVE_QUERY_VALUE_RE.search(value)
        or _CHINA_ID_RE.fullmatch(value)
        or _CHINA_PHONE_RE.fullmatch(value)
        or "@" in value
        or "/" in value
        or "\\" in value
        or value.startswith("~")
    ):
        raise RetrievalPolicyError("source URL query value is sensitive")


def _canonical_bcp47(value: str) -> str:
    _validate_query_value_safety(value)
    if len(value) > 35 or _BCP47_RE.fullmatch(value) is None:
        raise RetrievalPolicyError("source URL language value is invalid")
    subtags = value.split("-")
    normalized = [subtags[0].lower()]
    for subtag in subtags[1:]:
        if len(subtag) == 2 and subtag.isalpha():
            normalized.append(subtag.upper())
        elif len(subtag) == 4 and subtag.isalpha():
            normalized.append(subtag.title())
        else:
            normalized.append(subtag.lower())
    return "-".join(normalized)


def _canonical_integer(value: str, *, minimum: int, maximum: int) -> str:
    _validate_query_value_safety(value)
    if _CANONICAL_INTEGER_RE.fullmatch(value) is None:
        raise RetrievalPolicyError("source URL integer value is invalid")
    number = int(value)
    if not minimum <= number <= maximum:
        raise RetrievalPolicyError("source URL integer value is out of bounds")
    return str(number)


def _closed_query_value(value: str, *, allowed: frozenset[str]) -> str:
    _validate_query_value_safety(value)
    normalized = value.casefold()
    if normalized not in allowed:
        raise RetrievalPolicyError("source URL query value is not allowed")
    return normalized


def _canonical_format(value: str) -> str:
    return _closed_query_value(value, allowed=frozenset({"csv", "html", "json"}))


def _canonical_lang(value: str) -> str:
    return _canonical_bcp47(value)


def _canonical_limit(value: str) -> str:
    return _canonical_integer(value, minimum=1, maximum=1_000)


def _canonical_locale(value: str) -> str:
    return _canonical_bcp47(value)


def _canonical_offset(value: str) -> str:
    return _canonical_integer(value, minimum=0, maximum=1_000_000)


def _canonical_order(value: str) -> str:
    return _closed_query_value(value, allowed=frozenset({"asc", "desc"}))


def _canonical_page(value: str) -> str:
    return _canonical_integer(value, minimum=1, maximum=1_000_000)


def _canonical_sort(value: str) -> str:
    return _closed_query_value(value, allowed=frozenset({"date", "relevance", "title"}))


def _canonical_version(value: str) -> str:
    return _closed_query_value(value, allowed=frozenset({"1", "2", "3"}))


_QUERY_VALUE_VALIDATORS = {
    "format": _canonical_format,
    "lang": _canonical_lang,
    "limit": _canonical_limit,
    "locale": _canonical_locale,
    "offset": _canonical_offset,
    "order": _canonical_order,
    "page": _canonical_page,
    "sort": _canonical_sort,
    "version": _canonical_version,
}


def _normalize_source_url(value: object) -> str:
    text = _nonempty(value, field="url")
    try:
        parsed = urlsplit(text)
    except ValueError as error:
        raise RetrievalPolicyError("source URL is invalid") from error
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise RetrievalPolicyError("source URL must be an absolute HTTP(S) URL")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise RetrievalPolicyError("source URL contains disallowed credentials or fragment")
    try:
        query_pairs = (
            parse_qsl(
                parsed.query,
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=10,
            )
            if parsed.query
            else []
        )
    except ValueError as error:
        raise RetrievalPolicyError("source URL query is invalid") from error
    normalized_pairs: list[tuple[str, str]] = []
    seen_keys: set[str] = set()
    for raw_key, raw_value in query_pairs:
        key = raw_key.casefold()
        validator = _QUERY_VALUE_VALIDATORS.get(key)
        if key not in _SAFE_URL_QUERY_KEYS or validator is None:
            raise RetrievalPolicyError("source URL query key is not allowlisted")
        if key in seen_keys:
            raise RetrievalPolicyError("source URL query key is duplicated")
        seen_keys.add(key)
        normalized_pairs.append((key, validator(raw_value)))
    host = parsed.hostname.casefold()
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    normalized_query = urlencode(normalized_pairs, doseq=True)
    return urlunsplit((parsed.scheme.casefold(), host, parsed.path or "/", normalized_query, ""))


def validate_source_record(record: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(record, Mapping):
        raise RetrievalPolicyError("retrieved source must be an object")
    snapshot = copy.deepcopy(dict(record))
    if frozenset(snapshot) != _SOURCE_FIELDS:
        missing = sorted(_SOURCE_FIELDS - frozenset(snapshot))
        extra = sorted(frozenset(snapshot) - _SOURCE_FIELDS)
        raise RetrievalPolicyError(
            f"retrieved source fields are not closed (missing={missing}, extra={extra})"
        )
    for field in (
        "source_id",
        "interest",
        "supported_claim",
        "cannot_prove",
    ):
        _nonempty(snapshot[field], field=field)
    snapshot["url"] = _normalize_source_url(snapshot["url"])
    snapshot["event_date"] = _canonical_date(
        snapshot["event_date"], field="event_date"
    )
    snapshot["publication_date"] = _canonical_date(
        snapshot["publication_date"], field="publication_date"
    )
    lineage = snapshot["upstream_lineage"]
    if not isinstance(lineage, (list, tuple)):
        raise RetrievalPolicyError("upstream_lineage must be a string list")
    lineage_values = [_nonempty(value, field="upstream_lineage") for value in lineage]
    if len(lineage_values) != len(set(lineage_values)):
        raise RetrievalPolicyError("upstream_lineage contains duplicates")
    snapshot["upstream_lineage"] = lineage_values
    return snapshot


def make_source_record(
    *,
    source_id: str,
    url: str,
    event_date: str | None,
    publication_date: str | None,
    interest: str,
    upstream_lineage: Sequence[str],
    supported_claim: str,
    cannot_prove: str,
) -> dict[str, object]:
    return validate_source_record(
        {
            "source_id": source_id,
            "url": url,
            "event_date": event_date,
            "publication_date": publication_date,
            "interest": interest,
            "upstream_lineage": list(upstream_lineage),
            "supported_claim": supported_claim,
            "cannot_prove": cannot_prove,
        }
    )


def make_source_inventory_item(
    record: Mapping[str, object],
    *,
    query: PreparedQuery,
    authorization: RetrievalAuthorization,
) -> dict[str, object]:
    if not _valid_authorization(authorization) or authorization.status != "authorized":
        raise RetrievalPolicyError("source inventory requires issued retrieval authorization")
    if not _valid_prepared_query(query):
        raise RetrievalPolicyError("source inventory requires an issued prepared query")
    if (
        query.authorization_sha256 != authorization.authorization_sha256
        or query.eligibility_decision_sha256 != authorization.decision_sha256
        or query._boundary != authorization._boundary
    ):
        raise RetrievalPolicyError("source inventory authority differs from its query")
    normalized = validate_source_record(record)
    item: dict[str, object] = {
        "record": normalized,
        "source_record_sha256": hashlib.sha256(
            canonical_json_bytes(normalized)
        ).hexdigest(),
        "query_sha256": query.query_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "decision_sha256": authorization.decision_sha256,
        "run_id": query.run_id,
        "u1_parent_event_sha256": query.u1_parent_event_sha256,
        "request_sha256": query.request_sha256,
        "version_binding": copy.deepcopy(query.version_binding),
    }
    item["inventory_item_sha256"] = _hash_without(
        item, "inventory_item_sha256"
    )
    return item


def make_retrieval_entry(
    *,
    query_id: str,
    query: PreparedQuery,
    direction: str,
    result_summary: str,
    source_refs: Sequence[str],
    stop_reason: str,
) -> dict[str, object]:
    if not _valid_prepared_query(query):
        raise RetrievalPolicyError("retrieval entry requires an issued prepared query")
    if direction not in {
        "support",
        "counterexample",
        "affected-position",
        "source-lineage",
        "calibration",
    }:
        raise RetrievalPolicyError("retrieval direction is invalid")
    refs = [_nonempty(value, field="source_refs") for value in source_refs]
    if len(refs) != len(set(refs)):
        raise RetrievalPolicyError("retrieval source references contain duplicates")
    return {
        "query_id": _nonempty(query_id, field="query_id"),
        "query_sha256": query.query_sha256,
        "direction": direction,
        "result_summary": _nonempty(result_summary, field="result_summary"),
        "source_refs": refs,
        "stop_reason": _nonempty(stop_reason, field="stop_reason"),
    }


def _validate_query_document(
    query: Mapping[str, object],
    *,
    boundary: Mapping[str, object],
    decision_sha256: str,
    authorization_sha256: str,
) -> None:
    expected = {
        "eligibility_status": "required",
        "eligibility_decision_sha256": decision_sha256,
        "authorization_sha256": authorization_sha256,
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "run_id": boundary["run_id"],
        "version_binding": boundary["version_binding"],
    }
    for field, value in expected.items():
        if query.get(field) != value:
            raise RetrievalPolicyError("retrieval query differs from external authority")
    redacted = query.get("redacted_query")
    if not isinstance(redacted, str) or not redacted.strip():
        raise RetrievalPolicyError("retrieval query is empty")
    if query.get("query_sha256") != hashlib.sha256(redacted.encode("utf-8")).hexdigest():
        raise RetrievalPolicyError("retrieval query hash is invalid")
    if redact_query(redacted) != redacted or hostile_instruction_detected(redacted):
        raise RetrievalPolicyError("retrieval query is not safely deidentified")


def _validate_inventory_item(
    item: Mapping[str, object],
    *,
    boundary: Mapping[str, object],
    decision_sha256: str,
    authorization_sha256: str,
    query_hashes: set[str],
) -> str:
    record = item.get("record")
    if not isinstance(record, Mapping):
        raise RetrievalPolicyError("retrieval source record is invalid")
    normalized = validate_source_record(record)
    if normalized != dict(record):
        raise RetrievalPolicyError("retrieval source record is not canonical")
    if item.get("source_record_sha256") != hashlib.sha256(
        canonical_json_bytes(normalized)
    ).hexdigest():
        raise RetrievalPolicyError("retrieval source record hash is invalid")
    if item.get("inventory_item_sha256") != _hash_without(
        item, "inventory_item_sha256"
    ):
        raise RetrievalPolicyError("retrieval inventory item hash is invalid")
    if item.get("query_sha256") not in query_hashes:
        raise RetrievalPolicyError("retrieval source has no authorized query")
    for field, value in {
        "authorization_sha256": authorization_sha256,
        "decision_sha256": decision_sha256,
        "run_id": boundary["run_id"],
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "version_binding": boundary["version_binding"],
    }.items():
        if item.get(field) != value:
            raise RetrievalPolicyError("retrieval source differs from external authority")
    return str(normalized["source_id"])


def _validate_entry_document(
    entry: Mapping[str, object],
    *,
    query_hashes: set[str],
    source_ids: set[str],
) -> None:
    if entry.get("query_sha256") not in query_hashes:
        raise RetrievalPolicyError("retrieval entry has no authorized query")
    refs = entry.get("source_refs")
    if not isinstance(refs, list) or any(ref not in source_ids for ref in refs):
        raise RetrievalPolicyError("retrieval entry has an unknown source reference")


def build_retrieval_ledger(
    decision: RetrievalDecision,
    *,
    generated_at: str,
    phase_store: object,
    authorization: RetrievalAuthorization | None = None,
    queries: Sequence[PreparedQuery] = (),
    sources: Sequence[Mapping[str, object]] = (),
    entries: Sequence[Mapping[str, object]] = (),
    retrieval_result: RetrievalResult | None = None,
    resource_status: ResourceStatus | None = None,
) -> dict[str, object]:
    boundary = _boundary_document(phase_store)
    if not _valid_decision(decision) or decision._boundary != boundary:
        raise RetrievalPolicyError("retrieval ledger decision authority is invalid")
    query_documents: list[dict[str, object]] = []
    source_documents = [copy.deepcopy(dict(source)) for source in sources]
    entry_documents = [copy.deepcopy(dict(entry)) for entry in entries]
    if decision.status == "not-applicable":
        if (
            authorization is not None
            or queries
            or sources
            or entries
            or retrieval_result is not None
            or resource_status is not None
        ):
            raise RetrievalPolicyError("not-applicable retrieval cannot carry execution artifacts")
        retrieval_status = "not-applicable"
        authorization_sha256 = None
        block_result = None
        outbound_authorized = False
        saturation = {"rounds": 0, "stop_reason": "not-applicable"}
        completion_authorized = True
        disposition: dict[str, object] = {
            "kind": "not-applicable",
            "boundary": copy.deepcopy(boundary),
            "decision_sha256": decision.decision_sha256,
            "retrieval_status": retrieval_status,
            "block_result": None,
            "saturation": copy.deepcopy(saturation),
            "completion_authorized": completion_authorized,
        }
    elif decision.status == "required":
        if not _valid_authorization(authorization):
            raise RetrievalPolicyError("required retrieval ledger needs issued authorization")
        assert isinstance(authorization, RetrievalAuthorization)
        if (
            authorization._boundary != boundary
            or authorization.decision_sha256 != decision.decision_sha256
        ):
            raise RetrievalPolicyError("retrieval authorization differs from ledger authority")
        authorization_sha256 = authorization.authorization_sha256
        block_result = copy.deepcopy(authorization.block_result)
        outbound_authorized = authorization.outbound_authorized
        if authorization.status == "blocked":
            if (
                queries
                or sources
                or entries
                or retrieval_result is not None
                or resource_status is not None
            ):
                raise RetrievalPolicyError("blocked retrieval cannot carry execution artifacts")
            retrieval_status = "required-blocked"
            saturation = {"rounds": 0, "stop_reason": "required-blocked"}
            completion_authorized = False
            disposition = {
                "kind": "authorization-blocked",
                "boundary": copy.deepcopy(boundary),
                "authorization": _authorization_snapshot(authorization),
                "retrieval_status": retrieval_status,
                "block_result": copy.deepcopy(block_result),
                "saturation": copy.deepcopy(saturation),
                "completion_authorized": completion_authorized,
            }
        elif authorization.status == "authorized":
            if not queries:
                raise RetrievalPolicyError(
                    "authorized retrieval requires an issued prepared query"
                )
            query_authority_keys: set[
                tuple[str, str, str, str, str, str]
            ] = set()
            for query in queries:
                if not _valid_prepared_query(query):
                    raise RetrievalPolicyError("retrieval ledger query is not issuer-produced")
                if (
                    query._boundary != boundary
                    or query.authorization_sha256 != authorization.authorization_sha256
                    or query.eligibility_decision_sha256 != decision.decision_sha256
                ):
                    raise RetrievalPolicyError("retrieval ledger query authority is invalid")
                query_documents.append(query.document)
                query_authority_keys.add(_prepared_query_authority_key(query))
            if not _valid_retrieval_result(
                retrieval_result,
                boundary=boundary,
                authorization=authorization,
                query_keys=query_authority_keys,
            ):
                raise RetrievalPolicyError(
                    "retrieval ledger requires issuer-produced execution disposition"
                )
            if not _valid_resource_status(
                resource_status,
                boundary=boundary,
                authorization=authorization,
                query_keys=query_authority_keys,
            ):
                raise RetrievalPolicyError(
                    "retrieval ledger requires issuer-produced resource disposition"
                )
            assert isinstance(retrieval_result, RetrievalResult)
            assert isinstance(resource_status, ResourceStatus)
            saturation = copy.deepcopy(phase_store.retrieval_saturation)
            if resource_status.status != "running":
                retrieval_status = "required-blocked"
                block_result = {
                    "block_class": "resource-condition",
                    "detail": "host free-space authority requires attention",
                }
                completion_authorized = False
            elif (
                retrieval_result.status == "needs_attention"
                or saturation.get("stop_reason") == "material-novelty-exhausted"
            ):
                retrieval_status = "required-blocked"
                block_result = {
                    "block_class": "retry-exhaustion",
                    "detail": "material novelty limit requires attention",
                }
                completion_authorized = False
            elif retrieval_result.status == "blocked":
                last_reason = (
                    str(retrieval_result.attempts[-1].get("reason"))
                    if retrieval_result.attempts
                    else "retry-exhaustion"
                )
                block_class = (
                    last_reason
                    if last_reason in {"rate-limit", "timeout"}
                    else "retry-exhaustion"
                )
                retrieval_status = "required-blocked"
                block_result = {
                    "block_class": block_class,
                    "detail": "bounded retrieval attempts were exhausted",
                }
                completion_authorized = False
            elif retrieval_result.status == "complete":
                retrieval_status = "required-complete"
                block_result = None
                completion_authorized = True
            else:
                raise RetrievalPolicyError("retrieval execution disposition is invalid")
            disposition = {
                "kind": "executed",
                "boundary": copy.deepcopy(boundary),
                "authorization": _authorization_snapshot(authorization),
                "result": _retrieval_result_snapshot(retrieval_result),
                "resource": _resource_status_snapshot(resource_status),
                "retrieval_status": retrieval_status,
                "block_result": copy.deepcopy(block_result),
                "saturation": copy.deepcopy(saturation),
                "completion_authorized": completion_authorized,
            }
        else:
            raise RetrievalPolicyError("retrieval authorization status is invalid")
    else:
        raise RetrievalPolicyError("retrieval decision status is invalid")

    query_hashes = {
        str(query["query_sha256"])
        for query in query_documents
    }
    for query in query_documents:
        _validate_query_document(
            query,
            boundary=boundary,
            decision_sha256=decision.decision_sha256,
            authorization_sha256=str(authorization_sha256),
        )
    source_ids = {
        _validate_inventory_item(
            source,
            boundary=boundary,
            decision_sha256=decision.decision_sha256,
            authorization_sha256=str(authorization_sha256),
            query_hashes=query_hashes,
        )
        for source in source_documents
    }
    if len(source_ids) != len(source_documents):
        raise RetrievalPolicyError("retrieval source identifiers are duplicated")
    for entry in entry_documents:
        _validate_entry_document(
            entry,
            query_hashes=query_hashes,
            source_ids=source_ids,
        )
    artifact: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.retrieval-ledger",
        "schema_version": 1,
        "run_id": boundary["run_id"],
        "version_binding": copy.deepcopy(boundary["version_binding"]),
        "generated_at": generated_at,
        "phase_id": "U2",
        "decision_sha256": decision.decision_sha256,
        "u1_parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "decision": decision.document,
        "retrieval_status": retrieval_status,
        "block_result": block_result,
        "authorization_sha256": authorization_sha256,
        "query_count": len(query_documents),
        "queries": query_documents,
        "sources": source_documents,
        "network_available": bool(boundary["network_available"]),
        "outbound_authorized": outbound_authorized,
        "entries": entry_documents,
        "saturation": saturation,
    }
    artifact["content_sha256"] = _hash_without(artifact, "content_sha256")
    try:
        validate_instance("ultra-retrieval-ledger.schema.json", artifact)
    except ValidationError as error:
        raise RetrievalPolicyError("retrieval ledger does not satisfy the frozen schema") from error
    artifact_sha256 = hashlib.sha256(canonical_json_bytes(artifact)).hexdigest()
    disposition["artifact_sha256"] = artifact_sha256
    disposition["disposition_sha256"] = _hash_without(
        disposition, "disposition_sha256"
    )
    disposition_sha256 = str(disposition["disposition_sha256"])
    issued_dispositions = _LEDGER_DISPOSITIONS.setdefault(artifact_sha256, {})
    previous = issued_dispositions.get(disposition_sha256)
    if previous is not None and previous != disposition:
        raise RetrievalPolicyError("retrieval ledger disposition authority collision")
    issued_dispositions[disposition_sha256] = copy.deepcopy(disposition)
    return artifact


def _ledger_seal_snapshot(seal: RetrievalLedgerSeal) -> dict[str, object]:
    return {
        "run_id": seal.run_id,
        "version_binding": copy.deepcopy(seal.version_binding),
        "u1_parent_event_sha256": seal.u1_parent_event_sha256,
        "request_sha256": seal.request_sha256,
        "decision_sha256": seal.decision_sha256,
        "authorization_sha256": seal.authorization_sha256,
        "content_sha256": seal.content_sha256,
        "artifact_sha256": seal.artifact_sha256,
        "retrieval_status": seal.retrieval_status,
        "completion_authorized": seal.completion_authorized,
        "disposition_sha256": seal.disposition_sha256,
    }


def verify_retrieval_ledger_seal(seal: object) -> RetrievalLedgerSeal:
    if not isinstance(seal, RetrievalLedgerSeal):
        raise RetrievalPolicyError("retrieval ledger authority is not issuer-produced")
    try:
        issued = _ISSUED_LEDGER_SEALS.get(seal._issuer_token)
        computed = _snapshot_sha256(_ledger_seal_snapshot(seal))
        if not issued or seal._seal_sha256 != issued or issued != computed:
            raise RetrievalPolicyError("retrieval ledger authority integrity is invalid")
    except (AttributeError, TypeError, ValueError) as error:
        raise RetrievalPolicyError("retrieval ledger authority integrity is invalid") from error
    return seal


def validate_retrieval_ledger(
    artifact: Mapping[str, object],
    *,
    phase_store: object,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_phase_id: str,
    expected_u1_parent_event_sha256: str,
    expected_request_sha256: str,
    expected_decision_sha256: str,
    expected_authorization_sha256: str | None,
) -> RetrievalLedgerSeal:
    boundary = _boundary_document(phase_store)
    if not isinstance(artifact, Mapping):
        raise RetrievalPolicyError("retrieval ledger must be an object")
    snapshot = copy.deepcopy(dict(artifact))
    try:
        validate_instance("ultra-retrieval-ledger.schema.json", snapshot)
    except ValidationError as error:
        raise RetrievalPolicyError("retrieval ledger does not satisfy the frozen schema") from error
    if snapshot.get("content_sha256") != _hash_without(snapshot, "content_sha256"):
        raise RetrievalPolicyError("retrieval ledger content hash is invalid")
    artifact_sha256 = hashlib.sha256(canonical_json_bytes(snapshot)).hexdigest()
    external = {
        "run_id": expected_run_id,
        "version_binding": copy.deepcopy(dict(expected_version_binding)),
        "phase_id": expected_phase_id,
        "u1_parent_event_sha256": expected_u1_parent_event_sha256,
        "request_sha256": expected_request_sha256,
        "decision_sha256": expected_decision_sha256,
        "authorization_sha256": expected_authorization_sha256,
    }
    for field, value in external.items():
        if snapshot.get(field) != value:
            raise RetrievalPolicyError(f"retrieval ledger differs from expected {field} authority")
    decision_authority = _DECISION_AUTHORITIES.get(expected_decision_sha256)
    if (
        decision_authority is None
        or decision_authority.get("document") != snapshot.get("decision")
        or decision_authority.get("boundary") != boundary
    ):
        raise RetrievalPolicyError("retrieval decision is not issuer-produced authority")
    for field in (
        "run_id",
        "version_binding",
        "u1_parent_event_sha256",
        "request_sha256",
    ):
        if snapshot.get(field) != boundary[field]:
            raise RetrievalPolicyError("retrieval ledger differs from sealed U1 authority")
    if snapshot.get("network_available") is not boundary["network_available"]:
        raise RetrievalPolicyError("retrieval ledger network state differs from sealed U0 authority")
    decision = snapshot.get("decision")
    if not isinstance(decision, Mapping):
        raise RetrievalPolicyError("retrieval ledger decision is invalid")
    basis = decision.get("eligibility_basis")
    if not isinstance(basis, Mapping):
        raise RetrievalPolicyError("retrieval eligibility basis is invalid")
    if (
        basis.get("basis_sha256") != _hash_without(basis, "basis_sha256")
        or decision.get("basis_sha256") != basis.get("basis_sha256")
        or decision.get("decision_sha256") != _hash_without(decision, "decision_sha256")
        or decision.get("decision_sha256") != snapshot["decision_sha256"]
        or basis.get("claim_sha256")
        != hashlib.sha256(str(basis.get("claim", "")).encode("utf-8")).hexdigest()
        or decision.get("claim_sha256") != basis.get("claim_sha256")
    ):
        raise RetrievalPolicyError("retrieval decision semantic hashes are invalid")
    for field in (
        "run_id",
        "version_binding",
        "u1_parent_event_sha256",
        "request_sha256",
    ):
        if decision.get(field) != snapshot[field] or basis.get(field) != snapshot[field]:
            raise RetrievalPolicyError("retrieval decision differs from upstream authority")
    authorization_sha256 = snapshot.get("authorization_sha256")
    if expected_authorization_sha256 is None:
        if authorization_sha256 is not None:
            raise RetrievalPolicyError("retrieval authorization authority is unexpected")
        authorization_authority = None
    else:
        authorization_authority = _AUTHORIZATION_AUTHORITIES.get(
            expected_authorization_sha256
        )
        if (
            authorization_authority is None
            or authorization_authority.get("boundary") != boundary
            or authorization_authority.get("decision_sha256")
            != expected_decision_sha256
            or authorization_authority.get("authorization_sha256")
            != expected_authorization_sha256
            or (
                authorization_authority.get("status") == "blocked"
                and authorization_authority.get("block_result")
                != snapshot.get("block_result")
            )
            or authorization_authority.get("network_available")
            != snapshot.get("network_available")
            or authorization_authority.get("outbound_authorized")
            != snapshot.get("outbound_authorized")
        ):
            raise RetrievalPolicyError(
                "retrieval authorization is not issuer-produced authority"
            )
    issued_dispositions = copy.deepcopy(
        _LEDGER_DISPOSITIONS.get(artifact_sha256, {})
    )
    if not issued_dispositions:
        raise RetrievalPolicyError(
            "retrieval ledger lacks issuer-produced execution disposition"
        )
    matching_dispositions = {
        disposition_sha256: disposition
        for disposition_sha256, disposition in issued_dispositions.items()
        if (
            disposition.get("artifact_sha256") == artifact_sha256
            and disposition.get("disposition_sha256") == disposition_sha256
            and disposition_sha256
            == _hash_without(disposition, "disposition_sha256")
            and disposition.get("boundary") == boundary
            and disposition.get("retrieval_status")
            == snapshot.get("retrieval_status")
            and disposition.get("block_result") == snapshot.get("block_result")
            and disposition.get("saturation") == snapshot.get("saturation")
        )
    }
    if not matching_dispositions:
        raise RetrievalPolicyError("retrieval disposition authority is invalid")
    disposition_sha256 = min(matching_dispositions)
    disposition = matching_dispositions[disposition_sha256]
    queries = snapshot.get("queries")
    sources = snapshot.get("sources")
    entries = snapshot.get("entries")
    if not isinstance(queries, list) or not isinstance(sources, list) or not isinstance(entries, list):
        raise RetrievalPolicyError("retrieval execution records are invalid")
    if snapshot.get("query_count") != len(queries):
        raise RetrievalPolicyError("retrieval query count is invalid")
    query_hashes: set[str] = set()
    if authorization_sha256 is not None:
        for query in queries:
            if not isinstance(query, Mapping):
                raise RetrievalPolicyError("retrieval query record is invalid")
            _validate_query_document(
                query,
                boundary=boundary,
                decision_sha256=str(snapshot["decision_sha256"]),
                authorization_sha256=str(authorization_sha256),
            )
            query_authority = _QUERY_AUTHORITIES.get(
                _prepared_query_authority_key(query)
            )
            if (
                query_authority is None
                or query_authority.get("document") != dict(query)
                or query_authority.get("boundary") != boundary
            ):
                raise RetrievalPolicyError("retrieval query is not issuer-produced authority")
            query_hashes.add(str(query["query_sha256"]))
    source_ids = {
        _validate_inventory_item(
            source,
            boundary=boundary,
            decision_sha256=str(snapshot["decision_sha256"]),
            authorization_sha256=str(authorization_sha256),
            query_hashes=query_hashes,
        )
        for source in sources
        if isinstance(source, Mapping)
    }
    if len(source_ids) != len(sources):
        raise RetrievalPolicyError("retrieval source identifiers are duplicated or invalid")
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise RetrievalPolicyError("retrieval entry is invalid")
        _validate_entry_document(entry, query_hashes=query_hashes, source_ids=source_ids)
    status = snapshot.get("retrieval_status")
    expected_outbound = (
        bool(authorization_authority.get("outbound_authorized"))
        if authorization_authority is not None
        else False
    )
    if snapshot.get("outbound_authorized") is not expected_outbound:
        raise RetrievalPolicyError("retrieval ledger outbound state is inconsistent")
    if disposition.get("kind") == "executed":
        if snapshot.get("saturation") != phase_store.retrieval_saturation:
            raise RetrievalPolicyError("retrieval saturation differs from sealed session state")
    elif snapshot.get("saturation", {}).get("rounds") != 0:
        raise RetrievalPolicyError("non-executed retrieval cannot select saturation state")
    completion_authorized = disposition.get("completion_authorized")
    if not isinstance(completion_authorized, bool):
        raise RetrievalPolicyError("retrieval completion disposition is invalid")
    if completion_authorized != (status in {"not-applicable", "required-complete"}):
        raise RetrievalPolicyError("retrieval completion disposition is inconsistent")
    seal = object.__new__(RetrievalLedgerSeal)
    fields = {
        "run_id": str(snapshot["run_id"]),
        "version_binding": copy.deepcopy(dict(snapshot["version_binding"])),
        "u1_parent_event_sha256": str(snapshot["u1_parent_event_sha256"]),
        "request_sha256": str(snapshot["request_sha256"]),
        "decision_sha256": str(snapshot["decision_sha256"]),
        "authorization_sha256": (
            str(snapshot["authorization_sha256"])
            if snapshot["authorization_sha256"] is not None
            else None
        ),
        "content_sha256": str(snapshot["content_sha256"]),
        "artifact_sha256": artifact_sha256,
        "retrieval_status": str(status),
        "completion_authorized": completion_authorized,
        "disposition_sha256": str(disposition_sha256),
    }
    for field, value in fields.items():
        object.__setattr__(seal, field, value)
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_LEDGER_SEALS, _ledger_seal_snapshot(seal)
    )
    object.__setattr__(seal, "_issuer_token", token)
    object.__setattr__(seal, "_seal_sha256", seal_sha256)
    return seal


def _resource_status_snapshot(result: ResourceStatus) -> dict[str, object]:
    return {
        "status": result.status,
        "checkpoint": copy.deepcopy(result.checkpoint),
        "deleted": result.deleted,
        "boundary": copy.deepcopy(result._boundary),
        "authorization_sha256": result._authorization_sha256,
        "query_key": list(result._query_key),
        "measured_root": result._measured_root,
        "free_bytes": result._free_bytes,
        "reserve_bytes": result._reserve_bytes,
    }


def _valid_resource_status(
    result: object,
    *,
    boundary: Mapping[str, object],
    authorization: RetrievalAuthorization,
    query_keys: set[tuple[str, str, str, str, str, str]],
) -> bool:
    if not isinstance(result, ResourceStatus):
        return False
    try:
        issued = _ISSUED_RESOURCE_STATUSES.get(result._issuer_token)
        return bool(
            issued
            and result._seal_sha256
            == issued
            == _snapshot_sha256(_resource_status_snapshot(result))
            and result.status in {"running", "needs_attention", "unknown"}
            and result.deleted is False
            and result._boundary == boundary
            and result._authorization_sha256
            == authorization.authorization_sha256
            and result._query_key in query_keys
            and result._measured_root == str(Path(boundary["input_root"]).resolve())
        )
    except (AttributeError, TypeError, ValueError):
        return False


def resource_status(
    *,
    phase_store: object,
    authorization: RetrievalAuthorization | None,
    prepared_query: PreparedQuery | None,
    checkpoint: Mapping[str, object],
) -> ResourceStatus:
    if not isinstance(checkpoint, Mapping):
        raise RetrievalPolicyError("checkpoint must be an object")
    from .source_integrity import MIN_FREE_SPACE_RESERVE_BYTES

    verified_authorization, verified_query, boundary = _validate_execution_authority(
        authorization,
        prepared_query,
        phase_store=phase_store,
    )
    measured_root = Path(str(boundary["input_root"])).resolve()
    free: int | None
    try:
        free = shutil.disk_usage(measured_root).free
    except OSError:
        free = None
    result = object.__new__(ResourceStatus)
    object.__setattr__(
        result,
        "status",
        (
            "unknown"
            if free is None
            else "needs_attention"
            if free < MIN_FREE_SPACE_RESERVE_BYTES
            else "running"
        ),
    )
    object.__setattr__(result, "checkpoint", copy.deepcopy(dict(checkpoint)))
    object.__setattr__(result, "deleted", False)
    object.__setattr__(result, "_boundary", copy.deepcopy(boundary))
    object.__setattr__(
        result,
        "_authorization_sha256",
        verified_authorization.authorization_sha256,
    )
    object.__setattr__(
        result,
        "_query_key",
        _prepared_query_authority_key(verified_query),
    )
    object.__setattr__(result, "_measured_root", str(measured_root))
    object.__setattr__(result, "_free_bytes", free)
    object.__setattr__(
        result, "_reserve_bytes", MIN_FREE_SPACE_RESERVE_BYTES
    )
    token, seal_sha256 = _issue_snapshot(
        _ISSUED_RESOURCE_STATUSES,
        _resource_status_snapshot(result),
    )
    object.__setattr__(result, "_issuer_token", token)
    object.__setattr__(result, "_seal_sha256", seal_sha256)
    return result


def inspect_acl(path: Path) -> str:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    from .source_integrity import measure_current_user_acl

    return measure_current_user_acl(path)


def _canonical_host_timestamp(value: object, *, field: str) -> tuple[str, datetime]:
    text = _nonempty(value, field=field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise RetrievalPolicyError(f"{field} must be an ISO UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RetrievalPolicyError(f"{field} must be an ISO UTC timestamp")
    timespec = "microseconds" if parsed.microsecond else "seconds"
    canonical = parsed.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )
    if canonical != text:
        raise RetrievalPolicyError(f"{field} must be a canonical ISO UTC timestamp")
    return canonical, parsed


def _phase_store_layout(
    phase_store: object,
    *,
    boundary: Mapping[str, object],
):
    from .paths import RunLayout, assert_safe_descendant

    layout = getattr(phase_store, "_run_layout", None)
    if not isinstance(layout, RunLayout):
        raise RetrievalPolicyError("retrieval requires a runtime-owned run layout")
    try:
        assert_safe_descendant(layout.root, layout.run_dir)
        assert_safe_descendant(layout.root, layout.recovery_dir)
    except (OSError, TypeError, ValueError) as error:
        raise RetrievalPolicyError("retrieval run layout authority is invalid") from error
    if layout.run_dir.name != boundary["run_id"]:
        raise RetrievalPolicyError("retrieval run layout differs from sealed U1")
    return layout


def _retrieval_action_path(layout) -> Path:
    from .paths import assert_safe_descendant

    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / _RETRIEVAL_ACTION_RELATIVE_PATH,
    )


def _admitted_host_result_path(layout) -> Path:
    from .paths import assert_safe_descendant

    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / _ADMITTED_HOST_RESULT_RELATIVE_PATH,
    )


def _retrieval_decision_action_document(
    decision: RetrievalDecision,
) -> dict[str, object]:
    document = decision.document
    basis = document.get("eligibility_basis")
    if not isinstance(basis, Mapping):
        raise RetrievalPolicyError("retrieval decision basis is invalid")
    trigger_kinds = basis.get("trigger_kinds")
    if not isinstance(trigger_kinds, list) or not trigger_kinds:
        raise RetrievalPolicyError("required retrieval has no trigger authority")
    return {
        "status": decision.status,
        "reason": decision.reason,
        "decision_sha256": decision.decision_sha256,
        "claim_sha256": document["claim_sha256"],
        "basis_sha256": document["basis_sha256"],
        "trigger_kinds": copy.deepcopy(trigger_kinds),
    }


def _retrieval_authorization_action_document(
    authorization: RetrievalAuthorization,
) -> dict[str, object]:
    return {
        "status": authorization.status,
        "reason": authorization.reason,
        "decision_sha256": authorization.decision_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "network_available": authorization.network_available,
        "outbound_authorized": authorization.outbound_authorized,
        "block_result": copy.deepcopy(authorization.block_result),
    }


def _retrieval_action_payload(
    *,
    phase_store: object,
    decision: RetrievalDecision,
    authorization: RetrievalAuthorization,
    queries: Sequence[PreparedQuery],
    boundary: Mapping[str, object],
) -> dict[str, object]:
    if not queries:
        raise RetrievalPolicyError("retrieval action requires at least one query")
    attestation = getattr(phase_store, "capability_attestation", None)
    document = getattr(attestation, "document", None)
    if not isinstance(document, Mapping):
        raise RetrievalPolicyError("retrieval requires sealed host capabilities")
    providers = document.get("providers")
    tools = document.get("tools")
    if not isinstance(providers, list) or not providers:
        raise RetrievalPolicyError("retrieval has no measured host provider identity")
    if not isinstance(tools, list) or not tools:
        raise RetrievalPolicyError("retrieval has no measured host tool identity")
    provider_ids = {
        provider.get("provider_id")
        for provider in providers
        if isinstance(provider, Mapping)
    }
    if any(
        not isinstance(tool, Mapping) or tool.get("provider_id") not in provider_ids
        for tool in tools
    ):
        raise RetrievalPolicyError("retrieval tool identity has no measured provider")
    return {
        "decision": _retrieval_decision_action_document(decision),
        "authorization": _retrieval_authorization_action_document(authorization),
        "queries": [query.document for query in queries],
        "allowed_providers": copy.deepcopy(providers),
        "allowed_tools": copy.deepcopy(tools),
        "maximum_tool_retries": int(boundary["maximum_tool_retries"]),
        "requested_result_fields": [
            "entries",
            "provider",
            "queries",
            "sources",
            "tool",
        ],
    }


def _validate_persisted_retrieval_action(
    document: Mapping[str, object],
    *,
    layout,
    boundary: Mapping[str, object],
    expected_payload: Mapping[str, object],
):
    from .host_handshake import HostActionSeal
    from .paths import assert_safe_descendant

    snapshot = copy.deepcopy(dict(document))
    try:
        validate_instance("ultra-host-action.schema.json", snapshot)
    except Exception as error:
        raise RetrievalPolicyError("persisted retrieval action is invalid") from error
    supplied = snapshot.get("action_sha256")
    if supplied != _hash_without(snapshot, "action_sha256"):
        raise RetrievalPolicyError("persisted retrieval action hash differs")
    expected = {
        "run_id": boundary["run_id"],
        "version_binding": boundary["version_binding"],
        "phase_id": "U2",
        "action_kind": "retrieval",
        "parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "result_relative_path": _RETRIEVAL_RESULT_RELATIVE_PATH,
        "payload": copy.deepcopy(dict(expected_payload)),
    }
    if any(snapshot.get(field) != value for field, value in expected.items()):
        raise RetrievalPolicyError("persisted retrieval action authority differs")
    _canonical_host_timestamp(snapshot.get("issued_at"), field="issued_at")
    result_path = assert_safe_descendant(
        layout.root,
        layout.run_dir / _RETRIEVAL_RESULT_RELATIVE_PATH,
    )
    return HostActionSeal(snapshot, str(supplied), result_path)


def _persist_retrieval_action(layout, action) -> None:
    path = _retrieval_action_path(layout)
    if path.exists():
        try:
            raw = path.read_bytes()
            current = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise RetrievalPolicyError("persisted retrieval action is unreadable") from error
        if raw != canonical_json_bytes(current) or current != action.document:
            raise RetrievalPolicyError("persisted retrieval action changed")
        return
    atomic_write_json(path, action.document)


def issue_retrieval_action(
    phase_store: object,
    *,
    claim: str,
    trigger_kinds: Sequence[str],
    generated_at: str,
    analysis_kind: str | None = None,
    material_inventory: Sequence[Mapping[str, object]] | None = None,
    material_universe_sha256: str | None = None,
):
    """Issue a redacted, persistent U2 action or a zero-dispatch blocked ledger."""

    from .host_handshake import issue_host_action, load_pending_action

    boundary = _boundary_document(phase_store)
    _, issued_at = _canonical_host_timestamp(generated_at, field="generated_at")
    decision = assess_retrieval_eligibility(
        claim,
        phase_store=phase_store,
        analysis_kind=analysis_kind,
        trigger_kinds=trigger_kinds,
        material_inventory=material_inventory,
        material_universe_sha256=material_universe_sha256,
    )
    authorization = gate_retrieval(decision, phase_store=phase_store)
    if not isinstance(authorization, RetrievalAuthorization):
        return build_retrieval_ledger(
            decision,
            generated_at=generated_at,
            phase_store=phase_store,
        )
    if authorization.status == "blocked":
        return build_retrieval_ledger(
            decision,
            generated_at=generated_at,
            phase_store=phase_store,
            authorization=authorization,
        )
    if authorization.status != "authorized":
        raise RetrievalPolicyError("retrieval authorization state is invalid")
    prepared = (
        prepare_query(
            authorization,
            claim,
            phase_store=phase_store,
        ),
    )
    payload = _retrieval_action_payload(
        phase_store=phase_store,
        decision=decision,
        authorization=authorization,
        queries=prepared,
        boundary=boundary,
    )
    layout = _phase_store_layout(phase_store, boundary=boundary)
    persisted_path = _retrieval_action_path(layout)
    if persisted_path.exists():
        try:
            raw = persisted_path.read_bytes()
            persisted = load_json_object_bytes(raw, source=str(persisted_path))
        except (OSError, TypeError, ValueError) as error:
            raise RetrievalPolicyError("persisted retrieval action is unreadable") from error
        if raw != canonical_json_bytes(persisted):
            raise RetrievalPolicyError("persisted retrieval action is not canonical")
        action = _validate_persisted_retrieval_action(
            persisted,
            layout=layout,
            boundary=boundary,
            expected_payload=payload,
        )
        pending = load_pending_action(layout)
        accepted = (
            layout.recovery_dir
            / "host-results"
            / action.action_sha256
            / "accepted.json"
        )
        if pending == action or accepted.is_file():
            return action
        raise RetrievalPolicyError(
            "persisted retrieval action has neither pending nor accepted authority"
        )
    action = issue_host_action(
        layout,
        action_kind="retrieval",
        phase_id="U2",
        parent_event_sha256=str(boundary["u1_parent_event_sha256"]),
        request_sha256=str(boundary["request_sha256"]),
        payload=payload,
        result_relative_path=_RETRIEVAL_RESULT_RELATIVE_PATH,
        now=issued_at,
    )
    _persist_retrieval_action(layout, action)
    return action


def _accepted_retrieval_result_document(
    receipt: object,
    *,
    phase_store: object,
    boundary: Mapping[str, object],
    action,
) -> dict[str, object]:
    from .host_handshake import HostResultSeal
    from .paths import assert_safe_descendant

    if not isinstance(receipt, HostResultSeal):
        raise RetrievalPolicyError("host retrieval result requires an accepted receipt seal")
    receipt_document = copy.deepcopy(receipt.document)
    try:
        validate_instance("ultra-host-result-receipt.schema.json", receipt_document)
    except Exception as error:
        raise RetrievalPolicyError("host retrieval receipt is invalid") from error
    if (
        receipt.receipt_sha256 != receipt_document.get("receipt_sha256")
        or receipt.action_sha256 != action.action_sha256
    ):
        raise RetrievalPolicyError("host retrieval receipt seal hash differs")
    if receipt_document.get("receipt_sha256") != _hash_without(
        receipt_document, "receipt_sha256"
    ):
        raise RetrievalPolicyError("host retrieval receipt hash differs")
    expected = {
        "run_id": boundary["run_id"],
        "version_binding": boundary["version_binding"],
        "phase_id": "U2",
        "action_kind": "retrieval",
        "parent_event_sha256": boundary["u1_parent_event_sha256"],
        "request_sha256": boundary["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": _RETRIEVAL_RESULT_RELATIVE_PATH,
    }
    if any(receipt_document.get(field) != value for field, value in expected.items()):
        raise RetrievalPolicyError("host retrieval receipt authority differs")
    _, issued_at = _canonical_host_timestamp(
        action.document.get("issued_at"),
        field="issued_at",
    )
    _, completed_at = _canonical_host_timestamp(
        receipt_document.get("completed_at"),
        field="completed_at",
    )
    if completed_at < issued_at:
        raise RetrievalPolicyError("host retrieval completed before its action was issued")
    layout = _phase_store_layout(phase_store, boundary=boundary)
    accepted_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json",
    )
    try:
        accepted_raw = accepted_path.read_bytes()
        accepted = load_json_object_bytes(accepted_raw, source=str(accepted_path))
    except (OSError, TypeError, ValueError) as error:
        raise RetrievalPolicyError("accepted host retrieval receipt is unavailable") from error
    if (
        accepted_raw != canonical_json_bytes(accepted)
        or accepted != receipt_document
    ):
        raise RetrievalPolicyError("accepted host retrieval receipt differs")
    try:
        result_raw = action.result_path.read_bytes()
        result = load_json_object_bytes(result_raw, source=str(action.result_path))
    except (OSError, TypeError, ValueError) as error:
        raise RetrievalPolicyError("host retrieval result is unavailable") from error
    if result_raw != canonical_json_bytes(result):
        raise RetrievalPolicyError("host retrieval result is not canonical")
    if receipt_document.get("result_sha256") != sha256_bytes(result_raw):
        raise RetrievalPolicyError("host retrieval result hash differs")
    return result


def _validate_host_execution_receipt(
    document: Mapping[str, object],
    *,
    maximum_attempts: int,
) -> tuple[dict[str, object], ...]:
    if document.get("execution_status") != "complete":
        raise RetrievalPolicyError("required host retrieval did not complete")
    attempts = document.get("attempts")
    if not isinstance(attempts, list) or not 1 <= len(attempts) <= maximum_attempts:
        raise RetrievalPolicyError("host retrieval attempts are outside the bounded limit")
    normalized: list[dict[str, object]] = []
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, Mapping) or attempt.get("attempt") != index:
            raise RetrievalPolicyError("host retrieval attempt sequence is invalid")
        status = attempt.get("status")
        if status not in {"success", "rate-limit", "timeout", "error"}:
            raise RetrievalPolicyError("host retrieval attempt status is invalid")
        if status == "success" and attempt.get("error") is not None:
            raise RetrievalPolicyError("successful host retrieval cannot carry an error")
        if status == "success" and index != len(attempts):
            raise RetrievalPolicyError("host retrieval continued after success")
        normalized.append(
            {
                "attempt": index,
                "reason": status,
                "message": copy.deepcopy(attempt.get("error")),
            }
        )
    if attempts[-1].get("status") != "success":
        raise RetrievalPolicyError("required host retrieval has no successful attempt")
    return tuple(normalized)


def _validate_host_identities(
    receipt: Mapping[str, object],
    result: Mapping[str, object],
    *,
    action_payload: Mapping[str, object],
) -> None:
    provider = receipt.get("provider")
    tool = receipt.get("tool")
    if (
        not isinstance(provider, Mapping)
        or not isinstance(tool, Mapping)
        or result.get("provider") != provider
        or result.get("tool") != tool
        or result.get("execution_id") != receipt.get("execution_id")
    ):
        raise RetrievalPolicyError("host retrieval provider, tool, or execution differs")
    allowed_providers = action_payload.get("allowed_providers")
    allowed_tools = action_payload.get("allowed_tools")
    if (
        not isinstance(allowed_providers, list)
        or dict(provider) not in allowed_providers
        or not isinstance(allowed_tools, list)
        or dict(tool) not in allowed_tools
        or tool.get("provider_id") != provider.get("provider_id")
    ):
        raise RetrievalPolicyError("host retrieval used an unmeasured provider or tool")


def _persist_admitted_host_result(
    layout,
    *,
    action_sha256: str,
    receipt_sha256: str,
    provider: Mapping[str, object],
    tool: Mapping[str, object],
    sources: Sequence[Mapping[str, object]],
) -> None:
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.admitted-host-retrieval-result",
        "schema_version": 1,
        "action_sha256": action_sha256,
        "receipt_sha256": receipt_sha256,
        "provider": copy.deepcopy(dict(provider)),
        "tool": copy.deepcopy(dict(tool)),
        "sources": [copy.deepcopy(dict(source)) for source in sources],
    }
    document["content_sha256"] = _hash_without(document, "content_sha256")
    path = _admitted_host_result_path(layout)
    if path.exists():
        try:
            raw = path.read_bytes()
            current = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise RetrievalPolicyError("admitted host retrieval result is unreadable") from error
        if raw != canonical_json_bytes(current) or current != document:
            raise RetrievalPolicyError("admitted host retrieval result changed")
        return
    atomic_write_json(path, document)


def admit_host_retrieval_result(
    receipt: object,
    *,
    phase_store: object,
    decision: RetrievalDecision,
    authorization: RetrievalAuthorization,
) -> dict[str, object]:
    """Validate an accepted host result and build a schema-valid U2 ledger."""

    boundary = _boundary_document(phase_store)
    if not _valid_decision(decision) or decision._boundary != boundary:
        raise RetrievalPolicyError("host retrieval decision authority is invalid")
    if (
        not _valid_authorization(authorization)
        or authorization.status != "authorized"
        or authorization._boundary != boundary
        or authorization.decision_sha256 != decision.decision_sha256
    ):
        raise RetrievalPolicyError("host retrieval authorization authority is invalid")
    decision_document = decision.document
    basis = decision_document.get("eligibility_basis")
    if not isinstance(basis, Mapping):
        raise RetrievalPolicyError("host retrieval decision basis is invalid")
    claim = _nonempty(basis.get("claim"), field="claim")
    prepared = (
        prepare_query(
            authorization,
            claim,
            phase_store=phase_store,
        ),
    )
    expected_payload = _retrieval_action_payload(
        phase_store=phase_store,
        decision=decision,
        authorization=authorization,
        queries=prepared,
        boundary=boundary,
    )
    layout = _phase_store_layout(phase_store, boundary=boundary)
    action_path = _retrieval_action_path(layout)
    try:
        action_raw = action_path.read_bytes()
        action_document = load_json_object_bytes(action_raw, source=str(action_path))
    except (OSError, TypeError, ValueError) as error:
        raise RetrievalPolicyError("persisted retrieval action is unavailable") from error
    if action_raw != canonical_json_bytes(action_document):
        raise RetrievalPolicyError("persisted retrieval action is not canonical")
    action = _validate_persisted_retrieval_action(
        action_document,
        layout=layout,
        boundary=boundary,
        expected_payload=expected_payload,
    )
    result = _accepted_retrieval_result_document(
        receipt,
        phase_store=phase_store,
        boundary=boundary,
        action=action,
    )
    receipt_document = receipt.document
    action_payload = action.document.get("payload")
    if not isinstance(action_payload, Mapping):
        raise RetrievalPolicyError("persisted retrieval action payload is invalid")
    attempts = _validate_host_execution_receipt(
        receipt_document,
        maximum_attempts=int(action_payload["maximum_tool_retries"]),
    )
    expected_result_fields = {
        "schema_id",
        "schema_version",
        "action_sha256",
        "provider",
        "tool",
        "execution_id",
        "queries",
        "sources",
        "entries",
    }
    if (
        set(result) != expected_result_fields
        or result.get("schema_id")
        != "crossframe.ultra.v82.host-retrieval-result"
        or result.get("schema_version") != 1
        or result.get("action_sha256") != action.action_sha256
    ):
        raise RetrievalPolicyError("host retrieval result fields are not closed")
    _validate_host_identities(
        receipt_document,
        result,
        action_payload=action_payload,
    )
    result_queries = result.get("queries")
    if not isinstance(result_queries, list) or not result_queries:
        raise RetrievalPolicyError("required retrieval returned no query results")
    prepared_by_hash = {query.query_sha256: query for query in prepared}
    returned_query_hashes: set[str] = set()
    for query_result in result_queries:
        if (
            not isinstance(query_result, Mapping)
            or set(query_result) != {"query_sha256", "status"}
            or query_result.get("status") != "complete"
            or query_result.get("query_sha256") not in prepared_by_hash
        ):
            raise RetrievalPolicyError("host retrieval query result is invalid")
        query_sha256 = str(query_result["query_sha256"])
        if query_sha256 in returned_query_hashes:
            raise RetrievalPolicyError("host retrieval repeats a query result")
        returned_query_hashes.add(query_sha256)
    if returned_query_hashes != set(prepared_by_hash):
        raise RetrievalPolicyError("host retrieval omitted an authorized query")
    source_results = result.get("sources")
    if not isinstance(source_results, list) or not source_results:
        raise RetrievalPolicyError("required retrieval returned no sources")
    source_inventory: list[dict[str, object]] = []
    admitted_external: list[dict[str, object]] = []
    source_ids: set[str] = set()
    source_fields = {
        "source_id",
        "query_sha256",
        "url",
        "content",
        "content_sha256",
        "event_date",
        "publication_date",
        "interest",
        "upstream_lineage",
        "supported_claim",
        "cannot_prove",
    }
    for source in source_results:
        if not isinstance(source, Mapping) or set(source) != source_fields:
            raise RetrievalPolicyError("host retrieval source fields are not closed")
        query_sha256 = source.get("query_sha256")
        query = prepared_by_hash.get(str(query_sha256))
        if query is None or query_sha256 not in returned_query_hashes:
            raise RetrievalPolicyError("host retrieval source has no completed query")
        content = _nonempty(source.get("content"), field="content")
        external = store_external_content(content)
        if source.get("content_sha256") != external["content_sha256"]:
            raise RetrievalPolicyError("host retrieval source content hash differs")
        record = make_source_record(
            source_id=_nonempty(source.get("source_id"), field="source_id"),
            url=_nonempty(source.get("url"), field="url"),
            event_date=source.get("event_date"),
            publication_date=source.get("publication_date"),
            interest=_nonempty(source.get("interest"), field="interest"),
            upstream_lineage=source.get("upstream_lineage"),
            supported_claim=_nonempty(
                source.get("supported_claim"), field="supported_claim"
            ),
            cannot_prove=_nonempty(
                source.get("cannot_prove"), field="cannot_prove"
            ),
        )
        source_id = str(record["source_id"])
        if source_id in source_ids:
            raise RetrievalPolicyError("host retrieval repeats a source identifier")
        source_ids.add(source_id)
        source_inventory.append(
            make_source_inventory_item(
                record,
                query=query,
                authorization=authorization,
            )
        )
        admitted_external.append(
            {
                "source_id": source_id,
                "query_sha256": str(query_sha256),
                "external_content": external,
            }
        )
    raw_entries = result.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise RetrievalPolicyError("required retrieval returned no source-linked entries")
    entries: list[dict[str, object]] = []
    entry_fields = {
        "query_id",
        "query_sha256",
        "direction",
        "result_summary",
        "source_refs",
        "stop_reason",
    }
    for entry in raw_entries:
        if not isinstance(entry, Mapping) or set(entry) != entry_fields:
            raise RetrievalPolicyError("host retrieval entry fields are not closed")
        query = prepared_by_hash.get(str(entry.get("query_sha256")))
        refs = entry.get("source_refs")
        if query is None or not isinstance(refs, list) or not refs:
            raise RetrievalPolicyError("host retrieval entry has no query or source")
        entries.append(
            make_retrieval_entry(
                query_id=_nonempty(entry.get("query_id"), field="query_id"),
                query=query,
                direction=_nonempty(entry.get("direction"), field="direction"),
                result_summary=_nonempty(
                    entry.get("result_summary"), field="result_summary"
                ),
                source_refs=refs,
                stop_reason=_nonempty(entry.get("stop_reason"), field="stop_reason"),
            )
        )
    result_sha256 = str(receipt_document["result_sha256"])
    try:
        round_state = phase_store.record_retrieval_round(result_sha256)
    except Exception as error:
        raise RetrievalPolicyError(
            "host retrieval result cannot enter the sealed session"
        ) from error
    retrieval_result = _issue_retrieval_result(
        status="needs_attention" if round_state["needs_attention"] else "complete",
        attempts=attempts,
        value={
            "action_sha256": action.action_sha256,
            "receipt_sha256": receipt.receipt_sha256,
            "result_sha256": result_sha256,
            "source_ids": sorted(source_ids),
        },
        boundary=boundary,
        authorization=authorization,
        query=prepared[0],
        round_state=round_state,
    )
    resources = resource_status(
        phase_store=phase_store,
        authorization=authorization,
        prepared_query=prepared[0],
        checkpoint={
            "phase": "U2",
            "action_sha256": action.action_sha256,
            "receipt_sha256": receipt.receipt_sha256,
        },
    )
    generated_at = _nonempty(receipt_document.get("completed_at"), field="completed_at")
    _canonical_host_timestamp(generated_at, field="completed_at")
    ledger = build_retrieval_ledger(
        decision,
        generated_at=generated_at,
        phase_store=phase_store,
        authorization=authorization,
        queries=prepared,
        sources=source_inventory,
        entries=entries,
        retrieval_result=retrieval_result,
        resource_status=resources,
    )
    validate_retrieval_ledger(
        ledger,
        phase_store=phase_store,
        expected_run_id=str(boundary["run_id"]),
        expected_version_binding=boundary["version_binding"],
        expected_phase_id="U2",
        expected_u1_parent_event_sha256=str(boundary["u1_parent_event_sha256"]),
        expected_request_sha256=str(boundary["request_sha256"]),
        expected_decision_sha256=decision.decision_sha256,
        expected_authorization_sha256=authorization.authorization_sha256,
    )
    _persist_admitted_host_result(
        layout,
        action_sha256=action.action_sha256,
        receipt_sha256=receipt.receipt_sha256,
        provider=receipt_document["provider"],
        tool=receipt_document["tool"],
        sources=admitted_external,
    )
    return ledger


def admit_subagent_candidates(
    receipt: object,
    *,
    admitted_source_ids: Collection[str],
) -> tuple[dict[str, object], ...]:
    """Return only role-limited candidates whose every source is already admitted."""

    from .host_handshake import HostResultSeal

    if not isinstance(receipt, HostResultSeal):
        raise RetrievalPolicyError("subagent candidates require a host result seal")
    document = copy.deepcopy(receipt.document)
    try:
        validate_instance("ultra-host-result-receipt.schema.json", document)
    except Exception as error:
        raise RetrievalPolicyError("subagent result receipt is invalid") from error
    if (
        document.get("action_kind") != "subagent"
        or document.get("phase_id") != "U2"
        or receipt.action_sha256 != document.get("action_sha256")
        or receipt.receipt_sha256 != document.get("receipt_sha256")
        or document.get("receipt_sha256")
        != _hash_without(document, "receipt_sha256")
    ):
        raise RetrievalPolicyError("subagent result receipt authority differs")
    _validate_host_execution_receipt(document, maximum_attempts=3)
    if isinstance(admitted_source_ids, (str, bytes)) or not isinstance(
        admitted_source_ids, Collection
    ):
        raise TypeError("admitted_source_ids must be a collection of source IDs")
    admitted = {
        _nonempty(source_id, field="admitted_source_ids")
        for source_id in admitted_source_ids
    }
    result = document.get("result")
    if (
        not isinstance(result, Mapping)
        or result.get("content_sha256") != _hash_without(result, "content_sha256")
    ):
        raise RetrievalPolicyError("subagent result content hash differs")
    _nonempty(result.get("cannot_prove"), field="cannot_prove")
    resource_limits = result.get("resource_limits")
    if not isinstance(resource_limits, Mapping):
        raise RetrievalPolicyError("subagent result resource limits are invalid")
    maximum_candidates = resource_limits.get("maximum_candidates")
    maximum_refs = resource_limits.get("maximum_source_refs_per_candidate")
    if type(maximum_candidates) is not int or type(maximum_refs) is not int:
        raise RetrievalPolicyError("subagent result resource limits are invalid")
    candidates = result.get("candidates") if isinstance(result, Mapping) else None
    if (
        not isinstance(candidates, list)
        or not candidates
        or len(candidates) > maximum_candidates
    ):
        raise RetrievalPolicyError("subagent result has no candidate list")
    accepted: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    expected_fields = {
        "candidate_id",
        "role",
        "claim",
        "source_refs",
        "cannot_prove",
    }
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or set(candidate) != expected_fields:
            raise RetrievalPolicyError("subagent candidate fields are not closed")
        candidate_id = _nonempty(candidate.get("candidate_id"), field="candidate_id")
        if candidate_id in seen_ids:
            raise RetrievalPolicyError("subagent candidate identifier is duplicated")
        seen_ids.add(candidate_id)
        role = _nonempty(candidate.get("role"), field="role")
        if role not in _SUBAGENT_CANDIDATE_ROLES:
            raise RetrievalPolicyError("subagent candidate role is not allowed")
        _nonempty(candidate.get("claim"), field="claim")
        _nonempty(candidate.get("cannot_prove"), field="cannot_prove")
        refs = candidate.get("source_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or len(refs) > maximum_refs
            or len(refs) != len(set(refs))
            or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
        ):
            raise RetrievalPolicyError("subagent candidate source references are invalid")
        if set(refs).issubset(admitted):
            accepted.append(copy.deepcopy(dict(candidate)))
    return tuple(accepted)


__all__ = (
    "PreparedQuery",
    "PureLogicEligibilityAuthority",
    "RateLimitError",
    "ResourceStatus",
    "RetrievalAuthorization",
    "RetrievalDecision",
    "RetrievalLedgerSeal",
    "RetrievalPolicyError",
    "RetrievalResult",
    "RetrievalTimeoutError",
    "apply_external_content_policy",
    "admit_host_retrieval_result",
    "admit_subagent_candidates",
    "assess_retrieval_eligibility",
    "bounded_retrieve",
    "build_retrieval_ledger",
    "gate_retrieval",
    "hostile_instruction_detected",
    "inspect_acl",
    "issue_retrieval_action",
    "make_retrieval_entry",
    "make_source_record",
    "make_source_inventory_item",
    "prepare_query",
    "redact_query",
    "resource_status",
    "store_external_content",
    "validate_retrieval_ledger",
    "validate_pure_logic_eligibility_basis",
    "validate_source_record",
    "verify_retrieval_ledger_seal",
)
