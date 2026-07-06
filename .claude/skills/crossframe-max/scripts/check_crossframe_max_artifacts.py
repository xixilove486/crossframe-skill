from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path
from typing import Any

from check_crossframe_max_read_ledger import check as check_structured_ledgers
from check_crossframe_max_route_ledgers import check as check_route_ledgers


REQUIRED_DOSSIER_HEADINGS = [
    "## max-phase-lock",
    "## max-worldview-capsule",
    "## max-continuation-ledger",
    "## max-source-frontier",
    "## max-transcendence-window",
    "## max-position-matrix",
    "## max-local-world-model",
    "## max-concept-graph",
    "## max-scale-map",
    "## 运行规律",
    "## 问题定位",
    "## max-path-tree",
    "## max-path-confidence-layers",
    "## max-red-team-pass",
    "## max-unexhaustible-declaration",
    "## 处理问题",
    "## 证据与台账",
    "## max-evidence-reasoning-audit",
    "## max-validation-and-repair-state",
    "## 反例与撤回条件",
    "## max-essay 准备",
    "## max-output-layers",
    "## max-continuation-index",
]

REQUIRED_DOSSIER_MARKERS = [
    "phase-lock gate",
    "phase artifacts",
    "max-run-contract.json",
    "max-read-plan.json",
    "max-source-snapshot.json",
    "max-worldview-capsule.locked.md",
    "max-local-world-model.locked.md",
    "max-claim-board.json",
    "max-audit-board.json",
    "max-output-plan.locked.md",
    "phase_exception_record",
    "affected phase reset",
    "source_anchor",
    "claim_id",
    "claim ledger",
    "source ledger",
    "concept-registry lookup",
    "retrieval-trigger-policy",
    "内部概念检索",
    "外部检索触发",
    "先查 registry 再读 full-source",
    "max-evidence-reasoning-audit",
    "举证链",
    "推理链",
    "反向证据",
    "证据-推理-反例-降档循环",
    "max-output-layers",
    "max-continuation-index",
    "max-full-source-read-ledger",
    "full-source exhaustive pass: satisfied",
    "total paragraphs: 3273 / 3273",
    "stage 0 source inventory",
    "stage 8 final read audit",
    "read status: full / partial / missing",
    "layer digest",
    "max-read-ledger.json",
    "max-claim-ledger.json",
    "max-concept-hit-ledger.json",
    "max-evidence-reasoning-audit.json",
    "max-validator-report.json",
    "max-repair-plan.json",
    "validation_attempt",
    "affected_phase",
    "downstream_reset",
    "repair_action",
    "final_output_allowed",
    "registry expected source ranges",
    "source_ranges_from_registry",
    "source_ranges_read",
    "source_paragraph_ids inside read ranges",
    "contract_id",
    "contract heading exists",
    "contract map status",
    "concept-source-contract closure",
]

REQUIRED_ESSAY_MARKERS = [
    "phase-lock gate",
    "max-run-contract.json",
    "max-output-plan.locked.md",
    "局部世界",
    "运行规律",
    "问题形成",
    "路径演化",
    "概念注册表",
    "处理问题",
    "伪修复",
    "资料前沿",
    "retrieval-trigger-policy",
    "路径置信分层",
    "主体位置矩阵",
    "反向推演",
    "不可判断区",
    "撤回条件",
    "不可穷尽",
    "续写索引",
    "max-continuation-index",
    "max-full-source-read-ledger",
    "full-source exhaustive pass: satisfied",
    "total paragraphs: 3273 / 3273",
    "stage 8 final read audit",
    "max-read-ledger.json",
    "max-claim-ledger.json",
    "max-concept-hit-ledger.json",
    "max-evidence-reasoning-audit.json",
    "max-validator-report.json",
]

