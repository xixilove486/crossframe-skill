from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
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
