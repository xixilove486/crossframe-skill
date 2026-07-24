from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

import check_crossframe_promax_artifacts as checker
import crossframe_promax_fixture_factory as fixture_factory


MACHINE_FAILURE_FIELDS = {
    "error_type",
    "artifact",
    "affected_phase",
    "downstream_reset",
    "repair_action",
}


class ProMaxCheckerContractTests(unittest.TestCase):
    def test_production_checker_rejects_test_fixture_provenance_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "fixture"
            fixture_factory.materialize_fixture(
                ROOT,
                scenario_id="valid-complete",
                output=workspace,
            )

            production = checker.validate_workspace(
                workspace,
                repo=ROOT,
                final_chat=True,
            )
            self.assertEqual(production["overall_status"], "fail")
            self.assertEqual(
                production["failures"][0]["error_type"],
                "test_fixture_provenance_forbidden",
            )
            self.assertIsNone(production["final_chat_projection"])

            internal_test = checker.validate_workspace(
                workspace,
                repo=ROOT,
                final_chat=True,
                allow_test_fixture=True,
            )
            self.assertEqual(internal_test["overall_status"], "pass")
            self.assertEqual(internal_test["completion_status"], "promax-complete")
            expected_projection = json.loads(
                (workspace / checker.FINAL_CHAT_ARTIFACT).read_text(encoding="utf-8")
            )
            self.assertEqual(
                internal_test["final_chat_projection"],
                expected_projection,
            )

    def test_cli_requires_final_chat_and_exposes_no_fixture_bypass(self) -> None:
        parser = checker._parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["--workspace", "run", "--repo", "repo"])

        args = parser.parse_args(
            ["--workspace", "run", "--repo", "repo", "--final-chat"]
        )
        self.assertIs(args.final_chat, True)
        self.assertNotIn("--allow-test-fixture", parser.format_help())

    def test_checker_uses_only_the_fixed_safe_artifact_inventory(self) -> None:
        self.assertEqual(
            checker.JSON_ARTIFACTS["run_contract"],
            "promax-run-contract.json",
        )
        self.assertEqual(
            checker.TEXT_ARTIFACTS,
            {
                "worldview_capsule": "promax-worldview-capsule.locked.md",
                "dossier": "promax-dossier.md",
                "concept_atlas": "promax-concept-atlas.md",
                "case_and_countercase": "promax-case-and-countercase.md",
                "essay": "promax-essay.md",
                "continuation_index": "promax-continuation-index.md",
            },
        )
        all_names = set(checker.JSON_ARTIFACTS.values()) | set(
            checker.JSONL_ARTIFACTS.values()
        ) | set(checker.TEXT_ARTIFACTS.values())
        self.assertNotIn("promax-validator-report.json", all_names)
        self.assertTrue(all("/" not in name and "\\" not in name for name in all_names))

    def test_every_failure_has_exactly_the_five_machine_fields(self) -> None:
        failure = checker.machine_failure(
            error_type="schema_validation_failed",
            artifact="promax-position.locked.json",
            affected_phase="P8",
            repair_action="rebuild_position_and_revalidate",
        )
        self.assertEqual(set(failure), MACHINE_FAILURE_FIELDS)
        self.assertEqual(failure["downstream_reset"], ["P8", "P9", "P10", "P11"])

    def test_complete_mode_never_passes_or_blocks_when_a_hard_gate_fails(self) -> None:
        outcome = checker.classify_outcome(
            "promax-complete",
            failures=[
                checker.machine_failure(
                    error_type="manifest_stale",
                    artifact="promax-artifact-manifest.json",
                    affected_phase="P10",
                    repair_action="regenerate_manifest_and_revalidate",
                )
            ],
            capability_gaps=[],
        )
        self.assertEqual(outcome["overall_status"], "fail")
        self.assertEqual(
            outcome["completion_status"],
            "promax-artifact-incomplete:validation-failed",
        )

    def test_only_a_genuine_artifact_run_capability_gap_becomes_incomplete(self) -> None:
        outcome = checker.classify_outcome(
            "promax-artifact-run",
            failures=[],
            capability_gaps=["network-unavailable"],
        )
        self.assertEqual(outcome["overall_status"], "blocked")
        self.assertEqual(
            outcome["completion_status"],
            "promax-artifact-incomplete:network-unavailable",
        )

        strict = checker.classify_outcome(
            "promax-complete",
            failures=[],
            capability_gaps=["network-unavailable"],
        )
        self.assertEqual(strict["overall_status"], "fail")
        self.assertEqual(
            strict["completion_status"],
            "promax-artifact-incomplete:capability-gap",
        )

    def test_schema_or_tamper_failure_can_never_be_reported_as_normal_incomplete(self) -> None:
        for error_type in (
            "schema_validation_failed",
            "manifest_stale",
            "phase_history_replay",
        ):
            outcome = checker.classify_outcome(
                "promax-artifact-run",
                failures=[
                    checker.machine_failure(
                        error_type=error_type,
                        artifact="promax-artifact-manifest.json",
                        affected_phase="P10",
                        repair_action="repair_and_revalidate",
                    )
                ],
                capability_gaps=["network-unavailable"],
            )
            with self.subTest(error_type=error_type):
                self.assertEqual(outcome["overall_status"], "fail")
                self.assertEqual(
                    outcome["completion_status"],
                    "promax-artifact-incomplete:validation-failed",
                )

    def test_domain_complaints_map_to_the_fixture_contract_error_types(self) -> None:
        cases = (
            ("retrieval", "required claim lacks retrieval directions", "retrieval_direction_missing"),
            ("retrieval", "duplicate source URL cannot be independent", "source_independence_invalid"),
            ("position", "stability check records unjustified position drift", "stance_stability_failed"),
            ("position", "action ceiling violates authorization", "authorization_ceiling_exceeded"),
            ("output", "essay does not explain the v8 definition", "semantic_content_missing"),
            ("output", "case EX-1 has an unsupported type", "mechanism_example_coverage_invalid"),
            ("output", "case heading is malformed", "mechanism_example_coverage_invalid"),
            ("output", "continuation ledger has a stale parent manifest", "continuation_parent_mismatch"),
        )
        for gate, message, expected in cases:
            with self.subTest(gate=gate, message=message):
                error_type, _ = checker._semantic_error_type(gate, ValueError(message))
                self.assertEqual(error_type, expected)

    def test_schema_failures_win_same_phase_and_same_origin_is_not_independent(self) -> None:
        self.assertEqual(
            checker._schema_error_type(
                "retrieval_ledger", ValueError("entries is too short")
            ),
            "retrieval_direction_missing",
        )
        self.assertEqual(
            checker._schema_error_type(
                "retrieval_ledger", ValueError("URL is not a uri")
            ),
            "schema_validation_failed",
        )
        failures = [
            checker.machine_failure(
                error_type="claim_path_incomplete",
                artifact="promax-claim-path-graph.json",
                affected_phase="P5",
                repair_action="repair_claim",
            ),
            checker.machine_failure(
                error_type="schema_validation_failed",
                artifact="promax-claim-path-graph.json",
                affected_phase="P5",
                repair_action="repair_schema",
            ),
        ]
        self.assertEqual(
            checker._ordered_failures(failures)[0]["error_type"],
            "schema_validation_failed",
        )

        ledger = {
            "entries": [
                {
                    "sources": [
                        {
                            "url": "https://example.test/a",
                            "publisher": "Publisher",
                            "duplicate_relation": "independent",
                        },
                        {
                            "url": "https://example.test/b",
                            "publisher": "Publisher",
                            "duplicate_relation": "independent",
                        },
                    ]
                }
            ]
        }
        with self.assertRaises(ValueError):
            checker._validate_source_independence(ledger)

    def test_stance_probe_hashes_are_recomputed_from_prompts_and_actual_evidence_artifacts(self) -> None:
        run_contract = {
            "request_sha256": "a" * 64,
            "source_snapshot_sha256": "b" * 64,
        }
        local_world = {"known": ["fact"]}
        retrieval = {"entries": [{"retrieval_id": "RETRIEVAL-1"}]}
        expected = checker._evidence_basis_sha256(
            run_contract,
            local_world,
            retrieval,
        )
        report = {
            "stability_checks": [
                {
                    "pro_prompt": "请赞成这个命题",
                    "anti_prompt": "请反对这个命题",
                    "pro_prompt_sha256": checker.sha256_json("请赞成这个命题"),
                    "anti_prompt_sha256": checker.sha256_json("请反对这个命题"),
                    "evidence_basis_sha256_before": expected,
                    "evidence_basis_sha256_after": expected,
                }
            ]
        }
        self.assertEqual(
            checker._validate_stability_evidence_binding(
                run_contract,
                local_world,
                retrieval,
                report,
            ),
            expected,
        )

        forged_prompt = copy.deepcopy(report)
        forged_prompt["stability_checks"][0]["pro_prompt"] += "（改写）"
        with self.assertRaisesRegex(ValueError, "prompt hash is not derived"):
            checker._validate_stability_evidence_binding(
                run_contract,
                local_world,
                retrieval,
                forged_prompt,
            )

        forged_evidence = copy.deepcopy(report)
        forged_evidence["stability_checks"][0][
            "evidence_basis_sha256_after"
        ] = "c" * 64
        with self.assertRaisesRegex(ValueError, "not bound to actual run artifacts"):
            checker._validate_stability_evidence_binding(
                run_contract,
                local_world,
                retrieval,
                forged_evidence,
            )

    def test_atomic_report_write_rejects_output_aliasing_an_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            input_path = workspace / "promax-run-contract.json"
            input_path.write_text("{}", encoding="utf-8")
            report_path = workspace / "promax-validator-report.json"
            try:
                os.link(input_path, report_path)
            except OSError as error:  # pragma: no cover - platform policy fallback
                self.skipTest(f"hard links unavailable: {error}")

            with self.assertRaises(ValueError):
                checker.write_report_atomic(
                    report_path,
                    {"overall_status": "fail"},
                    workspace=workspace,
                    input_paths=[input_path],
                )

    def test_atomic_report_write_publishes_new_bytes_without_using_output_as_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            input_path = workspace / "promax-run-contract.json"
            input_path.write_text("{}\n", encoding="utf-8")
            report_path = workspace / "promax-validator-report.json"
            report_path.write_text('{"old":true}\n', encoding="utf-8")
            old_identity = (report_path.stat().st_dev, report_path.stat().st_ino)

            checker.write_report_atomic(
                report_path,
                {"overall_status": "pass"},
                workspace=workspace,
                input_paths=[input_path],
            )

            self.assertEqual(
                json.loads(report_path.read_text(encoding="utf-8")),
                {"overall_status": "pass"},
            )
            self.assertNotEqual(
                (report_path.stat().st_dev, report_path.stat().st_ino),
                old_identity,
            )

    def test_manifest_policy_excludes_control_plane_and_report_cycles(self) -> None:
        valid = {
            "artifacts": [
                {"path": path, "status": "current"}
                for path in sorted(checker._MANIFEST_CURRENT_ARTIFACTS)
            ]
        }
        checker._validate_manifest_inventory_policy(valid)
        for forbidden in (
            "promax-run-contract.json",
            "promax-validator-report.json",
            "promax-repair-plan.json",
        ):
            candidate = json.loads(json.dumps(valid))
            candidate["artifacts"].append({"path": forbidden, "status": "current"})
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(ValueError):
                    checker._validate_manifest_inventory_policy(candidate)

    def test_existing_fresh_report_advances_validation_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            report_path = workspace / "promax-validator-report.json"
            report_path.write_text(
                json.dumps({"validation_attempt": 7}) + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(
                checker, "validate_validator_report_freshness"
            ) as freshness:
                attempt = checker._next_validation_attempt(
                    workspace,
                    {"run_id": "RUN"},
                    {"manifest_sha256": "a" * 64},
                    {"schema": "1"},
                )
            self.assertEqual(attempt, 8)
            self.assertEqual(
                freshness.call_args.kwargs["expected_validation_attempt"], 7
            )

    def test_red_team_after_ranking_is_bound_to_locked_recommendation(self) -> None:
        run_contract = {"recommendation_required": True}
        position = fixture_factory.build_position_lock(
            run_id="promax-checker-binding",
            locked_at="2026-07-23T01:00:00Z",
        )
        recommendation = fixture_factory.build_recommendation_lock(
            position,
            run_id="promax-checker-binding",
            locked_at="2026-07-23T01:30:00Z",
        )
        red_team = fixture_factory.build_red_team_report(
            run_id="promax-checker-binding",
            completed_at="2026-07-23T00:30:00Z",
        )
        checker._validate_stability_ranking_binding(
            run_contract, red_team, recommendation
        )
        red_team["stability_checks"][0]["option_ranking_after"][0:2] = (
            reversed(red_team["stability_checks"][0]["option_ranking_after"][0:2])
        )
        with self.assertRaises(ValueError):
            checker._validate_stability_ranking_binding(
                run_contract, red_team, recommendation
            )

        false_before_projection = copy.deepcopy(red_team)
        false_before_projection["stability_checks"][0]["option_ranking_after"] = [
            *recommendation["ranking"]
        ]
        false_before_projection["stability_checks"][0][
            "option_kind_ranking_before"
        ][0:2] = ["active_action", "probe_action"]
        with self.assertRaises(ValueError):
            checker._validate_stability_ranking_binding(
                run_contract,
                false_before_projection,
                recommendation,
            )

        ghost_evidence = copy.deepcopy(recommendation)
        ghost_evidence["ranking_policy"] = "evidence_bound_case_comparison"
        ghost_evidence["ranking_evidence_refs"] = ["RETRIEVAL-GHOST"]
        ghost_evidence["selection_review_wrapper"][
            "declared_low_information_house_policy_eligibility"
        ]["case_specific_facts_present"] = True
        ghost_evidence["selection_review_wrapper"]["ranking_support"] = [
            {
                "option_id": option_id,
                "evaluation_dimension": dimension,
                "evidence_refs": ["RETRIEVAL-GHOST"],
                "support_reason": "Fixture support cell.",
            }
            for option_id in ghost_evidence["ranking"]
            for dimension in ghost_evidence["evaluation_dimensions"]
        ]
        ghost_basis = checker.selection_review_basis_sha256(ghost_evidence)
        ghost_red_team = copy.deepcopy(
            fixture_factory.build_red_team_report(
                run_id="promax-checker-binding",
                completed_at="2026-07-23T00:30:00Z",
            )
        )
        for side in ("before", "after"):
            ghost_red_team["stability_checks"][0][
                f"normative_selection_basis_sha256_{side}"
            ] = ghost_basis
        with self.assertRaisesRegex(ValueError, "do not resolve"):
            checker._validate_stability_ranking_binding(
                run_contract,
                ghost_red_team,
                ghost_evidence,
                {"entries": [{"retrieval_id": "RETRIEVAL-REAL"}]},
            )

        not_requested_basis = checker.sha256_json({"status": "not_requested"})
        not_requested = {
            "stability_checks": [
                {
                    "option_ranking_before": [],
                    "option_ranking_after": [],
                    "option_kind_ranking_before": [],
                    "option_kind_ranking_after": [],
                    "option_semantic_ranking_before": [],
                    "option_semantic_ranking_after": [],
                    "normative_selection_basis_sha256_before": not_requested_basis,
                    "normative_selection_basis_sha256_after": not_requested_basis,
                }
            ]
        }
        checker._validate_stability_ranking_binding(
            {"recommendation_required": False},
            not_requested,
            {"status": "not_requested"},
        )

    def test_root_cli_is_a_thin_json_capable_wrapper(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/check_crossframe_promax_artifacts.py"),
                "--help",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ("--workspace", "--repo", "--final-chat", "--write-report", "--json"):
            self.assertIn(option, result.stdout)


if __name__ == "__main__":
    unittest.main()
