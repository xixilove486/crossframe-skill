from __future__ import annotations

from dataclasses import FrozenInstanceError
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = REPO_ROOT / "skills/crossframe-ultra"
SCRIPTS_DIR = ULTRA_ROOT / "scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
ARTICLE_MODULE = RUNTIME_DIR / "article.py"
AUTHORITY_FIXTURE = (
    REPO_ROOT
    / "tests/fixtures/ultra-runtime/article-packets/frozen-upstream-authority.json"
)

EXPECTED_SECTIONS = (
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
EXPECTED_APPENDICES = (
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差和停止点",
    "预测、时间窗、指标和解析条件",
    "概念、证据和来源锚点",
    "未知项与框架缺口候选",
)
OFFICIAL_FILENAME = "CrossFrame-Ultra-完整文章.md"


def _runtime_module(name: str):
    module_file = RUNTIME_DIR / f"{name}.py"
    if not module_file.is_file():
        pytest.skip(f"Article runtime module is missing: {module_file}")
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def article():
    return _runtime_module("article")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _build_frozen_output_plan(article) -> dict[str, object]:
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


def _valid_case() -> tuple[dict[str, object], list[dict[str, object]]]:
    entries: list[dict[str, object]] = []
    packets: list[dict[str, object]] = []
    required_artifacts: list[dict[str, str]] = []
    for ordinal, title in enumerate(EXPECTED_SECTIONS + EXPECTED_APPENDICES, 1):
        section_id = f"reader-{ordinal:02d}"
        dependency_hash = hashlib.sha256(f"dependency-{ordinal}".encode()).hexdigest()
        semantic_unit_id = f"unit-{ordinal:02d}"
        entries.append(
            {
                "section_id": section_id,
                "title": title,
                "ordinal": ordinal,
                "semantic_unit_ids": [semantic_unit_id],
                "dependency_hashes": [dependency_hash],
            }
        )
        prose = (
            f"## {title}\n\n"
            f"第{ordinal}部分给出一项可核查的具体说明，并交代它怎样影响本案判断。"
        )
        packets.append(
            {
                "packet_id": f"packet-{ordinal:02d}",
                "section_id": section_id,
                "ordinal": ordinal,
                "dependency_hashes": [dependency_hash],
                "semantic_unit_ids": [semantic_unit_id],
                "source_refs": [f"P{ordinal:04d}"],
                "prose": prose,
                "prose_sha256": _sha256(prose),
            }
        )
        required_artifacts.append(
            {
                "path": f"artifacts/U09-U10-verdict/dependency-{ordinal:02d}.json",
                "sha256": dependency_hash,
                "media_type": "application/json",
            }
        )
    return (
        {
            "phase_id": "U10",
            "article_path": "work/authoring/article.partial.md",
            "required_artifacts": required_artifacts,
            "coverage_required": True,
            "official_filename_allowed": False,
            "sections": entries[:10],
            "appendices": entries[10:],
        },
        packets,
    )


def _replace_prose(packet: dict[str, object], prose: str) -> None:
    packet["prose"] = prose
    packet["prose_sha256"] = _sha256(prose)


def test_article_runtime_module_exists_for_red_gate() -> None:
    assert ARTICLE_MODULE.is_file(), (
        f"Article runtime module is missing: {ARTICLE_MODULE}"
    )


def test_reader_contract_has_exact_ten_sections_and_five_same_file_appendices(
    article, tmp_path: Path
) -> None:
    assert article.REQUIRED_READER_SECTIONS == EXPECTED_SECTIONS
    assert article.REQUIRED_READER_APPENDICES == EXPECTED_APPENDICES

    plan, packets = _valid_case()
    assembled = article.assemble_article(plan, packets, tmp_path / "article.partial.md")
    headings = [
        line.removeprefix("## ")
        for line in assembled.article_text.splitlines()
        if line.startswith("## ")
    ]
    assert headings == list(EXPECTED_SECTIONS + EXPECTED_APPENDICES)


def test_u10_output_plan_producer_conforms_to_public_schema_and_external_authority(
    article,
) -> None:
    schemas = _runtime_module("schemas")
    authority = _authority_fixture()
    artifact = _build_frozen_output_plan(article)

    assert article.U10_OUTPUT_PLAN_PATH == "work/authoring/U10-output-plan.json"
    assert article.ARTICLE_PACKET_DIRECTORY == "work/authoring/article/packets"
    assert artifact["u9_parent_event_sha256"] == authority["u9_parent_event_sha256"]
    assert artifact["required_artifacts"] == authority["required_artifacts"]
    assert artifact["semantic_universe_sha256"] == _canonical_sha256(
        authority["semantic_universe"]
    )
    assert artifact["content_sha256"] == _canonical_sha256(
        {key: value for key, value in artifact.items() if key != "content_sha256"}
    )
    validated = schemas.validate_phase_artifact(
        "ultra-output-plan.schema.json",
        artifact,
        expected_schema_id="crossframe.ultra.v82.output-plan",
        expected_run_id=authority["run_id"],
        expected_version_binding=authority["version_binding"],
        expected_phase_id="U10",
    )
    assert validated == artifact


def test_u10_output_plan_rejects_string_artifacts_empty_dependencies_and_swapped_authority(
    article,
) -> None:
    authority = _authority_fixture()

    string_artifacts = copy.deepcopy(authority)
    string_artifacts["required_artifacts"] = [
        str(item["path"]) for item in authority["required_artifacts"]
    ]
    with pytest.raises(ValueError, match="required.*artifact|object|mapping"):
        article.build_output_plan_artifact(
            run_id=string_artifacts["run_id"],
            version_binding=string_artifacts["version_binding"],
            generated_at=string_artifacts["generated_at"]["u10"],
            u9_parent_event_sha256=string_artifacts["u9_parent_event_sha256"],
            article_path=string_artifacts["article_path"],
            sections=string_artifacts["sections"],
            appendices=string_artifacts["appendices"],
            required_artifacts=string_artifacts["required_artifacts"],
            semantic_universe=string_artifacts["semantic_universe"],
            blind_recovery_expectations=string_artifacts[
                "blind_recovery_expectations"
            ],
        )

    missing_dependency = copy.deepcopy(authority)
    missing_dependency["sections"][0]["dependency_hashes"] = []
    with pytest.raises(ValueError, match="dependenc.*empty|dependenc.*required"):
        article.build_output_plan_artifact(
            run_id=missing_dependency["run_id"],
            version_binding=missing_dependency["version_binding"],
            generated_at=missing_dependency["generated_at"]["u10"],
            u9_parent_event_sha256=missing_dependency["u9_parent_event_sha256"],
            article_path=missing_dependency["article_path"],
            sections=missing_dependency["sections"],
            appendices=missing_dependency["appendices"],
            required_artifacts=missing_dependency["required_artifacts"],
            semantic_universe=missing_dependency["semantic_universe"],
            blind_recovery_expectations=missing_dependency[
                "blind_recovery_expectations"
            ],
        )

    artifact = _build_frozen_output_plan(article)
    swapped = copy.deepcopy(artifact)
    swapped["u9_parent_event_sha256"] = "f" * 64
    swapped["content_sha256"] = _canonical_sha256(
        {key: value for key, value in swapped.items() if key != "content_sha256"}
    )
    with pytest.raises(ValueError, match="parent.*authority|authority.*parent"):
        article.validate_output_plan_artifact(
            swapped,
            expected_run_id=authority["run_id"],
            expected_version_binding=authority["version_binding"],
            expected_u9_parent_event_sha256=authority["u9_parent_event_sha256"],
            expected_required_artifacts=authority["required_artifacts"],
        )


def test_u10_rejects_plan_and_packet_that_share_an_unfrozen_dependency(article) -> None:
    plan, packets = _valid_case()
    forged_dependency = "f" * 64
    plan["sections"][0]["dependency_hashes"] = [forged_dependency]
    packets[0]["dependency_hashes"] = [forged_dependency]

    with pytest.raises(ValueError, match="unknown.*artifact|required.*authority"):
        article.order_and_validate_packets(plan, packets)


@pytest.mark.parametrize(
    "machine_dump",
    (
        '{\n  "status": "partial"\n}',
        '{\n  "type": "object",\n  "properties": {\n    "unit": {"type": "string"}\n  }\n}',
        '[\n  {\n    "name": "claim",\n    "value": "applied"\n  }\n]',
        "record_count = 15\nconfidence_level = \"medium\"\nreview_state = \"approved\"\nsource_bundle = \"frozen\"",
        "[review]\nrecord_count=15\nconfidence_level=medium\nreview_state=approved\nsource_bundle=frozen",
        "review:\n  state: approved\n  coverage:\n    record_count: 15\n    source_bundle: frozen",
        "review:\n  state: approved\n  sources:\n    - alpha\n    - beta",
        "review:\n  state:\n    phase: U10\n    approved: true\n  sources:\n    - alpha\n    - beta",
        "review:\n  state:\n    decision:\n      approved: true\n  sources:\n    - alpha\n    - beta",
        "review:\n  sources:\n    - name: alpha\n      state: frozen\n    - name: beta\n      state: frozen",
        "记录数：15\n置信等级：中等\n复核状态：通过\n来源包：冻结",
        "- field: verdict\n  value: provisional\n- field: confidence\n  value: medium\n- field: action\n  value: hold",
    ),
)
def test_reader_contract_rejects_non_fenced_multiline_machine_dumps(
    article, machine_dump: str
) -> None:
    plan, packets = _valid_case()
    text = "\n\n".join(str(packet["prose"]).strip() for packet in packets) + "\n"
    text = text.replace(
        "第3部分给出一项可核查的具体说明，并交代它怎样影响本案判断。",
        machine_dump,
        1,
    )

    with pytest.raises(ValueError, match="JSON|schema|machine"):
        article.validate_reader_article(text)

    # Ordinary prose may use braces and Markdown lists without becoming a dump.
    ordinary = text.replace(machine_dump, "- 条件：{可逆、可观察、可退出} 都要逐项说明。")
    article.validate_reader_article(ordinary)

    flat_reader_list = text.replace(
        machine_dump,
        "- 条件：可逆\n- 指标：可观察\n- 退出：可执行",
    )
    article.validate_reader_article(flat_reader_list)


def test_reader_contract_rejects_non_fenced_machine_key_value_records(
    article, tmp_path: Path
) -> None:
    plan, packets = _valid_case()
    machine_record = (
        "record_count: 15\n"
        "confidence_level: medium\n"
        "review_state: approved\n"
        "source_bundle: frozen"
    )
    _replace_prose(
        packets[2],
        f"## {EXPECTED_SECTIONS[2]}\n\n{machine_record}",
    )

    with pytest.raises(ValueError, match="YAML|key-value|machine"):
        article.assemble_article(plan, packets, tmp_path / "machine.partial.md")

    article.validate_reader_article(
        "\n\n".join(str(packet["prose"]).strip() for packet in _valid_case()[1])
        + "\n"
    )


def test_packet_assembly_is_deterministic_and_writes_one_canonical_file(
    article, tmp_path: Path
) -> None:
    plan, packets = _valid_case()
    first = article.assemble_article(plan, packets, tmp_path / "first.partial.md")
    second = article.assemble_article(
        plan, reversed(packets), tmp_path / "second.partial.md"
    )

    assert first.article_sha256 == second.article_sha256
    assert first.article_text == second.article_text
    assert first.article_text.endswith("\n")
    assert "\n\n\n" not in first.article_text
    assert (tmp_path / "first.partial.md").read_bytes() == first.article_text.encode(
        "utf-8"
    )
    assert first.packet_ids == tuple(f"packet-{number:02d}" for number in range(1, 16))
    assert first.semantic_unit_ids == tuple(
        f"unit-{number:02d}" for number in range(1, 16)
    )
    assert first.article_sha256 == _sha256(first.article_text)
    with pytest.raises(FrozenInstanceError):
        first.article_text = "mutated"


def test_packet_boundary_whitespace_is_hash_checked_then_canonicalized(
    article, tmp_path: Path
) -> None:
    plan, packets = _valid_case()
    raw = f"\n\n{packets[0]['prose']}\n\n"
    _replace_prose(packets[0], raw)
    assembled = article.assemble_article(
        plan, packets, tmp_path / "canonical.partial.md"
    )
    assert assembled.article_text.startswith(f"## {EXPECTED_SECTIONS[0]}\n\n")
    assert "\n\n\n" not in assembled.article_text


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "missing"),
        ("duplicate-packet-id", "duplicate.*packet"),
        ("duplicate-section", "duplicate.*section"),
        ("stale-dependency", "dependenc"),
        ("stale-prose", "prose.*sha|hash"),
        ("stale-semantic-units", "semantic"),
        ("extra-packet-field", "field|key"),
    ],
)
def test_packet_freeze_rejects_missing_duplicate_or_stale_material(
    article, tmp_path: Path, mutation: str, message: str
) -> None:
    plan, packets = _valid_case()
    if mutation == "missing":
        packets.pop()
    elif mutation == "duplicate-packet-id":
        packets[1]["packet_id"] = packets[0]["packet_id"]
    elif mutation == "duplicate-section":
        packets[1]["section_id"] = packets[0]["section_id"]
    elif mutation == "stale-dependency":
        packets[0]["dependency_hashes"] = ["f" * 64]
    elif mutation == "stale-prose":
        packets[0]["prose"] = str(packets[0]["prose"]) + "被事后改写"
    elif mutation == "stale-semantic-units":
        packets[0]["semantic_unit_ids"] = ["replacement-unit"]
    elif mutation == "extra-packet-field":
        packets[0]["hidden_payload"] = "not frozen"

    with pytest.raises(ValueError, match=message):
        article.assemble_article(plan, packets, tmp_path / "invalid.partial.md")
    assert not (tmp_path / "invalid.partial.md").exists()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        ("wrong-title", "title|section"),
        ("wrong-ordinal", "ordinal|order"),
        ("missing-appendix", "append"),
        ("duplicate-plan-id", "duplicate.*section"),
        ("official-enabled", "official"),
        ("official-path", "official|partial"),
        ("coverage-disabled", "coverage"),
    ],
)
def test_output_plan_must_freeze_the_complete_reader_shape(
    article, tmp_path: Path, mutate: str, message: str
) -> None:
    plan, packets = _valid_case()
    if mutate == "wrong-title":
        plan["sections"][0]["title"] = "泛化摘要"
    elif mutate == "wrong-ordinal":
        plan["sections"][0]["ordinal"] = 2
    elif mutate == "missing-appendix":
        plan["appendices"].pop()
    elif mutate == "duplicate-plan-id":
        plan["sections"][1]["section_id"] = plan["sections"][0]["section_id"]
    elif mutate == "official-enabled":
        plan["official_filename_allowed"] = True
    elif mutate == "official-path":
        plan["article_path"] = f"delivery/{OFFICIAL_FILENAME}"
    elif mutate == "coverage-disabled":
        plan["coverage_required"] = False

    with pytest.raises(ValueError, match=message):
        article.assemble_article(plan, packets, tmp_path / "invalid.partial.md")


