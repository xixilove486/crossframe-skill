from __future__ import annotations

import copy
from dataclasses import fields
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import compute_artifact_content_sha256, validate_instance


RUN_ID = "ultra-world-fixture-run"
VERSION_BINDING: dict[str, object] = {
    "framework_version": "8.2",
    "framework_revision": "v8.2-r1",
    "framework_raw_sha256": (
        "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
    ),
    "framework_semantic_sha256": (
        "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
    ),
    "runtime_version": "1.1.0",
    "artifact_schema_version": 2,
    "compiler_version": "1.0.0",
    "validator_version": "1.1.0",
    "article_contract_version": "1.1.0",
    "source_tree_sha256": (
        "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
    ),
}
WORLD_SHA256 = "053716f0de6b642d2bc53b82862761c5815402005ecaad3e2f0abfc5103cc746"
TRANSFORMATION_SHA256 = (
    "76bc58745c59ea40566e17ad2324cfbd737d4f7fcd4a92ce2c179b42f8288084"
)
CLAIM_GRAPH_SHA256 = (
    "40d6e4d2b7cbf2ce41ea0861513e0d01c14cfa0fe8ad50382c073f9aa116cb19"
)
CLAIM_GRAPH_CONTENT_SHA256 = (
    "3a9fb63b8bf7b4e6db616a62a29a3f499d6809d077cd7bbf67d60470a811af8a"
)


def load_fixture(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def rehash_artifact(value: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(value))
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return snapshot


def load_runtime():
    spec = importlib.util.find_spec("ultra_runtime.recursion")
    assert spec is not None, "missing U7 recursive-state and lineage producer"
    return importlib.import_module("ultra_runtime.recursion")


def upstream() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        load_fixture("world-volume-valid.json"),
        load_fixture("transformation-valid.json"),
        load_fixture("claim-mechanism-graph-valid.json"),
    )


def derive_state(base: Mapping[str, object], **changes: object) -> dict[str, Any]:
    state = copy.deepcopy(dict(base))
    state.pop("content_sha256", None)
    state.update(changes)
    return rehash_artifact(state)


