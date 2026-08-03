from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import compute_artifact_content_sha256


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
    "runtime_version": "1.0.0",
    "artifact_schema_version": 1,
    "compiler_version": "1.0.0",
    "validator_version": "1.0.0",
    "article_contract_version": "1.0.0",
    "source_tree_sha256": (
        "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
    ),
}
REGISTRY_SHA256 = (
    "8c88d2b3d47c378b7beccd74082f8b460f5e91780f18aae1fd74d3a26242ff6d"
)
ROUTE_MAP_SHA256 = (
    "b4b14305303db066f1ecc7bfd1f8e5703925632131f13aba0cd9955e6534b20f"
)
CONTRACT_MAP_SHA256 = (
    "f21f844022d7b67aae1596c154cfe75ecb7b000b0d7959533b71c41c2293e84e"
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


def make_evidence_ledger() -> dict[str, Any]:
    evidence = load_fixture("evidence-ledger-valid.json")
    evidence["run_id"] = RUN_ID
    return rehash_artifact(evidence)


def make_concept_disposition(
    evidence: Mapping[str, object],
    world: Mapping[str, object],
    transformations: Mapping[str, object],
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.concept-disposition",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": copy.deepcopy(VERSION_BINDING),
        "generated_at": "2026-08-02T09:00:00Z",
        "phase_id": "U5",
        "evidence_artifact_sha256": canonical_sha256(evidence),
        "evidence_content_sha256": evidence["content_sha256"],
        "world_volume_artifact_sha256": canonical_sha256(world),
        "world_volume_content_sha256": world["content_sha256"],
        "transformation_ledger_artifact_sha256": canonical_sha256(transformations),
        "transformation_ledger_content_sha256": transformations["content_sha256"],
        "registry_sha256": REGISTRY_SHA256,
        "route_map_sha256": ROUTE_MAP_SHA256,
        "contract_map_sha256": CONTRACT_MAP_SHA256,
        "required_route_ids": ["ROUTE-CHANNEL"],
        "required_contract_ids": ["CONTRACT-CHANNEL"],
        "required_requirement_ids": ["REQUIREMENT-CHANNEL"],
        "dispositions": [
            {
                "concept_id": "V82-CONCEPT-CHANNEL",
                "status": "applied",
                "rationale": (
                    "The sealed world volume contains a local review channel and the "
                    "U5 ledger preserves its relation boundary."
                ),
                "route_required": True,
                "neighbor_concept_ids": [],
                "route_ids": ["ROUTE-CHANNEL"],
                "contract_ids": ["CONTRACT-CHANNEL"],
                "requirement_ids": ["REQUIREMENT-CHANNEL"],
                "obligation_ids": ["OBLIGATION-CHANNEL"],
                "evidence_ids": ["EVIDENCE-ROSTER-ATLAS"],
                "unknown_ids": [],
                "transformation_ids": ["TRANSFORM-CIRCLE-RELATION"],
                "condition_branch": None,
            }
        ],
        "semantic_obligations": [
            {
                "obligation_id": "OBLIGATION-CHANNEL",
                "concept_id": "V82-CONCEPT-CHANNEL",
                "status": "applied",
                "semantic_unit_id": "UNIT-CHANNEL-LOCALITY",
                "evidence_ids": ["EVIDENCE-ROSTER-ATLAS"],
                "unknown_ids": [],
                "transformation_ids": ["TRANSFORM-CIRCLE-RELATION"],
                "route_ids": ["ROUTE-CHANNEL"],
                "contract_ids": ["CONTRACT-CHANNEL"],
                "requirement_ids": ["REQUIREMENT-CHANNEL"],
                "condition_branch_id": None,
            }
        ],
        "unvisited_concept_ids": [],
        "closure_complete": True,
    }
    return rehash_artifact(artifact)


def make_authority_chain() -> dict[str, dict[str, Any]]:
    evidence = make_evidence_ledger()
    world = load_fixture("world-volume-valid.json")
    transformations = load_fixture("transformation-valid.json")
    concept = make_concept_disposition(evidence, world, transformations)
    return {
        "evidence": evidence,
        "world": world,
        "transformations": transformations,
        "concept": concept,
    }


def load_runtime():
    spec = importlib.util.find_spec("ultra_runtime.judgment")
    assert spec is not None, "missing U6 claim/mechanism producer"
    return importlib.import_module("ultra_runtime.judgment")


def authority_kwargs(
    chain: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "evidence_ledger": chain["evidence"],
        "world_volume": chain["world"],
        "transformation_ledger": chain["transformations"],
        "concept_disposition": chain["concept"],
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_ledger_artifact_sha256": canonical_sha256(
            chain["evidence"]
        ),
        "expected_world_volume_artifact_sha256": canonical_sha256(chain["world"]),
        "expected_transformation_ledger_artifact_sha256": canonical_sha256(
            chain["transformations"]
        ),
        "expected_concept_disposition_artifact_sha256": canonical_sha256(
            chain["concept"]
        ),
    }


