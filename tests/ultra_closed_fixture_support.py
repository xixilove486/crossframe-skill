from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
import re
import sys
from typing import Mapping


CLOSED_ORGANIZATION_CASE = {
    "case_id": "org-delay-multiparent",
    "material_closed": True,
    "parents": ["care-constraint", "incentive-system", "resource-allocation"],
    "channels": [
        {"channel_id": "formal-schedule", "clock": "weekly", "latency_days": 2},
        {"channel_id": "care-load", "clock": "event-driven", "latency_days": 11},
    ],
    "order_2": {
        "effect": "reversal",
        "condition": "formal escalation increases hidden care-load displacement",
    },
    "order_3": {
        "effect": "lock-in",
        "condition": "promotion metrics reward the escalation pattern",
    },
    "rival": {
        "explanation_id": "individual-execution-deficit",
        "confidence": "low",
    },
    "verdict_kinds": [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ],
}


def _module(repo_root: Path, name: str):
    scripts = str(repo_root / "skills/crossframe-ultra/scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"ultra_runtime.{name}")


def _fixture(repo_root: Path, name: str) -> dict[str, object]:
    path = repo_root / "tests/fixtures/ultra-runtime" / name
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"closed fixture must be an object: {name}")
    return value


def write_closed_u4_u10_authoring(
    repo_root: Path,
    layout: object,
) -> dict[str, object]:
    from tests.test_ultra_concept_closure import make_concept_document
    from tests.test_ultra_judgment import make_action_ranking, make_gap_ledger
    from tests.test_ultra_recursion import state_registry

    jsonio = _module(repo_root, "jsonio")
    article = _module(repo_root, "article")
    evidence = _fixture(repo_root, "evidence-ledger-valid.json")
    world = _fixture(repo_root, "world-volume-valid.json")
    transformation = _fixture(repo_root, "transformation-valid.json")
    verdict = _fixture(repo_root, "verdict-valid.json")
    authored: dict[str, dict[str, object]] = {
        "U04-world-volume.json": world,
        "U05-transformation-ledger.json": transformation,
        "U05-concept-disposition.json": make_concept_document(
            evidence,
            world,
            transformation,
        ),
        "U06-claim-mechanism-graph.json": _fixture(
            repo_root, "claim-mechanism-graph-valid.json"
        ),
        "U07-recursive-lineage.json": _fixture(
            repo_root, "recursive-lineage-valid.json"
        ),
        "U08-order-evaluation.json": _fixture(
            repo_root, "order-evaluation-valid.json"
        ),
        "U08-red-team-report.json": _fixture(
            repo_root, "red-team-report-valid.json"
        ),
        "U09-verdict.json": verdict,
        "U09-action-ranking.json": make_action_ranking(verdict),
        "U09-forecast-ledger.json": _fixture(repo_root, "forecast-valid.json"),
    }
    for recursive_state in state_registry().values():
        authored[
            f"U07-recursive-states/{recursive_state['node_id']}.json"
        ] = recursive_state
    authored["U10-framework-gap-ledger.json"] = make_gap_ledger(
        authored["U09-action-ranking.json"]
    )

    output_authority = _fixture(
        repo_root,
        "article-packets/frozen-upstream-authority.json",
    )
    required = output_authority["required_artifacts"]
    if not isinstance(required, list) or len(required) < 2:
        raise ValueError("closed output authority lacks required artifacts")
    required[0]["path"] = "artifacts/U09-U10-verdict/U09-verdict.json"
    required[1]["path"] = "artifacts/U09-U10-verdict/U09-action-ranking.json"
    authored["U10-output-plan.json"] = article.build_output_plan_artifact(
        run_id=output_authority["run_id"],
        version_binding=output_authority["version_binding"],
        generated_at=output_authority["generated_at"]["u10"],
        u9_parent_event_sha256=output_authority["u9_parent_event_sha256"],
        article_path=output_authority["article_path"],
        sections=output_authority["sections"],
        appendices=output_authority["appendices"],
        required_artifacts=required,
        semantic_universe=output_authority["semantic_universe"],
        blind_recovery_expectations=output_authority[
            "blind_recovery_expectations"
        ],
    )
    authoring_dir = layout.authoring_dir
    for relative, document in authored.items():
        jsonio.atomic_write_json(authoring_dir / relative, document)
    return output_authority


def write_closed_u11_authoring(
    repo_root: Path,
    layout: object,
    sealed_plan: Mapping[str, object],
    output_authority: Mapping[str, object],
    *,
    generated_at: str,
) -> None:
    article = _module(repo_root, "article")
    constants = _module(repo_root, "constants")
    coverage = _module(repo_root, "coverage")
    jsonio = _module(repo_root, "jsonio")
    materialization = _module(repo_root, "materialization")

    article_text = (
        repo_root
        / "tests/fixtures/ultra-runtime/article-packets/blind-reader-article.md"
    ).read_text("utf-8").replace("\r\n", "\n")
    article_parts = tuple(
        match.group(0).strip() + "\n"
        for match in re.finditer(r"(?ms)^## .*?(?=^## |\Z)", article_text)
    )
    if len(article_parts) != 15:
        raise ValueError("closed article fixture must contain exactly 15 packets")
    packet_dir = layout.authoring_dir / "article/packets"
    for ordinal, prose in enumerate(article_parts, start=1):
        packet_path = packet_dir / f"packet-{ordinal:02d}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(prose, encoding="utf-8", newline="\n")
    packet_paths = tuple(sorted(packet_dir.glob("*.md"), key=lambda path: path.name))
    packet_documents = materialization._packet_mappings(sealed_plan, packet_paths)
    assembled = article.assemble_article(
        sealed_plan,
        packet_documents,
        layout.authoring_dir / "article.partial.md",
    )
    plan_sha256 = jsonio.sha256_bytes(jsonio.canonical_json_bytes(sealed_plan))
    mappings = output_authority.get("mappings")
    if not isinstance(mappings, list):
        raise ValueError("closed output authority lacks semantic mappings")
    coverage_document = coverage.build_semantic_coverage_artifact(
        assembled.article_text,
        sealed_plan,
        mappings,
        run_id=layout.run_dir.name,
        version_binding=constants.current_version_binding(),
        generated_at=generated_at,
        expected_output_plan_artifact_sha256=plan_sha256,
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-semantic-coverage.json",
        coverage_document,
    )
    coverage_sha256 = jsonio.sha256_bytes(
        jsonio.canonical_json_bytes(coverage_document)
    )
    review_document = coverage.build_article_review_artifact(
        assembled.article_text,
        sealed_plan,
        coverage_document,
        run_id=layout.run_dir.name,
        version_binding=constants.current_version_binding(),
        generated_at=generated_at,
        expected_output_plan_artifact_sha256=plan_sha256,
        expected_coverage_artifact_sha256=coverage_sha256,
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-article-review.json",
        review_document,
    )
    (layout.authoring_dir / "完整推演档案.md").write_text(
        "# 完整推演档案\n\n真实磁盘 seam 验证档案。\n",
        encoding="utf-8",
        newline="\n",
    )


__all__ = (
    "CLOSED_ORGANIZATION_CASE",
    "write_closed_u4_u10_authoring",
    "write_closed_u11_authoring",
)
