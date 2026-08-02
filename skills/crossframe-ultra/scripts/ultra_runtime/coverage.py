from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata

from .article import (
    REQUIRED_READER_APPENDICES,
    REQUIRED_READER_SECTIONS,
    contains_machine_dump,
    extract_reader_sections,
    validate_reader_article,
)
from .errors import UltraRuntimeError


REQUIRED_UNIT_KINDS = (
    "claim",
    "evidence",
    "unknown",
    "circle-relation",
    "scale-transform",
    "translation-loss",
    "mechanism",
    "branch",
    "residual",
    "forecast",
    "verdict",
    "action",
    "reversal-condition",
)
SUBSTANTIVE_STATUSES = frozenset(
    {
        "applied",
        "retained",
        "tested-rejected",
        "unresolved",
        "unknown-pending",
        "used-in-reasoning",
        "promised-to-reader",
    }
)
NON_SUBSTANTIVE_STATUSES = frozenset({"not-applicable"})
BLIND_READER_FIELDS = (
    "main_verdict",
    "confidence",
    "steelmanned_user_position",
    "decisive_evidence",
    "unknowns",
    "circle_relations",
    "mechanisms",
    "strongest_rival",
    "order_1",
    "order_2",
    "order_3",
    "five_verdicts",
    "action",
    "residuals",
    "reversal_conditions",
)
_BLIND_READER_LABELS = {
    "main_verdict": "主判断",
    "confidence": "置信度",
    "steelmanned_user_position": "用户观点的最强重建",
    "decisive_evidence": "决定性证据",
    "unknowns": "未知项",
    "circle_relations": "圈层关系",
    "mechanisms": "机制",
    "strongest_rival": "最强竞争解释",
    "order_1": "一阶推演",
    "order_2": "二阶推演",
    "order_3": "三阶推演",
    "five_verdicts": "五类裁决",
    "action": "首选行动",
    "residuals": "残差",
    "reversal_conditions": "反转条件",
}
_BLIND_READER_SECTION_TITLES = {
    "main_verdict": REQUIRED_READER_SECTIONS[0],
    "confidence": REQUIRED_READER_SECTIONS[0],
    "steelmanned_user_position": REQUIRED_READER_SECTIONS[1],
    "decisive_evidence": REQUIRED_READER_SECTIONS[2],
    "unknowns": REQUIRED_READER_SECTIONS[2],
    "circle_relations": REQUIRED_READER_SECTIONS[3],
    "mechanisms": REQUIRED_READER_SECTIONS[4],
    "strongest_rival": REQUIRED_READER_SECTIONS[5],
    "order_1": REQUIRED_READER_SECTIONS[6],
    "order_2": REQUIRED_READER_SECTIONS[6],
    "order_3": REQUIRED_READER_SECTIONS[6],
    "residuals": REQUIRED_READER_SECTIONS[7],
    "five_verdicts": REQUIRED_READER_SECTIONS[8],
    "action": REQUIRED_READER_SECTIONS[9],
    "reversal_conditions": REQUIRED_READER_SECTIONS[9],
}
_MAPPING_FIELDS = frozenset(
    {"unit_id", "unit_kind", "section_id", "normalized_excerpt", "source_refs"}
)
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*\Z")
_WHITESPACE_RE = re.compile(r"\s+")
_TEMPLATE_LANGUAGE_RE = re.compile(
    r"在本节中[，,]?我们将|以下将从.{0,24}(?:方面|维度)(?:展开|分析)|"
    r"本文将进行全面分析|首先.{0,20}其次.{0,20}最后"
)
_JARGON_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:Ω|Ψ|Rcc|Rac|Z[_-]?[0-9A-Za-z]+|MC\*|G[1-6]|M[0-9]{2})(?![A-Za-z0-9])"
)
_PLAIN_EXPLANATION_RE = re.compile(r"也就是|这里指|指的是|换句话说|具体来说|表示|记录")
_UNRESOLVED_PRONOUN_RE = re.compile(r"^(?:这|它|其)(?:说明|证明|表明|意味着)")
_CERTAINTY_RE = re.compile(r"毫无疑问|必然(?:会|将|导致|成立)?|确定会|一定会|绝不可能")
_SUPPORT_QUALIFIER_RE = re.compile(r"证据|来源|条件|如果|若|置信|支持|观察|记录|假设")
_EXTERNAL_DEPENDENCY_RE = re.compile(
    r"(?:(?:请|详)?见\s*(?:附件|报告|外部(?:档案|文件)?|档案)|"
    r"参见\s*(?:附件|报告|外部(?:档案|文件)?|档案)|"
    r"附件\s*(?:[A-Za-z0-9_\-\u3400-\u9fff《\"“#（(]|第?\d+))",
    re.IGNORECASE,
)
_EXTERNAL_FILE_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"[A-Za-z0-9_\-\u3400-\u9fff][A-Za-z0-9_\-\u3400-\u9fff .()]*?"
    r"\.(?:pdf|csv|xlsx|docx|json|md)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_CONTEXTUAL_EXTERNAL_FILE_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"[A-Za-z0-9_\-\u3400-\u9fff][A-Za-z0-9_\-\u3400-\u9fff .()]{0,80}?"
    r"\.[A-Za-z][A-Za-z0-9_-]{0,15}(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_EXTERNAL_DOCUMENT_RE = re.compile(
    r"《[^》\n]{1,80}(?:报告|总表|附件|档案|材料|文件|记录)[^》\n]*》|"
    r"(?:内部|外部|年度|季度|调查|审计|统计|数据|排班|项目|工作)?"
    r"[\u3400-\u9fff]{0,10}(?:报告|总表|附件|档案|材料|文件|记录)"
)
_EXTERNAL_SUPPORT_RE = re.compile(
    r"(?:完整|详细|主要|关键)?(?:依据|结论|数据|材料|证据|内容|计算).{0,12}"
    r"(?:载于|收录于|见于|记录于)|"
    r"(?:结论|判断|主张|结果|排序).{0,12}由.{0,50}(?:支持|证实|决定)"
)
_EXTERNAL_OMISSION_RE = re.compile(
    r"(?:本文|文章|文中).{0,12}(?:仅|只).{0,8}(?:给出|提供).{0,8}(?:摘要|概述)|"
    r"(?:本文|文章|文中).{0,16}(?:不再复述|不展开|未复述)|"
    r"(?:不再复述|不展开|仅给出摘要|只给出摘要)"
)
_EXTERNAL_CARRIER_RE = re.compile(
    r"另册|附件|报告|纪要|总表|档案|材料|文件|数据"
)
_EXTERNAL_DEPENDENCE_CUE_RE = re.compile(
    r"保存|载有|载于|收录于|依据|支持|详见|见|完整"
)
_TRUNCATION_RE = re.compile(
    r"篇幅所限|未完待续|下一篇继续|下篇继续|后续(?:再|将)?补充|"
    r"to\s+be\s+continued|\bTBC\b|\[truncated\]",
    re.IGNORECASE,
)
_BLIND_READER_PLACEHOLDER_RE = re.compile(
    r"无法判断|不详|同上|见附件|详见附件|待补充|待定|暂无(?:资料|信息|结论)?"
)
_BLIND_READER_MIN_CONTENT_CHARS = 12
_BLIND_READER_VAGUE_RE = re.compile(
    r"(?:结合|围绕).{0,8}(?:当前|现有|具体)?背景.{0,12}(?:进一步|持续).{0,8}"
    r"(?:讨论|分析|考虑)|需要.{0,10}(?:继续|进一步).{0,6}(?:讨论|分析)"
)
_BLIND_READER_FIELD_ANCHORS: dict[str, tuple[tuple[str, ...], ...]] = {
    "main_verdict": (("支持", "建议", "优先", "应", "维持", "缩小"), ("先", "再", "若", "如果", "时间", "两周")),
    "confidence": (("高", "中", "低", "置信"), ("证据", "记录", "观察", "未知", "缺少", "不足")),
    "steelmanned_user_position": (("用户", "对方", "当事人"), ("担心", "主张", "认为", "要求", "顾虑")),
    "decisive_evidence": (("证据", "记录", "数据", "材料", "观察"), ("显示", "比较", "重复", "发现", "表明")),
    "unknowns": (("未知", "尚不", "尚未", "不知道", "不确定", "缺少", "无法"), ("来自", "原因", "区分", "影响", "是否")),
    "circle_relations": (("圈层", "个人", "团队", "组织", "角色"), ("通道", "连接", "反馈", "约束", "影响")),
    "mechanisms": (("减少", "增加", "扩大", "缩小", "审批", "节点", "等待"), ("导致", "使", "若", "因此", "抵消", "放大")),
    "strongest_rival": (("竞争", "替代", "另一", "可能", "其他"), ("解释", "但是", "但", "不能", "比较", "反例")),
    "order_1": (("会", "将", "若", "保持", "继续"), ("两周", "短期", "直接", "时间", "等待")),
    "order_2": (("若", "会", "扩大", "反转", "协调"), ("新增", "拥堵", "影响", "第二", "之后")),
    "order_3": (("若", "规则", "制度", "长期", "持续"), ("成本", "分工", "退出", "第三", "重组")),
    "five_verdicts": (("事实",), ("预测",), ("价值",), ("责任",), ("授权",)),
    "action": (("行动", "维持", "执行", "记录", "退出", "扩大"), ("若", "如果", "时间", "指标", "再", "停止")),
    "residuals": (("残差", "未解释", "不足", "缺少", "无法"), ("停止", "材料", "影响", "贡献", "进入")),
    "reversal_conditions": (("如果", "若", "条件", "显示", "出现"), ("撤回", "重新", "反转", "比较", "改变")),
}


