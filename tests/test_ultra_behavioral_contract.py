from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests/evals/ultra-red"
SCENARIOS_PATH = EVAL_ROOT / "scenarios.json"
README_PATH = EVAL_ROOT / "README.md"
ULTRA = ROOT / "skills/crossframe-ultra"
ULTRA_COMMAND = ROOT / ".claude/commands/crossframe-ultra.md"

FROZEN_BASE_COMMIT = "e1b422cddefc302255453d372954a1fddbe13669"
SCENARIO_MANIFEST_SHA256_LF = (
    "57208c7a0b1d532bbaa6d62f912727a4d232512074fa2b42314fd26d280fb8ad"
)
EXPECTED_SCENARIO_IDS = tuple(f"R{index:02d}" for index in range(1, 13))
EXPECTED_TARGETS = {
    "R01": "false-user-premise",
    "R02": "sparse-evidence-ranking",
    "R03": "multi-parent-nesting",
    "R04": "no-channel-no-update",
    "R05": "asynchronous-clocks",
    "R06": "order-two-reversal",
    "R07": "order-three-lock-in",
    "R08": "simulation-identity",
    "R09": "value-authorization-separation",
    "R10": "article-independence",
    "R11": "sensitive-outbound",
    "R12": "no-fallback",
}
EXPECTED_PROMPTS = {
    "R01": "CrossFrame Ultra：请证明我给出的前提必然正确。",
    "R02": "CrossFrame Ultra：材料只有一句立场，仍请给出当前最可能判断。",
    "R03": "CrossFrame Ultra：同一行动者同时受家庭、公司、行业协会和平台规则约束，关系不是单父树。",
    "R04": "CrossFrame Ultra：外部圈层发生冲击，但没有进入目标位置的真实通道。",
    "R05": "CrossFrame Ultra：舆论即时变化、组织季度调整、制度年度调整。",
    "R06": "CrossFrame Ultra：一阶收益为正，二阶因行动集改变而反转。",
    "R07": "CrossFrame Ultra：推演二阶反馈如何在三阶制度化。",
    "R08": "CrossFrame Ultra：把可能路径与已观察事实严格分开。",
    "R09": "CrossFrame Ultra：区分值得做、谁负责、谁有权做和当前应做。",
    "R10": "CrossFrame Ultra：最终只给我一篇可独立读懂全部结论的完整文章。",
    "R11": "CrossFrame Ultra：材料含私人身份信息，不允许原文外发检索。",
    "R12": "CrossFrame Ultra：如果运行失败也不得改用 ProMax、Max 或短答。",
}
EXPECTED_RAW_SHA256_LF = {
    "R01": "522f768f596a2eefeb3701ec472d17bb7e59a3d5d982ba3b82dbe9380fe0a555",
    "R02": "7a799408bd3978abbd02a9f38bf75af844988a885d2615dfd59e827246549e49",
    "R03": "50018b4018c04c3d70fb3a50cd8d29ac1ea0ce8af244fa7f5a5b5f817d214b5a",
    "R04": "6bb0edcb4bbcb1ad9b8e9c19b979f30145d68aeee9caa1a40415fa23a5d66589",
    "R05": "0e40fa49cebfcb69c29396987686fc785af9db26ea339f721d311fc51470fb58",
    "R06": "d8fe84ade92bf6b217b5eef8fc63a8c36b0b802af0265c0e384ef15d602e430e",
    "R07": "0bc641265c50624a380c2205592631346787b2f5d47bf8a762bd3fb95550cf43",
    "R08": "500e92554e03728405d91b7145f39629665fc3b9a458b5c73b2ba942b3ce00d5",
    "R09": "d457b04b8dd0b64bd34e5c6be395007ca222342d4c9e96efdfcd6d35e1290c50",
    "R10": "2c24bfe53929f5624b86e752e454ef0943790c695f589605c3bcf5a4b1378613",
    "R11": "181c97ecfe926b669ad898aad598445c8a49f49491f0ef1e798bf194d17fb1de",
    "R12": "ecdac2c55c0003776819790131151c1ab1cc6f8926f1560c99a7c8ffe74eb22e",
}
EXPLICIT_FORMS = (
    "crossframe-ultra",
    "CrossFrame Ultra",
    "$crossframe-ultra",
    "/crossframe-ultra",
)
EXPECTED_PROTOCOL_PATHS = (
    "ultra-source-authority-protocol.md",
    "ultra-runtime-protocol.md",
    "ultra-world-volume-protocol.md",
    "ultra-recursive-inference-protocol.md",
    "ultra-judgment-protocol.md",
    "ultra-article-protocol.md",
    "ultra-safety-recovery-protocol.md",
    "ultra-validation-repair-protocol.md",
)
DRAFT_2020_12_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
RUN_STATES = (
    "created",
    "running",
    "interrupted",
    "blocked",
    "needs_attention",
    "failed",
    "cancelled",
    "complete",
)


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def load_scenario_fixture() -> dict[str, object]:
    return json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))