def validate_graph(
    graph: Mapping[str, object],
    chain: Mapping[str, Mapping[str, object]] | None = None,
    **authority_overrides: object,
) -> dict[str, Any]:
    runtime = load_runtime()
    accepted_chain = chain or make_authority_chain()
    kwargs = authority_kwargs(accepted_chain)
    kwargs.update(authority_overrides)
    return runtime._validate_claim_mechanism_graph(graph, **kwargs)


def seal_graph(
    graph: Mapping[str, object],
    chain: Mapping[str, Mapping[str, object]] | None = None,
    **authority_overrides: object,
) -> dict[str, Any]:
    runtime = load_runtime()
    accepted_chain = chain or make_authority_chain()
    kwargs = authority_kwargs(accepted_chain)
    kwargs.update(authority_overrides)
    return runtime._seal_claim_mechanism_graph(graph, **kwargs)


def rebind_chain(
    evidence: Mapping[str, object],
    graph: Mapping[str, object],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rebound_evidence = rehash_artifact(evidence)
    rebound_world = load_fixture("world-volume-valid.json")
    rebound_world["evidence_artifact_sha256"] = canonical_sha256(rebound_evidence)
    rebound_world["evidence_content_sha256"] = rebound_evidence["content_sha256"]
    rebound_world = rehash_artifact(rebound_world)

    rebound_transformations = load_fixture("transformation-valid.json")
    rebound_transformations["evidence_artifact_sha256"] = canonical_sha256(
        rebound_evidence
    )
    rebound_transformations["evidence_content_sha256"] = rebound_evidence[
        "content_sha256"
    ]
    rebound_transformations["world_volume_artifact_sha256"] = canonical_sha256(
        rebound_world
    )
    rebound_transformations["world_volume_content_sha256"] = rebound_world[
        "content_sha256"
    ]
    rebound_transformations = rehash_artifact(rebound_transformations)

    rebound_concept = make_concept_disposition(
        rebound_evidence, rebound_world, rebound_transformations
    )
    rebound_graph = copy.deepcopy(dict(graph))
    rebound_graph["evidence_ledger_artifact_sha256"] = canonical_sha256(
        rebound_evidence
    )
    rebound_graph["world_volume_artifact_sha256"] = canonical_sha256(rebound_world)
    rebound_graph["transformation_ledger_artifact_sha256"] = canonical_sha256(
        rebound_transformations
    )
    rebound_graph["concept_disposition_artifact_sha256"] = canonical_sha256(
        rebound_concept
    )
    rebound_graph = rehash_artifact(rebound_graph)
    return (
        {
            "evidence": rebound_evidence,
            "world": rebound_world,
            "transformations": rebound_transformations,
            "concept": rebound_concept,
        },
        rebound_graph,
    )


def test_existing_insight_helper_shape_and_frozen_effects() -> None:
    runtime = load_runtime()
    parameter = tuple(inspect.signature(runtime.qualifies_as_insight).parameters.values())
    assert tuple(item.name for item in parameter) == ("candidate",)
    assert parameter[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameter[0].default is inspect.Parameter.empty
    assert runtime.INSIGHT_EFFECTS == (
        "changes-ranking",
        "explains-residual",
        "changes-observable-forecast",
        "changes-counterfactual",
        "changes-intervention",
        "identifies-circle-scale-channel",
    )
    assert runtime.qualifies_as_insight({"effects": ["changes-ranking"]})
    assert not runtime.qualifies_as_insight({"effects": []})
    assert not runtime.qualifies_as_insight({"effects": ["restates-claim"]})


def test_valid_graph_binds_the_accepted_u3_u4_u5_authority_without_mutation() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    chain = make_authority_chain()
    before_graph = copy.deepcopy(graph)
    before_chain = copy.deepcopy(chain)

    validated = validate_graph(graph, chain)

    assert validated == graph
    assert graph == before_graph
    assert chain == before_chain
    assert graph["evidence_ledger_artifact_sha256"] == canonical_sha256(
        chain["evidence"]
    )
    assert graph["world_volume_artifact_sha256"] == canonical_sha256(chain["world"])
    assert graph["transformation_ledger_artifact_sha256"] == canonical_sha256(
        chain["transformations"]
    )
    assert graph["concept_disposition_artifact_sha256"] == canonical_sha256(
        chain["concept"]
    )


def test_private_producer_seals_only_after_external_authority_matches() -> None:
    expected = load_fixture("claim-mechanism-graph-valid.json")
    candidate = copy.deepcopy(expected)
    del candidate["content_sha256"]
    before = copy.deepcopy(candidate)

    assert seal_graph(candidate) == expected
    assert candidate == before

    stale = copy.deepcopy(candidate)
    stale["evidence_ledger_artifact_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="U3 evidence ledger authority"):
        seal_graph(stale)
    assert "content_sha256" not in stale


@pytest.mark.parametrize(
    ("left", "right"),
    (
        (
            "evidence_ledger_artifact_sha256",
            "world_volume_artifact_sha256",
        ),
        (
            "world_volume_artifact_sha256",
            "transformation_ledger_artifact_sha256",
        ),
        (
            "transformation_ledger_artifact_sha256",
            "concept_disposition_artifact_sha256",
        ),
    ),
)
def test_swapped_upstream_roles_are_rejected(left: str, right: str) -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph[left], graph[right] = graph[right], graph[left]
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="upstream authority"):
        validate_graph(graph)


def test_graph_cannot_self_select_external_authority() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["evidence_ledger_artifact_sha256"] = "f" * 64
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="full artifact hash"):
        validate_graph(
            graph,
            expected_evidence_ledger_artifact_sha256="f" * 64,
        )


def test_u5_concept_chain_cannot_hide_a_stale_transformation_authority() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    chain = make_authority_chain()
    concept = copy.deepcopy(chain["concept"])
    concept["transformation_ledger_artifact_sha256"] = "f" * 64
    concept = rehash_artifact(concept)
    chain["concept"] = concept
    graph["concept_disposition_artifact_sha256"] = canonical_sha256(concept)
    graph = rehash_artifact(graph)

    with pytest.raises(ValueError, match="stale upstream hash chain"):
        validate_graph(graph, chain)


def test_definition_identity_cannot_be_reused_across_claim_and_mechanism_roles() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    old_id = graph["mechanisms"][0]["mechanism_id"]
    reused_id = graph["central_claim_id"]
    graph["mechanisms"][0]["mechanism_id"] = reused_id
    for explanation in graph["explanations"]:
        explanation["mechanism_ids"] = [
            reused_id if item == old_id else item
            for item in explanation["mechanism_ids"]
        ]
    for edge in graph["edges"]:
        for endpoint in (edge["source"], edge["target"]):
            if endpoint.get("mechanism_id") == old_id:
                endpoint["mechanism_id"] = reused_id
    graph = rehash_artifact(graph)

    with pytest.raises(ValueError, match="identity roles"):
        validate_graph(graph)


def test_graph_references_must_resolve_their_declared_roles() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["mechanisms"][0]["channel_refs"] = ["CHANNEL-NOT-FROZEN"]
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="channel_refs"):
        validate_graph(graph)


