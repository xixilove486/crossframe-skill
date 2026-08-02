from __future__ import annotations

import copy
from datetime import date, datetime, timezone
import hashlib
from typing import Mapping, Sequence

from .jsonio import canonical_json_bytes


EVIDENCE_IDENTITIES = (
    "observed",
    "reported",
    "inferred",
    "competing",
    "user-claim",
    "model-candidate",
    "simulated",
    "unknown",
)
_CONFIDENCE_VALUES = frozenset({"low", "medium", "high", "unknown"})
_FACTUAL_IDENTITIES = frozenset({"observed", "reported"})
_NON_ESCALATING_IDENTITIES = frozenset(
    {"user-claim", "model-candidate", "simulated", "unknown"}
)
_ENTRY_FIELDS = frozenset(
    {
        "evidence_id",
        "identity",
        "statement",
        "source_refs",
        "observed_at",
        "confidence",
        "event_date",
        "publication_date",
        "interest",
        "upstream_lineage",
        "supported_claim",
        "cannot_prove",
    }
)


class EvidenceValidationError(ValueError):
    """Raised when evidence identity, lineage, or temporal scope is invalid."""


class EvidenceFrozenError(RuntimeError):
    """Raised when a frozen U3 evidence ledger would be changed."""


def _nonempty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceValidationError(f"{field} must be a non-empty string")
    return value


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, (list, tuple)) or not value:
        raise EvidenceValidationError(f"{field} must be a non-empty string list")
    result = [_nonempty_string(item, field=field) for item in value]
    if len(result) != len(set(result)):
        raise EvidenceValidationError(f"{field} contains duplicates")
    return result


