from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path

from tests.pytest_import_guard import pytest


from tests import test_ultra_validation as support


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
        "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json",
        mutate,
    )


def _empty_rival(run) -> None:
    def mutate(graph):
        rival = next(item for item in graph["explanations"] if item["kind"] == "strongest-rival")
        rival_claim = next(item for item in graph["claims"] if item["claim_id"] in rival["claim_ids"])
        rival_claim["statement"] = ""

    _rewrite_json(
        run,
        "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json",
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

    _rewrite_json(
        run,
        "artifacts/U09-U10-verdict/U11-semantic-coverage.json",
        mutate,
    )


def _premature_publish(run) -> None:
    path = run.layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("published before fresh validation", encoding="utf-8")


def _simulation_as_fact(run) -> None:
    evidence_path = "artifacts/U00-U03-evidence/U03-evidence-ledger.json"
    graph_path = "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json"

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
        run.path("artifacts/U04-U05-world-volume/U04-world-volume.json"), flat
    )
    support.refresh_manifest(run)


def _lose_lineage(run) -> None:
    def mutate(state):
        state["inherited_unknown_ids"] = []
        state["inherited_residual_ids"] = []

    _rewrite_json(
        run,
        "artifacts/U06-U08-inference/U07-recursive-states/NODE-MAIN-ORDER-1.json",
        mutate,
    )


def _secret_log(run) -> None:
    path = run.layout.logs_dir / "validator.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Authorization: Bearer sk-live-1234567890abcdefghijklmnopqrstuvwxyz", encoding="utf-8")


def _fabricate_u1_authority(run) -> None:
    events_path = run.path("artifacts/U00-U03-evidence/ultra-read-events.jsonl")
    rows = [json.loads(row) for row in events_path.read_bytes().splitlines()]
    for ordinal, event in enumerate(rows, start=1):
        event["source_lock_sha256"] = "1" * 64
        event["parent_event_sha256"] = "2" * 64
        event["receipt_sha256"] = hashlib.sha256(
            f"fabricated-receipt:{ordinal}".encode("utf-8")
        ).hexdigest()
        event["reader_mode"] = "assistive"
        event["execution_identity"] = {
            "kind": "host-process",
            "process_id": 900_000 + ordinal,
            "executable": "fabricated-reader.exe",
            "user": "fabricated-reader",
        }
        event["read_at"] = "2026-08-04T00:00:01Z"
        event["read_event_sha256"] = support.canonical_sha256(
            {key: value for key, value in event.items() if key != "read_event_sha256"}
        )
    events_path.write_bytes(b"".join(support.canonical_bytes(event) for event in rows))

    coverage_path = run.path("recovery/u1-authority/source-coverage.json")
    coverage = support.load_json(coverage_path)
    coverage["parent_event_sha256"] = "2" * 64
    coverage["source_lock_sha256"] = "1" * 64
    coverage["receipt_sha256s"] = [event["receipt_sha256"] for event in rows]
    coverage["read_event_sha256s"] = [event["read_event_sha256"] for event in rows]
    support.write_json(coverage_path, coverage)
    support.refresh_manifest(run)


def _reseal_phase_events_with_substituted_u4_output(run) -> None:
    path = run.path("recovery/phase-events.jsonl")
    events = support._phase_events(run.run_dir)
    changed = False
    parent = "0" * 64
    for event in events:
        event["parent_event_sha256"] = parent
        if event["phase_id"] == "U4":
            event["output_artifact_hashes"][0] = "f" * 64
            changed = True
        event["content_sha256"] = run.modules.state_machine._compute_event_content_sha256(
            event
        )
        event["event_sha256"] = run.modules.state_machine.compute_event_sha256(event)
        parent = event["event_sha256"]
    assert changed
    path.write_bytes(b"".join(support.canonical_bytes(event) for event in events))
    support.refresh_manifest(run)