def recursive_states() -> dict[str, dict[str, Any]]:
    main1 = load_fixture("recursive-state-valid.json")
    return {
        "main1": main1,
        "main2": derive_state(
            main1,
            generated_at="2026-08-02T10:05:00Z",
            node_id="NODE-MAIN-ORDER-2",
            parent_node_id="NODE-MAIN-ORDER-1",
            order=2,
            full_state_sha256=(
                "a9b46daf47867f0706406687ee5e23b05712cdf99a8a3f4e2b5b659999846ad4"
            ),
            event_id="EVENT-ACTION-SET-REVERSAL",
            mechanism_ids=["MECHANISM-WORKLOAD-ALLOCATION"],
            state_diff_sha256=(
                "7fa17563e075a39cf12c75e515ffe874977d940fe2d3a636ef9b3fc85f3bdd97"
            ),
            signal_ids=["SIGNAL-ACTION-REVERSAL"],
            evidence_identity="simulated-result",
            declared_evidence_grade="low",
        ),
        "main3": derive_state(
            main1,
            generated_at="2026-08-02T10:10:00Z",
            node_id="NODE-MAIN-ORDER-3",
            parent_node_id="NODE-MAIN-ORDER-2",
            order=3,
            full_state_sha256=(
                "830f9e7149814e40ca028af7408b2f2afe2a1abd6a0207f2d30de9cdfeaa118b"
            ),
            event_id="EVENT-INSTITUTIONAL-LOCK-IN",
            mechanism_ids=["MECHANISM-COMBINED-PRESSURE"],
            state_diff_sha256=(
                "663a9e460d9fb3970411ec16d8140f49a48ad60637b96d8ae0ca437d2ca19d8f"
            ),
            signal_ids=["SIGNAL-INSTITUTIONAL-LOCK"],
            evidence_identity="simulated-result",
            declared_evidence_grade="low",
        ),
        "rival1": derive_state(
            main1,
            generated_at="2026-08-02T10:01:00Z",
            path_id="PATH-RIVAL",
            node_id="NODE-RIVAL-ORDER-1",
            parent_path_id="PATH-RIVAL",
            full_state_sha256=(
                "72949ab79e88afb8a38cff054a78404db2bfe55336c6c8faa860e67fc27cfc3c"
            ),
            event_id="EVENT-RIVAL-WORKLOAD",
            mechanism_ids=["MECHANISM-WORKLOAD-ALLOCATION"],
            state_diff_sha256=(
                "6ff419a803b41b17dd267ea22cfd8800072f3ae7f35d92558f6f7896e289f1fd"
            ),
            signal_ids=["SIGNAL-RIVAL-WORKLOAD"],
            evidence_identity="competing-explanation",
            declared_evidence_grade="low",
        ),
        "mixture1": derive_state(
            main1,
            generated_at="2026-08-02T10:02:00Z",
            path_id="PATH-MIXTURE",
            node_id="NODE-MIXTURE-ORDER-1",
            parent_path_id="PATH-MIXTURE",
            full_state_sha256=(
                "596fe5666c335e9770a9ee1acbed81a7955bce822afaeac6f3f5f56384f0e544"
            ),
            event_id="EVENT-MIXTURE-PRESSURE",
            mechanism_ids=["MECHANISM-COMBINED-PRESSURE"],
            state_diff_sha256=(
                "f59670c1b37cd097540827cff040537593774c807ed9aec010c56579bab29973"
            ),
            signal_ids=["SIGNAL-MIXTURE-PRESSURE"],
            evidence_identity="competing-explanation",
            declared_evidence_grade="low",
        ),
        "residual1": derive_state(
            main1,
            generated_at="2026-08-02T10:03:00Z",
            path_id="PATH-RESIDUAL",
            node_id="NODE-RESIDUAL-ORDER-1",
            parent_path_id="PATH-RESIDUAL",
            full_state_sha256=(
                "d05dbb2b880d1c520c3cc9f84e973a62ef02fb83c0eff196c7aeb926bc6f9791"
            ),
            event_id="EVENT-RESIDUAL-PEER",
            mechanism_ids=["MECHANISM-PEER-RESIDUAL"],
            state_diff_sha256=(
                "ea7ade3f6cdc3be7a4c9294bf4991ab15c1ad6e1bc01071d2a92cdf2f6e1447a"
            ),
            signal_ids=["SIGNAL-RESIDUAL-PEER"],
            evidence_identity="unknown",
            declared_evidence_grade="unknown",
        ),
    }


def state_registry(
    states: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, dict[str, Any]]:
    accepted = states or recursive_states()
    return {
        canonical_sha256(state): copy.deepcopy(dict(state))
        for state in accepted.values()
    }


def authority_kwargs(
    *,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    world: Mapping[str, object] | None = None,
    transformations: Mapping[str, object] | None = None,
    claim_graph: Mapping[str, object] | None = None,
) -> dict[str, object]:
    accepted_world, accepted_transformations, accepted_claim_graph = upstream()
    if world is not None:
        accepted_world = copy.deepcopy(dict(world))
    if transformations is not None:
        accepted_transformations = copy.deepcopy(dict(transformations))
    if claim_graph is not None:
        accepted_claim_graph = copy.deepcopy(dict(claim_graph))
    return {
        "recursive_state_artifacts": registry or {},
        "transformation_ledger": accepted_transformations,
        "claim_mechanism_graph": accepted_claim_graph,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_world_volume_artifact_sha256": WORLD_SHA256,
        "expected_transformation_ledger_artifact_sha256": TRANSFORMATION_SHA256,
        "expected_claim_mechanism_graph_artifact_sha256": CLAIM_GRAPH_SHA256,
    }


