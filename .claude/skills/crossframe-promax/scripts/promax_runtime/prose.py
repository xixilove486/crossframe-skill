from __future__ import annotations

import copy
import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence

from .jsonio import sha256_json


ARTICLE_TYPES = frozenset(
    {
        "reply",
        "public-commentary",
        "concept-explanation",
        "organization-review",
        "case-analysis",
        "debate-refutation",
        "reading-synthesis",
        "trend-deduction",
        "neutral-analysis",
    }
)
PROSE_TECHNIQUE_ROUTES = {
    "reply": {
        "core": ("direct-emotion", "winding-path", "less-is-more"),
        "auxiliary": frozenset(
            {
                "analogical-reasoning",
                "retreat-to-advance",
                "scene-emotion",
                "feint-attack",
                "hide-before-reveal",
                "sparse-outline",
            }
        ),
    },
    "public-commentary": {
        "core": (
            "event-association",
            "layered-argument",
            "positive-negative-contrast",
        ),
        "auxiliary": frozenset(
            {
                "ancient-modern-global",
                "language-momentum",
                "guest-host-contrast",
                "point-surface",
                "praise-blame-interlace",
                "finishing-touch",
            }
        ),
    },
    "concept-explanation": {
        "core": (
            "analogical-reasoning",
            "split-wood-reasoning",
            "virtual-to-real",
        ),
        "auxiliary": frozenset(
            {
                "double-bridge",
                "form-by-object",
                "object-reason",
                "one-word-spine",
                "symbolic-meaning",
                "personified-object",
            }
        ),
    },
    "organization-review": {
        "core": (
            "vertical-narration",
            "fixed-point-changing-scenes",
            "moving-viewpoint",
        ),
        "auxiliary": frozenset(
            {
                "clouds-moon",
                "life-from-dead",
                "motion-for-stillness",
                "praise-blame-interlace",
                "form-by-object",
            }
        ),
    },
    "case-analysis": {
        "core": ("narration-commentary", "fine-carving", "point-surface"),
        "auxiliary": frozenset(
            {
                "coincidence-structure",
                "point-spirit",
                "scene-emotion",
                "suspense",
                "guest-host-contrast",
            }
        ),
    },
    "debate-refutation": {
        "core": (
            "feint-attack",
            "positive-negative-contrast",
            "release-to-capture",
        ),
        "auxiliary": frozenset(
            {
                "raise-high-drop-heavy",
                "retreat-to-advance",
                "same-different",
                "one-stone-many-birds",
                "remove-foundation",
            }
        ),
    },
    "reading-synthesis": {
        "core": ("thread-beads", "one-word-spine", "narration-commentary"),
        "auxiliary": frozenset(
            {
                "final-reveal",
                "meaning-beyond-words",
                "stars-moon",
                "stream-consciousness",
                "symbolic-meaning",
            }
        ),
    },
    "trend-deduction": {
        "core": (
            "small-water-waves",
            "multi-edge-extension",
            "ancient-modern-global",
        ),
        "auxiliary": frozenset(
            {
                "coincidence-structure",
                "event-association",
                "motion-for-stillness",
                "surprise-victory",
                "fixed-point-changing-scenes",
            }
        ),
    },
    "neutral-analysis": {
        "core": (
            "layered-argument",
            "same-different",
            "one-stone-many-birds",
        ),
        "auxiliary": frozenset(
            {
                "release-to-capture",
                "point-surface",
                "less-is-more",
                "multi-edge-extension",
                "virtual-to-real",
            }
        ),
    },
}
PROSE_TECHNIQUE_IDS = frozenset(
    technique_id
    for route in PROSE_TECHNIQUE_ROUTES.values()
    for tier in ("core", "auxiliary")
    for technique_id in route[tier]
)
PROSE_REVIEW_DIMENSION_IDS = (
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
READER_ACTION_IDS = (
    "reality_entry",
    "center_thesis",
    "mechanism_progression",
    "same_dimension_comparison",
    "strongest_counterposition",
    "explicit_position",
    "withdrawal_action_boundary",
    "resonant_close",
)
_POSITION_RELATIONS = frozenset(
    {"supports", "rejects", "mixed", "indeterminate"}
)
_JUDGMENT_STRENGTHS = frozenset(
    {"tentative", "moderate", "strong", "indeterminate"}
)
_OPTION_KINDS = frozenset(
    {
        "maintain_status_quo",
        "active_action",
        "delayed_action",
        "probe_action",
        "exit_or_transfer",
        "no_action",
    }
)
_OPTION_ID_RE = re.compile(r"^OPTION-[A-Za-z0-9][A-Za-z0-9._-]*$")
_PROJECTION_FIELDS = frozenset(
    {
        "article_type",
        "house_voice_id",
        "thesis_claim_id",
        "stance_projection",
        "core_concept_ids",
        "atlas_only_concept_ids",
        "core_concept_bindings",
        "selected_techniques",
        "reader_beats",
    }
)
_CONCEPT_BINDING_FIELDS = frozenset(
    {
        "concept_id",
        "reader_anchor_terms",
        "source_support_spans",
        "source_misuse_spans",
        "reader_explanation",
    }
)
_STANCE_PROJECTION_FIELDS = frozenset(
    {
        "relation_to_proposition",
        "judgment_strength",
        "center_thesis_text",
        "preferred_option_id",
        "preferred_option_kind",
        "preferred_option_text",
        "second_option_id",
        "second_option_kind",
        "second_option_text",
        "withdrawal_text",
        "action_ceiling_text",
    }
)
_TECHNIQUE_FIELDS = frozenset(
    {"technique_id", "tier", "paragraph_action", "section_ids"}
)
_BEAT_FIELDS = frozenset(
    {
        "beat_id",
        "function",
        "action_ids",
        "section_ids",
        "claim_ids",
        "mechanism_ids",
        "evidence_refs",
        "core_concept_ids",
        "technique_ids",
    }
)
_REVIEW_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "source_snapshot_sha256",
        "essay_sha256",
        "position_sha256",
        "output_plan_sha256",
        "article_type",
        "technique_ids",
        "required_beat_mappings",
        "dimensions",
        "overall_status",
        "reviewed_at",
    }
)
_BEAT_MAPPING_FIELDS = frozenset(
    {"beat_id", "action_ids", "section_ids", "evidence_excerpts"}
)
_DIMENSION_FIELDS = frozenset(
    {"status", "evidence_excerpts", "repair_target"}
)
_READER_ACTION_CUES = {
    "reality_entry": (
        "现实",
        "正在",
        "发生",
        "承担",
        "承受",
        "代价",
        "real",
        "cost",
    ),
    "center_thesis": (
        "中心命题",
        "当前应",
        "当前较强",
        "最合理",
        "结论",
        "判断",
        "thesis",
        "judgment",
    ),
    "mechanism_progression": (
        "机制",
        "路径",
        "通道",
        "因为",
        "导致",
        "如果",
        "条件",
        "mechanism",
        "because",
        "if",
    ),
    "same_dimension_comparison": (
        "同一",
        "相同",
        "比较",
        "对照",
        "相比",
        "same",
        "compare",
    ),
    "strongest_counterposition": (
        "最强的反对",
        "最强反方",
        "最有力的反对",
        "最有力的异议",
        "strongest counter",
        "strongest objection",
    ),
    "explicit_position": (
        "我的判断",
        "明确立场",
        "我的结论",
        "所以我",
        "因此我",
        "不足以取代",
        "position",
        "my judgment",
    ),
    "withdrawal_action_boundary": (
        "撤回",
        "退出",
        "停止",
        "切换",
        "不授权",
        "现实授权",
        "另行授权",
        "withdraw",
        "exit",
        "authorization",
    ),
    "resonant_close": (
        "最后",
        "最终",
        "留下",
        "问题",
        "价值",
        "归根",
        "承担",
        "in the end",
        "finally",
    ),
}


