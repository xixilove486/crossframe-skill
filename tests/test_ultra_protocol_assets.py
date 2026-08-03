from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills/crossframe-ultra"
PROTOCOL_ROOT = ULTRA / "protocols"
ROUTING_PATH = ULTRA / "references/runtime-routing-map.md"
RETRIEVAL_PATH = ULTRA / "references/retrieval-policy.md"
SMOKE_PATH = ULTRA / "evals/crossframe-ultra-smoke-tests.md"

PROTOCOL_NAMES = (
    "ultra-source-authority-protocol.md",
    "ultra-runtime-protocol.md",
    "ultra-world-volume-protocol.md",
    "ultra-recursive-inference-protocol.md",
    "ultra-judgment-protocol.md",
    "ultra-article-protocol.md",
    "ultra-safety-recovery-protocol.md",
    "ultra-validation-repair-protocol.md",
)
REQUIRED_PROTOCOL_HEADINGS = (
    "Inputs",
    "Outputs",
    "Dependencies",
    "Stop/Failure",
    "Corresponding validator",
)
EXPECTED_VALIDATOR_MARKERS = {
    "ultra-source-authority-protocol.md": (
        "check_crossframe_ultra_v82_source.py",
        "check_crossframe_ultra_v82_knowledge.py",
    ),
    "ultra-runtime-protocol.md": (
        "crossframe_ultra_runtime.py",
        "check_crossframe_ultra_artifacts.py",
    ),
    "ultra-world-volume-protocol.md": (
        "validate_world_volume",
        "validate_transformations",
        "validate_concept_closure",
    ),
    "ultra-recursive-inference-protocol.md": (
        "ultra-recursive-state.schema.json",
        "ultra-recursive-lineage.schema.json",
        "ultra-order-evaluation.schema.json",
        "ultra-red-team-report.schema.json",
    ),
    "ultra-judgment-protocol.md": (
        "validate_verdict_bundle",
        "ultra-action-ranking.schema.json",
        "validate_forecast",
    ),
    "ultra-article-protocol.md": (
        "validate_output_plan_artifact",
        "validate_semantic_coverage",
        "review_article_in_clean_room",
    ),
    "ultra-safety-recovery-protocol.md": (
        "check_crossframe_ultra_artifacts.py",
        "ultra-recovery-checkpoint.schema.json",
    ),
    "ultra-validation-repair-protocol.md": (
        "check_crossframe_ultra_artifacts.py",
        "build_crossframe_ultra_repair_plan.py",
        "ultra-repair-plan.schema.json",
    ),
}
CLI_SIGNATURES = (
    "start          --repo PATH --mode production|test (--request-file PATH | --request-stdin)",
    "prepare        --repo PATH --mode production|test --run-id RUN_ID",
    "checkpoint     --repo PATH --mode production|test --run-id RUN_ID --phase U0..U11",
    "materialize    --repo PATH --mode production|test --run-id RUN_ID",
    "validate       --repo PATH --mode production|test --run-id RUN_ID [--json]",
    "repair-plan    --repo PATH --mode production|test --run-id RUN_ID",
    "resume         --repo PATH --mode production|test --run-id RUN_ID",
    "fork           --repo PATH --mode production|test --run-id RUN_ID --reason TEXT",
    "cancel         --repo PATH --mode production|test --run-id RUN_ID",
    "rebuild-index  --repo PATH --mode production|test",
)
FORBIDDEN_CLI_OPTIONS = (
    "--run-dir",
    "--authoring-dir",
    "--output-root",
    "--destination",
    "--fallback",
)
AUTHORING_SLOTS = (
    "work/authoring/U01-read-events.jsonl",
    "work/authoring/U02-retrieval-ledger.json",
    "work/authoring/U03-evidence-ledger.json",
    "work/authoring/U04-world-volume.json",
    "work/authoring/U05-transformation-ledger.json",
    "work/authoring/U05-concept-disposition.json",
    "work/authoring/U06-claim-mechanism-graph.json",
    "work/authoring/U07-recursive-states/<node-id>.json",
    "work/authoring/U07-recursive-lineage.json",
    "work/authoring/U08-order-evaluation.json",
    "work/authoring/U08-red-team-report.json",
    "work/authoring/U09-verdict.json",
    "work/authoring/U09-action-ranking.json",
    "work/authoring/U09-forecast-ledger.json",
    "work/authoring/U10-framework-gap-ledger.json",
    "work/authoring/U10-output-plan.json",
    "work/authoring/U11-semantic-coverage.json",
    "work/authoring/article/packets/<packet-id>.md",
    "work/authoring/U11-article-review.json",
    "work/authoring/完整推演档案.md",
)
TEMPLATE_NAMES = {
    "ultra-output-plan-output.md",
    "ultra-article-output.md",
    "ultra-semantic-coverage-output.md",
    "ultra-article-review-output.md",
    "ultra-run-status-output.md",
    "ultra-world-volume-output.md",
    "ultra-transformation-ledger-output.md",
    "ultra-concept-disposition-output.md",
    "ultra-claim-mechanism-output.md",
    "ultra-recursive-state-output.md",
    "ultra-recursive-lineage-output.md",
    "ultra-order-evaluation-output.md",
    "ultra-retrieval-output.md",
    "ultra-red-team-output.md",
    "ultra-verdict-output.md",
    "ultra-action-ranking-output.md",
    "ultra-forecast-output.md",
    "ultra-framework-gap-output.md",
    "ultra-dossier-output.md",
    "ultra-artifact-index-output.md",
    "ultra-validator-report-output.md",
    "ultra-repair-plan-output.md",
}
RETRIEVAL_QUALIFICATION_STATUSES = ("required", "not-applicable")
RETRIEVAL_TRIGGER_KINDS = (
    "real-world",
    "time-sensitive",
    "legal",
    "medical",
    "financial",
    "political",
    "product",
    "policy",
    "institutional",
    "current-fact",
)
RETRIEVAL_DIRECTIONS = (
    "support",
    "counterexample",
    "affected-position",
    "source-lineage",
    "calibration",
)
SOURCE_PROVENANCE_FIELDS = (
    "source_id",
    "url",
    "event_date",
    "publication_date",
    "interest",
    "upstream_lineage",
    "supported_claim",
    "cannot_prove",
)