@pytest.mark.parametrize(
    ("bad_prose", "message"),
    [
        (
            '## 主判断、范围和置信度\n\n```json\n{"schema_id": "x"}\n```',
            "JSON|schema|reader prose",
        ),
        (
            '## 主判断、范围和置信度\n\n{"任意键": ["机器数据", "不是读者解释"]}',
            "JSON|machine|reader prose",
        ),
        (
            "## 主判断、范围和置信度\n\nmain_verdict 与 dependency_hashes 如上。",
            "internal|field",
        ),
        (
            "## 主判断、范围和置信度\n\n篇幅所限，剩余内容将在下一篇继续。",
            "truncat|continu|篇幅|完整",
        ),
        (
            "## 主判断、范围和置信度\n\nM01、M02、M03、M04、M05、M06。",
            "concept|具体|stuff",
        ),
        (
            "## 主判断、范围和置信度\n\n边界、嵌入、外溢、递归、转义、锁定、同构。",
            "concept|具体|stuff",
        ),
    ],
)
def test_reader_prose_rejects_machine_dumps_internal_fields_truncation_and_stuffing(
    article, tmp_path: Path, bad_prose: str, message: str
) -> None:
    plan, packets = _valid_case()
    _replace_prose(packets[0], bad_prose)
    with pytest.raises(ValueError, match=message):
        article.assemble_article(plan, packets, tmp_path / "bad.partial.md")


