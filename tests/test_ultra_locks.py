from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier, Event

from tests.pytest_import_guard import pytest
from tests.ultra_capability_support import (
    capability_attestation_for_contract,
    default_capability_requirements,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
LOCKS_FILE = RUNTIME_DIR / "locks.py"


def _runtime_module(name: str):
    module_file = RUNTIME_DIR / f"{name}.py"
    if not module_file.is_file():
        pytest.skip(f"runtime module not implemented yet: {module_file}")
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def runtime_modules():
    return (
        _runtime_module("paths"),
        _runtime_module("jsonio"),
        _runtime_module("locks"),
    )


def _layout(paths_module, tmp_path: Path, suffix: str = "000000000001"):
    policy = paths_module.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths_module.build_run_layout(
        paths_module.RunMode.TEST,
        f"20260802T030405Z-{suffix}",
        policy,
    )


def _forged_outside_layout(paths_module, tmp_path: Path):
    run_id = "20260802T030405Z-000000000001"
    safe_root = tmp_path / "safe-root"
    run_dir = tmp_path / "outside" / "runs" / "2026" / "08" / run_id
    return paths_module.RunLayout(
        root=safe_root,
        root_staging_dir=safe_root / ".staging",
        run_dir=run_dir,
        input_dir=run_dir / "input",
        authoring_dir=run_dir / "work" / "authoring",
        artifacts_dir=run_dir / "artifacts",
        delivery_dir=run_dir / "delivery",
        validation_dir=run_dir / "validation",
        validation_current_dir=run_dir / "validation" / "current",
        validation_attempts_dir=run_dir / "validation" / "attempts",
        recovery_dir=run_dir / "recovery",
        logs_dir=run_dir / "logs",
    )


def _placeholder_lease(locks, run_id: str):
    return locks.Lease(
        run_id=run_id,
        owner_pid=os.getpid(),
        owner_nonce="f" * 24,
        acquired_at="2026-08-02T03:04:05Z",
        heartbeat_at="2026-08-02T03:04:05Z",
        expires_at="2026-08-02T03:04:35Z",
    )


def test_locks_module_exists_for_red_gate() -> None:
    assert LOCKS_FILE.is_file(), f"Task 6 lease runtime is missing: {LOCKS_FILE}"


def test_lease_dataclass_shape_and_single_writer(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)

    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))

    assert lease.run_id == layout.run_dir.name
    assert lease.owner_pid == os.getpid()
    assert lease.owner_nonce
    assert datetime.fromisoformat(lease.acquired_at.replace("Z", "+00:00")) == now
    with pytest.raises(RuntimeError, match="lease|writer|owned|live"):
        locks.acquire_run_lease(layout, now + timedelta(seconds=1), timedelta(seconds=30))


def test_different_runs_can_acquire_in_parallel(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layouts = [
        _layout(paths_module, tmp_path, "000000000001"),
        _layout(paths_module, tmp_path, "000000000002"),
    ]
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        leases = list(
            executor.map(
                lambda layout: locks.acquire_run_lease(
                    layout, now, timedelta(seconds=30)
                ),
                layouts,
            )
        )

    assert {lease.run_id for lease in leases} == {layout.run_dir.name for layout in layouts}


def test_expired_lease_with_live_pid_is_not_reclaimed(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    original = locks.acquire_run_lease(layout, now, timedelta(seconds=1))

    with pytest.raises(RuntimeError, match="live|pid|owner|lease"):
        locks.acquire_run_lease(
            layout, now + timedelta(seconds=5), timedelta(seconds=30)
        )
    assert locks._read_lease(layout) == original


def test_expired_lease_with_dead_pid_is_reclaimed_by_cas(
    runtime_modules, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    original = locks.acquire_run_lease(layout, now, timedelta(seconds=1))
    monkeypatch.setattr(locks, "_pid_exists", lambda pid: False)

    replacement = locks.acquire_run_lease(
        layout, now + timedelta(seconds=5), timedelta(seconds=30)
    )

    assert replacement.run_id == original.run_id
    assert replacement.owner_nonce != original.owner_nonce
    assert locks._read_lease(layout) == replacement


def test_heartbeat_advances_monotonically_and_preserves_ttl(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))

    heartbeat = locks.heartbeat_run_lease(
        layout, lease, now + timedelta(seconds=10)
    )

    assert heartbeat.acquired_at == lease.acquired_at
    assert datetime.fromisoformat(heartbeat.heartbeat_at.replace("Z", "+00:00")) == (
        now + timedelta(seconds=10)
    )
    assert datetime.fromisoformat(heartbeat.expires_at.replace("Z", "+00:00")) == (
        now + timedelta(seconds=40)
    )
    assert locks._read_lease(layout) == heartbeat
    with pytest.raises((TypeError, ValueError, RuntimeError), match="monotonic|after|heartbeat"):
        locks.heartbeat_run_lease(layout, heartbeat, now + timedelta(seconds=9))


def test_wrong_owner_cannot_heartbeat_or_release(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))
    impostor = replace(lease, owner_nonce="not-the-owner")

    with pytest.raises(RuntimeError, match="owner|nonce|lease"):
        locks.heartbeat_run_lease(layout, impostor, now + timedelta(seconds=1))
    with pytest.raises(RuntimeError, match="owner|nonce|lease"):
        locks.release_run_lease(layout, impostor)
    assert locks._read_lease(layout) == lease


def test_non_owner_cannot_transition_status_while_live_writer_holds_lease(
    runtime_modules,
    tmp_path: Path,
) -> None:
    paths_module, _, locks = runtime_modules
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))
    impostor = replace(lease, owner_nonce="not-the-owner")
    before = store.path.read_bytes()

    with pytest.raises(locks.LeaseOwnershipError, match="owner|nonce|lease"):
        store.transition(
            created,
            "running",
            now + timedelta(seconds=1),
            lease=impostor,
        )

    assert store.path.read_bytes() == before
    assert locks._read_lease(layout) == lease