def _non_empty_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _mapping_array(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    result: list[Mapping[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field}[{index}] must be an object")
        result.append(item)
    if not result and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    return result


def _text_ids(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
) -> list[str]:
    if (
        isinstance(value, (str, bytes, Mapping))
        or not isinstance(value, Iterable)
    ):
        raise ValueError(f"{field} must be an array or set of identifiers")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be a non-empty identifier")
        result.append(item.strip())
    if not result and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must contain unique identifiers")
    return result


def _require_exact_fields(
    value: Mapping[str, object],
    *,
    expected: frozenset[str],
    field: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{field} must contain exactly its contract fields "
            f"(missing={missing}, extra={extra})"
        )


def _require_subset(
    values: Sequence[str],
    allowed: set[str],
    *,
    field: str,
) -> None:
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"{field} contains references outside P9: {sorted(unknown)}")


def validate_reader_projection(
    reader_projection: Mapping[str, object],
    *,
    applied_concept_ids: Iterable[str],
    section_ids: Iterable[str],
    claim_ids: Iterable[str],
    mechanism_ids: Iterable[str],
    evidence_refs: Iterable[str],
    required_evidence_refs: Iterable[str] | None = None,
    claim_evidence_refs: Mapping[str, Iterable[str]] | None = None,
    mechanism_claim_ids: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Validate the independently callable P9 reader-facing projection."""

    if not isinstance(reader_projection, Mapping):
        raise ValueError("reader_projection must be a structured object")
    _require_exact_fields(
        reader_projection,
        expected=_PROJECTION_FIELDS,
        field="reader_projection",
    )

    article_type = _non_empty_text(
        reader_projection.get("article_type"),
        field="reader_projection.article_type",
    )
    if article_type not in ARTICLE_TYPES:
        raise ValueError("reader_projection.article_type is not a supported article type")
    if reader_projection.get("house_voice_id") != "crossframe-promax":
        raise ValueError(
            "reader_projection.house_voice_id must be exactly crossframe-promax"
        )
    stance_projection = reader_projection.get("stance_projection")
    if not isinstance(stance_projection, Mapping):
        raise ValueError(
            "reader_projection.stance_projection must be a structured object"
        )
    _require_exact_fields(
        stance_projection,
        expected=_STANCE_PROJECTION_FIELDS,
        field="reader_projection.stance_projection",
    )
    relation = _non_empty_text(
        stance_projection.get("relation_to_proposition"),
        field="reader_projection.stance_projection.relation_to_proposition",
    )
    if relation not in _POSITION_RELATIONS:
        raise ValueError(
            "reader_projection.stance_projection has an invalid proposition relation"
        )
    strength = _non_empty_text(
        stance_projection.get("judgment_strength"),
        field="reader_projection.stance_projection.judgment_strength",
    )
    if strength not in _JUDGMENT_STRENGTHS:
        raise ValueError(
            "reader_projection.stance_projection has an invalid judgment strength"
        )
    for field_name in (
        "center_thesis_text",
        "withdrawal_text",
        "action_ceiling_text",
    ):
        _non_empty_text(
            stance_projection.get(field_name),
            field=f"reader_projection.stance_projection.{field_name}",
        )
    for prefix in ("preferred", "second"):
        option_id = stance_projection.get(f"{prefix}_option_id")
        option_kind = stance_projection.get(f"{prefix}_option_kind")
        option_text = stance_projection.get(f"{prefix}_option_text")
        values = (option_id, option_kind, option_text)
        if all(value is None for value in values):
            continue
        if any(value is None for value in values):
            raise ValueError(
                "reader_projection.stance_projection option projections must be "
                "entirely present or entirely null"
            )
        if not isinstance(option_id, str) or _OPTION_ID_RE.fullmatch(option_id) is None:
            raise ValueError(
                f"reader_projection.stance_projection.{prefix}_option_id is invalid"
            )
        if option_kind not in _OPTION_KINDS:
            raise ValueError(
                f"reader_projection.stance_projection.{prefix}_option_kind is invalid"
            )
        _non_empty_text(
            option_text,
            field=(
                f"reader_projection.stance_projection.{prefix}_option_text"
            ),
        )

    known_applied = set(
        _text_ids(applied_concept_ids, field="applied_concept_ids")
    )
    known_sections = set(_text_ids(section_ids, field="section_ids"))
    known_claims = set(_text_ids(claim_ids, field="claim_ids"))
    known_mechanisms = set(
        _text_ids(mechanism_ids, field="mechanism_ids", allow_empty=True)
    )
    known_evidence = set(
        _text_ids(evidence_refs, field="evidence_refs", allow_empty=True)
    )
    core_ids = _text_ids(
        reader_projection.get("core_concept_ids"),
        field="reader_projection.core_concept_ids",
    )
    atlas_only_ids = _text_ids(
        reader_projection.get("atlas_only_concept_ids"),
        field="reader_projection.atlas_only_concept_ids",
        allow_empty=True,
    )
    overlap = set(core_ids) & set(atlas_only_ids)
    if overlap:
        raise ValueError(
            "reader_projection core_concept_ids and atlas_only_concept_ids "
            f"must be disjoint: {sorted(overlap)}"
        )
    if set(core_ids) | set(atlas_only_ids) != known_applied:
        raise ValueError(
            "reader_projection core_concept_ids and atlas_only_concept_ids "
            "must exactly cover applied concepts"
        )
    concept_bindings = _mapping_array(
        reader_projection.get("core_concept_bindings"),
        field="reader_projection.core_concept_bindings",
    )
    bound_concept_ids: list[str] = []
    for index, binding in enumerate(concept_bindings):
        field = f"reader_projection.core_concept_bindings[{index}]"
        _require_exact_fields(
            binding,
            expected=_CONCEPT_BINDING_FIELDS,
            field=field,
        )
        concept_id = _non_empty_text(
            binding.get("concept_id"),
            field=f"{field}.concept_id",
        )
        if concept_id in bound_concept_ids:
            raise ValueError(
                "reader_projection core_concept_bindings repeat a concept"
            )
        bound_concept_ids.append(concept_id)
        anchor_terms = _text_ids(
            binding.get("reader_anchor_terms"),
            field=f"{field}.reader_anchor_terms",
        )
        if not 2 <= len(anchor_terms) <= 4:
            raise ValueError(
                f"{field}.reader_anchor_terms must contain two to four terms"
            )
        if any(
            len(re.findall(r"[A-Za-z0-9\u3400-\u9fff]", term)) < 2
            or len(term) > 24
            for term in anchor_terms
        ):
            raise ValueError(
                f"{field}.reader_anchor_terms must be short substantive terms"
            )
        source_support_spans = _text_ids(
            binding.get("source_support_spans"),
            field=f"{field}.source_support_spans",
        )
        if not 1 <= len(source_support_spans) <= 3 or any(
            len(span) < 4 or len(span) > 500
            for span in source_support_spans
        ):
            raise ValueError(
                f"{field}.source_support_spans must contain one to three "
                "bounded canonical spans"
            )
        source_misuse_spans = _text_ids(
            binding.get("source_misuse_spans"),
            field=f"{field}.source_misuse_spans",
            allow_empty=True,
        )
        if len(source_misuse_spans) > 3 or any(
            len(span) < 4 or len(span) > 500
            for span in source_misuse_spans
        ):
            raise ValueError(
                f"{field}.source_misuse_spans must contain at most three "
                "bounded canonical spans"
            )
        reader_explanation = _non_empty_text(
            binding.get("reader_explanation"),
            field=f"{field}.reader_explanation",
        )
        if not 12 <= len(reader_explanation) <= 800:
            raise ValueError(
                f"{field}.reader_explanation must be bounded natural prose"
            )
    if set(bound_concept_ids) != set(core_ids):
        raise ValueError(
            "reader_projection core_concept_bindings must exactly close "
            "core_concept_ids"
        )

    thesis_claim_id = _non_empty_text(
        reader_projection.get("thesis_claim_id"),
        field="reader_projection.thesis_claim_id",
    )
    if thesis_claim_id not in known_claims:
        raise ValueError("reader_projection.thesis_claim_id is outside P9 claim_ids")

    techniques = _mapping_array(
        reader_projection.get("selected_techniques"),
        field="reader_projection.selected_techniques",
    )
    if not 3 <= len(techniques) <= 5:
        raise ValueError("reader_projection must select three to five techniques")
    technique_ids: list[str] = []
    tiers: list[str] = []
    for index, technique in enumerate(techniques):
        field = f"reader_projection.selected_techniques[{index}]"
        _require_exact_fields(technique, expected=_TECHNIQUE_FIELDS, field=field)
        technique_id = _non_empty_text(
            technique.get("technique_id"),
            field=f"{field}.technique_id",
        )
        if technique_id in technique_ids:
            raise ValueError("reader_projection technique_id values must be unique")
        technique_ids.append(technique_id)
        tier = _non_empty_text(technique.get("tier"), field=f"{field}.tier")
        if tier not in {"core", "auxiliary"}:
            raise ValueError(f"{field}.tier must be core or auxiliary")
        tiers.append(tier)
        _non_empty_text(
            technique.get("paragraph_action"),
            field=f"{field}.paragraph_action",
        )
        technique_sections = _text_ids(
            technique.get("section_ids"),
            field=f"{field}.section_ids",
        )
        _require_subset(
            technique_sections,
            known_sections,
            field=f"{field}.section_ids",
        )
    if tiers.count("core") != 3:
        raise ValueError("reader_projection must select exactly three core techniques")
    if tiers.count("auxiliary") > 2:
        raise ValueError(
            "reader_projection may select at most two auxiliary techniques"
        )
    route = PROSE_TECHNIQUE_ROUTES[article_type]
    expected_core = list(route["core"])
    selected_core = [
        technique_id
        for technique_id, tier in zip(technique_ids, tiers)
        if tier == "core"
    ]
    if selected_core != expected_core:
        raise ValueError(
            "reader_projection core techniques do not match the ordered "
            f"article_type route: expected {expected_core}"
        )
    if tiers[:3] != ["core", "core", "core"] or any(
        tier != "auxiliary" for tier in tiers[3:]
    ):
        raise ValueError(
            "reader_projection must list its three routed core techniques "
            "before auxiliary techniques"
        )
    unknown_auxiliary = set(technique_ids[3:]) - set(route["auxiliary"])
    if unknown_auxiliary:
        raise ValueError(
            "reader_projection auxiliary techniques are outside the "
            f"article_type route: {sorted(unknown_auxiliary)}"
        )

    beats = _mapping_array(
        reader_projection.get("reader_beats"),
        field="reader_projection.reader_beats",
    )
    beat_ids: set[str] = set()
    beat_claim_ids: set[str] = set()
    beat_mechanism_ids: set[str] = set()
    beat_evidence_refs: set[str] = set()
    beat_core_concept_ids: set[str] = set()
    beat_technique_ids: set[str] = set()
    ordered_action_ids: list[str] = []
    normalized_claim_evidence = {
        claim_id: set(
            _text_ids(
                refs,
                field=f"claim_evidence_refs[{claim_id}]",
                allow_empty=True,
            )
        )
        for claim_id, refs in (claim_evidence_refs or {}).items()
    }
    normalized_mechanism_claims = {
        mechanism_id: set(
            _text_ids(
                refs,
                field=f"mechanism_claim_ids[{mechanism_id}]",
                allow_empty=True,
            )
        )
        for mechanism_id, refs in (mechanism_claim_ids or {}).items()
    }
    for index, beat in enumerate(beats):
        field = f"reader_projection.reader_beats[{index}]"
        _require_exact_fields(beat, expected=_BEAT_FIELDS, field=field)
        beat_id = _non_empty_text(beat.get("beat_id"), field=f"{field}.beat_id")
        if beat_id in beat_ids:
            raise ValueError("reader_projection beat_id values must be unique")
        beat_ids.add(beat_id)
        _non_empty_text(beat.get("function"), field=f"{field}.function")
        action_ids = _text_ids(
            beat.get("action_ids"),
            field=f"{field}.action_ids",
        )
        if len(action_ids) > 2:
            raise ValueError(
                f"{field}.action_ids may combine at most two adjacent reader actions"
            )
        unknown_actions = set(action_ids) - set(READER_ACTION_IDS)
        if unknown_actions:
            raise ValueError(
                f"{field}.action_ids contain unknown reader actions: "
                f"{sorted(unknown_actions)}"
            )
        ordered_action_ids.extend(action_ids)
        references = (
            (
                "section_ids",
                _text_ids(beat.get("section_ids"), field=f"{field}.section_ids"),
                known_sections,
            ),
            (
                "claim_ids",
                _text_ids(
                    beat.get("claim_ids"),
                    field=f"{field}.claim_ids",
                    allow_empty=True,
                ),
                known_claims,
            ),
            (
                "mechanism_ids",
                _text_ids(
                    beat.get("mechanism_ids"),
                    field=f"{field}.mechanism_ids",
                    allow_empty=True,
                ),
                known_mechanisms,
            ),
            (
                "evidence_refs",
                _text_ids(
                    beat.get("evidence_refs"),
                    field=f"{field}.evidence_refs",
                    allow_empty=True,
                ),
                known_evidence,
            ),
            (
                "core_concept_ids",
                _text_ids(
                    beat.get("core_concept_ids"),
                    field=f"{field}.core_concept_ids",
                    allow_empty=True,
                ),
                set(core_ids),
            ),
            (
                "technique_ids",
                _text_ids(
                    beat.get("technique_ids"),
                    field=f"{field}.technique_ids",
                    allow_empty=True,
                ),
                set(technique_ids),
            ),
        )
        for reference_name, values, allowed in references:
            _require_subset(
                values,
                allowed,
                field=f"{field}.{reference_name}",
            )
            if reference_name == "claim_ids":
                beat_claim_ids.update(values)
            elif reference_name == "mechanism_ids":
                beat_mechanism_ids.update(values)
            elif reference_name == "evidence_refs":
                beat_evidence_refs.update(values)
            elif reference_name == "core_concept_ids":
                beat_core_concept_ids.update(values)
            elif reference_name == "technique_ids":
                beat_technique_ids.update(values)

        current_claims = set(
            _text_ids(
                beat.get("claim_ids"),
                field=f"{field}.claim_ids",
                allow_empty=True,
            )
        )
        current_mechanisms = set(
            _text_ids(
                beat.get("mechanism_ids"),
                field=f"{field}.mechanism_ids",
                allow_empty=True,
            )
        )
        current_evidence = set(
            _text_ids(
                beat.get("evidence_refs"),
                field=f"{field}.evidence_refs",
                allow_empty=True,
            )
        )
        if not current_claims:
            raise ValueError(f"{field} must carry at least one claim")
        for mechanism_id in current_mechanisms:
            linked_claims = normalized_mechanism_claims.get(mechanism_id)
            if linked_claims is not None and not current_claims & linked_claims:
                raise ValueError(
                    f"{field} mechanism {mechanism_id} is not linked to a claim "
                    "carried by the same reader beat"
                )
        if normalized_claim_evidence:
            linked_evidence = set().union(
                *(
                    normalized_claim_evidence.get(claim_id, set())
                    for claim_id in current_claims
                )
            )
            if not current_evidence.issubset(linked_evidence):
                raise ValueError(
                    f"{field} evidence_refs are not linked to a claim carried "
                    "by the same reader beat"
                )
    if thesis_claim_id not in beat_claim_ids:
        raise ValueError(
            "reader_projection thesis_claim_id must be carried by a reader beat"
        )
    if ordered_action_ids != list(READER_ACTION_IDS):
        raise ValueError(
            "reader beat action_ids must carry the fixed reader action sequence "
            "exactly once and in order"
        )
    if beat_core_concept_ids != set(core_ids):
        raise ValueError(
            "reader beat coverage must exactly close every core concept"
        )
    if beat_technique_ids != set(technique_ids):
        raise ValueError(
            "reader beat coverage must exactly close every selected technique"
        )
    if beat_mechanism_ids != known_mechanisms:
        raise ValueError(
            "reader beat coverage must exactly close every planned mechanism"
        )
    required_evidence = (
        set(
            _text_ids(
                required_evidence_refs,
                field="required_evidence_refs",
                allow_empty=True,
            )
        )
        if required_evidence_refs is not None
        else known_evidence
    )
    if not required_evidence.issubset(beat_evidence_refs):
        raise ValueError(
            "reader beat coverage must close every claim-bound evidence reference"
        )
    return copy.deepcopy(dict(reader_projection))


def _validate_excerpt_array(
    value: object,
    *,
    essay: str,
    field: str,
    allow_empty: bool,
) -> list[str]:
    excerpts = _text_ids(value, field=field, allow_empty=allow_empty)
    for excerpt in excerpts:
        substantive_length = len(
            re.findall(r"[A-Za-z0-9\u3400-\u9fff]", excerpt)
        )
        if substantive_length < 8 or len(excerpt) > 240:
            raise ValueError(
                f"{field} must use a substantive short evidence_excerpt"
            )
        if excerpt not in essay:
            raise ValueError(
                f"{field} contains an evidence_excerpt not found verbatim in essay"
            )
        if essay.find(excerpt) != essay.rfind(excerpt):
            raise ValueError(
                f"{field} contains an ambiguous repeated evidence_excerpt"
            )
    return excerpts


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in re.finditer(
        r"[。！？!?]+|\.(?=\s|$)|(?:\r\n?|\n)[ \t]*(?:\r\n?|\n)+",
        text,
    ):
        end = match.end()
        if text[start:end].strip():
            spans.append((start, end))
        start = end
    if text[start:].strip():
        spans.append((start, len(text)))
    return spans


def _excerpt_sentence_regions(
    essay: str,
    excerpt: str,
    *,
    sentence_spans: Sequence[tuple[int, int]],
) -> tuple[int, ...]:
    excerpt_start = essay.find(excerpt)
    excerpt_end = excerpt_start + len(excerpt)
    regions = tuple(
        index
        for index, (sentence_start, sentence_end) in enumerate(sentence_spans)
        if sentence_start < excerpt_end and sentence_end > excerpt_start
    )
    if not regions:
        raise ValueError("evidence_excerpt does not bind a sentence region")
    return regions


def _reader_paragraph_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    block_start = 0
    separator = re.compile(r"(?:\r\n?|\n)[ \t]*(?:\r\n?|\n)+")
    for match in separator.finditer(text):
        block = text[block_start : match.start()]
        if any(
            line.strip() and not line.lstrip().startswith("#")
            for line in block.splitlines()
        ):
            ranges.append((block_start, match.start()))
        block_start = match.end()
    block = text[block_start:]
    if any(
        line.strip() and not line.lstrip().startswith("#")
        for line in block.splitlines()
    ):
        ranges.append((block_start, len(text)))
    return ranges


def _validate_dimension_evidence(
    *,
    dimension_id: str,
    excerpts: Sequence[str],
    essay: str,
    projection: Mapping[str, object],
    paragraph_ranges: Sequence[tuple[int, int]],
) -> None:
    joined = "\n".join(excerpts)
    folded = joined.casefold()

    def require_cue(cues: Sequence[str], message: str) -> None:
        if not any(cue.casefold() in folded for cue in cues):
            raise ValueError(message)

    if dimension_id == "reality_entry":
        first_start, first_end = paragraph_ranges[0]
        if not any(
            (start := essay.find(excerpt)) < first_end
            and start + len(excerpt) > first_start
            for excerpt in excerpts
        ):
            raise ValueError(
                "prose review reality_entry does not bind the first prose paragraph"
            )
    elif dimension_id == "argument_dependency":
        require_cue(
            ("如果", "只有", "取决于", "因为", "导致", "一旦", "条件", "if", "because"),
            "prose review argument_dependency lacks a dependency relation",
        )
    elif dimension_id == "v8_concept_fidelity":
        bindings = _mapping_array(
            projection.get("core_concept_bindings"),
            field="output plan core_concept_bindings",
        )
        for binding in bindings:
            explanation = _non_empty_text(
                binding.get("reader_explanation"),
                field="output plan core concept reader_explanation",
            )
            anchors = _text_ids(
                binding.get("reader_anchor_terms"),
                field="output plan core concept reader_anchor_terms",
            )
            if not any(
                excerpt in explanation or explanation in excerpt
                for excerpt in excerpts
            ) or not all(anchor in joined for anchor in anchors):
                raise ValueError(
                    "prose review v8_concept_fidelity is not bound to every "
                    "locked core-concept explanation"
                )
    elif dimension_id == "evidence_binding":
        require_cue(
            ("证据", "材料", "来源", "观察", "数据", "显示", "支持", "尚未", "evidence"),
            "prose review evidence_binding lacks an evidence-bearing excerpt",
        )
    elif dimension_id == "strongest_counterposition":
        require_cue(
            ("最强的反对", "最强反方", "最有力的反对", "最有力的异议", "strongest"),
            "prose review strongest_counterposition lacks the strongest counter",
        )
        if re.search(
            r"(?:最强的反对意见|最强反方)[^。！？!?]{0,16}"
            r"(?:根本不存在|并不存在)|"
            r"没有任何[^。！？!?]{0,18}(?:观点|意见)[^。！？!?]{0,12}"
            r"(?:构成|足以成为)(?:反方|异议)?",
            joined,
        ):
            raise ValueError(
                "prose review strongest_counterposition maps a denial of any counter"
            )
    elif dimension_id == "fair_comparison":
        require_cue(
            ("同一", "相同", "比较", "对照", "相比", "same", "compare"),
            "prose review fair_comparison lacks same-dimension comparison",
        )
    elif dimension_id == "position_recommendation_consistency":
        stance = projection.get("stance_projection")
        if not isinstance(stance, Mapping):
            raise ValueError("output plan has no stance_projection")
        required_texts = [
            stance.get("center_thesis_text"),
            stance.get("preferred_option_text"),
            stance.get("second_option_text"),
        ]
        for required_text in required_texts:
            if required_text is not None and (
                not isinstance(required_text, str) or required_text not in joined
            ):
                raise ValueError(
                    "prose review position_recommendation_consistency omits a "
                    "locked reader stance"
                )
    elif dimension_id == "withdrawal_action_boundary":
        stance = projection.get("stance_projection")
        if not isinstance(stance, Mapping):
            raise ValueError("output plan has no stance_projection")
        for field in ("withdrawal_text", "action_ceiling_text"):
            required_text = stance.get(field)
            if not isinstance(required_text, str) or required_text not in joined:
                raise ValueError(
                    "prose review withdrawal_action_boundary must bind both the "
                    "locked withdrawal condition and action ceiling"
                )
    elif dimension_id == "house_voice":
        require_cue(
            ("判断", "承担", "代价", "边界", "撤回", "judgment", "cost"),
            "prose review house_voice lacks the required judgment trace",
        )
    elif dimension_id == "model_flavor_independence":
        require_cue(
            ("但", "反方", "如果", "一旦", "仍", "however", "if"),
            "prose review model_flavor_independence lacks self-opposition or condition",
        )
    elif dimension_id == "audit_leakage":
        if re.search(
            r"\b(?:CLAIM|OPTION|MECH|BEAT|SECTION)-[A-Za-z0-9._-]+\b|"
            r"[\"'](?:position|judgment_strength|repair_target)[\"']\s*:",
            essay,
            re.IGNORECASE,
        ):
            raise ValueError("prose review audit_leakage contradicts the essay")


def _validate_reader_action_evidence(
    *,
    action_ids: Sequence[str],
    excerpts: Sequence[str],
    essay: str,
    paragraph_ranges: Sequence[tuple[int, int]],
) -> list[int]:
    joined = "\n".join(excerpts).casefold()
    excerpt_records = [
        (excerpt, essay.find(excerpt), essay.find(excerpt) + len(excerpt))
        for excerpt in excerpts
    ]
    action_offsets: list[int] = []
    for action_id in action_ids:
        cues = _READER_ACTION_CUES[action_id]
        cue_records = [
            (excerpt, start, end)
            for excerpt, start, end in excerpt_records
            if any(cue.casefold() in excerpt.casefold() for cue in cues)
        ]
        if not cue_records:
            raise ValueError(
                f"reader action {action_id} lacks semantically relevant "
                "evidence_excerpts"
            )
        action_offsets.append(min(start for _, start, _ in cue_records))
        if action_id == "withdrawal_action_boundary":
            if not any(
                cue in joined
                for cue in ("撤回", "收回", "withdraw", "切换", "停止")
            ) or not any(
                cue in joined
                for cue in (
                    "授权",
                    "行动边界",
                    "不构成现实",
                    "analysis only",
                    "authorization",
                )
            ):
                raise ValueError(
                    "reader action withdrawal_action_boundary must bind both "
                    "a withdrawal condition and an action ceiling"
                )
        if action_id == "reality_entry":
            first_start, first_end = paragraph_ranges[0]
            if not any(
                start < first_end and end > first_start
                for _, start, end in cue_records
            ):
                raise ValueError(
                    "reader action reality_entry must bind the first prose paragraph"
                )
        if action_id == "resonant_close":
            last_start, last_end = paragraph_ranges[-1]
            if not any(
                start < last_end and end > last_start
                for _, start, end in cue_records
            ):
                raise ValueError(
                    "reader action resonant_close must bind the last prose paragraph"
                )
    return action_offsets


def validate_prose_review(
    review: Mapping[str, object],
    *,
    essay: str,
    position: Mapping[str, object],
    output_plan: Mapping[str, object],
    run_id: str,
    source_snapshot_sha256: str,
) -> dict[str, object]:
    """Validate a P10 prose review against the current essay and P8/P9 locks."""

    if not isinstance(review, Mapping):
        raise ValueError("prose review must be a structured object")
    if not isinstance(essay, str):
        raise ValueError("essay must be text")
    if not isinstance(position, Mapping):
        raise ValueError("position must be a structured object")
    if not isinstance(output_plan, Mapping):
        raise ValueError("output_plan must be a structured object")
    for artifact_name, artifact in (
        ("position", position),
        ("output_plan", output_plan),
    ):
        if artifact.get("run_id") != run_id:
            raise ValueError(f"{artifact_name}.run_id is not current")
        if artifact.get("source_snapshot_sha256") != source_snapshot_sha256:
            raise ValueError(
                f"{artifact_name}.source_snapshot_sha256 is not current"
            )
    _require_exact_fields(review, expected=_REVIEW_FIELDS, field="prose review")
    if review.get("schema_id") != "crossframe.promax.v8.prose-review":
        raise ValueError("prose review schema_id is invalid")
    if review.get("schema_version") != 1:
        raise ValueError("prose review schema_version must be 1")
    if review.get("run_id") != run_id:
        raise ValueError("prose review run_id is not current")
    if review.get("source_snapshot_sha256") != source_snapshot_sha256:
        raise ValueError("prose review source_snapshot_sha256 is not current")
    expected_hashes = {
        "essay_sha256": hashlib.sha256(essay.encode("utf-8")).hexdigest(),
        "position_sha256": sha256_json(position),
        "output_plan_sha256": sha256_json(output_plan),
    }
    for field, expected in expected_hashes.items():
        if review.get(field) != expected:
            raise ValueError(f"prose review {field} is stale")

    projection = output_plan.get("reader_projection")
    if not isinstance(projection, Mapping):
        raise ValueError("output_plan.reader_projection must be a structured object")
    if review.get("article_type") != projection.get("article_type"):
        raise ValueError(
            "prose review article_type differs from output_plan.reader_projection"
        )
    techniques = _mapping_array(
        projection.get("selected_techniques"),
        field="output_plan.reader_projection.selected_techniques",
    )
    projected_technique_ids = [
        _non_empty_text(
            item.get("technique_id"),
            field="output_plan.reader_projection.selected_techniques.technique_id",
        )
        for item in techniques
    ]
    reviewed_technique_ids = _text_ids(
        review.get("technique_ids"),
        field="prose review technique_ids",
    )
    if reviewed_technique_ids != projected_technique_ids:
        raise ValueError(
            "prose review technique_ids differ from output_plan.reader_projection"
        )

    projected_beats = _mapping_array(
        projection.get("reader_beats"),
        field="output_plan.reader_projection.reader_beats",
    )
    projected_by_id: dict[str, Mapping[str, object]] = {}
    projected_beat_order: list[str] = []
    for beat in projected_beats:
        beat_id = _non_empty_text(
            beat.get("beat_id"),
            field="output_plan.reader_projection.reader_beats.beat_id",
        )
        if beat_id in projected_by_id:
            raise ValueError("output_plan.reader_projection repeats a reader beat")
        projected_by_id[beat_id] = beat
        projected_beat_order.append(beat_id)

    mappings = _mapping_array(
        review.get("required_beat_mappings"),
        field="prose review required_beat_mappings",
    )
    mapped_ids: set[str] = set()
    mapped_beat_order: list[str] = []
    ordered_action_offsets: list[int] = []
    paragraph_ranges = _reader_paragraph_ranges(essay)
    if not paragraph_ranges:
        raise ValueError("prose review essay has no reader prose paragraph")
    for index, mapping in enumerate(mappings):
        field = f"prose review required_beat_mappings[{index}]"
        _require_exact_fields(
            mapping,
            expected=_BEAT_MAPPING_FIELDS,
            field=field,
        )
        beat_id = _non_empty_text(mapping.get("beat_id"), field=f"{field}.beat_id")
        if beat_id in mapped_ids:
            raise ValueError("prose review maps a required reader beat more than once")
        mapped_ids.add(beat_id)
        mapped_beat_order.append(beat_id)
        projected = projected_by_id.get(beat_id)
        if projected is None:
            raise ValueError(
                f"prose review maps reader beat outside P9: {beat_id}"
            )
        mapped_sections = _text_ids(
            mapping.get("section_ids"),
            field=f"{field}.section_ids",
        )
        projected_sections = _text_ids(
            projected.get("section_ids"),
            field=f"output plan reader beat {beat_id}.section_ids",
        )
        if set(mapped_sections) != set(projected_sections):
            raise ValueError(
                f"prose review reader beat {beat_id} section mapping differs from P9"
            )
        mapped_actions = _text_ids(
            mapping.get("action_ids"),
            field=f"{field}.action_ids",
        )
        projected_actions = _text_ids(
            projected.get("action_ids"),
            field=f"output plan reader beat {beat_id}.action_ids",
        )
        if mapped_actions != projected_actions:
            raise ValueError(
                f"prose review reader beat {beat_id} action mapping differs from P9"
            )
        beat_excerpts = _validate_excerpt_array(
            mapping.get("evidence_excerpts"),
            essay=essay,
            field=f"{field}.evidence_excerpts",
            allow_empty=False,
        )
        ordered_action_offsets.extend(
            _validate_reader_action_evidence(
                action_ids=mapped_actions,
                excerpts=beat_excerpts,
                essay=essay,
                paragraph_ranges=paragraph_ranges,
            )
        )
    if mapped_ids != set(projected_by_id):
        raise ValueError(
            "prose review must map every required reader beat exactly once"
        )
    if mapped_beat_order != projected_beat_order:
        raise ValueError(
            "prose review reader beat mappings must preserve P9 beat order"
        )
    if ordered_action_offsets != sorted(ordered_action_offsets):
        raise ValueError(
            "prose review action excerpts do not follow the fixed reader action "
            "sequence in the actual essay"
        )

    dimensions = review.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise ValueError("prose review dimensions must be an object")
    if set(dimensions) != set(PROSE_REVIEW_DIMENSION_IDS):
        raise ValueError(
            "prose review must contain exactly the eleven prose-review dimensions"
        )
    statuses: list[str] = []
    passing_excerpt_sets: list[tuple[str, tuple[str, ...]]] = []
    passing_region_sets: list[tuple[str, tuple[int, ...]]] = []
    sentence_spans = _sentence_spans(essay)
    for dimension_id in PROSE_REVIEW_DIMENSION_IDS:
        dimension = dimensions[dimension_id]
        if not isinstance(dimension, Mapping):
            raise ValueError(
                f"prose review dimension {dimension_id} must be an object"
            )
        _require_exact_fields(
            dimension,
            expected=_DIMENSION_FIELDS,
            field=f"prose review dimension {dimension_id}",
        )
        status = _non_empty_text(
            dimension.get("status"),
            field=f"prose review dimension {dimension_id}.status",
        )
        if status not in {"pass", "fail"}:
            raise ValueError(
                f"prose review dimension {dimension_id}.status must be pass or fail"
            )
        statuses.append(status)
        dimension_excerpts = _validate_excerpt_array(
            dimension.get("evidence_excerpts"),
            essay=essay,
            field=f"prose review dimension {dimension_id}.evidence_excerpts",
            allow_empty=status == "fail",
        )
        if status == "pass":
            _validate_dimension_evidence(
                dimension_id=dimension_id,
                excerpts=dimension_excerpts,
                essay=essay,
                projection=projection,
                paragraph_ranges=paragraph_ranges,
            )
            passing_excerpt_sets.append(
                (dimension_id, tuple(sorted(dimension_excerpts)))
            )
            dimension_regions = tuple(
                sorted(
                    {
                        region
                        for excerpt in dimension_excerpts
                        for region in _excerpt_sentence_regions(
                            essay,
                            excerpt,
                            sentence_spans=sentence_spans,
                        )
                    }
                )
            )
            passing_region_sets.append((dimension_id, dimension_regions))
        repair_target = dimension.get("repair_target")
        if status == "pass" and repair_target is not None:
            raise ValueError(
                f"passing prose review dimension {dimension_id} cannot have a repair_target"
            )
        if status == "fail" and (
            not isinstance(repair_target, str) or not repair_target.strip()
        ):
            raise ValueError(
                f"failing prose review dimension {dimension_id} needs a repair_target"
            )
    excerpt_signatures = [signature for _, signature in passing_excerpt_sets]
    if len(excerpt_signatures) != len(set(excerpt_signatures)):
        raise ValueError(
            "passing prose review dimensions need distinct evidence_excerpt "
            "mappings instead of a reused generic proof"
        )
    excerpt_use: dict[str, int] = {}
    for _, excerpts in passing_excerpt_sets:
        for excerpt in excerpts:
            excerpt_use[excerpt] = excerpt_use.get(excerpt, 0) + 1
    if excerpt_use and max(excerpt_use.values()) > 2:
        raise ValueError(
            "one evidence_excerpt cannot be reused across more than two "
            "prose review dimensions"
        )
    minimum_distinct = (len(passing_excerpt_sets) * 2 + 2) // 3
    if len(excerpt_use) < minimum_distinct:
        raise ValueError(
            "passing prose review dimensions need more distinct evidence_excerpts"
        )
    distinct_region_sets = {
        regions for _, regions in passing_region_sets
    }
    if len(distinct_region_sets) < minimum_distinct:
        raise ValueError(
            "passing prose review dimensions need evidence_excerpts from more "
            "distinct sentence regions"
        )
    region_use: dict[int, int] = {}
    for _, regions in passing_region_sets:
        for region in regions:
            region_use[region] = region_use.get(region, 0) + 1
    if region_use and max(region_use.values()) > 2:
        raise ValueError(
            "one essay sentence region cannot support more than two passing "
            "prose review dimensions"
        )
    expected_overall = "pass" if all(item == "pass" for item in statuses) else "fail"
    if review.get("overall_status") != expected_overall:
        raise ValueError(
            "prose review overall_status is inconsistent with its eleven dimensions"
        )
    _non_empty_text(review.get("reviewed_at"), field="prose review reviewed_at")
    return copy.deepcopy(dict(review))


__all__ = (
    "ARTICLE_TYPES",
    "PROSE_TECHNIQUE_IDS",
    "PROSE_TECHNIQUE_ROUTES",
    "PROSE_REVIEW_DIMENSION_IDS",
    "validate_prose_review",
    "validate_reader_projection",
)
