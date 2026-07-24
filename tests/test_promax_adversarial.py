from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.deliverables import validate_final_chat
from promax_runtime.artifacts import (
    ROLE_IDS,
    build_capability_disclosure,
    build_role_plan,
)
from promax_runtime.jsonio import sha256_json
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


RUN_ID = "promax-final-chat-test"
RUN_NONCE = "r" * 64
REQUEST_SHA256 = hashlib.sha256(b"promax-final-chat-request").hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_contract() -> dict[str, object]:
    capabilities = build_capability_disclosure(
        subagents_available=False,
        max_parallelism=0,
        validator_ids=("schema",),
    )
    return {
        "schema_id": "crossframe.promax.v8.run-contract",
        "schema_version": 1,
        "framework_version": "v8.0",
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": REQUEST_SHA256,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "mode": "promax-complete",
        "recommendation_required": True,
        "blocker": None,
        "requested_skill_names": ["crossframe-promax"],
        "routing_conflict": {
            "detected": False,
            "conflicting_names": [],
            "resolved_to": "crossframe-promax",
            "priority_rule": "routing-priority-crossframe-promax-over-crossframe-max-no-fallback",
            "fallback_allowed": False,
        },
        "capabilities": capabilities,
        "orchestration_mode": "single-agent-separated",
        "role_plan": build_role_plan(capabilities),
        "budgets": {
            "paragraphs": 3863,
            "tables": 117,
            "registry_concepts": 709,
            "minimum_red_team_rounds": 2,
            "minimum_no_novelty_rounds": 2,
        },
        "completion_criteria": [
            "source-closure",
            "concept-closure",
            "claim-path-closure",
            "retrieval-and-counterexample-closure",
            "position-lock",
            "output-and-validator-closure",
        ],
        "created_at": "2026-07-23T06:00:00Z",
    }


def position() -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.position",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-1",
        "relation_to_proposition": "supports",
        "proposition_verdict": "VERDICT[supports] 当前条件下，机制甲是最合理解释。",
        "position": "当前条件下，机制甲是最合理解释。",
        "judgment_strength": "moderate",
        "primary_reasons": ["当前结构最符合机制甲。"],
        "runner_up_explanation": "机制乙在对象边界改变时成为次优解释。",
        "strongest_counterevidence": ["对象边界并不稳定"],
        "why_not_adopted": ["现有证据尚未证明对象边界已经改变"],
        "withdrawal_conditions": [
            "若对象边界并不稳定得到新证据证实，则撤回当前判断。"
        ],
        "action_ceiling": "不授权现实行动，现实处置需另行授权。",
        "locked_at": "2026-07-23T04:00:00Z",
    }


def deliverables() -> dict[str, str]:
    return {
        "promax-dossier.md": "# 推演档案\n结构化审计记录。\n",
        "promax-concept-atlas.md": "# 概念图谱\nv8 概念解释。\n",
        "promax-case-and-countercase.md": "# 案例与反例\n结构案例。\n",
        "promax-essay.md": (
            "# 完整正文\n当前条件下，机制甲是最合理解释。"
            "若对象边界并不稳定得到新证据证实，则撤回当前判断。\n"
        ),
    }


def manifest(contents: dict[str, str]) -> dict[str, object]:
    contract = run_contract()
    role_records = []
    for index, role_id in enumerate(ROLE_IDS, start=1):
        input_ref = {
            "path": f"inputs/{index}.json",
            "sha256": "a" * 64,
            "media_type": "application/json",
        }
        role_records.append(
            {
                "role_id": role_id,
                "sequence": index,
                "execution_mode": "single-agent-separated",
                "exchange_protocol": "structured-artifacts-only",
                "input_artifacts": [input_ref],
                "observed_input_artifacts": [input_ref],
                "output_artifacts": [
                    {
                        "path": f"outputs/{index}.json",
                        "sha256": "c" * 64,
                        "media_type": "application/json",
                    }
                ],
                "status": "completed",
            }
        )
    body: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.artifact-manifest",
        "schema_version": 1,
        "run_id": RUN_ID,
        "run_nonce": contract["run_nonce"],
        "request_sha256": contract["request_sha256"],
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "run_contract_sha256": sha256_json(contract),
        "mode": contract["mode"],
        "orchestration_mode": contract["orchestration_mode"],
        "role_records": role_records,
        "phase_chain_head_sha256": "b" * 64,
        "artifacts": [
            {
                "path": path,
                "sha256": text_sha(text),
                "media_type": "text/markdown",
                "generating_phase": "P10",
                "input_artifact_sha256s": ["a" * 64],
                "status": "current",
            }
            for path, text in sorted(contents.items())
        ],
        "generated_at": "2026-07-23T06:15:00Z",
    }
    return {**body, "manifest_sha256": sha256_json(body)}


