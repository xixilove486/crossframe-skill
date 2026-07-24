from __future__ import annotations

import hashlib
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
from promax_runtime.deliverables import validate_output_bundle  # noqa: E402
from tests import test_promax_artifacts as legacy  # noqa: E402
from tests.test_promax_v2_checker import (  # noqa: E402
    _append_essay_and_bind_manifest,
    _rewrite_review_and_bind_manifest,
    v2_bundle,
)


class ProMaxAdversarialReaderProseTests(unittest.TestCase):
    def test_old_long_machine_ledger_is_not_rescued_by_length(self) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] = (
            "position: 当前结构最符合机制甲。\n"
            "claim_id: CLAIM-CENTRAL\n"
            "concept_id: V8-CANON-OBJECT\n"
        ) * 700
        self.assertGreater(
            len(bundle["deliverables"]["promax-essay.md"]),
            48_000,
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(
            ValueError,
            "machine identifier|raw key/value",
        ):
            validate_output_bundle(**bundle)

    def test_readable_copy_cannot_hide_wrong_atlas_or_ghost_evidence(self) -> None:
        wrong_atlas = v2_bundle()
        wrong_atlas["deliverables"]["promax-concept-atlas.md"] = wrong_atlas[
            "deliverables"
        ]["promax-concept-atlas.md"].replace(
            "对象由被分析关系与排除范围共同界定。",
            "对象只是一个方便传播的固定标签。",
        )
        legacy.refresh_delivery_bindings(wrong_atlas)

        ghost_evidence = v2_bundle()
        ghost_evidence["output_plan"]["reader_projection"]["reader_beats"][0][
            "evidence_refs"
        ] = ["EVIDENCE-GHOST"]

        with self.assertRaisesRegex(ValueError, "definition"):
            validate_output_bundle(**wrong_atlas)
        with self.assertRaisesRegex(ValueError, "evidence_refs.*outside P9"):
            validate_output_bundle(**ghost_evidence)

    def test_very_long_natural_closure_is_only_advisory(self) -> None:
        bundle = v2_bundle()
        natural_paragraph = (
            "\n\n现实责任仍然落在能够观察损害的人身上，因为新的材料只会改变"
            "判断强度，不会自动生成行动授权；若退出成本上升，就应提前撤回。"
        )
        bundle["deliverables"]["promax-essay.md"] += natural_paragraph * 850
        self.assertGreater(
            len(bundle["deliverables"]["promax-essay.md"]),
            48_000,
        )
        legacy.refresh_delivery_bindings(bundle)

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")
        self.assertIn("essay_length_above_advisory", result["anomalies"])

    def test_machine_fields_leak_even_inside_otherwise_readable_copy(self) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            "\n\n这一段仍然自然。\nposition: 当前应继续观察\n"
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "raw key/value"):
            validate_output_bundle(**bundle)

    def test_control_plane_identifiers_leak_from_reader_copy(self) -> None:
        for marker in (
            "MECH-1",
            "SECTION-1",
            "BEAT-ENTRY",
            "EVIDENCE-1",
            "RETRIEVAL-1",
            "POSITION-LOCK",
        ):
            bundle = v2_bundle()
            bundle["deliverables"]["promax-essay.md"] += f"\n\n泄漏标记 {marker}。\n"
            legacy.refresh_delivery_bindings(bundle)
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(ValueError, "machine identifier"):
                    validate_output_bundle(**bundle)

    def test_app_ins_pipe_sentence_is_not_a_machine_field(self) -> None:
        bundle = v2_bundle()
        self.assertIn("APP-INS |", bundle["deliverables"]["promax-essay.md"])

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")


class ProMaxAdversarialReviewTests(unittest.TestCase):
    def test_semantic_review_rejects_unsupported_numbers_and_missing_countercase(
        self,
    ) -> None:
        for dimension_id in ("evidence_binding", "strongest_counterposition"):
            with self.subTest(dimension_id=dimension_id):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = Path(temp_dir) / "run"
                    fixture_factory.materialize_fixture(
                        ROOT,
                        scenario_id="valid-complete",
                        output=workspace,
                    )
                    unsupported_number_essay = None
                    if dimension_id == "evidence_binding":
                        unsupported_number_essay = _append_essay_and_bind_manifest(
                            workspace,
                            "\n\n没有来源的数字声称成功率已经达到 87.3%。\n",
                        )

                    def fail_dimension(review: dict[str, object]) -> None:
                        if unsupported_number_essay is not None:
                            review["essay_sha256"] = hashlib.sha256(
                                unsupported_number_essay.encode("utf-8")
                            ).hexdigest()
                        dimension = review["dimensions"][dimension_id]
                        dimension["status"] = "fail"
                        dimension["evidence_excerpts"] = []
                        dimension["repair_target"] = (
                            "删除无证据数字并补足证据绑定。"
                            if dimension_id == "evidence_binding"
                            else "重建最强反方及其失败条件。"
                        )
                        review["overall_status"] = "fail"

                    _rewrite_review_and_bind_manifest(
                        workspace,
                        fail_dimension,
                    )

                    result = checker.validate_workspace(
                        workspace,
                        repo=ROOT,
                        final_chat=True,
                        allow_test_fixture=True,
                    )

                self.assertEqual(result["overall_status"], "fail")
                review_failures = [
                    failure
                    for failure in result["failures"]
                    if failure["artifact"] == "promax-prose-review.json"
                ]
                self.assertTrue(review_failures, result["diagnostics"])
                self.assertTrue(
                    all(
                        failure["error_type"] == "prose_review_invalid"
                        for failure in review_failures
                    )
                )


if __name__ == "__main__":
    unittest.main()