def validate_state(
    state: Mapping[str, object],
    *,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    runtime = load_runtime()
    world, _, _ = upstream()
    kwargs = authority_kwargs(registry=registry)
    kwargs.update(overrides)
    return runtime._validate_recursive_state(state, parent_volume=world, **kwargs)


def seal_state(
    state: Mapping[str, object],
    *,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    runtime = load_runtime()
    world, _, _ = upstream()
    kwargs = authority_kwargs(registry=registry)
    kwargs.update(overrides)
    return runtime._seal_recursive_state(state, parent_volume=world, **kwargs)


def validate_lineage(
    lineage: Mapping[str, object],
    *,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    **overrides: object,
):
    runtime = load_runtime()
    world, _, _ = upstream()
    kwargs = authority_kwargs(registry=registry or state_registry())
    kwargs.update(overrides)
    return runtime._validate_recursive_lineage_bundle(
        lineage, parent_volume=world, **kwargs
    )


def test_public_recursive_lineage_contract_is_frozen() -> None:
    runtime = load_runtime()
    signature = inspect.signature(runtime.validate_recursive_lineage)
    assert tuple(signature.parameters) == ("lineage", "parent_volume")
    assert tuple(item.name for item in fields(runtime.LineageValidation)) == (
        "node_ids",
        "maximum_order",
        "early_stop_nodes",
        "inherited_unknown_ids",
        "inherited_residual_ids",
    )
    assert runtime.BRANCH_KINDS == (
        "main",
        "strongest-rival",
        "mixture",
        "residual",
    )
    assert runtime.STOP_KINDS == (
        "order-limit",
        "baseline-wins",
        "no-material-state-change",
        "local-predictability-exhausted",
        "evidence-boundary",
    )


def test_sealed_recursive_state_fixture_binds_distinct_u4_u5_u6_authority() -> None:
    state = load_fixture("recursive-state-valid.json")
    before = copy.deepcopy(state)
    assert validate_state(state) == state
    assert state == before
    validate_instance("ultra-recursive-state.schema.json", state)
    assert state["world_volume_artifact_sha256"] == WORLD_SHA256
    assert state["transformation_ledger_artifact_sha256"] == TRANSFORMATION_SHA256
    assert state["claim_mechanism_graph_artifact_sha256"] == CLAIM_GRAPH_SHA256
    assert len(
        {
            state["world_volume_artifact_sha256"],
            state["transformation_ledger_artifact_sha256"],
            state["concept_disposition_artifact_sha256"],
            state["claim_mechanism_graph_artifact_sha256"],
        }
    ) == 4


def test_recursive_state_producer_seals_only_after_authority_matches() -> None:
    expected = load_fixture("recursive-state-valid.json")
    candidate = copy.deepcopy(expected)
    candidate.pop("content_sha256")
    before = copy.deepcopy(candidate)
    assert seal_state(candidate) == expected
    assert candidate == before


def test_valid_lineage_resolves_every_sealed_state_without_mutation() -> None:
    runtime = load_runtime()
    world, _, _ = upstream()
    lineage = load_fixture("recursive-lineage-valid.json")
    registry = state_registry()
    before_lineage = copy.deepcopy(lineage)
    before_registry = copy.deepcopy(registry)
    result = validate_lineage(lineage, registry=registry)
    assert result == runtime.LineageValidation(
        node_ids=tuple(node["node_id"] for node in lineage["nodes"]),
        maximum_order=3,
        early_stop_nodes=("NODE-MAIN-ORDER-3",),
        inherited_unknown_ids=("UNKNOWN-ADAPTATION",),
        inherited_residual_ids=("RESIDUAL-PEER-EFFECT",),
    )
    assert runtime.validate_recursive_lineage(lineage, world) == result
    assert lineage == before_lineage
    assert registry == before_registry


def test_state_sequence_models_direct_reversal_and_institutional_lock_in() -> None:
    states = recursive_states()
    assert states["main1"]["order"] == 1
    assert states["main1"]["event_id"] == "WORLD-EVENT-LOCAL"
    assert states["main2"]["order"] == 2
    assert states["main2"]["event_id"] == "EVENT-ACTION-SET-REVERSAL"
    assert states["main3"]["order"] == 3
    assert states["main3"]["event_id"] == "EVENT-INSTITUTIONAL-LOCK-IN"
    validate_lineage(load_fixture("recursive-lineage-valid.json"))


def test_schema_valid_invalid_fixture_is_rejected_semantically() -> None:
    invalid = load_fixture("recursive-lineage-invalid.json")
    validate_instance("ultra-recursive-lineage.schema.json", invalid)
    with pytest.raises(ValueError, match="order-1|branch kinds|cycle"):
        validate_lineage(invalid, registry={
            canonical_sha256(load_fixture("recursive-state-valid.json")):
            load_fixture("recursive-state-valid.json")
        })


def test_lineage_rejects_caller_declared_state_hash_without_artifact() -> None:
    lineage = load_fixture("recursive-lineage-valid.json")
    registry = state_registry()
    registry.pop(lineage["nodes"][2]["recursive_state_artifact_sha256"])
    with pytest.raises(ValueError, match="sealed recursive-state artifact"):
        validate_lineage(lineage, registry=registry)


def test_state_registry_key_must_equal_recomputed_full_artifact_hash() -> None:
    registry = state_registry()
    artifact = registry.pop(next(iter(registry)))
    registry["f" * 64] = artifact
    with pytest.raises(ValueError, match="registry key"):
        validate_lineage(load_fixture("recursive-lineage-valid.json"), registry=registry)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("expected_world_volume_artifact_sha256", TRANSFORMATION_SHA256),
        ("expected_transformation_ledger_artifact_sha256", CLAIM_GRAPH_SHA256),
        ("expected_claim_mechanism_graph_artifact_sha256", WORLD_SHA256),
    ),
)
def test_swapped_or_stale_external_authority_is_rejected(
    field: str, value: str
) -> None:
    with pytest.raises(ValueError, match="authority"):
        validate_state(load_fixture("recursive-state-valid.json"), **{field: value})


