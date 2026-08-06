from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
CLI_PATH = SCRIPTS / "crossframe_ultra_runtime.py"
NOW = datetime(2026, 8, 5, 18, 0, tzinfo=timezone.utc)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _module(name: str):
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


def _load_cli():
    spec = importlib.util.spec_from_file_location("task2_ultra_cli", CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root_policy(tmp_path: Path):
    paths = _module("paths")
    return paths.RootPolicy(tmp_path / "production", tmp_path / "test")


def _capability_result(*, network: str = "unavailable") -> dict[str, object]:
    return {
        "measured_availability": {
            "filesystem": "available",
            "docx_parser": "unavailable",
            "network": network,
            "retrieval": network,
            "validators": "available",
            "subagents": "unavailable",
            "model_context": "available",
        },
        "providers": [
            {
                "provider_id": "codex-runtime",
                "provider_kind": "runtime",
                "version": "1.0.0",
            }
        ],
        "tools": [
            {
                "tool_id": "local-filesystem",
                "provider_id": "codex-runtime",
                "version": "1.0.0",
            }
        ],
        "measured_at": "2026-08-05T18:00:02Z",
        "proof_grade": "host-measured",
    }


def _accept_capability_result(
    layout,
    action,
    result: dict[str, object],
    *,
    completed_at: str = "2026-08-05T18:00:03Z",
):
    host_handshake = _module("host_handshake")
    jsonio = _module("jsonio")
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": action.document["version_binding"],
        "phase_id": action.document["phase_id"],
        "action_kind": action.document["action_kind"],
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": "task-2-capability-host",
        "completed_at": completed_at,
    }
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()
    return host_handshake.accept_host_result(
        layout,
        action=action,
        receipt=receipt,
    )


@pytest.fixture
def fresh_run(tmp_path: Path):
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    stdout = StringIO()
    cli.execute(
        ["start", "--repo", str(ROOT), "--mode", "test", "--request-stdin"],
        stdin=BytesIO("AI 会怎样改变就业？\n".encode("utf-8")),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: NOW,
        entropy=lambda: b"task-2-foundation",
    )
    run_id = json.loads(stdout.getvalue())["run_id"]
    paths = _module("paths")
    layout = paths.build_run_layout(paths.RunMode.TEST, run_id, policy)
    return SimpleNamespace(layout=layout, repo=ROOT, now=NOW + timedelta(seconds=1))


def test_plain_natural_language_defaults_to_open_world_profile() -> None:
    foundation = _module("foundation")

    profile = foundation.parse_request_profile(
        "AI 会怎样改变就业？\n".encode("utf-8")
    )

    assert profile.analysis_kind == "open-world"
    assert profile.claim == "AI 会怎样改变就业？"
    assert profile.material_inventory == ()
    assert profile.material_universe_sha256 is None


def test_closed_input_profile_cannot_copy_claim_into_material_universe() -> None:
    foundation = _module("foundation")
    request = _canonical(
        {
            "analysis_kind": "closed-input",
            "claim": "AI 会怎样改变就业？",
            "material": "AI 会怎样改变就业？",
        }
    )

    with pytest.raises(
        foundation.FoundationInputError,
        match="material universe|same as claim",
    ):
        foundation.parse_request_profile(request)


def test_u0_waits_for_host_capability_attestation_instead_of_blocking_plain_text(
    fresh_run,
) -> None:
    foundation = _module("foundation")

    progress = foundation.advance_u0(
        fresh_run.layout,
        repo=fresh_run.repo,
        now=fresh_run.now,
    )

    assert progress.outcome == "awaiting-host-action"
    assert progress.phase_store is None
    assert progress.pending_action is not None
    assert progress.pending_action.document["action_kind"] == "capability-attestation"


