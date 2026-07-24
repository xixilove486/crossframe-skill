from __future__ import annotations

import copy
import hashlib
import re
from typing import Mapping, Sequence

from .jsonio import sha256_json
from .paths import validate_relative_artifact_path
from .position import (
    validate_position_lock,
    validate_recommendation_semantics,
)
from .validation import validate_bound_document


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_HEADER_RE = re.compile(
    r"^##\s+(?P<example_id>\S+)\s+\|\s*"
    r"mechanism=(?P<mechanism_id>[A-Za-z0-9._-]+)\s+\|\s*"
    r"relation=(?P<relation>similar|failure)\s+\|\s*"
    r"type=(?P<example_type>[A-Za-z_]+)\s*$",
    re.MULTILINE,
)
_ALLOWED_EXAMPLE_TYPES = frozenset(
    {"real_case", "user_material", "conditional_scenario", "structural_analogy"}
)
_SIMILARITY_CUES = ("相似", "类比", "条件", "因为", "similar", "analogy", "when")
_FAILURE_CUES = ("失效", "反例", "不成立", "停止", "退出", "failure", "counterexample")
_HIDDEN_REASONING_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "chain of thought",
    "hidden-reasoning",
    "hidden_reasoning",
    "hidden reasoning",
    "internal-monologue",
    "internal_monologue",
    "internal monologue",
    "scratchpad",
)
_ACTION_GRANT_MARKERS = (
    "已授权",
    "授权立即",
    "立即采取现实行动",
    "authorized to",
    "permission granted",
    "must act now",
)
_SEMANTIC_RELATION_CUES = (
    "因为",
    "由于",
    "因此",
    "所以",
    "从而",
    "导致",
    "使得",
    "意味着",
    "决定",
    "共同",
    "关联",
    "但",
    "然而",
    "而非",
    "相比",
    "尽管",
    "虽然",
    "尚未",
    "不能",
    "若",
    "如果",
    "当",
    "何时",
    "除非",
    "否则",
    "条件",
    "撤回",
    "切换",
    "不行动",
    "because",
    "due to",
    "therefore",
    "so that",
    "leads to",
    "means that",
    "determines",
    "together",
    "but",
    "however",
    "whereas",
    "rather than",
    "compared",
    "although",
    "only where",
    "cannot",
    "if",
    "when",
    "unless",
    "otherwise",
    "condition",
    "withdraw",
    "switch",
    "inaction",
)
_MACHINE_LEDGER_LINE_RE = re.compile(
    r"^(?:[-*+]\s*)?[A-Za-z_][A-Za-z0-9_.-]*\s*[:：=|]\s*\S"
)
_IDENTIFIER_LEDGER_LINE_RE = re.compile(
    r"^(?:[-*+]\s*)?(?:V8-[A-Z0-9._-]+|CLAIM-[A-Z0-9._-]+|"
    r"MECH-[A-Z0-9._-]+|OPTION-[A-Z0-9._-]+|POSITION-LOCK|"
    r"RECOMMENDATION-LOCK)(?:\s*[:：=|—-]|\s+)"
)
_FINAL_CHAT_FIELDS = frozenset(
    {
        "run_status",
        "center_judgment_summary",
        "key_withdrawal_conditions",
        "artifact_links",
        "continuation_entry",
    }
)
_RUN_STATUSES = frozenset(
    {
        "promax-artifact-run",
        "promax-complete",
        "promax-design-review",
        "promax-blocked/progress",
    }
)
_ESSAY_ADVISORY_MIN_CHARS = 2_000


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="strict")).hexdigest()