class SemanticCoverageError(UltraRuntimeError, ValueError):
    """Raised when article semantics are absent, stuffed, or mislocated."""


@dataclass(frozen=True, slots=True)
class SemanticCoverageValidation:
    article_sha256: str
    covered_unit_ids: tuple[str, ...]
    missing_unit_ids: tuple[str, ...]
    coverage_percent: float
    coverage_complete: bool


@dataclass(frozen=True, slots=True)
class ArticleQualityIssue:
    code: str
    evidence: str


@dataclass(frozen=True, slots=True)
class ArticleReview:
    article_sha256: str
    blind_reader_fields: tuple[tuple[str, str], ...]
    blind_reader_evidence: tuple["BlindReaderFieldEvidence", ...]
    quality_issues: tuple[ArticleQualityIssue, ...]
    external_dependencies: tuple[str, ...]
    overall_status: str
    official_filename_allowed: bool
    review_stage: str
    needs_u12_validation: bool
    u12_validator_artifact_required: bool
    blind_recovery_contract_sha256: str | None


@dataclass(frozen=True, slots=True)
class BlindReaderFieldEvidence:
    """Mechanical article-local evidence for one recoverable reader field."""

    field_id: str
    section_id: str
    field_excerpt: str
    support_excerpt: str


@dataclass(frozen=True, slots=True)
class BlindRecoveryFieldContract:
    field_id: str
    expected_normalized_value: str
    section_id: str
    semantic_unit_ids: tuple[str, ...]
    supporting_excerpts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrozenBlindRecoveryContract:
    """U10-frozen mechanical recovery expectations; this is not a U12 verdict."""

    article_sha256: str
    output_plan_sha256: str
    coverage_article_sha256: str
    coverage_validation_sha256: str
    fields: tuple[BlindRecoveryFieldContract, ...]
    contract_sha256: str