def _reseal_phase_tail_and_checkpoints(run, first_phase: str) -> None:
    first_ordinal = int(first_phase[1:])
    checkpoints_dir = run.path("recovery/checkpoints")
    checkpoint_records = [
        (path, support.load_json(path))
        for path in sorted(checkpoints_dir.glob("*.json"))
    ]
    for _, checkpoint in checkpoint_records:
        if int(str(checkpoint["phase_id"])[1:]) < first_ordinal:
            continue
        for artifact_ref in checkpoint["artifact_hashes"]:
            artifact_ref["sha256"] = hashlib.sha256(
                run.path(artifact_ref["path"]).read_bytes()
            ).hexdigest()

    phase_checkpoints = {
        checkpoint["phase_id"]: checkpoint
        for _, checkpoint in checkpoint_records
        if checkpoint["boundary_kind"] == "phase"
    }
    events = support._phase_events(run.run_dir)
    parent = "0" * 64
    events_by_phase = {}
    for event in events:
        ordinal = int(str(event["phase_id"])[1:])
        if ordinal >= first_ordinal:
            event["parent_event_sha256"] = parent
            if event["status"] == "complete":
                event["output_artifact_hashes"] = [
                    item["sha256"]
                    for item in phase_checkpoints[event["phase_id"]]["artifact_hashes"]
                ]
            event["content_sha256"] = run.modules.state_machine._compute_event_content_sha256(
                event
            )
            event["event_sha256"] = run.modules.state_machine.compute_event_sha256(event)
        parent = event["event_sha256"]
        events_by_phase[event["phase_id"]] = event
    run.path("recovery/phase-events.jsonl").write_bytes(
        b"".join(support.canonical_bytes(event) for event in events)
    )

    replacements = []
    for source, checkpoint in checkpoint_records:
        if int(str(checkpoint["phase_id"])[1:]) < first_ordinal:
            continue
        bound_phase = (
            checkpoint["phase_id"]
            if checkpoint["boundary_kind"] == "phase"
            else "U10"
        )
        checkpoint["phase_event_sha256"] = events_by_phase[bound_phase]["event_sha256"]
        checkpoint["content_sha256"] = (
            run.modules.schemas.compute_artifact_content_sha256(checkpoint)
        )
        raw = support.canonical_bytes(checkpoint)
        target = checkpoints_dir / f"{hashlib.sha256(raw).hexdigest()}.json"
        target.write_bytes(raw)
        replacements.append((source, target))
    for source, target in replacements:
        if source != target:
            source.unlink()
    support.refresh_manifest(run)


def _substitute_u4_checkpoint_path(run) -> None:
    checkpoints = run.path("recovery/checkpoints")
    source = run.path("artifacts/U04-U05-world-volume/U04-world-volume.json")
    substitute = run.path("recovery/u1-authority/u4-world-volume-substitute.json")
    substitute.write_bytes(source.read_bytes())
    target = next(
        path
        for path in checkpoints.glob("*.json")
        if support.load_json(path).get("phase_id") == "U4"
        and support.load_json(path).get("boundary_kind") == "phase"
    )
    checkpoint = support.load_json(target)
    checkpoint["artifact_hashes"][0]["path"] = (
        "recovery/u1-authority/u4-world-volume-substitute.json"
    )
    checkpoint["content_sha256"] = run.modules.schemas.compute_artifact_content_sha256(
        checkpoint
    )
    raw = support.canonical_bytes(checkpoint)
    replacement = checkpoints / f"{hashlib.sha256(raw).hexdigest()}.json"
    replacement.write_bytes(raw)
    target.unlink()
    support.refresh_manifest(run)


DAG_TAMPER_CASES = (
    (
        "u4-evidence",
        "artifacts/U04-U05-world-volume/U04-world-volume.json",
        "evidence_artifact_sha256",
    ),
    (
        "u5-world",
        "artifacts/U04-U05-world-volume/U05-transformation-ledger.json",
        "world_volume_artifact_sha256",
    ),
    (
        "u5-transformations",
        "artifacts/U04-U05-world-volume/U05-concept-disposition.json",
        "transformation_ledger_artifact_sha256",
    ),
    (
        "u6-concepts",
        "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json",
        "concept_disposition_artifact_sha256",
    ),
    (
        "u7-world",
        "artifacts/U06-U08-inference/U07-recursive-lineage.json",
        "world_volume_artifact_sha256",
    ),
    (
        "u8-lineage",
        "artifacts/U06-U08-inference/U08-order-evaluation.json",
        "recursive_lineage_artifact_sha256",
    ),
    (
        "u8-order",
        "artifacts/U06-U08-inference/U08-red-team-report.json",
        "order_evaluation_artifact_sha256",
    ),
    (
        "u9-evidence",
        "artifacts/U09-U10-verdict/U09-verdict.json",
        "evidence_ledger_artifact_sha256",
    ),
    (
        "u9-verdict-action",
        "artifacts/U09-U10-verdict/U09-action-ranking.json",
        "verdict_artifact_sha256",
    ),
    (
        "u9-verdict-forecast",
        "artifacts/U09-U10-verdict/U09-forecast-ledger.json",
        "verdict_artifact_sha256",
    ),
)


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


def test_fresh_validator_rejects_fabricated_u1_authority_after_full_reseal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    _fabricate_u1_authority(run)

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail"
    assert "ULTRA-READ-AUTHORITY" in support.report_error_codes(report)