def test_status_transition_without_supplied_lease_owns_one_during_commit(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_module, _, locks = runtime_modules
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    observed_owner = []
    real_atomic_write_json = status_module.atomic_write_json

    def observe_status_commit(path: Path, value: object) -> None:
        if isinstance(value, dict) and value.get("status") == "running":
            observed_owner.append(locks._read_lease(layout))
        real_atomic_write_json(path, value)

    monkeypatch.setattr(status_module, "atomic_write_json", observe_status_commit)
    running = store.transition(
        created,
        "running",
        now + timedelta(seconds=1),
    )

    assert running.status == "running"
    assert len(observed_owner) == 1
    assert observed_owner[0].run_id == layout.run_dir.name
    assert not locks._lease_path(layout).exists()


def test_cancel_intent_is_persisted_without_waiting_for_live_writer(
    runtime_modules,
    tmp_path: Path,
) -> None:
    paths_module, _, locks = runtime_modules
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    store.transition(created, "running", now + timedelta(seconds=1))
    lease = locks.acquire_run_lease(
        layout,
        now + timedelta(seconds=2),
        timedelta(seconds=30),
    )

    intent = locks.request_cancel(
        layout,
        reason="operator requested cancellation",
        now=now + timedelta(seconds=3),
    )

    assert intent.run_id == layout.run_dir.name
    assert locks.load_cancel_intent(layout) == intent
    assert locks._read_lease(layout) == lease
    with pytest.raises(locks.CancelledRunError, match="cancel"):
        locks.heartbeat_run_lease(
            layout,
            lease,
            now + timedelta(seconds=4),
        )
    assert locks._read_lease(layout) == lease


def test_cancel_intent_blocks_owner_status_mutation_until_cancel_converges(
    runtime_modules,
    tmp_path: Path,
) -> None:
    paths_module, _, locks = runtime_modules
    recovery = _runtime_module("recovery")
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    running = store.transition(created, "running", now + timedelta(seconds=1))
    writer = locks.acquire_run_lease(
        layout,
        now + timedelta(seconds=2),
        timedelta(minutes=5),
    )
    try:
        locks.request_cancel(
            layout,
            reason="operator requested cancellation",
            now=now + timedelta(seconds=3),
        )

        with pytest.raises(locks.CancelledRunError, match="cancel intent"):
            store.transition(
                running,
                "blocked",
                now + timedelta(seconds=4),
                reason="owner attempted to continue after cancellation",
                lease=writer,
            )

        with pytest.raises(locks.CancelledRunError, match="cancel intent"):
            store.transition(
                running,
                "cancelled",
                now + timedelta(seconds=4),
                reason="owner attempted to bypass cancellation convergence",
                lease=writer,
            )

        converged = recovery.converge_cancel_if_requested(
            layout,
            lease=writer,
            now=now + timedelta(seconds=5),
        )
    finally:
        locks.release_run_lease(layout, writer)

    assert converged is not None
    assert converged.status == "cancelled"
    assert store.read() == converged


def test_status_commit_serializes_with_cancel_intent_creation(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_module, _, locks = runtime_modules
    recovery = _runtime_module("recovery")
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    running = store.transition(created, "running", now + timedelta(seconds=1))
    writer = locks.acquire_run_lease(
        layout,
        now + timedelta(seconds=2),
        timedelta(minutes=5),
    )
    status_write_started = Event()
    allow_status_write = Event()
    cancel_started = Event()
    cancel_finished = Event()
    original_write = status_module.atomic_write_json

    def pause_status_write(path: Path, value: object) -> None:
        if isinstance(value, dict) and value.get("status") == "blocked":
            status_write_started.set()
            if not allow_status_write.wait(timeout=5):
                raise TimeoutError("test did not release status CAS")
        original_write(path, value)

    def request_cancel():
        cancel_started.set()
        try:
            return locks.request_cancel(
                layout,
                reason="cancel at status CAS boundary",
                now=now + timedelta(seconds=3),
            )
        finally:
            cancel_finished.set()

    monkeypatch.setattr(status_module, "atomic_write_json", pause_status_write)
    executor = ThreadPoolExecutor(max_workers=2)
    status_future = executor.submit(
        store.transition,
        running,
        "blocked",
        now + timedelta(seconds=4),
        reason="blocked before cancellation linearized",
        lease=writer,
    )
    cancel_future = None
    try:
        assert status_write_started.wait(timeout=2)
        cancel_future = executor.submit(request_cancel)
        assert cancel_started.wait(timeout=2)
        assert not cancel_finished.wait(timeout=0.3), (
            "cancel intent crossed status CAS in progress"
        )
    finally:
        allow_status_write.set()
        executor.shutdown(wait=True)

    try:
        blocked = status_future.result()
        assert blocked.status == "blocked"
        assert cancel_future is not None
        assert cancel_future.result().run_id == layout.run_dir.name
        converged = recovery.converge_cancel_if_requested(
            layout,
            lease=writer,
            now=now + timedelta(seconds=5),
        )
    finally:
        locks.release_run_lease(layout, writer)

    assert converged is not None
    assert converged.status == "cancelled"


def test_phase_commit_rechecks_cancel_intent_before_appending_event(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_module, _, locks = runtime_modules
    constants = _runtime_module("constants")
    state_machine = _runtime_module("state_machine")
    layout = _layout(paths_module, tmp_path)
    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    request_sha256 = "1" * 64
    binding = constants.current_version_binding()
    run_contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-02T03:04:05Z",
        "capabilities": default_capability_requirements(),
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }
    attestation = capability_attestation_for_contract(
        run_id=layout.run_dir.name,
        version_binding=binding,
        contract=run_contract,
        generated_at="2026-08-02T03:04:05Z",
    )
    run_contract["capability_attestation_sha256"] = attestation.artifact_sha256
    store = state_machine.PhaseStore(
        run_id=layout.run_dir.name,
        version_binding=binding,
        source_sha256="2" * 64,
        input_artifact_hashes=(request_sha256,),
        input_snapshot_sha256=request_sha256,
        evidence_cutoff="2026-08-02T03:04:05Z",
        now=now,
        run_contract=run_contract,
        capability_attestation=attestation,
        source_repository=REPO_ROOT,
        run_layout=layout,
    )
    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))
    locks.request_cancel(
        layout,
        reason="operator requested cancellation",
        now=now + timedelta(seconds=1),
    )

    with pytest.raises(locks.CancelledRunError, match="cancel"):
        store.complete(
            "U0",
            artifact_hashes=(store.run_contract_artifact_sha256,),
        )

    assert store.events == ()
    assert locks._read_lease(layout) == lease


