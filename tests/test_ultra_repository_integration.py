from __future__ import annotations

import json
import re
from pathlib import Path

from tests.pytest_import_guard import pytest

from scripts import check_crossframe_skill_integrity as integrity
from scripts.sync_skill_mirrors import CROSSFRAME_SKILLS, same_tree


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills/crossframe-ultra"
ULTRA_MIRROR = ROOT / ".claude/skills/crossframe-ultra"
ULTRA_COMMAND = ROOT / ".claude/commands/crossframe-ultra.md"

EXPECTED_SKILLS = (
    "crossframe",
    "crossframe-suite",
    "crossframe-essay",
    "crossframe-critical",
    "crossframe-review",
    "crossframe-dialogue",
    "crossframe-casebook",
    "crossframe-history",
    "crossframe-inquiry",
    "crossframe-max",
    "crossframe-promax",
    "crossframe-public",
    "crossframe-org",
    "crossframe-teach",
    "crossframe-debate",
    "crossframe-notebook",
    "crossframe-ultra",
)
EXACT_ULTRA_FORMS = (
    "crossframe-ultra",
    "CrossFrame Ultra",
    "$crossframe-ultra",
    "/crossframe-ultra",
)
NON_CURRENT_LISTS = (
    "LEGACY_CROSSFRAME_SKILLS",
    "CLAIM_LEDGER_DELTA_SKILLS",
    "SIBLING_CLAIM_BRIDGE_SKILLS",
    "SIBLING_AGENT_PROMPT_SKILLS",
)
ROUTING_ADAPTERS = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "CONVENTIONS.md",
    "INTERFACES.md",
    ".github/copilot-instructions.md",
    "llms.txt",
    "README.md",
)
ROUTING_BEGIN = "<!-- CROSSFRAME-ULTRA-ROUTING-BEGIN -->"
ROUTING_END = "<!-- CROSSFRAME-ULTRA-ROUTING-END -->"
ROUTING_OUTCOMES = {
    "exact Ultra-only request routes Ultra": (
        "单独精确点名 Ultra 时直接进入 Ultra",
        "An exact Ultra-only request routes to Ultra",
    ),
    "generic maximum/deep/full remains Max": (
        "泛化的最大/深度/完整请求仍由 Max",
        "generic maximum/deep/full requests remain Max",
    ),
    "ProMax-over-Max remains unchanged": (
        "Max 与 ProMax 同时出现仍由 ProMax 优先",
        "ProMax-over-Max remains unchanged",
    ),
    "explicit comparison runs independently": (
        "Ultra 与其它 runtime 同时点名且显式要求比较时分别独立运行",
        "when Ultra and another runtime are both named, an explicit comparison runs each independently",
    ),
    "ambiguous multi-runtime invocation pauses": (
        "同时点名但未要求比较时暂停确认 runtime",
        "when both are named without an explicit comparison, pause for runtime choice",
    ),
    "suite cannot route to Ultra implicitly": (
        "suite 未精确点名 Ultra 时绝不进入 Ultra",
        "suite without an exact Ultra name never routes to Ultra",
    ),
    "Ultra failure cannot fall back": (
        "Ultra 失败不得回退",
        "Ultra failure never falls back",
    ),
}


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _ultra_routing_block(relative: str) -> str:
    text = _text(relative)
    assert text.count(ROUTING_BEGIN) == 1, relative
    assert text.count(ROUTING_END) == 1, relative
    start = text.index(ROUTING_BEGIN) + len(ROUTING_BEGIN)
    end = text.index(ROUTING_END, start)
    return text[start:end]


def _workflow_job_blocks(workflow: str) -> dict[str, str]:
    match = re.search(r"(?m)^jobs:\s*\n", workflow)
    assert match is not None
    payload = workflow[match.end() :]
    headers = list(re.finditer(r"(?m)^  ([a-z0-9][a-z0-9-]*):\s*\n", payload))
    assert headers
    return {
        header.group(1): payload[
            header.start() : headers[index + 1].start()
            if index + 1 < len(headers)
            else len(payload)
        ]
        for index, header in enumerate(headers)
    }


def test_inventory_contains_exactly_seventeen_unique_current_skills() -> None:
    assert tuple(CROSSFRAME_SKILLS) == EXPECTED_SKILLS
    assert len(CROSSFRAME_SKILLS) == 17
    assert len(set(CROSSFRAME_SKILLS)) == 17
    assert set(integrity.CURRENT_CROSSFRAME_SKILLS) == set(EXPECTED_SKILLS)
    assert len(set(integrity.CURRENT_CROSSFRAME_SKILLS)) == 17
    for list_name in NON_CURRENT_LISTS:
        assert "crossframe-ultra" not in getattr(integrity, list_name), list_name


