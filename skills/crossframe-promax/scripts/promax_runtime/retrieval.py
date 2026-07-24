from __future__ import annotations

from typing import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

from jsonschema import ValidationError

from .validation import validate_bound_document


RETRIEVAL_DIRECTIONS = (
    "support",
    "reverse",
    "failure",
    "alternative_mechanism",
    "affected_or_low_power",
)
_ALLOWED_RELATIONS = {
    "support": {"supports", "mixed", "contextual"},
    "reverse": {"refutes", "mixed", "contextual"},
    "failure": {"refutes", "mixed", "contextual"},
    "alternative_mechanism": {"alternative_mechanism"},
    "affected_or_low_power": {"affected_position"},
}


class RetrievalSaturationError(ValueError):
    """Raised when a retrieval ledger is present but not saturated or auditable."""


def validate_retrieval_ledger(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    return validate_bound_document(
        "promax-retrieval-ledger.schema.json",
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )


def _required_claim_set(value: object) -> set[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise RetrievalSaturationError(
            "required_claim_ids must be a non-empty string sequence"
        )
    result = set(value)
    if len(result) != len(value):
        raise RetrievalSaturationError("required_claim_ids must not contain duplicates")
    return result


def _canonical_http_url(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise RetrievalSaturationError(f"{field} must be an HTTP(S) URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise RetrievalSaturationError(f"{field} is not a valid URL") from error
    scheme = parsed.scheme.casefold()
    if (
        scheme not in {"http", "https"}
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise RetrievalSaturationError(f"{field} must be an absolute HTTP(S) URL")
    host = parsed.hostname.casefold()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    default_port = (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    )
    netloc = host if port is None or default_port else f"{host}:{port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def validate_retrieval_saturation(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
    required_claim_ids: Sequence[str],
    strict_completion: bool = True,
) -> dict[str, object]:
    """Enforce five-way retrieval and two consecutive zero-novelty rounds."""

    if not isinstance(strict_completion, bool):
        raise RetrievalSaturationError("strict_completion must be boolean")
    required_claims = _required_claim_set(required_claim_ids)
    try:
        normalized = validate_retrieval_ledger(
            document,
            expected_run_id=expected_run_id,
            expected_source_snapshot_sha256=expected_source_snapshot_sha256,
        )
    except ValidationError as error:
        raise RetrievalSaturationError(
            f"retrieval ledger violates its schema: {error.message}"
        ) from error

    network_available = normalized.get("network_available")
    if network_available is False and strict_completion:
        raise RetrievalSaturationError(
            "network unavailability is structured incompleteness, not strict completion"
        )
    entries = normalized.get("entries")
    if not isinstance(entries, list):
        raise RetrievalSaturationError("retrieval entries must be an array")
    seen_retrieval_ids: set[str] = set()
    coverage = {claim_id: set() for claim_id in required_claims}
    sources_by_url: dict[str, Mapping[str, object]] = {}
    source_relations: list[tuple[str, Mapping[str, object]]] = []
    entry_rounds: list[int] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise RetrievalSaturationError("retrieval entry must be an object")
        retrieval_id = entry.get("retrieval_id")
        if not isinstance(retrieval_id, str) or retrieval_id in seen_retrieval_ids:
            raise RetrievalSaturationError(
                f"duplicate or invalid retrieval_id: {retrieval_id!r}"
            )
        seen_retrieval_ids.add(retrieval_id)
        round_number = entry.get("round")
        if not isinstance(round_number, int) or isinstance(round_number, bool):
            raise RetrievalSaturationError(
                f"retrieval {retrieval_id} must reference an integer round"
            )
        entry_rounds.append(round_number)
        direction = entry.get("direction")
        relation = entry.get("claim_relation")
        if direction not in _ALLOWED_RELATIONS or relation not in _ALLOWED_RELATIONS[direction]:
            raise RetrievalSaturationError(
                f"retrieval {retrieval_id} has incompatible direction/claim_relation"
            )
        claim_ids = entry.get("claim_ids")
        if not isinstance(claim_ids, list):
            raise RetrievalSaturationError(
                f"retrieval {retrieval_id} claim_ids must be an array"
            )
        for claim_id in required_claims.intersection(claim_ids):
            coverage[claim_id].add(direction)
        sources = entry.get("sources")
        if not isinstance(sources, list):
            raise RetrievalSaturationError(
                f"retrieval {retrieval_id} sources must be an array"
            )
        if network_available is True and not sources:
            raise RetrievalSaturationError(
                f"network retrieval {retrieval_id} must retain at least one real source"
            )
        for source in sources:
            if not isinstance(source, Mapping):
                raise RetrievalSaturationError("retrieval source must be an object")
            canonical_url = _canonical_http_url(
                source.get("url"),
                field=f"retrieval {retrieval_id} source.url",
            )
            if canonical_url in sources_by_url:
                raise RetrievalSaturationError(
                    f"duplicate source URL cannot be presented as independent: {canonical_url}"
                )
            sources_by_url[canonical_url] = source
            source_relations.append((canonical_url, source))

    expected_directions = set(RETRIEVAL_DIRECTIONS)
    for claim_id, observed_directions in coverage.items():
        if observed_directions != expected_directions:
            missing = sorted(expected_directions - observed_directions)
            raise RetrievalSaturationError(
                f"required claim {claim_id} lacks retrieval directions: {missing!r}"
            )

    for canonical_url, source in source_relations:
        relation = source.get("duplicate_relation")
        duplicate_of = source.get("duplicate_of_url")
        if relation == "independent":
            if duplicate_of is not None:
                raise RetrievalSaturationError(
                    f"independent source must not name duplicate_of_url: {canonical_url}"
                )
            continue
        target_url = _canonical_http_url(
            duplicate_of,
            field=f"source {canonical_url} duplicate_of_url",
        )
        if target_url == canonical_url:
            raise RetrievalSaturationError(
                f"source duplicate relation cannot point to itself: {canonical_url}"
            )
        target = sources_by_url.get(target_url)
        if target is None:
            raise RetrievalSaturationError(
                f"source duplicate relation target is absent from ledger: {target_url}"
            )
        if target.get("independence_group") != source.get("independence_group"):
            raise RetrievalSaturationError(
                "dependent source relation must retain the referenced independence_group"
            )

    rounds = normalized.get("saturation_rounds")
    if not isinstance(rounds, list) or len(rounds) < 2:
        raise RetrievalSaturationError(
            "retrieval saturation requires at least two completed rounds"
        )
    for expected_round, round_record in enumerate(rounds, start=1):
        if not isinstance(round_record, Mapping) or round_record.get(
            "round"
        ) != expected_round:
            raise RetrievalSaturationError(
                "retrieval saturation rounds must be contiguous from 1"
            )
        if round_record.get("substantive_novelty") is False and round_record.get(
            "changed_claim_ids"
        ) != []:
            raise RetrievalSaturationError(
                "a zero-novelty saturation round cannot report changed claims"
            )
    valid_rounds = set(range(1, len(rounds) + 1))
    unknown_rounds = set(entry_rounds) - valid_rounds
    if unknown_rounds:
        raise RetrievalSaturationError(
            f"retrieval entries reference unknown saturation rounds: {sorted(unknown_rounds)!r}"
        )
    empty_rounds = sorted(valid_rounds - set(entry_rounds))
    if empty_rounds:
        raise RetrievalSaturationError(
            f"saturation rounds cannot be self-reported without queries: {empty_rounds!r}"
        )
    for round_record in rounds[-2:]:
        if (
            round_record.get("substantive_novelty") is not False
            or round_record.get("changed_claim_ids") != []
        ):
            raise RetrievalSaturationError(
                "the final two retrieval rounds must have no substantive change"
            )
    return normalized
