from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
import re
from typing import Any

from jsonschema import ValidationError

from .errors import UltraSchemaError
from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


INSIGHT_EFFECTS = (
    "changes-ranking",
    "explains-residual",
    "changes-observable-forecast",
    "changes-counterfactual",
    "changes-intervention",
    "identifies-circle-scale-channel",
)

VERDICT_KINDS = (
    "fact",
    "prediction",
    "value",
    "responsibility",
    "authorization",
)

ACTION_KINDS = (
    "active",
    "delay",
    "probe",
    "exit-or-transfer",
    "maintain-status-quo",
    "no-action",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_AUTHORITY_FIELDS = (
    "evidence_ledger_artifact_sha256",
    "world_volume_artifact_sha256",
    "transformation_ledger_artifact_sha256",
    "concept_disposition_artifact_sha256",
)
_GRAPH_ROLE_FIELDS = {
    "claim": ("claims", "claim_id"),
    "mechanism": ("mechanisms", "mechanism_id"),
    "edge": ("edges", "edge_id"),
    "explanation": ("explanations", "explanation_id"),
    "insight": ("insights", "insight_id"),
}
_ENVELOPE_ID_FIELDS = frozenset({"schema_id", "run_id", "phase_id"})
_FACT_IDENTITIES = frozenset(
    {"observed", "reported", "inferred-from-material"}
)
_MATERIAL_EVIDENCE_IDENTITIES = frozenset({"observed", "reported", "inferred"})


class ClaimMechanismError(ValueError):
    """Raised when a U6 graph changes identity, evidence, or authority roles."""


class JudgmentError(ValueError):
    """Raised when a U9 verdict changes evidence, identity, or authority roles."""


def qualifies_as_insight(candidate: Mapping[str, object]) -> bool:
    effects = set(candidate["effects"])
    return bool(effects.intersection(INSIGHT_EFFECTS))


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ClaimMechanismError(
                    f"{label} has a non-native JSON object key"
                )
            _require_native_json(item, label=label)
        return
    if value_type is list:
        for item in value:
            _require_native_json(item, label=label)
        return
    if value_type in {str, int, float, bool, type(None)}:
        return
    raise ClaimMechanismError(f"{label} contains a non-native JSON value")


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimMechanismError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ClaimMechanismError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ClaimMechanismError(
            f"artifact authority is not canonical JSON: {error}"
        ) from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ClaimMechanismError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _validated_public_authorities(
    *,
    expected_run_id: object,
    expected_version_binding: Mapping[str, object],
    expected_evidence_ledger_artifact_sha256: object,
    expected_world_volume_artifact_sha256: object,
    expected_transformation_ledger_artifact_sha256: object,
    expected_concept_disposition_artifact_sha256: object,
) -> tuple[str, dict[str, Any], tuple[str, str, str, str]]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise ClaimMechanismError("expected run_id authority must be explicit")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    hashes = (
        _require_sha256(
            expected_evidence_ledger_artifact_sha256,
            label="expected U3 evidence ledger artifact hash",
        ),
        _require_sha256(
            expected_world_volume_artifact_sha256,
            label="expected U4 world volume artifact hash",
        ),
        _require_sha256(
            expected_transformation_ledger_artifact_sha256,
            label="expected U5 transformation ledger artifact hash",
        ),
        _require_sha256(
            expected_concept_disposition_artifact_sha256,
            label="expected U5 concept disposition artifact hash",
        ),
    )
    if len(set(hashes)) != len(hashes):
        raise ClaimMechanismError(
            "U3/U4/U5 authority roles require four distinct artifact hashes"
        )
    return expected_run_id, binding, hashes


def _phase(
    schema_name: str,
    artifact: Mapping[str, object],
    *,
    schema_id: str,
    run_id: str,
    version_binding: Mapping[str, object],
    phase_id: str,
    label: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(artifact, label=label)
    try:
        return validate_phase_artifact(
            schema_name,
            snapshot,
            expected_schema_id=schema_id,
            expected_run_id=run_id,
            expected_version_binding=version_binding,
            expected_phase_id=phase_id,
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise ClaimMechanismError(f"invalid {label}: {error}") from error


def _records_by_id(
    records: Sequence[Mapping[str, Any]], *, field: str, label: str
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identifier = record[field]
        if identifier in result:
            raise ClaimMechanismError(f"duplicate {label} identity {identifier!r}")
        result[identifier] = record
    return result


def _validate_concept_links(
    concept: Mapping[str, Any],
    evidence: Mapping[str, Any],
    world: Mapping[str, Any],
    transformations: Mapping[str, Any],
) -> None:
    if concept["closure_complete"] is not True or concept["unvisited_concept_ids"]:
        raise ClaimMechanismError(
            "U6 cannot consume an incomplete U5 concept disposition"
        )
    evidence_ids = {entry["evidence_id"] for entry in evidence["entries"]}
    unknown_ids = {
        *(item["unknown_id"] for item in evidence["unknowns"]),
        *(item["unknown_id"] for item in world["unknowns"]),
    }
    transformation_ids = {
        item["transform_id"] for item in transformations["transformations"]
    }
    for record in (*concept["dispositions"], *concept["semantic_obligations"]):
        if not set(record["evidence_ids"]).issubset(evidence_ids):
            raise ClaimMechanismError(
                "U5 concept disposition cites evidence outside the sealed U3 ledger"
            )
        if not set(record["unknown_ids"]).issubset(unknown_ids):
            raise ClaimMechanismError(
                "U5 concept disposition cites an unknown outside U3/U4"
            )
        if not set(record["transformation_ids"]).issubset(transformation_ids):
            raise ClaimMechanismError(
                "U5 concept disposition cites an unsealed transformation"
            )


def _validate_upstream(
    *,
    evidence_ledger: Mapping[str, object],
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    concept_disposition: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_hashes: tuple[str, str, str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence = _phase(
        "ultra-evidence-ledger.schema.json",
        evidence_ledger,
        schema_id="crossframe.ultra.v82.evidence-ledger",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U3",
        label="U3 evidence ledger",
    )
    world = _phase(
        "ultra-world-volume.schema.json",
        world_volume,
        schema_id="crossframe.ultra.v82.world-volume",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U4",
        label="U4 world volume",
    )
    transformations = _phase(
        "ultra-transformation-ledger.schema.json",
        transformation_ledger,
        schema_id="crossframe.ultra.v82.transformation-ledger",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U5",
        label="U5 transformation ledger",
    )
    concept = _phase(
        "ultra-concept-disposition.schema.json",
        concept_disposition,
        schema_id="crossframe.ultra.v82.concept-disposition",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U5",
        label="U5 concept disposition",
    )

    labels = (
        "U3 evidence ledger",
        "U4 world volume",
        "U5 transformation ledger",
        "U5 concept disposition",
    )
    for label, artifact, expected_hash in zip(
        labels,
        (evidence, world, transformations, concept),
        expected_hashes,
        strict=True,
    ):
        if _canonical_sha256(artifact) != expected_hash:
            raise ClaimMechanismError(
                f"{label} full artifact hash differs from external authority"
            )

    evidence_hash, world_hash, transformations_hash, _ = expected_hashes
    if (
        world["evidence_artifact_sha256"] != evidence_hash
        or world["evidence_content_sha256"] != evidence["content_sha256"]
    ):
        raise ClaimMechanismError("U4 world volume carries a stale upstream hash chain")
    transformation_chain = {
        "evidence_artifact_sha256": evidence_hash,
        "evidence_content_sha256": evidence["content_sha256"],
        "world_volume_artifact_sha256": world_hash,
        "world_volume_content_sha256": world["content_sha256"],
    }
    if any(
        transformations[field] != expected
        for field, expected in transformation_chain.items()
    ):
        raise ClaimMechanismError(
            "U5 transformation ledger carries a stale upstream hash chain"
        )
    concept_chain = {
        **transformation_chain,
        "transformation_ledger_artifact_sha256": transformations_hash,
        "transformation_ledger_content_sha256": transformations["content_sha256"],
    }
    if any(concept[field] != expected for field, expected in concept_chain.items()):
        raise ClaimMechanismError(
            "U5 concept disposition carries a stale upstream hash chain"
        )
    _validate_concept_links(concept, evidence, world, transformations)
    return evidence, world, transformations, concept


def _assert_graph_authorities(
    graph: Mapping[str, Any], expected_hashes: tuple[str, str, str, str]
) -> None:
    for field, expected in zip(_AUTHORITY_FIELDS, expected_hashes, strict=True):
        if graph.get(field) != expected:
            role = {
                "evidence_ledger_artifact_sha256": "U3 evidence ledger",
                "world_volume_artifact_sha256": "U4 world volume",
                "transformation_ledger_artifact_sha256": "U5 transformation ledger",
                "concept_disposition_artifact_sha256": "U5 concept disposition",
            }[field]
            raise ClaimMechanismError(
                f"U6 graph {role} authority does not match external upstream authority"
            )


def _identifier_values(value: object) -> set[str]:
    identifiers: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _ENVELOPE_ID_FIELDS:
                continue
            if key.endswith("_id") and type(item) is str:
                identifiers.add(item)
            elif key.endswith("_ids") and isinstance(item, list):
                identifiers.update(element for element in item if type(element) is str)
            identifiers.update(_identifier_values(item))
    elif isinstance(value, list):
        for item in value:
            identifiers.update(_identifier_values(item))
    return identifiers


def _validate_identity_roles(
    graph: Mapping[str, Any],
    upstream: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Mapping[str, Any]]]:
    catalogs: dict[str, dict[str, Mapping[str, Any]]] = {}
    used: set[str] = set()
    reserved = set().union(*(_identifier_values(artifact) for artifact in upstream))
    for role, (collection_field, identity_field) in _GRAPH_ROLE_FIELDS.items():
        catalog = _records_by_id(
            graph[collection_field], field=identity_field, label=role
        )
        role_ids = set(catalog)
        if role_ids & used or role_ids & reserved:
            raise ClaimMechanismError(
                "U6 definition identity is reused across artifact identity roles"
            )
        used.update(role_ids)
        catalogs[role] = catalog
    return catalogs


def _validate_ranking(graph: Mapping[str, Any]) -> None:
    ranks = [item["rank"] for item in graph["explanations"]]
    justification = graph["partial_ranking_justification"]
    if justification is None:
        if len(ranks) != 4 or set(ranks) != {1, 2, 3, 4}:
            raise ClaimMechanismError(
                "total ranking requires the unique ranks 1, 2, 3, and 4"
            )
        return

    ranked = [rank for rank in ranks if rank is not None]
    if not 1 <= len(ranked) < 4:
        raise ClaimMechanismError(
            "justified partial ranking requires one to three ranked explanations"
        )
    if len(set(ranked)) != len(ranked) or set(ranked) != set(
        range(1, len(ranked) + 1)
    ):
        raise ClaimMechanismError(
            "justified partial ranking requires a unique contiguous prefix from rank 1"
        )
    if sum(rank is None for rank in ranks) != 4 - len(ranked):
        raise ClaimMechanismError(
            "unranked partial explanations must carry explicit null ranks"
        )


def _validate_claim_evidence(
    claims: Mapping[str, Mapping[str, Any]],
    mechanisms: Mapping[str, Mapping[str, Any]],
    evidence: Mapping[str, Any],
) -> None:
    entries = _records_by_id(
        evidence["entries"], field="evidence_id", label="evidence"
    )
    for claim in claims.values():
        refs = claim["evidence_refs"]
        if not set(refs).issubset(entries):
            raise ClaimMechanismError("claim evidence_refs do not resolve the U3 ledger")
        identities = {entries[ref]["identity"] for ref in refs}
        claim_identity = claim["identity"]
        if "simulated" in identities and claim_identity != "simulated-result":
            raise ClaimMechanismError(
                "a simulated result cannot be promoted to a material fact"
            )
        if "user-claim" in identities and claim_identity != "user-claim":
            raise ClaimMechanismError(
                "a user claim cannot be treated as material evidence"
            )
        if claim_identity in _FACT_IDENTITIES:
            if not refs:
                raise ClaimMechanismError(
                    "a material claim must cite frozen U3 evidence"
                )
            if not identities.issubset(_MATERIAL_EVIDENCE_IDENTITIES):
                raise ClaimMechanismError(
                    "a material claim uses non-material evidence identity"
                )
        if claim_identity == "observed" and identities != {"observed"}:
            raise ClaimMechanismError(
                "an observed claim must resolve only observed evidence"
            )
        if claim_identity == "reported" and not identities.issubset(
            {"observed", "reported"}
        ):
            raise ClaimMechanismError(
                "a reported claim cannot upgrade another evidence identity"
            )

    prohibited_mechanism_identities = {
        "user-claim",
        "model-candidate",
        "simulated",
        "unknown",
    }
    for mechanism in mechanisms.values():
        refs = mechanism["evidence_refs"]
        if not set(refs).issubset(entries):
            raise ClaimMechanismError(
                "mechanism evidence_refs do not resolve the U3 ledger"
            )
        if any(
            entries[ref]["identity"] in prohibited_mechanism_identities
            for ref in refs
        ):
            raise ClaimMechanismError(
                "mechanism support cannot promote user, model, simulated, or unknown identity"
            )


def _validate_graph_references(
    graph: Mapping[str, Any],
    catalogs: Mapping[str, Mapping[str, Mapping[str, Any]]],
    evidence: Mapping[str, Any],
    world: Mapping[str, Any],
    transformations: Mapping[str, Any],
    concept: Mapping[str, Any],
) -> None:
    claims = catalogs["claim"]
    mechanisms = catalogs["mechanism"]
    explanations = catalogs["explanation"]
    insights = catalogs["insight"]
    if graph["central_claim_id"] not in claims:
        raise ClaimMechanismError("central claim does not resolve a U6 claim identity")
    if claims[graph["central_claim_id"]]["status"] != "active":
        raise ClaimMechanismError("central claim must remain active in the U6 graph")

    evidence_ids = {entry["evidence_id"] for entry in evidence["entries"]}
    channel_ids = {channel["channel_id"] for channel in world["channels"]}
    general_refs = {
        *claims,
        *mechanisms,
        *_identifier_values(evidence),
        *_identifier_values(world),
        *_identifier_values(transformations),
        *_identifier_values(concept),
    }
    for mechanism in mechanisms.values():
        if not set(mechanism["input_refs"]).issubset(general_refs):
            raise ClaimMechanismError(
                "mechanism input_refs do not resolve a frozen artifact identity"
            )
        if not set(mechanism["output_refs"]).issubset(general_refs):
            raise ClaimMechanismError(
                "mechanism output_refs do not resolve a frozen artifact identity"
            )
        if not set(mechanism["channel_refs"]).issubset(channel_ids):
            raise ClaimMechanismError(
                "mechanism channel_refs do not resolve a real U4 channel"
            )
        if not set(mechanism["evidence_refs"]).issubset(evidence_ids):
            raise ClaimMechanismError(
                "mechanism evidence_refs do not resolve the U3 ledger"
            )

    for explanation in explanations.values():
        if not set(explanation["claim_ids"]).issubset(claims):
            raise ClaimMechanismError(
                "explanation claim_ids do not resolve U6 claims"
            )
        if not set(explanation["mechanism_ids"]).issubset(mechanisms):
            raise ClaimMechanismError(
                "explanation mechanism_ids do not resolve U6 mechanisms"
            )

    graph_refs = {
        "claim_id": claims,
        "mechanism_id": mechanisms,
        "explanation_id": explanations,
        "insight_id": insights,
    }
    for edge in catalogs["edge"].values():
        for endpoint in (edge["source"], edge["target"]):
            field, identifier = next(iter(endpoint.items()))
            if identifier not in graph_refs[field]:
                raise ClaimMechanismError(
                    f"edge {field} does not resolve its declared U6 identity role"
                )
        if edge["edge_type"] != "qualifies" and any(
            "insight_id" in endpoint for endpoint in (edge["source"], edge["target"])
        ):
            raise ClaimMechanismError(
                "insight cannot become mechanism or framework authority"
            )

    by_kind = {record["kind"]: record for record in explanations.values()}
    main = by_kind["main"]
    rival = by_kind["strongest-rival"]
    mixture = by_kind["mixture"]
    if graph["central_claim_id"] not in main["claim_ids"]:
        raise ClaimMechanismError("main explanation must retain the central claim")
    if (
        set(main["claim_ids"]) == set(rival["claim_ids"])
        and set(main["mechanism_ids"]) == set(rival["mechanism_ids"])
    ):
        raise ClaimMechanismError(
            "strongest rival must be distinct from the main explanation"
        )
    main_refs = {*main["claim_ids"], *main["mechanism_ids"]}
    rival_refs = {*rival["claim_ids"], *rival["mechanism_ids"]}
    mixture_refs = {*mixture["claim_ids"], *mixture["mechanism_ids"]}
    if not mixture_refs.intersection(main_refs) or not mixture_refs.intersection(
        rival_refs
    ):
        raise ClaimMechanismError(
            "mixture explanation must combine the main and strongest-rival paths"
        )


def _validate_semantics(
    graph: Mapping[str, Any],
    evidence: Mapping[str, Any],
    world: Mapping[str, Any],
    transformations: Mapping[str, Any],
    concept: Mapping[str, Any],
) -> None:
    catalogs = _validate_identity_roles(
        graph, (evidence, world, transformations, concept)
    )
    _validate_ranking(graph)
    _validate_claim_evidence(
        catalogs["claim"], catalogs["mechanism"], evidence
    )
    _validate_graph_references(
        graph, catalogs, evidence, world, transformations, concept
    )
    if any(not qualifies_as_insight(insight) for insight in catalogs["insight"].values()):
        raise ClaimMechanismError(
            "U6 insight has no frozen ranking, residual, forecast, counterfactual, "
            "intervention, circle, scale, or channel effect"
        )


def _validate_claim_mechanism_graph(
    graph: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    concept_disposition: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_ledger_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_concept_disposition_artifact_sha256: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(graph, label="U6 claim/mechanism graph")
    run_id, binding, expected_hashes = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_ledger_artifact_sha256=(
            expected_evidence_ledger_artifact_sha256
        ),
        expected_world_volume_artifact_sha256=(
            expected_world_volume_artifact_sha256
        ),
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_concept_disposition_artifact_sha256=(
            expected_concept_disposition_artifact_sha256
        ),
    )
    evidence, world, transformations, concept = _validate_upstream(
        evidence_ledger=evidence_ledger,
        world_volume=world_volume,
        transformation_ledger=transformation_ledger,
        concept_disposition=concept_disposition,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
    )
    try:
        snapshot = validate_phase_artifact(
            "ultra-claim-mechanism-graph.schema.json",
            snapshot,
            expected_schema_id="crossframe.ultra.v82.claim-mechanism-graph",
            expected_run_id=run_id,
            expected_version_binding=binding,
            expected_phase_id="U6",
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise ClaimMechanismError(
            f"invalid U6 claim/mechanism graph or ranking: {error}"
        ) from error
    _assert_graph_authorities(snapshot, expected_hashes)
    _validate_semantics(snapshot, evidence, world, transformations, concept)
    return snapshot


def _seal_claim_mechanism_graph(
    graph: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    concept_disposition: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_ledger_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_concept_disposition_artifact_sha256: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(graph, label="unsealed U6 claim/mechanism graph")
    if "content_sha256" in snapshot:
        raise ClaimMechanismError(
            "U6 producer accepts an unsealed graph without content_sha256"
        )
    run_id, binding, expected_hashes = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_ledger_artifact_sha256=(
            expected_evidence_ledger_artifact_sha256
        ),
        expected_world_volume_artifact_sha256=(
            expected_world_volume_artifact_sha256
        ),
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_concept_disposition_artifact_sha256=(
            expected_concept_disposition_artifact_sha256
        ),
    )
    _validate_upstream(
        evidence_ledger=evidence_ledger,
        world_volume=world_volume,
        transformation_ledger=transformation_ledger,
        concept_disposition=concept_disposition,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
    )
    _assert_graph_authorities(snapshot, expected_hashes)
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_claim_mechanism_graph(
        snapshot,
        evidence_ledger=evidence_ledger,
        world_volume=world_volume,
        transformation_ledger=transformation_ledger,
        concept_disposition=concept_disposition,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_evidence_ledger_artifact_sha256=expected_hashes[0],
        expected_world_volume_artifact_sha256=expected_hashes[1],
        expected_transformation_ledger_artifact_sha256=expected_hashes[2],
        expected_concept_disposition_artifact_sha256=expected_hashes[3],
    )


def _verdict_rank_prefix(verdict: Mapping[str, Any]) -> None:
    ranking = verdict["explanation_ranking"]
    explanation_ids = [item["explanation_id"] for item in ranking]
    if len(explanation_ids) != len(set(explanation_ids)):
        raise JudgmentError("verdict explanation identities must be unique")
    ranks = [item["rank"] for item in ranking]
    if verdict["judgment_kind"] == "best-current":
        if verdict["partial_ranking_justification"] is not None:
            raise JudgmentError(
                "best-current judgment cannot carry a partial-ranking justification"
            )
        if ranks != [1, 2, 3, 4] and set(ranks) != {1, 2, 3, 4}:
            raise JudgmentError(
                "best-current judgment requires unique total ranks one through four"
            )
        return

    justification = verdict["partial_ranking_justification"]
    if type(justification) is not str or not justification.strip():
        raise JudgmentError(
            "non-decidability requires an explicit partial-ranking justification"
        )
    ranked = [rank for rank in ranks if rank is not None]
    if not 1 <= len(ranked) < 4:
        raise JudgmentError(
            "non-decidability requires one to three ranked explanations"
        )
    if ranked != list(range(1, len(ranked) + 1)):
        raise JudgmentError(
            "non-decidability ranking must be a contiguous prefix from rank one"
        )
    if ranks[len(ranked) :] != [None] * (4 - len(ranked)):
        raise JudgmentError(
            "non-decidability ranking must leave only a null tail"
        )


def _validate_public_verdict_semantics(
    verdict: Mapping[str, Any],
    evidence: Mapping[str, Any],
    lineage: Mapping[str, Any],
) -> None:
    expected_hashes = (_canonical_sha256(evidence), _canonical_sha256(lineage))
    if len(set(expected_hashes)) != 2:
        raise JudgmentError("U3 evidence and U7 lineage authority must be distinct")
    if (
        verdict.get("evidence_ledger_artifact_sha256"),
        verdict.get("recursive_lineage_artifact_sha256"),
    ) != expected_hashes:
        raise JudgmentError(
            "verdict U3 evidence or U7 lineage authority does not match its supplied artifact"
        )

    _verdict_rank_prefix(verdict)
    locks = verdict["five_verdicts"]
    by_kind = {item["kind"]: item for item in locks}
    if set(by_kind) != set(VERDICT_KINDS) or len(locks) != len(VERDICT_KINDS):
        raise JudgmentError("verdict must keep exactly five independent lock kinds")
    lock_ids = [item["verdict_id"] for item in locks]
    if len(set(lock_ids)) != len(VERDICT_KINDS):
        raise JudgmentError("five verdict lock identities must be mutually distinct")

    evidence_records = {
        item["evidence_id"]: item for item in evidence.get("entries", [])
    }
    lineage_node_ids = {item["node_id"] for item in lineage.get("nodes", [])}
    public_reserved = _identifier_values(evidence) | _identifier_values(lineage)
    if set(lock_ids).intersection(public_reserved):
        raise JudgmentError(
            "verdict lock identity cannot reuse an evidence or lineage identity"
        )

    for lock in locks:
        if not set(lock["evidence_refs"]).issubset(evidence_records):
            raise JudgmentError(
                f"{lock['kind']} verdict evidence_refs do not resolve the sealed U3 ledger"
            )
        if not set(lock["recursive_node_ids"]).issubset(lineage_node_ids):
            raise JudgmentError(
                f"{lock['kind']} verdict recursive_node_ids do not resolve U7"
            )

    factual = by_kind["fact"]
    if not any(
        factual[field]
        for field in (
            "evidence_refs",
            "claim_ids",
            "mechanism_ids",
            "recursive_node_ids",
        )
    ):
        raise JudgmentError(
            "a factual verdict requires material support rather than rhetoric"
        )
    material_identities = {"observed", "reported", "inferred"}
    if any(
        evidence_records[ref]["identity"] not in material_identities
        for ref in factual["evidence_refs"]
    ):
        raise JudgmentError(
            "a factual verdict cannot promote a user, model, simulated, or unknown identity"
        )

    if verdict["judgment_kind"] == "best-current":
        main = verdict["main_verdict"]
        if not set(main["decisive_evidence_refs"]).issubset(evidence_records):
            raise JudgmentError(
                "main verdict decisive evidence does not resolve the sealed U3 ledger"
            )
        if not set(main["decisive_node_ids"]).issubset(lineage_node_ids):
            raise JudgmentError(
                "main verdict decisive nodes do not resolve the sealed U7 lineage"
            )
        if main["confidence"] == "high" and verdict["decisive_unknown_ids"]:
            raise JudgmentError(
                "high confidence cannot retain an unresolved decisive unknown"
            )
        if main["confidence"] == "low" and (
            not verdict["assumptions"] or not main["reversal_conditions"]
        ):
            raise JudgmentError(
                "low confidence requires explicit assumptions and reversal conditions"
            )


def _validated_public_verdict_inputs(
    verdict: Mapping[str, object],
    evidence: Mapping[str, object],
    lineage: Mapping[str, object],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    verdict_snapshot = _snapshot_mapping(verdict, label="U9 verdict")
    run_id = verdict_snapshot.get("run_id")
    binding = verdict_snapshot.get("version_binding")
    if type(run_id) is not str or not isinstance(binding, Mapping):
        raise JudgmentError("U9 verdict must expose its run and version authority")
    evidence_snapshot = _phase(
        "ultra-evidence-ledger.schema.json",
        evidence,
        schema_id="crossframe.ultra.v82.evidence-ledger",
        run_id=run_id,
        version_binding=binding,
        phase_id="U3",
        label="U3 evidence ledger",
    )
    lineage_snapshot = _phase(
        "ultra-recursive-lineage.schema.json",
        lineage,
        schema_id="crossframe.ultra.v82.recursive-lineage",
        run_id=run_id,
        version_binding=binding,
        phase_id="U7",
        label="U7 recursive lineage",
    )
    verdict_snapshot = _phase(
        "ultra-verdict.schema.json",
        verdict_snapshot,
        schema_id="crossframe.ultra.v82.verdict",
        run_id=run_id,
        version_binding=binding,
        phase_id="U9",
        label="U9 verdict",
    )
    _validate_public_verdict_semantics(
        verdict_snapshot, evidence_snapshot, lineage_snapshot
    )
    return verdict_snapshot, evidence_snapshot, lineage_snapshot


def validate_verdict_bundle(
    verdict: Mapping[str, object],
    evidence: Mapping[str, object],
    lineage: Mapping[str, object],
) -> None:
    _validated_public_verdict_inputs(verdict, evidence, lineage)


def _verdict_reference_catalogs(
    graph: Mapping[str, Any],
    lineage: Mapping[str, Any],
    state_registry: Mapping[str, Mapping[str, Any]],
) -> tuple[set[str], set[str], set[str], dict[str, Mapping[str, Any]], set[str], set[str]]:
    claims = {item["claim_id"] for item in graph["claims"]}
    mechanisms = {item["mechanism_id"] for item in graph["mechanisms"]}
    explanations = {item["explanation_id"] for item in graph["explanations"]}
    states_by_node = {
        item["node_id"]: state_registry[item["recursive_state_artifact_sha256"]]
        for item in lineage["nodes"]
    }
    unknowns = {
        unknown_id
        for state in state_registry.values()
        for unknown_id in state["inherited_unknown_ids"]
    }
    residuals = {
        residual_id
        for state in state_registry.values()
        for residual_id in state["inherited_residual_ids"]
    }
    return claims, mechanisms, explanations, states_by_node, unknowns, residuals


def _validate_verdict_against_inference(
    verdict: Mapping[str, Any],
    evidence: Mapping[str, Any],
    graph: Mapping[str, Any],
    lineage: Mapping[str, Any],
    order_evaluation: Mapping[str, Any],
    red_team_report: Mapping[str, Any],
    state_registry: Mapping[str, Mapping[str, Any]],
) -> None:
    (
        claim_ids,
        mechanism_ids,
        explanation_ids,
        states_by_node,
        unknown_ids,
        residual_ids,
    ) = _verdict_reference_catalogs(graph, lineage, state_registry)
    ranking_ids = {item["explanation_id"] for item in verdict["explanation_ranking"]}
    if ranking_ids != explanation_ids:
        raise JudgmentError(
            "verdict explanation ranking must exactly cover the sealed U6 competitors"
        )
    rival_ids = {
        item["explanation_id"]
        for item in graph["explanations"]
        if item["kind"] == "strongest-rival"
    }
    main = verdict.get("main_verdict")
    if main is not None:
        if main["strongest_rival_id"] not in rival_ids:
            raise JudgmentError(
                "main verdict strongest rival does not resolve the sealed U6 rival"
            )
        if not set(main["decisive_claim_ids"]).issubset(claim_ids):
            raise JudgmentError("main verdict cites an unknown U6 claim")
        if not set(main["decisive_mechanism_ids"]).issubset(mechanism_ids):
            raise JudgmentError("main verdict cites an unknown U6 mechanism")
        if not set(main["residual_ids"]).issubset(residual_ids):
            raise JudgmentError("main verdict cites an unsealed residual identity")
    if not set(verdict["decisive_unknown_ids"]).issubset(unknown_ids):
        raise JudgmentError("verdict cites an unsealed decisive unknown identity")

    locks = verdict["five_verdicts"]
    for lock in locks:
        if not set(lock["claim_ids"]).issubset(claim_ids):
            raise JudgmentError(f"{lock['kind']} verdict cites an unknown U6 claim")
        if not set(lock["mechanism_ids"]).issubset(mechanism_ids):
            raise JudgmentError(
                f"{lock['kind']} verdict cites an unknown U6 mechanism"
            )
    fact = next(item for item in locks if item["kind"] == "fact")
    if any(
        states_by_node[node_id]["evidence_identity"] == "simulated-result"
        for node_id in fact["recursive_node_ids"]
    ):
        raise JudgmentError(
            "a simulated recursive node cannot be promoted into a factual verdict"
        )

    lock_ids = {item["verdict_id"] for item in locks}
    upstream_reserved = set().union(
        *(
            _identifier_values(artifact)
            for artifact in (
                evidence,
                graph,
                lineage,
                order_evaluation,
                red_team_report,
                *state_registry.values(),
            )
        )
    )
    if lock_ids.intersection(upstream_reserved):
        raise JudgmentError(
            "verdict lock IDs must be disjoint from every upstream identity domain"
        )


def _validate_verdict_with_authority(
    verdict: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    order_evaluation: Mapping[str, object],
    red_team_report: Mapping[str, object],
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_ledger_artifact_sha256: str,
    expected_claim_mechanism_graph_artifact_sha256: str,
    expected_recursive_lineage_artifact_sha256: str,
    expected_order_evaluation_artifact_sha256: str,
    expected_red_team_report_artifact_sha256: str,
) -> dict[str, Any]:
    expected_hashes = tuple(
        _require_sha256(value, label=label)
        for value, label in (
            (
                expected_evidence_ledger_artifact_sha256,
                "expected U3 evidence ledger artifact hash",
            ),
            (
                expected_claim_mechanism_graph_artifact_sha256,
                "expected U6 claim/mechanism graph artifact hash",
            ),
            (
                expected_recursive_lineage_artifact_sha256,
                "expected U7 recursive lineage artifact hash",
            ),
            (
                expected_order_evaluation_artifact_sha256,
                "expected U8 order evaluation artifact hash",
            ),
            (
                expected_red_team_report_artifact_sha256,
                "expected U8 red-team report artifact hash",
            ),
        )
    )
    if len(set(expected_hashes)) != len(expected_hashes):
        raise JudgmentError("U3/U6/U7/U8 authority roles require distinct hashes")
    if type(expected_run_id) is not str or not expected_run_id:
        raise JudgmentError("expected U9 run authority must be explicit")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected U9 version binding"
    )

    verdict_snapshot, evidence, lineage = _validated_public_verdict_inputs(
        verdict, evidence_ledger, recursive_lineage
    )
    if verdict_snapshot["run_id"] != expected_run_id or verdict_snapshot[
        "version_binding"
    ] != binding:
        raise JudgmentError("U9 verdict run or version authority does not match")
    if _canonical_sha256(evidence) != expected_hashes[0]:
        raise JudgmentError(
            "U3 evidence full artifact hash differs from external authority"
        )

    from . import recursion as recursive_runtime

    graph_snapshot = _snapshot_mapping(
        claim_mechanism_graph, label="U6 claim/mechanism graph"
    )
    evaluation_snapshot = _snapshot_mapping(
        order_evaluation, label="U8 order evaluation"
    )
    red_team_snapshot = recursive_runtime._validate_red_team_report(
        red_team_report,
        claim_mechanism_graph=graph_snapshot,
        recursive_lineage=lineage,
        order_evaluation=evaluation_snapshot,
        recursive_state_artifacts=recursive_state_artifacts,
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        expected_claim_mechanism_graph_artifact_sha256=expected_hashes[1],
        expected_recursive_lineage_artifact_sha256=expected_hashes[2],
        expected_order_evaluation_artifact_sha256=expected_hashes[3],
    )
    if _canonical_sha256(red_team_snapshot) != expected_hashes[4]:
        raise JudgmentError(
            "U8 red-team full artifact hash differs from external authority"
        )
    if tuple(
        verdict_snapshot[field]
        for field in (
            "evidence_ledger_artifact_sha256",
            "claim_mechanism_graph_artifact_sha256",
            "recursive_lineage_artifact_sha256",
            "order_evaluation_artifact_sha256",
            "red_team_report_artifact_sha256",
        )
    ) != expected_hashes:
        raise JudgmentError(
            "U9 verdict authority fields do not match externally verified U3/U6/U7/U8 artifacts"
        )

    state_registry = recursive_runtime._state_registry_documents(
        recursive_state_artifacts,
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        expected_hashes=(
            lineage["world_volume_artifact_sha256"],
            lineage["transformation_ledger_artifact_sha256"],
            expected_hashes[1],
        ),
        expected_concept_hash=lineage["concept_disposition_artifact_sha256"],
    )
    _validate_verdict_against_inference(
        verdict_snapshot,
        evidence,
        graph_snapshot,
        lineage,
        evaluation_snapshot,
        red_team_snapshot,
        state_registry,
    )
    return verdict_snapshot


def _seal_verdict_bundle(
    verdict: Mapping[str, object],
    **authority: object,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(verdict, label="unsealed U9 verdict")
    if "content_sha256" in snapshot:
        raise JudgmentError(
            "U9 producer accepts an unsealed verdict without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_verdict_with_authority(snapshot, **authority)


def _validate_action_ranking(
    action: Mapping[str, object],
    *,
    verdict: Mapping[str, object],
    evidence: Mapping[str, object],
    lineage: Mapping[str, object],
    expected_verdict_artifact_sha256: str,
) -> dict[str, Any]:
    verdict_snapshot, _, _ = _validated_public_verdict_inputs(
        verdict, evidence, lineage
    )
    expected_verdict_hash = _require_sha256(
        expected_verdict_artifact_sha256,
        label="expected sealed U9 verdict artifact hash",
    )
    if _canonical_sha256(verdict_snapshot) != expected_verdict_hash:
        raise JudgmentError(
            "sealed verdict full artifact hash differs from external authority"
        )
    action_snapshot = _phase(
        "ultra-action-ranking.schema.json",
        action,
        schema_id="crossframe.ultra.v82.action-ranking",
        run_id=verdict_snapshot["run_id"],
        version_binding=verdict_snapshot["version_binding"],
        phase_id="U9",
        label="U9 action ranking",
    )
    if action_snapshot["verdict_artifact_sha256"] != expected_verdict_hash:
        raise JudgmentError(
            "action ranking does not bind the externally sealed U9 verdict"
        )

    locks = {item["kind"]: item for item in verdict_snapshot["five_verdicts"]}
    lock_ids = {item["verdict_id"] for item in locks.values()}
    if set(action_snapshot["considered_verdict_ids"]) != lock_ids:
        raise JudgmentError(
            "action ranking must consider exactly the five bound verdict lock IDs"
        )

    options = action_snapshot["options"]
    option_ids = [item["option_id"] for item in options]
    option_kinds = [item["kind"] for item in options]
    if len(set(option_ids)) != len(ACTION_KINDS):
        raise JudgmentError("action option identities must be unique")
    if set(option_kinds) != set(ACTION_KINDS) or len(options) != len(ACTION_KINDS):
        raise JudgmentError("action ranking must compare all six frozen action kinds")
    if set(option_ids).intersection(lock_ids | _identifier_values(verdict_snapshot)):
        raise JudgmentError(
            "action option identities must remain distinct from verdict identity roles"
        )
    if set(action_snapshot["ranking"]) != set(option_ids) or len(
        action_snapshot["ranking"]
    ) != len(option_ids):
        raise JudgmentError("action ranking must cover each option exactly once")
    if action_snapshot["requested_choice"]:
        if (
            action_snapshot["preferred_option_id"] != action_snapshot["ranking"][0]
            or action_snapshot["second_option_id"] != action_snapshot["ranking"][1]
            or action_snapshot["preferred_option_id"]
            == action_snapshot["second_option_id"]
        ):
            raise JudgmentError(
                "a direct choice request requires distinct first and second ranked recommendations"
            )

    authorization_id = locks["authorization"]["verdict_id"]
    for option in options:
        reference = option["authorization_verdict_id"]
        if option["authorized"]:
            if reference != authorization_id:
                raise JudgmentError(
                    "an authorized action must resolve only the authorization verdict lock"
                )
        elif reference is not None:
            raise JudgmentError(
                "an unauthorized action cannot carry an authorization verdict reference"
            )
    return action_snapshot


def _seal_action_ranking(
    action: Mapping[str, object],
    **authority: object,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(action, label="unsealed U9 action ranking")
    if "content_sha256" in snapshot:
        raise JudgmentError(
            "U9 producer accepts an unsealed action ranking without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_action_ranking(snapshot, **authority)


def _validate_framework_gap_isolation(
    gap: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    verdict: Mapping[str, object],
    action_ranking: Mapping[str, object],
) -> dict[str, Any]:
    verdict_snapshot = _snapshot_mapping(verdict, label="sealed U9 verdict")
    run_id = verdict_snapshot.get("run_id")
    binding = verdict_snapshot.get("version_binding")
    if type(run_id) is not str or not isinstance(binding, Mapping):
        raise JudgmentError("sealed U9 verdict must expose run and version authority")
    verdict_snapshot = _phase(
        "ultra-verdict.schema.json",
        verdict_snapshot,
        schema_id="crossframe.ultra.v82.verdict",
        run_id=run_id,
        version_binding=binding,
        phase_id="U9",
        label="sealed U9 verdict",
    )
    graph_snapshot = _phase(
        "ultra-claim-mechanism-graph.schema.json",
        claim_mechanism_graph,
        schema_id="crossframe.ultra.v82.claim-mechanism-graph",
        run_id=run_id,
        version_binding=binding,
        phase_id="U6",
        label="sealed U6 claim/mechanism graph",
    )
    action_snapshot = _phase(
        "ultra-action-ranking.schema.json",
        action_ranking,
        schema_id="crossframe.ultra.v82.action-ranking",
        run_id=run_id,
        version_binding=binding,
        phase_id="U9",
        label="sealed U9 action ranking",
    )
    gap_snapshot = _phase(
        "ultra-framework-gap-ledger.schema.json",
        gap,
        schema_id="crossframe.ultra.v82.framework-gap-ledger",
        run_id=run_id,
        version_binding=binding,
        phase_id="U10",
        label="isolated U10 framework-gap ledger",
    )

    authority_fields = (
        "evidence_ledger_artifact_sha256",
        "claim_mechanism_graph_artifact_sha256",
        "recursive_lineage_artifact_sha256",
        "order_evaluation_artifact_sha256",
        "red_team_report_artifact_sha256",
        "verdict_artifact_sha256",
        "action_ranking_artifact_sha256",
        "forecast_ledger_artifact_sha256",
    )
    authority_hashes = tuple(gap_snapshot[field] for field in authority_fields)
    if len(set(authority_hashes)) != len(authority_hashes):
        raise JudgmentError(
            "U10 gap ledger authority roles require eight distinct artifact hashes"
        )
    if (
        gap_snapshot["claim_mechanism_graph_artifact_sha256"]
        != _canonical_sha256(graph_snapshot)
        or gap_snapshot["verdict_artifact_sha256"]
        != _canonical_sha256(verdict_snapshot)
        or gap_snapshot["action_ranking_artifact_sha256"]
        != _canonical_sha256(action_snapshot)
    ):
        raise JudgmentError(
            "U10 gap ledger does not bind the supplied current U6/U9 artifacts"
        )
    gap_ids = [item["gap_id"] for item in gap_snapshot["candidates"]]
    if len(set(gap_ids)) != len(gap_ids):
        raise JudgmentError("framework-gap candidate identities must be unique")
    current_reasoning_ids = set().union(
        *(
            _identifier_values(artifact)
            for artifact in (graph_snapshot, verdict_snapshot, action_snapshot)
        )
    )
    if set(gap_ids).intersection(current_reasoning_ids):
        raise JudgmentError(
            "a U10 framework-gap candidate cannot become current U6/U9 authority"
        )
    return gap_snapshot
