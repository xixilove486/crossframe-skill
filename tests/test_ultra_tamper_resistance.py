from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SUPPORT_PATH = Path(__file__).with_name("test_ultra_validation.py")
_SPEC = importlib.util.spec_from_file_location("_ultra_validation_support", SUPPORT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
support = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = support
_SPEC.loader.exec_module(support)


def _rewrite_json(run, relative: str, mutate) -> None:
    path = run.path(relative)
    value = support.load_json(path)
    mutate(value)
    value["content_sha256"] = run.modules.schemas.compute_artifact_content_sha256(value)
    support.write_json(path, value)
    support.refresh_manifest(run)


def _marker_stuffing(run) -> None:
    def mutate(graph):
        stuffed = "mechanism " * 300
        for claim in graph["claims"]:
            claim["statement"] = stuffed
        for mechanism in graph["mechanisms"]:
            mechanism["description"] = stuffed

    _rewrite_json(
        run,
        "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
        mutate,
    )


def _empty_rival(run) -> None:
    def mutate(graph):
        rival = next(item for item in graph["explanations"] if item["kind"] == "strongest-rival")
        rival_claim = next(item for item in graph["claims"] if item["claim_id"] in rival["claim_ids"])
        rival_claim["statement"] = ""

    _rewrite_json(
        run,
        "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
        mutate,
    )


def _fake_read_ledger(run) -> None:
    path = run.path("artifacts/U00-U03-evidence/ultra-read-events.jsonl")
    path.write_bytes(path.read_bytes().splitlines(keepends=True)[0])
    support.refresh_manifest(run)


def _source_mismatch(run) -> None:
    path = run.path("artifacts/U00-U03-evidence/ultra-read-events.jsonl")
    rows = path.read_bytes().splitlines()
    first = json.loads(rows[0])
    first["content_sha256"] = "f" * 64
    first["read_event_sha256"] = support.canonical_sha256(
        {key: value for key, value in first.items() if key != "read_event_sha256"}
    )
    rows[0] = support.canonical_bytes(first).rstrip(b"\n")
    path.write_bytes(b"\n".join(rows) + b"\n")
    support.refresh_manifest(run)


def _article_hash_mismatch(run) -> None:
    path = run.path("work/authoring/article.partial.md")
    path.write_bytes(path.read_bytes() + b"article changed after coverage freeze\n")
    support.refresh_manifest(run)


def _coverage_excerpt_missing(run) -> None:
    def mutate(coverage):
        coverage["mappings"][0]["normalized_excerpt"] = "This excerpt is absent from the article."

    _rewrite_json(run, "work/authoring/U11-semantic-coverage.json", mutate)


def _premature_publish(run) -> None:
    path = run.layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("published before fresh validation", encoding="utf-8")


def _simulation_as_fact(run) -> None:
    evidence_path = "artifacts/U00-U03-evidence/ultra-evidence-ledger.json"
    graph_path = "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json"

    def add_simulation(evidence):
        simulated = copy.deepcopy(evidence["entries"][0])
        simulated.update(
            {
                "evidence_id": "EVIDENCE-SIMULATION",
                "identity": "simulated",
                "statement": "A model branch produced a local response.",
                "source_refs": ["SOURCE-SIMULATION"],
                "upstream_lineage": ["UPSTREAM-SIMULATION"],
                "supported_claim": "The simulated branch contains this response.",
                "cannot_prove": "The simulation cannot establish an observed fact.",
            }
        )
        evidence["entries"].append(simulated)

    _rewrite_json(run, evidence_path, add_simulation)

    def promote(graph):
        graph["claims"][0]["identity"] = "observed"
        graph["claims"][0]["evidence_refs"] = ["EVIDENCE-SIMULATION"]

    _rewrite_json(run, graph_path, promote)


def _flatten_world(run) -> None:
    flat = support.seal_fixture(run.modules, "world-volume-flat-invalid.json")
    support.write_json(
        run.path("artifacts/U04-U05-world-volume/ultra-world-volume.json"), flat
    )
    support.refresh_manifest(run)


def _lose_lineage(run) -> None:
    def mutate(state):
        state["inherited_unknown_ids"] = []
        state["inherited_residual_ids"] = []

    _rewrite_json(
        run,
        "artifacts/U06-U08-inference/recursive-state-NODE-MAIN-ORDER-1.json",
        mutate,
    )


def _secret_log(run) -> None:
    path = run.layout.logs_dir / "validator.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Authorization: Bearer sk-live-1234567890abcdefghijklmnopqrstuvwxyz", encoding="utf-8")


TAMPER_CASES = (
    ("marker-stuffing", _marker_stuffing, "ULTRA-MARKER-STUFFING"),
    ("empty-rival", _empty_rival, "ULTRA-EMPTY-RIVAL"),
    ("fake-read-ledger", _fake_read_ledger, "ULTRA-READ-COVERAGE"),
    ("source-mismatch", _source_mismatch, "ULTRA-SOURCE-MISMATCH"),
    ("article-hash-mismatch", _article_hash_mismatch, "ULTRA-ARTICLE-HASH"),
    ("coverage-excerpt-missing", _coverage_excerpt_missing, "ULTRA-COVERAGE-MISSING"),
    ("premature-publish", _premature_publish, "ULTRA-PREMATURE-PUBLISH"),
    ("simulation-as-fact", _simulation_as_fact, "ULTRA-SIMULATION-AS-FACT"),
    ("flattened-world", _flatten_world, "ULTRA-WORLD-FLATTENING"),
    ("lineage-loss", _lose_lineage, "ULTRA-LINEAGE-LOSS"),
    ("secret-log", _secret_log, "ULTRA-SECRET-LOG"),
)


@pytest.mark.parametrize(
    ("case_name", "mutate", "expected_code"),
    TAMPER_CASES,
    ids=[item[0] for item in TAMPER_CASES],
)
def test_fresh_validator_rejects_task12_tamper_conditions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    mutate,
    expected_code: str,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    mutate(run)

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )
    assert report["overall_status"] == "fail", case_name
    assert expected_code in support.report_error_codes(report), case_name


def test_tamper_validation_never_modifies_disk_or_acquires_a_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    _marker_stuffing(run)
    before = support.file_tree(run.run_dir)

    run.modules.validation.validate_run_from_disk(
        support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
    )

    assert support.file_tree(run.run_dir) == before
    assert not (run.run_dir / ".writer-lease.json").exists()
    assert not run.layout.validation_current_dir.exists()
    assert not run.layout.validation_attempts_dir.exists()
