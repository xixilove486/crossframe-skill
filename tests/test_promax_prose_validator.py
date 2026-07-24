from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "crossframe-promax" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from promax_runtime.deliverables import (  # noqa: E402
    _continuous_semantic_paragraphs,
    validate_prose_review,
    validate_reader_projection,
    validate_v2_reader_documents,
)
from promax_runtime.jsonio import sha256_json  # noqa: E402


RUN_ID = "promax-prose-test"
SOURCE_SHA = "a" * 64
DIMENSION_IDS = (
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


def reader_projection() -> dict[str, object]:
    return {
        "article_type": "public-commentary",
        "house_voice_id": "crossframe-promax",
        "thesis_claim_id": "CLAIM-THESIS",
        "core_concept_ids": ["V8-CANON-OBJECT"],
        "atlas_only_concept_ids": ["V8-CANON-BOUNDARY"],
        "selected_techniques": [
            {
                "technique_id": "event-association",
                "tier": "core",
                "paragraph_action": "从现实矛盾进入",
                "section_ids": ["SEC-1"],
            },
            {
                "technique_id": "layered-argument",
                "tier": "core",
                "paragraph_action": "按机制依赖递进",
                "section_ids": ["SEC-1", "SEC-2"],
            },
            {
                "technique_id": "positive-negative-contrast",
                "tier": "core",
                "paragraph_action": "重建最强反方",
                "section_ids": ["SEC-2"],
            },
            {
                "technique_id": "finishing-touch",
                "tier": "auxiliary",
                "paragraph_action": "回到现实责任",
                "section_ids": ["SEC-2"],
            },
        ],
        "reader_beats": [
            {
                "beat_id": "BEAT-ENTRY",
                "function": "现实入口与中心命题",
                "section_ids": ["SEC-1"],
                "claim_ids": ["CLAIM-THESIS"],
                "mechanism_ids": ["MECH-1"],
                "evidence_refs": ["EVID-1"],
                "core_concept_ids": ["V8-CANON-OBJECT"],
                "technique_ids": ["event-association", "layered-argument"],
            },
            {
                "beat_id": "BEAT-BOUNDARY",
                "function": "最强反方、撤回与行动边界",
                "section_ids": ["SEC-2"],
                "claim_ids": ["CLAIM-COUNTER"],
                "mechanism_ids": ["MECH-2"],
                "evidence_refs": ["EVID-2"],
                "core_concept_ids": ["V8-CANON-OBJECT"],
                "technique_ids": [
                    "positive-negative-contrast",
                    "finishing-touch",
                ],
            },
        ],
    }


def projection_context() -> dict[str, object]:
    return {
        "applied_concept_ids": {
            "V8-CANON-OBJECT",
            "V8-CANON-BOUNDARY",
        },
        "section_ids": {"SEC-1", "SEC-2"},
        "claim_ids": {"CLAIM-THESIS", "CLAIM-COUNTER"},
        "mechanism_ids": {"MECH-1", "MECH-2"},
        "evidence_refs": {"EVID-1", "EVID-2"},
    }


def concept_registry() -> dict[str, object]:
    return {
        "concepts": [
            {
                "concept_id": "V8-CANON-OBJECT",
                "authoritative_name_zh": "对象边界",
                "definition": "对象由被分析关系与排除范围共同界定。",
            },
            {
                "concept_id": "V8-CANON-BOUNDARY",
                "authoritative_name_zh": "边界约束",
                "definition": "边界约束说明对象何时需要重新冻结。",
            },
        ]
    }


def dispositions() -> list[dict[str, object]]:
    return [
        {
            "concept_id": "V8-CANON-OBJECT",
            "status": "applied",
            "rationale": "它区分了当前分析对象与被转嫁的成本。",
            "misuses_excluded": ["不能把对象边界误写成固定标签。"],
            "required_neighbor_ids": ["V8-CANON-BOUNDARY"],
        },
        {
            "concept_id": "V8-CANON-BOUNDARY",
            "status": "applied",
            "rationale": "它规定了何时必须撤回当前判断。",
            "misuses_excluded": ["不能把边界约束当作行动授权。"],
            "required_neighbor_ids": ["V8-CANON-OBJECT"],
        },
    ]


def atlas() -> str:
    return """# 概念图谱

## V8-CANON-OBJECT | 对象边界
对象由被分析关系与排除范围共同界定。
它区分了当前分析对象与被转嫁的成本。
不能把对象边界误写成固定标签。
相邻概念是 V8-CANON-BOUNDARY。

## V8-CANON-BOUNDARY | 边界约束
边界约束说明对象何时需要重新冻结。
它规定了何时必须撤回当前判断。
不能把边界约束当作行动授权。
相邻概念是 V8-CANON-OBJECT。
"""


def position() -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SHA,
        "position": "当前应先做可撤回的小范围试验。",
        "judgment_strength": "moderate",
        "primary_reasons": ["现有证据支持先验证机制。"],
        "runner_up_explanation": "若成本已经不可逆，则停止试验是次优解释。",
        "strongest_counterevidence": ["试验本身可能扩大既有损害。"],
        "why_not_adopted": ["目前仍有可执行的停止条件。"],
        "withdrawal_conditions": ["一旦损害不可逆就撤回。"],
        "action_ceiling": "只允许准备，不构成现实授权。",
    }


