from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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


def _materialize_with_fresh_review(
    workspace: Path,
    transform,
) -> dict[str, object]:
    original = fixture_factory.build_deliverables

    def tampered(*args, **kwargs):
        deliverables = original(*args, **kwargs)
        deliverables["promax-essay.md"] = transform(
            deliverables["promax-essay.md"]
        )
        return deliverables

    with mock.patch.object(
        fixture_factory,
        "build_deliverables",
        side_effect=tampered,
    ):
        fixture_factory.materialize_fixture(
            ROOT,
            scenario_id="valid-complete",
            output=workspace,
        )
    return checker.validate_workspace(
        workspace,
        repo=ROOT,
        final_chat=True,
        allow_test_fixture=True,
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

    def test_app_ins_colon_sentence_is_not_a_machine_field(self) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            "\n\nAPP-INS：制度与公共治理这个术语提醒我们追问责任链。\n"
        )
        legacy.refresh_delivery_bindings(bundle)

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")

    def test_control_plane_hashes_and_validator_markers_never_enter_reader_copy(
        self,
    ) -> None:
        for marker in (
            "a" * 64,
            "crossframe-promax-artifact-checker/1",
        ):
            bundle = v2_bundle()
            bundle["deliverables"]["promax-essay.md"] += (
                f"\n\n这一段泄漏了内部控制标记 {marker}。\n"
            )
            legacy.refresh_delivery_bindings(bundle)
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(
                    ValueError,
                    "control-plane|machine identifier",
                ):
                    validate_output_bundle(**bundle)

    def test_reader_beats_must_close_claim_mechanism_evidence_and_prose_roles(
        self,
    ) -> None:
        bundle = v2_bundle()
        beat = bundle["output_plan"]["reader_projection"]["reader_beats"][0]
        beat["function"] = "结尾。"
        for field in (
            "mechanism_ids",
            "evidence_refs",
            "core_concept_ids",
            "technique_ids",
        ):
            beat[field] = []

        with self.assertRaisesRegex(ValueError, "reader beat|coverage|close"):
            validate_output_bundle(**bundle)

    def test_numeric_claims_require_upstream_provenance_or_explicit_hypothesis(
        self,
    ) -> None:
        sourced = v2_bundle()
        sourced["retrieval_ledger"]["entries"][0]["finding"] = (
            "来源记录的成功率为 87.3%。"
        )
        sourced["deliverables"]["promax-essay.md"] += (
            "\n\n来源记录的成功率为 87.3%，因此该数字只支撑有限判断。\n"
        )
        legacy.refresh_delivery_bindings(sourced)

        hypothetical = v2_bundle()
        hypothetical["deliverables"]["promax-essay.md"] += (
            "\n\n假设成功率为 87.3%，结论仍需接受退出条件约束。\n"
        )
        legacy.refresh_delivery_bindings(hypothetical)

        for bundle in (sourced, hypothetical):
            with self.subTest(essay=bundle["deliverables"]["promax-essay.md"][-80:]):
                result = validate_output_bundle(**bundle)
                self.assertEqual(result["status"], "valid")

    def test_urls_footnotes_and_list_ordinals_are_not_numeric_claims(self) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            "\n\n1. 参考资料[12]可见于 https://example.org/report/2024，"
            "这里没有把编号当成事实比例。\n"
        )
        legacy.refresh_delivery_bindings(bundle)

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")

    def test_quoted_or_indented_json_ledgers_cannot_enter_reader_prose(self) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            '\n\n{\n  "position": "内部立场字段",\n'
            '  "judgment_strength": "high",\n'
            '  "repair_target": "P10"\n}\n'
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "key/value|control-plane|ledger"):
            validate_output_bundle(**bundle)

    def test_url_mask_stops_before_chinese_punctuation_and_numeric_claims(
        self,
    ) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            "\n\n资料见 https://example.org/report/2024，"
            "成功率已经精确达到87.3%。\n"
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "unsupported numeric claim"):
            validate_output_bundle(**bundle)

    def test_single_digit_counts_and_multipliers_need_numeric_provenance(
        self,
    ) -> None:
        bundle = v2_bundle()
        bundle["deliverables"]["promax-essay.md"] += (
            "\n\n没有任何来源，但这里断言已有9人死亡，而且风险扩大了9倍。\n"
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "unsupported numeric claim"):
            validate_output_bundle(**bundle)

    def test_source_anchors_cannot_rescue_a_wrong_core_concept_definition(
        self,
    ) -> None:
        bundle = v2_bundle()
        essay = bundle["deliverables"]["promax-essay.md"]
        original = (
            "对象边界要求先说明分析关系与排除范围，"
            "再问清楚谁被纳入判断、谁承担代价；"
        )
        replacement = (
            "对象边界说明分析关系与排除范围都只是装饰，"
            "真正边界完全由段落字数决定，这会导致现实后果；"
        )
        self.assertIn(original, essay)
        bundle["deliverables"]["promax-essay.md"] = essay.replace(
            original,
            replacement,
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "concept|v8|meaning"):
            validate_output_bundle(**bundle)

    def test_reader_prose_cannot_reverse_the_locked_position_and_recommendation(
        self,
    ) -> None:
        bundle = v2_bundle()
        essay = bundle["deliverables"]["promax-essay.md"]
        self.assertIn("当前结构最符合机制甲。", essay)
        bundle["deliverables"]["promax-essay.md"] = essay.replace(
            "当前结构最符合机制甲。",
            "我的判断是：当前结构最不符合机制甲，"
            "首选应永久禁止一切试验，次选也是维持禁令。",
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(
            ValueError,
            "stance|position|recommendation|judgment",
        ):
            validate_output_bundle(**bundle)

    def test_declaring_that_no_counterposition_exists_is_not_a_strongest_counter(
        self,
    ) -> None:
        bundle = v2_bundle()
        essay = bundle["deliverables"]["promax-essay.md"]
        original = "最强的反对意见是试验本身会扩大既有损害。"
        replacement = (
            "最强的反对意见根本不存在，没有任何观点足以构成反方。"
        )
        self.assertIn(original, essay)
        bundle["deliverables"]["promax-essay.md"] = essay.replace(
            original,
            replacement,
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "counter|反方"):
            validate_output_bundle(**bundle)

    def test_first_reader_paragraph_rejects_internal_mechanism_labels(self) -> None:
        bundle = v2_bundle()
        essay = bundle["deliverables"]["promax-essay.md"]
        original = "现实中的冲突不是术语不够多，"
        replacement = "现实中的冲突已经被框架机制甲预先命名，"
        self.assertIn(original, essay)
        bundle["deliverables"]["promax-essay.md"] = essay.replace(
            original,
            replacement,
        )
        legacy.refresh_delivery_bindings(bundle)

        with self.assertRaisesRegex(ValueError, "first paragraph|framework terminology"):
            validate_output_bundle(**bundle)

    def test_fair_counterwording_is_not_misread_as_counter_dismissal(self) -> None:
        bundle = v2_bundle()
        essay = bundle["deliverables"]["promax-essay.md"]
        original = "最强的反对意见是试验本身会扩大既有损害。"
        self.assertIn(original, essay)
        bundle["deliverables"]["promax-essay.md"] = essay.replace(
            original,
            "最强反方不需要被立即否定；" + original,
        )
        legacy.refresh_delivery_bindings(bundle)

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")


class ProMaxAdversarialReviewTests(unittest.TestCase):
    def test_fresh_forged_review_cannot_rescue_semantically_invalid_prose(
        self,
    ) -> None:
        def audit_body_over_48k(essay: str) -> str:
            paragraph = (
                "\n\n审校记录说明，这一段只是在逐项声称文章已经通过现实入口、"
                "证据绑定、最强反方、公平比较、固定声口和泄漏检查，"
                "却没有继续向读者展开问题本身。"
            )
            return essay + paragraph * (50_000 // len(paragraph) + 10)

        def wrong_core_concept(essay: str) -> str:
            old = (
                "A* 行动者候选状态不是永久身份标签；"
                "它只是在当前观察窗和证据边界内保留未知项的一份候选描述。"
            )
            new = (
                "A* 行动者候选状态意味着对象一经命名就永远固定，"
                "任何变化都可直接证明转移机制为真。"
            )
            self.assertIn(old, essay)
            return essay.replace(old, new)

        def unsupported_precise_number(essay: str) -> str:
            return essay + (
                "\n\n没有任何上游来源支持，"
                "但这里断言成功率已经精确达到 87.3%。"
            )

        def remove_strongest_counterposition(essay: str) -> str:
            old = (
                "最强的反对意见是：对象边界本身可能不稳定，"
                "所谓转移只是重新划分对象后的视觉效果。"
            )
            new = (
                "所有反对意见都不值一提。"
                "反方无需获得成立条件。"
                "当前结论也不需要任何撤回路径。"
            )
            self.assertIn(old, essay)
            return essay.replace(old, new)

        for transform in (
            audit_body_over_48k,
            wrong_core_concept,
            unsupported_precise_number,
            remove_strongest_counterposition,
        ):
            with self.subTest(transform=transform.__name__):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = Path(temp_dir) / "run"
                    result = _materialize_with_fresh_review(
                        workspace,
                        transform,
                    )

                self.assertEqual(
                    result["overall_status"],
                    "fail",
                    result["diagnostics"],
                )

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