def test_user_claim_cannot_be_used_as_material_evidence() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["claims"][0]["evidence_refs"] = ["EVIDENCE-ASSOCIATION-CHARTER"]
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="user claim"):
        validate_graph(graph)


def test_simulated_result_cannot_be_promoted_to_observed_fact() -> None:
    evidence = make_evidence_ledger()
    simulated = copy.deepcopy(evidence["entries"][2])
    simulated.update(
        {
            "evidence_id": "EVIDENCE-SIMULATION",
            "identity": "simulated",
            "statement": "A model-generated branch produced a local response.",
            "source_refs": ["SOURCE-SIMULATION"],
            "confidence": "low",
            "upstream_lineage": ["UPSTREAM-SIMULATION"],
            "supported_claim": "The simulated branch contains this response.",
            "cannot_prove": "The simulation cannot establish an observed fact.",
        }
    )
    evidence["entries"].append(simulated)
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["claims"][0]["identity"] = "observed"
    graph["claims"][0]["evidence_refs"] = ["EVIDENCE-SIMULATION"]
    chain, rebound_graph = rebind_chain(evidence, graph)

    with pytest.raises(ValueError, match="simulated result"):
        validate_graph(rebound_graph, chain)


def test_justified_partial_ranking_uses_one_contiguous_ranked_prefix() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["partial_ranking_justification"] = (
        "The frozen evidence orders the two leading explanations but does not "
        "distinguish the mixture from the residual branch."
    )
    ranks = (1, 2, None, None)
    for explanation, rank in zip(graph["explanations"], ranks, strict=True):
        explanation["rank"] = rank
    graph = rehash_artifact(graph)

    assert validate_graph(graph) == graph