def test_host_capability_attestation_advances_u0_with_measured_availability(
    fresh_run,
) -> None:
    foundation = _module("foundation")
    first = foundation.advance_u0(
        fresh_run.layout,
        repo=fresh_run.repo,
        now=fresh_run.now,
    )
    assert first.pending_action is not None
    _accept_capability_result(
        fresh_run.layout,
        first.pending_action,
        _capability_result(),
    )

    progress = foundation.advance_u0(
        fresh_run.layout,
        repo=fresh_run.repo,
        now=fresh_run.now + timedelta(seconds=3),
    )

    assert progress.outcome == "advanced"
    assert progress.completed_phase == "U0"
    assert progress.pending_action is None
    assert progress.phase_store.current_phase == "U0"
    assert progress.phase_store.capability_availability["network"] == "unavailable"
    assert progress.phase_store.run_contract["capabilities"]["network"] == "required"
    assert progress.phase_store.run_contract["analysis_kind"] == "open-world"
    attestation_path = (
        fresh_run.layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json"
    )
    attestation_sha256 = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
    assert (
        progress.phase_store.run_contract["capability_attestation_sha256"]
        == attestation_sha256
    )
    assert (
        fresh_run.layout.artifacts_dir / "ultra-run-contract.json"
    ).is_file()


def test_host_capability_result_cannot_submit_runtime_owned_attestation_fields(
    fresh_run,
) -> None:
    foundation = _module("foundation")
    first = foundation.advance_u0(
        fresh_run.layout,
        repo=fresh_run.repo,
        now=fresh_run.now,
    )
    assert first.pending_action is not None
    result = _capability_result()
    result["run_id"] = fresh_run.layout.run_dir.name
    _accept_capability_result(fresh_run.layout, first.pending_action, result)

    with pytest.raises(
        foundation.FoundationInputError,
        match="runtime-owned|host capability result",
    ):
        foundation.advance_u0(
            fresh_run.layout,
            repo=fresh_run.repo,
            now=fresh_run.now + timedelta(seconds=3),
        )