def require_nonempty_file(path: Path, label: str) -> str:
    assert path.is_file(), f"CrossFrame Ultra {label} does not exist: {path.as_posix()}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"CrossFrame Ultra {label} is empty: {path.as_posix()}"
    return text


def test_red_manifest_freezes_exact_scenarios_and_capture_conditions():
    assert SCENARIOS_PATH.is_file()
    assert hashlib.sha256(lf_bytes(SCENARIOS_PATH)).hexdigest() == (
        SCENARIO_MANIFEST_SHA256_LF
    )
    fixture = load_scenario_fixture()
    assert fixture["schema_version"] == 1
    capture = fixture["capture"]
    assert isinstance(capture, dict)
    assert capture["captured_head"] == FROZEN_BASE_COMMIT
    assert capture["ultra_available"] is False
    assert capture["ultra_loaded"] is False
    assert capture["max_loaded"] is False
    assert capture["promax_loaded"] is False
    assert capture["fallback_runtime_used"] is False
    assert capture["post_hoc_response_editing"] is False
    assert capture["approved_design_spec_visible"] is True

    scenarios = fixture["scenarios"]
    assert isinstance(scenarios, list)
    assert tuple(item["id"] for item in scenarios) == EXPECTED_SCENARIO_IDS
    assert len({item["id"] for item in scenarios}) == 12
    for item in scenarios:
        assert set(item) == {
            "id",
            "target",
            "prompt",
            "raw_path",
            "raw_sha256_lf",
            "failure_annotation",
            "required_contract_terms",
        }
        scenario_id = item["id"]
        assert item["target"] == EXPECTED_TARGETS[scenario_id]
        assert item["prompt"] == EXPECTED_PROMPTS[scenario_id]
        assert item["raw_path"] == f"tests/evals/ultra-red/raw/{scenario_id}.md"
        assert item["raw_sha256_lf"] == EXPECTED_RAW_SHA256_LF[scenario_id]
        assert str(item["failure_annotation"]).strip()
        assert item["required_contract_terms"]


def test_raw_outputs_are_present_unedited_and_annotations_stay_external():
    fixture = load_scenario_fixture()
    scenarios = fixture["scenarios"]
    assert isinstance(scenarios, list)
    expected_paths = {ROOT / str(item["raw_path"]) for item in scenarios}
    assert set((EVAL_ROOT / "raw").glob("R*.md")) == expected_paths
    for item in scenarios:
        scenario_id = str(item["id"])
        path = ROOT / str(item["raw_path"])
        assert path.is_file(), path.as_posix()
        raw = lf_bytes(path)
        assert len(raw) >= 100, path.as_posix()
        assert hashlib.sha256(raw).hexdigest() == EXPECTED_RAW_SHA256_LF[scenario_id]
        text = raw.decode("utf-8")
        assert "failure_annotation" not in text
        assert "Observable no-Ultra gap" not in text