def test_ultra_mirror_is_generated_from_canonical() -> None:
    assert same_tree(ULTRA, ULTRA_MIRROR)


def test_integrity_exposes_and_enforces_the_ultra_contract() -> None:
    assert integrity.ULTRA_EXACT_TRIGGER_NAMES == EXACT_ULTRA_FORMS
    integrity.check_crossframe_ultra_skill(ROOT / "skills", "test")


def test_no_promax_import_gate_ignores_comparison_prose_but_rejects_python(
    tmp_path: Path,
) -> None:
    ultra = tmp_path / "crossframe-ultra"
    (ultra / "references").mkdir(parents=True)
    (ultra / "references/comparison.md").write_text(
        "ProMax remains v8.0 for comparison.\n",
        encoding="utf-8",
    )
    integrity.check_crossframe_ultra_no_promax_imports(ultra, "test")

    scripts = ultra / "scripts"
    scripts.mkdir()
    (scripts / "invalid.py").write_text(
        "from crossframe_promax import runtime\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="ProMax Python import"):
        integrity.check_crossframe_ultra_no_promax_imports(ultra, "test")


@pytest.mark.parametrize("relative", ROUTING_ADAPTERS)
def test_allowed_adapter_has_complete_ultra_routing_policy(relative: str) -> None:
    block = _ultra_routing_block(relative)
    assert "skills/crossframe-ultra/SKILL.md" in block
    assert "v8.2" in block
    for trigger in EXACT_ULTRA_FORMS:
        assert trigger in block, (relative, trigger)
    for outcome, aliases in ROUTING_OUTCOMES.items():
        assert any(alias in block for alias in aliases), (relative, outcome)


def test_ultra_claude_command_is_a_thin_fixed_runtime_adapter() -> None:
    text = ULTRA_COMMAND.read_text(encoding="utf-8")
    assert len(text) < 2400
    assert "skills/crossframe-ultra/SKILL.md" in text
    assert "$ARGUMENTS" in text
    assert "v8.2" in text
    assert "暂停确认" in text
    assert "不得回退" in text
    assert "An exact Ultra-only request starts Ultra directly" in text
    for trigger in EXACT_ULTRA_FORMS:
        assert trigger in text
    for forbidden in (
        "skills/crossframe-max",
        "skills/crossframe-promax",
        "crossframe-review",
        "protocols/",
    ):
        assert forbidden not in text


def test_public_docs_state_ultra_runtime_and_release_boundaries() -> None:
    readme = _text("README.md")
    site = _text("site/index.html")
    combined = readme + "\n" + site
    for marker in (
        "17 个 `crossframe-*` skills",
        "E:\\世界模型\\output\\crossframe-ultra",
        "E:\\世界模型\\output\\crossframe-ultra-tests",
        "delivery\\CrossFrame-Ultra-完整文章.md",
        "Ultra 不自行演化理论",
        "预测机制验证不等于前瞻准确率验证",
        "ProMax 保持 v8.0",
        ".\\scripts\\install-codex.ps1 -Repo (Resolve-Path .).Path",
        'bash scripts/install-codex.sh --repo "$(pwd -P)"',
    ):
        assert marker in combined, marker
    assert "仓库共 <b>17 个 crossframe-* skills</b>" in site
    assert "CrossFrame Skill Suite · 17 skills · explicit-only" in site
    assert '<span class="fam-name">crossframe-ultra</span>' in site


def test_ultra_ci_job_is_isolated_and_preserves_frozen_runtime_jobs() -> None:
    workflow = _text(".github/workflows/verify.yml").replace("\r\n", "\n")
    jobs = _workflow_job_blocks(workflow)
    manifest = json.loads(
        _text("tests/fixtures/ultra-preservation.json")
    )["workflow_jobs"]
    for frozen_job in ("max-contracts-and-artifacts", "promax-contracts-and-artifacts"):
        assert jobs[frozen_job] == manifest[frozen_job]["raw_text"]

    ultra_job = jobs["ultra-contracts-and-artifacts"]
    for marker in (
        "name: ultra-contracts-and-artifacts",
        "runs-on: windows-latest",
        "shell: bash",
        "Prepare fixed Windows roots",
        "subst.exe E:",
        "python -m pip install jsonschema pytest PyYAML",
        "python -I -S -B scripts/check_crossframe_ultra_v82_source.py --repo .",
        "python -B scripts/check_crossframe_ultra_v82_knowledge.py --repo .",
        "for schema in skills/crossframe-ultra/schemas/*.json; do",
        'python -m json.tool "$schema" > /dev/null',
        "python -B -m pytest -q tests/test_ultra_*.py",
    ):
        assert marker in ultra_job
