from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills/crossframe-ultra/scripts"
HOST_HANDSHAKE_PATH = SCRIPTS_DIR / "ultra_runtime/host_handshake.py"
RUN_ID = "20260805T120000Z-111111111111"
NOW = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def runtime():
    if not HOST_HANDSHAKE_PATH.is_file():
        pytest.skip(f"Task 1 runtime is not implemented: {HOST_HANDSHAKE_PATH}")
    return (
        _module("host_handshake"),
        _module("paths"),
        _module("jsonio"),
        _module("constants"),
    )


@pytest.fixture
def run_layout(runtime, tmp_path: Path):
    _, paths, _, _ = runtime
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)


def _canonical_sha256(value: object) -> str:
    encoded = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _issue(host_handshake, run_layout):
    return host_handshake.issue_host_action(
        run_layout,
        action_kind="capability-attestation",
        phase_id="U0",
        parent_event_sha256=None,
        request_sha256="1" * 64,
        payload={"required_capabilities": ["filesystem", "validators"]},
        result_relative_path="work/host/U00-capability-result.json",
        now=NOW,
    )


def _write_result_for(action, jsonio, constants, *, execution_id: str):
    result = {
        "capabilities": {"filesystem": True, "validators": True},
        "execution_id": execution_id,
    }
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": constants.current_version_binding(),
        "phase_id": action.document["phase_id"],
        "action_kind": action.document["action_kind"],
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": execution_id,
        "completed_at": "2026-08-05T12:00:01Z",
    }
    receipt["receipt_sha256"] = _canonical_sha256(receipt)
    return receipt


def test_host_action_handshake_module_exists_for_red_gate() -> None:
    assert HOST_HANDSHAKE_PATH.is_file(), HOST_HANDSHAKE_PATH


def test_pending_host_action_round_trip_is_parent_bound_and_replay_safe(
    runtime, run_layout
) -> None:
    host_handshake, _, jsonio, constants = runtime
    action = _issue(host_handshake, run_layout)

    loaded = host_handshake.load_pending_action(run_layout)
    assert loaded == action
    assert json.loads(
        (run_layout.recovery_dir / "pending-action.json").read_text("utf-8")
    ) == action.document

    receipt = _write_result_for(
        action, jsonio, constants, execution_id="host-exec-1"
    )
    accepted = host_handshake.accept_host_result(
        run_layout, action=action, receipt=receipt
    )

    assert accepted.action_sha256 == action.action_sha256
    assert not (run_layout.recovery_dir / "pending-action.json").exists()
    accepted_path = (
        run_layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json"
    )
    assert json.loads(accepted_path.read_text("utf-8")) == accepted.document
    with pytest.raises(host_handshake.HostHandshakeError, match="replay|completed"):
        host_handshake.accept_host_result(
            run_layout, action=action, receipt=receipt
        )
    attempts_dir = accepted_path.parent / "attempts"
    assert len(tuple(attempts_dir.glob("*-submitted.json"))) == 2
    assert len(tuple(attempts_dir.glob("*-rejected.json"))) == 1


@pytest.mark.parametrize("mutation", ["run", "request", "parent", "slot", "hash"])
def test_host_result_cannot_select_or_reseal_its_authority(
    runtime, run_layout, mutation: str
) -> None:
    host_handshake, _, jsonio, constants = runtime
    action = _issue(host_handshake, run_layout)
    receipt = _write_result_for(
        action, jsonio, constants, execution_id="host-exec-authority"
    )
    if mutation == "run":
        receipt["run_id"] = "20260805T120001Z-222222222222"
    elif mutation == "request":
        receipt["request_sha256"] = "2" * 64
    elif mutation == "parent":
        receipt["parent_event_sha256"] = "3" * 64
    elif mutation == "slot":
        alternate = run_layout.run_dir / "work/host/U00-selected-result.json"
        jsonio.atomic_write_json(alternate, {"selected": True})
        receipt["result_relative_path"] = "work/host/U00-selected-result.json"
        receipt["result_sha256"] = hashlib.sha256(alternate.read_bytes()).hexdigest()
    else:
        receipt["action_sha256"] = "4" * 64
    receipt.pop("receipt_sha256")
    receipt["receipt_sha256"] = _canonical_sha256(receipt)

    with pytest.raises(
        host_handshake.HostHandshakeError, match="authority|action|result"
    ):
        host_handshake.accept_host_result(
            run_layout, action=action, receipt=receipt
        )

    attempts_dir = (
        run_layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "attempts"
    )
    attempts = tuple(attempts_dir.glob("*.json"))
    assert any(path.name.endswith("-submitted.json") for path in attempts)
    assert any(path.name.endswith("-rejected.json") for path in attempts)
    assert host_handshake.load_pending_action(run_layout) == action


