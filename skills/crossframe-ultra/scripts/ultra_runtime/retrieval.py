from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date
import hashlib
import os
from pathlib import Path
import re
import shutil
from typing import Callable, Mapping, Sequence, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


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
    _decision_id: str


@dataclass(frozen=True, init=False)
class RetrievalAuthorization:
    eligibility_status: str
    reason: str
    _authorization_id: str


@dataclass(frozen=True)
class PreparedQuery:
    eligibility_status: str
    redacted_query: str
    query_sha256: str


@dataclass(frozen=True)
class RetrievalResult:
    status: str
    attempts: tuple[dict[str, object], ...]
    value: object | None = None


@dataclass(frozen=True)
class ResourceStatus:
    status: str
    checkpoint: dict[str, object]
    deleted: bool


_ISSUED_DECISIONS: set[str] = set()
_ISSUED_AUTHORIZATIONS: set[str] = set()


def _issue_decision(status: str, reason: str) -> RetrievalDecision:
    decision_id = hashlib.sha256(os.urandom(32)).hexdigest()
    _ISSUED_DECISIONS.add(decision_id)
    decision = object.__new__(RetrievalDecision)
    object.__setattr__(decision, "status", status)
    object.__setattr__(decision, "reason", reason)
    object.__setattr__(decision, "_decision_id", decision_id)
    return decision


def _issue_authorization(reason: str) -> RetrievalAuthorization:
    authorization_id = hashlib.sha256(os.urandom(32)).hexdigest()
    _ISSUED_AUTHORIZATIONS.add(authorization_id)
    authorization = object.__new__(RetrievalAuthorization)
    object.__setattr__(authorization, "eligibility_status", "required")
    object.__setattr__(authorization, "reason", reason)
    object.__setattr__(authorization, "_authorization_id", authorization_id)
    return authorization


def _nonempty(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrievalPolicyError(f"{field} must be a non-empty string")
    return value


def assess_retrieval_eligibility(
    claim: str,
    *,
    pure_logic: bool = False,
    supplied_material_closed: bool = False,
) -> RetrievalDecision:
    _nonempty(claim, field="claim")
    if not isinstance(pure_logic, bool) or not isinstance(supplied_material_closed, bool):
        raise RetrievalPolicyError("retrieval qualification flags must be booleans")
    if pure_logic:
        return _issue_decision("not-applicable", "pure-logic")
    if supplied_material_closed:
        return _issue_decision("not-applicable", "closed-supplied-material")
    return _issue_decision("required", "real-or-potentially-current-claim")


def gate_retrieval(
    decision: RetrievalDecision,
    *,
    phase_store: object,
) -> RetrievalDecision | RetrievalAuthorization:
    if (
        not isinstance(decision, RetrievalDecision)
        or decision._decision_id not in _ISSUED_DECISIONS
    ):
        raise RetrievalPolicyError("retrieval eligibility must be recorded first")
    from .state_machine import PhaseStore

    if not isinstance(phase_store, PhaseStore):
        raise RetrievalPolicyError("retrieval requires a verified U1 run context")
    if phase_store.current_phase != "U1":
        raise RetrievalPolicyError("retrieval requires a completed U1 run context")
    if not phase_store.has_valid_u1_source_coverage:
        raise RetrievalPolicyError("retrieval requires valid U1 source coverage")
    contract = phase_store.run_contract
    sensitivity = contract["sensitivity"]
    outbound_permission = contract["outbound_permission"]
    network_available = contract["capabilities"]["network"] == "available"
    if decision.status == "not-applicable":
        return decision
    if decision.status != "required":
        raise RetrievalPolicyError("retrieval decision has an unknown status")
    if not network_available:
        return _issue_decision("blocked", "required-network-unavailable")
    if outbound_permission == "denied":
        return _issue_decision("blocked", "required-outbound-disallowed")
    if sensitivity not in _SENSITIVITIES or outbound_permission not in _OUTBOUND_PERMISSIONS:
        raise RetrievalPolicyError("run context has an invalid outbound policy")
    return _issue_authorization(decision.reason)


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
) -> PreparedQuery:
    if (
        not isinstance(authorization, RetrievalAuthorization)
        or authorization._authorization_id not in _ISSUED_AUTHORIZATIONS
    ):
        raise RetrievalPolicyError("retrieval eligibility must be recorded before a query")
    if hostile_instruction_detected(query):
        raise RetrievalPolicyError("query contains a hostile instruction")
    redacted = redact_query(query)
    return PreparedQuery(
        eligibility_status="required",
        redacted_query=redacted,
        query_sha256=hashlib.sha256(redacted.encode("utf-8")).hexdigest(),
    )


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


