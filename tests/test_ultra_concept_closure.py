from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
REFERENCES = ROOT / "skills" / "crossframe-ultra" / "references"
REGISTRY_PATH = REFERENCES / "concept-registry" / "v8.2-concept-registry.json"
ROUTE_PATH = REFERENCES / "v8.2-route-map.json"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from ultra_runtime.concept_closure import (
    ConceptClosureError,
    validate_concept_closure,
)
from ultra_runtime.article import order_and_validate_packets
from test_ultra_article import _valid_case


ARTICLE_UNITS = frozenset(
    {"ARTICLE-UNIT-M01", "ARTICLE-UNIT-M02", "ARTICLE-UNIT-M03"}
)


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def registry() -> dict[str, object]:
    return load_object(REGISTRY_PATH)


@pytest.fixture(scope="module")
def route_map() -> dict[str, object]:
    return load_object(ROUTE_PATH)


@pytest.fixture
def all_route_ids(route_map: dict[str, object]) -> tuple[str, ...]:
    routes = route_map["routes"]
    assert isinstance(routes, list)
    return tuple(route["route_id"] for route in routes)


@pytest.fixture
def closure_document(
    registry: dict[str, object],
) -> dict[str, object]:
    concepts = registry["concepts"]
    assert isinstance(concepts, list)
    status_by_concept = {
        "V82-M01": "applied",
        "V82-M02": "applied",
        "V82-M03": "tested-rejected",
        "V82-M04": "not-applicable",
        "V82-M05": "not-applicable",
        "V82-M06": "not-applicable",
        "V82-M07": "not-applicable",
        "V82-M08": "not-applicable",
        "V82-M09": "unknown-pending",
    }
    semantic_by_concept = {
        "V82-M01": ["ARTICLE-UNIT-M01"],
        "V82-M02": ["ARTICLE-UNIT-M02"],
        "V82-M03": ["ARTICLE-UNIT-M03"],
    }
    rationale_by_concept = {
        "V82-M01": "The unit-to-total partition is applied because weights and excluded members remain recoverable.",
        "V82-M02": "Boundary-member nesting is applied descriptively; no cross-layer causal claim is promoted.",
        "V82-M03": "The propagation candidate is retained as tested-rejected because the second directed hop is absent.",
        "V82-M04": "Longitudinal accumulation is not applicable because this frozen event has no repeated time window.",
        "V82-M05": "Institutionalization is not applicable because no durable rule or resource writeback is claimed.",
        "V82-M06": "Emergence is not applicable because no interaction model is compared with a simple additive baseline.",
        "V82-M07": "Delegation is not applicable to the household-to-team event and grants no new J authority.",
        "V82-M08": "Representation compression is not applicable because the source unit remains separately recoverable.",
        "V82-M09": "Lateral transfer remains pending until an independent target-domain instance and break map are collected.",
    }
    dispositions = []
    for concept in concepts:
        assert isinstance(concept, dict)
        concept_id = concept["concept_id"]
        status = status_by_concept[concept_id]
        dispositions.append(
            {
                "concept_id": concept_id,
                "status": status,
                "rationale": rationale_by_concept[concept_id],
                "route_required": True,
                "neighbor_concept_ids": list(concept["required_neighbors"]),
                "semantic_unit_ids": semantic_by_concept.get(concept_id, []),
                "condition_branch": (
                    "Re-open when an independently evidenced target-domain mapping exists."
                    if status == "unknown-pending"
                    else None
                ),
                "evidence_plan": (
                    "Collect a target-domain instance and a prohibited-mapping counterexample."
                    if status == "unknown-pending"
                    else None
                ),
            }
        )
    return {
        "schema_id": "crossframe.ultra.v82.concept-disposition",
        "schema_version": 1,
        "run_id": "ultra-task8-run",
        "version_binding": {
            "framework_version": "8.2",
            "framework_revision": "v8.2-r1",
            "framework_raw_sha256": "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20",
            "framework_semantic_sha256": "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0",
            "runtime_version": "1.0.0",
            "artifact_schema_version": 1,
            "compiler_version": "1.0.0",
            "validator_version": "1.0.0",
            "article_contract_version": "1.0.0",
            "source_tree_sha256": "c" * 64,
        },
        "generated_at": "2026-08-02T08:00:00Z",
        "content_sha256": "a" * 64,
        "phase_id": "U5",
        "registry_sha256": hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest(),
        "dispositions": dispositions,
        "unvisited_concept_ids": [],
        "closure_complete": True,
    }


def validate(
    document: dict[str, object],
    route_ids: tuple[str, ...],
) -> frozenset[str]:
    return validate_concept_closure(
        document,
        repo=ROOT,
        required_route_ids=route_ids,
    )


