from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

from jsonschema import ValidationError

from .errors import UltraRuntimeError
from .jsonio import atomic_write_bytes, canonical_json_bytes, sha256_bytes
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


REQUIRED_READER_SECTIONS = (
    "主判断、范围和置信度",
    "用户观点的最强重建",
    "事实、证据、来源关系和未知项",
    "立体多圈层联合状态",
    "机制、真实通道和跨圈层级联",
    "竞争解释与排序",
    "一阶、二阶、三阶推演",
    "每阶简单基线、增量和停止理由",
    "事实、预测、价值、责任、授权裁决",
    "行动、不行动、切换和反转条件",
)
REQUIRED_READER_APPENDICES = (
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差和停止点",
    "预测、时间窗、指标和解析条件",
    "概念、证据和来源锚点",
    "未知项与框架缺口候选",
)
U10_OUTPUT_PLAN_PATH = "work/authoring/U10-output-plan.json"
ARTICLE_PACKET_DIRECTORY = "work/authoring/article/packets"
OFFICIAL_ARTICLE_FILENAME = "CrossFrame-Ultra-完整文章.md"

SEMANTIC_UNIT_KINDS = (
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
BLIND_RECOVERY_FIELD_IDS = (
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
QUALITY_DIMENSIONS = (
    "direct-answer",
    "evidence-boundary",
    "mechanism-competition",
    "recursive-expansion",
    "reversal-conditions",
    "action-comparison",
    "reader-independence",
)

_PACKET_FIELDS = frozenset(
    {
        "packet_id",
        "section_id",
        "ordinal",
        "dependency_hashes",
        "semantic_unit_ids",
        "source_refs",
        "prose",
        "prose_sha256",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*\Z")
_HEADING_RE = re.compile(r"(?m)^## ([^\n]+)$")
_INTERNAL_FIELD_RE = re.compile(
    r"\b(?:main_verdict|dependency_hashes|semantic_unit_ids|source_refs|"
    r"article_sha256|coverage_complete|normalized_excerpt|unit_id|section_id|"
    r"packet_id|prose_sha256|official_filename_allowed)\b"
)
_TRUNCATION_RE = re.compile(
    r"篇幅所限|未完待续|下一篇继续|下篇继续|后续(?:再|将)?补充|"
    r"to\s+be\s+continued|\bTBC\b|\[truncated\]",
    re.IGNORECASE,
)
_CONCEPT_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])[A-Z][A-Z0-9-]*\d+[A-Z0-9-]*(?![A-Za-z0-9])"
)
_CONCEPT_NAME_RE = re.compile(
    r"边界|嵌入|外溢|递归|转义|锁定|同构|尺度变换|关系重构|圈层"
)
_CONCRETE_ROLE_RE = re.compile(
    r"作用|用于|表示|记录|检验|连接|限制|支持|拒绝|应用|承担|解释|导致|改变"
)
_RAW_JSON_RE = re.compile(
    r"(?m)^[ \t]*(?:\{[^\n{}]*\"[^\"]+\"[ \t]*:|\[[ \t]*(?:\"|\{))"
)
_MULTILINE_JSON_OBJECT_RE = re.compile(
    r"(?m)^[ \t]*\{[ \t]*\n"
    r"[ \t]*\"[^\"\n]+\"[ \t]*:[^\n]+,[ \t]*\n"
    r"[ \t]*\"[^\"\n]+\"[ \t]*:"
)
_MULTILINE_JSON_ARRAY_RE = re.compile(
    r"(?m)^[ \t]*\[[ \t]*\n[ \t]*\{[ \t]*\n"
    r"[ \t]*\"[^\"\n]+\"[ \t]*:"
)
_MACHINE_ASSIGNMENT_LINE_RE = re.compile(
    r"^[ \t]*(?:-\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_.-]*|[\u3400-\u9fff]{2,16})"
    r"[ \t]*(?P<separator>[:=：])[ \t]*(?P<value>[^\n]+?)[ \t]*$"
)
_MACHINE_MAPPING_START_RE = re.compile(
    r"^[ \t]*(?:-\s+)?(?:[A-Za-z_][A-Za-z0-9_.-]*|[\u3400-\u9fff]{2,16})[ \t]*[:：][ \t]*$"
)
_MACHINE_SECTION_RE = re.compile(r"^[ \t]*\[[A-Za-z_][A-Za-z0-9_.-]*\][ \t]*$")
_MACHINE_BARE_LIST_ITEM_RE = re.compile(r"^[ \t]+-\s+[A-Za-z0-9_.-]+[ \t]*$")
_MACHINE_SCALAR_RE = re.compile(
    r'(?:"[^"\n]{0,80}"|\'[^\'\n]{0,80}\'|[A-Za-z0-9_.:/-]{1,80}|[\u3400-\u9fffA-Za-z0-9_.:/-]{1,40})\Z',
    re.IGNORECASE,
)
_MACHINE_METADATA_KEYS = frozenset(
    {
        "count",
        "id",
        "record",
        "schema",
        "source",
        "state",
        "status",
        "type",
        "version",
    }
)


class ArticleContractError(UltraRuntimeError, ValueError):
    """Raised when a frozen article packet or reader contract is invalid."""


@dataclass(frozen=True, slots=True)
class AssembledArticle:
    article_text: str
    article_sha256: str
    packet_ids: tuple[str, ...]
    semantic_unit_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReaderSection:
    section_id: str
    title: str
    ordinal: int
    body: str


@dataclass(frozen=True, slots=True)
class _PlanEntry:
    section_id: str
    title: str
    ordinal: int
    semantic_unit_ids: tuple[str, ...]
    dependency_hashes: tuple[str, ...]


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ArticleContractError(f"{label} must be a mapping")
    return value


def _require_sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ArticleContractError(f"{label} must be an array")
    return value


def _bounded_packet_items(value: object, *, expected_count: int) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise ArticleContractError("article packets must be an iterable of mappings")
    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise ArticleContractError(
            "article packets must be an iterable of mappings"
        ) from error
    items: list[object] = []
    for _ in range(expected_count + 1):
        try:
            items.append(next(iterator))
        except StopIteration:
            break
    if len(items) > expected_count:
        raise ArticleContractError(
            f"article packet iterable has more than {expected_count} packets"
        )
    return tuple(items)


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise ArticleContractError(f"{label} must be a valid identifier")
    return value


def _require_ordinal(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ArticleContractError(f"{label} must be a positive integer ordinal")
    return value


def _require_string_tuple(
    value: object,
    label: str,
    *,
    allow_empty: bool,
    identifiers: bool = False,
    hashes: bool = False,
) -> tuple[str, ...]:
    items = _require_sequence(value, label)
    if not allow_empty and not items:
        raise ArticleContractError(f"{label} must not be empty")
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item:
            raise ArticleContractError(f"{label}[{index}] must be a non-empty string")
        if identifiers and _IDENTIFIER_RE.fullmatch(item) is None:
            raise ArticleContractError(f"{label}[{index}] is not a valid identifier")
        if hashes and _SHA256_RE.fullmatch(item) is None:
            raise ArticleContractError(f"{label}[{index}] is not a SHA-256 digest")
        result.append(item)
    if len(set(result)) != len(result):
        raise ArticleContractError(f"{label} contains duplicate values")
    return tuple(result)


def _require_artifact_tuple(
    value: object, label: str
) -> tuple[Mapping[str, str], ...]:
    items = _require_sequence(value, label)
    if not items:
        raise ArticleContractError(f"{label} must not be empty")
    result: list[Mapping[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(items):
        item = _require_mapping(raw, f"{label}[{index}]")
        if frozenset(item) != {"path", "sha256", "media_type"}:
            raise ArticleContractError(
                f"{label}[{index}] must contain only path, sha256, and media_type"
            )
        path = item.get("path")
        digest = item.get("sha256")
        media_type = item.get("media_type")
        if not isinstance(path, str) or not path.strip():
            raise ArticleContractError(f"{label}[{index}] path must be non-empty")
        if (
            path.startswith(("/", "\\"))
            or re.match(r"^[A-Za-z]:", path)
            or any(part in {"", ".", ".."} for part in re.split(r"[/\\]", path))
        ):
            raise ArticleContractError(f"{label}[{index}] path must be relative and canonical")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ArticleContractError(f"{label}[{index}] sha256 is invalid")
        if (
            not isinstance(media_type, str)
            or not media_type.strip()
            or "/" not in media_type
        ):
            raise ArticleContractError(f"{label}[{index}] media_type is invalid")
        key = (path, digest, media_type)
        if key in seen:
            raise ArticleContractError(f"{label} contains duplicate artifact objects")
        seen.add(key)
        result.append(
            MappingProxyType(
                {"path": path, "sha256": digest, "media_type": media_type}
            )
        )
    return tuple(result)


def _reader_plan_entries(
    output_plan: Mapping[str, object], *, require_packet_fields: bool
) -> tuple[_PlanEntry, ...]:
    plan = _require_mapping(output_plan, "output plan")
    sections = _require_sequence(plan.get("sections"), "output plan sections")
    appendices = _require_sequence(plan.get("appendices"), "output plan appendices")
    if len(sections) != len(REQUIRED_READER_SECTIONS):
        raise ArticleContractError(
            f"output plan must contain {len(REQUIRED_READER_SECTIONS)} reader sections"
        )
    if len(appendices) != len(REQUIRED_READER_APPENDICES):
        raise ArticleContractError(
            f"output plan must contain {len(REQUIRED_READER_APPENDICES)} reader appendices"
        )

    expected_titles = REQUIRED_READER_SECTIONS + REQUIRED_READER_APPENDICES
    entries: list[_PlanEntry] = []
    seen_ids: set[str] = set()
    seen_semantic_ids: set[str] = set()
    for expected_ordinal, (raw, expected_title) in enumerate(
        zip(tuple(sections) + tuple(appendices), expected_titles, strict=True), 1
    ):
        entry = _require_mapping(raw, f"output plan entry {expected_ordinal}")
        section_id = _require_identifier(
            entry.get("section_id"), f"output plan entry {expected_ordinal} section_id"
        )
        if section_id in seen_ids:
            raise ArticleContractError(
                f"duplicate output plan section_id: {section_id}"
            )
        seen_ids.add(section_id)
        title = entry.get("title")
        if title != expected_title:
            raise ArticleContractError(
                f"output plan section title at ordinal {expected_ordinal} must be {expected_title!r}"
            )
        ordinal = _require_ordinal(
            entry.get("ordinal"), f"output plan section {section_id} ordinal"
        )
        if ordinal != expected_ordinal:
            raise ArticleContractError(
                f"output plan section {section_id} has out-of-order ordinal {ordinal}"
            )
        if require_packet_fields:
            semantic_unit_ids = _require_string_tuple(
                entry.get("semantic_unit_ids"),
                f"output plan section {section_id} semantic_unit_ids",
                allow_empty=False,
                identifiers=True,
            )
            duplicate_semantic_ids = seen_semantic_ids.intersection(semantic_unit_ids)
            if duplicate_semantic_ids:
                raise ArticleContractError(
                    "semantic units cannot occur in multiple output-plan sections: "
                    f"{sorted(duplicate_semantic_ids)}"
                )
            seen_semantic_ids.update(semantic_unit_ids)
            dependency_hashes = _require_string_tuple(
                entry.get("dependency_hashes"),
                f"output plan section {section_id} dependency_hashes",
                allow_empty=False,
                hashes=True,
            )
        else:
            semantic_unit_ids = ()
            dependency_hashes = ()
        entries.append(
            _PlanEntry(
                section_id=section_id,
                title=expected_title,
                ordinal=ordinal,
                semantic_unit_ids=semantic_unit_ids,
                dependency_hashes=dependency_hashes,
            )
        )
    return tuple(entries)


def _validate_output_plan(output_plan: Mapping[str, object]) -> tuple[_PlanEntry, ...]:
    plan = _require_mapping(output_plan, "output plan")
    if plan.get("phase_id") != "U10":
        raise ArticleContractError("article output plan must be frozen at phase U10")
    if plan.get("official_filename_allowed") is not False:
        raise ArticleContractError(
            "official article filename is not allowed in the U10 output plan"
        )
    if plan.get("coverage_required") is not True:
        raise ArticleContractError(
            "semantic coverage must remain required in the frozen output plan"
        )
    required_artifacts = _require_artifact_tuple(
        plan.get("required_artifacts"),
        "output plan required_artifacts",
    )
    article_path = plan.get("article_path")
    if not isinstance(article_path, str) or not article_path.strip():
        raise ArticleContractError(
            "output plan article_path must name a partial article"
        )
    article_basename = re.split(r"[/\\]", article_path)[-1]
    canonical_basename = article_basename.rstrip(" .").casefold()
    if canonical_basename == OFFICIAL_ARTICLE_FILENAME.casefold():
        raise ArticleContractError(
            "output plan cannot name the official article before U12"
        )
    if not canonical_basename.endswith(".partial.md"):
        raise ArticleContractError(
            "output plan article_path must use an explicit partial filename"
        )
    entries = _reader_plan_entries(plan, require_packet_fields=True)
    required_hashes = {item["sha256"] for item in required_artifacts}
    for entry in entries:
        unknown_hashes = set(entry.dependency_hashes) - required_hashes
        if unknown_hashes:
            raise ArticleContractError(
                f"output plan section {entry.section_id} depends on unknown artifacts: "
                f"{sorted(unknown_hashes)}"
            )
    return entries


def _validate_output_plan_relations(
    plan: Mapping[str, object], entries: Sequence[_PlanEntry]
) -> None:
    required_artifacts = _require_artifact_tuple(
        plan.get("required_artifacts"), "output plan required_artifacts"
    )
    required_hashes = {item["sha256"] for item in required_artifacts}
    raw_universe = _require_sequence(
        plan.get("semantic_universe"), "output plan semantic_universe"
    )
    if not raw_universe:
        raise ArticleContractError("output plan semantic_universe must not be empty")
    universe_by_id: dict[str, Mapping[str, object]] = {}
    observed_kinds: set[str] = set()
    for index, raw in enumerate(raw_universe):
        unit = _require_mapping(raw, f"semantic_universe[{index}]")
        unit_id = _require_identifier(
            unit.get("unit_id"), f"semantic_universe[{index}] unit_id"
        )
        if unit_id in universe_by_id:
            raise ArticleContractError(f"duplicate semantic unit_id: {unit_id}")
        unit_kind = unit.get("unit_kind")
        if unit_kind not in SEMANTIC_UNIT_KINDS:
            raise ArticleContractError(
                f"semantic unit {unit_id} has an unknown unit_kind"
            )
        observed_kinds.add(str(unit_kind))
        authority_hash = unit.get("authority_artifact_sha256")
        if (
            not isinstance(authority_hash, str)
            or _SHA256_RE.fullmatch(authority_hash) is None
        ):
            raise ArticleContractError(
                f"semantic unit {unit_id} authority_artifact_sha256 is invalid"
            )
        if authority_hash not in required_hashes:
            raise ArticleContractError(
                f"semantic unit {unit_id} authority artifact is not required upstream authority"
            )
        universe_by_id[unit_id] = unit
    missing_kinds = set(SEMANTIC_UNIT_KINDS) - observed_kinds
    if missing_kinds:
        raise ArticleContractError(
            f"semantic universe is missing frozen unit kinds: {sorted(missing_kinds)}"
        )

    planned_unit_ids = {
        unit_id for entry in entries for unit_id in entry.semantic_unit_ids
    }
    universe_unit_ids = set(universe_by_id)
    if planned_unit_ids != universe_unit_ids:
        raise ArticleContractError(
            "section semantic_unit_ids must materialize the complete semantic universe"
        )
    expected_universe_hash = sha256_bytes(canonical_json_bytes(list(raw_universe)))
    if plan.get("semantic_universe_sha256") != expected_universe_hash:
        raise ArticleContractError(
            "output plan semantic_universe_sha256 does not match the frozen universe"
        )

    entry_by_id = {entry.section_id: entry for entry in entries}
    expectations = _require_sequence(
        plan.get("blind_recovery_expectations"),
        "output plan blind_recovery_expectations",
    )
    if len(expectations) != len(BLIND_RECOVERY_FIELD_IDS):
        raise ArticleContractError(
            "output plan must contain the frozen fifteen blind recovery fields"
        )
    for index, (raw, expected_field_id) in enumerate(
        zip(expectations, BLIND_RECOVERY_FIELD_IDS, strict=True)
    ):
        expectation = _require_mapping(
            raw, f"blind_recovery_expectations[{index}]"
        )
        if expectation.get("field_id") != expected_field_id:
            raise ArticleContractError(
                "blind recovery field order differs from the frozen fifteen-field contract"
            )
        section_id = _require_identifier(
            expectation.get("section_id"),
            f"blind recovery field {expected_field_id} section_id",
        )
        entry = entry_by_id.get(section_id)
        if entry is None:
            raise ArticleContractError(
                f"blind recovery field {expected_field_id} names an unknown section"
            )
        semantic_ids = _require_string_tuple(
            expectation.get("semantic_unit_ids"),
            f"blind recovery field {expected_field_id} semantic_unit_ids",
            allow_empty=False,
            identifiers=True,
        )
        if not set(semantic_ids).issubset(entry.semantic_unit_ids):
            raise ArticleContractError(
                f"blind recovery field {expected_field_id} is not bound to its section units"
            )
        normalized_hash = expectation.get("normalized_value_sha256")
        if (
            not isinstance(normalized_hash, str)
            or _SHA256_RE.fullmatch(normalized_hash) is None
        ):
            raise ArticleContractError(
                f"blind recovery field {expected_field_id} normalized value hash is invalid"
            )


def validate_output_plan_artifact(
    artifact: Mapping[str, Any],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, Any],
    expected_u9_parent_event_sha256: str,
    expected_required_artifacts: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    prevalidated_entries = _validate_output_plan(artifact)
    try:
        snapshot = validate_phase_artifact(
            "ultra-output-plan.schema.json",
            artifact,
            expected_schema_id="crossframe.ultra.v82.output-plan",
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_phase_id="U10",
        )
    except (UltraRuntimeError, ValidationError, TypeError, ValueError) as error:
        raise ArticleContractError(f"invalid U10 output plan artifact: {error}") from error
    if snapshot.get("u9_parent_event_sha256") != expected_u9_parent_event_sha256:
        raise ArticleContractError(
            "U10 parent authority does not match the frozen U9 event"
        )
    actual_required = [
        dict(item)
        for item in _require_artifact_tuple(
            snapshot.get("required_artifacts"), "output plan required_artifacts"
        )
    ]
    expected_required = [
        dict(item)
        for item in _require_artifact_tuple(
            expected_required_artifacts, "expected required artifacts"
        )
    ]
    if actual_required != expected_required:
        raise ArticleContractError(
            "U10 required artifact authority does not match frozen upstream authority"
        )
    _validate_output_plan_relations(snapshot, prevalidated_entries)
    return snapshot


def build_output_plan_artifact(
    *,
    run_id: str,
    version_binding: Mapping[str, Any],
    generated_at: str,
    u9_parent_event_sha256: str,
    article_path: str,
    sections: Sequence[Mapping[str, object]],
    appendices: Sequence[Mapping[str, object]],
    required_artifacts: Sequence[Mapping[str, object]],
    semantic_universe: Sequence[Mapping[str, object]],
    blind_recovery_expectations: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    frozen_required = [
        dict(item)
        for item in _require_artifact_tuple(
            required_artifacts, "output plan required_artifacts"
        )
    ]
    frozen_universe = copy.deepcopy(list(semantic_universe))
    artifact: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.output-plan",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": copy.deepcopy(dict(version_binding)),
        "generated_at": generated_at,
        "phase_id": "U10",
        "u9_parent_event_sha256": u9_parent_event_sha256,
        "article_path": article_path,
        "sections": copy.deepcopy(list(sections)),
        "appendices": copy.deepcopy(list(appendices)),
        "required_artifacts": frozen_required,
        "semantic_universe": frozen_universe,
        "semantic_universe_sha256": sha256_bytes(
            canonical_json_bytes(frozen_universe)
        ),
        "blind_recovery_expectations": copy.deepcopy(
            list(blind_recovery_expectations)
        ),
        "coverage_required": True,
        "official_filename_allowed": False,
    }
    artifact["content_sha256"] = compute_artifact_content_sha256(artifact)
    return validate_output_plan_artifact(
        artifact,
        expected_run_id=run_id,
        expected_version_binding=version_binding,
        expected_u9_parent_event_sha256=u9_parent_event_sha256,
        expected_required_artifacts=required_artifacts,
    )


def _validated_packet_copy(
    raw: Mapping[str, object], expected: _PlanEntry
) -> Mapping[str, object]:
    packet = _require_mapping(raw, f"packet for section {expected.section_id}")
    keys = frozenset(packet.keys())
    if keys != _PACKET_FIELDS:
        missing = sorted(_PACKET_FIELDS - keys)
        extra = sorted(keys - _PACKET_FIELDS)
        raise ArticleContractError(
            f"packet field set is not frozen; missing={missing}, extra={extra}"
        )
    packet_id = _require_identifier(packet.get("packet_id"), "packet_id")
    section_id = _require_identifier(packet.get("section_id"), "packet section_id")
    if section_id != expected.section_id:
        raise ArticleContractError(
            f"packet section {section_id!r} does not match frozen section {expected.section_id!r}"
        )
    ordinal = _require_ordinal(packet.get("ordinal"), f"packet {packet_id} ordinal")
    if ordinal != expected.ordinal:
        raise ArticleContractError(
            f"packet {packet_id} ordinal does not match the output plan order"
        )
    dependency_hashes = _require_string_tuple(
        packet.get("dependency_hashes"),
        f"packet {packet_id} dependency_hashes",
        allow_empty=True,
        hashes=True,
    )
    if dependency_hashes != expected.dependency_hashes:
        raise ArticleContractError(f"packet {packet_id} has stale dependency hashes")
    semantic_unit_ids = _require_string_tuple(
        packet.get("semantic_unit_ids"),
        f"packet {packet_id} semantic_unit_ids",
        allow_empty=False,
        identifiers=True,
    )
    if semantic_unit_ids != expected.semantic_unit_ids:
        raise ArticleContractError(
            f"packet {packet_id} semantic unit IDs do not match the frozen output plan"
        )
    source_refs = _require_string_tuple(
        packet.get("source_refs"),
        f"packet {packet_id} source_refs",
        allow_empty=True,
        identifiers=True,
    )
    prose = packet.get("prose")
    if not isinstance(prose, str) or not prose.strip():
        raise ArticleContractError(f"packet {packet_id} prose must be non-empty text")
    if "\r" in prose or "\x00" in prose or prose.lstrip().startswith("\ufeff"):
        raise ArticleContractError(
            f"packet {packet_id} prose is not canonical UTF-8 text"
        )
    try:
        prose_bytes = prose.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ArticleContractError(
            f"packet {packet_id} prose is not valid UTF-8: {error}"
        ) from error
    prose_sha256 = packet.get("prose_sha256")
    if not isinstance(prose_sha256, str) or _SHA256_RE.fullmatch(prose_sha256) is None:
        raise ArticleContractError(f"packet {packet_id} prose_sha256 is invalid")
    actual_hash = hashlib.sha256(prose_bytes).hexdigest()
    if prose_sha256 != actual_hash:
        raise ArticleContractError(f"packet {packet_id} prose SHA-256 hash is stale")
    return MappingProxyType(
        {
            "packet_id": packet_id,
            "section_id": section_id,
            "ordinal": ordinal,
            "dependency_hashes": dependency_hashes,
            "semantic_unit_ids": semantic_unit_ids,
            "source_refs": source_refs,
            "prose": prose,
            "prose_sha256": prose_sha256,
        }
    )


def order_and_validate_packets(
    output_plan: Mapping[str, object],
    packets: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    entries = _validate_output_plan(output_plan)
    packet_items = _bounded_packet_items(packets, expected_count=len(entries))
    by_section: dict[str, Mapping[str, object]] = {}
    raw_packet_ids: set[str] = set()
    expected_by_section = {entry.section_id: entry for entry in entries}
    for index, raw in enumerate(packet_items):
        packet = _require_mapping(raw, f"article packet {index}")
        packet_id = _require_identifier(
            packet.get("packet_id"), f"packet {index} packet_id"
        )
        if packet_id in raw_packet_ids:
            raise ArticleContractError(f"duplicate packet_id: {packet_id}")
        raw_packet_ids.add(packet_id)
        section_id = _require_identifier(
            packet.get("section_id"), f"packet {packet_id} section_id"
        )
        if section_id in by_section:
            raise ArticleContractError(f"duplicate packet section: {section_id}")
        expected = expected_by_section.get(section_id)
        if expected is None:
            raise ArticleContractError(f"unexpected packet section: {section_id}")
        by_section[section_id] = _validated_packet_copy(packet, expected)

    missing = [
        entry.section_id for entry in entries if entry.section_id not in by_section
    ]
    if missing:
        raise ArticleContractError(f"missing article packets for sections: {missing}")
    return tuple(by_section[entry.section_id] for entry in entries)


def _body_paragraphs(body: str) -> tuple[str, ...]:
    return tuple(
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n[ \t]*\n", body)
        if paragraph.strip()
    )


def contains_machine_dump(article_text: str) -> bool:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    decoder = json.JSONDecoder()
    for match in re.finditer(
        r"(?<![A-Za-z0-9_\u3400-\u9fff])(?P<json>[\[{])", article_text
    ):
        candidate = article_text[match.start("json") :]
        try:
            value, end = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)) and "\n" in candidate[:end]:
            return True
    return bool(
        re.search(r"```\s*(?:json|jsonc|schema)\b", article_text, re.IGNORECASE)
        or _RAW_JSON_RE.search(article_text)
        or _MULTILINE_JSON_OBJECT_RE.search(article_text)
        or _MULTILINE_JSON_ARRAY_RE.search(article_text)
        or _contains_machine_key_value_record(article_text)
    )


def _contains_machine_key_value_record(article_text: str) -> bool:
    """Reject dense multi-line data structures without treating prose as YAML."""
    assignments: list[re.Match[str]] = []
    mapping_indents: list[int] = []
    section_headers = 0
    list_items = 0
    bare_list_items = 0
    for line in article_text.splitlines():
        if _MACHINE_SECTION_RE.fullmatch(line):
            section_headers += 1
            continue
        if _MACHINE_MAPPING_START_RE.fullmatch(line):
            mapping_indents.append(len(line) - len(line.lstrip(" \t")))
            continue
        if _MACHINE_BARE_LIST_ITEM_RE.fullmatch(line):
            bare_list_items += 1
            continue
        match = _MACHINE_ASSIGNMENT_LINE_RE.fullmatch(line)
        if match is not None and _MACHINE_SCALAR_RE.fullmatch(match.group("value")):
            assignments.append(match)
            if line.lstrip().startswith("-"):
                list_items += 1
            continue
        if _is_machine_structure(
            assignments,
            mapping_indents,
            section_headers,
            list_items,
            bare_list_items,
        ):
            return True
        assignments.clear()
        mapping_indents.clear()
        section_headers = 0
        list_items = 0
        bare_list_items = 0
    return _is_machine_structure(
        assignments,
        mapping_indents,
        section_headers,
        list_items,
        bare_list_items,
    )


def _is_machine_structure(
    assignments: Sequence[re.Match[str]],
    mapping_indents: Sequence[int],
    section_headers: int,
    list_items: int,
    bare_list_items: int,
) -> bool:
    if (
        len(assignments) >= 1
        and bare_list_items >= 2
        and len(mapping_indents) >= 2
        and len(set(mapping_indents)) >= 2
    ):
        return True
    if len(assignments) < 3:
        return False
    keys = tuple(match.group("key").casefold() for match in assignments)
    separators = {match.group("separator") for match in assignments}
    metadata_count = sum(
        key in _MACHINE_METADATA_KEYS or key.rsplit("_", 1)[-1] in _MACHINE_METADATA_KEYS
        for key in keys
    )
    structured_keys = sum(
        "_" in key or "-" in key or "." in key or key.isascii() for key in keys
    )
    dense_chinese_record = (
        len(assignments) >= 4
        and all(match.group("separator") in {":", "："} for match in assignments)
        and all(not match.group("key").isascii() for match in assignments)
    )
    return bool(
        section_headers
        or mapping_indents
        or "=" in separators
        or structured_keys >= 2
        or metadata_count >= 2
        or dense_chinese_record
    )


def _validate_reader_prose(article_text: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(article_text, str) or not article_text:
        raise ArticleContractError("reader article must be non-empty text")
    if _TRUNCATION_RE.search(article_text):
        raise ArticleContractError(
            "complete reader article contains a truncation or continuation promise"
        )
    if contains_machine_dump(article_text):
        raise ArticleContractError(
            "JSON, YAML, or key-value machine records are forbidden in reader prose"
        )
    if _INTERNAL_FIELD_RE.search(article_text):
        raise ArticleContractError("internal field names are forbidden in reader prose")

    headings = list(_HEADING_RE.finditer(article_text))
    expected_titles = REQUIRED_READER_SECTIONS + REQUIRED_READER_APPENDICES
    actual_titles = tuple(match.group(1).strip() for match in headings)
    if actual_titles != expected_titles:
        raise ArticleContractError(
            "reader article headings must contain the ten sections followed by all five appendices"
        )
    bodies: list[tuple[str, str]] = []
    normalized_bodies: set[str] = set()
    seen_paragraphs: set[str] = set()
    for index, match in enumerate(headings):
        body_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(article_text)
        )
        body = article_text[match.end() : body_end].strip()
        title = expected_titles[index]
        if not body:
            raise ArticleContractError(f"reader section body is empty: {title}")
        normalized_body = re.sub(r"\s+", " ", body).strip()
        if normalized_body in normalized_bodies:
            raise ArticleContractError(
                f"reader article contains a repeated boilerplate body: {title}"
            )
        normalized_bodies.add(normalized_body)
        for paragraph in _body_paragraphs(body):
            if len(paragraph) < 12:
                continue
            if paragraph in seen_paragraphs:
                raise ArticleContractError(
                    "reader article contains a repeated boilerplate paragraph"
                )
            seen_paragraphs.add(paragraph)
        concept_tokens = _CONCEPT_TOKEN_RE.findall(body)
        concept_names = _CONCEPT_NAME_RE.findall(body)
        if (
            len(concept_tokens) >= 5 or len(set(concept_names)) >= 5
        ) and _CONCRETE_ROLE_RE.search(body) is None:
            raise ArticleContractError(
                f"concept-name stuffing lacks a concrete role in reader section {title}"
            )
        bodies.append((title, body))
    return tuple(bodies)


def extract_reader_sections(
    article_text: str, output_plan: Mapping[str, object]
) -> tuple[ReaderSection, ...]:
    entries = _reader_plan_entries(output_plan, require_packet_fields=False)
    bodies = _validate_reader_prose(article_text)
    return tuple(
        ReaderSection(
            section_id=entry.section_id,
            title=entry.title,
            ordinal=entry.ordinal,
            body=body,
        )
        for entry, (_, body) in zip(entries, bodies, strict=True)
    )


def validate_reader_article(article_text: str) -> None:
    _validate_reader_prose(article_text)


def _quality_spans(article_text: str) -> tuple[str, ...]:
    return tuple(
        " ".join(raw.split())
        for raw in re.split(
            r"\n[ \t]*\n|^#{1,6}[^\n]*$",
            article_text,
            flags=re.MULTILINE,
        )
        if " ".join(raw.split())
    )


def _quality_content_characters(value: str) -> int:
    return sum(character.isalnum() for character in value)


def evaluate_answer_quality(
    article_text: str,
    contract: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(article_text, str):
        raise TypeError("article_text must be text")
    if not isinstance(contract, Mapping):
        raise TypeError("answer quality contract must be a mapping")
    raw_dimensions = contract.get("dimensions")
    if not isinstance(raw_dimensions, Sequence) or isinstance(
        raw_dimensions, (str, bytes, bytearray)
    ):
        raise ArticleContractError("answer quality dimensions must be a sequence")
    dimensions = tuple(raw_dimensions)
    dimension_ids = tuple(
        item.get("dimension_id") if isinstance(item, Mapping) else None
        for item in dimensions
    )
    if dimension_ids != QUALITY_DIMENSIONS:
        raise ArticleContractError(
            "answer quality contract must contain the frozen dimension order"
        )

    spans = _quality_spans(article_text)
    used_spans: set[int] = set()
    statuses: dict[str, str] = {}
    for raw in dimensions:
        if not isinstance(raw, Mapping):
            raise ArticleContractError("answer quality dimension must be a mapping")
        dimension_id = str(raw["dimension_id"])
        minimum = raw.get("minimum_span_characters")
        if type(minimum) is not int or minimum < 1:
            raise ArticleContractError(
                f"answer quality dimension {dimension_id} needs a positive span minimum"
            )
        raw_groups = raw.get("required_anchor_groups")
        if not isinstance(raw_groups, Sequence) or isinstance(
            raw_groups, (str, bytes, bytearray)
        ) or not raw_groups:
            raise ArticleContractError(
                f"answer quality dimension {dimension_id} needs anchor groups"
            )
        matched: list[int] = []
        for raw_group in raw_groups:
            if not isinstance(raw_group, Sequence) or isinstance(
                raw_group, (str, bytes, bytearray)
            ) or not raw_group:
                raise ArticleContractError(
                    f"answer quality dimension {dimension_id} has an invalid anchor group"
                )
            anchors = tuple(raw_group)
            if any(type(anchor) is not str or not anchor for anchor in anchors):
                raise ArticleContractError(
                    f"answer quality dimension {dimension_id} has an invalid anchor"
                )
            candidate = next(
                (
                    index
                    for index, span in enumerate(spans)
                    if index not in used_spans
                    and _quality_content_characters(span) >= minimum
                    and all(anchor in span for anchor in anchors)
                ),
                None,
            )
            if candidate is None:
                matched = []
                break
            matched.append(candidate)
        if matched:
            used_spans.update(matched)
            statuses[dimension_id] = "pass"
        else:
            statuses[dimension_id] = "fail"

    simulated_values = contract.get("simulated_values", [])
    qualifiers = contract.get("simulation_qualifiers", [])
    if not isinstance(simulated_values, Sequence) or isinstance(
        simulated_values, (str, bytes, bytearray)
    ) or not isinstance(qualifiers, Sequence) or isinstance(
        qualifiers, (str, bytes, bytearray)
    ):
        raise ArticleContractError("simulation quality boundaries must be sequences")
    if any(type(value) is not str or not value for value in simulated_values) or any(
        type(value) is not str or not value for value in qualifiers
    ):
        raise ArticleContractError("simulation quality boundaries must contain text")
    simulated_as_fact = "pass"
    for value in simulated_values:
        containing = [span for span in spans if value in span]
        if containing and any(
            not any(qualifier in span for qualifier in qualifiers)
            for span in containing
        ):
            simulated_as_fact = "fail"
            break
    overall = (
        "pass"
        if set(statuses.values()) == {"pass"} and simulated_as_fact == "pass"
        else "fail"
    )
    return {
        "schema_id": "crossframe.ultra.v82.answer-quality",
        "dimensions": statuses,
        "simulated_as_fact": simulated_as_fact,
        "overall_status": overall,
    }


def assemble_article(
    output_plan: Mapping[str, object],
    packets: Iterable[Mapping[str, object]],
    partial_path: Path,
) -> AssembledArticle:
    if not isinstance(partial_path, Path):
        raise TypeError("partial_path must be a pathlib.Path")
    windows_name = partial_path.name.rstrip(" .").casefold()
    official_name = OFFICIAL_ARTICLE_FILENAME.casefold()
    if windows_name == official_name or windows_name.startswith(official_name + ":"):
        raise ArticleContractError(
            "the official article filename cannot be written by the pre-U12 assembler"
        )
    ordered = order_and_validate_packets(output_plan, packets)
    text = (
        "\n\n".join(str(packet["prose"]).strip() for packet in ordered).rstrip() + "\n"
    )
    _validate_reader_prose(text)
    encoded = text.encode("utf-8")
    atomic_write_bytes(partial_path, encoded)
    return AssembledArticle(
        article_text=text,
        article_sha256=hashlib.sha256(encoded).hexdigest(),
        packet_ids=tuple(str(packet["packet_id"]) for packet in ordered),
        semantic_unit_ids=tuple(
            unit_id for packet in ordered for unit_id in packet["semantic_unit_ids"]
        ),
    )


__all__ = (
    "ARTICLE_PACKET_DIRECTORY",
    "ArticleContractError",
    "AssembledArticle",
    "BLIND_RECOVERY_FIELD_IDS",
    "SEMANTIC_UNIT_KINDS",
    "U10_OUTPUT_PLAN_PATH",
    "build_output_plan_artifact",
    "contains_machine_dump",
    "evaluate_answer_quality",
    "OFFICIAL_ARTICLE_FILENAME",
    "QUALITY_DIMENSIONS",
    "REQUIRED_READER_APPENDICES",
    "REQUIRED_READER_SECTIONS",
    "ReaderSection",
    "assemble_article",
    "extract_reader_sections",
    "order_and_validate_packets",
    "validate_output_plan_artifact",
    "validate_reader_article",
)