def test_release_removes_only_the_current_owner_lease(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))

    locks.release_run_lease(layout, lease)

    assert not locks._lease_path(layout).exists()
    next_lease = locks.acquire_run_lease(
        layout, now + timedelta(seconds=1), timedelta(seconds=30)
    )
    assert next_lease.owner_nonce != lease.owner_nonce


def test_cancelled_status_rejects_lease_acquisition(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(base)
    cancelled = store.transition(
        created,
        "cancelled",
        base + timedelta(seconds=1),
        reason="cancelled",
    )
    assert cancelled.tools_allowed is False

    with pytest.raises(RuntimeError, match="cancelled"):
        locks.acquire_run_lease(
            layout,
            datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
            timedelta(seconds=30),
        )


def test_status_only_cancellation_forgery_is_rejected_as_corrupt_authority(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    layout.run_dir.mkdir(parents=True)
    jsonio.atomic_write_json(
        layout.run_dir / "run-status.json", {"status": "cancelled"}
    )

    with pytest.raises(locks.LeaseNeedsAttentionError) as caught:
        locks.acquire_run_lease(
            layout,
            datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
            timedelta(seconds=30),
        )

    assert not isinstance(caught.value, locks.CancelledRunError)
    assert not locks._lease_path(layout).exists()


@pytest.mark.parametrize("operation", ["acquire", "heartbeat"])
def test_cancel_transition_serializes_with_lease_admission_and_heartbeat(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    paths_module, _, locks = runtime_modules
    status_module = _runtime_module("status")
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store = status_module.RunStatusStore(layout)
    created = store.create(now)
    running = store.transition(created, "running", now + timedelta(seconds=1))
    lease = None
    if operation == "heartbeat":
        lease = locks.acquire_run_lease(
            layout, now + timedelta(seconds=2), timedelta(seconds=30)
        )

    cancellation_reached_commit = Event()
    allow_cancellation_commit = Event()
    lease_operation_finished = Event()
    real_atomic_write_json = status_module.atomic_write_json

    def pause_cancel_commit(path: Path, value: object) -> None:
        if isinstance(value, dict) and value.get("status") == "cancelled":
            cancellation_reached_commit.set()
            if not allow_cancellation_commit.wait(timeout=5):
                raise TimeoutError("test did not release the cancelled status commit")
        real_atomic_write_json(path, value)

    def attempt_lease_operation():
        try:
            if operation == "acquire":
                return locks.acquire_run_lease(
                    layout,
                    now + timedelta(seconds=2),
                    timedelta(seconds=30),
                )
            assert lease is not None
            return locks.heartbeat_run_lease(
                layout, lease, now + timedelta(seconds=3)
            )
        except BaseException as error:
            return error
        finally:
            lease_operation_finished.set()

    monkeypatch.setattr(status_module, "atomic_write_json", pause_cancel_commit)
    executor = ThreadPoolExecutor(max_workers=2)
    cancel_future = executor.submit(
        store.transition,
        running,
        "cancelled",
        now + timedelta(seconds=4),
        **({"lease": lease} if lease is not None else {}),
    )
    operation_future = None
    try:
        assert cancellation_reached_commit.wait(timeout=2)
        operation_future = executor.submit(attempt_lease_operation)
        assert not lease_operation_finished.wait(timeout=0.3), (
            "lease operation crossed a cancelled-status commit in progress"
        )
    finally:
        allow_cancellation_commit.set()
        executor.shutdown(wait=True)

    cancelled = cancel_future.result()
    assert operation_future is not None
    result = operation_future.result()
    assert cancelled.status == "cancelled"
    assert isinstance(result, locks.CancelledRunError)
    if operation == "acquire":
        assert not locks._lease_path(layout).exists()
    else:
        assert lease is not None
        assert locks._read_lease(layout) == lease


def test_bad_lease_json_requires_attention_and_is_not_overwritten(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    layout.run_dir.mkdir(parents=True)
    lease_path = locks._lease_path(layout)
    lease_path.write_bytes(b"{not-json")

    with pytest.raises(RuntimeError, match="attention|corrupt|invalid|lease"):
        locks.acquire_run_lease(
            layout,
            datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
            timedelta(seconds=30),
        )
    assert lease_path.read_bytes() == b"{not-json"


@pytest.mark.parametrize(
    "noncanonical",
    [
        "2026-08-02T03:04:05+00:00",
        "2026-08-02\u202803:04:05Z",
        "2026-08-02T03:04:05.0Z",
        "2026-08-02T03:04:05Z\n",
        "2026-08-02T03:04:05Z\x00",
    ],
)
def test_lease_rejects_noncanonical_or_control_bearing_utc_timestamps(
    runtime_modules, tmp_path: Path, noncanonical: str
) -> None:
    paths_module, jsonio, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    locks.acquire_run_lease(layout, now, timedelta(seconds=30))
    lease_path = locks._lease_path(layout)
    value = jsonio.load_json_object(lease_path)
    value["acquired_at"] = noncanonical
    jsonio.atomic_write_json(lease_path, value)

    with pytest.raises(
        (TypeError, ValueError, RuntimeError), match="canonical|timestamp|UTC|lease"
    ):
        locks._read_lease(layout)


@pytest.mark.parametrize(
    ("now", "ttl"),
    [
        (datetime(2026, 8, 2, 3, 4, 5), timedelta(seconds=30)),
        (
            datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=8))),
            timedelta(seconds=30),
        ),
        (datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc), timedelta(0)),
        (datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc), timedelta(seconds=-1)),
    ],
)
def test_acquire_rejects_invalid_clock_or_ttl(runtime_modules, tmp_path: Path, now, ttl) -> None:
    paths_module, _, locks = runtime_modules
    with pytest.raises((TypeError, ValueError)):
        locks.acquire_run_lease(_layout(paths_module, tmp_path), now, ttl)