def test_all_v82_m01_through_m09_receive_independent_closed_dispositions(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    required_article_units = validate(closure_document, all_route_ids)

    assert required_article_units == ARTICLE_UNITS
    dispositions = closure_document["dispositions"]
    assert isinstance(dispositions, list)
    assert [item["concept_id"] for item in dispositions] == [
        f"V82-M{number:02d}" for number in range(1, 10)
    ]
    assert {item["status"] for item in dispositions} <= {
        "applied",
        "tested-rejected",
        "not-applicable",
        "unknown-pending",
    }


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-disposition",
        "duplicate-disposition",
        "unvisited",
        "closure-false",
        "wrong-registry-hash",
        "route-required-false",
        "wrong-neighbor-closure",
        "copied-rationale",
        "applied-without-unit",
        "unknown-without-plan",
    ),
)
def test_registry_route_neighbor_and_independent_disposition_closure_fail_closed(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
    mutation: str,
) -> None:
    broken = copy.deepcopy(closure_document)
    dispositions = broken["dispositions"]
    if mutation == "missing-disposition":
        dispositions.pop()
    elif mutation == "duplicate-disposition":
        dispositions.append(copy.deepcopy(dispositions[0]))
    elif mutation == "unvisited":
        broken["unvisited_concept_ids"] = ["V82-M09"]
    elif mutation == "closure-false":
        broken["closure_complete"] = False
    elif mutation == "wrong-registry-hash":
        broken["registry_sha256"] = "b" * 64
    elif mutation == "route-required-false":
        dispositions[0]["route_required"] = False
    elif mutation == "wrong-neighbor-closure":
        dispositions[0]["neighbor_concept_ids"] = ["V82-M02"]
    elif mutation == "copied-rationale":
        dispositions[1]["rationale"] = dispositions[0]["rationale"]
    elif mutation == "applied-without-unit":
        dispositions[0]["semantic_unit_ids"] = []
    elif mutation == "unknown-without-plan":
        pending = next(
            item for item in dispositions if item["status"] == "unknown-pending"
        )
        pending["condition_branch"] = None
        pending["evidence_plan"] = None
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(ConceptClosureError):
        validate(broken, all_route_ids)


