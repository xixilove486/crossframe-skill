from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import unicodedata

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
COVERAGE_MODULE = RUNTIME_DIR / "coverage.py"
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/ultra-runtime/article-packets"
AUTHORITY_FIXTURE = FIXTURE_ROOT / "frozen-upstream-authority.json"
ARTICLE_FIXTURE = FIXTURE_ROOT / "blind-reader-article.md"

EXPECTED_UNIT_KINDS = (
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
TITLES = (
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
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差和停止点",
    "预测、时间窗、指标和解析条件",
    "概念、证据和来源锚点",
    "未知项与框架缺口候选",
)
STATUSES = (
    "applied",
    "retained",
    "unresolved",
    "used-in-reasoning",
    "promised-to-reader",
)


def _runtime_module(name: str):
    module_file = RUNTIME_DIR / f"{name}.py"
    if not module_file.is_file():
        pytest.skip(f"Semantic coverage runtime module is missing: {module_file}")
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    sys.modules.pop(f"ultra_runtime.{name}", None)
    return importlib.import_module(f"ultra_runtime.{name}")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()


def _authority_fixture() -> dict[str, object]:
    value = json.loads(AUTHORITY_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _frozen_output_plan() -> dict[str, object]:
    article = _runtime_module("article")
    authority = _authority_fixture()
    return article.build_output_plan_artifact(
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u10"],
        u9_parent_event_sha256=authority["u9_parent_event_sha256"],
        article_path=authority["article_path"],
        sections=authority["sections"],
        appendices=authority["appendices"],
        required_artifacts=authority["required_artifacts"],
        semantic_universe=authority["semantic_universe"],
        blind_recovery_expectations=authority["blind_recovery_expectations"],
    )


@pytest.fixture
def coverage():
    return _runtime_module("coverage")


def _coverage_case() -> tuple[
    str,
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    plan_entries: list[dict[str, object]] = []
    bodies: list[str] = []
    units: list[dict[str, object]] = []
    mappings: list[dict[str, object]] = []
    for ordinal, title in enumerate(TITLES, 1):
        section_id = f"reader-{ordinal:02d}"
        excerpt = (
            f"语义单元{ordinal}在本案中承担第{ordinal}项具体作用，并改变对应判断。"
        )
        plan_entries.append(
            {
                "section_id": section_id,
                "title": title,
                "ordinal": ordinal,
                "semantic_unit_ids": [
                    f"semantic-{min(ordinal, len(EXPECTED_UNIT_KINDS)):02d}"
                ],
            }
        )
        bodies.append(f"## {title}\n\n{excerpt}")
        if ordinal <= len(EXPECTED_UNIT_KINDS):
            unit_id = f"semantic-{ordinal:02d}"
            units.append(
                {
                    "unit_id": unit_id,
                    "unit_kind": EXPECTED_UNIT_KINDS[ordinal - 1],
                    "status": STATUSES[(ordinal - 1) % len(STATUSES)],
                }
            )
            mappings.append(
                {
                    "unit_id": unit_id,
                    "unit_kind": EXPECTED_UNIT_KINDS[ordinal - 1],
                    "section_id": section_id,
                    "normalized_excerpt": unicodedata.normalize("NFKC", excerpt),
                    "source_refs": [f"P{ordinal:04d}"],
                }
            )
    article_text = "\n\n".join(bodies) + "\n"
    output_plan = {
        "sections": plan_entries[:10],
        "appendices": plan_entries[10:],
    }
    return article_text, output_plan, units, mappings


def test_semantic_coverage_runtime_module_exists_for_red_gate() -> None:
    assert COVERAGE_MODULE.is_file(), (
        f"Semantic coverage runtime module is missing: {COVERAGE_MODULE}"
    )


def test_semantic_coverage_requires_all_thirteen_substantive_unit_kinds(
    coverage,
) -> None:
    assert coverage.REQUIRED_UNIT_KINDS == EXPECTED_UNIT_KINDS
    article_text, output_plan, units, mappings = _coverage_case()
    result = coverage.validate_semantic_coverage(
        article_text, output_plan, units, mappings
    )
    assert result.article_sha256 == hashlib.sha256(article_text.encode()).hexdigest()
    assert result.covered_unit_ids == tuple(
        f"semantic-{number:02d}" for number in range(1, 14)
    )
    assert result.missing_unit_ids == ()
    assert result.coverage_percent == 100.0
    assert result.coverage_complete is True


def test_u11_semantic_coverage_producer_conforms_to_public_schema_and_hash_authority(
    coverage,
) -> None:
    schemas = _runtime_module("schemas")
    authority = _authority_fixture()
    output_plan = _frozen_output_plan()
    output_plan_sha256 = _canonical_sha256(output_plan)
    article_text = ARTICLE_FIXTURE.read_text(encoding="utf-8")

    artifact = coverage.build_semantic_coverage_artifact(
        article_text,
        output_plan,
        authority["mappings"],
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=output_plan_sha256,
    )

    assert coverage.U11_SEMANTIC_COVERAGE_PATH == (
        "work/authoring/U11-semantic-coverage.json"
    )
    assert artifact["output_plan_artifact_sha256"] == output_plan_sha256
    assert artifact["semantic_universe_sha256"] == output_plan[
        "semantic_universe_sha256"
    ]
    assert artifact["article_sha256"] == hashlib.sha256(
        article_text.encode("utf-8")
    ).hexdigest()
    assert artifact["required_unit_kinds"] == list(EXPECTED_UNIT_KINDS)
    assert artifact["coverage_complete"] is True
    assert artifact["coverage_percent"] == 100
    assert artifact["missing_unit_ids"] == []
    assert artifact["content_sha256"] == _canonical_sha256(
        {key: value for key, value in artifact.items() if key != "content_sha256"}
    )
    validated = schemas.validate_phase_artifact(
        "ultra-semantic-coverage.schema.json",
        artifact,
        expected_schema_id="crossframe.ultra.v82.semantic-coverage",
        expected_run_id=authority["run_id"],
        expected_version_binding=authority["version_binding"],
        expected_phase_id="U11",
    )
    assert validated == artifact


def test_u11_semantic_coverage_producer_records_controlled_incomplete_without_publishing(
    coverage,
) -> None:
    schemas = _runtime_module("schemas")
    authority = _authority_fixture()
    output_plan = _frozen_output_plan()
    article_text = ARTICLE_FIXTURE.read_text(encoding="utf-8")
    mappings = list(authority["mappings"][:-1])

    artifact = coverage.build_semantic_coverage_artifact(
        article_text,
        output_plan,
        mappings,
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
    )

    assert artifact["coverage_complete"] is False
    assert artifact["coverage_percent"] < 100
    assert artifact["missing_unit_ids"] == [
        authority["semantic_universe"][-1]["unit_id"]
    ]
    assert "official_filename_allowed" not in artifact
    validated = schemas.validate_phase_artifact(
        "ultra-semantic-coverage.schema.json",
        artifact,
        expected_schema_id="crossframe.ultra.v82.semantic-coverage",
        expected_run_id=authority["run_id"],
        expected_version_binding=authority["version_binding"],
        expected_phase_id="U11",
    )
    assert validated == artifact


def test_u11_semantic_coverage_rejects_stale_output_plan_hash(coverage) -> None:
    authority = _authority_fixture()
    output_plan = _frozen_output_plan()
    with pytest.raises(ValueError, match="output-plan.*hash|hash.*output-plan|authority"):
        coverage.build_semantic_coverage_artifact(
            ARTICLE_FIXTURE.read_text(encoding="utf-8"),
            output_plan,
            authority["mappings"],
            run_id=authority["run_id"],
            version_binding=authority["version_binding"],
            generated_at=authority["generated_at"]["u11"],
            expected_output_plan_artifact_sha256="0" * 64,
        )


def test_coverage_cannot_self_report_complete_when_a_required_kind_is_absent(
    coverage,
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    units.pop()
    mappings.pop()
    with pytest.raises(ValueError, match="required.*kind|reversal-condition|missing"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_unknown_unit_status_cannot_hide_a_substantive_unit(coverage) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    units[0]["status"] = "silently-ignored"
    mappings.pop(0)
    with pytest.raises(ValueError, match="status|claim|required"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "missing|coverage"),
        ("duplicate", "duplicate"),
        ("wrong-kind", "kind"),
        ("unknown-unit", "unknown|unexpected"),
    ],
)
def test_coverage_rejects_missing_duplicate_mismatched_or_unknown_units(
    coverage, mutation: str, message: str
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    if mutation == "missing":
        mappings.pop()
    elif mutation == "duplicate":
        mappings.append(dict(mappings[0]))
    elif mutation == "wrong-kind":
        mappings[0]["unit_kind"] = "evidence"
    elif mutation == "unknown-unit":
        mappings[0]["unit_id"] = "semantic-never-required"

    with pytest.raises(ValueError, match=message):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_ranking_reasoning_and_reader_promises_cannot_live_only_in_dossier(
    coverage,
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    units.append(
        {
            "unit_id": "rank-affecting-rival",
            "unit_kind": "branch",
            "status": "tested-rejected",
            "affects_ranking": True,
        }
    )
    with pytest.raises(ValueError, match="rank-affecting-rival|missing|coverage"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)

    units[-1] = {
        "unit_id": "reader-promise",
        "unit_kind": "unknown",
        "status": "tested-rejected",
        "promised_to_reader": True,
    }
    with pytest.raises(ValueError, match="reader-promise|missing|coverage"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_unknown_pending_concept_is_an_unresolved_reader_obligation(coverage) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    units.append(
        {
            "unit_id": "concept-unknown-pending",
            "unit_kind": "unknown",
            "status": "unknown-pending",
        }
    )
    with pytest.raises(ValueError, match="concept-unknown-pending|missing|coverage"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_tested_rejected_concept_remains_a_reader_visible_retained_unit(
    coverage,
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    units.append(
        {
            "unit_id": "concept-tested-rejected",
            "unit_kind": "branch",
            "status": "tested-rejected",
        }
    )
    with pytest.raises(ValueError, match="concept-tested-rejected|missing|coverage"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("excerpt-absent", "excerpt|occur"),
        ("wrong-section", "section|excerpt"),
        ("heading-only", "body|heading|excerpt"),
        ("not-normalized", "normalized"),
        ("reverse-order", "order"),
    ],
)
def test_coverage_validates_normalized_prose_occurrence_and_article_order(
    coverage, mutation: str, message: str
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    if mutation == "excerpt-absent":
        mappings[0]["normalized_excerpt"] = "这句话从未进入文章。"
    elif mutation == "wrong-section":
        mappings[0]["section_id"] = "reader-02"
    elif mutation == "heading-only":
        mappings[0]["normalized_excerpt"] = TITLES[0]
    elif mutation == "not-normalized":
        mappings[0]["normalized_excerpt"] = "语义单元1   在本案中承担"
    elif mutation == "reverse-order":
        mappings[:] = list(reversed(mappings))

    with pytest.raises(ValueError, match=message):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_coverage_mapping_unit_must_belong_to_its_frozen_section(coverage) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    mappings[0]["section_id"] = "reader-02"
    mappings[0]["normalized_excerpt"] = mappings[1]["normalized_excerpt"]

    with pytest.raises(ValueError, match="section.*semantic|semantic.*section|frozen"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_complete_coverage_mapping_requires_nonempty_source_refs(coverage) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    mappings[0]["source_refs"] = []

    with pytest.raises(ValueError, match="source.*empty|source.*required"):
        coverage.validate_semantic_coverage(article_text, output_plan, units, mappings)


def test_u11_mapping_source_refs_are_bound_to_frozen_semantic_unit(coverage) -> None:
    authority = _authority_fixture()
    output_plan = _frozen_output_plan()
    article_text = ARTICLE_FIXTURE.read_text(encoding="utf-8")
    mappings = copy.deepcopy(authority["mappings"])
    mappings[0]["source_refs"] = ["FORGED-SOURCE"]

    with pytest.raises(ValueError, match="source.*frozen|source.*authority"):
        coverage.build_semantic_coverage_artifact(
            article_text,
            output_plan,
            mappings,
            run_id=authority["run_id"],
            version_binding=authority["version_binding"],
            generated_at=authority["generated_at"]["u11"],
            expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
        )


def test_normalized_excerpt_can_match_whitespace_variation_without_marker_stuffing(
    coverage,
) -> None:
    article_text, output_plan, units, mappings = _coverage_case()
    original = str(mappings[0]["normalized_excerpt"])
    article_text = article_text.replace(
        "语义单元1在本案中承担", "语义单元1在本案中\n承担", 1
    )
    mappings[0]["normalized_excerpt"] = original
    result = coverage.validate_semantic_coverage(
        article_text, output_plan, units, mappings
    )
    assert result.coverage_complete is True


def test_quality_inspection_penalizes_the_named_independence_failures(coverage) -> None:
    repeated = "这一段是可被复制到任何主题的空泛模板。"
    text = (
        "在本节中，我们将进行全面分析。\n\n"
        "Ω 表明结论必然成立。\n\n"
        "这证明了一切。\n\n"
        f"{repeated}\n\n{repeated}\n\n"
        "其余证据详见附件 evidence.json。"
    )
    issue_codes = {
        issue.code
        for issue in coverage.inspect_article_quality(
            text, external_dependencies=["evidence.json"]
        )
    }
    assert {
        "repeated-paragraph",
        "template-language",
        "jargon-before-explanation",
        "unresolved-pronoun",
        "unsupported-certainty",
        "external-dependency",
    }.issubset(issue_codes)


def test_quality_inspection_detects_unregistered_external_file_reference(coverage) -> None:
    issue_codes = {
        issue.code
        for issue in coverage.inspect_article_quality(
            "详细计算请见附件 工作簿.xlsx；文章内不再复述其结论。",
            external_dependencies=(),
        )
    }
    assert "external-dependency" in issue_codes


@pytest.mark.parametrize(
    "article_text",
    (
        "完整依据载于《年度审计报告》，本文不再复述其结论。",
        "结论由内部调查总表支持，文章仅给出摘要。",
    ),
)
def test_quality_inspection_detects_indirect_named_document_dependencies(
    coverage, article_text: str
) -> None:
    issue_codes = {
        issue.code
        for issue in coverage.inspect_article_quality(
            article_text, external_dependencies=()
        )
    }
    assert "external-dependency" in issue_codes
