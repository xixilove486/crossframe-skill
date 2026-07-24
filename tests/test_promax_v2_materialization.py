from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

import crossframe_promax_runtime
import crossframe_promax_fixture_factory as fixture_factory
from promax_runtime.jsonio import canonical_json_bytes, load_json, sha256_json
from promax_runtime.materialization import (
    MaterializationError,
    ROLE_ATTESTATIONS_ARTIFACT,
    _authoring_contract,
    _load_semantic_json,
    _metadata,
    _phase_specs,
    _role_attestation_scaffold,
    _role_records,
    _validate_authoring_contract,
    prepare_run,
)


REQUEST = "请使用 $crossframe-promax 分析 bounded transfer mechanism。"
CREATED_AT = "2026-07-25T10:00:00Z"
READ_AT = "2026-07-25T10:01:00Z"
LEGACY_RUN_CONTRACT = (
    ROOT
    / "tests/evals/promax-green/artifacts/gpt-5.6-sol/A1/run"
    / "promax-run-contract.json"
)


def initialize_v2_run(run_dir: Path, *, subagents: bool) -> None:
    args = [
        "init",
        "--repo",
        str(ROOT),
        "--run-dir",
        str(run_dir),
        "--request",
        REQUEST,
        "--mode",
        "promax-complete",
        "--run-id",
        "promax-v2-materialization-test",
        "--created-at",
        CREATED_AT,
        "--network",
        "--recommendation-required",
    ]
    if subagents:
        args.extend(["--subagents", "--max-parallelism", "6"])
    with redirect_stdout(io.StringIO()):
        result = crossframe_promax_runtime.main(args)
    if result != 0:
        raise AssertionError(f"init returned {result}")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def v2_semantic_authoring(
    authoring_dir: Path,
) -> tuple[dict[str, object], str]:
    run_id = "promax-v2-semantic-test"
    contract = {
        "schema_version": 2,
        "run_id": run_id,
        "request_sha256": "a" * 64,
        "source_snapshot_sha256": fixture_factory.V8_SOURCE_SNAPSHOT_SHA256,
    }
    local_world = fixture_factory.build_local_world_model(
        run_id=run_id,
        locked_at="2026-07-25T11:00:00Z",
    )
    claim_graph = fixture_factory.build_claim_path_graph(
        run_id=run_id,
        updated_at="2026-07-25T11:01:00Z",
    )
    retrieval = fixture_factory.build_retrieval_ledger(
        run_id=run_id,
        completed_at="2026-07-25T11:02:00Z",
    )
    evidence_basis = sha256_json(
        {
            "request_sha256": contract["request_sha256"],
            "source_snapshot_sha256": contract["source_snapshot_sha256"],
            "local_world_model_sha256": sha256_json(local_world),
            "retrieval_ledger_sha256": sha256_json(retrieval),
        }
    )
    red_team = fixture_factory.build_red_team_report(
        run_id=run_id,
        completed_at="2026-07-25T11:03:00Z",
        recommendation_locked_at="2026-07-25T11:05:00Z",
        evidence_basis_sha256=evidence_basis,
    )
    position = fixture_factory.build_position_lock(
        run_id=run_id,
        locked_at="2026-07-25T11:04:00Z",
    )
    recommendation = fixture_factory.build_recommendation_lock(
        position,
        run_id=run_id,
        locked_at="2026-07-25T11:05:00Z",
    )
    output_plan = fixture_factory.build_output_plan(
        run_id=run_id,
        locked_at="2026-07-25T11:06:00Z",
    )
    essay = fixture_factory.build_deliverables(
        ROOT,
        position=position,
        recommendation=recommendation,
    )["promax-essay.md"]
    review = fixture_factory.build_prose_review(
        run_id=run_id,
        reviewed_at="2026-07-25T11:07:00Z",
        essay=essay,
        position=position,
        output_plan=output_plan,
    )
    for field in (
        "schema_id",
        "schema_version",
        "run_id",
        "source_snapshot_sha256",
        "essay_sha256",
        "position_sha256",
        "output_plan_sha256",
        "reviewed_at",
    ):
        review.pop(field)
    values = {
        "promax-local-world-model.locked.json": local_world,
        "promax-claim-path-graph.json": claim_graph,
        "promax-retrieval-ledger.json": retrieval,
        "promax-red-team-report.json": red_team,
        "promax-position.locked.json": position,
        "promax-recommendation.locked.json": recommendation,
        "promax-output-plan.locked.json": output_plan,
        "promax-prose-review.json": review,
    }
    for artifact, value in values.items():
        write_json(authoring_dir / artifact, value)
    return contract, essay


