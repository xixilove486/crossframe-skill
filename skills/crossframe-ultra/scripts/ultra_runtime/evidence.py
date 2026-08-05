from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
from typing import Mapping, Sequence

from jsonschema import ValidationError

from check_crossframe_ultra_v82_source import EXPECTED_TREE_MERKLE_ROOT

from .constants import (
    ARTICLE_CONTRACT_VERSION,
    ARTIFACT_SCHEMA_VERSION,
    COMPILER_VERSION,
    FRAMEWORK_RAW_SHA256,
    FRAMEWORK_REVISION,
    FRAMEWORK_SEMANTIC_SHA256,
    FRAMEWORK_VERSION,
    RUNTIME_VERSION,
    VALIDATOR_VERSION,
)
from .jsonio import canonical_json_bytes
from .schemas import validate_instance


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
_UNKNOWN_FIELDS = frozenset(
    {"unknown_id", "location_ref", "description", "resolution_condition"}
)
_CURRENT_VERSION_BINDING = {
    "framework_version": FRAMEWORK_VERSION,
    "framework_revision": FRAMEWORK_REVISION,
    "framework_raw_sha256": FRAMEWORK_RAW_SHA256,
    "framework_semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
    "runtime_version": RUNTIME_VERSION,
    "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
    "compiler_version": COMPILER_VERSION,
    "validator_version": VALIDATOR_VERSION,
    "article_contract_version": ARTICLE_CONTRACT_VERSION,
    "source_tree_sha256": EXPECTED_TREE_MERKLE_ROOT,
}


class EvidenceValidationError(ValueError):
    """Raised when evidence identity, lineage, or temporal scope is invalid."""


class EvidenceFrozenError(RuntimeError):
    """Raised when a frozen U3 evidence ledger would be changed."""


@dataclass(frozen=True, init=False)
class EvidenceArtifactSeal:
    run_id: str
    version_binding: dict[str, object]
    phase_id: str
    evidence_cutoff: str
    content_sha256: str
    artifact_sha256: str


def _issue_seal(artifact: Mapping[str, object]) -> EvidenceArtifactSeal:
    seal = object.__new__(EvidenceArtifactSeal)
    object.__setattr__(seal, "run_id", str(artifact["run_id"]))
    object.__setattr__(seal, "version_binding", copy.deepcopy(artifact["version_binding"]))
    object.__setattr__(seal, "phase_id", str(artifact["phase_id"]))
    object.__setattr__(seal, "evidence_cutoff", str(artifact["evidence_cutoff"]))
    object.__setattr__(seal, "content_sha256", str(artifact["content_sha256"]))
    object.__setattr__(
        seal,
        "artifact_sha256",
        hashlib.sha256(canonical_json_bytes(artifact)).hexdigest(),
    )
    return seal


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