def test_material_files_are_copied_into_an_anonymous_profile_inventory(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    foundation = _module("foundation")
    policy = _root_policy(tmp_path)
    source = tmp_path / "private-name.md"
    source.write_text("封闭材料", encoding="utf-8")
    stdout = StringIO()

    cli.execute(
        [
            "start",
            "--repo",
            str(ROOT),
            "--mode",
            "test",
            "--request-stdin",
            "--material-file",
            str(source),
        ],
        stdin=BytesIO("问题".encode("utf-8")),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: NOW,
        entropy=lambda: b"task-2-material-inventory",
    )
    run_id = json.loads(stdout.getvalue())["run_id"]
    paths = _module("paths")
    layout = paths.build_run_layout(paths.RunMode.TEST, run_id, policy)

    inventory = foundation.load_input_inventory(layout)
    assert [item["path"] for item in inventory["materials"]] == [
        "materials/MAT-0001.md"
    ]
    assert all(
        item["path"] not in {"request.bin", "request-metadata.json"}
        for item in inventory["materials"]
    )
    assert "private-name" not in _canonical(inventory).decode("utf-8")
    copied = layout.input_dir / inventory["materials"][0]["path"]
    assert copied.read_bytes() == source.read_bytes()
    assert inventory["materials"][0]["sha256"] == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()


def test_closed_input_profile_material_is_sealed_outside_request_authority(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    request_bytes = _canonical(
        {
            "analysis_kind": "closed-input",
            "claim": "判断材料是否支持结论",
            "material": "独立封存的材料正文",
        }
    )
    stdout = StringIO()

    cli.execute(
        ["start", "--repo", str(ROOT), "--mode", "test", "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: NOW,
        entropy=lambda: b"task-2-closed-material",
    )
    run_id = json.loads(stdout.getvalue())["run_id"]
    paths = _module("paths")
    layout = paths.build_run_layout(paths.RunMode.TEST, run_id, policy)

    inventory = _module("foundation").load_input_inventory(layout)
    assert [item["path"] for item in inventory["materials"]] == [
        "materials/MAT-0001.txt"
    ]
    assert (
        layout.input_dir / "materials/MAT-0001.txt"
    ).read_text("utf-8") == "独立封存的材料正文"
    assert (layout.input_dir / "request.bin").read_bytes() == request_bytes


@pytest.fixture
def task3_fresh_u0(fresh_run, tmp_path: Path, monkeypatch):
    foundation = _module("foundation")
    source_integrity = _module("source_integrity")
    from tests.test_ultra_source_read_coverage import _write_release_manifest

    authority_repo = tmp_path / "task3-authority-repo"
    skill_root = authority_repo / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", skill_root)
    release_path = skill_root / "references/release-manifest.json"
    _write_release_manifest(authority_repo, release_path)

    monkeypatch.setattr(
        source_integrity,
        "PRODUCTION_ROOT",
        fresh_run.layout.root.parent / "production",
    )
    first = foundation.advance_u0(
        fresh_run.layout,
        repo=authority_repo,
        now=fresh_run.now,
    )
    assert first.pending_action is not None
    _accept_capability_result(
        fresh_run.layout,
        first.pending_action,
        _capability_result(network="available"),
    )
    completed = foundation.advance_u0(
        fresh_run.layout,
        repo=authority_repo,
        now=fresh_run.now + timedelta(seconds=3),
    )
    assert completed.phase_store is not None
    assert completed.phase_store.current_phase == "U0"
    return SimpleNamespace(
        layout=fresh_run.layout,
        repo=authority_repo,
        now=fresh_run.now + timedelta(seconds=4),
    )


def _task3_source_read_item(
    *,
    action_sha256: str,
    read_plan_sha256: str,
    reader_mode: str,
    execution_id: str,
    read_at: str,
    source_unit_id: str,
    source_unit_sha256: str,
) -> dict[str, str]:
    payload = {
        "receipt_type": "crossframe.ultra.v82.host-source-read",
        "action_sha256": action_sha256,
        "read_plan_sha256": read_plan_sha256,
        "reader_mode": reader_mode,
        "execution_id": execution_id,
        "read_at": read_at,
        "source_unit_id": source_unit_id,
        "source_unit_sha256": source_unit_sha256,
    }
    return {
        "source_unit_id": source_unit_id,
        "source_unit_sha256": source_unit_sha256,
        "receipt_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
    }


def _accept_task3_source_read(layout, action, *, batch_ordinal: int) -> int:
    host_handshake = _module("host_handshake")
    jsonio = _module("jsonio")
    payload = action.document["payload"]
    assert isinstance(payload, dict)
    source_units = payload["source_units"]
    assert isinstance(source_units, list)
    execution_id = f"host-reader-{batch_ordinal:06d}"
    read_at = f"2026-08-05T18:{batch_ordinal // 60:02d}:{batch_ordinal % 60:02d}Z"
    items = [
        _task3_source_read_item(
            action_sha256=action.action_sha256,
            read_plan_sha256=str(payload["read_plan_sha256"]),
            reader_mode=str(payload["reader_mode"]),
            execution_id=execution_id,
            read_at=read_at,
            source_unit_id=str(unit["source_unit_id"]),
            source_unit_sha256=str(unit["source_unit_sha256"]),
        )
        for unit in source_units
    ]
    result = {
        "schema_id": "crossframe.ultra.v82.source-read-result",
        "schema_version": 1,
        "action_sha256": action.action_sha256,
        "read_plan_sha256": payload["read_plan_sha256"],
        "reader_mode": payload["reader_mode"],
        "execution_id": execution_id,
        "read_at": read_at,
        "items": items,
    }
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": action.document["version_binding"],
        "phase_id": "U1",
        "action_kind": "source-read",
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": execution_id,
        "completed_at": read_at,
    }
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()
    host_handshake.accept_host_result(layout, action=action, receipt=receipt)
    return len(items)


def test_task3_u1_persists_plan_before_requesting_host_reads(task3_fresh_u0) -> None:
    foundation = _module("foundation")
    jsonio = _module("jsonio")
    schemas = _module("schemas")

    progress = foundation.advance_foundation(
        task3_fresh_u0.layout,
        repo=task3_fresh_u0.repo,
        now=task3_fresh_u0.now,
    )

    assert progress.outcome == "awaiting-host-action"
    assert progress.pending_action is not None
    assert progress.pending_action.document["action_kind"] == "source-read"
    plan_path = task3_fresh_u0.layout.recovery_dir / "u1-authority/read-plan.json"
    plan = jsonio.load_json_object(plan_path)
    schemas.validate_instance("ultra-read-plan.schema.json", plan)
    assert plan["source_unit_count"] == 4_753
    assert len(plan["source_units"]) == 4_753
    assert plan["request_sha256"] == progress.pending_action.document["request_sha256"]
    assert progress.pending_action.document["payload"]["read_plan_sha256"] == (
        hashlib.sha256(plan_path.read_bytes()).hexdigest()
    )
    assert 0 < progress.pending_action.document["payload"]["source_unit_count"] < 4_753
    assert not (
        task3_fresh_u0.layout.artifacts_dir
        / "U00-U03-evidence/ultra-read-events.jsonl"
    ).exists()


def test_task3_u1_partial_batches_resume_and_seal_three_distinct_hashes(
    task3_fresh_u0,
) -> None:
    foundation = _module("foundation")
    jsonio = _module("jsonio")
    recovery = _module("recovery")

    progress = foundation.advance_foundation(
        task3_fresh_u0.layout,
        repo=task3_fresh_u0.repo,
        now=task3_fresh_u0.now,
    )
    plan_path = task3_fresh_u0.layout.recovery_dir / "u1-authority/read-plan.json"
    original_plan_bytes = plan_path.read_bytes()
    admitted = 0
    for batch_ordinal in range(1, 32):
        assert progress.pending_action is not None
        admitted += _accept_task3_source_read(
            task3_fresh_u0.layout,
            progress.pending_action,
            batch_ordinal=batch_ordinal,
        )
        progress = foundation.advance_foundation(
            task3_fresh_u0.layout,
            repo=task3_fresh_u0.repo,
            now=task3_fresh_u0.now + timedelta(seconds=batch_ordinal),
        )
        if progress.completed_phase == "U1":
            break
        assert progress.outcome == "awaiting-host-action"
    else:
        pytest.fail("U1 did not finish its bounded read batches")

    assert admitted == 4_753
    assert progress.phase_store is not None
    assert progress.phase_store.current_phase == "U1"
    assert plan_path.read_bytes() == original_plan_bytes
    events = progress.phase_store.events
    outputs = events[-1]["output_artifact_hashes"]
    assert len(outputs) == len(set(outputs)) == 3
    checkpoint = next(
        item
        for item in recovery.load_checkpoints(task3_fresh_u0.layout)
        if item["phase_id"] == "U1"
    )
    assert [item["path"] for item in checkpoint["artifact_hashes"]] == [
        "recovery/u1-authority/source-lock.json",
        "recovery/u1-authority/read-plan.json",
        "recovery/u1-authority/source-coverage.json",
    ]
    assert [item["sha256"] for item in checkpoint["artifact_hashes"]] == outputs
    read_events_path = (
        task3_fresh_u0.layout.artifacts_dir
        / "U00-U03-evidence/ultra-read-events.jsonl"
    )
    assert len(read_events_path.read_bytes().splitlines()) == 4_753
    coverage = jsonio.load_json_object(
        task3_fresh_u0.layout.recovery_dir / "u1-authority/source-coverage.json"
    )
    assert coverage["source_unit_count"] == 4_753
    assert coverage["read_plan_sha256"] == outputs[1]
    resumed = recovery.resume_run(
        task3_fresh_u0.layout,
        now=task3_fresh_u0.now + timedelta(minutes=1),
        source_repository=task3_fresh_u0.repo,
    )
    assert resumed.checkpoint is not None
    assert resumed.checkpoint["phase_id"] == "U1"
    assert resumed.phase_store is not None
    assert resumed.phase_store.current_phase == "U1"
    assert resumed.phase_store.events[-1]["output_artifact_hashes"] == outputs


@pytest.mark.parametrize("mutation", ("missing", "rebound"))
def test_task3_u1_partial_resume_rejects_missing_or_tampered_plan(
    task3_fresh_u0,
    mutation: str,
) -> None:
    foundation = _module("foundation")
    jsonio = _module("jsonio")

    progress = foundation.advance_foundation(
        task3_fresh_u0.layout,
        repo=task3_fresh_u0.repo,
        now=task3_fresh_u0.now,
    )
    assert progress.pending_action is not None
    _accept_task3_source_read(
        task3_fresh_u0.layout,
        progress.pending_action,
        batch_ordinal=1,
    )
    plan_path = task3_fresh_u0.layout.recovery_dir / "u1-authority/read-plan.json"
    if mutation == "missing":
        plan_path.unlink()
    else:
        plan = jsonio.load_json_object(plan_path)
        plan["batch_size"] = int(plan["batch_size"]) - 1
        plan["content_sha256"] = "0" * 64
        plan["content_sha256"] = hashlib.sha256(
            _canonical({key: value for key, value in plan.items() if key != "content_sha256"})
        ).hexdigest()
        jsonio.atomic_write_json(plan_path, plan)

    with pytest.raises(foundation.FoundationInputError, match="read plan|U1"):
        foundation.advance_foundation(
            task3_fresh_u0.layout,
            repo=task3_fresh_u0.repo,
            now=task3_fresh_u0.now + timedelta(seconds=1),
        )


def test_task3_u1_final_seal_rechecks_unrelated_source_tree_bytes_after_restart(
    task3_fresh_u0,
) -> None:
    foundation = _module("foundation")

    progress = foundation.advance_foundation(
        task3_fresh_u0.layout,
        repo=task3_fresh_u0.repo,
        now=task3_fresh_u0.now,
    )
    for batch_ordinal in range(1, 32):
        assert progress.pending_action is not None
        payload = progress.pending_action.document["payload"]
        _accept_task3_source_read(
            task3_fresh_u0.layout,
            progress.pending_action,
            batch_ordinal=batch_ordinal,
        )
        if (
            int(payload["batch_ordinal"]) * 512
            >= 4_753
        ):
            unrelated = (
                task3_fresh_u0.repo
                / "skills/crossframe-ultra/references/v8.2-full-source/00-source-envelope.md"
            )
            unrelated.write_bytes(unrelated.read_bytes() + b"\n")
            with pytest.raises(
                foundation.FoundationInputError,
                match="final U1|disk authority|source",
            ):
                foundation.advance_foundation(
                    task3_fresh_u0.layout,
                    repo=task3_fresh_u0.repo,
                    now=task3_fresh_u0.now + timedelta(seconds=batch_ordinal),
                )
            phase_events_path = (
                task3_fresh_u0.layout.recovery_dir / "phase-events.jsonl"
            )
            phase_events = [
                json.loads(line)
                for line in phase_events_path.read_text(encoding="utf-8").splitlines()
            ]
            assert not any(event.get("phase_id") == "U1" for event in phase_events)
            return
        progress = foundation.advance_foundation(
            task3_fresh_u0.layout,
            repo=task3_fresh_u0.repo,
            now=task3_fresh_u0.now + timedelta(seconds=batch_ordinal),
        )
    pytest.fail("U1 did not reach its final source-tree recheck")