def _required_text(path: Path) -> str:
    assert path.is_file(), f"required Task 14 asset is missing: {path.as_posix()}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"required Task 14 asset is empty: {path.as_posix()}"
    return text


def _marked_block(text: str, name: str) -> str:
    begin = f"<!-- {name}-BEGIN -->"
    end = f"<!-- {name}-END -->"
    assert text.count(begin) == 1, f"missing or duplicate {begin}"
    assert text.count(end) == 1, f"missing or duplicate {end}"
    return text.split(begin, 1)[1].split(end, 1)[0]


def _marked_code_items(text: str, name: str) -> tuple[str, ...]:
    return tuple(
        re.findall(
            r"^- `([^`]+)`\s*$",
            _marked_block(text, name),
            flags=re.MULTILINE,
        )
    )


def test_protocol_surface_is_exact_thin_and_structurally_complete() -> None:
    expected = {PROTOCOL_ROOT / name for name in PROTOCOL_NAMES}
    actual = set(PROTOCOL_ROOT.glob("*.md")) if PROTOCOL_ROOT.is_dir() else set()
    assert actual == expected
    for path in sorted(expected):
        text = _required_text(path)
        assert len(text.encode("utf-8")) < 12_000, f"protocol is not thin: {path.name}"
        for heading in REQUIRED_PROTOCOL_HEADINGS:
            assert len(re.findall(rf"^## {re.escape(heading)}$", text, re.MULTILINE)) == 1
        for validator in EXPECTED_VALIDATOR_MARKERS[path.name]:
            assert validator in text, f"{path.name} omits {validator}"
        assert "source-paragraph:" not in text
        assert not re.search(r"\bV82-[PT]\d+\b", text)
        assert "house policy" not in text.casefold()
        assert "house-policy" not in text.casefold()
        assert "v8.3" not in text.casefold()