def recommendation() -> dict[str, object]:
    return {
        "status": "locked",
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-EXIT",
        "ranking": ["OPTION-PROBE", "OPTION-EXIT"],
        "switch_conditions": ["损害不可逆时切换到退出。"],
        "inaction_consequences": ["不行动会继续转嫁成本。"],
        "authorization_status": "conditional_recommendation_only",
        "options": [
            {
                "option_id": "OPTION-PROBE",
                "description": "先做可撤回的小范围试验。",
            },
            {
                "option_id": "OPTION-EXIT",
                "description": "停止并退出当前路径。",
            },
        ],
    }


def essay() -> str:
    return """现实入口是试验成本正在被转嫁给无法退出的人。

当前应先做可撤回的小范围试验。对象边界这个区分让我们看到，收益与代价并没有落在同一批人身上。现有证据支持先验证机制。

最强的反对意见是试验本身可能扩大既有损害；若成本已经不可逆，就应停止并退出当前路径。当前仍有可执行的停止条件，一旦损害不可逆就撤回。这里只允许准备，不构成现实授权。

最后的问题不是怎样证明自己判断正确，而是谁承担下一次验证的代价。
"""


def dossier() -> str:
    values = [
        "推演档案",
        *string_leaves(position()),
        *string_leaves(recommendation()),
    ]
    return "\n".join(values)