def test_fresh_validator_rejects_missing_persisted_u1_read_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    run.path("recovery/u1-authority/read-plan.json").unlink()

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail"
    assert "ULTRA-READ-AUTHORITY" in support.report_error_codes(report)


def test_persisted_u1_helper_rejects_rebuilt_read_plan_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    arguments = support.persisted_u1_authority_args(run)
    read_plan = copy.deepcopy(arguments["read_plan"])
    read_plan["source_unit_count"] = 4_752
    support.write_json(
        run.path("recovery/u1-authority/read-plan.json"),
        read_plan,
    )
    arguments["read_plan"] = read_plan

    with pytest.raises(
        run.modules.source_integrity.SourceCoverageError,
        match="read plan",
    ):
        run.modules.source_integrity._validate_persisted_u1_authority(
            **arguments
        )


def test_persisted_u1_helper_rejects_stale_role_after_hash_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    arguments = support.persisted_u1_authority_args(run)
    source_lock = copy.deepcopy(arguments["source_lock"])
    source_lock["knowledge_report_sha256"] = "f" * 64
    source_lock["content_sha256"] = (
        run.modules.schemas.compute_artifact_content_sha256(source_lock)
    )
    support.write_json(
        run.path("recovery/u1-authority/source-lock.json"),
        source_lock,
    )
    arguments["source_lock"] = source_lock
    arguments["expected_source_lock_sha256"] = support.canonical_sha256(source_lock)

    with pytest.raises(
        run.modules.source_integrity.SourceLockError,
        match="disk authority",
    ):
        run.modules.source_integrity._validate_persisted_u1_authority(
            **arguments
        )


def test_persisted_u1_helper_rejects_resealed_receipt_event_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    arguments = support.persisted_u1_authority_args(run)
    read_events = copy.deepcopy(arguments["read_events"])
    read_events[0]["receipt_sha256"] = "f" * 64
    read_events[0]["read_event_sha256"] = support.canonical_sha256(
        {
            key: value
            for key, value in read_events[0].items()
            if key != "read_event_sha256"
        }
    )
    events_path = run.path(
        "artifacts/U00-U03-evidence/ultra-read-events.jsonl"
    )
    events_path.write_bytes(
        b"".join(support.canonical_bytes(event) for event in read_events)
    )
    coverage = copy.deepcopy(arguments["coverage"])
    coverage["receipt_sha256s"][0] = read_events[0]["receipt_sha256"]
    coverage["read_event_sha256s"][0] = read_events[0]["read_event_sha256"]
    support.write_json(
        run.path("recovery/u1-authority/source-coverage.json"),
        coverage,
    )
    arguments["read_events"] = read_events
    arguments["coverage"] = coverage
    arguments["expected_read_coverage_sha256"] = support.canonical_sha256(
        coverage
    )

    with pytest.raises(
        run.modules.source_integrity.SourceCoverageError,
        match="receipt",
    ):
        run.modules.source_integrity._validate_persisted_u1_authority(
            **arguments
        )


def test_persisted_u1_helper_rejects_wrong_boundaries_and_witness_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    arguments = support.persisted_u1_authority_args(run)
    wrong_binding = copy.deepcopy(arguments["expected_version_binding"])
    wrong_binding["runtime_version"] = "0.0.0"
    wrong_inputs = copy.deepcopy(arguments["expected_inputs"])
    wrong_inputs[0]["sha256"] = "f" * 64
    witness_coverage = copy.deepcopy(arguments["coverage"])
    witness_coverage["run_id"] = "fabricated-witness"
    cases = (
        ("run", {"expected_run_id": "20260804T000000Z-000000000000"}),
        ("mode", {"expected_run_mode": "production"}),
        ("version", {"expected_version_binding": wrong_binding}),
        ("parent", {"expected_parent_event_sha256": "f" * 64}),
        ("cutoff", {"expected_evidence_cutoff": "2026-08-04T00:00:01Z"}),
        ("input", {"expected_inputs": wrong_inputs}),
        ("witness", {"coverage": witness_coverage}),
    )

    for _case_name, overrides in cases:
        with pytest.raises(
            (
                run.modules.source_integrity.SourceLockError,
                run.modules.source_integrity.SourceCoverageError,
            )
        ):
            run.modules.source_integrity._validate_persisted_u1_authority(
                **{**arguments, **overrides}
            )