def test_responsibility_protocols_close_the_specific_judgment_article_and_root_gates() -> None:
    judgment = _required_text(PROTOCOL_ROOT / "ultra-judgment-protocol.md")
    article = _required_text(PROTOCOL_ROOT / "ultra-article-protocol.md")
    safety = _required_text(PROTOCOL_ROOT / "ultra-safety-recovery-protocol.md")
    validation = _required_text(PROTOCOL_ROOT / "ultra-validation-repair-protocol.md")
    assert "ULTRA-LOW-EVIDENCE-RANKING" in judgment
    assert "降低置信度" in judgment and "当前最佳排序" in judgment
    assert "ULTRA-NO-WORD-CAP" in article
    assert "ULTRA-BLIND-RECOVERY-GATE" in article
    assert "ULTRA-FIXED-ROOT-FAILS-CLOSED" in safety
    assert "ULTRA-FRESH-CONTEXT-VALIDATION" in validation
    assert "ULTRA-BOUNDED-LOCAL-REPAIR" in validation


def test_runtime_routing_map_freezes_exact_cli_authoring_slots_and_template_refs() -> None:
    routing = _required_text(ROUTING_PATH)
    command_lines = tuple(
        line.rstrip()
        for line in _marked_block(routing, "ULTRA-CLI").splitlines()
        if line.strip() and not line.strip().startswith("```")
    )
    assert command_lines == CLI_SIGNATURES
    for line in command_lines:
        assert not any(option in line for option in FORBIDDEN_CLI_OPTIONS)
    assert _marked_code_items(routing, "ULTRA-FORBIDDEN-CLI-OPTIONS") == (
        FORBIDDEN_CLI_OPTIONS
    )
    assert _marked_code_items(routing, "ULTRA-AUTHORING-SLOTS") == AUTHORING_SLOTS

    referenced_templates = set(re.findall(r"templates/([^`\s|]+\.md)", routing))
    assert referenced_templates == TEMPLATE_NAMES


def test_retrieval_policy_matches_the_existing_u2_status_privacy_and_provenance_contract() -> None:
    policy = _required_text(RETRIEVAL_PATH)
    assert _marked_code_items(policy, "U2-QUALIFICATION-STATUSES") == (
        RETRIEVAL_QUALIFICATION_STATUSES
    )
    assert _marked_code_items(policy, "U2-TRIGGER-KINDS") == RETRIEVAL_TRIGGER_KINDS
    assert _marked_code_items(policy, "U2-RETRIEVAL-DIRECTIONS") == RETRIEVAL_DIRECTIONS
    assert _marked_code_items(policy, "U2-SOURCE-PROVENANCE-FIELDS") == (
        SOURCE_PROVENANCE_FIELDS
    )
    for marker in (
        "public / internal / private / restricted",
        "allowed / deidentified-only / denied",
        "verified-current-user",
        "redact_query",
        "hostile_instruction_detected",
        "untrusted",
        "required-complete",
        "required-blocked",
    ):
        assert marker in policy


def test_smoke_matrix_covers_activation_and_all_hard_failure_boundaries() -> None:
    smoke = _required_text(SMOKE_PATH)
    for form in (
        "crossframe-ultra",
        "CrossFrame Ultra",
        "$crossframe-ultra",
        "/crossframe-ultra",
    ):
        assert f"`{form}`" in smoke
    for scenario in tuple(f"S{index:02d}" for index in range(1, 13)):
        assert f"| {scenario} |" in smoke
    for boundary in (
        "near-miss",
        "suite-auto-upgrade",
        "review-chain",
        "no-fallback",
        "v8.2-only",
        "U0-U12",
        "low-evidence-ranking",
        "blind-reader-recovery",
        "privacy-provenance",
        "fixed-root",
        "framework-gap-next-run",
        "fresh-validation-before-final",
    ):
        assert boundary in smoke
