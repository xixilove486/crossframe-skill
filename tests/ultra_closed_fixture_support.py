from __future__ import annotations

import hashlib
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
    materialization = _module(repo_root, "materialization")
    evidence = _fixture(repo_root, "evidence-ledger-valid.json")
    world = _fixture(repo_root, "world-volume-valid.json")
    transformation = _fixture(repo_root, "transformation-valid.json")
    verdict = _fixture(repo_root, "verdict-valid.json")
    concept_document = make_concept_document(
        evidence,
        world,
        transformation,
    )
    authored: dict[str, dict[str, object]] = {
        "U04-world-volume.json": world,
        "U05-transformation-ledger.json": transformation,
        "U05-concept-disposition.json": concept_document,
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
    recursive_relatives = tuple(
        sorted(
            relative
            for relative in authored
            if relative.startswith("U07-recursive-states/")
        )
    )
    upstream_relatives = (
        "U03-evidence-ledger.json",
        "U04-world-volume.json",
        "U05-transformation-ledger.json",
        "U05-concept-disposition.json",
        "U06-claim-mechanism-graph.json",
        *recursive_relatives,
        "U07-recursive-lineage.json",
        "U08-order-evaluation.json",
        "U08-red-team-report.json",
        "U09-verdict.json",
        "U09-action-ranking.json",
        "U09-forecast-ledger.json",
    )
    required: list[dict[str, str]] = []
    placeholder_by_relative: dict[str, str] = {}
    for relative in upstream_relatives:
        destination = materialization.artifact_destination(
            layout,
            layout.authoring_dir / relative,
        )
        artifact_path = destination.relative_to(layout.run_dir).as_posix()
        placeholder = hashlib.sha256(
            f"closed-fixture-authority:{artifact_path}".encode("utf-8")
        ).hexdigest()
        placeholder_by_relative[relative] = placeholder
        required.append(
            {
                "path": artifact_path,
                "sha256": placeholder,
                "media_type": "application/json",
            }
        )

    semantic_authority = {
        "UNIT-MAIN-VERDICT": (
            "U06-claim-mechanism-graph.json",
            "CLAIM-CHANNEL-CONSTRAINT",
        ),
        "UNIT-CONFIDENCE": (
            "U08-order-evaluation.json",
            "BASELINE-ORDER-1",
        ),
        "UNIT-STEELMAN": (
            "U07-recursive-states/NODE-MIXTURE-ORDER-1.json",
            "NODE-MIXTURE-ORDER-1",
        ),
        "UNIT-DECISIVE-EVIDENCE": (
            "U03-evidence-ledger.json",
            "EVIDENCE-ASSOCIATION-CHARTER",
        ),
        "UNIT-UNKNOWN": ("U04-world-volume.json", "UNKNOWN-ADAPTATION"),
        "UNIT-CIRCLE-RELATION": (
            "U05-transformation-ledger.json",
            "TRANSFORM-CIRCLE-RELATION",
        ),
        "UNIT-MECHANISM": (
            "U06-claim-mechanism-graph.json",
            "MECHANISM-REVIEW-CHANNEL",
        ),
        "UNIT-RIVAL": (
            "U07-recursive-states/NODE-RIVAL-ORDER-1.json",
            "NODE-RIVAL-ORDER-1",
        ),
        "UNIT-ORDER-1": (
            "U07-recursive-states/NODE-MAIN-ORDER-1.json",
            "NODE-MAIN-ORDER-1",
        ),
        "UNIT-ORDER-2": (
            "U07-recursive-states/NODE-MAIN-ORDER-2.json",
            "NODE-MAIN-ORDER-2",
        ),
        "UNIT-ORDER-3": (
            "U07-recursive-states/NODE-MAIN-ORDER-3.json",
            "NODE-MAIN-ORDER-3",
        ),
        "UNIT-RESIDUAL": (
            "U07-recursive-states/NODE-RESIDUAL-ORDER-1.json",
            "NODE-RESIDUAL-ORDER-1",
        ),
        "UNIT-FIVE-VERDICTS": ("U09-verdict.json", "VERDICT-FACT"),
        "UNIT-ACTION": ("U09-action-ranking.json", "OPTION-PROBE"),
        "UNIT-REVERSAL": ("U09-action-ranking.json", "OPTION-DELAY"),
        "UNIT-APPENDIX-MAPPING": ("U04-world-volume.json", "OMEGA-FIXTURE"),
        "UNIT-APPENDIX-BRANCHES": (
            "U07-recursive-lineage.json",
            "BRANCH-MAIN",
        ),
        "UNIT-APPENDIX-FORECAST": (
            "U09-forecast-ledger.json",
            "FORECAST-BRANCH-SELECTION",
        ),
        "UNIT-APPENDIX-SOURCES": (
            "U03-evidence-ledger.json",
            "EVIDENCE-INTERVIEW-ONE",
        ),
        "UNIT-APPENDIX-GAPS": (
            "U08-red-team-report.json",
            "UNRESOLVED-PEER-CHANNEL",
        ),
    }
    semantic_units = output_authority.get("semantic_universe")
    if not isinstance(semantic_units, list):
        raise ValueError("closed output authority lacks a semantic universe")
    mappings = output_authority.get("mappings")
    if not isinstance(mappings, list):
        raise ValueError("closed output authority lacks semantic mappings")
    entries = (*output_authority["sections"], *output_authority["appendices"])
    concept_section = next(
        entry for entry in entries if entry["section_id"] == "reader-14"
    )
    concept_unit_ids = concept_section.get("semantic_unit_ids")
    if not isinstance(concept_unit_ids, list):
        raise ValueError("closed concept section lacks semantic unit IDs")
    source_mapping = next(
        mapping for mapping in mappings if mapping["unit_id"] == "UNIT-APPENDIX-SOURCES"
    )
    concept_excerpt = source_mapping.get("normalized_excerpt")
    if not isinstance(concept_excerpt, str) or not concept_excerpt:
        raise ValueError("closed concept section lacks normalized reader prose")
    concept_excerpt_sha256 = hashlib.sha256(
        concept_excerpt.encode("utf-8")
    ).hexdigest()
    obligations = concept_document.get("semantic_obligations")
    if not isinstance(obligations, list) or not obligations:
        raise ValueError("closed concept disposition lacks semantic obligations")
    concept_mappings: list[dict[str, object]] = []
    for obligation in obligations:
        if not isinstance(obligation, dict):
            raise ValueError("closed semantic obligation must be an object")
        obligation_id = obligation.get("obligation_id")
        unit_id = obligation.get("semantic_unit_id")
        status = obligation.get("status")
        if not all(
            isinstance(value, str) and value
            for value in (obligation_id, unit_id, status)
        ):
            raise ValueError("closed semantic obligation lacks its identity")
        concept_unit_ids.append(unit_id)
        semantic_authority[unit_id] = (
            "U05-concept-disposition.json",
            obligation_id,
        )
        semantic_units.append(
            {
                "unit_id": unit_id,
                "unit_kind": "claim",
                "status": status,
                "affects_ranking": True,
                "used_in_reasoning": True,
                "promised_to_reader": True,
                "source_refs": [obligation_id],
                "authority_artifact_sha256": placeholder_by_relative[
                    "U05-concept-disposition.json"
                ],
                "authority_locator": obligation_id,
                "normalized_semantic_text_sha256": concept_excerpt_sha256,
            }
        )
        concept_mappings.append(
            {
                "unit_id": unit_id,
                "unit_kind": "claim",
                "section_id": "reader-14",
                "normalized_excerpt": concept_excerpt,
                "source_refs": [obligation_id],
            }
        )
    gap_mapping_index = next(
        index
        for index, mapping in enumerate(mappings)
        if mapping["section_id"] == "reader-15"
    )
    mappings[gap_mapping_index:gap_mapping_index] = concept_mappings
    units_by_id: dict[str, dict[str, object]] = {}
    for unit in semantic_units:
        if not isinstance(unit, dict) or not isinstance(unit.get("unit_id"), str):
            raise ValueError("closed semantic unit must be an identified object")
        unit_id = unit["unit_id"]
        try:
            relative, locator = semantic_authority[unit_id]
        except KeyError as error:
            raise ValueError(f"closed semantic unit has no authority: {unit_id}") from error
        unit["authority_artifact_sha256"] = placeholder_by_relative[relative]
        unit["authority_locator"] = locator
        units_by_id[unit_id] = unit
    for entry in entries:
        entry["dependency_hashes"] = list(
            dict.fromkeys(
                str(units_by_id[unit_id]["authority_artifact_sha256"])
                for unit_id in entry["semantic_unit_ids"]
            )
        )
    represented_hashes = {
        str(unit["authority_artifact_sha256"])
        for unit in semantic_units
        if isinstance(unit, dict)
    }
    if represented_hashes != set(placeholder_by_relative.values()):
        raise ValueError(
            "closed semantic universe must authorize every U3-U9 artifact"
        )
    output_authority["required_artifacts"] = required
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