def test_reader_prose_rejects_empty_and_repeated_boilerplate_bodies(
    article, tmp_path: Path
) -> None:
    plan, packets = _valid_case()
    _replace_prose(packets[0], "## 主判断、范围和置信度")
    with pytest.raises(ValueError, match="empty|body"):
        article.assemble_article(plan, packets, tmp_path / "empty.partial.md")

    plan, packets = _valid_case()
    repeated = "这一段只是可以复制到任何主题的通用模板，没有说明本案中的具体作用。"
    _replace_prose(packets[0], f"## {EXPECTED_SECTIONS[0]}\n\n{repeated}")
    _replace_prose(packets[1], f"## {EXPECTED_SECTIONS[1]}\n\n{repeated}")
    with pytest.raises(ValueError, match="repeat|boilerplate|重复"):
        article.assemble_article(plan, packets, tmp_path / "repeated.partial.md")


def test_one_semantic_unit_cannot_be_stuffed_into_multiple_packets(
    article, tmp_path: Path
) -> None:
    plan, packets = _valid_case()
    duplicate_unit = plan["sections"][0]["semantic_unit_ids"]
    plan["sections"][1]["semantic_unit_ids"] = duplicate_unit
    packets[1]["semantic_unit_ids"] = duplicate_unit
    with pytest.raises(ValueError, match="duplicate.*semantic|semantic.*multiple"):
        article.assemble_article(plan, packets, tmp_path / "duplicate-unit.partial.md")