@pytest.mark.parametrize(
    ("justification", "ranks"),
    (
        (None, (1, 2, 3, None)),
        ("Partial order.", (1, 1, None, None)),
        ("Partial order.", (1, 3, None, None)),
        ("Partial order.", (None, None, None, None)),
        ("Partial order.", (1, 2, 3, 4)),
        (None, (1, 2, 3, 5)),
    ),
)
def test_ranking_rejects_unjustified_tied_gapped_empty_or_out_of_range_forms(
    justification: str | None,
    ranks: tuple[int | None, ...],
) -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["partial_ranking_justification"] = justification
    for explanation, rank in zip(graph["explanations"], ranks, strict=True):
        explanation["rank"] = rank
    graph = rehash_artifact(graph)

    with pytest.raises(ValueError, match="ranking"):
        validate_graph(graph)


def test_main_and_strongest_rival_must_be_semantically_distinct() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    by_kind = {item["kind"]: item for item in graph["explanations"]}
    by_kind["strongest-rival"]["claim_ids"] = copy.deepcopy(
        by_kind["main"]["claim_ids"]
    )
    by_kind["strongest-rival"]["mechanism_ids"] = copy.deepcopy(
        by_kind["main"]["mechanism_ids"]
    )
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="strongest rival"):
        validate_graph(graph)


def test_insight_cannot_become_mechanism_or_framework_authority() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["edges"][0] = {
        "edge_id": graph["edges"][0]["edge_id"],
        "source": {"insight_id": graph["insights"][0]["insight_id"]},
        "target": {"claim_id": graph["central_claim_id"]},
        "edge_type": "supported-by",
    }
    graph = rehash_artifact(graph)
    with pytest.raises(ValueError, match="insight.*authority"):
        validate_graph(graph)

    extra_authority = load_fixture("claim-mechanism-graph-valid.json")
    extra_authority["insights"][0]["framework_authority"] = True
    extra_authority = rehash_artifact(extra_authority)
    with pytest.raises(ValueError, match="invalid U6 claim/mechanism graph"):
        validate_graph(extra_authority)