def _date_value(value: object, *, field: str) -> date:
    text = _nonempty_string(value, field=field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as error:
        raise EvidenceValidationError(f"{field} must use ISO date format") from error
    if text != parsed.isoformat():
        raise EvidenceValidationError(f"{field} must use canonical ISO date format")
    return parsed


def _timestamp(value: object, *, field: str) -> datetime:
    text = _nonempty_string(value, field=field)
    candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise EvidenceValidationError(f"{field} must be RFC3339") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceValidationError(f"{field} must include an offset")
    return parsed.astimezone(timezone.utc)


def validate_evidence_entry(
    entry: Mapping[str, object],
    *,
    factual_requirement: bool = False,
    evidence_cutoff: str | None = None,
) -> dict[str, object]:
    if not isinstance(entry, Mapping):
        raise EvidenceValidationError("evidence entry must be an object")
    snapshot = copy.deepcopy(dict(entry))
    if frozenset(snapshot) != _ENTRY_FIELDS:
        missing = sorted(_ENTRY_FIELDS - frozenset(snapshot))
        extra = sorted(frozenset(snapshot) - _ENTRY_FIELDS)
        raise EvidenceValidationError(
            f"evidence entry fields are not closed (missing={missing}, extra={extra})"
        )
    _nonempty_string(snapshot["evidence_id"], field="evidence_id")
    identity = snapshot["identity"]
    if identity not in EVIDENCE_IDENTITIES:
        raise EvidenceValidationError(f"invalid evidence identity: {identity!r}")
    _nonempty_string(snapshot["statement"], field="statement")
    snapshot["source_refs"] = _string_list(snapshot["source_refs"], field="source_refs")
    confidence = snapshot["confidence"]
    if confidence not in _CONFIDENCE_VALUES:
        raise EvidenceValidationError(f"invalid evidence confidence: {confidence!r}")
    event_date = _date_value(snapshot["event_date"], field="event_date")
    publication_date = _date_value(
        snapshot["publication_date"], field="publication_date"
    )
    _nonempty_string(snapshot["interest"], field="interest")
    snapshot["upstream_lineage"] = _string_list(
        snapshot["upstream_lineage"], field="upstream_lineage"
    )
    _nonempty_string(snapshot["supported_claim"], field="supported_claim")
    _nonempty_string(snapshot["cannot_prove"], field="cannot_prove")

    observed_at = snapshot["observed_at"]
    parsed_observed: datetime | None = None
    if observed_at is not None:
        parsed_observed = _timestamp(observed_at, field="observed_at")
    if identity == "observed" and parsed_observed is None:
        raise EvidenceValidationError("observed evidence requires observed_at")
    if factual_requirement and identity not in _FACTUAL_IDENTITIES:
        raise EvidenceValidationError(
            f"{identity!r} cannot satisfy a factual evidence requirement"
        )
    if identity in _NON_ESCALATING_IDENTITIES:
        snapshot["confidence"] = "unknown"

    if evidence_cutoff is not None:
        cutoff = _timestamp(evidence_cutoff, field="evidence_cutoff")
        cutoff_date = cutoff.date()
        if event_date > cutoff_date or publication_date > cutoff_date:
            raise EvidenceValidationError("evidence source date is after the cutoff")
        if parsed_observed is not None and parsed_observed > cutoff:
            raise EvidenceValidationError("observed evidence is after the cutoff")
    return snapshot


class EvidenceLedger:
    """U3 evidence ledger with explicit identities and upstream clustering."""

    def __init__(self, run_id: str, evidence_cutoff: str) -> None:
        self.run_id = _nonempty_string(run_id, field="run_id")
        _timestamp(evidence_cutoff, field="evidence_cutoff")
        self.evidence_cutoff = evidence_cutoff
        self._entries: list[dict[str, object]] = []
        self._ids: set[str] = set()
        self._frozen = False

    @classmethod
    def from_entries(
        cls,
        run_id: str,
        evidence_cutoff: str,
        entries: Sequence[Mapping[str, object]],
    ) -> "EvidenceLedger":
        ledger = cls(run_id, evidence_cutoff)
        for entry in entries:
            ledger.append(entry)
        return ledger

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def entries(self) -> tuple[dict[str, object], ...]:
        return tuple(copy.deepcopy(self._entries))

    @property
    def content_sha256(self) -> str:
        payload = {
            "run_id": self.run_id,
            "evidence_cutoff": self.evidence_cutoff,
            "entries": self._entries,
        }
        return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

    @property
    def explicit_unknowns(self) -> tuple[dict[str, object], ...]:
        return tuple(
            copy.deepcopy(entry)
            for entry in self._entries
            if entry["identity"] == "unknown"
        )

    def append(self, entry: Mapping[str, object]) -> dict[str, object]:
        if self._frozen:
            raise EvidenceFrozenError("evidence ledger is frozen")
        snapshot = validate_evidence_entry(
            entry,
            evidence_cutoff=self.evidence_cutoff,
        )
        evidence_id = str(snapshot["evidence_id"])
        if evidence_id in self._ids:
            raise EvidenceValidationError(f"duplicate evidence_id: {evidence_id}")
        self._ids.add(evidence_id)
        self._entries.append(snapshot)
        return copy.deepcopy(snapshot)

    def freeze(self) -> "EvidenceLedger":
        self._frozen = True
        return self

    def fork(self, run_id: str, evidence_cutoff: str) -> "EvidenceLedger":
        next_run_id = _nonempty_string(run_id, field="run_id")
        if next_run_id == self.run_id:
            raise EvidenceValidationError("fork requires a new run_id")
        return EvidenceLedger.from_entries(
            next_run_id,
            evidence_cutoff,
            self._entries,
        )

    def independence_clusters(self) -> tuple[tuple[str, ...], ...]:
        remaining = {str(entry["evidence_id"]): entry for entry in self._entries}
        clusters: list[tuple[str, ...]] = []
        while remaining:
            seed_id = next(iter(remaining))
            member_ids = {seed_id}
            lineage = set(remaining[seed_id]["upstream_lineage"]) | set(
                remaining[seed_id]["source_refs"]
            )
            changed = True
            while changed:
                changed = False
                for evidence_id, entry in list(remaining.items()):
                    if evidence_id in member_ids:
                        continue
                    entry_lineage = set(entry["upstream_lineage"]) | set(
                        entry["source_refs"]
                    )
                    if lineage.intersection(entry_lineage):
                        member_ids.add(evidence_id)
                        lineage.update(entry_lineage)
                        changed = True
            for evidence_id in member_ids:
                remaining.pop(evidence_id, None)
            clusters.append(tuple(sorted(member_ids)))
        return tuple(sorted(clusters, key=lambda cluster: cluster[0]))

    def independent_support_count(self, claim: str) -> int:
        eligible_ids = {
            str(entry["evidence_id"])
            for entry in self._entries
            if entry["supported_claim"] == claim
            and entry["identity"] in _FACTUAL_IDENTITIES
        }
        return sum(
            1
            for cluster in self.independence_clusters()
            if eligible_ids.intersection(cluster)
        )

    def satisfies_factual_requirement(
        self, claim: str, *, require_observed: bool = False
    ) -> bool:
        required_identities = {"observed"} if require_observed else _FACTUAL_IDENTITIES
        return any(
            entry["supported_claim"] == claim
            and entry["identity"] in required_identities
            for entry in self._entries
        )

    def confidence_for(self, evidence_id: str) -> str:
        for entry in self._entries:
            if entry["evidence_id"] == evidence_id:
                if entry["identity"] in _NON_ESCALATING_IDENTITIES:
                    return "unknown"
                return str(entry["confidence"])
        raise KeyError(evidence_id)


__all__ = (
    "EVIDENCE_IDENTITIES",
    "EvidenceFrozenError",
    "EvidenceLedger",
    "EvidenceValidationError",
    "validate_evidence_entry",
)
