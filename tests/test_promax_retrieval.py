from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.retrieval import (
    RETRIEVAL_DIRECTIONS,
    validate_retrieval_saturation,
)
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


RUN_ID = "promax-retrieval-run"
CENTRAL_CLAIM = "CLAIM-CENTRAL"
STAMP = "2026-07-23T13:00:00Z"
RELATIONS = {
    "support": "supports",
    "reverse": "refutes",
    "failure": "refutes",
    "alternative_mechanism": "alternative_mechanism",
    "affected_or_low_power": "affected_position",
}


def source(index: int) -> dict[str, object]:
    return {
        "url": f"https://evidence.example/source-{index}",
        "title": f"Source {index}",
        "publisher": f"Publisher {index}",
        "published_at": "2026-07-20",
        "event_date": "2026-07-19",
        "source_type": "primary",
        "interest_relevance": "The publisher's institutional role is recorded for source evaluation.",
        "independence_group": f"origin-{index}",
        "duplicate_relation": "independent",
        "duplicate_of_url": None,
    }


def ledger(*, network_available: bool = True) -> dict[str, object]:
    entries = []
    for index, direction in enumerate(RETRIEVAL_DIRECTIONS, start=1):
        entries.append(
            {
                "retrieval_id": f"RETRIEVAL-{index}",
                "round": 1 if index <= 3 else 2,
                "direction": direction,
                "claim_relation": RELATIONS[direction],
                "query": f"Independent query for {direction}",
                "tool": "verified-web-retrieval",
                "retrieved_at": STAMP,
                "sources": [source(index)] if network_available else [],
                "claim_ids": [CENTRAL_CLAIM],
                "finding": f"Structured finding for {direction}",
                "cannot_prove": [
                    "This query alone cannot prove the full mechanism or authorize action."
                ],
                "stop_reason": "The query frontier was exhausted for this registered direction.",
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.retrieval-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "entries": entries,
        "saturation_rounds": [
            {
                "round": 1,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "No claim, concept state, path rank, or action ceiling changed.",
            },
            {
                "round": 2,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "A second consecutive round produced no substantive change.",
            },
        ],
        "network_available": network_available,
        "completed_at": STAMP,
    }


class ProMaxRetrievalSaturationTests(unittest.TestCase):
    def validate(
        self,
        document: dict[str, object],
        *,
        strict_completion: bool = True,
    ) -> dict[str, object]:
        return validate_retrieval_saturation(
            document,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            required_claim_ids=(CENTRAL_CLAIM,),
            strict_completion=strict_completion,
        )

    def test_five_directions_full_fields_and_two_zero_novelty_rounds_pass(self) -> None:
        result = self.validate(ledger())
        self.assertEqual(
            {entry["direction"] for entry in result["entries"]},
            set(RETRIEVAL_DIRECTIONS),
        )
        self.assertEqual(len(result["saturation_rounds"]), 2)

    def test_each_required_claim_needs_all_five_directions_and_stop_reasons(self) -> None:
        missing_direction = ledger()
        missing_direction["entries"].pop()

        wrong_claim = ledger()
        wrong_claim["entries"][0]["claim_ids"] = ["CLAIM-OTHER"]

        missing_stop = ledger()
        missing_stop["entries"][0].pop("stop_reason")

        for label, document in (
            ("direction", missing_direction),
            ("claim", wrong_claim),
            ("stop", missing_stop),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_direction_to_claim_relation_is_explicit_not_inferred_from_text(self) -> None:
        cases = (
            ("support", "refutes"),
            ("reverse", "supports"),
            ("failure", "supports"),
            ("alternative_mechanism", "contextual"),
            ("affected_or_low_power", "supports"),
        )
        for direction, relation in cases:
            document = ledger()
            entry = next(
                item for item in document["entries"] if item["direction"] == direction
            )
            entry["claim_relation"] = relation
            entry["finding"] = "supports refutes alternative affected " * 100
            with self.subTest(direction=direction, relation=relation):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_legacy_direction_spellings_are_rejected(self) -> None:
        for legacy in ("failure_case", "affected_or_low_power_position"):
            document = ledger()
            document["entries"][0]["direction"] = legacy
            with self.subTest(legacy=legacy):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_duplicate_and_independence_relations_are_structural(self) -> None:
        duplicate_url = ledger()
        copied = copy.deepcopy(duplicate_url["entries"][0]["sources"][0])
        copied["title"] = "Same URL presented as another source"
        copied["independence_group"] = "forged-independent-origin"
        duplicate_url["entries"][1]["sources"].append(copied)

        missing_target = ledger()
        related = missing_target["entries"][1]["sources"][0]
        related["duplicate_relation"] = "derived"
        related["duplicate_of_url"] = "https://evidence.example/not-in-ledger"

        self_target = ledger()
        related = self_target["entries"][1]["sources"][0]
        related["duplicate_relation"] = "duplicate"
        related["duplicate_of_url"] = related["url"]

        for label, document in (
            ("duplicate URL", duplicate_url),
            ("missing target", missing_target),
            ("self target", self_target),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_network_unavailability_is_incomplete_not_silent_completion(self) -> None:
        unavailable = ledger(network_available=False)
        with self.assertRaises(ValueError):
            self.validate(copy.deepcopy(unavailable), strict_completion=True)
        self.assertFalse(
            self.validate(
                copy.deepcopy(unavailable), strict_completion=False
            )["network_available"]
        )

    def test_network_sources_must_be_real_http_urls_and_nonempty(self) -> None:
        no_source = ledger()
        no_source["entries"][0]["sources"] = []

        unsupported = ledger()
        unsupported["entries"][0]["sources"][0]["url"] = "urn:example:source"

        for label, document in (("missing", no_source), ("scheme", unsupported)):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_saturation_requires_two_consecutive_zero_change_final_rounds(self) -> None:
        one_round = ledger()
        one_round["saturation_rounds"] = one_round["saturation_rounds"][:1]

        novelty = ledger()
        novelty["saturation_rounds"][-1]["substantive_novelty"] = True

        changed_claim = ledger()
        changed_claim["saturation_rounds"][-1]["changed_claim_ids"] = [CENTRAL_CLAIM]

        nonsequential = ledger()
        nonsequential["saturation_rounds"][-1]["round"] = 3

        for label, document in (
            ("one round", one_round),
            ("novelty", novelty),
            ("changed claim", changed_claim),
            ("nonsequential", nonsequential),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(document)

    def test_every_saturation_round_is_backed_by_real_queries(self) -> None:
        missing_round_reference = ledger()
        missing_round_reference["entries"][0]["round"] = 3
        with self.assertRaises(ValueError):
            self.validate(missing_round_reference)

        self_reported_empty_round = ledger()
        for entry in self_reported_empty_round["entries"]:
            entry["round"] = 1
        with self.assertRaises(ValueError):
            self.validate(self_reported_empty_round)


if __name__ == "__main__":
    unittest.main()
