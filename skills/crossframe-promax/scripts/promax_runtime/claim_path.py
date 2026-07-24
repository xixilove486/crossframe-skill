from __future__ import annotations

from collections import deque
from typing import Mapping

from jsonschema import ValidationError

from .validation import validate_bound_document


class ClaimPathSaturationError(ValueError):
    """Raised when a claim/path graph is shaped but not semantically closed."""


def validate_claim_path_graph(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    return validate_bound_document(
        "promax-claim-path-graph.schema.json",
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )


def _unique_records(
    records: object,
    *,
    id_field: str,
    label: str,
) -> dict[str, Mapping[str, object]]:
    if not isinstance(records, list) or not records:
        raise ClaimPathSaturationError(f"{label} must be a non-empty array")
    result: dict[str, Mapping[str, object]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ClaimPathSaturationError(f"{label} records must be objects")
        identifier = record.get(id_field)
        if not isinstance(identifier, str) or identifier in result:
            raise ClaimPathSaturationError(
                f"duplicate or invalid {label} identifier: {identifier!r}"
            )
        result[identifier] = record
    return result


def _require_nonempty_list(value: object, *, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise ClaimPathSaturationError(f"{field} must contain substantive records")


def _assert_acyclic(
    node_ids: set[str],
    edges: list[Mapping[str, object]],
) -> None:
    indegree = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        source = edge.get("from_node_id")
        target = edge.get("to_node_id")
        assert isinstance(source, str) and isinstance(target, str)
        outgoing[source].append(target)
        indegree[target] += 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in outgoing[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(node_ids):
        raise ClaimPathSaturationError("path graph must be a DAG")


def validate_claim_path_saturation(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
    minimum_competing_mechanisms: int = 3,
) -> dict[str, object]:
    """Enforce the explicit judgment cycle, competing mechanisms and path DAG."""

    if (
        not isinstance(minimum_competing_mechanisms, int)
        or isinstance(minimum_competing_mechanisms, bool)
        or minimum_competing_mechanisms < 2
    ):
        raise ClaimPathSaturationError(
            "minimum_competing_mechanisms cannot be lower than the absolute floor of 2"
        )
    try:
        normalized = validate_claim_path_graph(
            document,
            expected_run_id=expected_run_id,
            expected_source_snapshot_sha256=expected_source_snapshot_sha256,
        )
    except ValidationError as error:
        raise ClaimPathSaturationError(
            f"claim/path graph violates its schema: {error.message}"
        ) from error

    claims = _unique_records(
        normalized.get("claims"),
        id_field="claim_id",
        label="claims",
    )
    central_claim_id = normalized.get("central_claim_id")
    if not isinstance(central_claim_id, str) or central_claim_id not in claims:
        raise ClaimPathSaturationError(
            "central_claim_id must reference exactly one claim record"
        )
    central_claim = claims[central_claim_id]
    _require_nonempty_list(
        central_claim.get("evidence_refs"),
        field="central claim evidence_refs",
    )
    cycle = normalized.get("central_claim_cycle")
    if not isinstance(cycle, Mapping) or cycle.get("central_claim_id") != central_claim_id:
        raise ClaimPathSaturationError(
            "central_claim_cycle must reference the unique central claim"
        )

    mechanisms = _unique_records(
        normalized.get("mechanisms"),
        id_field="mechanism_id",
        label="mechanisms",
    )
    if len(mechanisms) < minimum_competing_mechanisms:
        raise ClaimPathSaturationError(
            f"claim graph requires at least {minimum_competing_mechanisms} competing mechanisms"
        )
    for mechanism_id, mechanism in mechanisms.items():
        claim_ids = mechanism.get("claim_ids")
        if not isinstance(claim_ids, list) or central_claim_id not in claim_ids:
            raise ClaimPathSaturationError(
                f"competing mechanism is not linked to the central claim: {mechanism_id}"
            )
        unknown_claim_ids = set(claim_ids) - set(claims)
        if unknown_claim_ids:
            raise ClaimPathSaturationError(
                f"mechanism {mechanism_id} references unknown claims: {sorted(unknown_claim_ids)!r}"
            )
        _require_nonempty_list(
            mechanism.get("distinguishing_conditions"),
            field=f"mechanism {mechanism_id} distinguishing_conditions",
        )

    nodes = _unique_records(
        normalized.get("path_nodes"),
        id_field="node_id",
        label="path nodes",
    )
    raw_edges = normalized.get("path_edges")
    if not isinstance(raw_edges, list) or not raw_edges:
        raise ClaimPathSaturationError("path graph must contain at least one branch edge")
    edge_index = _unique_records(
        raw_edges,
        id_field="edge_id",
        label="path edges",
    )
    edges = list(edge_index.values())
    branch_sources: set[str] = set()
    referenced_nodes: set[str] = set()
    for edge_id, edge in edge_index.items():
        source = edge.get("from_node_id")
        target = edge.get("to_node_id")
        if not isinstance(source, str) or source not in nodes:
            raise ClaimPathSaturationError(
                f"edge {edge_id} references an unknown source node"
            )
        if not isinstance(target, str) or target not in nodes:
            raise ClaimPathSaturationError(
                f"edge {edge_id} references an unknown target node"
            )
        branch_sources.add(source)
        referenced_nodes.update((source, target))
        mechanism_ids = edge.get("mechanism_ids")
        if not isinstance(mechanism_ids, list) or not mechanism_ids:
            raise ClaimPathSaturationError(
                f"edge {edge_id} must identify its mechanism set"
            )
        unknown_mechanisms = set(mechanism_ids) - set(mechanisms)
        if unknown_mechanisms:
            raise ClaimPathSaturationError(
                f"edge {edge_id} references unknown mechanisms: {sorted(unknown_mechanisms)!r}"
            )
    if referenced_nodes != set(nodes):
        raise ClaimPathSaturationError("path graph contains orphan nodes")
    for node_id in branch_sources:
        node = nodes[node_id]
        for field in (
            "trigger_conditions",
            "early_signals",
            "reverse_signals",
            "stop_conditions",
        ):
            _require_nonempty_list(
                node.get(field),
                field=f"path branch {node_id} {field}",
            )
    _assert_acyclic(set(nodes), edges)
    return normalized