REQUIRED_LEDGER_MARKERS = [
    "phase-lock gate",
    "phase artifacts",
    "max-run-contract.json",
    "max-source-snapshot.json",
    "max-output-plan.locked.md",
    "max-run-state",
    "已读材料",
    "已展开路径",
    "未展开路径",
    "已撤回判断",
    "下一轮续写入口",
    "防重复",
    "防漂移",
    "max-full-source-read-ledger",
    "full-source exhaustive pass: satisfied",
    "total paragraphs: 3273 / 3273",
    "read status: full / partial / missing",
    "stage 8 final read audit",
    "max-read-ledger.json",
    "max-claim-ledger.json",
    "max-concept-hit-ledger.json",
    "max-evidence-reasoning-audit.json",
]

REQUIRED_INDEX_MARKERS = [
    "下一轮续写入口",
    "未展开路径",
    "未展开主体位置",
    "未穷尽资料队列",
    "未展开反例",
    "不得重复内容",
    "不得越界内容",
]

REQUIRED_MANIFEST_MARKERS = [
    "phase-lock gate",
    "phase artifacts",
    "artifact-first gate",
    "产物目录",
    "生成时间",
    "输入摘要",
    "读态摘要",
    "校验状态",
    "下一轮入口",
    "max-dossier.md",
    "max-essay.md",
    "max-continuation-ledger.md",
    "max-continuation-index.md",
    "max-run-contract.json",
    "max-read-plan.json",
    "max-source-snapshot.json",
    "max-worldview-capsule.locked.md",
    "max-local-world-model.locked.md",
    "max-claim-board.json",
    "max-audit-board.json",
    "max-output-plan.locked.md",
    "max-full-source-read-ledger",
    "full-source exhaustive pass: satisfied",
    "total paragraphs: 3273 / 3273",
    "stage 0 source inventory",
    "stage 8 final read audit",
    "read status: full / partial / missing",
    "max-read-ledger.json",
    "max-claim-ledger.json",
    "max-concept-hit-ledger.json",
    "max-evidence-reasoning-audit.json",
]

REQUIRED_FULL_SOURCE_FILES = [
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
]

FORBIDDEN_FINAL_MARKERS = [
    "max-incomplete:",
    "full-source exhaustive pass: not satisfied",
    "full-source exhaustive pass: unsatisfied",
    "read status: partial",
    "read status: missing",
]

MIN_ESSAY_TO_DOSSIER_RATIO = 1.6
STRONG_ESSAY_TO_DOSSIER_RATIO = 2.2
MAX_ESSAY_TO_DOSSIER_RATIO = 3.0
MIN_DOSSIER_SECTION_CHARS = 32
MAX_CONSECUTIVE_REPEATED_LINES = 5
MAX_REPEATED_LINE_RATIO = 0.20
MAX_HEADING_LINE_RATIO = 0.45
SOURCE_PARAGRAPH_RE = re.compile(r"\bP\d{4}\b")

DEFAULT_FILENAMES = {
    "manifest": "max-artifact-manifest.md",
    "dossier": "max-dossier.md",
    "essay": "max-essay.md",
    "ledger": "max-continuation-ledger.md",
    "index": "max-continuation-index.md",
}

STRUCTURED_LEDGER_FILENAMES = [
    "max-read-ledger.json",
    "max-claim-ledger.json",
    "max-concept-hit-ledger.json",
    "max-evidence-reasoning-audit.json",
]

PHASE_LOCK_FILENAMES = [
    "max-run-contract.json",
    "max-read-plan.json",
    "max-source-snapshot.json",
    "max-worldview-capsule.locked.md",
    "max-local-world-model.locked.md",
    "max-claim-board.json",
    "max-audit-board.json",
    "max-output-plan.locked.md",
]

ALLOWED_CLAIM_STATUSES = {
    "candidate",
    "supported",
    "downgraded",
    "split",
    "withdrawn",
    "needs_search",
    "unexhaustible",
    "final",
}

ALLOWED_AUDIT_RESULTS = {
    "keep",
    "downgrade",
    "split",
    "withdraw",
    "needs_external_search",
    "move_to_unexhaustible",
}

VALIDATOR_NAME = "check_crossframe_max_artifacts"