@pytest.mark.parametrize(
    "filename",
    (OFFICIAL_FILENAME, "crossframe-ultra-完整文章.MD", OFFICIAL_FILENAME + "."),
)
def test_assembler_never_publishes_the_official_filename_before_u12(
    article, tmp_path: Path, filename: str
) -> None:
    plan, packets = _valid_case()
    official = tmp_path / "delivery" / filename
    with pytest.raises(ValueError, match="official|U12|正式"):
        article.assemble_article(plan, packets, official)
    assert not official.exists()


def test_article_has_no_word_or_character_cap(article, tmp_path: Path) -> None:
    plan, packets = _valid_case()
    long_body = "这是一项有来源且会影响排序的完整说明。" * 30_000
    _replace_prose(packets[0], f"## {EXPECTED_SECTIONS[0]}\n\n{long_body}")
    result = article.assemble_article(plan, packets, tmp_path / "long.partial.md")
    assert long_body in result.article_text
    assert len(result.article_text) > 300_000


def test_article_schemas_do_not_define_a_prose_length_ceiling() -> None:
    schema_names = (
        "ultra-output-plan.schema.json",
        "ultra-semantic-coverage.schema.json",
        "ultra-article-review.schema.json",
    )
    forbidden_keys = {
        "maxwords",
        "maxwordcount",
        "maxcharacters",
        "maxcharactercount",
        "articlemaxlength",
        "prosemaxlength",
    }

    def walk(value: object):
        if isinstance(value, dict):
            for key, child in value.items():
                yield str(key).replace("_", "").casefold()
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    for name in schema_names:
        document = json.loads((ULTRA_ROOT / "schemas" / name).read_text("utf-8"))
        assert forbidden_keys.isdisjoint(walk(document)), name