@pytest.mark.parametrize("operation", ["acquire", "heartbeat", "release"])
def test_lease_operations_reject_forged_layout_outside_selected_root_before_io(
    runtime_modules, tmp_path: Path, operation: str
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _forged_outside_layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    lease = _placeholder_lease(locks, layout.run_dir.name)
    guard_path = layout.run_dir / locks.LEASE_LOCK_FILENAME

    with pytest.raises(
        (ValueError, RuntimeError), match="outside|selected root|descendant|contain"
    ):
        if operation == "acquire":
            locks.acquire_run_lease(layout, now, timedelta(seconds=30))
        elif operation == "heartbeat":
            locks.heartbeat_run_lease(layout, lease, now + timedelta(seconds=1))
        else:
            locks.release_run_lease(layout, lease)

    assert not layout.run_dir.exists()
    assert not guard_path.exists()


@pytest.mark.parametrize("operation", ["acquire", "heartbeat", "release"])
def test_lease_operations_recheck_reparse_ancestors_after_layout_construction(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    reparse_parent = layout.run_dir.parent
    reparse_parent.mkdir(parents=True)
    lease_path = layout.run_dir / locks.LEASE_FILENAME
    guard_path = layout.run_dir / locks.LEASE_LOCK_FILENAME
    lease = None
    if operation != "acquire":
        lease = locks.acquire_run_lease(layout, now, timedelta(seconds=30))
    original_lease_bytes = lease_path.read_bytes() if lease_path.exists() else None
    real_is_reparse_point = paths_module._is_reparse_point

    def simulated_reparse(path: Path) -> bool:
        return Path(path) == reparse_parent or real_is_reparse_point(Path(path))

    monkeypatch.setattr(paths_module, "_is_reparse_point", simulated_reparse)
    with pytest.raises((ValueError, RuntimeError), match="reparse|symlink|junction"):
        if operation == "acquire":
            locks.acquire_run_lease(layout, now, timedelta(seconds=30))
        elif operation == "heartbeat":
            assert lease is not None
            locks.heartbeat_run_lease(layout, lease, now + timedelta(seconds=1))
        else:
            assert lease is not None
            locks.release_run_lease(layout, lease)

    if operation == "acquire":
        assert not lease_path.exists()
        assert not guard_path.exists()
    else:
        assert lease_path.read_bytes() == original_lease_bytes


def test_concurrent_acquisition_has_exactly_one_winner(runtime_modules, tmp_path: Path) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    barrier = Barrier(12)

    def contender():
        barrier.wait()
        try:
            return locks.acquire_run_lease(layout, now, timedelta(seconds=30))
        except RuntimeError:
            return None

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: contender(), range(12)))

    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    assert locks._read_lease(layout) == winners[0]


