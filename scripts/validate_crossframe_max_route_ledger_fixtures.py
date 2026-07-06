from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

from check_crossframe_max_artifacts import (
    REQUIRED_DOSSIER_HEADINGS,
    REQUIRED_DOSSIER_MARKERS,
    REQUIRED_ESSAY_MARKERS,
    REQUIRED_FULL_SOURCE_FILES,
    REQUIRED_INDEX_MARKERS,
    REQUIRED_LEDGER_MARKERS,
    REQUIRED_MANIFEST_MARKERS,
    check_crossframe_max_artifacts,
)
from check_crossframe_max_read_ledger import EXPECTED_FILE_RANGES, EXPECTED_TOTAL_PARAGRAPHS
from check_crossframe_max_route_ledgers import (
    check,
    paragraph_range_tuple,
    parse_contract_map,
    parse_registry_anchor_map,
)


SKILL_DESIGN_CONCEPTS = [
    "工具准入",
    "过程性产物边界",
    "开放断言",
    "命题验证表",
    "强判断八件套",
    "观测反身性",
    "反模型殖民",
    "概念武器化",
]

SKILL_DESIGN_LAYERS = [
    "01-guide.md",
    "02-boundary-layer.md",
    "05-interface-layer.md",
    "06-tool-layer.md",
    "09-governance-layer.md",
]

SKILL_DESIGN_OUTPUTS = [
    "max-local-world-model",
    "max-concept-graph",
    "max-evidence-reasoning-audit",
    "max-red-team-pass",
]

SKILL_DESIGN_FORBIDDEN_OUTPUTS = [
    "把 prompt 当作概念本体",
    "让运行入口吞掉长协议",
    "让工具输出越过行动上限",
]

ROUTE_FIXTURES = {
    "skill_design": {
        "concepts": SKILL_DESIGN_CONCEPTS,
        "layers": SKILL_DESIGN_LAYERS,
        "outputs": SKILL_DESIGN_OUTPUTS,
        "forbidden_outputs": SKILL_DESIGN_FORBIDDEN_OUTPUTS,
        "design": True,
    },
    "meaning_question": {
        "concepts": ["开放性承担行动", "时间不可逆", "演化记忆", "有序退场", "不可穷尽声明", "正当不透明"],
        "layers": ["03-world-layer.md", "04-state-layer.md", "09-governance-layer.md"],
        "outputs": [
            "max-worldview-capsule",
            "max-path-confidence-layers",
            "max-transcendence-window",
            "max-red-team-pass",
        ],
        "forbidden_outputs": ["把不可解释直接升格为爱", "把世界观解释写成现实终审"],
        "design": False,
    },
    "history_analysis": {
        "concepts": [
            "时间不可逆",
            "演化记忆",
            "状态坐标与生命周期",
            "非线性路径库",
            "路径置信分层",
            "观测反身性",
            "强判断八件套",
            "来源-证据-判断-行动上限",
        ],
        "layers": [
            "02-boundary-layer.md",
            "03-world-layer.md",
            "04-state-layer.md",
            "05-interface-layer.md",
            "06-tool-layer.md",
            "08-application-layer.md",
            "09-governance-layer.md",
        ],
        "outputs": [
            "max-source-frontier",
            "max-path-tree",
            "max-path-confidence-layers",
            "max-red-team-pass",
            "max-unexhaustible-declaration",
        ],
        "forbidden_outputs": ["把框架推演写成史实", "把单一路径写成历史必然", "忽略档案缺口和沉默主体"],
        "design": False,
    },
    "document_question": {
        "concepts": [
            "解释准入",
            "工具准入",
            "过程性产物边界",
            "来源-证据-判断-行动上限",
            "正当不透明",
            "不可穷尽声明",
        ],
        "layers": [
            "00-source-envelope.md",
            "01-guide.md",
            "02-boundary-layer.md",
            "03-world-layer.md",
            "04-state-layer.md",
            "05-interface-layer.md",
            "06-tool-layer.md",
            "07-intervention-layer.md",
            "08-application-layer.md",
            "09-governance-layer.md",
        ],
        "outputs": ["max-full-source-read-ledger", "max-concept-graph", "max-evidence-reasoning-audit"],
        "forbidden_outputs": ["用摘要替代原文段落回指", "跳过表格结构只看段落文本", "把文档定位回答写成现实判断"],
        "design": False,
    },
}

