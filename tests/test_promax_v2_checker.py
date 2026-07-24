from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "crossframe-promax" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_crossframe_promax_artifacts as checker  # noqa: E402
import crossframe_promax_fixture_factory as fixture_factory  # noqa: E402
from promax_runtime.artifacts import build_role_plan  # noqa: E402
from promax_runtime.deliverables import (  # noqa: E402
    validate_continuation_lineage,
    validate_output_bundle,
)
from tests import test_promax_artifacts as legacy  # noqa: E402


def _string_leaves(value: object) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for child in value.values():
            result.extend(_string_leaves(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(_string_leaves(child))
        return result
    return [value] if isinstance(value, str) and value else []


def v2_bundle() -> dict[str, object]:
    bundle = legacy.valid_bundle()
    contract = bundle["run_contract"]
    contract["schema_version"] = 2
    contract["skill_release"] = "1.0.1"
    contract["capabilities"]["validators"]["validator_ids"] = [
        "schema",
        "output",
        "prose",
    ]
    contract["role_plan"] = build_role_plan(
        contract["capabilities"],
        schema_version=2,
    )

    plan = bundle["output_plan"]
    plan["schema_version"] = 2
    plan["reader_projection"] = {
        "article_type": "public-commentary",
        "house_voice_id": "crossframe-promax",
        "thesis_claim_id": "CLAIM-CENTRAL",
        "core_concept_ids": ["V8-CANON-OBJECT"],
        "atlas_only_concept_ids": ["V8-CANON-BOUNDARY"],
        "selected_techniques": [
            {
                "technique_id": "event-association",
                "tier": "core",
                "paragraph_action": "从现实冲突进入。",
                "section_ids": ["SECTION-1"],
            },
            {
                "technique_id": "layered-argument",
                "tier": "core",
                "paragraph_action": "按机制依赖递进。",
                "section_ids": ["SECTION-1"],
            },
            {
                "technique_id": "positive-negative-contrast",
                "tier": "core",
                "paragraph_action": "重建最强反方。",
                "section_ids": ["SECTION-1"],
            },
            {
                "technique_id": "finishing-touch",
                "tier": "auxiliary",
                "paragraph_action": "回到现实责任。",
                "section_ids": ["SECTION-1"],
            },
        ],
        "reader_beats": [
            {
                "beat_id": "BEAT-ENTRY",
                "function": "现实入口、中心命题与撤回边界。",
                "section_ids": ["SECTION-1"],
                "claim_ids": ["CLAIM-CENTRAL"],
                "mechanism_ids": ["MECH-1"],
                "evidence_refs": ["EVIDENCE-1"],
                "core_concept_ids": ["V8-CANON-OBJECT"],
                "technique_ids": ["event-association", "layered-argument"],
            }
        ],
    }
    bundle["claim_path_graph"]["claims"][0]["evidence_refs"] = ["EVIDENCE-1"]
    bundle["retrieval_ledger"] = {
        "entries": [
            {
                "retrieval_id": "RETRIEVAL-1",
                "claim_ids": ["CLAIM-CENTRAL"],
            }
        ]
    }

    bundle["deliverables"]["promax-essay.md"] = """# 谁承担验证的代价

现实中的冲突不是术语不够多，而是试验收益与退出成本落在不同的人身上。APP-INS | 这句自然表达保留了问题的摩擦。

当前结构最符合机制甲。对象边界让我们先问清楚谁被纳入判断、谁承担代价；在现有材料下，这足以支持一个可以撤回的小范围判断。

最强的反对意见是试验本身会扩大既有损害。如果新的材料证明成本已经不可逆，就应停止并撤回，而不是把分析误写成现实授权。

真正需要留下的问题，是下一次验证由谁承担代价，以及承担者能否退出。
"""
    position = bundle["position"]
    recommendation = bundle["recommendation"]
    bundle["deliverables"]["promax-dossier.md"] = "\n".join(
        [
            "# 推演档案",
            *_string_leaves(position),
            *_string_leaves(recommendation),
        ]
    )
    legacy.refresh_delivery_bindings(bundle)
    return bundle


def _canonical_json_file(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _write_json(path: Path, value: object) -> bytes:
    payload = _canonical_json_file(value)
    path.write_bytes(payload)
    return payload


def _rewrite_review_and_bind_manifest(
    workspace: Path,
    mutate,
) -> None:
    review_path = workspace / "promax-prose-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    mutate(review)
    review_payload = _write_json(review_path, review)
    review_sha = hashlib.sha256(review_payload).hexdigest()

    manifest_path = workspace / "promax-artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        if artifact["path"] == "promax-prose-review.json":
            artifact["sha256"] = review_sha
    for role in manifest["role_records"]:
        for artifact in role["output_artifacts"]:
            if artifact["path"] == "promax-prose-review.json":
                artifact["sha256"] = review_sha
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256")
    manifest["manifest_sha256"] = checker.sha256_json(unsigned)
    _write_json(manifest_path, manifest)

    continuation_path = workspace / "promax-continuation-ledger.json"
    continuation = json.loads(continuation_path.read_text(encoding="utf-8"))
    continuation["parent_manifest_sha256"] = manifest["manifest_sha256"]
    _write_json(continuation_path, continuation)


def _append_essay_and_bind_manifest(
    workspace: Path,
    appendix: str,
) -> str:
    essay_path = workspace / "promax-essay.md"
    original_essay = essay_path.read_text(encoding="utf-8")
    original_essay_sha = hashlib.sha256(
        original_essay.encode("utf-8")
    ).hexdigest()
    essay = original_essay + appendix
    essay_payload = essay.encode("utf-8")
    essay_path.write_bytes(essay_payload)
    essay_sha = hashlib.sha256(essay_payload).hexdigest()

    manifest_path = workspace / "promax-artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        if artifact["path"] == "promax-essay.md":
            artifact["sha256"] = essay_sha
    for role in manifest["role_records"]:
        for collection in (
            "input_artifacts",
            "observed_input_artifacts",
            "output_artifacts",
        ):
            for artifact in role[collection]:
                if artifact["path"] == "promax-essay.md":
                    artifact["sha256"] = essay_sha
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256")
    manifest["manifest_sha256"] = checker.sha256_json(unsigned)
    _write_json(manifest_path, manifest)

    continuation_path = workspace / "promax-continuation-ledger.json"
    continuation = json.loads(continuation_path.read_text(encoding="utf-8"))
    continuation["parent_manifest_sha256"] = manifest["manifest_sha256"]
    for record in continuation["continuations"]:
        if record["parent_artifact_sha256"] == original_essay_sha:
            record["parent_artifact_sha256"] = essay_sha
    _write_json(continuation_path, continuation)
    return essay


class ProMaxV2RoutingTests(unittest.TestCase):
    def test_contract_version_routes_review_inventory(self) -> None:
        self.assertNotIn("prose_review", checker._json_artifact_keys_for(1))
        self.assertIn("prose_review", checker._json_artifact_keys_for(2))
        self.assertNotIn(
            "promax-prose-review.json",
            checker._manifest_current_artifacts(1),
        )
        self.assertIn(
            "promax-prose-review.json",
            checker._manifest_current_artifacts(2),
        )

        v1_manifest = {
            "artifacts": [
                {"path": path, "status": "current"}
                for path in sorted(checker._manifest_current_artifacts(1))
            ]
        }
        v2_manifest = copy.deepcopy(v1_manifest)
        v2_manifest["artifacts"].append(
            {"path": "promax-prose-review.json", "status": "current"}
        )
        checker._validate_manifest_inventory_policy(v1_manifest, schema_version=1)
        checker._validate_manifest_inventory_policy(v2_manifest, schema_version=2)
        with self.assertRaisesRegex(ValueError, "missing"):
            checker._validate_manifest_inventory_policy(
                v1_manifest,
                schema_version=2,
            )
        with self.assertRaisesRegex(ValueError, "extra"):
            checker._validate_manifest_inventory_policy(
                v2_manifest,
                schema_version=1,
            )

    def test_v2_prose_validator_paths_do_not_change_v1_frozen_checks(self) -> None:
        v1_contract = {
            "schema_version": 1,
            "capabilities": {
                "validators": {
                    "validator_ids": ["schema", "output"],
                }
            },
        }
        _, v1_checks = checker._validator_checks(v1_contract, [], [])
        self.assertEqual(
            [check["validator_id"] for check in v1_checks],
            ["schema", "output"],
        )
        self.assertNotIn(
            "promax-prose-review.json",
            v1_checks[0]["checked_artifact_paths"],
        )

        v2_contract = {
            "schema_version": 2,
            "capabilities": {
                "validators": {
                    "validator_ids": ["schema", "output", "prose"],
                }
            },
        }
        failure = checker.machine_failure(
            error_type="prose_review_invalid",
            artifact="promax-prose-review.json",
            affected_phase="P10",
            repair_action="rewrite_reader_prose_and_rerun_prose_review",
        )
        _, v2_checks = checker._validator_checks(v2_contract, [failure], [])
        prose = next(
            check for check in v2_checks if check["validator_id"] == "prose"
        )
        self.assertEqual(prose["status"], "fail")
        self.assertEqual(
            prose["checked_artifact_paths"],
            [
                "promax-essay.md",
                "promax-position.locked.json",
                "promax-output-plan.locked.json",
                "promax-prose-review.json",
            ],
        )
        missing_prose = copy.deepcopy(v2_contract)
        missing_prose["capabilities"]["validators"]["validator_ids"] = [
            "schema",
            "output",
        ]
        with self.assertRaisesRegex(ValueError, "prose"):
            checker._validator_checks(missing_prose, [], [])

    def test_reader_output_failures_map_to_the_artifact_that_must_be_rebuilt(
        self,
    ) -> None:
        stale_type, stale_key = checker._semantic_error_type(
            "output",
            ValueError(
                "deliverable promax-essay.md does not match its current manifest hash"
            ),
        )
        self.assertEqual((stale_type, stale_key), ("manifest_stale", "essay"))

        cases = (
            (
                "reader_projection.reader_beats evidence_refs outside P9",
                "output_plan",
            ),
            (
                "reader-first essay contains a forbidden raw key/value ledger",
                "essay",
            ),
            (
                "concept atlas omits definition for V8-CANON-OBJECT",
                "concept_atlas",
            ),
            (
                "dossier omits exact position semantics",
                "dossier",
            ),
        )
        for message, expected_key in cases:
            with self.subTest(message=message):
                _, artifact_key = checker._semantic_error_type(
                    "output",
                    ValueError(message),
                )
                self.assertEqual(artifact_key, expected_key)

    def test_legacy_contract_does_not_load_the_v2_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _write_json(
                workspace / "promax-run-contract.json",
                {"schema_version": 1},
            )

            result = checker.validate_workspace(workspace, repo=ROOT)

        self.assertNotIn(
            "promax-prose-review.json",
            {failure["artifact"] for failure in result["failures"]},
        )


class ProMaxV2OutputBundleTests(unittest.TestCase):
    def test_reader_first_bundle_does_not_require_legacy_essay_ledgers(self) -> None:
        result = validate_output_bundle(**v2_bundle())

        self.assertEqual(result["status"], "valid")
        self.assertEqual(
            result["covered_concept_ids"],
            ["V8-CANON-BOUNDARY", "V8-CANON-OBJECT"],
        )

    def test_reader_projection_references_real_upstream_sets(self) -> None:
        bundle = v2_bundle()
        bundle["output_plan"]["reader_projection"]["reader_beats"][0][
            "evidence_refs"
        ] = ["EVIDENCE-GHOST"]

        with self.assertRaisesRegex(ValueError, "evidence_refs.*outside P9"):
            validate_output_bundle(**bundle)


class ProMaxV2CanonicalCheckerTests(unittest.TestCase):
    def materialize(self, workspace: Path) -> None:
        fixture_factory.materialize_fixture(
            ROOT,
            scenario_id="valid-complete",
            output=workspace,
        )

    def validate(self, workspace: Path) -> dict[str, object]:
        return checker.validate_workspace(
            workspace,
            repo=ROOT,
            final_chat=True,
            allow_test_fixture=True,
        )

    def test_current_v2_fixture_requires_and_accepts_the_internal_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)

            result = self.validate(workspace)

        self.assertEqual(result["overall_status"], "pass", result["diagnostics"])
        self.assertNotIn(
            "promax-prose-review.json",
            result["final_chat_projection"]["artifact_links"],
        )

    def test_missing_review_is_a_p10_prose_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)
            (workspace / "promax-prose-review.json").unlink()

            result = self.validate(workspace)

        review_failures = [
            failure
            for failure in result["failures"]
            if failure["artifact"] == "promax-prose-review.json"
        ]
        self.assertTrue(review_failures, result["diagnostics"])
        self.assertTrue(
            all(failure["affected_phase"] == "P10" for failure in review_failures)
        )
        self.assertTrue(
            all(
                failure["repair_action"]
                == "rewrite_reader_prose_and_rerun_prose_review"
                for failure in review_failures
            )
        )

    def test_review_hashes_must_match_current_essay_p8_and_p9(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)
            _rewrite_review_and_bind_manifest(
                workspace,
                lambda review: review.__setitem__("essay_sha256", "f" * 64),
            )

            result = self.validate(workspace)

        self.assertIn(
            {
                "error_type": "prose_review_invalid",
                "artifact": "promax-prose-review.json",
                "affected_phase": "P10",
                "downstream_reset": ["P10", "P11"],
                "repair_action": "rewrite_reader_prose_and_rerun_prose_review",
            },
            result["failures"],
        )

    def test_review_overall_fail_can_never_pass_the_canonical_checker(self) -> None:
        def fail_strongest_counterposition(review: dict[str, object]) -> None:
            dimension = review["dimensions"]["strongest_counterposition"]
            dimension["status"] = "fail"
            dimension["evidence_excerpts"] = []
            dimension["repair_target"] = "重写最强反方并重新审校。"
            review["overall_status"] = "fail"

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)
            _rewrite_review_and_bind_manifest(
                workspace,
                fail_strongest_counterposition,
            )

            result = self.validate(workspace)

        self.assertEqual(result["overall_status"], "fail")
        self.assertIn(
            "promax-prose-review.json",
            {failure["artifact"] for failure in result["failures"]},
        )

    def test_internal_review_cannot_be_a_continuation_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)
            manifest = json.loads(
                (workspace / "promax-artifact-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            continuation = json.loads(
                (workspace / "promax-continuation-ledger.json").read_text(
                    encoding="utf-8"
                )
            )
            review_record = next(
                artifact
                for artifact in manifest["artifacts"]
                if artifact["path"] == "promax-prose-review.json"
            )
            continuation["continuations"] = [
                {
                    "continuation_id": "CONT-REVIEW",
                    "sequence": 1,
                    "parent_artifact_sha256": review_record["sha256"],
                    "resume_from_phase": "P10",
                    "pending_artifact_paths": ["promax-essay-part-2.md"],
                    "reason": "平台边界截断。",
                    "status": "pending",
                }
            ]
            deliverables = {
                name: (workspace / name).read_text(encoding="utf-8")
                for name in (
                    "promax-dossier.md",
                    "promax-concept-atlas.md",
                    "promax-case-and-countercase.md",
                    "promax-essay.md",
                )
            }

            with self.assertRaisesRegex(ValueError, "delivered"):
                validate_continuation_lineage(
                    continuation,
                    manifest=manifest,
                    deliverables=deliverables,
                )

    def test_validator_report_attempts_never_rewrite_review_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "run"
            self.materialize(workspace)
            review_path = workspace / "promax-prose-review.json"
            original_review = review_path.read_bytes()

            first = checker.validate_workspace(
                workspace,
                repo=ROOT,
                final_chat=True,
                write_report=True,
                allow_test_fixture=True,
            )
            second = checker.validate_workspace(
                workspace,
                repo=ROOT,
                final_chat=True,
                write_report=True,
                allow_test_fixture=True,
            )
            final_review = review_path.read_bytes()

        self.assertEqual(first["validator_report"]["validation_attempt"], 1)
        self.assertEqual(second["validator_report"]["validation_attempt"], 2)
        self.assertEqual(final_review, original_review)
        prose_check = next(
            check
            for check in second["validator_report"]["checks"]
            if check["validator_id"] == "prose"
        )
        self.assertEqual(prose_check["status"], "pass")


if __name__ == "__main__":
    unittest.main()
