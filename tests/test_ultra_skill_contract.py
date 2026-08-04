from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills/crossframe-ultra"
SKILL_PATH = ULTRA / "SKILL.md"
OPENAI_PATH = ULTRA / "agents/openai.yaml"

EXACT_ULTRA_FORMS = (
    "crossframe-ultra",
    "CrossFrame Ultra",
    "$crossframe-ultra",
    "/crossframe-ultra",
)
NEAR_MISSES = (
    "最大化",
    "最完整",
    "Ultra 分析",
    "maximum",
    "full",
)
FORBIDDEN_CLI_OPTIONS = (
    "--run-dir",
    "--authoring-dir",
    "--output-root",
    "--destination",
    "--fallback",
)
CONCEPT_DISPOSITIONS = (
    "applied",
    "tested-rejected",
    "not-applicable",
    "unknown-pending",
)
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
FINAL_CHAT_FIELDS = (
    "run_status",
    "center_judgment_summary",
    "key_reversal_conditions",
    "article_path",
    "run_path",
    "continuation_entry",
)


def _required_text(path: Path) -> str:
    assert path.is_file(), f"required Task 14 asset is missing: {path.as_posix()}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"required Task 14 asset is empty: {path.as_posix()}"
    return text


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    parts = text.split("---", 2)
    assert len(parts) == 3 and not parts[0].strip(), "SKILL.md needs YAML frontmatter"
    metadata = yaml.safe_load(parts[1])
    assert isinstance(metadata, dict)
    return metadata, parts[2]


def _marked_block(text: str, name: str) -> str:
    begin = f"<!-- {name}-BEGIN -->"
    end = f"<!-- {name}-END -->"
    assert text.count(begin) == 1, f"missing or duplicate {begin}"
    assert text.count(end) == 1, f"missing or duplicate {end}"
    return text.split(begin, 1)[1].split(end, 1)[0]


def _marked_code_items(text: str, name: str) -> tuple[str, ...]:
    block = _marked_block(text, name)
    return tuple(re.findall(r"^- `([^`]+)`\s*$", block, flags=re.MULTILINE))


def test_skill_frontmatter_and_openai_metadata_expose_the_exact_interface() -> None:
    skill = _required_text(SKILL_PATH)
    metadata, _body = _frontmatter(skill)
    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == "crossframe-ultra"
    description = metadata["description"]
    assert isinstance(description, str) and description.startswith("Use only when")
    assert all(form in description for form in EXACT_ULTRA_FORMS)
    assert _marked_code_items(skill, "ULTRA-ACCEPTED-FORMS") == EXACT_ULTRA_FORMS

    openai = yaml.safe_load(_required_text(OPENAI_PATH))
    assert openai == {
        "interface": {
            "display_name": "CrossFrame Ultra",
            "short_description": (
                "Explicit-only v8.2 world-volume inference with hard judgments."
            ),
            "default_prompt": (
                "Use $crossframe-ultra to run the complete v8.2 world-volume "
                "workflow and publish one independently readable Chinese article."
            ),
        },
        "policy": {"allow_implicit_invocation": False},
    }


def test_activation_contract_rejects_near_misses_and_adjacent_runtime_routes() -> None:
    skill = _required_text(SKILL_PATH)
    assert _marked_code_items(skill, "ULTRA-NEAR-MISSES") == NEAR_MISSES
    for marker in (
        "ULTRA-EXPLICIT-ONLY",
        "ULTRA-NO-SUITE-UPGRADE",
        "ULTRA-NO-REVIEW-CHAIN",
        "ULTRA-NO-FALLBACK",
        "ULTRA-MULTI-RUNTIME-CONFIRM",
    ):
        assert marker in skill
    assert "crossframe-suite" in skill
    assert "crossframe-review" in skill
    assert "Max" in skill and "ProMax" in skill
    assert "暂停确认" in skill


def test_multi_runtime_routing_separates_comparison_from_choice_confirmation() -> None:
    skill = _required_text(SKILL_PATH)
    marker = "<!-- ULTRA-MULTI-RUNTIME-CONFIRM -->"
    assert skill.count(marker) == 1
    contract = skill.split(marker, 1)[1].split("\n\n", 1)[0]
    assert "若用户明确要求比较 Ultra 与另一个 runtime" in contract
    assert "先分别独立运行 Ultra 和被比较 runtime，再比较各自结果" in contract
    assert "同时明确点名多个 runtime 但未提出比较" in contract
    assert "暂停确认本次选择哪个 runtime" in contract
    assert "两种分支互斥" in contract


def test_controller_is_v82_only_fixed_root_and_has_no_early_final_escape() -> None:
    skill = _required_text(SKILL_PATH)
    for marker in (
        "ULTRA-PROMOTED-V82-ONLY",
        "ULTRA-NO-THEORY-SELF-AMENDMENT",
        "ULTRA-NO-HIDDEN-THEORY",
        "ULTRA-NO-EARLY-FINAL",
        "ULTRA-FRAMEWORK-GAP-NEXT-RUN-ONLY",
        "ULTRA-FRESH-VALIDATION-REQUIRED",
    ):
        assert marker in skill
    assert "v8.2" in skill and "v8.0" in skill
    assert r"E:\世界模型\output\crossframe-ultra" in skill
    assert r"E:\世界模型\output\crossframe-ultra-tests" in skill
    assert "delivery\\CrossFrame-Ultra-完整文章.md" in skill
    assert "article_path" in skill and "run_path" in skill
    assert "绝对路径" in skill

    assert _marked_code_items(skill, "ULTRA-CONCEPT-DISPOSITIONS") == (
        CONCEPT_DISPOSITIONS
    )
    assert _marked_code_items(skill, "ULTRA-RUN-STATES") == RUN_STATES
    assert _marked_code_items(skill, "ULTRA-FINAL-CHAT-FIELDS") == FINAL_CHAT_FIELDS

    phase_block = _marked_block(skill, "ULTRA-PHASES")
    phases = tuple(re.findall(r"^- `(U\d+)`\b", phase_block, flags=re.MULTILINE))
    assert phases == tuple(f"U{index}" for index in range(13))


def test_controller_forbids_arbitrary_paths_and_requires_exact_runtime_cli() -> None:
    skill = _required_text(SKILL_PATH)
    assert "ULTRA-NO-ARBITRARY-PATH-FLAGS" in skill
    for option in FORBIDDEN_CLI_OPTIONS:
        assert option in skill
    assert "scripts/crossframe_ultra_runtime.py" in skill
    for command in (
        "start",
        "prepare",
        "checkpoint",
        "materialize",
        "validate",
        "repair-plan",
        "resume",
        "fork",
        "cancel",
        "rebuild-index",
    ):
        assert f"`{command}`" in skill
