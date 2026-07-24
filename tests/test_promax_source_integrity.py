from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.source_integrity import (
    V8_SOURCE_SNAPSHOT_SHA256,
    load_canonical_read_targets,
    validate_read_event_coverage,
)


RUN_ID = "promax-source-coverage-run"
READ_AT = "2026-07-23T10:00:00Z"


def read_events(targets: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    return [
        {
            "schema_id": "crossframe.promax.v8.read-event",
            "schema_version": 1,
            "event_id": f"read-event-{sequence:06d}",
            "run_id": RUN_ID,
            "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "sequence": sequence,
            "source_kind": target["source_kind"],
            "source_anchor": target["source_anchor"],
            "source_file": target["source_file"],
            "content_sha256": target["content_sha256"],
            "read_at": READ_AT,
        }
        for sequence, target in enumerate(targets, start=1)
    ]


class ProMaxSourceReadCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.targets = load_canonical_read_targets(ROOT)
        cls.events = read_events(cls.targets)

    def validate(self, events: list[dict[str, object]]) -> dict[str, object]:
        return validate_read_event_coverage(
            events,
            repo=ROOT,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )

    def test_canonical_targets_are_exact_full_source_not_marker_counts(self) -> None:
        self.assertEqual(len(self.targets), 3863 + 117)
        paragraph_targets = [
            target for target in self.targets if target["source_kind"] == "paragraph"
        ]
        table_targets = [
            target for target in self.targets if target["source_kind"] == "table"
        ]
        self.assertEqual(len(paragraph_targets), 3863)
        self.assertEqual(len(table_targets), 117)
        self.assertEqual(paragraph_targets[0]["source_anchor"], "V8-P0001")
        self.assertEqual(paragraph_targets[-1]["source_anchor"], "V8-P3863")
        self.assertEqual(table_targets[0]["source_anchor"], "V8-T001")
        self.assertEqual(table_targets[-1]["source_anchor"], "V8-T117")
        self.assertEqual(
            len({target["content_sha256"] for target in self.targets}),
            len(self.targets),
        )

    def test_all_3863_paragraph_and_117_table_events_pass(self) -> None:
        summary = self.validate(copy.deepcopy(self.events))
        self.assertEqual(
            summary,
            {
                "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
                "paragraph_count": 3863,
                "table_count": 117,
                "event_count": 3980,
            },
        )

    def test_missing_duplicate_and_out_of_order_events_fail(self) -> None:
        missing = copy.deepcopy(self.events[:-1])
        duplicate = copy.deepcopy(self.events)
        duplicate[-1] = copy.deepcopy(duplicate[-2])
        reordered = copy.deepcopy(self.events)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        for label, events in (
            ("missing", missing),
            ("duplicate", duplicate),
            ("reordered", reordered),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(events)

    def test_equal_count_forgery_marker_stuffing_and_binding_changes_fail(self) -> None:
        mutations = []

        forged_hash = copy.deepcopy(self.events)
        forged_hash[2000]["content_sha256"] = "a" * 64
        mutations.append(("forged content", forged_hash))

        marker_hash = copy.deepcopy(self.events)
        marker_hash[2000]["content_sha256"] = "8" * 64
        mutations.append(("marker stuffing", marker_hash))

        wrong_file = copy.deepcopy(self.events)
        wrong_file[0]["source_file"] = self.events[-1]["source_file"]
        mutations.append(("wrong source file", wrong_file))

        wrong_run = copy.deepcopy(self.events)
        wrong_run[2000]["run_id"] = "another-run"
        mutations.append(("wrong run", wrong_run))

        wrong_snapshot = copy.deepcopy(self.events)
        wrong_snapshot[2000]["source_snapshot_sha256"] = "f" * 64
        mutations.append(("wrong snapshot", wrong_snapshot))

        for label, events in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.validate(events)


if __name__ == "__main__":
    unittest.main()
