from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(CANONICAL_SCRIPTS))

import crossframe_promax_fixture_factory as fixture_factory
from promax_runtime.source_integrity import (
    V8_SOURCE_SNAPSHOT_SHA256,
    validate_read_event_coverage,
)
from promax_runtime.concept_closure import validate_concept_closure
from promax_runtime.claim_path import validate_claim_path_saturation
from promax_runtime.deliverables import (
    validate_prose_review,
    validate_v2_reader_documents,
)
from promax_runtime.jsonio import sha256_json
from promax_runtime.retrieval import validate_retrieval_saturation
from promax_runtime.schemas import validate_instance
from promax_runtime.position import (
    validate_position_semantics,
    validate_recommendation_semantics,
)


REQUIRED_SCENARIOS = {
    "valid-complete",
    "artifact-incomplete",
    "marker-stuffing",
    "empty-strings",
    "forged-read-coverage",
    "equal-count-source-mutation",
    "unsupported-url",
    "duplicate-sources-independent",
    "missing-reverse",
    "no-action-omitted",
    "stance-flip",
    "authorization-leakage",
    "untyped-examples",
    "phase-replay",
    "stale-manifest",
    "wrong-continuation-parent",
}


class ProMaxFixtureFactoryTests(unittest.TestCase):
    def test_read_event_factory_materializes_exact_full_source_proof(self) -> None:
        events = fixture_factory.build_read_events(
            ROOT,
            run_id="promax-fixture-factory-test",
            read_at="2026-07-23T14:00:00Z",
        )
        self.assertEqual(len(events), 3980)
        self.assertEqual(events[0]["source_anchor"], "V8-P0001")
        self.assertEqual(events[-1]["source_anchor"], "V8-T117")
        summary = validate_read_event_coverage(
            events,
            repo=ROOT,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(summary["paragraph_count"], 3863)
        self.assertEqual(summary["table_count"], 117)

    def test_concept_factory_materializes_all_709_terminal_dispositions(self) -> None:
        document = fixture_factory.build_concept_disposition(
            ROOT,
            run_id="promax-fixture-factory-test",
            completed_at="2026-07-23T14:30:00Z",
        )
        self.assertEqual(len(document["dispositions"]), 709)
        result = validate_concept_closure(
            document,
            repo=ROOT,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            required_route_ids=tuple(document["route_ids"]),
        )
        self.assertTrue(result["closure_complete"])
        self.assertEqual(result["unchecked_concept_ids"], [])

    def test_claim_path_factory_materializes_a_three_mechanism_closed_dag(self) -> None:
        document = fixture_factory.build_claim_path_graph(
            run_id="promax-fixture-factory-test",
            updated_at="2026-07-23T15:00:00Z",
        )
        result = validate_claim_path_saturation(
            document,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(len(result["mechanisms"]), 3)
        self.assertEqual(
            result["central_claim_cycle"]["central_claim_id"],
            result["central_claim_id"],
        )
        central_claim = next(
            claim
            for claim in result["claims"]
            if claim["claim_id"] == result["central_claim_id"]
        )
        problem = result["stance_neutral_problem"]
        self.assertEqual(
            problem["proposition_under_test"],
            central_claim["statement"],
        )
        self.assertEqual(
            problem["semantic_key_sha256"],
            sha256_json(
                {
                    "analysis_object": problem["analysis_object"],
                    "proposition_under_test": problem["proposition_under_test"],
                    "time_window": problem["time_window"],
                }
            ),
        )

    def test_retrieval_factory_materializes_five_directions_and_two_real_rounds(self) -> None:
        document = fixture_factory.build_retrieval_ledger(
            run_id="promax-fixture-factory-test",
            completed_at="2026-07-23T15:30:00Z",
        )
        result = validate_retrieval_saturation(
            document,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            required_claim_ids=("CLAIM-CENTRAL",),
        )
        self.assertEqual(len(result["entries"]), 5)
        self.assertEqual({entry["round"] for entry in result["entries"]}, {1, 2})

    def test_local_world_factory_emits_the_complete_p3_contract(self) -> None:
        document = fixture_factory.build_local_world_model(
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T16:00:00Z",
        )
        validate_instance("promax-local-world-model.schema.json", document)
        self.assertEqual(document["phase_id"], "P3")
        self.assertTrue(document["action_limits"])
        self.assertTrue(document["authorization_limits"])

    def test_judgment_factory_locks_attack_position_and_six_way_recommendation(self) -> None:
        graph = fixture_factory.build_claim_path_graph(
            run_id="promax-fixture-factory-test",
            updated_at="2026-07-23T16:00:00Z",
        )
        red_team = fixture_factory.build_red_team_report(
            run_id="promax-fixture-factory-test",
            completed_at="2026-07-23T16:30:00Z",
        )
        position = fixture_factory.build_position_lock(
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T17:00:00Z",
        )
        validated_position = validate_position_semantics(
            position,
            red_team_report=red_team,
            claim_path_graph=graph,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        recommendation = fixture_factory.build_recommendation_lock(
            validated_position,
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T17:30:00Z",
        )
        validated = validate_recommendation_semantics(
            {
                "run_id": "promax-fixture-factory-test",
                "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
                "recommendation_required": True,
            },
            recommendation,
            position=validated_position,
            expected_run_id="promax-fixture-factory-test",
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(len(validated["options"]), 6)
        self.assertEqual(validated["preferred_option_id"], validated["ranking"][0])
        expected_ids = [
            "OPTION-PROBE",
            "OPTION-ACTIVE",
            "OPTION-STATUS-QUO",
            "OPTION-DELAYED",
            "OPTION-EXIT",
            "OPTION-NO-ACTION",
        ]
        expected_kinds = [
            "probe_action",
            "active_action",
            "maintain_status_quo",
            "delayed_action",
            "exit_or_transfer",
            "no_action",
        ]
        self.assertEqual(validated_position["relation_to_proposition"], "supports")
        self.assertEqual(validated["ranking"], expected_ids)
        self.assertEqual(validated["option_kind_ranking"], expected_kinds)
        self.assertEqual(
            validated["option_semantic_ranking"],
            [
                sha256_json(
                    {
                        key: value
                        for key, value in option.items()
                        if key != "option_id"
                    }
                )
                for option in validated["options"]
            ],
        )
        stability = red_team["stability_checks"][0]
        problem = graph["stance_neutral_problem"]
        central_statement = graph["claims"][0]["statement"]
        self.assertEqual(
            stability["semantic_problem_sha256_before"],
            problem["semantic_key_sha256"],
        )
        self.assertEqual(
            stability["semantic_problem_sha256_after"],
            problem["semantic_key_sha256"],
        )
        self.assertEqual(
            stability["central_statement_sha256_before"],
            sha256_json(central_statement),
        )
        self.assertEqual(stability["relation_to_proposition_after"], "supports")
        self.assertEqual(stability["option_kind_ranking_after"], expected_kinds)
        self.assertEqual(
            stability["option_semantic_ranking_after"],
            validated["option_semantic_ranking"],
        )

    def test_stance_flip_fixture_is_schema_valid_before_semantic_rejection(self) -> None:
        run_id = "promax-fixture-stance-flip-unit"
        graph = fixture_factory.build_claim_path_graph(
            run_id=run_id,
            updated_at="2026-07-23T16:00:00Z",
        )
        red_team = fixture_factory.build_red_team_report(
            run_id=run_id,
            completed_at="2026-07-23T16:30:00Z",
        )
        position = fixture_factory.build_position_lock(
            run_id=run_id,
            locked_at="2026-07-23T17:00:00Z",
        )
        recommendation = fixture_factory.build_recommendation_lock(
            position,
            run_id=run_id,
            locked_at="2026-07-23T17:30:00Z",
        )

        fixture_factory._apply_pre_manifest_mutation(
            "record_position_drift_without_new_evidence",
            source_snapshot={},
            read_events=[],
            claim_graph=graph,
            retrieval={},
            red_team=red_team,
            position=position,
            recommendation=recommendation,
            deliverables={},
        )

        validate_instance("promax-red-team-report.schema.json", red_team)
        with self.assertRaisesRegex(ValueError, "after-relation"):
            validate_position_semantics(
                position,
                red_team_report=red_team,
                claim_path_graph=graph,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )

    def test_output_factory_traces_every_major_mechanism_and_applied_concept(self) -> None:
        plan = fixture_factory.build_output_plan(
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T18:00:00Z",
        )
        validate_instance("promax-output-plan.schema.json", plan)
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(
            plan["reader_projection"]["core_concept_ids"],
            [fixture_factory.FIXTURE_CONCEPT_ID],
        )
        self.assertEqual(
            sum(
                technique["tier"] == "core"
                for technique in plan["reader_projection"]["selected_techniques"]
            ),
            3,
        )
        self.assertEqual(
            plan["reader_projection"]["article_type"],
            "public-commentary",
        )
        self.assertEqual(
            [
                technique["technique_id"]
                for technique in plan["reader_projection"]["selected_techniques"]
            ],
            [
                "event-association",
                "layered-argument",
                "positive-negative-contrast",
            ],
        )
        section = plan["sections"][0]
        self.assertEqual(
            section["concept_ids"],
            [fixture_factory.FIXTURE_CONCEPT_ID],
        )
        self.assertEqual(
            set(section["example_ids"]),
            {
                "EX-M1-S1",
                "EX-M1-S2",
                "EX-M2-S1",
                "EX-M2-S2",
                "EX-M3-S1",
                "EX-M3-S2",
            },
        )
        self.assertEqual(
            set(section["counterexample_ids"]),
            {"EX-M1-F1", "EX-M2-F1", "EX-M3-F1"},
        )

        position = fixture_factory.build_position_lock(
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T17:40:00Z",
        )
        recommendation = fixture_factory.build_recommendation_lock(
            position,
            run_id="promax-fixture-factory-test",
            locked_at="2026-07-23T17:50:00Z",
        )
        deliverables = fixture_factory.build_deliverables(
            ROOT,
            position=position,
            recommendation=recommendation,
        )
        self.assertEqual(
            set(deliverables),
            {
                "promax-dossier.md",
                "promax-concept-atlas.md",
                "promax-case-and-countercase.md",
                "promax-essay.md",
            },
        )
        atlas = deliverables["promax-concept-atlas.md"]
        self.assertIn("V8-CANON-ACTOR-STATE", atlas)
        self.assertIn("A* 行动者候选状态", atlas)
        self.assertIn("行动者 ID", atlas)
        cases = deliverables["promax-case-and-countercase.md"]
        for mechanism in ("MECH-1", "MECH-2", "MECH-3"):
            self.assertEqual(cases.count(f"mechanism={mechanism} | relation=similar"), 2)
            self.assertEqual(cases.count(f"mechanism={mechanism} | relation=failure"), 1)

        locked_ranking = [
            "OPTION-PROBE",
            "OPTION-ACTIVE",
            "OPTION-STATUS-QUO",
            "OPTION-DELAYED",
            "OPTION-EXIT",
            "OPTION-NO-ACTION",
        ]
        dossier = deliverables["promax-dossier.md"]
        first_appearances = [dossier.index(option_id) for option_id in locked_ranking]
        self.assertEqual(first_appearances, sorted(first_appearances))
        essay = deliverables["promax-essay.md"]
        for machine_prefix in ("V8-CANON", "CLAIM-", "OPTION-"):
            self.assertNotIn(machine_prefix, essay)
        self.assertIn("bounded transfer mechanism", essay)

        disposition = fixture_factory.build_concept_disposition(
            ROOT,
            run_id="promax-fixture-factory-test",
            completed_at="2026-07-23T17:30:00Z",
            applied_concept_ids=(fixture_factory.FIXTURE_CONCEPT_ID,),
        )
        registry = json.loads(
            (
                ROOT
                / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
            ).read_text(encoding="utf-8")
        )
        validate_v2_reader_documents(
            reader_projection=plan["reader_projection"],
            concept_registry=registry,
            dispositions=disposition["dispositions"],
            atlas=deliverables["promax-concept-atlas.md"],
            essay=essay,
            dossier=dossier,
            position=position,
            recommendation=recommendation,
            recommendation_required=True,
        )
        review = fixture_factory.build_prose_review(
            run_id="promax-fixture-factory-test",
            reviewed_at="2026-07-23T18:10:00Z",
            essay=essay,
            position=position,
            output_plan=plan,
        )
        validate_instance("promax-prose-review.schema.json", review)
        validate_prose_review(
            review,
            essay=essay,
            position=position,
            output_plan=plan,
            run_id="promax-fixture-factory-test",
            source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(len(review["dimensions"]), 11)
        dimension_excerpts = [
            excerpt
            for dimension in review["dimensions"].values()
            for excerpt in dimension["evidence_excerpts"]
        ]
        self.assertGreaterEqual(len(set(dimension_excerpts)), 8)
        self.assertLessEqual(
            max(dimension_excerpts.count(excerpt) for excerpt in dimension_excerpts),
            2,
        )

    def test_adversarial_review_keeps_beat_excerpts_bounded_and_unique(self) -> None:
        run_id = "promax-fixture-marker-stuffing"
        position = fixture_factory.build_position_lock(
            run_id=run_id,
            locked_at="2026-07-23T17:40:00Z",
        )
        plan = fixture_factory.build_output_plan(
            run_id=run_id,
            locked_at="2026-07-23T18:00:00Z",
        )
        essay = (
            "# IDs only\n"
            + " V8-CANON-U01 CLAIM-CENTRAL MECH-1 MECH-2 MECH-3" * 120
        )

        review = fixture_factory.build_prose_review(
            run_id=run_id,
            reviewed_at="2026-07-23T18:10:00Z",
            essay=essay,
            position=position,
            output_plan=plan,
        )

        self.assertEqual(review["overall_status"], "fail")
        for mapping in review["required_beat_mappings"]:
            for excerpt in mapping["evidence_excerpts"]:
                self.assertGreaterEqual(len(excerpt), 8)
                self.assertLessEqual(len(excerpt), 240)
                self.assertEqual(essay.count(excerpt), 1)

    def test_catalog_is_closed_complete_and_has_all_fixture_classes(self) -> None:
        catalog = fixture_factory.load_scenario_catalog(ROOT)
        self.assertEqual(catalog["schema_version"], 1)
        scenarios = catalog["scenarios"]
        self.assertEqual(
            {scenario["scenario_id"] for scenario in scenarios},
            REQUIRED_SCENARIOS,
        )
        self.assertEqual(
            {scenario["fixture_class"] for scenario in scenarios},
            {"positive", "incomplete", "adversarial"},
        )
        for scenario in scenarios:
            self.assertEqual(
                set(scenario),
                {
                    "scenario_id",
                    "fixture_class",
                    "mutation",
                    (
                        "expected_outcome"
                        if scenario["fixture_class"] != "adversarial"
                        else "expected_error_type"
                    ),
                },
            )

    def test_new_fixture_workspace_materializes_v2_internal_prose_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "valid-complete"
            fixture_factory.materialize_fixture(
                ROOT,
                scenario_id="valid-complete",
                output=workspace,
            )

            contract = json.loads(
                (workspace / "promax-run-contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["schema_version"], 2)
            self.assertEqual(len(contract["role_plan"]), 6)
            self.assertIn("prose", contract["capabilities"]["validators"]["validator_ids"])

            plan = json.loads(
                (workspace / "promax-output-plan.locked.json").read_text(
                    encoding="utf-8"
                )
            )
            review = json.loads(
                (workspace / "promax-prose-review.json").read_text(encoding="utf-8")
            )
            self.assertEqual(plan["schema_version"], 2)
            validate_instance("promax-prose-review.schema.json", review)

            events = [
                json.loads(line)
                for line in (workspace / "promax-phase-events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            p10 = next(event for event in events if event["phase_id"] == "P10")
            self.assertIn(
                "promax-prose-review.json",
                p10["output_artifact_hashes"],
            )

            manifest = json.loads(
                (workspace / "promax-artifact-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            artifacts = {
                item["path"]: item for item in manifest["artifacts"]
            }
            self.assertIn("promax-prose-review.json", artifacts)
            review_record = manifest["role_records"][-1]
            self.assertEqual(review_record["role_id"], "prose_fidelity_auditor")
            self.assertEqual(
                [item["path"] for item in review_record["input_artifacts"]],
                [
                    "promax-essay.md",
                    "promax-position.locked.json",
                    "promax-output-plan.locked.json",
                ],
            )
            self.assertEqual(
                review_record["observed_input_artifacts"],
                review_record["input_artifacts"],
            )
            self.assertEqual(
                [item["path"] for item in review_record["output_artifacts"]],
                ["promax-prose-review.json"],
            )
            self.assertEqual(
                set(artifacts["promax-prose-review.json"]["input_artifact_sha256s"]),
                {
                    artifacts["promax-essay.md"]["sha256"],
                    artifacts["promax-position.locked.json"]["sha256"],
                    artifacts["promax-output-plan.locked.json"]["sha256"],
                },
            )

            final_chat = json.loads(
                (workspace / "promax-final-chat.json").read_text(encoding="utf-8")
            )
            self.assertNotIn(
                "promax-prose-review.json",
                final_chat["artifact_links"],
            )

    def test_list_cli_reports_the_canonical_catalog_and_root_entry_is_thin(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            exit_code = fixture_factory.main(["list", "--repo", str(ROOT)])
        self.assertEqual(exit_code, 0)
        status = json.loads(output.getvalue())
        self.assertEqual(status["status"], "ok")
        self.assertEqual(set(status["scenario_ids"]), REQUIRED_SCENARIOS)

        root_entry = ROOT / "scripts/crossframe_promax_fixture_factory.py"
        text = root_entry.read_text(encoding="utf-8")
        self.assertIn("runpy.run_path", text)
        self.assertNotIn("ArgumentParser", text)
        self.assertLess(len(text), 2000)


if __name__ == "__main__":
    unittest.main()