def bounded_retrieve(
    operation: Callable[[], _T], *, max_retries: int
) -> RetrievalResult:
    if not callable(operation):
        raise TypeError("operation must be callable")
    if (
        not isinstance(max_retries, int)
        or isinstance(max_retries, bool)
        or not 1 <= max_retries <= 100
    ):
        raise RetrievalPolicyError("max_retries must be between one and 100")
    attempts: list[dict[str, object]] = []
    for attempt_number in range(1, max_retries + 1):
        try:
            value = operation()
        except RateLimitError as error:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "reason": "rate-limit",
                    "message": None,
                }
            )
            continue
        except RetrievalTimeoutError as error:
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
        return RetrievalResult("complete", tuple(attempts), value)
    return RetrievalResult("blocked", tuple(attempts), None)


def _canonical_date(value: object, *, field: str) -> str:
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
    _canonical_date(snapshot["event_date"], field="event_date")
    _canonical_date(snapshot["publication_date"], field="publication_date")
    lineage = snapshot["upstream_lineage"]
    if not isinstance(lineage, (list, tuple)) or not lineage:
        raise RetrievalPolicyError("upstream_lineage must be a non-empty string list")
    lineage_values = [_nonempty(value, field="upstream_lineage") for value in lineage]
    if len(lineage_values) != len(set(lineage_values)):
        raise RetrievalPolicyError("upstream_lineage contains duplicates")
    snapshot["upstream_lineage"] = lineage_values
    return snapshot


def make_source_record(
    *,
    source_id: str,
    url: str,
    event_date: str,
    publication_date: str,
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


def resource_status(
    *,
    path: Path | None = None,
    free_bytes: int | None = None,
    reserve_bytes: int,
    checkpoint: Mapping[str, object],
) -> ResourceStatus:
    if free_bytes is not None:
        raise RetrievalPolicyError("filesystem free space must be read from the path")
    if not isinstance(path, Path):
        raise RetrievalPolicyError("filesystem path is required for resource checks")
    if not isinstance(reserve_bytes, int) or isinstance(reserve_bytes, bool) or reserve_bytes < 0:
        raise RetrievalPolicyError("reserve_bytes must be a non-negative integer")
    if not isinstance(checkpoint, Mapping):
        raise RetrievalPolicyError("checkpoint must be an object")
    try:
        free = shutil.disk_usage(path).free
    except OSError:
        return ResourceStatus("unknown", copy.deepcopy(dict(checkpoint)), False)
    return ResourceStatus(
        status="needs_attention" if free < reserve_bytes else "running",
        checkpoint=copy.deepcopy(dict(checkpoint)),
        deleted=False,
    )


def inspect_acl(path: Path) -> str:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    try:
        metadata = path.stat()
    except (OSError, PermissionError):
        return "unknown"
    owner_matches = True
    if hasattr(os, "getuid"):
        owner_matches = metadata.st_uid == os.getuid()
    if os.access(path, os.R_OK) and owner_matches:
        return "verified-current-user"
    return "not-current-user"


__all__ = (
    "PreparedQuery",
    "RateLimitError",
    "ResourceStatus",
    "RetrievalAuthorization",
    "RetrievalDecision",
    "RetrievalPolicyError",
    "RetrievalResult",
    "RetrievalTimeoutError",
    "apply_external_content_policy",
    "assess_retrieval_eligibility",
    "bounded_retrieve",
    "gate_retrieval",
    "hostile_instruction_detected",
    "inspect_acl",
    "make_source_record",
    "prepare_query",
    "redact_query",
    "resource_status",
    "store_external_content",
    "validate_source_record",
)
