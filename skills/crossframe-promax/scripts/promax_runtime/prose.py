from __future__ import annotations

import copy
import hashlib
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
_PROJECTION_FIELDS = frozenset(
    {
        "article_type",
        "house_voice_id",
        "thesis_claim_id",
        "core_concept_ids",
        "atlas_only_concept_ids",
        "selected_techniques",
        "reader_beats",
    }
)
_TECHNIQUE_FIELDS = frozenset(
    {"technique_id", "tier", "paragraph_action", "section_ids"}
)
_BEAT_FIELDS = frozenset(
    {
        "beat_id",
        "function",
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
    {"beat_id", "section_ids", "evidence_excerpts"}
)
_DIMENSION_FIELDS = frozenset(
    {"status", "evidence_excerpts", "repair_target"}
)


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

    beats = _mapping_array(
        reader_projection.get("reader_beats"),
        field="reader_projection.reader_beats",
    )
    beat_ids: set[str] = set()
    beat_claim_ids: set[str] = set()
    for index, beat in enumerate(beats):
        field = f"reader_projection.reader_beats[{index}]"
        _require_exact_fields(beat, expected=_BEAT_FIELDS, field=field)
        beat_id = _non_empty_text(beat.get("beat_id"), field=f"{field}.beat_id")
        if beat_id in beat_ids:
            raise ValueError("reader_projection beat_id values must be unique")
        beat_ids.add(beat_id)
        _non_empty_text(beat.get("function"), field=f"{field}.function")
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
    if thesis_claim_id not in beat_claim_ids:
        raise ValueError(
            "reader_projection thesis_claim_id must be carried by a reader beat"
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
        if excerpt not in essay:
            raise ValueError(
                f"{field} contains an evidence_excerpt not found verbatim in essay"
            )
    return excerpts


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
    for beat in projected_beats:
        beat_id = _non_empty_text(
            beat.get("beat_id"),
            field="output_plan.reader_projection.reader_beats.beat_id",
        )
        if beat_id in projected_by_id:
            raise ValueError("output_plan.reader_projection repeats a reader beat")
        projected_by_id[beat_id] = beat

    mappings = _mapping_array(
        review.get("required_beat_mappings"),
        field="prose review required_beat_mappings",
    )
    mapped_ids: set[str] = set()
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
        _validate_excerpt_array(
            mapping.get("evidence_excerpts"),
            essay=essay,
            field=f"{field}.evidence_excerpts",
            allow_empty=False,
        )
    if mapped_ids != set(projected_by_id):
        raise ValueError(
            "prose review must map every required reader beat exactly once"
        )

    dimensions = review.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise ValueError("prose review dimensions must be an object")
    if set(dimensions) != set(PROSE_REVIEW_DIMENSION_IDS):
        raise ValueError(
            "prose review must contain exactly the eleven prose-review dimensions"
        )
    statuses: list[str] = []
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
        _validate_excerpt_array(
            dimension.get("evidence_excerpts"),
            essay=essay,
            field=f"prose review dimension {dimension_id}.evidence_excerpts",
            allow_empty=status == "fail",
        )
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
    expected_overall = "pass" if all(item == "pass" for item in statuses) else "fail"
    if review.get("overall_status") != expected_overall:
        raise ValueError(
            "prose review overall_status is inconsistent with its eleven dimensions"
        )
    _non_empty_text(review.get("reviewed_at"), field="prose review reviewed_at")
    return copy.deepcopy(dict(review))


__all__ = (
    "ARTICLE_TYPES",
    "PROSE_REVIEW_DIMENSION_IDS",
    "validate_prose_review",
    "validate_reader_projection",
)