def _version_binding(value: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise EvidenceValidationError("version binding must be an object")
    snapshot = copy.deepcopy(dict(value))
    if snapshot != _CURRENT_VERSION_BINDING:
        raise EvidenceValidationError("version binding differs from current authority")
    return snapshot


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
        raise EvidenceValidationError("evidence entry fields are not closed")
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
    publication_date = _date_value(snapshot["publication_date"], field="publication_date")
    _nonempty_string(snapshot["interest"], field="interest")
    snapshot["upstream_lineage"] = _string_list(
        snapshot["upstream_lineage"], field="upstream_lineage"
    )
    _nonempty_string(snapshot["supported_claim"], field="supported_claim")
    _nonempty_string(snapshot["cannot_prove"], field="cannot_prove")
    observed_at = snapshot["observed_at"]
    parsed_observed = None if observed_at is None else _timestamp(observed_at, field="observed_at")
    if identity == "observed" and parsed_observed is None:
        raise EvidenceValidationError("observed evidence requires observed_at")
    if factual_requirement and identity not in _FACTUAL_IDENTITIES:
        raise EvidenceValidationError(f"{identity!r} cannot satisfy a factual evidence requirement")
    if identity in _NON_ESCALATING_IDENTITIES:
        snapshot["confidence"] = "unknown"
    if evidence_cutoff is not None:
        cutoff = _timestamp(evidence_cutoff, field="evidence_cutoff")
        if event_date > cutoff.date() or publication_date > cutoff.date():
            raise EvidenceValidationError("evidence source date is after the cutoff")
        if parsed_observed is not None and parsed_observed > cutoff:
            raise EvidenceValidationError("observed evidence is after the cutoff")
    return snapshot


def _validate_unknown(value: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise EvidenceValidationError("unknown must be an object")
    snapshot = copy.deepcopy(dict(value))
    if frozenset(snapshot) != _UNKNOWN_FIELDS:
        raise EvidenceValidationError("unknown fields are not closed")
    return {
        field: _nonempty_string(snapshot[field], field=field)
        for field in _UNKNOWN_FIELDS
    }


def validate_evidence_artifact(
    artifact: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_phase_id: str,
    expected_evidence_cutoff: str,
) -> EvidenceArtifactSeal:
    if not isinstance(artifact, Mapping):
        raise EvidenceValidationError("evidence artifact must be an object")
    snapshot = copy.deepcopy(dict(artifact))
    try:
        validate_instance("ultra-evidence-ledger.schema.json", snapshot)
    except ValidationError as error:
        raise EvidenceValidationError(f"evidence artifact violates public schema: {error.message}") from error
    supplied_content = snapshot.get("content_sha256")
    payload = copy.deepcopy(snapshot)
    payload.pop("content_sha256", None)
    if supplied_content != hashlib.sha256(canonical_json_bytes(payload)).hexdigest():
        raise EvidenceValidationError("evidence content hash is invalid")
    expected_binding = _version_binding(expected_version_binding)
    if (
        snapshot.get("run_id") != expected_run_id
        or snapshot.get("version_binding") != expected_binding
        or snapshot.get("phase_id") != expected_phase_id
        or snapshot.get("evidence_cutoff") != expected_evidence_cutoff
    ):
        raise EvidenceValidationError("evidence artifact differs from expected external authority")
    evidence_ids: set[str] = set()
    for entry in snapshot["entries"]:
        normalized = validate_evidence_entry(
            entry,
            evidence_cutoff=expected_evidence_cutoff,
        )
        if normalized != entry:
            raise EvidenceValidationError(
                "evidence entry is not in canonical normalized form"
            )
        evidence_id = str(normalized["evidence_id"])
        if evidence_id in evidence_ids:
            raise EvidenceValidationError("duplicate evidence_id in evidence artifact")
        evidence_ids.add(evidence_id)
    unknown_ids: set[str] = set()
    for unknown in snapshot["unknowns"]:
        normalized_unknown = _validate_unknown(unknown)
        unknown_id = normalized_unknown["unknown_id"]
        if unknown_id in unknown_ids:
            raise EvidenceValidationError("duplicate unknown_id in evidence artifact")
        unknown_ids.add(unknown_id)
    return _issue_seal(snapshot)


class EvidenceLedger:
    """Mutable evidence collection that becomes a hash-bound U3 artifact."""

    def __init__(
        self,
        run_id: str,
        evidence_cutoff: str,
        *,
        version_binding: Mapping[str, object] | None = None,
        generated_at: str | None = None,
    ) -> None:
        self.run_id = _nonempty_string(run_id, field="run_id")
        _timestamp(evidence_cutoff, field="evidence_cutoff")
        self.evidence_cutoff = evidence_cutoff
        self._version_binding = _version_binding(version_binding or _CURRENT_VERSION_BINDING)
        self._generated_at = generated_at or evidence_cutoff
        _timestamp(self._generated_at, field="generated_at")
        self._entries: list[dict[str, object]] = []
        self._unknowns: list[dict[str, str]] = []
        self._ids: set[str] = set()
        self._unknown_ids: set[str] = set()
        self._frozen = False

    @classmethod
    def from_entries(
        cls,
        run_id: str,
        evidence_cutoff: str,
        entries: Sequence[Mapping[str, object]],
        *,
        version_binding: Mapping[str, object] | None = None,
        generated_at: str | None = None,
    ) -> "EvidenceLedger":
        ledger = cls(
            run_id,
            evidence_cutoff,
            version_binding=version_binding,
            generated_at=generated_at,
        )
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
    def unknowns(self) -> tuple[dict[str, str], ...]:
        return tuple(copy.deepcopy(self._unknowns))

    @property
    def artifact(self) -> dict[str, object]:
        artifact: dict[str, object] = {
            "schema_id": "crossframe.ultra.v82.evidence-ledger",
            "schema_version": 1,
            "run_id": self.run_id,
            "version_binding": copy.deepcopy(self._version_binding),
            "generated_at": self._generated_at,
            "phase_id": "U3",
            "evidence_cutoff": self.evidence_cutoff,
            "entries": copy.deepcopy(self._entries),
            "unknowns": copy.deepcopy(self._unknowns),
        }
        artifact["content_sha256"] = hashlib.sha256(canonical_json_bytes(artifact)).hexdigest()
        return artifact

    @property
    def content_sha256(self) -> str:
        return str(self.artifact["content_sha256"])

    @property
    def artifact_sha256(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.artifact)).hexdigest()

    @property
    def explicit_unknowns(self) -> tuple[dict[str, object], ...]:
        return tuple(copy.deepcopy(entry) for entry in self._entries if entry["identity"] == "unknown")

    def append(self, entry: Mapping[str, object]) -> dict[str, object]:
        if self._frozen:
            raise EvidenceFrozenError("evidence ledger is frozen")
        snapshot = validate_evidence_entry(entry, evidence_cutoff=self.evidence_cutoff)
        evidence_id = str(snapshot["evidence_id"])
        if evidence_id in self._ids:
            raise EvidenceValidationError(f"duplicate evidence_id: {evidence_id}")
        self._ids.add(evidence_id)
        self._entries.append(snapshot)
        return copy.deepcopy(snapshot)

    def append_unknown(self, unknown: Mapping[str, object]) -> dict[str, str]:
        if self._frozen:
            raise EvidenceFrozenError("evidence ledger is frozen")
        snapshot = _validate_unknown(unknown)
        if snapshot["unknown_id"] in self._unknown_ids:
            raise EvidenceValidationError("duplicate unknown_id")
        self._unknown_ids.add(snapshot["unknown_id"])
        self._unknowns.append(snapshot)
        return copy.deepcopy(snapshot)

    def freeze(self) -> "EvidenceLedger":
        if not self._entries:
            raise EvidenceValidationError("evidence ledger requires at least one entry")
        validate_evidence_artifact(
            self.artifact,
            expected_run_id=self.run_id,
            expected_version_binding=self._version_binding,
            expected_phase_id="U3",
            expected_evidence_cutoff=self.evidence_cutoff,
        )
        self._frozen = True
        return self

    def seal(self) -> EvidenceArtifactSeal:
        self.freeze()
        return validate_evidence_artifact(
            self.artifact,
            expected_run_id=self.run_id,
            expected_version_binding=self._version_binding,
            expected_phase_id="U3",
            expected_evidence_cutoff=self.evidence_cutoff,
        )

    def fork(self, run_id: str, evidence_cutoff: str) -> "EvidenceLedger":
        next_run_id = _nonempty_string(run_id, field="run_id")
        if next_run_id == self.run_id:
            raise EvidenceValidationError("fork requires a new run_id")
        if _timestamp(evidence_cutoff, field="evidence_cutoff") <= _timestamp(
            self.evidence_cutoff, field="evidence_cutoff"
        ):
            raise EvidenceValidationError("fork requires a new evidence cutoff")
        forked = EvidenceLedger.from_entries(
            next_run_id,
            evidence_cutoff,
            self._entries,
            version_binding=self._version_binding,
            generated_at=evidence_cutoff,
        )
        for unknown in self._unknowns:
            forked.append_unknown(unknown)
        return forked

    def independence_clusters(self) -> tuple[tuple[str, ...], ...]:
        remaining = {str(entry["evidence_id"]): entry for entry in self._entries}
        clusters: list[tuple[str, ...]] = []
        while remaining:
            seed_id = next(iter(remaining))
            member_ids = {seed_id}
            lineage = set(remaining[seed_id]["upstream_lineage"]) | set(remaining[seed_id]["source_refs"])
            changed = True
            while changed:
                changed = False
                for evidence_id, entry in list(remaining.items()):
                    if evidence_id in member_ids:
                        continue
                    entry_lineage = set(entry["upstream_lineage"]) | set(entry["source_refs"])
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
            if entry["supported_claim"] == claim and entry["identity"] in _FACTUAL_IDENTITIES
        }
        return sum(1 for cluster in self.independence_clusters() if eligible_ids.intersection(cluster))

    def satisfies_factual_requirement(self, claim: str, *, require_observed: bool = False) -> bool:
        identities = {"observed"} if require_observed else _FACTUAL_IDENTITIES
        return any(
            entry["supported_claim"] == claim and entry["identity"] in identities
            for entry in self._entries
        )

    def confidence_for(self, evidence_id: str) -> str:
        for entry in self._entries:
            if entry["evidence_id"] == evidence_id:
                return "unknown" if entry["identity"] in _NON_ESCALATING_IDENTITIES else str(entry["confidence"])
        raise KeyError(evidence_id)


__all__ = (
    "EVIDENCE_IDENTITIES",
    "EvidenceArtifactSeal",
    "EvidenceFrozenError",
    "EvidenceLedger",
    "EvidenceValidationError",
    "validate_evidence_artifact",
    "validate_evidence_entry",
)