def test_persisted_u1_helper_rejects_issuer_reconstruction_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    arguments = support.persisted_u1_authority_args(run)
    source_integrity = run.modules.source_integrity
    register = source_integrity._register_issuer_snapshot

    def register_with_read_audit_mismatch(registry, fields):
        token, digest = register(registry, fields)
        if registry is source_integrity._ISSUED_READ_AUDITS:
            return token, "f" * 64
        return token, digest

    monkeypatch.setattr(
        source_integrity,
        "_register_issuer_snapshot",
        register_with_read_audit_mismatch,
    )

    with pytest.raises(
        source_integrity.SourceLockError,
        match="sealed source lock and read audit",
    ):
        source_integrity._validate_persisted_u1_authority(**arguments)


@pytest.mark.parametrize(
    ("case_name", "relative", "field"),
    DAG_TAMPER_CASES,
    ids=[item[0] for item in DAG_TAMPER_CASES],
)
def test_fresh_validator_rejects_resealed_u4_u9_upstream_hash_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    relative: str,
    field: str,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    _rewrite_json(run, relative, lambda document: document.__setitem__(field, "9" * 64))

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail", case_name
    assert "ULTRA-AUTHORITY-DAG" in support.report_error_codes(report), case_name


@pytest.mark.parametrize(
    "mutate",
    (_reseal_phase_events_with_substituted_u4_output, _substitute_u4_checkpoint_path),
    ids=("phase-event-output", "checkpoint-artifact-ref"),
)
def test_fresh_validator_rejects_resealed_phase_or_checkpoint_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    mutate(run)

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail"
    assert "ULTRA-AUTHORITY-DAG" in support.report_error_codes(report)


def test_fresh_validator_rejects_resealed_u10_parent_authority_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    baseline_report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )
    baseline_codes = support.report_error_codes(baseline_report)
    assert "ULTRA-AUTHORITY-DAG" not in baseline_codes
    output_plan_path = run.path(
        "artifacts/U09-U10-verdict/U10-output-plan.json"
    )
    output_plan = support.load_json(output_plan_path)
    output_plan["u9_parent_event_sha256"] = "9" * 64
    output_plan["content_sha256"] = (
        run.modules.schemas.compute_artifact_content_sha256(output_plan)
    )
    support.write_json(output_plan_path, output_plan)
    _reseal_phase_tail_and_checkpoints(run, "U10")

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail"
    assert "ULTRA-AUTHORITY-DAG" in (
        support.report_error_codes(report) - baseline_codes
    )


def test_fresh_validator_recomputes_and_rejects_external_dependent_u11_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = support.build_valid_run(tmp_path, monkeypatch)
    baseline_report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )
    baseline_codes = support.report_error_codes(baseline_report)
    assert "ULTRA-ARTICLE-REVIEW-FAILED" not in baseline_codes
    article_path = run.path("work/authoring/article.partial.md")
    article_path.write_text(
        article_path.read_text("utf-8").rstrip()
        + "\n\n完整判断依据详见附件。\n",
        encoding="utf-8",
        newline="\n",
    )
    output_plan = support.load_json(
        run.path("artifacts/U09-U10-verdict/U10-output-plan.json")
    )
    coverage_path = run.path(
        "artifacts/U09-U10-verdict/U11-semantic-coverage.json"
    )
    coverage_document = support.load_json(coverage_path)
    coverage_document["article_sha256"] = hashlib.sha256(
        article_path.read_bytes()
    ).hexdigest()
    coverage_document["content_sha256"] = (
        run.modules.schemas.compute_artifact_content_sha256(coverage_document)
    )
    support.write_json(coverage_path, coverage_document)

    review_path = run.path("artifacts/U09-U10-verdict/U11-article-review.json")
    prior_review = support.load_json(review_path)
    coverage_module = importlib.import_module("ultra_runtime.coverage")
    review_document = coverage_module.build_article_review_artifact(
        article_path.read_text("utf-8"),
        output_plan,
        coverage_document,
        run_id=support.RUN_ID,
        version_binding=run.modules.constants.current_version_binding(),
        generated_at=prior_review["generated_at"],
        expected_output_plan_artifact_sha256=hashlib.sha256(
            support.canonical_bytes(output_plan)
        ).hexdigest(),
        expected_coverage_artifact_sha256=hashlib.sha256(
            support.canonical_bytes(coverage_document)
        ).hexdigest(),
    )
    assert review_document["overall_status"] == "mechanical-fail"
    assert review_document["external_dependencies"]
    support.write_json(review_path, review_document)
    _reseal_phase_tail_and_checkpoints(run, "U11")

    report = support.parse_report(
        run.modules.validation.validate_run_from_disk(
            support.REPO_ROOT, run.modules.paths.RunMode.TEST, support.RUN_ID
        )
    )

    assert report["overall_status"] == "fail"
    assert "ULTRA-ARTICLE-REVIEW-FAILED" in (
        support.report_error_codes(report) - baseline_codes
    )