def test_host_result_hash_and_result_bytes_must_both_match(runtime, run_layout) -> None:
    host_handshake, _, jsonio, constants = runtime
    action = _issue(host_handshake, run_layout)
    receipt = _write_result_for(
        action, jsonio, constants, execution_id="host-exec-hash"
    )

    broken_receipt = copy.deepcopy(receipt)
    broken_receipt["execution_id"] = "host-exec-resealed"
    with pytest.raises(host_handshake.HostHandshakeError, match="receipt.*hash"):
        host_handshake.accept_host_result(
            run_layout, action=action, receipt=broken_receipt
        )

    receipt = _write_result_for(
        action, jsonio, constants, execution_id="host-exec-result"
    )
    action.result_path.write_bytes(b'{"capabilities":{}}\n')
    with pytest.raises(host_handshake.HostHandshakeError, match="result.*hash"):
        host_handshake.accept_host_result(
            run_layout, action=action, receipt=receipt
        )


def test_complete_host_action_rejects_an_unvalidated_result_seal(
    runtime, run_layout
) -> None:
    host_handshake, _, jsonio, constants = runtime
    action = _issue(host_handshake, run_layout)
    receipt = _write_result_for(
        action, jsonio, constants, execution_id="host-exec-forged"
    )
    receipt["execution_id"] = "host-exec-resealed"
    forged = host_handshake.HostResultSeal(
        receipt,
        str(receipt["receipt_sha256"]),
        action.action_sha256,
    )

    with pytest.raises(
        host_handshake.HostHandshakeError, match="receipt.*hash|authority|result"
    ):
        host_handshake.complete_host_action(
            run_layout,
            action=action,
            result=forged,
        )

    assert host_handshake.load_pending_action(run_layout) == action
    assert not (
        run_layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json"
    ).exists()


def test_host_action_rejects_non_native_json_and_unsafe_result_slot(
    runtime, run_layout
) -> None:
    host_handshake, _, _, _ = runtime
    with pytest.raises((TypeError, ValueError), match="native JSON|payload"):
        host_handshake.issue_host_action(
            run_layout,
            action_kind="subagent",
            phase_id="U6",
            parent_event_sha256="a" * 64,
            request_sha256="b" * 64,
            payload={"roles": ("red-team",)},
            result_relative_path="work/host/U06-subagent-result.json",
            now=NOW,
        )
    with pytest.raises((TypeError, ValueError), match="result|safe|outside|relative"):
        host_handshake.issue_host_action(
            run_layout,
            action_kind="source-read",
            phase_id="U1",
            parent_event_sha256="a" * 64,
            request_sha256="b" * 64,
            payload={"source": "locked"},
            result_relative_path="../outside.json",
            now=NOW,
        )


def test_tampered_pending_host_action_is_not_loadable(runtime, run_layout) -> None:
    host_handshake, _, jsonio, _ = runtime
    action = _issue(host_handshake, run_layout)
    tampered = copy.deepcopy(action.document)
    tampered["request_sha256"] = "f" * 64
    jsonio.atomic_write_json(run_layout.recovery_dir / "pending-action.json", tampered)

    with pytest.raises(
        host_handshake.HostHandshakeError, match="action.*hash|authority"
    ):
        host_handshake.load_pending_action(run_layout)