PHASE_DOWNSTREAM = {
    "run_contract": [
        "max-read-plan.json",
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    ],
    "read_plan": [
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-board.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "source_snapshot": [
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-evidence-reasoning-audit.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "concept_hit": [
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "claim": [
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "audit": [
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "output_plan": [
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    ],
    "final_markdown": [],
    "repository_maintenance": [],
}


@dataclass(frozen=True)
class ValidationError:
    error_id: str
    validator: str
    error_type: str
    severity: str
    artifact: str
    field: str | None
    message: str
    affected_phase: str
    repair_action: str
    downstream_reset: list[str]
    final_output_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_text(path: Path, errors: list[str]) -> str:
    if not path.exists():
        errors.append(f"missing file: {path}")
        return ""
    if not path.is_file():
        errors.append(f"not a file: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def read_json_file(path: Path, errors: list[str], missing_label: str = "phase-lock artifact") -> object | None:
    if not path.exists():
        errors.append(f"missing {missing_label}: {path.name}")
        return None
    if not path.is_file():
        errors.append(f"phase-lock artifact is not a file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return None


def check_markers(text: str, markers: list[str], label: str, errors: list[str]) -> None:
    for marker in markers:
        if marker not in text:
            errors.append(f"{label}: missing marker: {marker}")


def check_ordered_headings(text: str, headings: list[str], label: str, errors: list[str]) -> None:
    previous = -1
    lines = text.splitlines()
    for heading in headings:
        current = -1
        for idx, line in enumerate(lines):
            if line.startswith(heading):
                current = idx
                break
        if current == -1:
            errors.append(f"{label}: missing heading: {heading}")
            continue
        if current < previous:
            errors.append(f"{label}: heading out of order: {heading}")
        previous = current


def heading_positions(text: str, headings: list[str]) -> list[tuple[str, int]]:
    lines = text.splitlines()
    positions: list[tuple[str, int]] = []
    for heading in headings:
        for idx, line in enumerate(lines):
            if line.startswith(heading):
                positions.append((heading, idx))
                break
    return positions


def check_heading_sections_nonempty(text: str, headings: list[str], label: str, errors: list[str]) -> None:
    lines = text.splitlines()
    positions = heading_positions(text, headings)
    if len(positions) != len(headings):
        return
    for index, (heading, start) in enumerate(positions):
        end = positions[index + 1][1] if index + 1 < len(positions) else len(lines)
        section = "\n".join(line for line in lines[start + 1 : end] if line.strip())
        section_chars = visible_chars(section)
        if section_chars < MIN_DOSSIER_SECTION_CHARS:
            errors.append(
                f"{label}: heading section too thin: {heading} "
                f"({section_chars} visible chars, required>={MIN_DOSSIER_SECTION_CHARS})"
            )


def check_repetitive_filler(text: str, label: str, errors: list[str]) -> None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return
    heading_lines = [line for line in lines if line.startswith("#")]
    if len(lines) >= 10 and len(heading_lines) / len(lines) > MAX_HEADING_LINE_RATIO:
        errors.append(f"{label}: heading-to-content ratio too high for a completed artifact")

    previous = None
    repeated = 0
    for line in lines:
        if line == previous:
            repeated += 1
            if repeated >= MAX_CONSECUTIVE_REPEATED_LINES:
                errors.append(f"{label}: consecutive repeated line filler detected")
                break
        else:
            previous = line
            repeated = 1

    countable = [line for line in lines if not line.startswith("#") and len(line) >= 8]
    if len(countable) < 12:
        return
    line, count = Counter(countable).most_common(1)[0]
    if count >= 6 and count / len(countable) > MAX_REPEATED_LINE_RATIO:
        errors.append(f"{label}: repeated template line filler detected: {line[:60]}")


def check_no_template_truncation(text: str, errors: list[str]) -> None:
    if "## max-unexhaustible-declaration" in text and "## 证据与台账" not in text:
        errors.append(
            "max-dossier.md: template-fidelity gate failed: template appears truncated after max-unexhaustible-declaration"
        )
    if "CL1" in text and ("source_anchor" not in text or "claim ledger" not in text):
        errors.append(
            "max-dossier.md: CL-style claim ids require source_anchor, claim_id, source ledger, and claim ledger"
        )


def visible_chars(text: str) -> int:
    return len("".join(text.split()))


def check_longform_dominance(dossier: str, essay: str, errors: list[str]) -> None:
    """Enforce the longform-dominance gate: max-essay is the final explanation, not a dossier summary."""
    dossier_chars = visible_chars(dossier)
    essay_chars = visible_chars(essay)
    required_chars = int(dossier_chars * MIN_ESSAY_TO_DOSSIER_RATIO)
    if dossier_chars and essay_chars < required_chars:
        errors.append(
            "max-essay.md: longform-dominance gate failed: "
            f"max-essay visible chars must be at least {MIN_ESSAY_TO_DOSSIER_RATIO:.1f}x max-dossier "
            f"(essay={essay_chars}, dossier={dossier_chars}, required>={required_chars})"
        )


def check_essay_claim_or_source_references(
    essay: str, claim_ids: set[str], source_paragraph_ids: set[str], errors: list[str]
) -> None:
    if not claim_ids and not source_paragraph_ids:
        return
    if any(claim_id in essay for claim_id in claim_ids):
        return
    essay_source_ids = set(SOURCE_PARAGRAPH_RE.findall(essay))
    if source_paragraph_ids & essay_source_ids:
        return
    errors.append("max-essay.md: final explanation must reference a real claim_id or source_paragraph_id from structured ledgers")


def check_no_incomplete_final(text: str, label: str, errors: list[str]) -> None:
    normalized = text.lower()
    for marker in FORBIDDEN_FINAL_MARKERS:
        if marker in normalized:
            errors.append(f"{label}: incomplete full-source read state cannot pass final artifact validation: {marker}")


def default_skill_root() -> Path:
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "crossframe-max":
        return script_path.parent.parent
    return script_path.parents[1] / "skills" / "crossframe-max"


def ids_from_claim_ledger(workspace: Path, errors: list[str]) -> set[str]:
    data = read_json_file(workspace / "max-claim-ledger.json", errors, "structured ledger")
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return set()
    return {
        claim.get("claim_id")
        for claim in data["claims"]
        if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)
    }


def source_ids_from_claim_ledger(workspace: Path, errors: list[str]) -> set[str]:
    data = read_json_file(workspace / "max-claim-ledger.json", errors, "structured ledger")
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return set()
    source_ids: set[str] = set()
    for claim in data["claims"]:
        if not isinstance(claim, dict) or not isinstance(claim.get("source_paragraph_ids"), list):
            continue
        source_ids.update(
            source_id
            for source_id in claim["source_paragraph_ids"]
            if isinstance(source_id, str) and SOURCE_PARAGRAPH_RE.fullmatch(source_id)
        )
    return source_ids


def check_phase_lock_artifacts(workspace: Path, errors: list[str]) -> None:
    for filename in PHASE_LOCK_FILENAMES:
        if not (workspace / filename).exists():
            errors.append(f"missing phase-lock artifact: {filename}")

    run_contract = read_json_file(workspace / "max-run-contract.json", errors)
    if isinstance(run_contract, dict):
        if run_contract.get("run_mode") != "crossframe-v6-max":
            errors.append("max-run-contract.json: run_mode must be crossframe-v6-max")
        if run_contract.get("final_output_allowed") is not False:
            errors.append("max-run-contract.json: final_output_allowed must be false before output-plan lock")
        forbidden = run_contract.get("forbidden_behavior")
        if not isinstance(forbidden, list) or not forbidden:
            errors.append("max-run-contract.json: forbidden_behavior must be a non-empty list")
        for field in ["affected_phase_reset_rule", "phase_exception_rule"]:
            if not run_contract.get(field):
                errors.append(f"max-run-contract.json: missing {field}")

    read_plan = read_json_file(workspace / "max-read-plan.json", errors)
    if isinstance(read_plan, dict):
        if read_plan.get("final_full_source_required") is not True:
            errors.append("max-read-plan.json: final_full_source_required must be true")
        required_files = read_plan.get("required_full_source_files")
        if not isinstance(required_files, list):
            errors.append("max-read-plan.json: required_full_source_files must be a list")
        else:
            missing = sorted(set(REQUIRED_FULL_SOURCE_FILES) - set(required_files))
            if missing:
                errors.append(f"max-read-plan.json: missing required full-source files: {', '.join(missing)}")

    source_snapshot = read_json_file(workspace / "max-source-snapshot.json", errors)
    if isinstance(source_snapshot, dict):
        if not source_snapshot.get("source_snapshot_id"):
            errors.append("max-source-snapshot.json: missing source_snapshot_id")
        if source_snapshot.get("total_paragraphs") != 3273:
            errors.append("max-source-snapshot.json: total_paragraphs must be 3273")
        if source_snapshot.get("full_source_exhaustive_pass") is not True:
            errors.append("max-source-snapshot.json: full_source_exhaustive_pass must be true")
        if source_snapshot.get("table_count") != 60:
            errors.append("max-source-snapshot.json: table_count must be 60")
        if source_snapshot.get("frozen") is not True:
            errors.append("max-source-snapshot.json: frozen must be true")
        if source_snapshot.get("source_anchor_verification_only_after_freeze") is not True:
            errors.append(
                "max-source-snapshot.json: source_anchor_verification_only_after_freeze must be true"
            )

    worldview = read_text(workspace / "max-worldview-capsule.locked.md", errors)
    if worldview:
        check_markers(
            worldview,
            ["locked: true", "source_snapshot_id", "本轮预先设计的世界观", "worldview_exception_record"],
            "max-worldview-capsule.locked.md",
            errors,
        )

    local_world = read_text(workspace / "max-local-world-model.locked.md", errors)
    if local_world:
        check_markers(
            local_world,
            ["locked: true", "局部世界", "对象边界", "主体位置", "承接链", "只建模，不下最终判断"],
            "max-local-world-model.locked.md",
            errors,
        )

    claim_board = read_json_file(workspace / "max-claim-board.json", errors)
    claim_board_ids: set[str] = set()
    if isinstance(claim_board, dict):
        claims = claim_board.get("claims")
        if not isinstance(claims, list) or not claims:
            errors.append("max-claim-board.json: claims must be a non-empty list")
        else:
            for idx, claim in enumerate(claims, start=1):
                if not isinstance(claim, dict):
                    errors.append(f"max-claim-board.json: claim {idx} must be an object")
                    continue
                claim_id = claim.get("claim_id")
                if not isinstance(claim_id, str) or not claim_id:
                    errors.append(f"max-claim-board.json: claim {idx} missing claim_id")
                    continue
                claim_board_ids.add(claim_id)
                status = claim.get("status")
                if status not in ALLOWED_CLAIM_STATUSES:
                    errors.append(f"max-claim-board.json: {claim_id} invalid status: {status}")
                if not claim.get("source_paragraph_ids"):
                    errors.append(f"max-claim-board.json: {claim_id} missing source_paragraph_ids")
                if not claim.get("concept_ids"):
                    errors.append(f"max-claim-board.json: {claim_id} missing concept_ids")
                if claim.get("needs_evidence") is not True:
                    errors.append(f"max-claim-board.json: {claim_id} needs_evidence must be true before audit")
                if claim.get("needs_counterevidence") is not True:
                    errors.append(f"max-claim-board.json: {claim_id} needs_counterevidence must be true before audit")

    audit_board = read_json_file(workspace / "max-audit-board.json", errors)
    audit_board_ids: set[str] = set()
    if isinstance(audit_board, dict):
        if audit_board.get("red_team_final_text_authority") is not False:
            errors.append("max-audit-board.json: red_team_final_text_authority must be false")
        audits = audit_board.get("audits")
        if not isinstance(audits, list) or not audits:
            errors.append("max-audit-board.json: audits must be a non-empty list")
        else:
            for idx, audit in enumerate(audits, start=1):
                if not isinstance(audit, dict):
                    errors.append(f"max-audit-board.json: audit {idx} must be an object")
                    continue
                claim_id = audit.get("claim_id")
                if not isinstance(claim_id, str) or not claim_id:
                    errors.append(f"max-audit-board.json: audit {idx} missing claim_id")
                    continue
                audit_board_ids.add(claim_id)
                if audit.get("audit_result") not in ALLOWED_AUDIT_RESULTS:
                    errors.append(f"max-audit-board.json: {claim_id} invalid audit_result")
                if audit.get("final_status") not in ALLOWED_CLAIM_STATUSES:
                    errors.append(f"max-audit-board.json: {claim_id} invalid final_status")
                if not audit.get("source_paragraph_ids"):
                    errors.append(f"max-audit-board.json: {claim_id} missing source_paragraph_ids")
                if not audit.get("counterevidence_status"):
                    errors.append(f"max-audit-board.json: {claim_id} missing counterevidence_status")

    output_plan = read_text(workspace / "max-output-plan.locked.md", errors)
    if output_plan:
        check_markers(
            output_plan,
            [
                "locked: true",
                "进入正文的 claim",
                "降档表达的 claim",
                "撤回的 claim",
                "进入不可判断区的 claim",
                "不可写强的句子",
                "必须保留的撤回条件",
                "max-essay.md may now be written",
            ],
            "max-output-plan.locked.md",
            errors,
        )

    final_claim_ids = ids_from_claim_ledger(workspace, errors)
    if final_claim_ids and claim_board_ids:
        missing = sorted(final_claim_ids - claim_board_ids)
        if missing:
            errors.append(f"phase-lock gate: final claims missing from max-claim-board.json: {', '.join(missing)}")
    if final_claim_ids and audit_board_ids:
        missing = sorted(final_claim_ids - audit_board_ids)
        if missing:
            errors.append(f"phase-lock gate: final claims missing from max-audit-board.json: {', '.join(missing)}")


def check_crossframe_max_artifacts(workspace: Path, skill_root: Path | None = None) -> list[str]:
    """Validate generated crossframe-max artifacts against artifact, template, and longform gates."""
    errors: list[str] = []
    if not workspace.exists():
        errors.append(f"missing workspace directory: {workspace}")
        return errors
    if not workspace.is_dir():
        errors.append(f"workspace is not a directory: {workspace}")
        return errors

    manifest = read_text(workspace / DEFAULT_FILENAMES["manifest"], errors)
    dossier = read_text(workspace / DEFAULT_FILENAMES["dossier"], errors)
    essay = read_text(workspace / DEFAULT_FILENAMES["essay"], errors)
    ledger = read_text(workspace / DEFAULT_FILENAMES["ledger"], errors)
    index = read_text(workspace / DEFAULT_FILENAMES["index"], errors)
    claim_ids_for_essay = (
        ids_from_claim_ledger(workspace, errors) if (workspace / "max-claim-ledger.json").exists() else set()
    )
    source_ids_for_essay = (
        source_ids_from_claim_ledger(workspace, errors) if (workspace / "max-claim-ledger.json").exists() else set()
    )

    if manifest:
        check_markers(manifest, REQUIRED_MANIFEST_MARKERS, "max-artifact-manifest.md", errors)
        check_no_incomplete_final(manifest, "max-artifact-manifest.md", errors)
    if dossier:
        check_ordered_headings(dossier, REQUIRED_DOSSIER_HEADINGS, "max-dossier.md", errors)
        check_heading_sections_nonempty(dossier, REQUIRED_DOSSIER_HEADINGS, "max-dossier.md", errors)
        check_markers(dossier, REQUIRED_DOSSIER_MARKERS, "max-dossier.md", errors)
        check_markers(dossier, REQUIRED_FULL_SOURCE_FILES, "max-dossier.md", errors)
        check_no_incomplete_final(dossier, "max-dossier.md", errors)
        check_no_template_truncation(dossier, errors)
        check_repetitive_filler(dossier, "max-dossier.md", errors)
    if essay:
        check_markers(essay, REQUIRED_ESSAY_MARKERS, "max-essay.md", errors)
        check_no_incomplete_final(essay, "max-essay.md", errors)
        check_essay_claim_or_source_references(essay, claim_ids_for_essay, source_ids_for_essay, errors)
        check_repetitive_filler(essay, "max-essay.md", errors)
    if dossier and essay:
        check_longform_dominance(dossier, essay, errors)
    if ledger:
        check_markers(ledger, REQUIRED_LEDGER_MARKERS, "max-continuation-ledger.md", errors)
        check_markers(ledger, REQUIRED_FULL_SOURCE_FILES, "max-continuation-ledger.md", errors)
        check_no_incomplete_final(ledger, "max-continuation-ledger.md", errors)
    if index:
        check_markers(index, REQUIRED_INDEX_MARKERS, "max-continuation-index.md", errors)
        check_no_incomplete_final(index, "max-continuation-index.md", errors)
    for filename in STRUCTURED_LEDGER_FILENAMES:
        if not (workspace / filename).exists():
            errors.append(f"missing structured ledger: {filename}")
    check_phase_lock_artifacts(workspace, errors)
    if not any(error.startswith("missing structured ledger:") for error in errors):
        errors.extend(check_structured_ledgers(workspace, skill_root or default_skill_root()))
        errors.extend(check_route_ledgers(workspace, skill_root or default_skill_root()))

    return errors


def phase_for_artifact(artifact: str) -> str:
    if artifact == "max-run-contract.json":
        return "run_contract"
    if artifact == "max-read-plan.json":
        return "read_plan"
    if artifact == "max-source-snapshot.json":
        return "source_snapshot"
    if artifact == "max-concept-hit-ledger.json":
        return "concept_hit"
    if artifact in {"max-claim-ledger.json", "max-claim-board.json"}:
        return "claim"
    if artifact in {"max-evidence-reasoning-audit.json", "max-audit-board.json"}:
        return "audit"
    if artifact == "max-output-plan.locked.md":
        return "output_plan"
    if artifact in {
        "max-artifact-manifest.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    }:
        return "final_markdown"
    return "final_markdown"


def extract_artifact(message: str) -> str:
    for token in [
        "max-run-contract.json",
        "max-read-plan.json",
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-artifact-manifest.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
        "v6-route-map.yaml",
        "v6-contract-map.json",
        "concept-registry/index.md",
    ]:
        if token in message:
            return token
    if message.startswith("missing file:"):
        name = Path(message.split(":", 1)[1].strip()).name
        if name:
            return name
    if ": " in message:
        prefix = message.split(":", 1)[0]
        if prefix.endswith((".json", ".md", ".yaml")):
            return prefix
    return "workspace"


def classify_message(message: str) -> tuple[str, str, str, str | None]:
    lowered = message.lower()
    artifact = extract_artifact(message)
    if "invalid json" in lowered:
        return "invalid_json", "create_missing_artifact", phase_for_artifact(artifact), None
    if message.startswith("missing file:") or message.startswith("missing structured ledger:") or "missing phase-lock artifact" in message or "missing route-ledger artifact" in message:
        return "missing_artifact", "create_missing_artifact", phase_for_artifact(artifact), None
    if "full-source" in message and ("not satisfied" in lowered or "partial" in lowered or "missing" in lowered):
        return "full_source_incomplete", "max_incomplete", "source_snapshot", None
    if "source_ranges_from_registry does not match" in message or "source_ranges_read does not overlap" in message:
        return "concept_source_anchor_mismatch", "regenerate_concept_hit_and_downstream", "concept_hit", "source_ranges_from_registry"
    if "source_paragraph_ids not covered" in message:
        return "source_paragraph_not_in_read_range", "regenerate_concept_hit_and_downstream", "concept_hit", "source_paragraph_ids"
    if "contract_id" in message or "v6-contract-map.json" in message:
        return "concept_contract_missing", "repository_maintenance_required", "repository_maintenance", "contract_id"
    if "not found in concept registry" in message:
        return "concept_registry_missing", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_id"
    if "required_concepts missing from concept registry" in message or "missing route required concepts" in message:
        return "route_registry_closure_failed", "regenerate_concept_hit_and_downstream", "concept_hit", "route_required_concepts"
    if "route_key" in message or "route_map_version" in message or "missing route " in message or "forbidden output check" in message:
        return "route_plan_mismatch", "regenerate_output_plan_and_final_markdown", "read_plan", None
    if "concept_ids missing concept hits" in message:
        return "claim_missing_concept_hit", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_ids"
    if "final claims missing audits" in message or "design decisions missing audits" in message:
        return "claim_missing_audit", "regenerate_audit_and_downstream", "audit", "claim_id"
    if "missing evidence_chain" in message or "evidence chain" in lowered:
        return "evidence_chain_missing", "regenerate_audit_and_downstream", "audit", "evidence_chain"
    if "missing counterevidence" in message or "counterevidence_status" in message:
        return "counterevidence_missing", "regenerate_audit_and_downstream", "audit", "counterevidence"
    if "external search" in lowered or "needs_external_search" in message:
        return "external_search_required", "needs_external_search", "audit", None
    if "longform-dominance gate failed" in message:
        return "essay_too_short", "regenerate_markdown_only", "final_markdown", None
    if "heading section too thin" in message:
        return "dossier_section_too_thin", "regenerate_markdown_only", "final_markdown", None
    if "repeated" in lowered or "marker stuffing" in lowered:
        return "repeated_filler", "regenerate_markdown_only", "final_markdown", None
    if "forbidden output appears" in message:
        return "forbidden_output_present", "regenerate_markdown_only", "final_markdown", None
    if "must reference a real claim_id or source_paragraph_id" in message:
        return "missing_claim_or_source_reference", "regenerate_markdown_only", "final_markdown", None
    return "unrepairable_repository_state", "max_incomplete", phase_for_artifact(artifact), None


def check_crossframe_max_artifacts_structured(
    workspace: Path, skill_root: Path | None = None
) -> list[ValidationError]:
    errors = check_crossframe_max_artifacts(workspace, skill_root)
    structured: list[ValidationError] = []
    for index, message in enumerate(errors, start=1):
        error_type, repair_action, affected_phase, field = classify_message(message)
        structured.append(
            ValidationError(
                error_id=f"artifact-{index:04d}",
                validator=VALIDATOR_NAME,
                error_type=error_type,
                severity="error",
                artifact=extract_artifact(message),
                field=field,
                message=message,
                affected_phase=affected_phase,
                repair_action=repair_action,
                downstream_reset=list(PHASE_DOWNSTREAM.get(affected_phase, [])),
                final_output_allowed=False,
            )
        )
    return structured


def validator_report(workspace: Path, errors: list[ValidationError]) -> dict[str, Any]:
    return {
        "report_version": "v1",
        "workspace": str(workspace),
        "passed": not errors,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "validators": ["check_crossframe_max_artifacts", "check_crossframe_max_route_ledgers"],
        "errors": [error.to_dict() for error in errors],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="check_crossframe_max_artifacts: validate generated crossframe-max files against artifact-first, template-fidelity, longform-dominance, and route-ledger gates."
    )
    parser.add_argument("--workspace", default=".", help="Directory containing max-dossier.md and related artifacts.")
    parser.add_argument("--skill-root", default=None, help="Path to the crossframe-max skill root for source-id validation.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable validator report.")
    parser.add_argument(
        "--write-report",
        nargs="?",
        const="",
        default=None,
        help="Write max-validator-report.json; optional explicit path.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else default_skill_root()
    structured_errors = check_crossframe_max_artifacts_structured(workspace, skill_root)
    report = validator_report(workspace, structured_errors)
    if args.write_report is not None:
        report_path = Path(args.write_report).resolve() if args.write_report else workspace / "max-validator-report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if structured_errors else 0
    errors = [error.message for error in structured_errors]
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "ok: crossframe max artifacts passed artifact-first, template-fidelity, "
        f"longform-dominance, and route-ledger gates -> {workspace}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
