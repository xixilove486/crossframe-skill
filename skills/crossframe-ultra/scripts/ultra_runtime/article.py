from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType

from .errors import UltraRuntimeError
from .jsonio import atomic_write_bytes


REQUIRED_READER_SECTIONS = (
    "主判断、范围与置信度",
    "用户观点的最强重建",
    "事实、证据与未知",
    "立体多圈层状态",
    "机制、通道与级联",
    "竞争解释与排序",
    "一阶、二阶与三阶推演",
    "逐阶基线、增量与停止",
    "事实、预测、价值、责任与授权",
    "行动、不行动、切换与反转",
)
REQUIRED_READER_APPENDICES = (
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差与停止",
    "预测、时间窗、指标与解析",
    "概念、证据与来源",
    "未知项与框架缺口候选",
)
OFFICIAL_ARTICLE_FILENAME = "CrossFrame-Ultra-完整文章.md"

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
                allow_empty=True,
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
    _require_string_tuple(
        plan.get("required_artifacts"),
        "output plan required_artifacts",
        allow_empty=False,
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
    return _reader_plan_entries(plan, require_packet_fields=True)


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
    "ArticleContractError",
    "AssembledArticle",
    "contains_machine_dump",
    "OFFICIAL_ARTICLE_FILENAME",
    "REQUIRED_READER_APPENDICES",
    "REQUIRED_READER_SECTIONS",
    "ReaderSection",
    "assemble_article",
    "extract_reader_sections",
    "order_and_validate_packets",
    "validate_reader_article",
)