class ProMaxV2AuthoringContractTests(unittest.TestCase):
    def test_v2_authoring_contract_validates_against_v2_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_v2_run(run_dir, subagents=False)
            run_contract = load_json(run_dir / "promax-run-contract.json")
            authoring = _authoring_contract(
                run_contract,
                prepared_at=READ_AT,
            )

            _validate_authoring_contract(authoring, run_contract)

    def test_v2_prepare_requires_review_and_scaffolds_three_input_auditor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir = base / "run"
            authoring_dir = base / "authoring"
            initialize_v2_run(run_dir, subagents=True)

            prepare_run(
                ROOT,
                run_dir=run_dir,
                authoring_dir=authoring_dir,
                read_at=READ_AT,
            )

            contract = load_json(authoring_dir / "promax-authoring-contract.json")
            self.assertEqual(contract["schema_version"], 2)
            self.assertIn(
                "promax-prose-review.json",
                contract["required_semantic_artifacts"],
            )
            self.assertEqual(
                contract["template_map"]["promax-prose-review.json"],
                "templates/promax-prose-review-output.md",
            )

            attestations = load_json(
                authoring_dir / ROLE_ATTESTATIONS_ARTIFACT
            )
            self.assertEqual(len(attestations["roles"]), 6)
            auditor = attestations["roles"][-1]
            self.assertEqual(auditor["role_id"], "prose_fidelity_auditor")
            self.assertEqual(
                auditor["input_artifact_paths"],
                [
                    "promax-essay.md",
                    "promax-position.locked.json",
                    "promax-output-plan.locked.json",
                ],
            )
            self.assertEqual(
                auditor["output_artifact_paths"],
                ["promax-prose-review.json"],
            )

    def test_v1_authoring_and_attestation_contract_remain_unchanged(self) -> None:
        legacy = json.loads(LEGACY_RUN_CONTRACT.read_text(encoding="utf-8"))

        authoring = _authoring_contract(
            legacy,
            prepared_at=READ_AT,
        )
        attestations = _role_attestation_scaffold(legacy)

        self.assertEqual(authoring["schema_version"], 1)
        self.assertNotIn(
            "promax-prose-review.json",
            authoring["required_semantic_artifacts"],
        )
        self.assertNotIn(
            "promax-prose-review.json",
            authoring["template_map"],
        )
        self.assertEqual(len(attestations["roles"]), 5)
        self.assertEqual(
            attestations["roles"][-1]["input_artifact_paths"],
            ["promax-output-plan.locked.json"],
        )
        self.assertEqual(
            attestations["roles"][-1]["output_artifact_paths"],
            ["promax-essay.md"],
        )