def normalize_excerpt(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("excerpt must be text")
    normalized = _WHITESPACE_RE.sub(" ", unicodedata.normalize("NFKC", value)).strip()
    return re.sub(r"(?<=[\u3400-\u9fff]) (?=[\u3400-\u9fff])", "", normalized)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan_sections(output_plan: Mapping[str, object]) -> dict[str, tuple[str, tuple[str, ...]]]:
    sections = _sequence(output_plan.get("sections"), "output plan sections")
    appendices = _sequence(output_plan.get("appendices"), "output plan appendices")
    result: dict[str, tuple[str, tuple[str, ...]]] = {}
    for index, raw in enumerate(tuple(sections) + tuple(appendices), 1):
        entry = _mapping(raw, f"output plan entry {index}")
        section_id = _identifier(entry.get("section_id"), f"output plan entry {index} section_id")
        title = entry.get("title")
        if not isinstance(title, str) or not title:
            raise SemanticCoverageError(f"output plan entry {section_id} has no title")
        unit_ids = _source_refs(
            entry.get("semantic_unit_ids"),
            f"output plan entry {section_id} semantic_unit_ids",
        )
        if not unit_ids:
            raise SemanticCoverageError(
                f"output plan entry {section_id} needs semantic unit IDs"
            )
        if section_id in result:
            raise SemanticCoverageError(f"duplicate output plan section {section_id}")
        result[section_id] = (title, unit_ids)
    return result


def _contract_payload(
    *,
    article_sha256: str,
    output_plan_sha256: str,
    coverage_article_sha256: str,
    coverage_validation_sha256: str,
    fields: Sequence[BlindRecoveryFieldContract],
) -> dict[str, object]:
    return {
        "contract_version": "task11-blind-recovery-v1",
        "article_sha256": article_sha256,
        "output_plan_sha256": output_plan_sha256,
        "coverage_article_sha256": coverage_article_sha256,
        "coverage_validation_sha256": coverage_validation_sha256,
        "fields": [
            {
                "field_id": field.field_id,
                "expected_normalized_value": field.expected_normalized_value,
                "section_id": field.section_id,
                "semantic_unit_ids": list(field.semantic_unit_ids),
                "supporting_excerpts": list(field.supporting_excerpts),
            }
            for field in fields
        ],
    }


def _support_body(section_body: str, label: str) -> str:
    label_line = re.compile(rf"(?m)^\*\*{re.escape(label)}[：:].*$\n?")
    return normalize_excerpt(label_line.sub("", section_body, count=1))


def _contract_fields(
    fields: Sequence[Mapping[str, object]],
    *,
    article_text: str,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
) -> tuple[BlindRecoveryFieldContract, ...]:
    plan_sections = _plan_sections(output_plan)
    sections = extract_reader_sections(article_text, output_plan)
    bodies_by_title = {section.title: section.body for section in sections}
    if len(fields) != len(BLIND_READER_FIELDS):
        raise SemanticCoverageError("blind recovery contract must contain fifteen fields")
    result: list[BlindRecoveryFieldContract] = []
    used_excerpts: set[str] = set()
    used_semantic_unit_ids: set[str] = set()
    for field_id, raw in zip(BLIND_READER_FIELDS, fields, strict=True):
        item = _mapping(raw, f"blind recovery contract field {field_id}")
        if item.get("field_id") != field_id:
            raise SemanticCoverageError(
                f"blind recovery contract fields must use the frozen field order at {field_id}"
            )
        raw_expected = item.get("expected_normalized_value")
        if not isinstance(raw_expected, str):
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} needs an expected value"
            )
        expected = normalize_excerpt(raw_expected)
        if not expected:
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} needs an expected value"
            )
        section_id = _identifier(item.get("section_id"), f"blind recovery contract {field_id} section_id")
        plan_section = plan_sections.get(section_id)
        if plan_section is None:
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} names an unknown section"
            )
        semantic_unit_ids = _source_refs(
            item.get("semantic_unit_ids"), f"blind recovery contract {field_id} semantic_unit_ids"
        )
        if not semantic_unit_ids or not set(semantic_unit_ids).issubset(plan_section[1]):
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} uses semantic units outside its section"
            )
        if not set(semantic_unit_ids).issubset(coverage_validation.covered_unit_ids):
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} uses semantic units absent from coverage"
            )
        if used_semantic_unit_ids.intersection(semantic_unit_ids):
            raise SemanticCoverageError(
                "blind recovery contract cannot reuse semantic units across fields"
            )
        used_semantic_unit_ids.update(semantic_unit_ids)
        excerpts = _sequence(
            item.get("supporting_excerpts"),
            f"blind recovery contract {field_id} supporting_excerpts",
        )
        normalized_excerpts = tuple(normalize_excerpt(value) for value in excerpts)
        if not normalized_excerpts or any(not excerpt for excerpt in normalized_excerpts):
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} needs supporting excerpts"
            )
        if len(set(normalized_excerpts)) != len(normalized_excerpts):
            raise SemanticCoverageError(
                f"blind recovery contract {field_id} repeats supporting excerpts"
            )
        support_body = _support_body(
            bodies_by_title[plan_section[0]], _BLIND_READER_LABELS[field_id]
        )
        for excerpt in normalized_excerpts:
            if support_body.count(excerpt) != 1:
                raise SemanticCoverageError(
                    f"blind recovery contract {field_id} support excerpt is not unique in its section"
                )
            if excerpt in used_excerpts:
                raise SemanticCoverageError(
                    "blind recovery contract cannot reuse supporting excerpts"
                )
            used_excerpts.add(excerpt)
        result.append(
            BlindRecoveryFieldContract(
                field_id=field_id,
                expected_normalized_value=expected,
                section_id=section_id,
                semantic_unit_ids=semantic_unit_ids,
                supporting_excerpts=normalized_excerpts,
            )
        )
    return tuple(result)


