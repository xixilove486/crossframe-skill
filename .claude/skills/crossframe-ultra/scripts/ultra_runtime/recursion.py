from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
import re
from typing import Any

from jsonschema import ValidationError

from .errors import UltraSchemaError
from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


BRANCH_KINDS = ("main", "strongest-rival", "mixture", "residual")
STOP_KINDS = (
    "order-limit",
    "baseline-wins",
    "no-material-state-change",
    "local-predictability-exhausted",
    "evidence-boundary",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_STATE_AUTHORITY_FIELDS = (
    "world_volume_artifact_sha256",
    "transformation_ledger_artifact_sha256",
    "concept_disposition_artifact_sha256",
    "claim_mechanism_graph_artifact_sha256",
)
_INHERITED_FIELDS = (
    "inherited_fact_ids",
    "inherited_evidence_ids",
    "inherited_unknown_ids",
    "inherited_loss_ids",
    "inherited_residual_ids",
)
_GRADE_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3}


class RecursiveInferenceError(ValueError):
    """Raised when U7/U8 authority or recursive identity is inconsistent."""


@dataclass(frozen=True, slots=True)
class LineageValidation:
    node_ids: tuple[str, ...]
    maximum_order: int
    early_stop_nodes: tuple[str, ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise RecursiveInferenceError(
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
    raise RecursiveInferenceError(f"{label} contains a non-native JSON value")


def _snapshot_mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RecursiveInferenceError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise RecursiveInferenceError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise RecursiveInferenceError(
            f"artifact authority is not bounded canonical JSON: {error}"
        ) from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise RecursiveInferenceError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _phase(
    schema_name: str,
    schema_id: str,
    phase_id: str,
    artifact: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    label: str,
) -> dict[str, Any]:
    try:
        return validate_phase_artifact(
            schema_name,
            artifact,
            expected_schema_id=schema_id,
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_phase_id=phase_id,
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise RecursiveInferenceError(f"invalid {label}: {error}") from error


def _validate_expected_authority(
    *,
    expected_run_id: object,
    expected_version_binding: object,
    expected_world_volume_artifact_sha256: object,
    expected_transformation_ledger_artifact_sha256: object,
    expected_claim_mechanism_graph_artifact_sha256: object,
) -> tuple[str, dict[str, Any], tuple[str, str, str]]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise RecursiveInferenceError("expected run_id authority must be explicit")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    hashes = (
        _require_sha256(
            expected_world_volume_artifact_sha256,
            label="expected U4 world volume artifact hash",
        ),
        _require_sha256(
            expected_transformation_ledger_artifact_sha256,
            label="expected U5 transformation ledger artifact hash",
        ),
        _require_sha256(
            expected_claim_mechanism_graph_artifact_sha256,
            label="expected U6 claim/mechanism graph artifact hash",
        ),
    )
    if len(set(hashes)) != 3:
        raise RecursiveInferenceError(
            "U4/U5/U6 authority roles require three distinct full artifact hashes"
        )
    return expected_run_id, binding, hashes


def _validate_upstream_authority(
    *,
    parent_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_hashes: tuple[str, str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    world = _phase(
        "ultra-world-volume.schema.json",
        "crossframe.ultra.v82.world-volume",
        "U4",
        _snapshot_mapping(parent_volume, label="U4 parent world volume"),
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        label="U4 parent world volume",
    )
    transformations = _phase(
        "ultra-transformation-ledger.schema.json",
        "crossframe.ultra.v82.transformation-ledger",
        "U5",
        _snapshot_mapping(transformation_ledger, label="U5 transformation ledger"),
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        label="U5 transformation ledger",
    )
    graph = _phase(
        "ultra-claim-mechanism-graph.schema.json",
        "crossframe.ultra.v82.claim-mechanism-graph",
        "U6",
        _snapshot_mapping(claim_mechanism_graph, label="U6 claim/mechanism graph"),
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        label="U6 claim/mechanism graph",
    )

    actual_hashes = (
        _canonical_sha256(world),
        _canonical_sha256(transformations),
        _canonical_sha256(graph),
    )
    if actual_hashes != expected_hashes:
        raise RecursiveInferenceError(
            "U4/U5/U6 full artifact hash authority does not match the external expectation"
        )
    if transformations.get("world_volume_artifact_sha256") != expected_hashes[0]:
        raise RecursiveInferenceError(
            "U5 transformation ledger has a stale upstream hash chain to U4"
        )
    if (
        graph.get("world_volume_artifact_sha256") != expected_hashes[0]
        or graph.get("transformation_ledger_artifact_sha256") != expected_hashes[1]
    ):
        raise RecursiveInferenceError(
            "U6 claim/mechanism graph has a stale upstream hash chain to U4/U5"
        )
    concept_hash = _require_sha256(
        graph.get("concept_disposition_artifact_sha256"),
        label="U6-bound U5 concept disposition artifact hash",
    )
    if concept_hash in expected_hashes:
        raise RecursiveInferenceError(
            "concept, world, transformation, and claim authority roles must be distinct"
        )
    return world, transformations, graph, concept_hash


def _collect_ids(value: object, field_names: frozenset[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in field_names:
                if type(item) is str:
                    found.add(item)
                elif isinstance(item, Sequence) and not isinstance(
                    item, (str, bytes, bytearray)
                ):
                    found.update(entry for entry in item if type(entry) is str)
            found.update(_collect_ids(item, field_names))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            found.update(_collect_ids(item, field_names))
    return found


def _baseline_inherited_ids(
    world: Mapping[str, Any], transformations: Mapping[str, Any]
) -> dict[str, set[str]]:
    return {
        "inherited_fact_ids": _collect_ids(world, frozenset({"event_id"})),
        "inherited_evidence_ids": _collect_ids(
            world, frozenset({"evidence_id", "evidence_ids", "evidence_refs"})
        ),
        "inherited_unknown_ids": _collect_ids(
            (world, transformations), frozenset({"unknown_id"})
        ),
        "inherited_loss_ids": _collect_ids(
            transformations, frozenset({"loss_id"})
        ),
        "inherited_residual_ids": _collect_ids(
            (world, transformations), frozenset({"residual_id"})
        ),
    }


def _state_identity(state: Mapping[str, Any]) -> str:
    if "full_state_sha256" in state:
        return state["full_state_sha256"]
    bounded = state.get("bounded_subgraph")
    if not isinstance(bounded, Mapping):
        raise RecursiveInferenceError(
            "recursive state must expose a full state or bounded subgraph identity"
        )
    return bounded["subgraph_sha256"]


def _state_registry_documents(
    recursive_state_artifacts: object,
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_hashes: tuple[str, str, str],
    expected_concept_hash: str,
) -> dict[str, dict[str, Any]]:
    if not isinstance(recursive_state_artifacts, Mapping):
        raise RecursiveInferenceError(
            "recursive_state_artifacts must be a sealed artifact registry"
        )
    registry: dict[str, dict[str, Any]] = {}
    for key, artifact in recursive_state_artifacts.items():
        artifact_hash = _require_sha256(key, label="recursive-state registry key")
        state = _phase(
            "ultra-recursive-state.schema.json",
            "crossframe.ultra.v82.recursive-state",
            "U7",
            _snapshot_mapping(artifact, label="sealed recursive-state artifact"),
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            label="U7 recursive state",
        )
        if _canonical_sha256(state) != artifact_hash:
            raise RecursiveInferenceError(
                "recursive-state registry key does not match the recomputed full artifact hash"
            )
        expected_state_hashes = (
            expected_hashes[0],
            expected_hashes[1],
            expected_concept_hash,
            expected_hashes[2],
        )
        if tuple(state.get(field) for field in _STATE_AUTHORITY_FIELDS) != (
            expected_state_hashes
        ):
            raise RecursiveInferenceError(
                "sealed recursive-state artifact has stale U4/U5/U6 authority"
            )
        registry[artifact_hash] = state
    return registry


def _find_state_parent(
    state: Mapping[str, Any], registry: Mapping[str, Mapping[str, Any]]
) -> Mapping[str, Any]:
    matches = [
        candidate
        for candidate in registry.values()
        if candidate.get("run_id") == state.get("parent_run_id")
        and candidate.get("path_id") == state.get("parent_path_id")
        and candidate.get("node_id") == state.get("parent_node_id")
    ]
    if len(matches) != 1:
        raise RecursiveInferenceError(
            "order>1 state must resolve exactly one sealed parent recursive state"
        )
    return matches[0]


def _validate_recursive_state_semantics(
    state: Mapping[str, Any],
    *,
    world: Mapping[str, Any],
    transformations: Mapping[str, Any],
    graph: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> None:
    baseline = _baseline_inherited_ids(world, transformations)
    for field, required in baseline.items():
        if not required.issubset(set(state[field])):
            raise RecursiveInferenceError(
                f"recursive state lost required inherited identity in {field}"
            )

    if state["parent_run_id"] != world["run_id"]:
        raise RecursiveInferenceError(
            "recursive state parent run must remain the sealed U4 run"
        )
    if state["node_id"] in {
        state["event_id"],
        *state["mechanism_ids"],
        *state["signal_ids"],
    }:
        raise RecursiveInferenceError(
            "recursive node, event, mechanism, and signal identity roles must be distinct"
        )
    if _state_identity(state) == state["state_diff_sha256"]:
        raise RecursiveInferenceError(
            "recursive state and state-diff identities must be distinct"
        )

    mechanism_ids = {
        mechanism["mechanism_id"] for mechanism in graph.get("mechanisms", [])
    }
    if not set(state["mechanism_ids"]).issubset(mechanism_ids):
        raise RecursiveInferenceError(
            "recursive state mechanism_ids must resolve in the sealed U6 graph"
        )

    world_event_ids = _collect_ids(world.get("events", []), frozenset({"event_id"}))
    if (
        state["evidence_identity"] == "observed"
        and state["event_id"] not in world_event_ids
    ):
        raise RecursiveInferenceError(
            "a simulated recursive event cannot be marked observed without a frozen U4 event"
        )

    if state["order"] == 1:
        if state["parent_node_id"] != world.get("volume_id"):
            raise RecursiveInferenceError(
                "order-1 recursive state parent must be the sealed U4 volume"
            )
        if state["parent_path_id"] != state["path_id"]:
            raise RecursiveInferenceError(
                "order-1 recursive state must open its declared lineage path"
            )
        return

    parent = _find_state_parent(state, registry)
    if parent["order"] != state["order"] - 1:
        raise RecursiveInferenceError(
            "recursive-state parent must be at the immediately preceding order"
        )
    for field in _INHERITED_FIELDS:
        if not set(parent[field]).issubset(set(state[field])):
            raise RecursiveInferenceError(
                f"child recursive state lost inherited parent identity in {field}"
            )
    if _GRADE_ORDER[state["declared_evidence_grade"]] > _GRADE_ORDER[
        parent["declared_evidence_grade"]
    ]:
        raise RecursiveInferenceError(
            "recursive depth cannot increase the declared evidence grade"
        )
    transition_fields = (
        "state_diff_sha256",
        "event_id",
        "mechanism_ids",
        "signal_ids",
    )
    if _state_identity(state) == _state_identity(parent) and all(
        state[field] == parent[field] for field in transition_fields
    ):
        raise RecursiveInferenceError(
            "child must contain a material recursive state change, not only the parent conclusion"
        )


def _validate_recursive_state(
    state: Mapping[str, object],
    *,
    parent_volume: Mapping[str, object],
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    transformation_ledger: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_claim_mechanism_graph_artifact_sha256: str,
) -> dict[str, Any]:
    run_id, binding, expected_hashes = _validate_expected_authority(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_world_volume_artifact_sha256=(
            expected_world_volume_artifact_sha256
        ),
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
    )
    world, transformations, graph, concept_hash = _validate_upstream_authority(
        parent_volume=parent_volume,
        transformation_ledger=transformation_ledger,
        claim_mechanism_graph=claim_mechanism_graph,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
    )
    snapshot = _phase(
        "ultra-recursive-state.schema.json",
        "crossframe.ultra.v82.recursive-state",
        "U7",
        _snapshot_mapping(state, label="U7 recursive state"),
        expected_run_id=run_id,
        expected_version_binding=binding,
        label="U7 recursive state",
    )
    expected_state_hashes = (
        expected_hashes[0],
        expected_hashes[1],
        concept_hash,
        expected_hashes[2],
    )
    if tuple(snapshot.get(field) for field in _STATE_AUTHORITY_FIELDS) != (
        expected_state_hashes
    ):
        raise RecursiveInferenceError(
            "recursive state U4/U5/U6 upstream authority does not match"
        )
    registry = _state_registry_documents(
        recursive_state_artifacts,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
        expected_concept_hash=concept_hash,
    )
    _validate_recursive_state_semantics(
        snapshot,
        world=world,
        transformations=transformations,
        graph=graph,
        registry=registry,
    )
    return snapshot


def _seal_recursive_state(
    state: Mapping[str, object],
    *,
    parent_volume: Mapping[str, object],
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    transformation_ledger: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_claim_mechanism_graph_artifact_sha256: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(state, label="unsealed U7 recursive state")
    if "content_sha256" in snapshot:
        raise RecursiveInferenceError(
            "U7 producer accepts an unsealed recursive state without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_recursive_state(
        snapshot,
        parent_volume=parent_volume,
        recursive_state_artifacts=recursive_state_artifacts,
        transformation_ledger=transformation_ledger,
        claim_mechanism_graph=claim_mechanism_graph,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_world_volume_artifact_sha256=(
            expected_world_volume_artifact_sha256
        ),
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
    )


def _validate_lineage_structure(
    lineage: Mapping[str, Any], parent_volume: Mapping[str, Any]
) -> LineageValidation:
    nodes = lineage["nodes"]
    node_ids = [node["node_id"] for node in nodes]
    if len(set(node_ids)) != len(node_ids):
        raise RecursiveInferenceError("recursive lineage node identities must be unique")
    by_node = {node["node_id"]: node for node in nodes}
    orders = {node["order"] for node in nodes}
    maximum_order = max(orders)
    if orders != set(range(1, maximum_order + 1)):
        raise RecursiveInferenceError(
            "recursive lineage orders must be contiguous from order 1"
        )
    if lineage["maximum_order"] != maximum_order:
        raise RecursiveInferenceError(
            "recursive lineage maximum_order does not match its nodes"
        )
    for node in nodes:
        parents = node["parent_node_ids"]
        if node["order"] == 1:
            if parents:
                raise RecursiveInferenceError(
                    "order-1 recursive lineage node cannot name a recursive parent"
                )
            continue
        if not parents:
            raise RecursiveInferenceError(
                "deeper recursive lineage node requires a parent"
            )
        for parent_id in parents:
            parent = by_node.get(parent_id)
            if parent is None:
                raise RecursiveInferenceError(
                    "recursive lineage parent node does not resolve"
                )
            if parent["order"] != node["order"] - 1:
                raise RecursiveInferenceError(
                    "recursive lineage parent must be at the immediately preceding order"
                )

    branches = lineage["branches"]
    branch_ids = [branch["branch_id"] for branch in branches]
    if len(set(branch_ids)) != len(branch_ids):
        raise RecursiveInferenceError("recursive lineage branch identities must be unique")
    if {branch["kind"] for branch in branches} != set(BRANCH_KINDS):
        raise RecursiveInferenceError(
            "recursive lineage must preserve all four frozen branch kinds"
        )
    by_branch = {branch["branch_id"]: branch for branch in branches}
    covered_nodes: set[str] = set()
    early_stop_nodes: list[str] = []
    for branch in branches:
        branch_nodes = branch["node_ids"]
        if any(node_id not in by_node for node_id in branch_nodes):
            raise RecursiveInferenceError(
                "recursive lineage branch references an unknown node"
            )
        covered_nodes.update(branch_nodes)
        for parent_id, child_id in zip(branch_nodes, branch_nodes[1:]):
            if parent_id not in by_node[child_id]["parent_node_ids"]:
                raise RecursiveInferenceError(
                    "recursive lineage branch path is not parent-connected"
                )
        if branch["status"] == "merged":
            if branch["branch_id"] in branch["merge_parent_branch_ids"] or any(
                parent_id not in by_branch
                for parent_id in branch["merge_parent_branch_ids"]
            ):
                raise RecursiveInferenceError(
                    "merged branch has an invalid merge-parent identity"
                )
        if branch["status"] == "pruned" and (
            not branch["prune_reason"] or not branch["retained_residual_ids"]
        ):
            raise RecursiveInferenceError(
                "pruned branch requires a reason and retained residual"
            )
        if branch["status"] == "stopped":
            early_stop_nodes.append(branch_nodes[-1])
    if covered_nodes != set(node_ids):
        raise RecursiveInferenceError(
            "every recursive lineage node must belong to a declared branch"
        )

    inherited_unknown_ids = tuple(
        sorted(_collect_ids(parent_volume.get("unknowns", []), frozenset({"unknown_id"})))
    )
    inherited_residual_ids = tuple(
        sorted(
            _collect_ids(
                parent_volume.get("residuals", []), frozenset({"residual_id"})
            )
        )
    )
    return LineageValidation(
        node_ids=tuple(node_ids),
        maximum_order=maximum_order,
        early_stop_nodes=tuple(early_stop_nodes),
        inherited_unknown_ids=inherited_unknown_ids,
        inherited_residual_ids=inherited_residual_ids,
    )


def validate_recursive_lineage(
    lineage: Mapping[str, object], parent_volume: Mapping[str, object]
) -> LineageValidation:
    lineage_snapshot = _snapshot_mapping(lineage, label="U7 recursive lineage")
    world_snapshot = _snapshot_mapping(parent_volume, label="U4 parent world volume")
    run_id = lineage_snapshot.get("run_id")
    binding = lineage_snapshot.get("version_binding")
    if type(run_id) is not str or not isinstance(binding, Mapping):
        raise RecursiveInferenceError(
            "recursive lineage must expose its run and version binding"
        )
    world = _phase(
        "ultra-world-volume.schema.json",
        "crossframe.ultra.v82.world-volume",
        "U4",
        world_snapshot,
        expected_run_id=run_id,
        expected_version_binding=binding,
        label="U4 parent world volume",
    )
    lineage_validated = _phase(
        "ultra-recursive-lineage.schema.json",
        "crossframe.ultra.v82.recursive-lineage",
        "U7",
        lineage_snapshot,
        expected_run_id=run_id,
        expected_version_binding=binding,
        label="U7 recursive lineage",
    )
    if lineage_validated["world_volume_artifact_sha256"] != _canonical_sha256(world):
        raise RecursiveInferenceError(
            "recursive lineage does not bind the supplied U4 parent volume"
        )
    return _validate_lineage_structure(lineage_validated, world)


def _identity_fingerprint(state: Mapping[str, Any]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(sorted(state[field])) for field in _INHERITED_FIELDS)


def _validate_lineage_state_bindings(
    lineage: Mapping[str, Any], registry: Mapping[str, Mapping[str, Any]]
) -> None:
    declared_hashes = set(lineage["recursive_state_artifact_hashes"])
    referenced_hashes = {
        node["recursive_state_artifact_sha256"] for node in lineage["nodes"]
    }
    if declared_hashes != referenced_hashes or declared_hashes != set(registry):
        raise RecursiveInferenceError(
            "every lineage node must resolve one sealed recursive-state artifact and no caller-declared state hash may be unbound"
        )
    nodes = {node["node_id"]: node for node in lineage["nodes"]}
    states_by_node: dict[str, Mapping[str, Any]] = {}
    for node in lineage["nodes"]:
        state = registry[node["recursive_state_artifact_sha256"]]
        if (
            state["node_id"] != node["node_id"]
            or state["path_id"] != node["path_id"]
            or state["order"] != node["order"]
        ):
            raise RecursiveInferenceError(
                "lineage node identity does not match its sealed recursive-state artifact"
            )
        if node["order"] > 1:
            if state["parent_node_id"] not in node["parent_node_ids"]:
                raise RecursiveInferenceError(
                    "lineage node does not retain its sealed state parent identity"
                )
            parent_node = nodes[state["parent_node_id"]]
            if state["parent_path_id"] != parent_node["path_id"]:
                raise RecursiveInferenceError(
                    "lineage node does not retain its sealed parent path identity"
                )
        states_by_node[node["node_id"]] = state

    branches = {branch["branch_id"]: branch for branch in lineage["branches"]}
    for branch in branches.values():
        terminal_state = states_by_node[branch["node_ids"][-1]]
        if branch["status"] == "pruned" and not set(
            branch["retained_residual_ids"]
        ).issubset(set(terminal_state["inherited_residual_ids"])):
            raise RecursiveInferenceError(
                "pruned branch retained a residual absent from its sealed state"
            )
        if branch["status"] == "merged":
            fingerprints = {
                _identity_fingerprint(terminal_state),
                *(
                    _identity_fingerprint(
                        states_by_node[branches[parent_id]["node_ids"][-1]]
                    )
                    for parent_id in branch["merge_parent_branch_ids"]
                ),
            }
            if len(fingerprints) != 1:
                raise RecursiveInferenceError(
                    "branch merge requires compatible inherited state identities"
                )


def _validate_recursive_lineage_bundle(
    lineage: Mapping[str, object],
    parent_volume: Mapping[str, object],
    *,
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    transformation_ledger: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_claim_mechanism_graph_artifact_sha256: str,
) -> LineageValidation:
    run_id, binding, expected_hashes = _validate_expected_authority(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_world_volume_artifact_sha256=(
            expected_world_volume_artifact_sha256
        ),
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
    )
    world, transformations, graph, concept_hash = _validate_upstream_authority(
        parent_volume=parent_volume,
        transformation_ledger=transformation_ledger,
        claim_mechanism_graph=claim_mechanism_graph,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
    )
    lineage_snapshot = _phase(
        "ultra-recursive-lineage.schema.json",
        "crossframe.ultra.v82.recursive-lineage",
        "U7",
        _snapshot_mapping(lineage, label="U7 recursive lineage"),
        expected_run_id=run_id,
        expected_version_binding=binding,
        label="U7 recursive lineage",
    )
    expected_lineage_hashes = (
        expected_hashes[0],
        expected_hashes[1],
        concept_hash,
        expected_hashes[2],
    )
    if tuple(lineage_snapshot.get(field) for field in _STATE_AUTHORITY_FIELDS) != (
        expected_lineage_hashes
    ):
        raise RecursiveInferenceError(
            "recursive lineage U4/U5/U6 upstream authority does not match"
        )
    result = _validate_lineage_structure(lineage_snapshot, world)
    registry = _state_registry_documents(
        recursive_state_artifacts,
        expected_run_id=run_id,
        expected_version_binding=binding,
        expected_hashes=expected_hashes,
        expected_concept_hash=concept_hash,
    )
    for state in registry.values():
        _validate_recursive_state_semantics(
            state,
            world=world,
            transformations=transformations,
            graph=graph,
            registry=registry,
        )
    _validate_lineage_state_bindings(lineage_snapshot, registry)
    return result


def _validate_u6_u7_artifact_authority(
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    expected_run_id: object,
    expected_version_binding: object,
    expected_claim_mechanism_graph_artifact_sha256: object,
    expected_recursive_lineage_artifact_sha256: object,
) -> tuple[dict[str, Any], dict[str, Any], tuple[str, str], dict[str, Any]]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise RecursiveInferenceError("expected run_id authority must be explicit")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    expected_hashes = (
        _require_sha256(
            expected_claim_mechanism_graph_artifact_sha256,
            label="expected U6 claim/mechanism graph artifact hash",
        ),
        _require_sha256(
            expected_recursive_lineage_artifact_sha256,
            label="expected U7 recursive lineage artifact hash",
        ),
    )
    if expected_hashes[0] == expected_hashes[1]:
        raise RecursiveInferenceError(
            "U6 claim graph and U7 lineage authority roles require distinct hashes"
        )
    graph = _phase(
        "ultra-claim-mechanism-graph.schema.json",
        "crossframe.ultra.v82.claim-mechanism-graph",
        "U6",
        _snapshot_mapping(claim_mechanism_graph, label="U6 claim/mechanism graph"),
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        label="U6 claim/mechanism graph",
    )
    lineage = _phase(
        "ultra-recursive-lineage.schema.json",
        "crossframe.ultra.v82.recursive-lineage",
        "U7",
        _snapshot_mapping(recursive_lineage, label="U7 recursive lineage"),
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        label="U7 recursive lineage",
    )
    actual_hashes = (_canonical_sha256(graph), _canonical_sha256(lineage))
    if actual_hashes != expected_hashes:
        raise RecursiveInferenceError(
            "U6/U7 full artifact hash authority does not match the external expectation"
        )
    if lineage.get("claim_mechanism_graph_artifact_sha256") != expected_hashes[0]:
        raise RecursiveInferenceError(
            "U7 recursive lineage has a stale U6 authority binding"
        )
    return graph, lineage, expected_hashes, binding


def _validate_order_evaluation_semantics(
    evaluation: Mapping[str, Any], lineage: Mapping[str, Any]
) -> None:
    evaluations = evaluation["evaluations"]
    if len(evaluations) != lineage["maximum_order"]:
        raise RecursiveInferenceError(
            "order evaluation must cover every lineage order through maximum order"
        )
    if [record["order"] for record in evaluations] != list(
        range(1, lineage["maximum_order"] + 1)
    ):
        raise RecursiveInferenceError(
            "order evaluation order sequence must match every lineage order"
        )

    nodes = {node["node_id"]: node for node in lineage["nodes"]}
    branches = {branch["branch_id"]: branch for branch in lineage["branches"]}
    baseline_ids: set[str] = set()
    stopped = False
    for index, record in enumerate(evaluations):
        order = record["order"]
        baseline_id = record["baseline"]["baseline_id"]
        if baseline_id in baseline_ids:
            raise RecursiveInferenceError(
                "each simple baseline comparison requires a distinct baseline identity"
            )
        baseline_ids.add(baseline_id)
        if stopped:
            raise RecursiveInferenceError(
                "no evaluated order may follow a declared recursive stop"
            )

        for coverage in record["branch_coverage"]:
            kind = coverage["branch_kind"]
            matching_at_order = {
                branch["branch_id"]
                for branch in branches.values()
                if branch["kind"] == kind
                and any(nodes[node_id]["order"] == order for node_id in branch["node_ids"])
            }
            if coverage["applicability"] == "applicable":
                supplied = set(coverage["branch_ids"])
                if not supplied or not supplied.issubset(matching_at_order):
                    raise RecursiveInferenceError(
                        "applicable branch kind must resolve a branch at the evaluated order"
                    )
            else:
                not_applicable = coverage["not_applicable"]
                if matching_at_order:
                    raise RecursiveInferenceError(
                        "an existing branch at the evaluated order cannot be not-applicable"
                    )
                if not (
                    not_applicable["evidence_refs"]
                    or not_applicable["residual_ids"]
                ):
                    raise RecursiveInferenceError(
                        "not-applicable branch requires bounded evidence or residual authority"
                    )

        if record["continue_recursive"]:
            if index == len(evaluations) - 1:
                raise RecursiveInferenceError(
                    "maximum order cannot retain recursive continuation"
                )
        else:
            stopped = True


def _validate_order_evaluation(
    order_evaluation: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_claim_mechanism_graph_artifact_sha256: str,
    expected_recursive_lineage_artifact_sha256: str,
) -> dict[str, Any]:
    _, lineage, expected_hashes, binding = _validate_u6_u7_artifact_authority(
        claim_mechanism_graph=claim_mechanism_graph,
        recursive_lineage=recursive_lineage,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
        expected_recursive_lineage_artifact_sha256=(
            expected_recursive_lineage_artifact_sha256
        ),
    )
    snapshot = _phase(
        "ultra-order-evaluation.schema.json",
        "crossframe.ultra.v82.order-evaluation",
        "U8",
        _snapshot_mapping(order_evaluation, label="U8 order evaluation"),
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        label="U8 order evaluation",
    )
    if (
        snapshot.get("claim_mechanism_graph_artifact_sha256"),
        snapshot.get("recursive_lineage_artifact_sha256"),
    ) != expected_hashes:
        raise RecursiveInferenceError(
            "order evaluation U6/U7 authority does not match the sealed artifacts"
        )
    _validate_order_evaluation_semantics(snapshot, lineage)
    return snapshot


def _seal_order_evaluation(
    order_evaluation: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_claim_mechanism_graph_artifact_sha256: str,
    expected_recursive_lineage_artifact_sha256: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(
        order_evaluation, label="unsealed U8 order evaluation"
    )
    if "content_sha256" in snapshot:
        raise RecursiveInferenceError(
            "U8 producer accepts an unsealed order evaluation without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_order_evaluation(
        snapshot,
        claim_mechanism_graph=claim_mechanism_graph,
        recursive_lineage=recursive_lineage,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
        expected_recursive_lineage_artifact_sha256=(
            expected_recursive_lineage_artifact_sha256
        ),
    )


def _attack_target_identity(
    target: Mapping[str, Any],
    *,
    graph: Mapping[str, Any],
    lineage: Mapping[str, Any],
    states_by_node: Mapping[str, Mapping[str, Any]],
) -> tuple[set[str], set[str], str]:
    target_key, target_id = next(iter(target.items()))
    if target_key == "recursive_node_id":
        state = states_by_node.get(target_id)
        if state is None:
            raise RecursiveInferenceError(
                "red-team attack target does not resolve a sealed recursive node"
            )
        return (
            {state["evidence_identity"]},
            set(state["inherited_evidence_ids"]),
            target_id,
        )
    if target_key == "branch_id":
        branch = next(
            (item for item in lineage["branches"] if item["branch_id"] == target_id),
            None,
        )
        if branch is None:
            raise RecursiveInferenceError(
                "red-team attack target does not resolve a sealed branch"
            )
        state = states_by_node[branch["node_ids"][-1]]
        return (
            {state["evidence_identity"]},
            set(state["inherited_evidence_ids"]),
            target_id,
        )
    if target_key == "claim_id":
        claim = next(
            (item for item in graph["claims"] if item["claim_id"] == target_id),
            None,
        )
        if claim is None:
            raise RecursiveInferenceError(
                "red-team attack target does not resolve a sealed U6 claim"
            )
        return {claim["identity"]}, set(claim["evidence_refs"]), target_id
    if target_key == "mechanism_id":
        mechanism = next(
            (
                item
                for item in graph["mechanisms"]
                if item["mechanism_id"] == target_id
            ),
            None,
        )
        if mechanism is None:
            raise RecursiveInferenceError(
                "red-team attack target does not resolve a sealed U6 mechanism"
            )
        return set(), set(mechanism["evidence_refs"]), target_id
    if target_key == "explanation_id":
        explanation = next(
            (
                item
                for item in graph["explanations"]
                if item["explanation_id"] == target_id
            ),
            None,
        )
        if explanation is None:
            raise RecursiveInferenceError(
                "red-team attack target does not resolve a sealed U6 explanation"
            )
        claims = {
            item["claim_id"]: item for item in graph["claims"]
        }
        referenced = [claims[claim_id] for claim_id in explanation["claim_ids"]]
        return (
            {claim["identity"] for claim in referenced},
            {
                evidence_id
                for claim in referenced
                for evidence_id in claim["evidence_refs"]
            },
            target_id,
        )
    raise RecursiveInferenceError("red-team attack target role is not frozen")


def _validate_red_team_semantics(
    report: Mapping[str, Any],
    *,
    graph: Mapping[str, Any],
    lineage: Mapping[str, Any],
    order_evaluation: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> None:
    if set(registry) != set(lineage["recursive_state_artifact_hashes"]):
        raise RecursiveInferenceError(
            "red-team report requires every sealed recursive-state artifact named by U7"
        )
    state_by_hash = dict(registry)
    states_by_node = {
        node["node_id"]: state_by_hash[node["recursive_state_artifact_sha256"]]
        for node in lineage["nodes"]
    }

    attack_ids: set[str] = set()
    target_ids: set[str] = set()
    for attack in report["attacks"]:
        attack_id = attack["attack_id"]
        if attack_id in attack_ids:
            raise RecursiveInferenceError("red-team attack identities must be unique")
        attack_ids.add(attack_id)
        identities, evidence_refs, target_id = _attack_target_identity(
            attack["target"],
            graph=graph,
            lineage=lineage,
            states_by_node=states_by_node,
        )
        target_ids.add(target_id)
        if identities and attack["evidence_identity"] not in identities:
            raise RecursiveInferenceError(
                "red-team report cannot change the sealed target evidence identity"
            )
        if not set(attack["evidence_refs"]).issubset(evidence_refs):
            raise RecursiveInferenceError(
                "red-team attack evidence_refs exceed the sealed target evidence authority"
            )

    sensitivity_ids = [item["check_id"] for item in report["sensitivity_checks"]]
    if len(set(sensitivity_ids)) != len(sensitivity_ids):
        raise RecursiveInferenceError(
            "red-team sensitivity check identities must be unique"
        )
    if attack_ids.intersection(sensitivity_ids) or (
        attack_ids | set(sensitivity_ids)
    ).intersection(target_ids):
        raise RecursiveInferenceError(
            "red-team challenge, sensitivity, and target identity roles must be distinct"
        )

    expected_baselines = {
        (record["order"], record["baseline"]["baseline_id"])
        for record in order_evaluation["evaluations"]
    }
    actual_baselines = {
        (record["order"], record["baseline_ref"])
        for record in report["baseline_comparisons"]
    }
    if (
        actual_baselines != expected_baselines
        or len(report["baseline_comparisons"]) != len(expected_baselines)
    ):
        raise RecursiveInferenceError(
            "red-team baseline comparison must exactly cover the sealed order evaluation"
        )

    challenge_ids = attack_ids | set(sensitivity_ids)
    unresolved_ids: set[str] = set()
    for item in report["unresolved_items"]:
        if item["unresolved_item_id"] in unresolved_ids:
            raise RecursiveInferenceError(
                "red-team unresolved item identities must be unique"
            )
        unresolved_ids.add(item["unresolved_item_id"])
        if item["challenge_id"] not in challenge_ids:
            raise RecursiveInferenceError(
                "red-team unresolved item must name an existing challenge"
            )
    if unresolved_ids.intersection(challenge_ids | target_ids):
        raise RecursiveInferenceError(
            "red-team unresolved, challenge, and target identity roles must be distinct"
        )

    results = {attack["result"] for attack in report["attacks"]}
    if report["unresolved_items"]:
        expected_status = "needs-attention"
    elif "reject" in results:
        expected_status = "rejected"
    elif "revise" in results:
        expected_status = "revised"
    else:
        expected_status = "survives"
    if report["overall_status"] != expected_status:
        raise RecursiveInferenceError(
            "red-team overall status does not match its attacks and unresolved items"
        )


def _validate_red_team_report(
    red_team_report: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    order_evaluation: Mapping[str, object],
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_claim_mechanism_graph_artifact_sha256: str,
    expected_recursive_lineage_artifact_sha256: str,
    expected_order_evaluation_artifact_sha256: str,
) -> dict[str, Any]:
    graph, lineage, expected_hashes, binding = _validate_u6_u7_artifact_authority(
        claim_mechanism_graph=claim_mechanism_graph,
        recursive_lineage=recursive_lineage,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
        expected_recursive_lineage_artifact_sha256=(
            expected_recursive_lineage_artifact_sha256
        ),
    )
    expected_evaluation_hash = _require_sha256(
        expected_order_evaluation_artifact_sha256,
        label="expected U8 order evaluation artifact hash",
    )
    if expected_evaluation_hash in expected_hashes:
        raise RecursiveInferenceError(
            "U6/U7/U8 authority roles require three distinct artifact hashes"
        )
    evaluation = _validate_order_evaluation(
        order_evaluation,
        claim_mechanism_graph=graph,
        recursive_lineage=lineage,
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        expected_claim_mechanism_graph_artifact_sha256=expected_hashes[0],
        expected_recursive_lineage_artifact_sha256=expected_hashes[1],
    )
    if _canonical_sha256(evaluation) != expected_evaluation_hash:
        raise RecursiveInferenceError(
            "U8 order evaluation full artifact hash authority does not match the external expectation"
        )
    snapshot = _phase(
        "ultra-red-team-report.schema.json",
        "crossframe.ultra.v82.red-team-report",
        "U8",
        _snapshot_mapping(red_team_report, label="U8 red-team report"),
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        label="U8 red-team report",
    )
    report_hashes = (
        snapshot.get("claim_mechanism_graph_artifact_sha256"),
        snapshot.get("recursive_lineage_artifact_sha256"),
        snapshot.get("order_evaluation_artifact_sha256"),
    )
    if report_hashes != (*expected_hashes, expected_evaluation_hash):
        raise RecursiveInferenceError(
            "red-team U6/U7/order evaluation authority does not match the sealed artifacts"
        )

    registry = _state_registry_documents(
        recursive_state_artifacts,
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        expected_hashes=(
            lineage["world_volume_artifact_sha256"],
            lineage["transformation_ledger_artifact_sha256"],
            expected_hashes[0],
        ),
        expected_concept_hash=lineage["concept_disposition_artifact_sha256"],
    )
    _validate_red_team_semantics(
        snapshot,
        graph=graph,
        lineage=lineage,
        order_evaluation=evaluation,
        registry=registry,
    )
    return snapshot


def _seal_red_team_report(
    red_team_report: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    order_evaluation: Mapping[str, object],
    recursive_state_artifacts: Mapping[str, Mapping[str, object]],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_claim_mechanism_graph_artifact_sha256: str,
    expected_recursive_lineage_artifact_sha256: str,
    expected_order_evaluation_artifact_sha256: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(red_team_report, label="unsealed U8 red-team report")
    if "content_sha256" in snapshot:
        raise RecursiveInferenceError(
            "U8 producer accepts an unsealed red-team report without content_sha256"
        )
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return _validate_red_team_report(
        snapshot,
        claim_mechanism_graph=claim_mechanism_graph,
        recursive_lineage=recursive_lineage,
        order_evaluation=order_evaluation,
        recursive_state_artifacts=recursive_state_artifacts,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_claim_mechanism_graph_artifact_sha256=(
            expected_claim_mechanism_graph_artifact_sha256
        ),
        expected_recursive_lineage_artifact_sha256=(
            expected_recursive_lineage_artifact_sha256
        ),
        expected_order_evaluation_artifact_sha256=(
            expected_order_evaluation_artifact_sha256
        ),
    )