def test_subprocess_lease_contention_has_exactly_one_writer(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, locks = runtime_modules
    layout = _layout(paths_module, tmp_path)
    gate = tmp_path / "lease-subprocess.gate"
    child_code = """
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import time

sys.path.insert(0, sys.argv[1])
from ultra_runtime.locks import acquire_run_lease
from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

policy = RootPolicy(Path(sys.argv[2]), Path(sys.argv[3]))
layout = build_run_layout(RunMode.TEST, sys.argv[4], policy)
gate = Path(sys.argv[5])
deadline = time.monotonic() + 10
while not gate.exists():
    if time.monotonic() >= deadline:
        raise TimeoutError("subprocess lease gate was not released")
    time.sleep(0.005)
try:
    lease = acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(seconds=30),
    )
except RuntimeError:
    print("conflict", flush=True)
else:
    print("winner:" + lease.owner_nonce, flush=True)
"""
    command = [
        sys.executable,
        "-B",
        "-c",
        child_code,
        str(SCRIPTS_DIR),
        str(tmp_path / "production"),
        str(tmp_path / "test"),
        layout.run_dir.name,
        str(gate),
    ]
    processes = [
        subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(8)
    ]
    outputs = []
    try:
        gate.write_bytes(b"go\n")
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            assert process.returncode == 0, stderr
            outputs.append(stdout.strip())
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    winners = [output for output in outputs if output.startswith("winner:")]
    assert len(winners) == 1
    assert outputs.count("conflict") == 7
    persisted = locks._read_lease(layout)
    assert winners[0] == f"winner:{persisted.owner_nonce}"
