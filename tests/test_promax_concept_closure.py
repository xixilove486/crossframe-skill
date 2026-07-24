from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
REFERENCES = ROOT / "skills/crossframe-promax/references"
REGISTRY_PATH = REFERENCES / "concept-registry/v8-concept-registry.json"
ROUTE_PATH = REFERENCES / "v8-route-map.json"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.concept_closure import validate_concept_closure
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


RUN_ID = "promax-concept-closure-run"
STAMP = "2026-07-23T11:00:00Z"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def unique_strings(*groups: object) -> list[str]:
    values: list[str] = []
    for group in groups:
        assert isinstance(group, list)
        for item in group:
            assert isinstance(item, str)
            if item not in values:
                values.append(item)
    return values


def closure_document(
    registry: dict[str, object],
    route_id: str,
) -> dict[str, object]:
    concepts = registry["concepts"]
    assert isinstance(concepts, list)
    dispositions = []
    for concept in concepts:
        assert isinstance(concept, dict)
        dispositions.append(
            {
                "concept_id": concept["concept_id"],
                "status": "not_applicable",
                "rationale": "Checked against the authoritative v8 definition and excluded for this object.",
                "evidence_refs": [],
                "required_neighbor_ids": list(concept["required_neighbor_ids"]),
                "misuses_excluded": unique_strings(
                    concept["common_misuses"],
                    concept["forbidden_substitutions_or_generalizations"],
                ),
                "output_section_ids": [],
                "pending_evidence": [],
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.concept-disposition",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "registry_sha256": hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest(),
        "route_ids": [route_id],
        "dispositions": dispositions,
        "unchecked_concept_ids": [],
        "closure_complete": True,
        "completed_at": STAMP,
    }


class ProMaxConceptClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.routes = load_json(ROUTE_PATH)
        routes = cls.routes["routes"]
        assert isinstance(routes, list) and isinstance(routes[0], dict)
        cls.route_id = routes[0]["route_id"]
        assert isinstance(cls.route_id, str)
        cls.valid = closure_document(cls.registry, cls.route_id)

    def validate(self, document: dict[str, object]) -> dict[str, object]:
        return validate_concept_closure(
            document,
            repo=ROOT,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            required_route_ids=(self.route_id,),
        )

    def test_all_709_terminal_dispositions_and_route_neighbor_closure_pass(self) -> None:
        result = self.validate(copy.deepcopy(self.valid))
        self.assertEqual(len(result["dispositions"]), 709)
        self.assertTrue(result["closure_complete"])

    def test_missing_duplicate_or_nonterminal_inventory_fails(self) -> None:
        missing = copy.deepcopy(self.valid)
        missing["dispositions"].pop()

        duplicate = copy.deepcopy(self.valid)
        extra = copy.deepcopy(duplicate["dispositions"][0])
        extra["rationale"] = "A different marker cannot make a duplicate terminal."
        duplicate["dispositions"].append(extra)

        incomplete = copy.deepcopy(self.valid)
        incomplete["closure_complete"] = False
        incomplete["unchecked_concept_ids"] = [
            incomplete["dispositions"][0]["concept_id"]
        ]

        for label, document in (
            ("missing", missing),
            ("duplicate", duplicate),
            ("incomplete", incomplete),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_registry_neighbors_and_misuse_exclusions_are_not_self_reported(self) -> None:
        wrong_neighbor = copy.deepcopy(self.valid)
        disposition = next(
            item
            for item in wrong_neighbor["dispositions"]
            if item["required_neighbor_ids"]
        )
        disposition["required_neighbor_ids"] = []

        wrong_misuse = copy.deepcopy(self.valid)
        disposition = next(
            item for item in wrong_misuse["dispositions"] if item["misuses_excluded"]
        )
        disposition["misuses_excluded"] = []

        for label, document in (
            ("neighbor", wrong_neighbor),
            ("misuse", wrong_misuse),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_required_routes_and_exact_registry_hash_are_bound(self) -> None:
        missing_route = copy.deepcopy(self.valid)
        routes = self.routes["routes"]
        assert isinstance(routes, list) and isinstance(routes[1], dict)
        missing_route["route_ids"] = [routes[1]["route_id"]]

        wrong_hash = copy.deepcopy(self.valid)
        wrong_hash["registry_sha256"] = "a" * 64

        for label, document in (
            ("route", missing_route),
            ("hash", wrong_hash),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)


if __name__ == "__main__":
    unittest.main()
