from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.claim_path import validate_claim_path_saturation
from promax_runtime.jsonio import sha256_json
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


RUN_ID = "promax-claim-path-run"
CENTRAL_CLAIM = "CLAIM-CENTRAL"
CONCEPT_ID = "V8-CANON-U01"
STAMP = "2026-07-23T12:00:00Z"
CENTRAL_STATEMENT = "A bounded transfer mechanism best explains the observed structural update."


def graph(mechanism_count: int = 3) -> dict[str, object]:
    mechanism_ids = [f"MECH-{index}" for index in range(1, mechanism_count + 1)]
    semantic_problem_payload = {
        "analysis_object": "the observed structural update",
        "proposition_under_test": CENTRAL_STATEMENT,
        "time_window": "the registered observation horizon",
    }
    problem_payload = {
        **semantic_problem_payload,
        "evidence_cutoff": STAMP,
    }
    return {
        "schema_id": "crossframe.promax.v8.claim-path-graph",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": CENTRAL_CLAIM,
        "stance_neutral_problem": {
            **problem_payload,
            "semantic_key_sha256": sha256_json(semantic_problem_payload),
        },
        "central_claim_cycle": {
            "central_claim_id": CENTRAL_CLAIM,
            "initial_judgment": "The structural mechanism is currently the leading conditional explanation.",
            "strongest_attack": "Selection effects could reproduce the same observations without this mechanism.",
            "revision": "The claim is retained only where temporal ordering and transfer evidence are observed.",
            "counterfactual": "Without the proposed transfer channel, the downstream state should not update.",
            "withdrawal_conditions": [
                "Withdraw if the simple selection baseline explains the same observations out of sample."
            ],
        },
        "claims": [
            {
                "claim_id": CENTRAL_CLAIM,
                "statement": CENTRAL_STATEMENT,
                "claim_type": "mechanistic",
                "evidence_refs": ["EVIDENCE-OBSERVED-01"],
                "concept_ids": [CONCEPT_ID],
                "confidence": "medium",
                "authorization_ceiling": "Diagnostic comparison only; no real-world action is authorized.",
            }
        ],
        "mechanisms": [
            {
                "mechanism_id": mechanism_id,
                "label": f"Competing mechanism {index}",
                "claim_ids": [CENTRAL_CLAIM],
                "distinguishing_conditions": [
                    f"Observable discriminator for mechanism {index}"
                ],
            }
            for index, mechanism_id in enumerate(mechanism_ids, start=1)
        ],
        "path_nodes": [
            {
                "node_id": "NODE-START",
                "label": "Observed starting state",
                "node_type": "state",
                "trigger_conditions": ["The transfer channel becomes active"],
                "early_signals": ["A directional update first appears at the interface"],
                "reverse_signals": ["The update precedes activation of the channel"],
                "stop_conditions": ["The channel is absent or the object boundary changes"],
            },
            {
                "node_id": "NODE-OUTCOME",
                "label": "Conditional downstream outcome",
                "node_type": "outcome",
                "trigger_conditions": ["The branch condition remains satisfied"],
                "early_signals": [],
                "reverse_signals": [],
                "stop_conditions": ["The registered outcome is observed or the horizon ends"],
            },
        ],
        "path_edges": [
            {
                "edge_id": "EDGE-1",
                "from_node_id": "NODE-START",
                "to_node_id": "NODE-OUTCOME",
                "mechanism_ids": mechanism_ids,
                "condition": "The early signal persists and no reverse signal appears.",
                "outcome_writeback": "Write the observed outcome back to the claim confidence and path rank.",
            }
        ],
        "forecast_conditions": ["The object identity criterion remains unchanged"],
        "choice_boundary": "The graph informs diagnosis but does not authorize intervention.",
        "updated_at": STAMP,
    }


class ProMaxClaimPathSaturationTests(unittest.TestCase):
    def validate(
        self,
        document: dict[str, object],
        *,
        minimum_competing_mechanisms: int = 3,
    ) -> dict[str, object]:
        return validate_claim_path_saturation(
            document,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            minimum_competing_mechanisms=minimum_competing_mechanisms,
        )

    def test_three_mechanisms_claim_cycle_and_five_part_path_pass(self) -> None:
        result = self.validate(graph())
        self.assertEqual(result["central_claim_id"], CENTRAL_CLAIM)
        self.assertEqual(len(result["mechanisms"]), 3)

    def test_two_competitors_are_the_absolute_floor_but_three_is_default(self) -> None:
        two = graph(mechanism_count=2)
        with self.assertRaises(ValueError):
            self.validate(copy.deepcopy(two))
        self.assertEqual(
            len(
                self.validate(
                    copy.deepcopy(two), minimum_competing_mechanisms=2
                )["mechanisms"]
            ),
            2,
        )
        with self.assertRaises(ValueError):
            self.validate(graph(mechanism_count=1), minimum_competing_mechanisms=1)

    def test_central_claim_cycle_is_explicit_and_references_one_claim(self) -> None:
        missing = graph()
        missing.pop("central_claim_cycle")

        mismatched = graph()
        mismatched["central_claim_cycle"]["central_claim_id"] = "CLAIM-OTHER"

        duplicated = graph()
        duplicate_claim = copy.deepcopy(duplicated["claims"][0])
        duplicate_claim["statement"] = "A duplicate marker is not a second claim."
        duplicated["claims"].append(duplicate_claim)

        no_evidence = graph()
        no_evidence["claims"][0]["evidence_refs"] = []

        for label, document in (
            ("missing cycle", missing),
            ("mismatched cycle", mismatched),
            ("duplicate claim", duplicated),
            ("no evidence", no_evidence),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_mechanism_and_edge_references_are_closed(self) -> None:
        unknown_claim = graph()
        unknown_claim["mechanisms"][0]["claim_ids"] = ["CLAIM-UNKNOWN"]

        unknown_mechanism = graph()
        unknown_mechanism["path_edges"][0]["mechanism_ids"] = ["MECH-UNKNOWN"]

        unknown_node = graph()
        unknown_node["path_edges"][0]["to_node_id"] = "NODE-UNKNOWN"

        for label, document in (
            ("claim", unknown_claim),
            ("mechanism", unknown_mechanism),
            ("node", unknown_node),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_substantive_branches_need_trigger_early_reverse_stop_and_writeback(self) -> None:
        field_cases = (
            ("trigger_conditions", []),
            ("early_signals", []),
            ("reverse_signals", []),
            ("stop_conditions", []),
        )
        for field, replacement in field_cases:
            document = graph()
            document["path_nodes"][0][field] = replacement
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self.validate(document)

        no_writeback = graph()
        no_writeback["path_edges"][0]["outcome_writeback"] = " "
        with self.assertRaises(ValueError):
            self.validate(no_writeback)

    def test_path_graph_must_be_acyclic(self) -> None:
        cyclic = graph()
        cyclic["path_nodes"][1]["early_signals"] = ["Outcome begins feeding back"]
        cyclic["path_nodes"][1]["reverse_signals"] = ["No feedback is observed"]
        cyclic["path_edges"].append(
            {
                "edge_id": "EDGE-2",
                "from_node_id": "NODE-OUTCOME",
                "to_node_id": "NODE-START",
                "mechanism_ids": ["MECH-1"],
                "condition": "The outcome feeds back into the starting state.",
                "outcome_writeback": "Register the feedback as a new event before rerunning the graph.",
            }
        )
        with self.assertRaises(ValueError):
            self.validate(cyclic)


if __name__ == "__main__":
    unittest.main()