def freeze_blind_recovery_contract(
    article_text: str,
    *,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
    fields: Sequence[Mapping[str, object]],
) -> FrozenBlindRecoveryContract:
    """Freeze U10 recovery expectations against the exact plan, article, and coverage."""
    if not isinstance(coverage_validation, SemanticCoverageValidation):
        raise TypeError("coverage_validation must be a SemanticCoverageValidation")
    article_sha256 = hashlib.sha256(article_text.encode("utf-8")).hexdigest()
    if coverage_validation.article_sha256 != article_sha256:
        raise SemanticCoverageError("blind recovery contract coverage is not bound to article")
    frozen_fields = _contract_fields(
        _sequence(fields, "blind recovery contract fields"),
        article_text=article_text,
        output_plan=output_plan,
        coverage_validation=coverage_validation,
    )
    output_plan_sha256 = _canonical_sha256(output_plan)
    coverage_validation_sha256 = _canonical_sha256(
        {
            "article_sha256": coverage_validation.article_sha256,
            "covered_unit_ids": list(coverage_validation.covered_unit_ids),
            "missing_unit_ids": list(coverage_validation.missing_unit_ids),
            "coverage_percent": coverage_validation.coverage_percent,
            "coverage_complete": coverage_validation.coverage_complete,
        }
    )
    payload = _contract_payload(
        article_sha256=article_sha256,
        output_plan_sha256=output_plan_sha256,
        coverage_article_sha256=coverage_validation.article_sha256,
        coverage_validation_sha256=coverage_validation_sha256,
        fields=frozen_fields,
    )
    return FrozenBlindRecoveryContract(
        article_sha256=article_sha256,
        output_plan_sha256=output_plan_sha256,
        coverage_article_sha256=coverage_validation.article_sha256,
        coverage_validation_sha256=coverage_validation_sha256,
        fields=frozen_fields,
        contract_sha256=_canonical_sha256(payload),
    )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SemanticCoverageError(f"{label} must be a mapping")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise SemanticCoverageError(f"{label} must be an array")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise SemanticCoverageError(f"{label} must be a valid identifier")
    return value


def _source_refs(value: object, label: str) -> tuple[str, ...]:
    items = _sequence(value, label)
    result = tuple(_identifier(item, f"{label} item") for item in items)
    if len(result) != len(set(result)):
        raise SemanticCoverageError(f"{label} contains duplicate source references")
    return result


def _is_substantive(unit: Mapping[str, object]) -> bool:
    status = unit.get("status")
    if status not in SUBSTANTIVE_STATUSES | NON_SUBSTANTIVE_STATUSES:
        raise SemanticCoverageError(
            f"substantive unit status is invalid or missing: {status!r}"
        )
    if status in SUBSTANTIVE_STATUSES:
        return True
    for flag in ("affects_ranking", "used_in_reasoning", "promised_to_reader"):
        value = unit.get(flag, False)
        if type(value) is not bool:
            raise SemanticCoverageError(f"substantive unit {flag} must be boolean")
        if value:
            raise SemanticCoverageError(
                f"not-applicable unit cannot set substantive flag {flag}"
            )
    return False


