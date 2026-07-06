from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path

from build_crossframe_max_repair_plan import build_repair_plan, run_validators
from validate_crossframe_max_route_ledger_fixtures import (
    base_fixture,
    repo_root,
    write_full_artifact_fixture,
    write_fixture,
)


def error_types(errors: list[object]) -> set[str]:
    return {getattr(error, "error_type") for error in errors}


def actions(plan: dict[str, object]) -> set[str]:
    return set(plan.get("repair_actions", []))  # type: ignore[arg-type]


def assert_contains(value: object, expected: object, label: str) -> None:
    if isinstance(value, list) and expected in value:
        return
    if isinstance(value, set) and expected in value:
        return
    raise AssertionError(f"{label}: expected {expected!r}, got {value!r}")


def write_valid_fixture(workspace: Path) -> None:
    write_full_artifact_fixture(workspace)


def expect_error_plan(name: str, mutate, expected_error: str, expected_action: str | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix=f"crossframe-max-repair-{name}-") as temp_dir:
        workspace = Path(temp_dir)
        write_valid_fixture(workspace)
        mutate(workspace)
        errors = run_validators(workspace, repo_root() / "skills" / "crossframe-max")
        if expected_error not in error_types(errors):
            raise AssertionError(f"{name}: expected {expected_error}, got {[getattr(e, 'error_type') for e in errors]}")
        plan = build_repair_plan(errors, workspace, validation_attempt=1)
        if plan.get("final_output_allowed") is not False:
            raise AssertionError(f"{name}: final output must be blocked")
        if expected_action:
            assert_contains(actions(plan), expected_action, f"{name}: repair_actions")


def test_valid_report_produces_no_repair_plan() -> None:
    with tempfile.TemporaryDirectory(prefix="crossframe-max-repair-valid-") as temp_dir:
        workspace = Path(temp_dir)
        write_valid_fixture(workspace)
        errors = run_validators(workspace, repo_root() / "skills" / "crossframe-max")
        if errors:
            raise AssertionError(f"valid repair fixture expected pass, got {errors}")
        plan = build_repair_plan(errors, workspace, validation_attempt=1)
        if plan.get("final_output_allowed") is not True:
            raise AssertionError(f"valid repair fixture should allow final output, got {plan}")
        if plan.get("repair_actions"):
            raise AssertionError(f"valid repair fixture should not require repair actions, got {plan}")


def test_concept_anchor_mismatch() -> None:
    def mutate(workspace: Path) -> None:
        data = json.loads((workspace / "max-concept-hit-ledger.json").read_text(encoding="utf-8"))
        data["concept_hits"][1]["source_ranges_from_registry"] = ["P0276-P0355"]
        data["concept_hits"][1]["source_ranges_read"] = ["P0276-P0355"]
        data["concept_hits"][1]["source_paragraph_ids"] = ["P0276"]
        (workspace / "max-concept-hit-ledger.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    expect_error_plan(
        "concept-anchor-mismatch",
        mutate,
        "concept_source_anchor_mismatch",
        "regenerate_concept_hit_and_downstream",
    )


def test_missing_contract() -> None:
    def mutate(workspace: Path) -> None:
        data = json.loads((workspace / "max-concept-hit-ledger.json").read_text(encoding="utf-8"))
        data["concept_hits"][0]["contract_id"] = "v6-core-contracts.md#不存在概念"
        (workspace / "max-concept-hit-ledger.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    expect_error_plan("missing-contract", mutate, "concept_contract_missing", "repository_maintenance_required")


def test_essay_missing_real_claim_or_source() -> None:
    def mutate(workspace: Path) -> None:
        (workspace / "max-essay.md").write_text("source_anchor\n", encoding="utf-8")

    expect_error_plan(
        "essay-missing-real-claim-or-source",
        mutate,
        "missing_claim_or_source_reference",
        "regenerate_markdown_only",
    )


def test_evidence_insufficient() -> None:
    def mutate(workspace: Path) -> None:
        data = json.loads((workspace / "max-evidence-reasoning-audit.json").read_text(encoding="utf-8"))
        data["audits"][0].pop("counterevidence", None)
        data["audits"][0].pop("evidence_chain", None)
        (workspace / "max-evidence-reasoning-audit.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    expect_error_plan("evidence-insufficient", mutate, "counterevidence_missing")


def test_retry_budget_exceeded() -> None:
    fixture = copy.deepcopy(base_fixture("history_analysis"))
    with tempfile.TemporaryDirectory(prefix="crossframe-max-repair-retry-") as temp_dir:
        workspace = Path(temp_dir)
        write_fixture(workspace, fixture)
        errors = run_validators(workspace, repo_root() / "skills" / "crossframe-max")
        plan = build_repair_plan(errors, workspace, validation_attempt=3)
        assert_contains(actions(plan), "max_incomplete", "retry-budget: repair_actions")
        if plan.get("max_incomplete_if_unresolved") is not True:
            raise AssertionError(f"retry-budget: expected max incomplete, got {plan}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CrossFrame Max repair-loop fixtures.")
    parser.add_argument("--write-valid-fixture", default=None, help="Write a reusable valid artifact fixture.")
    args = parser.parse_args()
    if args.write_valid_fixture:
        target = Path(args.write_valid_fixture).resolve()
        target.mkdir(parents=True, exist_ok=True)
        write_valid_fixture(target)
        return 0
    test_valid_report_produces_no_repair_plan()
    test_concept_anchor_mismatch()
    test_missing_contract()
    test_essay_missing_real_claim_or_source()
    test_evidence_insufficient()
    test_retry_budget_exceeded()
    print("ok: crossframe max repair fixtures passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