ROUTE_CONCEPTS = SKILL_DESIGN_CONCEPTS
_REGISTRY_ANCHOR_MAP: dict[str, set[str]] | None = None
_CONTRACT_MAP: dict[str, dict[str, object]] | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_anchor_map() -> dict[str, set[str]]:
    global _REGISTRY_ANCHOR_MAP
    if _REGISTRY_ANCHOR_MAP is None:
        anchor_map, errors = parse_registry_anchor_map(
            repo_root() / "skills" / "crossframe-max" / "references" / "concept-registry" / "index.md"
        )
        if errors:
            raise AssertionError(f"registry anchor map failed: {errors}")
        _REGISTRY_ANCHOR_MAP = anchor_map
    return _REGISTRY_ANCHOR_MAP


def contract_map() -> dict[str, dict[str, object]]:
    global _CONTRACT_MAP
    if _CONTRACT_MAP is None:
        contracts, errors = parse_contract_map(
            repo_root()
            / "skills"
            / "crossframe-max"
            / "references"
            / "concept-contracts"
            / "v6-contract-map.json"
        )
        if errors:
            raise AssertionError(f"contract map failed: {errors}")
        _CONTRACT_MAP = contracts
    return _CONTRACT_MAP


def contract_id_for_concept(concept: str) -> str:
    entry = contract_map().get(concept)
    if not entry or not isinstance(entry.get("contract_id"), str):
        raise AssertionError(f"missing contract map entry for fixture concept: {concept}")
    return entry["contract_id"]


def sorted_anchor_ranges(concept: str) -> list[str]:
    ranges = registry_anchor_map().get(concept)
    if not ranges:
        raise AssertionError(f"missing registry anchors for fixture concept: {concept}")
    return sorted(ranges, key=lambda value: paragraph_range_tuple(value) or (9999, 9999))


def first_source_id(ranges: list[str]) -> str:
    parsed = paragraph_range_tuple(ranges[0])
    if parsed is None:
        raise AssertionError(f"invalid fixture range: {ranges[0]}")
    return f"P{parsed[0]:04d}"


def base_fixture(route_key: str = "skill_design") -> dict[str, object]:
    route = ROUTE_FIXTURES[route_key]
    route_concepts = route["concepts"]
    concept_hits = []
    for index, concept in enumerate(route_concepts, start=1):
        concept_ranges = sorted_anchor_ranges(concept)
        source_id = first_source_id(concept_ranges)
        concept_hits.append(
            {
                "concept_id": concept,
                "hit_type": "direct",
                "trigger_variable": f"{route_key}-variable-{index}",
                "registry_anchor": "concept-registry/index.md",
                "source_ranges_from_registry": concept_ranges,
                "source_ranges_read": concept_ranges,
                "source_paragraph_ids": [source_id],
                "contract_id": contract_id_for_concept(concept),
                "contract_checked": True,
                "downgraded_after_source_read": False,
            }
        )
    claim_source_id = first_source_id(sorted_anchor_ranges(route_concepts[0]))
    claim = {
        "claim_id": "CL1",
        "claim": f"The {route_key} route must keep route concepts, evidence, and action limits separated.",
        "claim_type": "mechanism_candidate",
        "source_anchor": sorted_anchor_ranges(route_concepts[0])[0],
        "source_paragraph_ids": [claim_source_id],
        "concept_ids": route_concepts,
        "evidence_status": "full",
        "counterevidence_status": "searched",
        "downgrade_condition": "If route concepts are not consumed, downgrade to incomplete route review.",
        "withdrawal_condition": "Withdraw if route-ledger validation fails.",
        "action_limit": "May guide max output structure; may not certify external reality.",
    }
    audit = {
        "claim_id": "CL1",
        "source_paragraph_ids": [claim_source_id],
        "evidence_chain": [sorted_anchor_ranges(route_concepts[0])[0], "P3103-P3116"],
        "reasoning_chain": [
            "route key -> required concept set",
            "required concept set -> concept hit ledger",
            "concept hit ledger -> bounded claim",
        ],
        "counterevidence": ["route concept missing would invalidate this decision"],
        "counterevidence_status": "searched",
        "calibration_rounds": [
            {
                "round": 1,
                "result": "kept",
                "reason": "Decision remains inside route and evidence boundaries.",
            }
        ],
        "final_strength": "mechanism_candidate",
        "withdrawal_condition": "Withdraw if route-ledger validation fails.",
        "final_output_allowed": True,
    }
    if route.get("design"):
        claim["design_decision_id"] = "DD1"
        claim["v6_rule_ids"] = ["R-skill-design-tool-boundary", "R-process-artifact-action-limit"]
        audit["design_decision_id"] = "DD1"
    return {
        "max-read-plan.json": {
            "phase": "read-plan",
            "route_key": route_key,
            "route_map_version": "v6.0",
            "final_full_source_required": True,
            "required_full_source_files": REQUIRED_FULL_SOURCE_FILES,
            "route_required_layers": route["layers"],
            "route_required_concepts": route_concepts,
            "route_required_outputs": route["outputs"],
            "route_forbidden_outputs_checked": [
                {"forbidden_output": value, "checked": True, "present": False}
                for value in route["forbidden_outputs"]
            ],
        },
        "max-concept-hit-ledger.json": {"concept_hits": concept_hits},
        "max-claim-ledger.json": {"claims": [claim]},
        "max-evidence-reasoning-audit.json": {"audits": [audit]},
        "max-dossier.md": "clean artifact text",
        "max-essay.md": "clean artifact text",
    }