def test_state_cannot_self_select_a_false_world_authority() -> None:
    state = load_fixture("recursive-state-valid.json")
    state["world_volume_artifact_sha256"] = "f" * 64
    state = rehash_artifact(state)
    with pytest.raises(ValueError, match="full artifact hash|world volume authority"):
        validate_state(
            state,
            expected_world_volume_artifact_sha256="f" * 64,
        )


def test_stale_u5_chain_is_rejected_even_when_resealed() -> None:
    _, transformations, _ = upstream()
    transformations["world_volume_artifact_sha256"] = "f" * 64
    transformations = rehash_artifact(transformations)
    with pytest.raises(ValueError, match="stale upstream hash chain"):
        validate_state(
            load_fixture("recursive-state-valid.json"),
            transformation_ledger=transformations,
            expected_transformation_ledger_artifact_sha256=canonical_sha256(
                transformations
            ),
        )


@pytest.mark.parametrize(
    "field",
    (
        "inherited_fact_ids",
        "inherited_evidence_ids",
        "inherited_unknown_ids",
        "inherited_loss_ids",
        "inherited_residual_ids",
    ),
)
def test_child_cannot_drop_inherited_identity(field: str) -> None:
    states = recursive_states()
    child = copy.deepcopy(states["main2"])
    child[field] = []
    child = rehash_artifact(child)
    with pytest.raises(ValueError, match="inherited"):
        validate_state(
            child,
            registry={canonical_sha256(states["main1"]): states["main1"]},
        )


def test_simulated_child_cannot_be_marked_observed() -> None:
    states = recursive_states()
    child = copy.deepcopy(states["main2"])
    child["evidence_identity"] = "observed"
    child = rehash_artifact(child)
    with pytest.raises(ValueError, match="simulated.*observed|observed.*frozen"):
        validate_state(
            child,
            registry={canonical_sha256(states["main1"]): states["main1"]},
        )


def test_deeper_order_does_not_increase_evidence_grade() -> None:
    states = recursive_states()
    child = copy.deepcopy(states["main2"])
    child["declared_evidence_grade"] = "high"
    child = rehash_artifact(child)
    with pytest.raises(ValueError, match="evidence grade"):
        validate_state(
            child,
            registry={canonical_sha256(states["main1"]): states["main1"]},
        )


def test_child_cannot_repeat_only_the_parent_state_and_transition() -> None:
    states = recursive_states()
    parent = states["main1"]
    child = copy.deepcopy(states["main2"])
    for field in (
        "full_state_sha256",
        "state_diff_sha256",
        "event_id",
        "mechanism_ids",
        "signal_ids",
    ):
        child[field] = copy.deepcopy(parent[field])
    child = rehash_artifact(child)
    with pytest.raises(ValueError, match="material recursive state change"):
        validate_state(
            child,
            registry={canonical_sha256(parent): parent},
        )