def validate_semantic_coverage(
    article_text: str,
    output_plan: Mapping[str, object],
    substantive_units: Sequence[Mapping[str, object]],
    mappings: Sequence[Mapping[str, object]],
) -> SemanticCoverageValidation:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    sections = extract_reader_sections(article_text, output_plan)
    section_by_id = {section.section_id: section for section in sections}

    units_by_id: dict[str, tuple[str, bool]] = {}
    required_ids: list[str] = []
    required_kinds: set[str] = set()
    for index, raw in enumerate(_sequence(substantive_units, "substantive units")):
        unit = _mapping(raw, f"substantive unit {index}")
        unit_id = _identifier(unit.get("unit_id"), f"substantive unit {index} unit_id")
        if unit_id in units_by_id:
            raise SemanticCoverageError(f"duplicate substantive unit: {unit_id}")
        unit_kind = unit.get("unit_kind")
        if unit_kind not in REQUIRED_UNIT_KINDS:
            raise SemanticCoverageError(
                f"substantive unit {unit_id} has unsupported unit kind {unit_kind!r}"
            )
        required = _is_substantive(unit)
        units_by_id[unit_id] = (str(unit_kind), required)
        if required:
            required_ids.append(unit_id)
            required_kinds.add(str(unit_kind))

    missing_kinds = tuple(
        unit_kind
        for unit_kind in REQUIRED_UNIT_KINDS
        if unit_kind not in required_kinds
    )
    if missing_kinds:
        raise SemanticCoverageError(
            f"semantic coverage is missing required unit kinds: {list(missing_kinds)}"
        )

    covered: list[str] = []
    seen_mappings: set[str] = set()
    last_position: tuple[int, int] | None = None
    for index, raw in enumerate(_sequence(mappings, "semantic coverage mappings")):
        mapping = _mapping(raw, f"semantic coverage mapping {index}")
        keys = frozenset(mapping.keys())
        if keys != _MAPPING_FIELDS:
            raise SemanticCoverageError(
                f"semantic coverage mapping {index} has an invalid field set"
            )
        unit_id = _identifier(mapping.get("unit_id"), f"mapping {index} unit_id")
        if unit_id in seen_mappings:
            raise SemanticCoverageError(
                f"duplicate semantic coverage mapping: {unit_id}"
            )
        seen_mappings.add(unit_id)
        unit_record = units_by_id.get(unit_id)
        if unit_record is None:
            raise SemanticCoverageError(
                f"unexpected or unknown coverage unit: {unit_id}"
            )
        expected_kind, required = unit_record
        if not required:
            raise SemanticCoverageError(
                f"coverage mapping {unit_id} does not refer to a required substantive unit"
            )
        unit_kind = mapping.get("unit_kind")
        if unit_kind != expected_kind:
            raise SemanticCoverageError(
                f"coverage unit kind mismatch for {unit_id}: {unit_kind!r}"
            )
        section_id = _identifier(
            mapping.get("section_id"), f"mapping {unit_id} section_id"
        )
        section = section_by_id.get(section_id)
        if section is None:
            raise SemanticCoverageError(
                f"coverage mapping {unit_id} names an unknown article section"
            )
        excerpt = mapping.get("normalized_excerpt")
        if not isinstance(excerpt, str) or not excerpt:
            raise SemanticCoverageError(
                f"coverage excerpt for {unit_id} must be non-empty"
            )
        normalized_excerpt = normalize_excerpt(excerpt)
        if normalized_excerpt != excerpt:
            raise SemanticCoverageError(
                f"coverage excerpt for {unit_id} is not normalized prose"
            )
        if normalized_excerpt == normalize_excerpt(section.title):
            raise SemanticCoverageError(
                f"coverage excerpt for {unit_id} is only a heading, not reader prose"
            )
        normalized_body = normalize_excerpt(section.body)
        occurrence = normalized_body.find(normalized_excerpt)
        if occurrence < 0:
            raise SemanticCoverageError(
                f"coverage excerpt for {unit_id} does not occur in section {section_id}"
            )
        if normalized_body.count(normalized_excerpt) != 1:
            raise SemanticCoverageError(
                f"coverage excerpt for {unit_id} does not identify one exact occurrence"
            )
        position = (section.ordinal, occurrence)
        if last_position is not None and position < last_position:
            raise SemanticCoverageError(
                f"coverage mappings are out of normalized article occurrence order at {unit_id}"
            )
        last_position = position
        _source_refs(mapping.get("source_refs"), f"mapping {unit_id} source_refs")
        covered.append(unit_id)

    missing = tuple(unit_id for unit_id in required_ids if unit_id not in seen_mappings)
    if missing:
        raise SemanticCoverageError(
            f"semantic coverage is missing required units: {list(missing)}"
        )
    return SemanticCoverageValidation(
        article_sha256=hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
        covered_unit_ids=tuple(covered),
        missing_unit_ids=(),
        coverage_percent=100.0,
        coverage_complete=True,
    )


def _paragraphs(article_text: str) -> tuple[str, ...]:
    paragraphs: list[str] = []
    for raw in re.split(r"\n[ \t]*\n", article_text):
        value = normalize_excerpt(raw)
        if value and not value.startswith("## "):
            paragraphs.append(value)
    return tuple(paragraphs)


def detect_external_dependencies(article_text: str) -> tuple[str, ...]:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    matches = [
        match.group(0).strip()
        for pattern in (_EXTERNAL_FILE_REFERENCE_RE, _EXTERNAL_DEPENDENCY_RE)
        for match in pattern.finditer(article_text)
        if match.group(0).strip()
    ]
    sentences = tuple(
        normalize_excerpt(sentence)
        for sentence in re.split(r"(?<=[。！？!?])|\n+", article_text)
        if normalize_excerpt(sentence)
    )
    for index, sentence in enumerate(sentences):
        normalized = " ".join(sentences[index : index + 2])
        document = _EXTERNAL_DOCUMENT_RE.search(normalized)
        has_omission = _EXTERNAL_OMISSION_RE.search(normalized) is not None
        contextual_file = _CONTEXTUAL_EXTERNAL_FILE_RE.search(normalized)
        if (
            document is not None
            and (_EXTERNAL_SUPPORT_RE.search(normalized) or has_omission)
        ) or (
            has_omission
            and _EXTERNAL_CARRIER_RE.search(normalized)
            and _EXTERNAL_DEPENDENCE_CUE_RE.search(normalized)
        ) or (
            has_omission
            and contextual_file is not None
            and _EXTERNAL_DEPENDENCE_CUE_RE.search(normalized)
        ):
            matches.append(
                contextual_file.group(0) if contextual_file is not None else normalized
            )
    return tuple(dict.fromkeys(matches))