def write_fixture(workspace: Path, fixture: dict[str, object]) -> None:
    for filename, value in fixture.items():
        path = workspace / filename
        if filename.endswith(".json"):
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            path.write_text(str(value) + "\n", encoding="utf-8")


def run_case(name: str, fixture: dict[str, object], expected_fragment: str | None) -> None:
    with tempfile.TemporaryDirectory(prefix=f"crossframe-max-route-{name}-") as temp_dir:
        workspace = Path(temp_dir)
        write_fixture(workspace, fixture)
        errors = check(workspace, repo_root() / "skills" / "crossframe-max")
    if expected_fragment is None:
        if errors:
            raise AssertionError(f"{name}: expected pass, got {errors}")
        return
    if not any(expected_fragment in error for error in errors):
        raise AssertionError(f"{name}: expected {expected_fragment!r}, got {errors}")


def marker_blob(markers: list[str], repeat: int = 1) -> str:
    return "\n".join(markers * repeat) + "\n"


def dossier_fixture_text() -> str:
    lines: list[str] = []
    for index, heading in enumerate(REQUIRED_DOSSIER_HEADINGS, start=1):
        lines.append(heading)
        lines.append(
            f"Section {index} records claim_id CL1, source_anchor P0276, route evidence, "
            "counterevidence, withdrawal condition, and action_limit inside the locked max artifact boundary."
        )
    lines.append(marker_blob(REQUIRED_DOSSIER_MARKERS + REQUIRED_FULL_SOURCE_FILES))
    return "\n".join(lines) + "\n"


def essay_fixture_text(repeat: int = 90, omit_marker: str | None = None, include_claim_reference: bool = True) -> str:
    markers = [marker for marker in REQUIRED_ESSAY_MARKERS if marker != omit_marker]
    paragraphs: list[str] = []
    if include_claim_reference:
        paragraphs.append(
            "The final explanation keeps claim_id CL1 tied to source_anchor P0276 before moving into interpretation."
        )
    for index in range(repeat):
        marker = markers[index % len(markers)]
        paragraphs.append(
            f"Paragraph {index + 1:03d} develops {marker} with bounded evidence, route concepts, "
            "counterevidence search, withdrawal conditions, and continuation discipline rather than marker stuffing."
        )
    return "\n\n".join(paragraphs) + "\n"