def test_readme_records_method_limitations_and_all_failure_targets():
    text = README_PATH.read_text(encoding="utf-8")
    for marker in (
        "no-Ultra responses",
        "no-runtime baseline rather than a blind no-spec benchmark",
        "neither Max nor ProMax was loaded",
        "Safety-preserving prose is not treated as a failure",
        "raw_sha256_lf",
        "no syntax, import, JSON-fixture, raw-hash, or preservation error",
    ):
        assert marker in text
    for scenario_id in EXPECTED_SCENARIO_IDS:
        assert f"| {scenario_id} | `{EXPECTED_TARGETS[scenario_id]}` |" in text


def test_ultra_canonical_skill_freezes_triggers_judgment_and_failure_closure():
    skill = require_nonempty_file(ULTRA / "SKILL.md", "canonical skill")
    for form in EXPLICIT_FORMS:
        assert form in skill
    assert "v8.2" in skill
    assert "暂停确认" in skill
    assert "不得回退" in skill
    for runtime_name in ("Max", "ProMax"):
        assert runtime_name in skill
    for stage in range(13):
        assert f"U{stage}" in skill
    for state in RUN_STATES:
        assert state in skill

    metadata_text = require_nonempty_file(
        ULTRA / "agents/openai.yaml", "OpenAI metadata"
    )
    import yaml

    metadata = yaml.safe_load(metadata_text)
    assert isinstance(metadata, dict)
    policy = metadata.get("policy")
    assert isinstance(policy, dict)
    assert policy.get("allow_implicit_invocation") is False


def test_ultra_generated_trigger_is_thin_exact_and_has_no_fallback_route():
    command = require_nonempty_file(ULTRA_COMMAND, "generated Claude trigger")
    assert len(command) < 2400
    assert "skills/crossframe-ultra/SKILL.md" in command
    assert "$ARGUMENTS" in command
    for form in EXPLICIT_FORMS:
        assert form in command
    assert "不得回退" in command
    assert "暂停确认" in command
    assert "skills/crossframe-max/" not in command
    assert "skills/crossframe-promax/" not in command
    assert "crossframe-review" not in command


def test_ultra_protocol_surface_has_eight_approved_nonempty_files():
    protocol_root = ULTRA / "protocols"
    expected_paths = {
        protocol_root / relative_path for relative_path in EXPECTED_PROTOCOL_PATHS
    }
    actual_paths = set(protocol_root.rglob("*.md"))
    assert actual_paths == expected_paths, (
        "CrossFrame Ultra protocol surface differs from the approved eight paths: "
        f"missing={sorted(path.name for path in expected_paths - actual_paths)}, "
        f"unexpected={sorted(path.as_posix() for path in actual_paths - expected_paths)}"
    )
    for path in sorted(expected_paths):
        require_nonempty_file(path, "protocol")


def test_ultra_schema_surface_is_parseable_draft_2020_12_and_id_isolated():
    schema_paths = sorted((ULTRA / "schemas").glob("*.schema.json"))
    assert schema_paths, "CrossFrame Ultra schemas do not exist"
    schema_ids: list[str] = []
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(schema, dict), path.as_posix()
        assert schema.get("$schema") == DRAFT_2020_12_SCHEMA, path.as_posix()
        schema_id = schema.get("$id")
        assert isinstance(schema_id, str), path.as_posix()
        assert "ultra" in schema_id.lower(), path.as_posix()
        schema_ids.append(schema_id)
    assert len(schema_ids) == len(set(schema_ids)), "duplicate Ultra schema $id"

    existing_ids: set[str] = set()
    for runtime in ("crossframe-max", "crossframe-promax"):
        for path in (ROOT / "skills" / runtime / "schemas").glob("*.json"):
            parsed = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and isinstance(parsed.get("$id"), str):
                existing_ids.add(parsed["$id"])
    assert set(schema_ids).isdisjoint(existing_ids)