def continuation(manifest_record: dict[str, object], contents: dict[str, str]) -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.continuation-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "parent_manifest_sha256": manifest_record["manifest_sha256"],
        "continuations": [
            {
                "continuation_id": "CONT-1",
                "sequence": 1,
                "parent_artifact_sha256": text_sha(contents["promax-essay.md"]),
                "resume_from_phase": "P10",
                "pending_artifact_paths": ["promax-essay-part-2.md"],
                "reason": "平台输出边界先耗尽",
                "status": "pending",
            }
        ],
        "updated_at": "2026-07-23T06:30:00Z",
    }


def context() -> dict[str, object]:
    contents = deliverables()
    manifest_record = manifest(contents)
    return {
        "run_contract": run_contract(),
        "position": position(),
        "manifest": manifest_record,
        "continuation_ledger": continuation(manifest_record, contents),
        "validated_output": {
            "status": "valid",
            "anomalies": ["essay_length_below_advisory"],
            "covered_concept_ids": ["V8-CANON-OBJECT"],
            "manifest_sha256": manifest_record["manifest_sha256"],
            "position_sha256": sha256_json(position()),
        },
    }


def final_chat() -> dict[str, object]:
    return {
        "run_status": "promax-complete",
        "center_judgment_summary": "当前条件下，机制甲是最合理解释。",
        "key_withdrawal_conditions": [
            "若对象边界并不稳定得到新证据证实，则撤回当前判断。"
        ],
        "artifact_links": [
            "promax-essay.md",
            "promax-dossier.md",
            "promax-concept-atlas.md",
            "promax-case-and-countercase.md",
        ],
        "continuation_entry": "CONT-1",
    }


class ProMaxFinalChatContractTests(unittest.TestCase):
    def test_exact_five_category_delivery_index_passes(self) -> None:
        result = validate_final_chat(final_chat(), **context())
        self.assertEqual(set(result), {
            "run_status",
            "center_judgment_summary",
            "key_withdrawal_conditions",
            "artifact_links",
            "continuation_entry",
        })

    def test_chat_cannot_replace_the_essay_or_add_an_extra_category(self) -> None:
        candidate = final_chat()
        candidate["full_answer"] = "这里直接塞入完整正文"
        with self.assertRaises(ValueError):
            validate_final_chat(candidate, **context())

        invalid_context = context()
        invalid_context["validated_output"] = {"status": "not_validated"}
        with self.assertRaises(ValueError):
            validate_final_chat(final_chat(), **invalid_context)

    def test_hidden_reasoning_is_rejected_at_any_depth(self) -> None:
        candidate = final_chat()
        candidate["artifact_links"] = {
            "promax-essay.md": "promax-essay.md",
            "metadata": {"chain_of_thought": "private scratchpad"},
        }
        with self.assertRaises(ValueError):
            validate_final_chat(candidate, **context())

    def test_links_must_be_current_and_include_the_independent_essay(self) -> None:
        for links in (
            ["promax-dossier.md"],
            ["promax-essay.md", "stale-essay.md"],
        ):
            candidate = final_chat()
            candidate["artifact_links"] = links
            with self.subTest(links=links):
                with self.assertRaises(ValueError):
                    validate_final_chat(candidate, **context())

    def test_continuation_and_position_summary_are_bound_to_locked_state(self) -> None:
        cases: list[dict[str, object]] = []

        wrong_continuation = final_chat()
        wrong_continuation["continuation_entry"] = "CONT-OLD"
        cases.append(wrong_continuation)

        missing_position = final_chat()
        missing_position["center_judgment_summary"] = "暂不表达判断。"
        cases.append(missing_position)

        invented_withdrawal = final_chat()
        invented_withdrawal["key_withdrawal_conditions"] = ["若天气变化则撤回"]
        cases.append(invented_withdrawal)

        authorization_leak = final_chat()
        authorization_leak["center_judgment_summary"] += " 已授权立即执行。"
        cases.append(authorization_leak)

        wrong_status = final_chat()
        wrong_status["run_status"] = "promax-artifact-run"
        cases.append(wrong_status)

        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_final_chat(candidate, **context())


if __name__ == "__main__":
    unittest.main()