def string_leaves(value: object) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for child in value.values():
            result.extend(string_leaves(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(string_leaves(child))
        return result
    return [value] if isinstance(value, str) and value else []


def output_plan() -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SHA,
        "reader_projection": reader_projection(),
    }


def prose_review() -> dict[str, object]:
    current_essay = essay()
    current_position = position()
    current_plan = output_plan()
    excerpt = "现实入口是试验成本正在被转嫁给无法退出的人。"
    return {
        "schema_id": "crossframe.promax.v8.prose-review",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SHA,
        "essay_sha256": hashlib.sha256(current_essay.encode("utf-8")).hexdigest(),
        "position_sha256": sha256_json(current_position),
        "output_plan_sha256": sha256_json(current_plan),
        "article_type": "public-commentary",
        "technique_ids": [
            "event-association",
            "layered-argument",
            "positive-negative-contrast",
            "finishing-touch",
        ],
        "required_beat_mappings": [
            {
                "beat_id": "BEAT-ENTRY",
                "section_ids": ["SEC-1"],
                "evidence_excerpts": [excerpt],
            },
            {
                "beat_id": "BEAT-BOUNDARY",
                "section_ids": ["SEC-2"],
                "evidence_excerpts": ["一旦损害不可逆就撤回。"],
            },
        ],
        "dimensions": {
            dimension_id: {
                "status": "pass",
                "evidence_excerpts": [dimension_excerpt],
                "repair_target": None,
            }
            for dimension_id, dimension_excerpt in zip(
                DIMENSION_IDS,
                (
                    "现实入口是试验成本正在被转嫁给无法退出的人。",
                    "当前应先做可撤回的小范围试验。对象边界这个区分让我们看到，收益与代价并没有落在同一批人身上。现有证据支持先验证机制。",
                    "对象边界这个区分让我们看到，收益与代价并没有落在同一批人身上。",
                    "现有证据支持先验证机制。",
                    "最强的反对意见是试验本身可能扩大既有损害；若成本已经不可逆，就应停止并退出当前路径。",
                    "若成本已经不可逆，就应停止并退出当前路径。",
                    "当前应先做可撤回的小范围试验。",
                    "一旦损害不可逆就撤回。",
                    "最后的问题不是怎样证明自己判断正确，而是谁承担下一次验证的代价。",
                    "当前仍有可执行的停止条件，一旦损害不可逆就撤回。",
                    "这里只允许准备，不构成现实授权。",
                ),
            )
        },
        "overall_status": "pass",
        "reviewed_at": "2026-07-25T08:00:00Z",
    }


class ProMaxReaderProjectionTests(unittest.TestCase):
    def test_projection_closes_concepts_techniques_and_p9_references(self) -> None:
        result = validate_reader_projection(
            reader_projection(),
            **projection_context(),
        )

        self.assertEqual(result["article_type"], "public-commentary")
        self.assertEqual(len(result["selected_techniques"]), 4)

    def test_core_and_atlas_only_concepts_are_an_exact_partition(self) -> None:
        overlap = reader_projection()
        overlap["atlas_only_concept_ids"].append("V8-CANON-OBJECT")
        incomplete = reader_projection()
        incomplete["atlas_only_concept_ids"] = []

        for candidate in (overlap, incomplete):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(
                    ValueError,
                    "core_concept_ids.*atlas_only_concept_ids|applied",
                ):
                    validate_reader_projection(candidate, **projection_context())

    def test_beat_references_must_come_from_p9_and_selected_techniques(self) -> None:
        mutations = (
            ("claim_ids", "CLAIM-UNKNOWN"),
            ("mechanism_ids", "MECH-UNKNOWN"),
            ("evidence_refs", "EVID-UNKNOWN"),
            ("technique_ids", "TECH-UNKNOWN"),
        )
        for field, unknown in mutations:
            candidate = reader_projection()
            candidate["reader_beats"][0][field] = [unknown]
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    validate_reader_projection(candidate, **projection_context())

    def test_projection_requires_exactly_three_core_techniques(self) -> None:
        candidate = reader_projection()
        candidate["selected_techniques"][2]["tier"] = "auxiliary"

        with self.assertRaisesRegex(ValueError, "three core"):
            validate_reader_projection(candidate, **projection_context())

    def test_projection_rejects_unknown_and_wrong_genre_techniques(self) -> None:
        unknown = reader_projection()
        unknown["selected_techniques"][0]["technique_id"] = "TECH-UNKNOWN"
        unknown["reader_beats"][0]["technique_ids"][0] = "TECH-UNKNOWN"
        wrong_genre = reader_projection()
        wrong_genre["selected_techniques"] = [
            {
                "technique_id": technique_id,
                "tier": "core",
                "paragraph_action": "保持既有判断，只调整读者进入顺序。",
                "section_ids": ["SEC-1"],
            }
            for technique_id in (
                "analogical-reasoning",
                "split-wood-reasoning",
                "virtual-to-real",
            )
        ]

        for candidate in (unknown, wrong_genre):
            with self.subTest(candidate=candidate["selected_techniques"][0]):
                with self.assertRaisesRegex(
                    ValueError,
                    "technique|route|article_type",
                ):
                    validate_reader_projection(candidate, **projection_context())


class ProMaxReaderDocumentTests(unittest.TestCase):
    def validate_documents(
        self,
        *,
        essay_text: str | None = None,
        atlas_text: str | None = None,
        dossier_text: str | None = None,
    ) -> dict[str, object]:
        return validate_v2_reader_documents(
            reader_projection=reader_projection(),
            concept_registry=concept_registry(),
            dispositions=dispositions(),
            atlas=atlas() if atlas_text is None else atlas_text,
            essay=essay() if essay_text is None else essay_text,
            dossier=dossier() if dossier_text is None else dossier_text,
            position=position(),
            recommendation=recommendation(),
            recommendation_required=True,
        )

    def test_natural_pipe_sentence_is_not_discarded_as_a_machine_ledger(self) -> None:
        paragraphs = _continuous_semantic_paragraphs(
            "APP-INS | 这个普通自然句因为解释了关系，所以应被保留。"
        )

        self.assertEqual(
            paragraphs,
            ["APP-INS | 这个普通自然句因为解释了关系，所以应被保留。"],
        )

    def test_v2_essay_needs_only_core_name_while_atlas_closes_every_definition(self) -> None:
        result = self.validate_documents()

        self.assertEqual(
            result["core_concept_ids"],
            ["V8-CANON-OBJECT"],
        )
        self.assertNotIn(
            "对象由被分析关系与排除范围共同界定。",
            essay(),
        )
        self.assertNotIn("V8-CANON-OBJECT", essay())
        self.assertIn("OPTION-PROBE", dossier())

    def test_essay_rejects_machine_ids_ledgers_and_repeated_run_scaffolding(self) -> None:
        mutations = (
            essay() + "\nV8-CANON-OBJECT",
            essay() + "\nCLAIM-THESIS",
            essay() + "\nOPTION-PROBE",
            essay() + "\n正文泄漏CLAIM-THESIS。",
            essay() + "\nposition: 当前应先做可撤回的小范围试验。",
            essay() + "\n在本题中如此。在本轮中如此。在本运行中仍如此。",
        )
        for candidate in mutations:
            with self.subTest(candidate=candidate[-80:]):
                with self.assertRaisesRegex(
                    ValueError,
                    "machine identifier|key/value|run-scaffolding",
                ):
                    self.validate_documents(essay_text=candidate)

    def test_essay_cannot_name_an_atlas_only_concept(self) -> None:
        candidate = essay() + "\n边界约束也在正文中被命名。"

        with self.assertRaisesRegex(ValueError, "atlas-only"):
            self.validate_documents(essay_text=candidate)

    def test_atlas_must_close_every_applied_definition(self) -> None:
        candidate = atlas().replace("边界约束说明对象何时需要重新冻结。", "")

        with self.assertRaisesRegex(ValueError, "atlas.*definition"):
            self.validate_documents(atlas_text=candidate)

    def test_dossier_owns_exact_position_and_recommendation_fields(self) -> None:
        for missing in (
            position()["action_ceiling"],
            recommendation()["preferred_option_id"],
        ):
            candidate = dossier().replace(str(missing), "")
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(
                    ValueError,
                    "dossier.*position|dossier.*recommendation",
                ):
                    self.validate_documents(dossier_text=candidate)


class ProMaxProseReviewTests(unittest.TestCase):
    def validate_review(self, candidate: dict[str, object]) -> dict[str, object]:
        return validate_prose_review(
            candidate,
            essay=essay(),
            position=position(),
            output_plan=output_plan(),
            run_id=RUN_ID,
            source_snapshot_sha256=SOURCE_SHA,
        )

    def test_current_complete_review_passes(self) -> None:
        result = self.validate_review(prose_review())

        self.assertEqual(result["overall_status"], "pass")
        self.assertEqual(set(result["dimensions"]), set(DIMENSION_IDS))

    def test_review_is_bound_to_current_bytes_p8_p9_run_and_source(self) -> None:
        mutations = (
            ("essay_sha256", "b" * 64),
            ("position_sha256", "b" * 64),
            ("output_plan_sha256", "b" * 64),
            ("run_id", "other-run"),
            ("source_snapshot_sha256", "b" * 64),
        )
        for field, value in mutations:
            candidate = prose_review()
            candidate[field] = value
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    self.validate_review(candidate)

        stale_plan = output_plan()
        stale_plan["run_id"] = "other-run"
        candidate = prose_review()
        candidate["output_plan_sha256"] = sha256_json(stale_plan)
        with self.assertRaisesRegex(ValueError, "output_plan.*run_id"):
            validate_prose_review(
                candidate,
                essay=essay(),
                position=position(),
                output_plan=stale_plan,
                run_id=RUN_ID,
                source_snapshot_sha256=SOURCE_SHA,
            )

    def test_review_article_type_and_techniques_match_reader_projection(self) -> None:
        wrong_type = prose_review()
        wrong_type["article_type"] = "reply"
        wrong_techniques = prose_review()
        wrong_techniques["technique_ids"] = ["TECH-ENTRY"]

        for candidate in (wrong_type, wrong_techniques):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, "article_type|technique_ids"):
                    self.validate_review(candidate)

    def test_review_has_exactly_eleven_dimensions_and_consistent_overall_status(self) -> None:
        missing = prose_review()
        missing["dimensions"].pop("audit_leakage")
        extra = prose_review()
        extra["dimensions"]["invented_dimension"] = copy.deepcopy(
            extra["dimensions"]["audit_leakage"]
        )
        false_pass = prose_review()
        false_pass["dimensions"]["audit_leakage"]["status"] = "fail"
        false_pass["dimensions"]["audit_leakage"]["repair_target"] = "P10"

        for candidate in (missing, extra, false_pass):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(
                    ValueError,
                    "eleven prose-review dimensions|overall_status",
                ):
                    self.validate_review(candidate)

    def test_every_excerpt_exists_verbatim_and_every_reader_beat_is_mapped(self) -> None:
        invented_excerpt = prose_review()
        invented_excerpt["dimensions"]["evidence_binding"]["evidence_excerpts"] = [
            "正文里从未出现的摘录"
        ]
        missing_beat = prose_review()
        missing_beat["required_beat_mappings"].pop()

        for candidate in (invented_excerpt, missing_beat):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(
                    ValueError,
                    "evidence_excerpt|reader beat",
                ):
                    self.validate_review(candidate)

    def test_review_rejects_one_excerpt_claimed_for_every_dimension(self) -> None:
        candidate = prose_review()
        excerpt = "现实入口是试验成本正在被转嫁给无法退出的人。"
        for dimension in candidate["dimensions"].values():
            dimension["evidence_excerpts"] = [excerpt]

        with self.assertRaisesRegex(
            ValueError,
            "excerpt|dimension|reuse|distinct",
        ):
            self.validate_review(candidate)


if __name__ == "__main__":
    unittest.main()