class ProMaxV2SemanticBindingTests(unittest.TestCase):
    def test_runtime_injects_current_review_bindings_without_writing_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            authoring_dir = Path(temp_dir)
            contract, essay = v2_semantic_authoring(authoring_dir)

            documents = _load_semantic_json(
                authoring_dir,
                contract,
                generated_at="2026-07-25T11:08:00Z",
                essay=essay,
            )

            review = documents["promax-prose-review.json"]
            self.assertEqual(
                review["essay_sha256"],
                hashlib.sha256(essay.encode("utf-8")).hexdigest(),
            )
            self.assertEqual(
                review["position_sha256"],
                sha256_json(documents["promax-position.locked.json"]),
            )
            self.assertEqual(
                review["output_plan_sha256"],
                sha256_json(documents["promax-output-plan.locked.json"]),
            )
            self.assertEqual(review["reviewed_at"], "2026-07-25T11:08:00Z")
            self.assertEqual(len(review["dimensions"]), 11)

    def test_runtime_rejects_conflicting_review_hash_instead_of_masking_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            authoring_dir = Path(temp_dir)
            contract, essay = v2_semantic_authoring(authoring_dir)
            review = load_json(authoring_dir / "promax-prose-review.json")
            review["essay_sha256"] = "f" * 64
            write_json(authoring_dir / "promax-prose-review.json", review)

            with self.assertRaisesRegex(
                MaterializationError,
                "semantic_binding_mismatch:promax-prose-review.json:essay_sha256",
            ):
                _load_semantic_json(
                    authoring_dir,
                    contract,
                    generated_at="2026-07-25T11:08:00Z",
                    essay=essay,
                )


class ProMaxV2LineageTests(unittest.TestCase):
    def test_metadata_phase_and_single_agent_role_bind_all_review_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "fixture"
            fixture_factory.materialize_fixture(
                ROOT,
                scenario_id="valid-complete",
                output=workspace,
            )
            contract = load_json(workspace / "promax-run-contract.json")
            manifest = load_json(workspace / "promax-artifact-manifest.json")
            digests = {
                artifact["path"]: artifact["sha256"]
                for artifact in manifest["artifacts"]
            }

            metadata = _metadata(digests, contract)
            phase_specs = _phase_specs(digests, contract)
            records = _role_records(
                contract,
                digests,
                authoring=workspace,
            )

            self.assertEqual(
                set(metadata["promax-prose-review.json"]["input_artifact_sha256s"]),
                {
                    digests["promax-essay.md"],
                    digests["promax-position.locked.json"],
                    digests["promax-output-plan.locked.json"],
                },
            )
            p10 = next(outputs for phase, _inputs, outputs in phase_specs if phase == "P10")
            self.assertIn("promax-prose-review.json", p10)
            auditor = records[-1]
            self.assertEqual(
                [item["path"] for item in auditor["input_artifacts"]],
                [
                    "promax-essay.md",
                    "promax-position.locked.json",
                    "promax-output-plan.locked.json",
                ],
            )
            self.assertEqual(
                auditor["observed_input_artifacts"],
                auditor["input_artifacts"],
            )
            self.assertEqual(
                [item["path"] for item in auditor["output_artifacts"]],
                ["promax-prose-review.json"],
            )

    def test_multi_agent_attestation_and_role_record_bind_same_three_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            authoring = Path(temp_dir)
            run_dir = authoring / "run"
            initialize_v2_run(run_dir, subagents=True)
            contract = load_json(run_dir / "promax-run-contract.json")
            scaffold = _role_attestation_scaffold(contract)
            bindings = [
                (
                    tuple(role["input_artifact_paths"]),
                    tuple(role["output_artifact_paths"]),
                )
                for role in scaffold["roles"]
            ]
            all_paths = {
                path
                for inputs, outputs in bindings
                for path in (*inputs, *outputs)
            }
            all_paths.update(
                {
                    "promax-local-world-model.locked.json",
                    "promax-concept-disposition-ledger.json",
                }
            )
            digests: dict[str, str] = {}
            for index, path in enumerate(sorted(all_paths), start=1):
                body = f"artifact {index}: {path}\n".encode()
                (authoring / path).write_bytes(body)
                digests[path] = hashlib.sha256(body).hexdigest()
            for role in scaffold["roles"]:
                role["agent_id"] = f"isolated-agent-{role['sequence']}"
                role["observed_input_artifacts"] = [
                    {"path": path, "sha256": digests[path]}
                    for path in role["input_artifact_paths"]
                ]
                role["produced_output_artifacts"] = [
                    {"path": path, "sha256": digests[path]}
                    for path in role["output_artifact_paths"]
                ]
                role["completed_at"] = "2026-07-25T11:10:00Z"
                role["status"] = "completed"
            write_json(authoring / ROLE_ATTESTATIONS_ARTIFACT, scaffold)

            records = _role_records(
                contract,
                digests,
                authoring=authoring,
            )

            auditor = records[-1]
            attestation = auditor["execution_attestation"]
            self.assertEqual(
                attestation["observed_input_artifacts"],
                auditor["observed_input_artifacts"],
            )
            self.assertEqual(
                attestation["produced_output_artifacts"],
                auditor["output_artifacts"],
            )
            self.assertEqual(len(attestation["observed_input_artifacts"]), 3)

    def test_legacy_metadata_and_p10_outputs_do_not_gain_review(self) -> None:
        legacy_run = LEGACY_RUN_CONTRACT.parent
        contract = load_json(LEGACY_RUN_CONTRACT)
        manifest = load_json(legacy_run / "promax-artifact-manifest.json")
        digests = {
            artifact["path"]: artifact["sha256"]
            for artifact in manifest["artifacts"]
        }

        metadata = _metadata(digests, contract)
        phase_specs = _phase_specs(digests, contract)

        self.assertNotIn("promax-prose-review.json", metadata)
        p10 = next(outputs for phase, _inputs, outputs in phase_specs if phase == "P10")
        self.assertNotIn("promax-prose-review.json", p10)

    def test_runtime_calls_semantic_review_validation_after_schema_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            authoring_dir = Path(temp_dir)
            contract, essay = v2_semantic_authoring(authoring_dir)
            review = load_json(authoring_dir / "promax-prose-review.json")
            review["dimensions"]["evidence_binding"]["evidence_excerpts"] = [
                "这段摘录不在正文里"
            ]
            write_json(authoring_dir / "promax-prose-review.json", review)

            with self.assertRaisesRegex(ValueError, "evidence_excerpt"):
                _load_semantic_json(
                    authoring_dir,
                    contract,
                    generated_at="2026-07-25T11:08:00Z",
                    essay=essay,
                )