def inspect_article_quality(
    article_text: str,
    *,
    external_dependencies: Sequence[str] = (),
) -> tuple[ArticleQualityIssue, ...]:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    dependencies = _sequence(external_dependencies, "external dependencies")
    for dependency in dependencies:
        if not isinstance(dependency, str) or not dependency.strip():
            raise SemanticCoverageError(
                "external dependency names must be non-empty strings"
            )

    issues: list[ArticleQualityIssue] = []
    issue_codes: set[str] = set()

    def add(code: str, evidence: str) -> None:
        if code not in issue_codes:
            issue_codes.add(code)
            issues.append(ArticleQualityIssue(code=code, evidence=evidence))

    paragraphs = _paragraphs(article_text)
    seen: set[str] = set()
    for paragraph in paragraphs:
        if len(paragraph) >= 12 and paragraph in seen:
            add("repeated-paragraph", paragraph[:120])
            break
        seen.add(paragraph)
    if _TEMPLATE_LANGUAGE_RE.search(article_text):
        add("template-language", "article contains generic template language")
    jargon_match = _JARGON_RE.search(article_text)
    if jargon_match is not None:
        paragraph_start = article_text.rfind("\n\n", 0, jargon_match.start()) + 2
        explanation_before = article_text[paragraph_start : jargon_match.start()]
        if _PLAIN_EXPLANATION_RE.search(explanation_before) is None:
            add(
                "jargon-before-explanation",
                f"jargon appears before a plain explanation: {jargon_match.group(0)}",
            )
    for paragraph in paragraphs:
        plain = paragraph.removeprefix("## ").strip()
        if _UNRESOLVED_PRONOUN_RE.match(plain):
            add("unresolved-pronoun", plain[:120])
            break
    for paragraph in paragraphs:
        if (
            _CERTAINTY_RE.search(paragraph)
            and _SUPPORT_QUALIFIER_RE.search(paragraph) is None
        ):
            add("unsupported-certainty", paragraph[:120])
            break
    detected_dependencies = detect_external_dependencies(article_text)
    if detected_dependencies:
        add("external-dependency", ", ".join(detected_dependencies))
    if _TRUNCATION_RE.search(article_text):
        add(
            "truncation-promise", "complete article promises omitted or continued prose"
        )
    if contains_machine_dump(article_text):
        add("machine-dump", "reader prose contains a JSON or schema dump")
    return tuple(issues)


_CONCRETE_SPAN_RE = re.compile(r"[A-Za-z0-9\u3400-\u9fff]{5,}")


def _support_excerpt_for_field(value: str, section_body: str, label_match: re.Match[str]) -> str:
    line_end = section_body.find("\n", label_match.end())
    if line_end < 0:
        line_end = len(section_body)
    support_body = section_body[: label_match.start()] + section_body[line_end:]
    normalized_support = normalize_excerpt(support_body)
    normalized_value = normalize_excerpt(value)
    for span in _CONCRETE_SPAN_RE.findall(normalized_value):
        maximum = min(len(span), 24)
        for width in range(maximum, 4, -1):
            for offset in range(0, len(span) - width + 1):
                candidate = span[offset : offset + width]
                if normalized_support.count(candidate) == 1:
                    return candidate
    raise SemanticCoverageError(
        "blind-reader field lacks a concrete article-local support excerpt"
    )


def recover_blind_reader_field_evidence(
    article_text: str,
) -> tuple[BlindReaderFieldEvidence, ...]:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    heading_matches = list(re.finditer(r"(?m)^## ([^\n]+)$", article_text))
    expected_titles = REQUIRED_READER_SECTIONS + REQUIRED_READER_APPENDICES
    actual_titles = tuple(match.group(1).strip() for match in heading_matches)
    if actual_titles != expected_titles:
        raise SemanticCoverageError(
            "blind reader cannot recover fields from an incomplete reader-section sequence"
        )
    section_ranges: dict[str, tuple[int, int]] = {}
    for index, match in enumerate(heading_matches):
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(article_text)
        )
        section_ranges[match.group(1).strip()] = (match.end(), end)
    recovered: dict[str, str] = {}
    evidence: list[BlindReaderFieldEvidence] = []
    normalized_recovered_values: set[str] = set()
    used_support_excerpts: set[str] = set()
    for field_id in BLIND_READER_FIELDS:
        label = _BLIND_READER_LABELS[field_id]
        pattern = re.compile(rf"(?m)^\*\*{re.escape(label)}[：:]\*\*[ \t]*(.*)$")
        matches = list(pattern.finditer(article_text))
        if not matches:
            raise SemanticCoverageError(f"blind reader cannot recover {field_id}")
        if len(matches) != 1:
            raise SemanticCoverageError(f"duplicate blind-reader label for {field_id}")
        expected_title = _BLIND_READER_SECTION_TITLES[field_id]
        section_start, section_end = section_ranges[expected_title]
        if not section_start <= matches[0].start() < section_end:
            raise SemanticCoverageError(
                f"blind-reader field {field_id} is outside its required section {expected_title}"
            )
        value = matches[0].group(1).strip()
        if not value:
            raise SemanticCoverageError(f"blind-reader field {field_id} is empty")
        normalized_value = normalize_excerpt(value)
        content_chars = sum(
            character.isalnum() or "\u3400" <= character <= "\u9fff"
            for character in normalized_value
        )
        if content_chars < _BLIND_READER_MIN_CONTENT_CHARS:
            raise SemanticCoverageError(
                f"blind-reader field {field_id} is too short for specific recovery"
            )
        if _BLIND_READER_PLACEHOLDER_RE.search(normalized_value):
            raise SemanticCoverageError(
                f"blind-reader field {field_id} contains a placeholder instead of specific recovery"
            )
        _validate_blind_reader_field(field_id, normalized_value)
        if normalized_value in normalized_recovered_values:
            raise SemanticCoverageError(
                f"blind-reader field {field_id} repeats another field's boilerplate"
            )
        section_body = article_text[section_start:section_end]
        relative_match = re.compile(
            rf"(?m)^\*\*{re.escape(label)}[：:]\*\*[ \t]*(.*)$"
        ).search(section_body)
        if relative_match is None:
            raise SemanticCoverageError(
                f"blind-reader field {field_id} cannot locate its section-local excerpt"
            )
        support_excerpt = _support_excerpt_for_field(
            value, section_body, relative_match
        )
        if support_excerpt in used_support_excerpts:
            raise SemanticCoverageError(
                f"blind-reader field {field_id} reuses another field's support excerpt"
            )
        recovered[field_id] = value
        evidence.append(
            BlindReaderFieldEvidence(
                field_id=field_id,
                section_id=expected_title,
                field_excerpt=value,
                support_excerpt=support_excerpt,
            )
        )
        normalized_recovered_values.add(normalized_value)
        used_support_excerpts.add(support_excerpt)
    return tuple(evidence)