def _text_items(value: object, *, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be non-empty text")
        result.append(item.strip())
    if not allow_empty and not result:
        raise ValueError(f"{field} must not be empty")
    return result


def _mapping_items(value: object, *, field: str, allow_empty: bool = False) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    result: list[Mapping[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field}[{index}] must be an object")
        result.append(item)
    if not allow_empty and not result:
        raise ValueError(f"{field} must not be empty")
    return result


def _contains_any(text: str, markers: Sequence[str]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


def _string_leaves(value: object) -> list[str]:
    if isinstance(value, Mapping):
        result: list[str] = []
        for child in value.values():
            result.extend(_string_leaves(child))
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = []
        for child in value:
            result.extend(_string_leaves(child))
        return result
    return [value] if isinstance(value, str) and value.strip() else []


def _contains_semantic_phrase(text: str, phrase: str) -> bool:
    normalized = phrase.strip().rstrip("。；;，,：:！？!?、")
    return bool(normalized) and normalized in text


def _contains_semantic_relation_cue(text: str) -> bool:
    folded = text.casefold()
    for cue in _SEMANTIC_RELATION_CUES:
        normalized = cue.casefold()
        if normalized.isascii() and " " not in normalized:
            if re.search(rf"\b{re.escape(normalized)}\b", folded) is not None:
                return True
        elif normalized in folded:
            return True
    return False


def _continuous_semantic_paragraphs(essay: str) -> list[str]:
    """Return prose paragraphs after removing headings and machine-ledger lines."""

    paragraphs: list[str] = []
    for block in re.split(r"\n\s*\n", essay):
        prose_lines: list[str] = []
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("|"):
                continue
            if _MACHINE_LEDGER_LINE_RE.match(line) is not None:
                continue
            if _IDENTIFIER_LEDGER_LINE_RE.match(line) is not None:
                continue
            prose_lines.append(line)
        if prose_lines:
            paragraphs.append(" ".join(prose_lines))
    return paragraphs


def _joint_semantic_paragraph_indices(
    paragraphs: Sequence[str],
    *,
    phrases: Sequence[str],
) -> set[int]:
    required = [phrase for phrase in phrases if phrase.strip()]
    return {
        index
        for index, paragraph in enumerate(paragraphs)
        if all(_contains_semantic_phrase(paragraph, phrase) for phrase in required)
        and _contains_semantic_relation_cue(paragraph)
    }


def _has_distinct_paragraph_assignment(groups: Sequence[set[int]]) -> bool:
    ordered = sorted(groups, key=len)

    def assign(index: int, used: set[int]) -> bool:
        if index == len(ordered):
            return True
        for paragraph_index in ordered[index] - used:
            if assign(index + 1, used | {paragraph_index}):
                return True
        return False

    return assign(0, set())


def _validate_continuous_essay_semantics(
    *,
    essay: str,
    position: Mapping[str, object],
    recommendation: Mapping[str, object],
    recommendation_required: bool,
    concept_registry: Mapping[str, object],
    dispositions: Sequence[Mapping[str, object]],
) -> None:
    paragraphs = _continuous_semantic_paragraphs(essay)
    if not paragraphs:
        raise ValueError("essay has no continuous semantic paragraph")

    judgment_phrases = [
        str(position["position"]),
        str(position["judgment_strength"]),
        *_text_items(position.get("primary_reasons"), field="position.primary_reasons"),
        str(position["runner_up_explanation"]),
    ]
    judgment_indices = _joint_semantic_paragraph_indices(
        paragraphs,
        phrases=judgment_phrases,
    )
    if not judgment_indices:
        raise ValueError(
            "judgment lock fields must share a continuous semantic paragraph with a relation cue"
        )

    registry = _registry_records(concept_registry)
    concept_indices: set[int] = set()
    for disposition in dispositions:
        if disposition.get("status") != "applied":
            continue
        concept_id = disposition.get("concept_id")
        record = registry.get(str(concept_id))
        if record is None:
            raise ValueError(f"applied concept is absent from the v8 registry: {concept_id}")
        concept_phrases = [
            str(record.get("authoritative_name_zh", "")),
            str(record.get("definition", "")),
            str(disposition.get("rationale", "")),
        ]
        matches = _joint_semantic_paragraph_indices(
            paragraphs,
            phrases=concept_phrases,
        )
        if not matches:
            raise ValueError(
                f"concept {concept_id} needs a continuous semantic paragraph joining its "
                "name, v8 definition, current role, and a relation cue"
            )
        concept_indices.update(matches)
    if not concept_indices:
        raise ValueError("essay has no applied-concept continuous semantic paragraph")

    counter_phrases = [
        *_text_items(
            position.get("strongest_counterevidence"),
            field="position.strongest_counterevidence",
        ),
        *_text_items(position.get("why_not_adopted"), field="position.why_not_adopted"),
        *_text_items(
            position.get("withdrawal_conditions"),
            field="position.withdrawal_conditions",
        ),
    ]
    counter_indices = _joint_semantic_paragraph_indices(
        paragraphs,
        phrases=counter_phrases,
    )
    if not counter_indices:
        raise ValueError(
            "countercase, rejection reason, and withdrawal lock must share a continuous "
            "semantic paragraph with a contrast or condition cue"
        )

    category_groups = [judgment_indices, concept_indices, counter_indices]
    if recommendation_required:
        preferred = str(recommendation.get("preferred_option_id", ""))
        second = str(recommendation.get("second_option_id", ""))
        recommendation_phrases = [
            preferred,
            second,
            *_text_items(
                recommendation.get("switch_conditions"),
                field="recommendation.switch_conditions",
            ),
            *_text_items(
                recommendation.get("inaction_consequences"),
                field="recommendation.inaction_consequences",
            ),
            str(recommendation.get("authorization_status", "")),
        ]
        recommendation_indices = _joint_semantic_paragraph_indices(
            paragraphs,
            phrases=recommendation_phrases,
        )
        if not recommendation_indices:
            raise ValueError(
                "recommendation ranking, switch, inaction, and authorization locks must share "
                "a continuous semantic paragraph with a relation or condition cue"
            )
        category_groups.append(recommendation_indices)

    if not _has_distinct_paragraph_assignment(category_groups):
        category_count = 4 if recommendation_required else 3
        raise ValueError(
            f"essay must distinguish {category_count} continuous semantic paragraph categories"
        )


def _reject_hidden_reasoning(value: object, *, pointer: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _contains_any(key_text, _HIDDEN_REASONING_MARKERS):
                raise ValueError(f"hidden reasoning field is forbidden at {pointer}/{key_text}")
            _reject_hidden_reasoning(child, pointer=f"{pointer}/{key_text}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _reject_hidden_reasoning(child, pointer=f"{pointer}/{index}")
        return
    if isinstance(value, str) and _contains_any(value, _HIDDEN_REASONING_MARKERS):
        raise ValueError(f"hidden reasoning content is forbidden at {pointer}")


def _assert_run_binding(
    document: Mapping[str, object],
    *,
    run_id: object,
    source_snapshot_sha256: object,
    artifact: str,
) -> None:
    if "run_id" in document and document.get("run_id") != run_id:
        raise ValueError(f"{artifact} is bound to a different run")
    if (
        "source_snapshot_sha256" in document
        and document.get("source_snapshot_sha256") != source_snapshot_sha256
    ):
        raise ValueError(f"{artifact} is bound to a different source snapshot")


def _manifest_records(
    manifest: Mapping[str, object],
    *,
    run_id: object | None = None,
    source_snapshot_sha256: object | None = None,
) -> dict[str, dict[str, object]]:
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a structured object")
    if run_id is not None and manifest.get("run_id") != run_id:
        raise ValueError("manifest is bound to a different run")
    if (
        source_snapshot_sha256 is not None
        and manifest.get("source_snapshot_sha256") != source_snapshot_sha256
    ):
        raise ValueError("manifest is bound to a different source snapshot")
    expected_hash = manifest.get("manifest_sha256")
    if not isinstance(expected_hash, str) or _SHA256_RE.fullmatch(expected_hash) is None:
        raise ValueError("manifest_sha256 must be a lowercase SHA-256")
    unsigned = copy.deepcopy(dict(manifest))
    unsigned.pop("manifest_sha256", None)
    if sha256_json(unsigned) != expected_hash:
        raise ValueError("manifest self hash is stale")

    records = _mapping_items(manifest.get("artifacts"), field="manifest.artifacts")
    current: dict[str, dict[str, object]] = {}
    seen_paths: set[str] = set()
    seen_folded: set[str] = set()
    for record in records:
        path = validate_relative_artifact_path(record.get("path"))
        folded = path.casefold()
        if path in seen_paths or folded in seen_folded:
            raise ValueError("manifest artifact paths must be unique under case folding")
        seen_paths.add(path)
        seen_folded.add(folded)
        digest = record.get("sha256")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ValueError(f"manifest has an invalid SHA-256 for {path}")
        if record.get("status") == "current":
            current[path] = copy.deepcopy(dict(record))
    if not current:
        raise ValueError("manifest must contain current artifacts")
    return current


def _validate_deliverable_bytes(
    deliverables: Mapping[str, str],
    *,
    current_records: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    if not isinstance(deliverables, Mapping):
        raise ValueError("deliverables must be a path-to-text mapping")
    normalized: dict[str, str] = {}
    folded_paths: set[str] = set()
    for raw_path, content in deliverables.items():
        path = validate_relative_artifact_path(raw_path)
        if path.casefold() in folded_paths:
            raise ValueError("deliverable paths must be unique under case folding")
        folded_paths.add(path.casefold())
        if not isinstance(content, str):
            raise ValueError(f"deliverable {path} must be strict UTF-8 text")
        try:
            content.encode("utf-8", errors="strict")
        except UnicodeError as error:
            raise ValueError(f"deliverable {path} is not strict UTF-8") from error
        record = current_records.get(path)
        if record is None:
            raise ValueError(f"deliverable {path} is absent from the current manifest")
        if record.get("sha256") != _text_sha256(content):
            raise ValueError(f"deliverable {path} does not match its current manifest hash")
        normalized[path] = content
    if not normalized:
        raise ValueError("deliverables must not be empty")
    return normalized


def _concept_section(atlas: str, *, concept_id: str, name: str) -> str:
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", atlas, flags=re.MULTILINE))
    for index, heading in enumerate(headings):
        title = heading.group(1)
        if concept_id not in title and name not in title:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(atlas)
        return atlas[heading.start():end]
    raise ValueError(f"concept atlas has no dedicated semantic section for {concept_id}")


def _registry_records(concept_registry: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    if not isinstance(concept_registry, Mapping):
        raise ValueError("concept registry must be a structured object")
    records = _mapping_items(concept_registry.get("concepts"), field="concept_registry.concepts")
    indexed: dict[str, Mapping[str, object]] = {}
    for record in records:
        concept_id = record.get("concept_id")
        if not isinstance(concept_id, str) or not concept_id:
            raise ValueError("concept registry record has no concept_id")
        if concept_id in indexed:
            raise ValueError(f"concept registry repeats {concept_id}")
        indexed[concept_id] = record
    return indexed


def _validate_concept_semantics(
    *,
    concept_registry: Mapping[str, object],
    dispositions: Sequence[Mapping[str, object]],
    plan_concept_ids: set[str],
    plan_sections_by_concept: Mapping[str, set[str]],
    atlas: str,
    essay: str,
) -> list[str]:
    registry = _registry_records(concept_registry)
    applied = [item for item in dispositions if item.get("status") == "applied"]
    applied_ids = {item.get("concept_id") for item in applied}
    if any(not isinstance(item, str) for item in applied_ids):
        raise ValueError("applied concept dispositions must have concept IDs")
    if applied_ids != plan_concept_ids:
        raise ValueError("output plan and applied concept dispositions are not bidirectionally closed")

    for disposition in applied:
        concept_id = str(disposition["concept_id"])
        record = registry.get(concept_id)
        if record is None:
            raise ValueError(f"applied concept is absent from the v8 registry: {concept_id}")
        name = record.get("authoritative_name_zh")
        definition = record.get("definition")
        if not isinstance(name, str) or not name.strip() or not isinstance(definition, str) or not definition.strip():
            raise ValueError(f"registry concept {concept_id} lacks an authoritative name or definition")
        section = _concept_section(atlas, concept_id=concept_id, name=name)
        rationale = disposition.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError(f"applied concept {concept_id} lacks a substantive role rationale")
        for required_text, role in (
            (name, "authoritative name"),
            (definition, "v8 definition"),
        ):
            if required_text not in section:
                raise ValueError(f"concept atlas omits {role} semantics for {concept_id}")
        if not _contains_semantic_phrase(section, rationale):
            raise ValueError(f"concept atlas omits current-object role semantics for {concept_id}")
        if name not in essay or definition not in essay:
            raise ValueError(f"essay does not explain the v8 definition of {concept_id}")

        misuses = _text_items(
            disposition.get("misuses_excluded"),
            field=f"concept disposition {concept_id}.misuses_excluded",
            allow_empty=True,
        )
        if not all(item in section for item in misuses):
            raise ValueError(f"concept atlas omits misuse boundaries for {concept_id}")

        neighbor_ids = _text_items(
            disposition.get("required_neighbor_ids"),
            field=f"concept disposition {concept_id}.required_neighbor_ids",
            allow_empty=True,
        )
        for neighbor_id in neighbor_ids:
            neighbor = registry.get(neighbor_id)
            if neighbor is None:
                raise ValueError(f"concept {concept_id} names an unknown neighbor {neighbor_id}")
            neighbor_name = neighbor.get("authoritative_name_zh")
            if not isinstance(neighbor_name, str):
                raise ValueError(f"neighbor {neighbor_id} has no authoritative name")
            if neighbor_id not in section and neighbor_name not in section:
                raise ValueError(f"concept atlas omits neighbor semantics for {concept_id}")

        expected_sections = plan_sections_by_concept.get(concept_id, set())
        output_sections = set(
            _text_items(
                disposition.get("output_section_ids"),
                field=f"concept disposition {concept_id}.output_section_ids",
            )
        )
        if output_sections != expected_sections:
            raise ValueError(f"concept {concept_id} output sections disagree with the locked plan")
    return sorted(str(item) for item in applied_ids)


def _parse_case_records(case_document: str) -> list[dict[str, str]]:
    matches = list(_CASE_HEADER_RE.finditer(case_document))
    if not matches:
        raise ValueError("case artifact contains no typed case records")
    stray_headers = [
        match.group(0)
        for match in re.finditer(r"^##\s+.+$", case_document, flags=re.MULTILINE)
        if _CASE_HEADER_RE.fullmatch(match.group(0)) is None
    ]
    if stray_headers:
        raise ValueError("every case heading must carry mechanism, relation, and allowed type")
    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(case_document)
        record = match.groupdict()
        record["body"] = case_document[match.end():end].strip()
        if record["example_id"] in seen_ids:
            raise ValueError(f"case artifact repeats {record['example_id']}")
        seen_ids.add(record["example_id"])
        if record["example_type"] not in _ALLOWED_EXAMPLE_TYPES:
            raise ValueError(f"case {record['example_id']} has an unsupported type")
        if not record["body"]:
            raise ValueError(f"case {record['example_id']} has an empty body")
        records.append(record)
    return records


def _validate_case_semantics(
    *,
    case_document: str,
    mechanisms: Sequence[Mapping[str, object]],
    planned_example_ids: set[str],
    planned_counterexample_ids: set[str],
) -> None:
    records = _parse_case_records(case_document)
    similar_ids = {item["example_id"] for item in records if item["relation"] == "similar"}
    failure_ids = {item["example_id"] for item in records if item["relation"] == "failure"}
    if similar_ids != planned_example_ids or failure_ids != planned_counterexample_ids:
        raise ValueError("case artifact IDs disagree with the locked output plan")

    mechanism_index: dict[str, Mapping[str, object]] = {}
    all_conditions: list[str] = []
    for mechanism in mechanisms:
        mechanism_id = mechanism.get("mechanism_id")
        label = mechanism.get("label")
        conditions = _text_items(
            mechanism.get("distinguishing_conditions"),
            field=f"mechanism {mechanism_id}.distinguishing_conditions",
        )
        if not isinstance(mechanism_id, str) or not isinstance(label, str) or not label.strip():
            raise ValueError("claim graph mechanism lacks an ID or label")
        if mechanism_id in mechanism_index:
            raise ValueError(f"claim graph repeats mechanism {mechanism_id}")
        mechanism_index[mechanism_id] = mechanism
        all_conditions.extend(conditions)

    unknown = {item["mechanism_id"] for item in records} - set(mechanism_index)
    if unknown:
        raise ValueError(f"case artifact names unknown mechanisms: {sorted(unknown)}")
    for mechanism_id, mechanism in mechanism_index.items():
        scoped = [item for item in records if item["mechanism_id"] == mechanism_id]
        similars = [item for item in scoped if item["relation"] == "similar"]
        failures = [item for item in scoped if item["relation"] == "failure"]
        if len(similars) < 2 or len(failures) < 1:
            raise ValueError(
                f"mechanism {mechanism_id} needs two typed similar cases and one typed failure"
            )
        label = str(mechanism["label"])
        own_conditions = _text_items(
            mechanism.get("distinguishing_conditions"),
            field=f"mechanism {mechanism_id}.distinguishing_conditions",
        )
        for record in similars:
            body = record["body"]
            if label not in body or not any(condition in body for condition in own_conditions):
                raise ValueError(f"similar case {record['example_id']} lacks mechanism semantics")
            if not _contains_any(body, _SIMILARITY_CUES):
                raise ValueError(f"similar case {record['example_id']} lacks an explicit relation cue")
        for record in failures:
            body = record["body"]
            if label not in body or not any(condition in body for condition in all_conditions):
                raise ValueError(f"failure case {record['example_id']} lacks distinguishing conditions")
            if not _contains_any(body, _FAILURE_CUES):
                raise ValueError(f"failure case {record['example_id']} lacks an explicit failure cue")


def _validate_position_output(position: Mapping[str, object], *, essay: str) -> None:
    scalar_fields = (
        "position",
        "runner_up_explanation",
        "action_ceiling",
    )
    list_fields = (
        "primary_reasons",
        "strongest_counterevidence",
        "why_not_adopted",
        "withdrawal_conditions",
    )
    for field in scalar_fields:
        value = position.get(field)
        if not isinstance(value, str) or value not in essay:
            raise ValueError(f"essay does not carry locked position field {field}")
    for field in list_fields:
        values = _text_items(position.get(field), field=f"position.{field}")
        if not all(value in essay for value in values):
            raise ValueError(f"essay does not carry every locked position item in {field}")
    judgment_strength = position.get("judgment_strength")
    if not isinstance(judgment_strength, str) or judgment_strength not in essay:
        raise ValueError("essay does not carry the locked judgment strength")


def _validate_recommendation_output(
    recommendation: Mapping[str, object],
    *,
    required: bool,
    essay: str,
    dossier: str,
) -> None:
    combined = f"{essay}\n{dossier}"
    if not required:
        if recommendation != {"status": "not_requested"}:
            raise ValueError("non-requested recommendation artifact is not exactly closed")
        if re.search(r"\bOPTION-[A-Za-z0-9._-]+\b", combined) or _contains_any(
            combined, ("我建议", "首选方案", "推荐方案", "优先选择")
        ):
            raise ValueError("output fabricates advice when recommendation was not requested")
        return

    options = _mapping_items(recommendation.get("options"), field="recommendation.options")
    option_ids: list[str] = []
    for option in options:
        option_id = option.get("option_id")
        option_kind = option.get("option_kind")
        description = option.get("description")
        if not all(
            isinstance(value, str) and value
            for value in (option_id, option_kind, description)
        ):
            raise ValueError("recommendation option lacks an ID, v8 kind, or description")
        if option_id not in essay or option_kind not in essay or description not in essay:
            raise ValueError(f"essay omits recommendation option {option_id}")
        for field in (
            "forecast_refs",
            "normative_premise_refs",
            "affected_position_refs",
            "rights_floor_refs",
            "expected_paths",
            "cross_circle_spillovers",
            "stop_conditions",
            "rollback_and_remedy",
        ):
            values = _text_items(
                option.get(field),
                field=f"recommendation option {option_id}.{field}",
            )
            if not all(value in essay for value in values):
                raise ValueError(f"essay omits {field} for recommendation option {option_id}")
        for field in (
            "worst_acceptable_outcome",
            "distribution_of_costs_and_benefits",
            "information_value",
            "lock_in_risk",
            "reversibility",
            "resource_cost",
            "authorized_actor_ref",
            "authorization_record_ref",
        ):
            value = option.get(field)
            if not isinstance(value, str) or value not in essay:
                raise ValueError(f"essay omits {field} for recommendation option {option_id}")
        option_ids.append(option_id)
    dimensions = _text_items(
        recommendation.get("evaluation_dimensions"),
        field="recommendation.evaluation_dimensions",
    )
    if not all(dimension in essay for dimension in dimensions):
        raise ValueError("essay omits one or more recommendation evaluation dimensions")
    ranking = _text_items(recommendation.get("ranking"), field="recommendation.ranking")
    first_positions = [essay.find(option_id) for option_id in ranking]
    if any(index < 0 for index in first_positions) or first_positions != sorted(first_positions):
        raise ValueError("essay does not express the locked recommendation ranking")
    preferred = str(recommendation.get("preferred_option_id"))
    second = str(recommendation.get("second_option_id"))
    if not _contains_any(essay, (f"首选 {preferred}", f"推荐 {preferred}", f"preferred {preferred}")):
        raise ValueError("essay does not directly state the preferred option")
    if not _contains_any(essay, (f"次选 {second}", f"第二选择 {second}", f"second {second}")):
        raise ValueError("essay does not directly state the second option")
    for field in ("switch_conditions", "inaction_consequences"):
        values = _text_items(recommendation.get(field), field=f"recommendation.{field}")
        if not all(value in essay for value in values):
            raise ValueError(f"essay omits locked recommendation field {field}")
    authorization = recommendation.get("authorization_status")
    if not isinstance(authorization, str) or authorization not in essay:
        raise ValueError("essay omits the recommendation authorization boundary")
    ranking_policy = recommendation.get("ranking_policy")
    if not isinstance(ranking_policy, str) or any(
        ranking_policy not in document for document in (essay, dossier)
    ):
        raise ValueError("essay and dossier must disclose the exact ranking_policy")
    evidence_refs = _text_items(
        recommendation.get("ranking_evidence_refs"),
        field="recommendation.ranking_evidence_refs",
        allow_empty=True,
    )
    wrapper = recommendation.get("selection_review_wrapper")
    if not isinstance(wrapper, Mapping):
        raise ValueError("recommendation output lacks the selection-review wrapper")
    for value in set(_string_leaves(wrapper)):
        if value not in essay:
            raise ValueError(
                f"essay omits selection-review wrapper semantics: {value}"
            )
    dossier_markers = [
        wrapper.get("wrapper_schema_id"),
        wrapper.get("wrapper_role"),
        wrapper.get("selection_type"),
        wrapper.get("selection_status"),
        *(
            wrapper.get("source_paragraph_refs")
            if isinstance(wrapper.get("source_paragraph_refs"), list)
            else []
        ),
    ]
    jurisdiction = wrapper.get("jurisdiction_review_boundary")
    if isinstance(jurisdiction, Mapping):
        dossier_markers.append(jurisdiction.get("boundary_role"))
    for review_name in ("least_harm", "proportionality"):
        review = wrapper.get(review_name)
        if isinstance(review, Mapping):
            dossier_markers.extend(
                [review.get("principle_id"), review.get("status")]
            )
    if any(
        not isinstance(marker, str) or marker not in dossier
        for marker in dossier_markers
    ):
        raise ValueError(
            "dossier omits the selection-review identity, v8 anchors, boundary, or principle status"
        )
    eligibility = wrapper.get(
        "declared_low_information_house_policy_eligibility"
    )
    if not isinstance(eligibility, Mapping):
        raise ValueError("recommendation output lacks declared house-policy eligibility")
    eligibility_line = (
        "declared_low_information_house_policy_eligibility: "
        f"case_specific_facts_present={str(eligibility.get('case_specific_facts_present')).lower()}; "
        "choice_changing_retrieval_evidence_present="
        f"{str(eligibility.get('choice_changing_retrieval_evidence_present')).lower()}"
    )
    if eligibility_line not in essay or eligibility_line not in dossier:
        raise ValueError(
            "essay and dossier must disclose the declared house-policy eligibility flags"
        )
    procedure_states = wrapper.get("procedure_states")
    if not isinstance(procedure_states, Mapping) or any(
        f"{procedure_id}={procedure_states.get(procedure_id)}" not in essay
        for procedure_id in ("O1", "O2", "O3", "O4")
    ):
        raise ValueError("essay omits the O1-O4 selection-review states")
    if ranking_policy == "promax_low_information_house_policy_not_v8":
        for document in (essay, dossier):
            if (
                "PROMAX-HOUSE-POLICY-NOT-V8" not in document
                or not _contains_any(document, ("不是 v8", "非 v8", "not v8"))
                or "ranking_evidence_refs=[]" not in document
            ):
                raise ValueError(
                    "house ranking must be disclosed in essay and dossier as ProMax policy, not v8"
                )
    elif not all(ref in essay and ref in dossier for ref in evidence_refs):
        raise ValueError(
            "evidence-bound ranking refs must be disclosed in essay and dossier"
        )


def _validate_continuation_structure(
    ledger: Mapping[str, object],
    *,
    manifest: Mapping[str, object],
    current_records: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if not isinstance(ledger, Mapping):
        raise ValueError("continuation ledger must be a structured object")
    normalized = copy.deepcopy(dict(ledger))
    validate_bound_document(
        "promax-continuation-ledger.schema.json",
        normalized,
        expected_run_id=str(manifest.get("run_id")),
        expected_source_snapshot_sha256=str(manifest.get("source_snapshot_sha256")),
    )
    if normalized.get("parent_manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("continuation ledger is attached to a stale parent manifest")
    records = _mapping_items(
        normalized.get("continuations"),
        field="continuation_ledger.continuations",
        allow_empty=True,
    )
    sequences = [record.get("sequence") for record in records]
    if sequences != list(range(1, len(records) + 1)):
        raise ValueError("continuation sequence must be contiguous and ordered from one")
    current_hashes = {str(record.get("sha256")) for record in current_records.values()}
    current_paths = set(current_records)
    pending_folded: set[str] = set()
    continuation_ids: set[str] = set()
    for record in records:
        continuation_id = record.get("continuation_id")
        if not isinstance(continuation_id, str) or continuation_id in continuation_ids:
            raise ValueError("continuation IDs must be unique")
        continuation_ids.add(continuation_id)
        if record.get("resume_from_phase") != "P10":
            raise ValueError("delivery continuation may resume only from P10")
        if record.get("parent_artifact_sha256") not in current_hashes:
            raise ValueError("continuation is attached to a stale parent artifact")
        parent_records = [
            artifact
            for artifact in current_records.values()
            if artifact.get("sha256") == record.get("parent_artifact_sha256")
        ]
        if not any(artifact.get("generating_phase") == "P10" for artifact in parent_records):
            raise ValueError("continuation parent artifact must have been generated in P10")
        pending = _text_items(
            record.get("pending_artifact_paths"),
            field=f"continuation {continuation_id}.pending_artifact_paths",
        )
        for raw_path in pending:
            path = validate_relative_artifact_path(raw_path)
            folded = path.casefold()
            if path in current_paths or folded in {item.casefold() for item in current_paths}:
                raise ValueError("continuation pending path already exists as a current artifact")
            if folded in pending_folded:
                raise ValueError("continuation pending paths must be globally unique")
            pending_folded.add(folded)
    return normalized


def validate_continuation_lineage(
    ledger: Mapping[str, object],
    *,
    manifest: Mapping[str, object],
    deliverables: Mapping[str, str],
) -> dict[str, object]:
    """Validate continuation attachment to current manifest and delivery bytes."""

    current = _manifest_records(manifest)
    _validate_deliverable_bytes(deliverables, current_records=current)
    return _validate_continuation_structure(
        ledger,
        manifest=manifest,
        current_records=current,
    )


def validate_output_bundle(
    *,
    run_contract: Mapping[str, object],
    position: Mapping[str, object],
    recommendation: Mapping[str, object],
    output_plan: Mapping[str, object],
    concept_disposition: Mapping[str, object],
    claim_path_graph: Mapping[str, object],
    concept_registry: Mapping[str, object],
    deliverables: Mapping[str, str],
    manifest: Mapping[str, object],
    continuation_ledger: Mapping[str, object],
) -> dict[str, object]:
    """Validate semantic output closure without using length as a pass gate."""

    if not isinstance(run_contract, Mapping):
        raise ValueError("run contract must be a structured object")
    run_id = run_contract.get("run_id")
    source_sha = run_contract.get("source_snapshot_sha256")
    if not isinstance(run_id, str) or not isinstance(source_sha, str):
        raise ValueError("run contract lacks output validation bindings")
    contract = validate_bound_document(
        "promax-run-contract.schema.json",
        run_contract,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    required = contract.get("recommendation_required")
    if type(required) is not bool:
        raise ValueError("run contract lacks a boolean recommendation intent")
    plan = validate_bound_document(
        "promax-output-plan.schema.json",
        output_plan,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    normalized_manifest = validate_bound_document(
        "promax-artifact-manifest.schema.json",
        manifest,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    if normalized_manifest.get("run_contract_sha256") != sha256_json(contract):
        raise ValueError("manifest is bound to a different run contract")
    for field in ("run_nonce", "request_sha256", "mode", "orchestration_mode"):
        if normalized_manifest.get(field) != contract.get(field):
            raise ValueError(f"manifest changes immutable run contract field {field}")
    if contract.get("mode") == "promax-complete":
        if plan.get("coverage_complete") is not True:
            raise ValueError("promax-complete requires coverage_complete=true")
        if plan.get("unexpanded_branch_ids") != []:
            raise ValueError("promax-complete forbids unexpanded output-plan branches")

    locked_position = validate_position_lock(
        position,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    locked_recommendation = validate_recommendation_semantics(
        contract,
        recommendation,
        position=locked_position,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    disposition = validate_bound_document(
        "promax-concept-disposition.schema.json",
        concept_disposition,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    _assert_run_binding(
        claim_path_graph,
        run_id=run_id,
        source_snapshot_sha256=source_sha,
        artifact="claim path graph",
    )

    current = _manifest_records(
        normalized_manifest,
        run_id=run_id,
        source_snapshot_sha256=source_sha,
    )
    content = _validate_deliverable_bytes(deliverables, current_records=current)
    _reject_hidden_reasoning(content)
    required_artifacts = set(
        _text_items(plan.get("required_artifacts"), field="output_plan.required_artifacts")
    )
    if not required_artifacts.issubset(content) or not required_artifacts.issubset(current):
        raise ValueError("locked output plan required artifacts are not all current and delivered")
    sections = _mapping_items(plan.get("sections"), field="output_plan.sections")
    section_ids: set[str] = set()
    plan_concept_ids: set[str] = set()
    plan_claim_ids: set[str] = set()
    planned_example_ids: set[str] = set()
    planned_counterexample_ids: set[str] = set()
    planned_judgment_ids: list[str] = []
    plan_sections_by_concept: dict[str, set[str]] = {}
    for section in sections:
        section_id = section.get("section_id")
        if not isinstance(section_id, str) or section_id in section_ids:
            raise ValueError("output plan section IDs must be unique")
        section_ids.add(section_id)
        concept_ids = set(
            _text_items(
                section.get("concept_ids"),
                field=f"output plan {section_id}.concept_ids",
                allow_empty=True,
            )
        )
        for concept_id in concept_ids:
            plan_sections_by_concept.setdefault(concept_id, set()).add(section_id)
        plan_concept_ids.update(concept_ids)
        plan_claim_ids.update(
            _text_items(
                section.get("claim_ids"),
                field=f"output plan {section_id}.claim_ids",
                allow_empty=True,
            )
        )
        planned_example_ids.update(
            _text_items(
                section.get("example_ids"),
                field=f"output plan {section_id}.example_ids",
                allow_empty=True,
            )
        )
        planned_counterexample_ids.update(
            _text_items(
                section.get("counterexample_ids"),
                field=f"output plan {section_id}.counterexample_ids",
                allow_empty=True,
            )
        )
        planned_judgment_ids.extend(
            _text_items(
                section.get("judgment_ids"),
                field=f"output plan {section_id}.judgment_ids",
                allow_empty=True,
            )
        )
        artifact_paths = set(
            _text_items(
                section.get("artifact_paths"),
                field=f"output plan {section_id}.artifact_paths",
            )
        )
        if not artifact_paths.issubset(current) or not artifact_paths.issubset(content):
            raise ValueError(f"output plan section {section_id} points to absent deliverables")
    expected_judgments = (
        {"POSITION-LOCK", "RECOMMENDATION-LOCK"}
        if required
        else {"POSITION-LOCK"}
    )
    if (
        set(planned_judgment_ids) != expected_judgments
        or len(planned_judgment_ids) != len(expected_judgments)
    ):
        raise ValueError("output plan judgment IDs disagree with recommendation intent")

    claims = _mapping_items(claim_path_graph.get("claims"), field="claim_path_graph.claims")
    claim_index: dict[str, Mapping[str, object]] = {}
    for claim in claims:
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or claim_id in claim_index:
            raise ValueError("claim path graph claim IDs must be unique")
        claim_index[claim_id] = claim
    if set(claim_index) != plan_claim_ids:
        raise ValueError("locked output plan and claim graph are not bidirectionally closed")

    dossier = content["promax-dossier.md"]
    atlas = content["promax-concept-atlas.md"]
    case_document = content["promax-case-and-countercase.md"]
    essay = content["promax-essay.md"]
    for claim_id in plan_claim_ids:
        statement = claim_index[claim_id].get("statement")
        if not isinstance(statement, str) or statement not in f"{essay}\n{dossier}":
            raise ValueError(f"planned claim {claim_id} is absent from output semantics")

    dispositions = _mapping_items(
        disposition.get("dispositions"),
        field="concept dispositions",
    )
    covered_concepts = _validate_concept_semantics(
        concept_registry=concept_registry,
        dispositions=dispositions,
        plan_concept_ids=plan_concept_ids,
        plan_sections_by_concept=plan_sections_by_concept,
        atlas=atlas,
        essay=essay,
    )
    _validate_position_output(locked_position, essay=essay)
    _validate_recommendation_output(
        locked_recommendation,
        required=required,
        essay=essay,
        dossier=dossier,
    )
    _validate_continuous_essay_semantics(
        essay=essay,
        position=locked_position,
        recommendation=locked_recommendation,
        recommendation_required=required,
        concept_registry=concept_registry,
        dispositions=dispositions,
    )
    _validate_case_semantics(
        case_document=case_document,
        mechanisms=_mapping_items(
            claim_path_graph.get("mechanisms"), field="claim_path_graph.mechanisms"
        ),
        planned_example_ids=planned_example_ids,
        planned_counterexample_ids=planned_counterexample_ids,
    )
    validate_continuation_lineage(
        continuation_ledger,
        manifest=normalized_manifest,
        deliverables=content,
    )

    anomalies: list[str] = []
    if len(essay) < _ESSAY_ADVISORY_MIN_CHARS:
        anomalies.append("essay_length_below_advisory")
    return {
        "status": "valid",
        "anomalies": anomalies,
        "covered_concept_ids": covered_concepts,
        "manifest_sha256": normalized_manifest["manifest_sha256"],
        "position_sha256": sha256_json(locked_position),
        "output_plan_sha256": sha256_json(plan),
    }


def validate_final_chat(
    payload: Mapping[str, object],
    *,
    run_contract: Mapping[str, object],
    position: Mapping[str, object],
    manifest: Mapping[str, object],
    continuation_ledger: Mapping[str, object],
    validated_output: Mapping[str, object],
) -> dict[str, object]:
    """Validate the five-category delivery index separately from the essay."""

    if not isinstance(payload, Mapping):
        raise ValueError("final chat payload must be a structured object")
    _reject_hidden_reasoning(payload)
    if set(payload) != _FINAL_CHAT_FIELDS:
        raise ValueError("final chat must contain exactly the five delivery-index categories")
    if not isinstance(validated_output, Mapping) or validated_output.get("status") != "valid":
        raise ValueError("final chat cannot substitute for an independently validated output bundle")
    if not isinstance(run_contract, Mapping):
        raise ValueError("run contract must be a structured object")
    run_id = run_contract.get("run_id")
    source_sha = run_contract.get("source_snapshot_sha256")
    if not isinstance(run_id, str) or not isinstance(source_sha, str):
        raise ValueError("run contract lacks immutable bindings")
    contract = validate_bound_document(
        "promax-run-contract.schema.json",
        run_contract,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    if not isinstance(position, Mapping):
        raise ValueError("position must be a structured object")
    locked_position = validate_position_lock(
        position,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    normalized_manifest = validate_bound_document(
        "promax-artifact-manifest.schema.json",
        manifest,
        expected_run_id=run_id,
        expected_source_snapshot_sha256=source_sha,
    )
    if normalized_manifest.get("run_contract_sha256") != sha256_json(contract):
        raise ValueError("final chat manifest is bound to a different run contract")
    for field in ("run_nonce", "request_sha256", "mode", "orchestration_mode"):
        if normalized_manifest.get(field) != contract.get(field):
            raise ValueError(f"final chat manifest changes run contract field {field}")
    current = _manifest_records(
        normalized_manifest,
        run_id=run_id,
        source_snapshot_sha256=source_sha,
    )
    if validated_output.get("manifest_sha256") != normalized_manifest.get("manifest_sha256"):
        raise ValueError("final chat references a manifest not covered by output validation")
    if validated_output.get("position_sha256") != sha256_json(locked_position):
        raise ValueError("final chat references a position not covered by output validation")
    if "promax-essay.md" not in current:
        raise ValueError("final chat requires a separately materialized current promax-essay.md")

    status = payload.get("run_status")
    frozen_mode = contract.get("mode")
    incomplete_artifact_status = (
        isinstance(status, str)
        and re.fullmatch(
            r"promax-artifact-incomplete:[a-z0-9-]+(?:\+[a-z0-9-]+)*",
            status,
        )
        is not None
    )
    if status != frozen_mode and not (
        frozen_mode == "promax-artifact-run" and incomplete_artifact_status
    ):
        raise ValueError(
            "final chat run status must match the frozen mode or its checker downgrade"
        )
    summary = payload.get("center_judgment_summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("center judgment summary must be non-empty text")
    locked_statement = locked_position.get("position")
    if not isinstance(locked_statement, str) or locked_statement not in summary:
        raise ValueError("center judgment summary changes or omits the locked position")
    if _contains_any(summary, _ACTION_GRANT_MARKERS):
        raise ValueError("final chat may not grant real-world authorization")

    withdrawals = _text_items(
        payload.get("key_withdrawal_conditions"),
        field="final_chat.key_withdrawal_conditions",
    )
    locked_withdrawals = set(
        _text_items(
            locked_position.get("withdrawal_conditions"),
            field="position.withdrawal_conditions",
        )
    )
    if not set(withdrawals).issubset(locked_withdrawals):
        raise ValueError("final chat invents a withdrawal condition outside the position lock")

    links = _text_items(payload.get("artifact_links"), field="final_chat.artifact_links")
    if len(set(links)) != len(links):
        raise ValueError("final chat artifact links must be unique")
    for path in links:
        validate_relative_artifact_path(path)
        if path not in current:
            raise ValueError(f"final chat links a stale or unknown artifact: {path}")
    if "promax-essay.md" not in links:
        raise ValueError("final chat must link the independent complete essay")

    normalized_ledger = _validate_continuation_structure(
        continuation_ledger,
        manifest=normalized_manifest,
        current_records=current,
    )
    active = [
        item
        for item in _mapping_items(
            normalized_ledger.get("continuations"),
            field="continuation_ledger.continuations",
            allow_empty=True,
        )
        if item.get("status") in {"pending", "in_progress"}
    ]
    expected_entry = active[-1].get("continuation_id") if active else None
    if payload.get("continuation_entry") != expected_entry:
        raise ValueError("final chat continuation entry is not the current continuation")

    return copy.deepcopy(dict(payload))
