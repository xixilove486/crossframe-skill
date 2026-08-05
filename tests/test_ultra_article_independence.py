from __future__ import annotations

from dataclasses import replace
import copy
import importlib
import json
from pathlib import Path
import shutil
import sys
import hashlib

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/ultra-runtime/article-packets"
ARTICLE_FIXTURE = FIXTURE_ROOT / "blind-reader-article.md"
EXPECTED_FIXTURE = FIXTURE_ROOT / "blind-reader-expected.json"
AUTHORITY_FIXTURE = FIXTURE_ROOT / "frozen-upstream-authority.json"

EXPECTED_BLIND_READER_FIELDS = (
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
EXPECTED_QUALITY_CHECK_IDS = (
    "reader-contract",
    "repeated-paragraph",
    "template-language",
    "jargon-before-explanation",
    "unresolved-pronoun",
    "unsupported-certainty",
    "truncation-promise",
    "machine-dump",
    "independent-article",
    "semantic-coverage",
    "blind-recovery",
)


def _runtime_module(name: str):
    module_file = RUNTIME_DIR / f"{name}.py"
    if not module_file.is_file():
        pytest.skip(f"Article independence runtime module is missing: {module_file}")
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def coverage():
    return _runtime_module("coverage")


def test_runtime_module_helper_preserves_package_export_coherence() -> None:
    _runtime_module("coverage")
    runtime = importlib.import_module("ultra_runtime")
    schemas = _runtime_module("schemas")

    assert runtime.load_compatibility_matrix is schemas.load_compatibility_matrix


def _fixture_article() -> str:
    return ARTICLE_FIXTURE.read_text(encoding="utf-8")


def _fixture_expected() -> dict[str, str]:
    value = json.loads(EXPECTED_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _authority_fixture() -> dict[str, object]:
    value = json.loads(AUTHORITY_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


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


def _producer_artifacts(coverage, article_text: str):
    article = _runtime_module("article")
    authority = _authority_fixture()
    output_plan = article.build_output_plan_artifact(
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
    output_plan_sha256 = _canonical_sha256(output_plan)
    coverage_artifact = coverage.build_semantic_coverage_artifact(
        article_text,
        output_plan,
        authority["mappings"],
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=output_plan_sha256,
    )
    return authority, output_plan, coverage_artifact


def _verified_coverage(coverage, article_text: str):
    return coverage.SemanticCoverageValidation(
        article_sha256=hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
        covered_unit_ids=tuple(f"fixture-unit-{index}" for index in range(1, 16)),
        missing_unit_ids=(),
        coverage_percent=100.0,
        coverage_complete=True,
    )


def _blind_output_plan() -> dict[str, object]:
    titles = (
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
    field_units_by_section = {
        1: ["fixture-unit-1", "fixture-unit-2"],
        2: ["fixture-unit-3"],
        3: ["fixture-unit-4", "fixture-unit-5"],
        4: ["fixture-unit-6"],
        5: ["fixture-unit-7"],
        6: ["fixture-unit-8"],
        7: ["fixture-unit-9", "fixture-unit-10", "fixture-unit-11"],
        8: ["fixture-unit-14"],
        9: ["fixture-unit-12"],
        10: ["fixture-unit-13", "fixture-unit-15"],
    }
    entries = [
        {
            "section_id": f"reader-{ordinal:02d}",
            "title": title,
            "ordinal": ordinal,
            "semantic_unit_ids": field_units_by_section.get(
                ordinal, [f"appendix-unit-{ordinal:02d}"]
            ),
            "dependency_hashes": ["a" * 64],
        }
        for ordinal, title in enumerate(titles, 1)
    ]
    return {
        "phase_id": "U10",
        "official_filename_allowed": False,
        "coverage_required": True,
        "required_artifacts": [
            {
                "path": "artifacts/U09-U10-verdict/ultra-verdict.json",
                "sha256": "a" * 64,
                "media_type": "application/json",
            }
        ],
        "article_path": "work/authoring/article.partial.md",
        "sections": entries[:10],
        "appendices": entries[10:],
    }


def _blind_contract_fields() -> tuple[dict[str, object], ...]:
    supports = (
        "缩小试点范围",
        "两个独立来源",
        "可逆选择变成难以退出",
        "沟通延迟下降",
        "权限交叠还是预算调整",
        "审批与反馈",
        "新增审批抵消",
        "审批拥堵位置",
        "两周内继续降低",
        "新增协调会",
        "退出成本持续上升",
        "审批设计者",
        "记录每次审批等待",
        "预算调整对延迟",
        "预算调整足以解释",
    )
    section_ordinals = (1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7, 9, 10, 8, 10)
    return tuple(
        {
            "field_id": field_id,
            "expected_normalized_value": coverage_value,
            "section_id": f"reader-{section_ordinal:02d}",
            "semantic_unit_ids": [f"fixture-unit-{field_index}"],
            "supporting_excerpts": [support],
        }
        for field_index, (field_id, coverage_value, support, section_ordinal) in enumerate(zip(
            EXPECTED_BLIND_READER_FIELDS,
            _fixture_expected().values(),
            supports,
            section_ordinals,
            strict=True,
        ), 1)
    )


def _blind_contract(coverage, article_text: str):
    return coverage.freeze_blind_recovery_contract(
        article_text,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, article_text),
        fields=_blind_contract_fields(),
    )


def _review(
    coverage,
    article_text: str,
    *,
    coverage_validation=None,
    blind_recovery_contract=None,
    external_dependencies=(),
):
    validation = coverage_validation or _verified_coverage(coverage, article_text)
    contract = blind_recovery_contract or _blind_contract(coverage, article_text)
    return coverage.review_article(
        article_text,
        output_plan=_blind_output_plan(),
        coverage_validation=validation,
        blind_recovery_contract=contract,
        external_dependencies=external_dependencies,
    )


def test_blind_reader_contract_names_every_required_recovery_field(coverage) -> None:
    assert coverage.BLIND_READER_FIELDS == EXPECTED_BLIND_READER_FIELDS


def test_u11_article_review_producer_emits_frozen_fifteen_and_eleven_rows(
    coverage,
) -> None:
    schemas = _runtime_module("schemas")
    article_text = _fixture_article()
    authority, output_plan, coverage_artifact = _producer_artifacts(
        coverage, article_text
    )
    output_plan_sha256 = _canonical_sha256(output_plan)
    coverage_sha256 = _canonical_sha256(coverage_artifact)

    artifact = coverage.build_article_review_artifact(
        article_text,
        output_plan,
        coverage_artifact,
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=output_plan_sha256,
        expected_coverage_artifact_sha256=coverage_sha256,
    )

    assert coverage.U11_ARTICLE_REVIEW_PATH == "work/authoring/U11-article-review.json"
    assert [row["field_id"] for row in artifact["blind_reader_fields"]] == list(
        EXPECTED_BLIND_READER_FIELDS
    )
    assert len(artifact["blind_reader_fields"]) == 15
    assert all(row["recovered"] is True for row in artifact["blind_reader_fields"])
    assert [row["check_id"] for row in artifact["quality_checks"]] == list(
        EXPECTED_QUALITY_CHECK_IDS
    )
    assert len(artifact["quality_checks"]) == 11
    assert all(row["status"] == "pass" for row in artifact["quality_checks"])
    assert artifact["overall_status"] == "mechanical-complete"
    assert artifact["official_filename_allowed"] is False
    assert artifact["needs_u12_validation"] is True
    assert artifact["u12_validator_artifact_required"] is True
    assert artifact["output_plan_artifact_sha256"] == output_plan_sha256
    assert artifact["coverage_artifact_sha256"] == coverage_sha256
    assert artifact["content_sha256"] == _canonical_sha256(
        {key: value for key, value in artifact.items() if key != "content_sha256"}
    )
    validated = schemas.validate_phase_artifact(
        "ultra-article-review.schema.json",
        artifact,
        expected_schema_id="crossframe.ultra.v82.article-review",
        expected_run_id=authority["run_id"],
        expected_version_binding=authority["version_binding"],
        expected_phase_id="U11",
    )
    assert validated == artifact


def test_u11_article_review_producer_records_controlled_fail_without_publishing(
    coverage,
) -> None:
    schemas = _runtime_module("schemas")
    repeated = (
        "核查依据明确写出“缩小试点范围”，并把两周观察设为扩大前的条件。"
    )
    article_text = _fixture_article().rstrip() + f"\n\n{repeated}\n"
    authority, output_plan, coverage_artifact = _producer_artifacts(
        coverage, article_text
    )
    artifact = coverage.build_article_review_artifact(
        article_text,
        output_plan,
        coverage_artifact,
        run_id=authority["run_id"],
        version_binding=authority["version_binding"],
        generated_at=authority["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
        expected_coverage_artifact_sha256=_canonical_sha256(coverage_artifact),
    )

    checks = {row["check_id"]: row["status"] for row in artifact["quality_checks"]}
    assert artifact["overall_status"] == "mechanical-fail"
    assert checks["repeated-paragraph"] == "fail"
    assert artifact["official_filename_allowed"] is False
    assert artifact["review_stage"] == "mechanical-precheck"
    validated = schemas.validate_phase_artifact(
        "ultra-article-review.schema.json",
        artifact,
        expected_schema_id="crossframe.ultra.v82.article-review",
        expected_run_id=authority["run_id"],
        expected_version_binding=authority["version_binding"],
        expected_phase_id="U11",
    )
    assert validated == artifact


@pytest.mark.parametrize(
    "mutation",
    ("article-sha256", "plan-authority", "semantic-universe-authority"),
)
def test_u11_article_review_rejects_stale_or_role_swapped_coverage(
    coverage, mutation: str
) -> None:
    article_text = _fixture_article()
    authority, output_plan, coverage_artifact = _producer_artifacts(
        coverage, article_text
    )
    tampered = copy.deepcopy(coverage_artifact)
    if mutation == "article-sha256":
        tampered["article_sha256"] = "0" * 64
    elif mutation == "plan-authority":
        tampered["output_plan_artifact_sha256"] = tampered[
            "semantic_universe_sha256"
        ]
    else:
        tampered["semantic_universe_sha256"] = tampered[
            "output_plan_artifact_sha256"
        ]
    tampered["content_sha256"] = _canonical_sha256(
        {key: value for key, value in tampered.items() if key != "content_sha256"}
    )

    with pytest.raises(ValueError, match="article|output-plan|semantic.*universe|authority"):
        coverage.build_article_review_artifact(
            article_text,
            output_plan,
            tampered,
            run_id=authority["run_id"],
            version_binding=authority["version_binding"],
            generated_at=authority["generated_at"]["u11"],
            expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
            expected_coverage_artifact_sha256=_canonical_sha256(tampered),
        )


def test_u11_blind_recovery_matches_frozen_normalized_value_hash_not_label_only(
    coverage,
) -> None:
    article = _runtime_module("article")
    authority = _authority_fixture()
    altered = copy.deepcopy(authority)
    altered["blind_recovery_expectations"][0]["normalized_value_sha256"] = "0" * 64
    output_plan = article.build_output_plan_artifact(
        run_id=altered["run_id"],
        version_binding=altered["version_binding"],
        generated_at=altered["generated_at"]["u10"],
        u9_parent_event_sha256=altered["u9_parent_event_sha256"],
        article_path=altered["article_path"],
        sections=altered["sections"],
        appendices=altered["appendices"],
        required_artifacts=altered["required_artifacts"],
        semantic_universe=altered["semantic_universe"],
        blind_recovery_expectations=altered["blind_recovery_expectations"],
    )
    article_text = _fixture_article()
    coverage_artifact = coverage.build_semantic_coverage_artifact(
        article_text,
        output_plan,
        altered["mappings"],
        run_id=altered["run_id"],
        version_binding=altered["version_binding"],
        generated_at=altered["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
    )
    review = coverage.build_article_review_artifact(
        article_text,
        output_plan,
        coverage_artifact,
        run_id=altered["run_id"],
        version_binding=altered["version_binding"],
        generated_at=altered["generated_at"]["u11"],
        expected_output_plan_artifact_sha256=_canonical_sha256(output_plan),
        expected_coverage_artifact_sha256=_canonical_sha256(coverage_artifact),
    )

    rows = {row["field_id"]: row for row in review["blind_reader_fields"]}
    checks = {row["check_id"]: row for row in review["quality_checks"]}
    assert rows["main_verdict"] == {
        "field_id": "main_verdict",
        "recovered": False,
        "excerpt": None,
    }
    assert checks["blind-recovery"]["status"] == "fail"
    assert review["overall_status"] == "mechanical-fail"
    assert review["official_filename_allowed"] is False


def test_mechanical_review_requires_a_frozen_blind_recovery_contract(coverage) -> None:
    article_text = _fixture_article()
    contract = _blind_contract(coverage, article_text)
    review = coverage.review_article(
        article_text,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, article_text),
        blind_recovery_contract=contract,
    )
    assert review.overall_status == "mechanical-complete"
    assert review.blind_recovery_contract_sha256 == contract.contract_sha256


def test_blind_recovery_contract_hash_uses_stable_public_version(coverage) -> None:
    contract = _blind_contract(coverage, _fixture_article())
    payload = {
        "contract_version": "ultra-blind-recovery-v1",
        "article_sha256": contract.article_sha256,
        "output_plan_sha256": contract.output_plan_sha256,
        "coverage_article_sha256": contract.coverage_article_sha256,
        "coverage_validation_sha256": contract.coverage_validation_sha256,
        "fields": [
            {
                "field_id": field.field_id,
                "expected_normalized_value": field.expected_normalized_value,
                "section_id": field.section_id,
                "semantic_unit_ids": list(field.semantic_unit_ids),
                "supporting_excerpts": list(field.supporting_excerpts),
            }
            for field in contract.fields
        ],
    }
    expected_sha256 = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    assert contract.contract_sha256 == expected_sha256


def test_frozen_blind_recovery_contract_rejects_hollow_field_echoes_and_swaps(
    coverage,
) -> None:
    original = _fixture_article()
    contract = _blind_contract(coverage, original)
    hollow = original.replace(
        _fixture_expected()["main_verdict"],
        "支持建议应先行动；若有时间再观察记录。",
    ).replace(
        "缩小试点范围",
        "支持建议应先行动",
    )
    review = coverage.review_article(
        hollow,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, hollow),
        blind_recovery_contract=contract,
    )
    assert review.overall_status == "mechanical-fail"
    assert "blind-recovery-contract" in {issue.code for issue in review.quality_issues}

    swapped = original.replace(_fixture_expected()["main_verdict"], "__SWAPPED__")
    swapped = swapped.replace(
        _fixture_expected()["action"], _fixture_expected()["main_verdict"], 1
    ).replace("__SWAPPED__", _fixture_expected()["action"])
    review = coverage.review_article(
        swapped,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, swapped),
        blind_recovery_contract=contract,
    )
    assert review.overall_status == "mechanical-fail"
    assert "blind-recovery-contract" in {issue.code for issue in review.quality_issues}


def test_frozen_blind_recovery_contract_rejects_other_article_and_reused_support(
    coverage,
) -> None:
    original = _fixture_article()
    contract = _blind_contract(coverage, original)
    other_article = original.replace("审批拥堵", "人员拥堵")
    review = coverage.review_article(
        other_article,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, other_article),
        blind_recovery_contract=contract,
    )
    assert review.overall_status == "mechanical-fail"
    assert "blind-recovery-contract" in {issue.code for issue in review.quality_issues}

    duplicated = [dict(field) for field in _blind_contract_fields()]
    duplicated[1]["supporting_excerpts"] = duplicated[0]["supporting_excerpts"]
    duplicated[1]["semantic_unit_ids"] = duplicated[0]["semantic_unit_ids"]
    with pytest.raises(ValueError, match="reuse.*supporting|reuse.*semantic"):
        coverage.freeze_blind_recovery_contract(
            original,
            output_plan=_blind_output_plan(),
            coverage_validation=_verified_coverage(coverage, original),
            fields=duplicated,
        )


def test_frozen_blind_recovery_contract_binds_the_complete_coverage_validation(
    coverage,
) -> None:
    article_text = _fixture_article()
    contract = _blind_contract(coverage, article_text)
    verified = _verified_coverage(coverage, article_text)
    altered_coverage = coverage.SemanticCoverageValidation(
        article_sha256=verified.article_sha256,
        covered_unit_ids=verified.covered_unit_ids + ("unrelated-unit",),
        missing_unit_ids=(),
        coverage_percent=100.0,
        coverage_complete=True,
    )
    review = coverage.review_article(
        article_text,
        output_plan=_blind_output_plan(),
        coverage_validation=altered_coverage,
        blind_recovery_contract=contract,
    )
    assert review.overall_status == "mechanical-fail"
    assert "blind-recovery-contract" in {issue.code for issue in review.quality_issues}


def test_review_rejects_rehashed_contract_that_reuses_a_semantic_unit(coverage) -> None:
    article_text = _fixture_article()
    contract = _blind_contract(coverage, article_text)
    fields = list(contract.fields)
    fields[1] = replace(fields[1], semantic_unit_ids=fields[0].semantic_unit_ids)
    payload = coverage._contract_payload(
        article_sha256=contract.article_sha256,
        output_plan_sha256=contract.output_plan_sha256,
        coverage_article_sha256=contract.coverage_article_sha256,
        coverage_validation_sha256=contract.coverage_validation_sha256,
        fields=fields,
    )
    rebuilt = replace(
        contract,
        fields=tuple(fields),
        contract_sha256=coverage._canonical_sha256(payload),
    )
    review = coverage.review_article(
        article_text,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, article_text),
        blind_recovery_contract=rebuilt,
    )
    assert review.overall_status == "mechanical-fail"
    assert "blind-recovery-contract" in {issue.code for issue in review.quality_issues}


def test_deletion_fixture_recovers_the_complete_judgment_from_article_alone(
    coverage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clean_room = tmp_path / "blind-reader"
    clean_room.mkdir()
    article_path = clean_room / "article.md"
    shutil.copyfile(ARTICLE_FIXTURE, article_path)
    expected = _fixture_expected()

    assert [path.name for path in clean_room.iterdir()] == ["article.md"]
    monkeypatch.chdir(clean_room)
    recovered = coverage.recover_blind_reader_fields(
        article_path.read_text(encoding="utf-8")
    )
    assert recovered == expected
    assert tuple(recovered) == EXPECTED_BLIND_READER_FIELDS


@pytest.mark.parametrize(
    ("label", "field_id"),
    [
        ("主判断", "main_verdict"),
        ("未知项", "unknowns"),
        ("二阶推演", "order_2"),
        ("反转条件", "reversal_conditions"),
    ],
)
def test_blind_reader_recovery_fails_closed_when_a_required_field_is_absent(
    coverage, label: str, field_id: str
) -> None:
    article_text = _fixture_article().replace(f"**{label}：**", f"**删去的{label}：**")
    with pytest.raises(ValueError, match=field_id):
        coverage.recover_blind_reader_fields(article_text)


def test_mechanical_precheck_passes_without_dossier_or_external_files(
    coverage,
) -> None:
    review = _review(coverage, _fixture_article())
    assert review.overall_status == "mechanical-complete"
    assert review.review_stage == "mechanical-precheck"
    assert review.needs_u12_validation is True
    assert review.quality_issues == ()
    assert review.external_dependencies == ()
    assert dict(review.blind_reader_fields) == _fixture_expected()
    assert review.official_filename_allowed is False


def test_article_review_derives_external_dependencies_from_reader_prose(
    coverage,
) -> None:
    clean = _review(
        coverage, _fixture_article(), external_dependencies=["caller-only.xlsx"]
    )
    assert clean.overall_status == "mechanical-complete"
    assert clean.external_dependencies == ()

    dependent_text = _fixture_article().replace(
        "文中每个判断都以可见的事实句、条件句和反例句说明作用；",
        "请见排班附表.xlsx，并参见本季度报告以补足依据。",
    )
    dependent = _review(coverage, dependent_text)
    assert dependent.overall_status == "mechanical-fail"
    assert "external-dependency" in {issue.code for issue in dependent.quality_issues}
    assert dependent.external_dependencies


def test_article_review_rejects_non_fenced_multiline_machine_dump(coverage) -> None:
    machine_dump = '{\n  "status": "partial"\n}'
    article_text = _fixture_article().replace(
        "两份独立记录都显示，小范围试行时沟通延迟下降，而扩大到全部成员后延迟重新上升。",
        machine_dump,
    )
    review = _review(
        coverage,
        article_text,
        blind_recovery_contract=_blind_contract(coverage, _fixture_article()),
    )
    assert review.overall_status == "mechanical-fail"
    assert {"machine-dump", "reader-contract"}.issubset(
        {issue.code for issue in review.quality_issues}
    )


def test_blind_reader_recovery_rejects_placeholder_short_or_duplicate_fields(
    coverage,
) -> None:
    article_text = _fixture_article()
    placeholder = article_text.replace(
        "尚不知道延迟上升来自人数、权限交叠还是同时发生的预算调整。",
        "无法判断。",
    )
    with pytest.raises(ValueError, match="unknowns|placeholder|specific"):
        coverage.recover_blind_reader_fields(placeholder)

    short = article_text.replace(
        "现有材料最支持先缩小试点范围、保留退出通道，再依据两周内的可核查变化决定是否扩大。",
        "继续观察。",
    )
    with pytest.raises(ValueError, match="main_verdict|specific|short"):
        coverage.recover_blind_reader_fields(short)

    duplicate = article_text.replace(
        "中等；关键记录来自两个独立来源，但长期效果仍缺少观察。",
        "现有材料最支持先缩小试点范围、保留退出通道，再依据两周内的可核查变化决定是否扩大。",
    )
    with pytest.raises(ValueError, match="confidence|duplicate|boilerplate"):
        coverage.recover_blind_reader_fields(duplicate)


def test_clean_room_path_runs_the_deterministic_article_only_gate(
    coverage, tmp_path: Path
) -> None:
    article_path = tmp_path / "input.md"
    article_path.write_text(_fixture_article(), encoding="utf-8")
    review = coverage.review_article_in_clean_room(
        article_path,
        output_plan=_blind_output_plan(),
        coverage_validation=_verified_coverage(coverage, _fixture_article()),
        blind_recovery_contract=_blind_contract(coverage, _fixture_article()),
    )
    assert review.overall_status == "mechanical-complete"
    assert dict(review.blind_reader_fields) == _fixture_expected()


def test_article_review_never_authorizes_an_official_filename_or_u12_evaluator(
    coverage,
) -> None:
    before_evaluation = _review(coverage, _fixture_article())
    assert before_evaluation.overall_status == "mechanical-complete"
    assert before_evaluation.official_filename_allowed is False
    assert before_evaluation.needs_u12_validation is True
    assert before_evaluation.u12_validator_artifact_required is True
    with pytest.raises(TypeError):
        coverage.review_article_in_clean_room(
            ARTICLE_FIXTURE,
            output_plan=_blind_output_plan(),
            coverage_validation=_verified_coverage(coverage, _fixture_article()),
            blind_recovery_contract=_blind_contract(coverage, _fixture_article()),
            fresh_evaluator=object(),
        )


def test_article_review_rejects_caller_boolean_and_mismatched_coverage_artifact(
    coverage,
) -> None:
    with pytest.raises(TypeError):
        coverage.review_article(
            _fixture_article(), coverage_complete=True, u12_passed=True
        )

    stale = _verified_coverage(coverage, _fixture_article())
    stale = coverage.SemanticCoverageValidation(
        article_sha256="0" * 64,
        covered_unit_ids=stale.covered_unit_ids,
        missing_unit_ids=(),
        coverage_percent=100.0,
        coverage_complete=True,
    )
    review = _review(coverage, _fixture_article(), coverage_validation=stale)
    assert review.overall_status == "mechanical-fail"
    assert "semantic-coverage-unverified" in {issue.code for issue in review.quality_issues}


def test_article_review_fails_when_coverage_or_independence_is_incomplete(
    coverage,
) -> None:
    incomplete = _review(
        coverage,
        _fixture_article(),
        coverage_validation=coverage.SemanticCoverageValidation(
            article_sha256=hashlib.sha256(_fixture_article().encode("utf-8")).hexdigest(),
            covered_unit_ids=(),
            missing_unit_ids=("missing-unit",),
            coverage_percent=0.0,
            coverage_complete=False,
        ),
    )
    assert incomplete.overall_status == "mechanical-fail"
    assert "semantic-coverage-unverified" in {
        issue.code for issue in incomplete.quality_issues
    }
    assert incomplete.official_filename_allowed is False

    dependent_text = _fixture_article().replace(
        "文中每个判断都以可见的事实句、条件句和反例句说明作用；",
        "完整依据详见附件 dossier.json；",
    )
    dependent = _review(
        coverage, dependent_text, external_dependencies=["dossier.json"]
    )
    assert dependent.overall_status == "mechanical-fail"
    assert "external-dependency" in {issue.code for issue in dependent.quality_issues}
    assert dependent.official_filename_allowed is False


def test_blind_reader_recovery_rejects_distinct_anchor_stuffed_field_values(coverage) -> None:
    article_text = _fixture_article()
    replacements = {
        "main_verdict": "支持建议应先行动；若有时间再观察记录。",
        "confidence": "中等置信来自证据记录，但仍有未知不足。",
        "steelmanned_user_position": "用户认为需要支持并担心条件，因此要求行动。",
        "decisive_evidence": "证据记录显示观察比较后发现支持。",
        "unknowns": "未知原因是否影响，尚不确定且缺少证据。",
        "circle_relations": "圈层角色通过通道连接并产生反馈约束。",
        "mechanisms": "审批增加导致等待放大，因此需要调整。",
        "strongest_rival": "另一种解释可能成立，但需要比较反例。",
        "order_1": "短期会继续变化，需要直接等待时间。",
        "order_2": "若新增协调，之后会扩大影响并反转。",
        "order_3": "长期规则会持续改变成本与退出安排。",
        "five_verdicts": "事实、预测、价值、责任与授权都需要判断。",
        "action": "行动维持执行记录；若有指标再停止。",
        "residuals": "残差仍未解释，材料不足时停止进入下一步。",
        "reversal_conditions": "如果条件显示变化，就撤回并重新比较改变。",
    }
    for field_id, replacement in replacements.items():
        article_text = article_text.replace(_fixture_expected()[field_id], replacement)

    with pytest.raises(ValueError, match="concrete|excerpt|field-specific"):
        coverage.recover_blind_reader_fields(article_text)


@pytest.mark.parametrize(
    "article_text",
    (
        "关键数据另册保存。本文只给出摘要而不展开。",
        "昨日会议纪要载有完整依据；本文仅给出摘要。",
        "排序所依据的数据在上级报告中，本文仅给出摘要。",
    ),
)
def test_external_dependency_detector_finds_cross_sentence_omitted_support(
    coverage, article_text: str
) -> None:
    assert coverage.detect_external_dependencies(article_text)


@pytest.mark.parametrize("extension", ("toml", "ini", "yaml", "yml", "xml", "cfg", "conf"))
def test_external_dependency_detector_finds_contextual_configuration_files(
    coverage, extension: str
) -> None:
    text = f"完整依据见配置.{extension}；本文仅给出摘要。"
    assert coverage.detect_external_dependencies(text)


@pytest.mark.parametrize(
    "article_text",
    (
        "本文批判《组织改革报告》的推理，并逐项给出可核查反例。",
        "《论语》的讨论用于比较责任语言，不作为本案证据。",
    ),
)
def test_external_dependency_detector_does_not_flag_commentary_or_citation(
    coverage, article_text: str
) -> None:
    assert coverage.detect_external_dependencies(article_text) == ()


@pytest.mark.parametrize(
    "article_text",
    (
        "本文讨论《配置管理》一书的版本 v1.2.3，不把它作为本案依据。",
        "版本 config.toml.v2 只是命名，不承载本文省略的依据。",
    ),
)
def test_external_dependency_detector_does_not_flag_books_or_versions(coverage, article_text: str) -> None:
    assert coverage.detect_external_dependencies(article_text) == ()


def test_duplicate_or_empty_recovery_labels_are_not_accepted_as_blind_readable(
    coverage,
) -> None:
    article_text = _fixture_article()
    duplicate = article_text.replace(
        "**置信度：** 中等；关键记录来自两个独立来源，但长期效果仍缺少观察。",
        "**主判断：** 第二个相互冲突的主判断。",
    )
    with pytest.raises(ValueError, match="main_verdict|duplicate"):
        coverage.recover_blind_reader_fields(duplicate)

    empty = article_text.replace(
        "**主判断：** 现有材料最支持先缩小试点范围、保留退出通道，再依据两周内的可核查变化决定是否扩大。",
        "**主判断：**",
    )
    with pytest.raises(ValueError, match="main_verdict|empty"):
        coverage.recover_blind_reader_fields(empty)


def test_blind_reader_labels_must_occur_in_their_reader_section(coverage) -> None:
    article_text = _fixture_article()
    action_line = (
        "**首选行动：** 维持两周小范围试点，同时记录每次审批等待；"
        "若等待下降且预算因素被排除，再考虑逐步扩大。"
    )
    confidence_line = (
        "**置信度：** 中等；关键记录来自两个独立来源，但长期效果仍缺少观察。"
    )
    misplaced = article_text.replace(action_line + "\n\n", "", 1).replace(
        confidence_line, confidence_line + "\n\n" + action_line, 1
    )
    with pytest.raises(ValueError, match="action|section|行动"):
        coverage.recover_blind_reader_fields(misplaced)


@pytest.mark.parametrize(
    ("label", "field_id", "hollow_value"),
    (
        ("主判断", "main_verdict", "需要把当前背景纳入后续安排，才能继续推进相关讨论。"),
        ("置信度", "confidence", "当前背景仍需持续讨论，之后再处理相关信息。"),
        ("用户观点的最强重建", "steelmanned_user_position", "应结合现有背景继续梳理各方说法。"),
        ("决定性证据", "decisive_evidence", "相关材料需要放在背景中进一步讨论。"),
        ("未知项", "unknowns", "后续仍要结合具体背景持续分析。"),
        ("圈层关系", "circle_relations", "不同方面需要在当前条件下继续协调。"),
        ("机制", "mechanisms", "有关过程仍应结合背景作进一步讨论。"),
        ("最强竞争解释", "strongest_rival", "其他说法需要在当前背景中继续考虑。"),
        ("一阶推演", "order_1", "后续变化仍需结合背景进一步观察。"),
        ("二阶推演", "order_2", "进一步影响需要持续讨论才能判断。"),
        ("三阶推演", "order_3", "长期情况仍要放进当前背景持续分析。"),
        ("五类裁决", "five_verdicts", "各项判断需要结合背景继续讨论。"),
        ("首选行动", "action", "下一步需要结合当前背景持续推进讨论。"),
        ("残差", "residuals", "剩余问题应在后续背景中进一步讨论。"),
        ("反转条件", "reversal_conditions", "变化条件需要结合背景继续分析。"),
    ),
)
def test_blind_reader_recovery_rejects_field_specific_hollow_paraphrases(
    coverage, label: str, field_id: str, hollow_value: str
) -> None:
    article_text = _fixture_article()
    expected_value = _fixture_expected()[field_id]
    article_text = article_text.replace(expected_value, hollow_value)

    with pytest.raises(ValueError, match="field-specific|information"):
        coverage.recover_blind_reader_fields(article_text)