def write_full_artifact_fixture(workspace: Path) -> None:
    fixture = base_fixture()
    write_fixture(workspace, fixture)
    read_files = []
    for file_name in REQUIRED_FULL_SOURCE_FILES:
        start, end = EXPECTED_FILE_RANGES[file_name]
        read_files.append(
            {
                "file": file_name,
                "expected_range": [start, end],
                "read_ranges": [[start, end]],
                "status": "full",
                "layer_digest": f"digest-{file_name}",
            }
        )
    (workspace / "max-read-ledger.json").write_text(
        json.dumps(
            {
                "total_expected_paragraphs": EXPECTED_TOTAL_PARAGRAPHS,
                "total_read_paragraphs": EXPECTED_TOTAL_PARAGRAPHS,
                "full_source_exhaustive_pass": True,
                "missing_paragraphs": [],
                "files": read_files,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "max-run-contract.json").write_text(
        json.dumps(
            {
                "run_mode": "crossframe-v6-max",
                "max_run_level": "max-complete",
                "final_output_allowed": False,
                "forbidden_behavior": ["output before lock"],
                "affected_phase_reset_rule": "affected phase reset",
                "phase_exception_rule": "phase_exception_record",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "max-source-snapshot.json").write_text(
        json.dumps(
            {
                "source_snapshot_id": "source_snapshot_001",
                "total_paragraphs": 3273,
                "full_source_exhaustive_pass": True,
                "table_count": 60,
                "frozen": True,
                "source_anchor_verification_only_after_freeze": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "max-worldview-capsule.locked.md").write_text(
        "locked: true\nsource_snapshot_id\n本轮预先设计的世界观\nworldview_exception_record\n",
        encoding="utf-8",
    )
    (workspace / "max-local-world-model.locked.md").write_text(
        "locked: true\n局部世界\n对象边界\n主体位置\n承接链\n只建模，不下最终判断\n",
        encoding="utf-8",
    )
    (workspace / "max-claim-board.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "CL1",
                        "status": "final",
                        "source_paragraph_ids": ["P0276"],
                        "concept_ids": ROUTE_CONCEPTS,
                        "needs_evidence": True,
                        "needs_counterevidence": True,
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "max-audit-board.json").write_text(
        json.dumps(
            {
                "red_team_final_text_authority": False,
                "audits": [
                    {
                        "claim_id": "CL1",
                        "audit_result": "keep",
                        "final_status": "final",
                        "source_paragraph_ids": ["P0276"],
                        "counterevidence_status": "searched",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "max-output-plan.locked.md").write_text(
        marker_blob(
            [
                "locked: true",
                "进入正文的 claim",
                "降档表达的 claim",
                "撤回的 claim",
                "进入不可判断区的 claim",
                "不可写强的句子",
                "必须保留的撤回条件",
                "max-essay.md may now be written",
            ]
        ),
        encoding="utf-8",
    )
    dossier = dossier_fixture_text()
    essay = essay_fixture_text()
    ledger = marker_blob(REQUIRED_LEDGER_MARKERS + REQUIRED_FULL_SOURCE_FILES)
    (workspace / "max-artifact-manifest.md").write_text(marker_blob(REQUIRED_MANIFEST_MARKERS), encoding="utf-8")
    (workspace / "max-dossier.md").write_text(dossier, encoding="utf-8")
    (workspace / "max-essay.md").write_text(essay, encoding="utf-8")
    (workspace / "max-continuation-ledger.md").write_text(ledger, encoding="utf-8")
    (workspace / "max-continuation-index.md").write_text(marker_blob(REQUIRED_INDEX_MARKERS), encoding="utf-8")


def main() -> int:
    artifact_validator = (repo_root() / "scripts" / "check_crossframe_max_artifacts.py").read_text(encoding="utf-8")
    if "check_crossframe_max_route_ledgers" not in artifact_validator or "check_route_ledgers" not in artifact_validator:
        raise AssertionError("artifact validator must call check_crossframe_max_route_ledgers")

    valid = base_fixture()
    run_case("valid-skill-design", valid, None)
    run_case("valid-meaning-question", base_fixture("meaning_question"), None)
    run_case("valid-history-analysis", base_fixture("history_analysis"), None)
    run_case("valid-document-question", base_fixture("document_question"), None)

    missing_route = copy.deepcopy(valid)
    del missing_route["max-read-plan.json"]["route_key"]  # type: ignore[index]
    run_case("missing-route-key", missing_route, "route_key")

    missing_concept = copy.deepcopy(valid)
    missing_concept["max-read-plan.json"]["route_required_concepts"] = ROUTE_CONCEPTS[:-1]  # type: ignore[index]
    run_case("missing-required-concept", missing_concept, "missing route required_concepts")

    missing_claim_concept = copy.deepcopy(valid)
    missing_claim_concept["max-claim-ledger.json"]["claims"][0]["concept_ids"] = ROUTE_CONCEPTS[:-1]  # type: ignore[index]
    run_case("claim-missing-route-concept", missing_claim_concept, "route concepts missing from concept_ids")

    fake_concept = copy.deepcopy(valid)
    fake_concept["max-concept-hit-ledger.json"]["concept_hits"][0]["concept_id"] = "不存在概念"  # type: ignore[index]
    run_case("fake-concept-id", fake_concept, "not found in concept registry")

    wrong_source_range = copy.deepcopy(base_fixture("history_analysis"))
    wrong_source_range["max-concept-hit-ledger.json"]["concept_hits"][0]["source_ranges_from_registry"] = [  # type: ignore[index]
        "P0276-P0355"
    ]
    run_case("wrong-registry-source-range", wrong_source_range, "source_ranges_from_registry does not match")

    source_id_outside_read = copy.deepcopy(base_fixture("history_analysis"))
    source_id_outside_read["max-concept-hit-ledger.json"]["concept_hits"][0]["source_paragraph_ids"] = [  # type: ignore[index]
        "P0276"
    ]
    run_case("source-id-outside-read", source_id_outside_read, "source_paragraph_ids not covered")

    missing_contract_heading = copy.deepcopy(valid)
    missing_contract_heading["max-concept-hit-ledger.json"]["concept_hits"][0]["contract_id"] = (  # type: ignore[index]
        "v6-core-contracts.md#不存在契约"
    )
    run_case("missing-contract-heading", missing_contract_heading, "contract_id heading not found")

    contract_id_not_equal_map = copy.deepcopy(valid)
    contract_id_not_equal_map["max-concept-hit-ledger.json"]["concept_hits"][0]["contract_id"] = (  # type: ignore[index]
        "v6-core-contracts.md#解释准入"
    )
    run_case("contract-id-not-equal-map", contract_id_not_equal_map, "must equal v6-contract-map.json entry")

    missing_v6_rule = copy.deepcopy(valid)
    del missing_v6_rule["max-claim-ledger.json"]["claims"][0]["v6_rule_ids"]  # type: ignore[index]
    run_case("missing-v6-rule-ids", missing_v6_rule, "missing v6_rule_ids")

    missing_action_limit = copy.deepcopy(valid)
    del missing_action_limit["max-claim-ledger.json"]["claims"][0]["action_limit"]  # type: ignore[index]
    run_case("missing-action-limit", missing_action_limit, "missing action_limit")

    forbidden_artifact = copy.deepcopy(valid)
    forbidden_artifact["max-dossier.md"] = "把 prompt 当作概念本体"
    run_case("forbidden-output", forbidden_artifact, "forbidden output appears")

    forbidden_checked = copy.deepcopy(valid)
    forbidden_checked["max-dossier.md"] = "已检查 forbidden output：`把 prompt 当作概念本体`，present=false。"
    run_case("forbidden-output-present-false", forbidden_checked, None)

    with tempfile.TemporaryDirectory(prefix="crossframe-max-full-artifact-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if errors:
            raise AssertionError(f"full artifact fixture: expected pass, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-short-essay-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        (workspace / "max-essay.md").write_text(marker_blob(REQUIRED_ESSAY_MARKERS), encoding="utf-8")
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("longform-dominance gate failed" in error for error in errors):
            raise AssertionError(f"short essay fixture: expected longform failure, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-coverage-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        (workspace / "max-essay.md").write_text(essay_fixture_text(omit_marker="局部世界"), encoding="utf-8")
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("missing marker: 局部世界" in error for error in errors):
            raise AssertionError(f"coverage fixture: expected missing marker, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-empty-section-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        empty_dossier = "\n".join(REQUIRED_DOSSIER_HEADINGS) + "\n" + marker_blob(
            REQUIRED_DOSSIER_MARKERS + REQUIRED_FULL_SOURCE_FILES
        )
        (workspace / "max-dossier.md").write_text(empty_dossier, encoding="utf-8")
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("heading section too thin" in error for error in errors):
            raise AssertionError(f"empty dossier fixture: expected section thin failure, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-no-claim-ref-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        (workspace / "max-essay.md").write_text(
            essay_fixture_text(include_claim_reference=False).replace("source_anchor", "source anchor"),
            encoding="utf-8",
        )
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("must reference a real claim_id or source_paragraph_id" in error for error in errors):
            raise AssertionError(f"claim reference fixture: expected claim/source failure, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-repetition-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        repeated_essay = "claim_id CL1 source_anchor P0276\n" + ("repeated filler line\n" * 60)
        repeated_essay += marker_blob(REQUIRED_ESSAY_MARKERS)
        (workspace / "max-essay.md").write_text(repeated_essay, encoding="utf-8")
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("repeated" in error for error in errors):
            raise AssertionError(f"repetition fixture: expected repeated filler failure, got {errors}")

    with tempfile.TemporaryDirectory(prefix="crossframe-max-missing-route-") as temp_dir:
        workspace = Path(temp_dir)
        write_full_artifact_fixture(workspace)
        read_plan = json.loads((workspace / "max-read-plan.json").read_text(encoding="utf-8"))
        del read_plan["route_key"]
        (workspace / "max-read-plan.json").write_text(
            json.dumps(read_plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        errors = check_crossframe_max_artifacts(workspace, repo_root() / "skills" / "crossframe-max")
        if not any("missing route_key" in error for error in errors):
            raise AssertionError(f"missing route fixture: expected route_key failure, got {errors}")

    print("ok: crossframe max route-ledger fixtures passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