def test_u5_obligations_are_consumed_by_the_frozen_article_authority(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    obligations = validate(closure_document, all_route_ids)
    output_plan, packets = _valid_case()
    for index, unit_id in enumerate(sorted(obligations)):
        entry = output_plan["sections"][index]
        packet = packets[index]
        entry["semantic_unit_ids"] = [unit_id]
        packet["semantic_unit_ids"] = [unit_id]

    ordered = order_and_validate_packets(output_plan, packets)

    consumed_units = frozenset(
        unit_id for packet in ordered for unit_id in packet["semantic_unit_ids"]
    )
    assert obligations <= consumed_units


def test_numeric_suffixes_do_not_make_copied_boilerplate_independent(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(closure_document)
    for ordinal, disposition in enumerate(broken["dispositions"], 1):
        disposition["rationale"] = (
            f"Concept V82-M{ordinal:02d}: independent-review — "
            f"the same template rationale, item {ordinal}!"
        )

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


def test_roman_numeral_suffixes_do_not_make_copied_boilerplate_independent(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(closure_document)
    roman_numerals = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
    for numeral, disposition in zip(roman_numerals, broken["dispositions"], strict=True):
        disposition["rationale"] = (
            "Independent-review — the same template rationale, "
            f"item {numeral}!"
        )

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


@pytest.mark.parametrize(
    ("label", "numerals"),
    (
        (
            "Independent-review",
            ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
        ),
        (
            "Independent-review",
            (
                "\u2160", "\u2161", "\u2162", "\u2163", "\u2164",
                "\u2165", "\u2166", "\u2167", "\u2168",
            ),
        ),
        (
            "Label",
            ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
        ),
    ),
)
def test_any_label_parenthesized_ordinal_does_not_make_copied_boilerplate_independent(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
    label: str,
    numerals: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(closure_document)
    for numeral, disposition in zip(numerals, broken["dispositions"], strict=True):
        disposition["rationale"] = f"{label} ({numeral}): same copied rationale."

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


@pytest.mark.parametrize("delimiter", ("/", "\u3001", "|", "\uff1b"))
def test_standalone_roman_ordinals_are_normalized_across_any_punctuation(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
    delimiter: str,
) -> None:
    broken = copy.deepcopy(closure_document)
    roman_numerals = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
    for numeral, disposition in zip(roman_numerals, broken["dispositions"], strict=True):
        disposition["rationale"] = (
            f"Unknown {numeral}{delimiter} same copied rationale."
        )

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


def test_standalone_roman_ordinals_are_normalized_with_mixed_surrounding_punctuation(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(closure_document)
    roman_numerals = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
    delimiters = ("/", "\u3001", "|", "~")
    for index, (numeral, disposition) in enumerate(
        zip(roman_numerals, broken["dispositions"], strict=True)
    ):
        delimiter = delimiters[index % len(delimiters)]
        disposition["rationale"] = (
            f"Unknown {delimiter}{numeral}{delimiter} same copied rationale."
        )

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


def test_roman_letters_inside_ordinary_words_remain_distinct_reason_text(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    document = copy.deepcopy(closure_document)
    document["dispositions"][0]["rationale"] = (
        "The civic review is independently documented."
    )
    document["dispositions"][1]["rationale"] = (
        "The civil review is independently documented."
    )

    assert validate(document, all_route_ids) == ARTICLE_UNITS


def test_ordinal_normalization_retains_genuinely_different_reason_text(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    document = copy.deepcopy(closure_document)
    document["dispositions"][0]["rationale"] = (
        "Independent-review (I): the source confirms the role."
    )
    document["dispositions"][1]["rationale"] = (
        "Label (II): the source contradicts the role."
    )

    assert validate(document, all_route_ids) == ARTICLE_UNITS


@pytest.mark.parametrize(
    "markers",
    (
        ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix"),
        ("(i)", "(ii)", "(iii)", "(iv)", "(v)", "(vi)", "(vii)", "(viii)", "(ix)"),
        (
            "\u2160", "\u2161", "\u2162", "\u2163", "\u2164",
            "\u2165", "\u2166", "\u2167", "\u2168",
        ),
        ("Item I:", "item II.", "ITEM III)", "No. IV -", "Ordinal V:", "(vi)", "[VII]", "VIII.", "\u7b2cIX\u9879\uff1a"),
    ),
)
def test_ordinal_prefixes_do_not_make_copied_boilerplate_independent(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
    markers: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(closure_document)
    for marker, disposition in zip(markers, broken["dispositions"], strict=True):
        disposition["rationale"] = f"{marker} same copied rationale."

    with pytest.raises(ConceptClosureError, match="boilerplate|independent"):
        validate(broken, all_route_ids)


def test_rationale_normalization_retains_materially_different_reasons(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    document = copy.deepcopy(closure_document)
    document["dispositions"][0]["rationale"] = "(i) The source confirms the role."
    document["dispositions"][1]["rationale"] = "\u2161 The source contradicts the role."

    assert validate(document, all_route_ids) == ARTICLE_UNITS


def test_required_route_subset_is_computed_instead_of_self_reported(
    closure_document: dict[str, object],
    route_map: dict[str, object],
) -> None:
    routes = route_map["routes"]
    assert isinstance(routes, list)
    aggregation_route = routes[0]
    assert aggregation_route["route_id"] == "V82-ROUTE-AGGREGATION"

    subset = copy.deepcopy(closure_document)
    for disposition in subset["dispositions"]:
        disposition["route_required"] = disposition["concept_id"] == "V82-M01"

    assert validate(
        subset,
        ("V82-ROUTE-AGGREGATION",),
    ) == ARTICLE_UNITS


def test_unknown_required_route_is_rejected(
    closure_document: dict[str, object],
) -> None:
    with pytest.raises(ConceptClosureError, match="route"):
        validate(closure_document, ("V82-ROUTE-MISSING",))


@pytest.mark.parametrize("authority", ("registry", "route-map"))
def test_closure_rejects_semantically_plausible_but_unpromoted_authority_bytes(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
    tmp_path: Path,
    authority: str,
) -> None:
    references = (
        tmp_path / "skills" / "crossframe-ultra" / "references"
    )
    registry_target = references / "concept-registry" / REGISTRY_PATH.name
    route_target = references / ROUTE_PATH.name
    registry_target.parent.mkdir(parents=True)
    shutil.copy2(REGISTRY_PATH, registry_target)
    shutil.copy2(ROUTE_PATH, route_target)

    if authority == "registry":
        tampered = load_object(registry_target)
        tampered["concepts"][0]["definition"] = (
            "A plausible but unpromoted replacement definition."
        )
        registry_target.write_text(
            json.dumps(tampered, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        closure_document["registry_sha256"] = hashlib.sha256(
            registry_target.read_bytes()
        ).hexdigest()
    else:
        tampered = load_object(route_target)
        tampered["routes"][0]["task"] = (
            "A plausible but unpromoted replacement route."
        )
        route_target.write_text(
            json.dumps(tampered, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    with pytest.raises(ConceptClosureError, match="promoted|hash|authority"):
        validate_concept_closure(
            closure_document,
            repo=tmp_path,
            required_route_ids=all_route_ids,
        )


def test_closure_validation_does_not_mutate_model_authored_dispositions(
    closure_document: dict[str, object],
    all_route_ids: tuple[str, ...],
) -> None:
    original = copy.deepcopy(closure_document)

    validate(closure_document, all_route_ids)

    assert closure_document == original