class ProMaxV2TemplateTests(unittest.TestCase):
    def test_output_plan_template_requires_reader_projection_contract(self) -> None:
        text = (
            ROOT
            / "skills/crossframe-promax/templates/promax-output-plan-output.md"
        ).read_text(encoding="utf-8")

        self.assertIn("schema_version=2", text)
        for field in (
            "reader_projection",
            "article_type",
            "house_voice_id",
            "thesis_claim_id",
            "core_concept_ids",
            "atlas_only_concept_ids",
            "selected_techniques",
            "reader_beats",
        ):
            self.assertIn(field, text)
        self.assertIn("固定顺序", text)
        self.assertIn("auxiliary_candidates", text)

    def test_prose_review_template_is_self_contained_and_names_all_dimensions(self) -> None:
        path = (
            ROOT
            / "skills/crossframe-promax/templates/promax-prose-review-output.md"
        )
        text = path.read_text(encoding="utf-8")

        for field in (
            "essay_sha256",
            "position_sha256",
            "output_plan_sha256",
            "required_beat_mappings",
            "evidence_excerpts",
            "reviewed_at",
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
        ):
            self.assertIn(field, text)
        self.assertIn("正文逐字短摘", text)
        self.assertIn("ceil(2N/3)", text)
        self.assertIn("至少 8", text)
        self.assertIn("最多复用于两个", text)
        self.assertIn("完全相同", text)
        self.assertIn("8 个实质字符", text)
        self.assertIn("最多 240", text)
        self.assertIn("正文中唯一", text)
        self.assertIn("按所在句区归一化", text)
        self.assertIn("任一句区最多支撑两个", text)
        self.assertIn("8 个不同句区组合", text)


if __name__ == "__main__":
    unittest.main()
