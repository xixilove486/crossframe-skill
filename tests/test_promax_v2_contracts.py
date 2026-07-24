from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "crossframe-promax" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from promax_runtime.artifacts import (  # noqa: E402
    ROLE_IDS,
    build_capability_disclosure,
    build_role_plan,
    initialize_run,
    validate_role_records,
)
from promax_runtime.jsonio import sha256_json  # noqa: E402
from promax_runtime.schemas import validate_instance  # noqa: E402


SOURCE_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)


class ProMaxV2RunContractTests(unittest.TestCase):
    def test_new_runs_emit_the_v2_release_and_six_role_plan(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
        )

        result = initialize_run(
            ROOT,
            "请明确调用 CrossFrame ProMax。",
            mode="promax-artifact-run",
            capabilities=capabilities,
            created_at="2026-07-25T00:00:00Z",
            run_id="promax-v2-contract-test",
        )

        contract = result["run_contract"]
        self.assertEqual(contract["schema_version"], 2)
        self.assertEqual(contract["skill_release"], "1.0.1")
        self.assertEqual(contract["framework_version"], "v8.0")
        self.assertEqual(
            ROLE_IDS,
            (
                "v8_source_concept_auditor",
                "external_case_researcher",
                "counterexample_auditor",
                "position_adjudicator",
                "longform_writer",
                "prose_fidelity_auditor",
            ),
        )
        self.assertEqual(
            [record["sequence"] for record in contract["role_plan"]],
            [1, 2, 3, 4, 5, 6],
        )
        self.assertEqual(
            contract["role_plan"][-1]["role_id"], "prose_fidelity_auditor"
        )
        self.assertIn(
            "prose",
            contract["capabilities"]["validators"]["validator_ids"],
        )

    def test_role_plan_builder_defaults_to_legacy_and_supports_explicit_v2(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
        )

        legacy = build_role_plan(capabilities)
        current = build_role_plan(capabilities, schema_version=2)

        self.assertEqual([item["role_id"] for item in legacy], list(ROLE_IDS[:5]))
        self.assertEqual([item["role_id"] for item in current], list(ROLE_IDS))
        with self.assertRaisesRegex(ValueError, "schema_version"):
            build_role_plan(capabilities, schema_version=3)

    def test_schema_versions_enforce_their_own_role_cardinality(self) -> None:
        legacy_path = (
            ROOT
            / "tests"
            / "evals"
            / "promax-green"
            / "artifacts"
            / "gpt-5.6-sol"
            / "A1"
            / "run"
            / "promax-run-contract.json"
        )
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        self.assertEqual(legacy["schema_version"], 1)
        self.assertEqual(len(legacy["role_plan"]), 5)
        validate_instance("promax-run-contract.schema.json", legacy)

        invalid_v1 = copy.deepcopy(legacy)
        invalid_v1["role_plan"].append(
            {
                "role_id": "prose_fidelity_auditor",
                "sequence": 6,
                "execution_mode": invalid_v1["orchestration_mode"],
                "exchange_protocol": "structured-artifacts-only",
            }
        )
        with self.assertRaises(ValidationError):
            validate_instance("promax-run-contract.schema.json", invalid_v1)

        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
        )
        current = initialize_run(
            ROOT,
            "请明确调用 CrossFrame ProMax。",
            mode="promax-artifact-run",
            capabilities=capabilities,
            created_at="2026-07-25T00:00:00Z",
            run_id="promax-v2-cardinality-test",
        )["run_contract"]
        invalid_v2 = copy.deepcopy(current)
        invalid_v2["role_plan"].pop()
        with self.assertRaises(ValidationError):
            validate_instance("promax-run-contract.schema.json", invalid_v2)

    def test_legacy_five_role_records_still_validate(self) -> None:
        run_dir = (
            ROOT
            / "tests"
            / "evals"
            / "promax-green"
            / "artifacts"
            / "gpt-5.6-sol"
            / "A1"
            / "run"
        )
        legacy = json.loads(
            (run_dir / "promax-run-contract.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (run_dir / "promax-artifact-manifest.json").read_text(encoding="utf-8")
        )
        known_artifacts = {
            artifact["path"]: artifact["sha256"]
            for artifact in manifest["artifacts"]
            if artifact["status"] == "current"
        }

        validated = validate_role_records(
            legacy,
            manifest["role_records"],
            known_artifacts,
            artifact_records=manifest["artifacts"],
        )

        self.assertEqual(len(validated), 5)
        self.assertEqual(validated[-1]["role_id"], "longform_writer")

    def test_sixth_role_reads_and_writes_p10_artifacts(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
        )
        contract = initialize_run(
            ROOT,
            "请明确调用 CrossFrame ProMax。",
            mode="promax-artifact-run",
            capabilities=capabilities,
            created_at="2026-07-25T00:00:00Z",
            run_id="promax-v2-phase-test",
        )["run_contract"]
        input_phases = ("P3", "P5", "P6", "P7", "P9")
        output_phases = ("P4", "P6", "P7", "P8", "P10", "P10")
        records = []
        known_artifacts = {}
        artifact_records = []
        previous_output = None
        for index, role_id in enumerate(ROLE_IDS, start=1):
            if index == 6:
                input_ref = previous_output
            else:
                input_ref = {
                    "path": f"inputs/{index}.json",
                    "sha256": f"{index:064x}",
                    "media_type": "application/json",
                }
                known_artifacts[input_ref["path"]] = input_ref["sha256"]
                artifact_records.append(
                    {
                        **input_ref,
                        "generating_phase": input_phases[index - 1],
                        "input_artifact_sha256s": [],
                        "status": "current",
                    }
                )
            output_ref = {
                "path": f"outputs/{index}.json",
                "sha256": f"{index + 10:064x}",
                "media_type": "application/json",
            }
            known_artifacts[output_ref["path"]] = output_ref["sha256"]
            artifact_records.append(
                {
                    **output_ref,
                    "generating_phase": output_phases[index - 1],
                    "input_artifact_sha256s": [input_ref["sha256"]],
                    "status": "current",
                }
            )
            records.append(
                {
                    "role_id": role_id,
                    "sequence": index,
                    "execution_mode": "single-agent-separated",
                    "exchange_protocol": "structured-artifacts-only",
                    "input_artifacts": [input_ref],
                    "observed_input_artifacts": [input_ref],
                    "output_artifacts": [output_ref],
                    "status": "completed",
                }
            )
            previous_output = output_ref

        validated = validate_role_records(
            contract,
            records,
            known_artifacts,
            artifact_records=artifact_records,
        )
        self.assertEqual(validated[-1]["input_artifacts"][0]["path"], "outputs/5.json")
        self.assertEqual(validated[-1]["output_artifacts"][0]["path"], "outputs/6.json")

        invalid_records = copy.deepcopy(records)
        invalid_artifacts = copy.deepcopy(artifact_records)
        invalid_known_artifacts = copy.deepcopy(known_artifacts)
        late_input = {
            "path": "inputs/6-late.json",
            "sha256": f"{99:064x}",
            "media_type": "application/json",
        }
        invalid_records[-1]["input_artifacts"] = [late_input]
        invalid_records[-1]["observed_input_artifacts"] = [late_input]
        invalid_known_artifacts[late_input["path"]] = late_input["sha256"]
        invalid_artifacts.append(
            {
                **late_input,
                "generating_phase": "P11",
                "input_artifact_sha256s": [],
                "status": "current",
            }
        )
        invalid_artifacts[-2]["input_artifact_sha256s"] = [late_input["sha256"]]
        with self.assertRaisesRegex(ValueError, "prior producer before P10"):
            validate_role_records(
                contract,
                invalid_records,
                invalid_known_artifacts,
                artifact_records=invalid_artifacts,
            )

    def test_isolated_prose_auditor_attests_all_three_current_inputs(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=True,
            max_parallelism=6,
        )
        contract = initialize_run(
            ROOT,
            "请明确调用 CrossFrame ProMax。",
            mode="promax-complete",
            capabilities=capabilities,
            created_at="2026-07-25T00:00:00Z",
            run_id="promax-v2-multi-input-attestation",
        )["run_contract"]
        bindings = (
            (("input/world.json", "P3"), ("output/concepts.json", "P4")),
            (("input/claims.json", "P5"), ("output/retrieval.json", "P6")),
            (("output/retrieval.json", "P6"), ("output/red-team.json", "P7")),
            (("output/red-team.json", "P7"), ("output/position.json", "P8")),
            (("input/plan.json", "P9"), ("output/essay.md", "P10")),
            (
                (
                    ("output/essay.md", "P10"),
                    ("output/position.json", "P8"),
                    ("input/plan.json", "P9"),
                ),
                ("output/prose-review.json", "P10"),
            ),
        )
        known: dict[str, str] = {}
        artifacts: dict[str, dict[str, object]] = {}

        def artifact_ref(path: str) -> dict[str, str]:
            digest = known.setdefault(
                path,
                f"{len(known) + 1:064x}",
            )
            return {
                "path": path,
                "sha256": digest,
                "media_type": (
                    "text/markdown" if path.endswith(".md") else "application/json"
                ),
            }

        records: list[dict[str, object]] = []
        for index, (raw_inputs, output_binding) in enumerate(bindings, start=1):
            normalized_inputs = (
                raw_inputs if index == 6 else (raw_inputs,)
            )
            input_refs = []
            for path, phase in normalized_inputs:
                ref = artifact_ref(path)
                input_refs.append(ref)
                artifacts.setdefault(
                    path,
                    {
                        **ref,
                        "generating_phase": phase,
                        "input_artifact_sha256s": [],
                        "status": "current",
                    },
                )
            output_path, output_phase = output_binding
            output_ref = artifact_ref(output_path)
            artifacts[output_path] = {
                **output_ref,
                "generating_phase": output_phase,
                "input_artifact_sha256s": [
                    ref["sha256"] for ref in input_refs
                ],
                "status": "current",
            }
            completed_at = f"2026-07-25T00:0{index}:00Z"
            claim = {
                "run_id": contract["run_id"],
                "request_sha256": contract["request_sha256"],
                "source_snapshot_sha256": contract["source_snapshot_sha256"],
                "role_id": ROLE_IDS[index - 1],
                "sequence": index,
                "agent_id": f"isolated-agent-{index}",
                "completed_at": completed_at,
                "observed_input_artifacts": input_refs,
                "produced_output_artifacts": [output_ref],
            }
            records.append(
                {
                    **contract["role_plan"][index - 1],
                    "input_artifacts": input_refs,
                    "observed_input_artifacts": copy.deepcopy(input_refs),
                    "output_artifacts": [output_ref],
                    "agent_id": f"isolated-agent-{index}",
                    "execution_attestation": {
                        "run_id": contract["run_id"],
                        "request_sha256": contract["request_sha256"],
                        "source_snapshot_sha256": contract[
                            "source_snapshot_sha256"
                        ],
                        "completed_at": completed_at,
                        "observed_input_artifacts": copy.deepcopy(input_refs),
                        "produced_output_artifacts": [copy.deepcopy(output_ref)],
                        "claim_sha256": sha256_json(claim),
                    },
                    "status": "completed",
                }
            )

        validated = validate_role_records(
            contract,
            records,
            known,
            artifact_records=list(artifacts.values()),
        )
        self.assertEqual(
            len(validated[-1]["execution_attestation"]["observed_input_artifacts"]),
            3,
        )

        incomplete = copy.deepcopy(records)
        incomplete[-1]["execution_attestation"]["observed_input_artifacts"].pop()
        incomplete_attestation = incomplete[-1]["execution_attestation"]
        incomplete_attestation["claim_sha256"] = sha256_json(
            {
                "run_id": contract["run_id"],
                "request_sha256": contract["request_sha256"],
                "source_snapshot_sha256": contract["source_snapshot_sha256"],
                "role_id": incomplete[-1]["role_id"],
                "sequence": incomplete[-1]["sequence"],
                "agent_id": incomplete[-1]["agent_id"],
                "completed_at": incomplete_attestation["completed_at"],
                "observed_input_artifacts": incomplete_attestation[
                    "observed_input_artifacts"
                ],
                "produced_output_artifacts": incomplete_attestation[
                    "produced_output_artifacts"
                ],
            }
        )
        with self.assertRaisesRegex(ValueError, "attested observed inputs"):
            validate_role_records(
                contract,
                incomplete,
                known,
                artifact_records=list(artifacts.values()),
            )


class ProMaxV2OutputPlanTests(unittest.TestCase):
    def test_v2_plan_carries_reader_projection_and_prose_mappings(self) -> None:
        plan = {
            "schema_id": "crossframe.promax.v8.output-plan",
            "schema_version": 2,
            "run_id": "promax-v2-contract-test",
            "source_snapshot_sha256": SOURCE_SHA256,
            "sections": [
                {
                    "section_id": "SECTION-1",
                    "title": "现实入口",
                    "concept_ids": ["V8-CANON-OBJECT-BOUNDARY"],
                    "claim_ids": ["CLAIM-THESIS"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "path_node_ids": ["NODE-1"],
                    "example_ids": ["CASE-1"],
                    "counterexample_ids": ["COUNTER-1"],
                    "judgment_ids": ["JUDGMENT-1"],
                    "artifact_paths": ["promax-essay.md"],
                }
            ],
            "reader_projection": {
                "article_type": "case-analysis",
                "house_voice_id": "crossframe-promax",
                "thesis_claim_id": "CLAIM-THESIS",
                "core_concept_ids": ["V8-CANON-OBJECT-BOUNDARY"],
                "atlas_only_concept_ids": ["V8-CANON-AUXILIARY"],
                "selected_techniques": [
                    {
                        "technique_id": "TECHNIQUE-REALITY-ENTRY",
                        "tier": "core",
                        "paragraph_action": "从现实冲突切入。",
                        "section_ids": ["SECTION-1"],
                    },
                    {
                        "technique_id": "TECHNIQUE-MECHANISM-LADDER",
                        "tier": "core",
                        "paragraph_action": "逐层展开机制依赖。",
                        "section_ids": ["SECTION-1"],
                    },
                    {
                        "technique_id": "TECHNIQUE-RESIDUE",
                        "tier": "core",
                        "paragraph_action": "以可继续思考的余味收束。",
                        "section_ids": ["SECTION-1"],
                    },
                    {
                        "technique_id": "TECHNIQUE-CONTRAST",
                        "tier": "auxiliary",
                        "paragraph_action": "压缩同维正反比较。",
                        "section_ids": ["SECTION-1"],
                    },
                ],
                "reader_beats": [
                    {
                        "beat_id": "BEAT-1",
                        "function": "建立现实问题与中心命题的依赖。",
                        "section_ids": ["SECTION-1"],
                        "claim_ids": ["CLAIM-THESIS"],
                        "mechanism_ids": ["MECHANISM-1"],
                        "evidence_refs": ["EVIDENCE-1"],
                        "core_concept_ids": ["V8-CANON-OBJECT-BOUNDARY"],
                        "technique_ids": ["TECHNIQUE-REALITY-ENTRY"],
                    }
                ],
            },
            "required_artifacts": [
                "promax-dossier.md",
                "promax-concept-atlas.md",
                "promax-case-and-countercase.md",
                "promax-essay.md",
            ],
            "unexpanded_branch_ids": [],
            "coverage_complete": True,
            "locked_at": "2026-07-25T00:00:00Z",
        }

        validate_instance("promax-output-plan.schema.json", plan)

        article_types = (
            "reply",
            "public-commentary",
            "concept-explanation",
            "organization-review",
            "case-analysis",
            "debate-refutation",
            "reading-synthesis",
            "trend-deduction",
            "neutral-analysis",
        )
        for article_type in article_types:
            with self.subTest(article_type=article_type):
                plan["reader_projection"]["article_type"] = article_type
                validate_instance("promax-output-plan.schema.json", plan)

        plan["sections"][0].pop("mechanism_ids")
        plan["sections"][0].pop("path_node_ids")
        validate_instance("promax-output-plan.schema.json", plan)

        too_few_core = copy.deepcopy(plan)
        too_few_core["reader_projection"]["selected_techniques"].pop(2)
        with self.assertRaises(ValidationError):
            validate_instance("promax-output-plan.schema.json", too_few_core)

    def test_legacy_output_plan_shape_remains_valid(self) -> None:
        legacy_path = (
            ROOT
            / "tests"
            / "evals"
            / "promax-green"
            / "artifacts"
            / "gpt-5.6-sol"
            / "A1"
            / "run"
            / "promax-output-plan.locked.json"
        )
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        self.assertEqual(legacy["schema_version"], 1)
        self.assertNotIn("reader_projection", legacy)
        validate_instance("promax-output-plan.schema.json", legacy)


class ProMaxProseReviewSchemaTests(unittest.TestCase):
    def test_review_binds_upstream_artifacts_and_all_review_dimensions(self) -> None:
        dimension_ids = (
            "reality_entry",
            "argument_dependency",
            "v8_concept_fidelity",
            "evidence_binding",
            "strongest_counterposition",
            "fair_comparison",
            "position_recommendation_consistency",
            "withdrawal_action_boundary",
            "house_voice",
            "model_flavor_independence",
            "audit_leakage",
        )
        review = {
            "schema_id": "crossframe.promax.v8.prose-review",
            "schema_version": 1,
            "run_id": "promax-v2-contract-test",
            "source_snapshot_sha256": SOURCE_SHA256,
            "essay_sha256": "a" * 64,
            "position_sha256": "b" * 64,
            "output_plan_sha256": "c" * 64,
            "article_type": "case-analysis",
            "technique_ids": [
                "TECHNIQUE-REALITY-ENTRY",
                "TECHNIQUE-MECHANISM-LADDER",
                "TECHNIQUE-RESIDUE",
            ],
            "required_beat_mappings": [
                {
                    "beat_id": "BEAT-1",
                    "section_ids": ["SECTION-1"],
                    "evidence_excerpts": ["现实冲突已经迫使判断进入下一步。"],
                }
            ],
            "dimensions": {
                dimension_id: {
                    "status": "pass",
                    "evidence_excerpts": [f"{dimension_id} 的正文短摘。"],
                    "repair_target": None,
                }
                for dimension_id in dimension_ids
            },
            "overall_status": "pass",
            "reviewed_at": "2026-07-25T00:00:00Z",
        }

        validate_instance("promax-prose-review.schema.json", review)

        inconsistent = copy.deepcopy(review)
        inconsistent["dimensions"]["reality_entry"] = {
            "status": "fail",
            "evidence_excerpts": [],
            "repair_target": "重写现实入口。",
        }
        with self.assertRaises(ValidationError):
            validate_instance("promax-prose-review.schema.json", inconsistent)

        inconsistent["overall_status"] = "fail"
        validate_instance("promax-prose-review.schema.json", inconsistent)

        unexpected = copy.deepcopy(review)
        unexpected["dimensions"]["audit_leakage"]["notes"] = "open field"
        with self.assertRaises(ValidationError):
            validate_instance("promax-prose-review.schema.json", unexpected)


if __name__ == "__main__":
    unittest.main()