def recover_blind_reader_fields(article_text: str) -> dict[str, str]:
    evidence = recover_blind_reader_field_evidence(article_text)
    return {item.field_id: item.field_excerpt for item in evidence}


def validate_frozen_blind_recovery_contract(
    article_text: str,
    *,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
    blind_recovery_contract: FrozenBlindRecoveryContract,
) -> tuple[BlindReaderFieldEvidence, ...]:
    if not isinstance(blind_recovery_contract, FrozenBlindRecoveryContract):
        raise TypeError("blind_recovery_contract must be a FrozenBlindRecoveryContract")
    if not isinstance(coverage_validation, SemanticCoverageValidation):
        raise TypeError("coverage_validation must be a SemanticCoverageValidation")
    article_sha256 = hashlib.sha256(article_text.encode("utf-8")).hexdigest()
    coverage_validation_sha256 = _canonical_sha256(
        {
            "article_sha256": coverage_validation.article_sha256,
            "covered_unit_ids": list(coverage_validation.covered_unit_ids),
            "missing_unit_ids": list(coverage_validation.missing_unit_ids),
            "coverage_percent": coverage_validation.coverage_percent,
            "coverage_complete": coverage_validation.coverage_complete,
        }
    )
    if (
        blind_recovery_contract.article_sha256 != article_sha256
        or blind_recovery_contract.coverage_article_sha256 != coverage_validation.article_sha256
        or blind_recovery_contract.coverage_validation_sha256 != coverage_validation_sha256
        or blind_recovery_contract.output_plan_sha256 != _canonical_sha256(output_plan)
    ):
        raise SemanticCoverageError(
            "blind recovery contract is not bound to this article, output plan, and coverage"
        )
    payload = _contract_payload(
        article_sha256=blind_recovery_contract.article_sha256,
        output_plan_sha256=blind_recovery_contract.output_plan_sha256,
        coverage_article_sha256=blind_recovery_contract.coverage_article_sha256,
        coverage_validation_sha256=blind_recovery_contract.coverage_validation_sha256,
        fields=blind_recovery_contract.fields,
    )
    if blind_recovery_contract.contract_sha256 != _canonical_sha256(payload):
        raise SemanticCoverageError("blind recovery contract hash is stale")
    plan_sections = _plan_sections(output_plan)
    raw_evidence = recover_blind_reader_field_evidence(article_text)
    if tuple(item.field_id for item in raw_evidence) != BLIND_READER_FIELDS:
        raise SemanticCoverageError("blind recovery fields do not have frozen order")
    if tuple(field.field_id for field in blind_recovery_contract.fields) != BLIND_READER_FIELDS:
        raise SemanticCoverageError("blind recovery contract fields do not have frozen order")
    evidence: list[BlindReaderFieldEvidence] = []
    used_excerpts: set[str] = set()
    used_semantic_unit_ids: set[str] = set()
    for recovered, field in zip(raw_evidence, blind_recovery_contract.fields, strict=True):
        expected_section = plan_sections.get(field.section_id)
        if expected_section is None or recovered.section_id != expected_section[0]:
            raise SemanticCoverageError(
                f"blind recovery contract {field.field_id} names the wrong section"
            )
        if normalize_excerpt(recovered.field_excerpt) != field.expected_normalized_value:
            raise SemanticCoverageError(
                f"blind recovery contract {field.field_id} does not match its expected proposition"
            )
        if not set(field.semantic_unit_ids).issubset(expected_section[1]) or not set(
            field.semantic_unit_ids
        ).issubset(coverage_validation.covered_unit_ids):
            raise SemanticCoverageError(
                f"blind recovery contract {field.field_id} has unverified semantic units"
            )
        if used_semantic_unit_ids.intersection(field.semantic_unit_ids):
            raise SemanticCoverageError(
                f"blind recovery contract {field.field_id} reuses a semantic unit"
            )
        used_semantic_unit_ids.update(field.semantic_unit_ids)
        sections = extract_reader_sections(article_text, output_plan)
        body_by_title = {section.title: section.body for section in sections}
        support_body = _support_body(
            body_by_title[expected_section[0]], _BLIND_READER_LABELS[field.field_id]
        )
        matched_support = next(
            (
                excerpt
                for excerpt in field.supporting_excerpts
                if support_body.count(excerpt) == 1 and excerpt not in used_excerpts
            ),
            None,
        )
        if matched_support is None:
            raise SemanticCoverageError(
                f"blind recovery contract {field.field_id} has no unique supporting excerpt"
            )
        used_excerpts.add(matched_support)
        evidence.append(
            BlindReaderFieldEvidence(
                field_id=recovered.field_id,
                section_id=field.section_id,
                field_excerpt=recovered.field_excerpt,
                support_excerpt=matched_support,
            )
        )
    return tuple(evidence)