@pytest.mark.parametrize("order", (0, 4))
def test_recursive_state_rejects_order_outside_one_through_three(order: int) -> None:
    state = load_fixture("recursive-state-valid.json")
    state["order"] = order
    state = rehash_artifact(state)
    with pytest.raises(ValueError, match="recursive state"):
        validate_state(state)


def test_child_parent_identity_must_resolve_exactly_once() -> None:
    states = recursive_states()
    child = copy.deepcopy(states["main2"])
    child["parent_node_id"] = "NODE-NOT-SEALED"
    child = rehash_artifact(child)
    with pytest.raises(ValueError, match="parent recursive state"):
        validate_state(
            child,
            registry={canonical_sha256(states["main1"]): states["main1"]},
        )


def test_lineage_rejects_nonconsecutive_parent_and_cycle() -> None:
    lineage = load_fixture("recursive-lineage-valid.json")
    lineage["nodes"][-1]["parent_node_ids"] = ["NODE-MAIN-ORDER-1"]
    lineage = rehash_artifact(lineage)
    with pytest.raises(ValueError, match="immediately preceding order"):
        validate_lineage(lineage)

    cycle = load_fixture("recursive-lineage-valid.json")
    cycle["nodes"][0]["parent_node_ids"] = ["NODE-MAIN-ORDER-3"]
    cycle = rehash_artifact(cycle)
    with pytest.raises(ValueError, match="order-1|cycle"):
        validate_lineage(cycle)


def test_lineage_requires_all_four_branch_kinds() -> None:
    lineage = load_fixture("recursive-lineage-valid.json")
    lineage["branches"] = lineage["branches"][:-1]
    lineage = rehash_artifact(lineage)
    with pytest.raises(ValueError, match="branch kinds"):
        validate_lineage(lineage)


def test_merge_requires_compatible_inherited_state_identities() -> None:
    states = recursive_states()
    mixture = copy.deepcopy(states["mixture1"])
    mixture["inherited_unknown_ids"].append("UNKNOWN-MIXTURE-ONLY")
    mixture = rehash_artifact(mixture)
    states["mixture1"] = mixture
    registry = state_registry(states)
    lineage = load_fixture("recursive-lineage-valid.json")
    old_hash = lineage["nodes"][2]["recursive_state_artifact_sha256"]
    new_hash = canonical_sha256(mixture)
    lineage["nodes"][2]["recursive_state_artifact_sha256"] = new_hash
    lineage["recursive_state_artifact_hashes"] = [
        new_hash if value == old_hash else value
        for value in lineage["recursive_state_artifact_hashes"]
    ]
    lineage = rehash_artifact(lineage)
    with pytest.raises(ValueError, match="merge.*compatible"):
        validate_lineage(lineage, registry=registry)


@pytest.mark.parametrize("mutation", ("reason", "residual"))
def test_pruning_requires_reason_and_retained_residual(mutation: str) -> None:
    lineage = load_fixture("recursive-lineage-valid.json")
    branch = next(item for item in lineage["branches"] if item["status"] == "pruned")
    if mutation == "reason":
        branch["prune_reason"] = None
    else:
        branch["retained_residual_ids"] = []
    lineage = rehash_artifact(lineage)
    with pytest.raises(ValueError, match="prun|recursive lineage"):
        validate_lineage(lineage)


def test_partial_u6_ranking_with_null_tail_remains_valid_authority() -> None:
    world, transformations, graph = upstream()
    graph["partial_ranking_justification"] = (
        "The frozen evidence orders the leading paths but leaves the tail tied."
    )
    for explanation, rank in zip(
        graph["explanations"], (1, 2, None, None), strict=True
    ):
        explanation["rank"] = rank
    graph = rehash_artifact(graph)
    graph_hash = canonical_sha256(graph)
    candidate = load_fixture("recursive-state-valid.json")
    candidate.pop("content_sha256")
    candidate["claim_mechanism_graph_artifact_sha256"] = graph_hash
    sealed = seal_state(
        candidate,
        claim_mechanism_graph=graph,
        expected_claim_mechanism_graph_artifact_sha256=graph_hash,
    )
    assert sealed["claim_mechanism_graph_artifact_sha256"] == graph_hash
    assert CLAIM_GRAPH_CONTENT_SHA256 != CLAIM_GRAPH_SHA256