def _validate_blind_reader_field(field_id: str, value: str) -> None:
    if _BLIND_READER_VAGUE_RE.search(value):
        raise SemanticCoverageError(
            f"blind-reader field {field_id} lacks field-specific information anchors"
        )
    anchor_groups = _BLIND_READER_FIELD_ANCHORS[field_id]
    if any(not any(anchor in value for anchor in group) for group in anchor_groups):
        raise SemanticCoverageError(
            f"blind-reader field {field_id} lacks field-specific information anchors"
        )


def review_article(
    article_text: str,
    *,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
    blind_recovery_contract: FrozenBlindRecoveryContract,
    external_dependencies: Sequence[str] = (),
) -> ArticleReview:
    """Run Task 11 mechanical prechecks; U12 remains the only semantic authority."""
    return _review_article(
        article_text,
        output_plan=output_plan,
        coverage_validation=coverage_validation,
        blind_recovery_contract=blind_recovery_contract,
        external_dependencies=external_dependencies,
    )


def _review_article(
    article_text: str,
    *,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
    blind_recovery_contract: FrozenBlindRecoveryContract,
    external_dependencies: Sequence[str],
) -> ArticleReview:
    if not isinstance(coverage_validation, SemanticCoverageValidation):
        raise TypeError("coverage_validation must be a SemanticCoverageValidation")
    dependencies = tuple(external_dependencies)
    detected_dependencies = detect_external_dependencies(article_text)
    quality_issues = list(
        inspect_article_quality(article_text, external_dependencies=dependencies)
    )
    try:
        validate_reader_article(article_text)
    except ValueError as error:
        quality_issues.append(
            ArticleQualityIssue(code="reader-contract", evidence=str(error))
        )
    try:
        blind_reader_evidence = validate_frozen_blind_recovery_contract(
            article_text,
            output_plan=output_plan,
            coverage_validation=coverage_validation,
            blind_recovery_contract=blind_recovery_contract,
        )
        recovered = {
            item.field_id: item.field_excerpt for item in blind_reader_evidence
        }
    except ValueError as error:
        recovered = {}
        blind_reader_evidence = ()
        quality_issues.append(
            ArticleQualityIssue(code="blind-recovery-contract", evidence=str(error))
        )
    article_sha256 = hashlib.sha256(article_text.encode("utf-8")).hexdigest()
    if (
        coverage_validation.article_sha256 != article_sha256
        or coverage_validation.coverage_complete is not True
        or coverage_validation.coverage_percent != 100.0
        or coverage_validation.missing_unit_ids
        or not coverage_validation.covered_unit_ids
    ):
        quality_issues.append(
            ArticleQualityIssue(
                code="semantic-coverage-unverified",
                evidence=(
                    "Task 11 review requires a hash-bound, complete semantic coverage "
                    "validation for this exact article"
                ),
            )
        )
    deduplicated: list[ArticleQualityIssue] = []
    seen_codes: set[str] = set()
    for issue in quality_issues:
        if issue.code not in seen_codes:
            seen_codes.add(issue.code)
            deduplicated.append(issue)
    overall_status = "mechanical-complete" if not deduplicated else "mechanical-fail"
    return ArticleReview(
        article_sha256=article_sha256,
        blind_reader_fields=tuple(
            (field_id, recovered[field_id])
            for field_id in BLIND_READER_FIELDS
            if field_id in recovered
        ),
        blind_reader_evidence=blind_reader_evidence,
        quality_issues=tuple(deduplicated),
        external_dependencies=detected_dependencies,
        overall_status=overall_status,
        official_filename_allowed=False,
        review_stage="mechanical-precheck",
        needs_u12_validation=True,
        u12_validator_artifact_required=True,
        blind_recovery_contract_sha256=(
            blind_recovery_contract.contract_sha256
            if isinstance(blind_recovery_contract, FrozenBlindRecoveryContract)
            else None
        ),
    )


def review_article_in_clean_room(
    article_path: Path,
    *,
    output_plan: Mapping[str, object],
    coverage_validation: SemanticCoverageValidation,
    blind_recovery_contract: FrozenBlindRecoveryContract,
) -> ArticleReview:
    if not isinstance(article_path, Path):
        raise TypeError("article_path must be a pathlib.Path")
    if not article_path.is_file():
        raise SemanticCoverageError("article_path must name a readable article file")
    with tempfile.TemporaryDirectory(prefix="crossframe-ultra-blind-reader-") as root:
        isolated_article = Path(root) / "article.md"
        shutil.copyfile(article_path, isolated_article)
        return _review_article(
            isolated_article.read_text(encoding="utf-8"),
            output_plan=output_plan,
            coverage_validation=coverage_validation,
            blind_recovery_contract=blind_recovery_contract,
            external_dependencies=(),
        )


__all__ = (
    "ArticleQualityIssue",
    "ArticleReview",
    "BLIND_READER_FIELDS",
    "BlindReaderFieldEvidence",
    "BlindRecoveryFieldContract",
    "FrozenBlindRecoveryContract",
    "NON_SUBSTANTIVE_STATUSES",
    "REQUIRED_UNIT_KINDS",
    "SUBSTANTIVE_STATUSES",
    "SemanticCoverageError",
    "SemanticCoverageValidation",
    "detect_external_dependencies",
    "freeze_blind_recovery_contract",
    "inspect_article_quality",
    "normalize_excerpt",
    "recover_blind_reader_fields",
    "recover_blind_reader_field_evidence",
    "review_article",
    "review_article_in_clean_room",
    "validate_semantic_coverage",
    "validate_frozen_blind_recovery_contract",
)
