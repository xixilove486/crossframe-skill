from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import gc
import importlib
import json
from pathlib import Path
import subprocess
import sys
from threading import Barrier, Event

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
STATUS_AUTHORITY_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "content_sha256",
        "phase_id",
        "status",
        "previous_status",
        "current_phase",
        "last_complete_phase",
        "reason",
        "tools_allowed",
        "validation_passed",
        "updated_at",
        "created_at",
        "revision",
    }
)
INDEX_PROJECTION_FIELDS = frozenset(
    {"run_id", "status", "created_at", "updated_at", "revision"}
)


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
def jsonio():
    return _runtime_module("jsonio")


@pytest.fixture
def runtime_modules():
    return (
        _runtime_module("paths"),
        _runtime_module("jsonio"),
        _runtime_module("status"),
        _runtime_module("indexes"),
    )


def _layout(paths_module, root: Path, run_id: str):
    policy = paths_module.RootPolicy(root / "production", root / "test")
    return paths_module.build_run_layout(paths_module.RunMode.TEST, run_id, policy)


def _create_status(status_module, layout, now: datetime):
    store = status_module.RunStatusStore(layout)
    return store, store.create(now)


def _rehash_status(value: dict[str, object]) -> dict[str, object]:
    schemas = _runtime_module("schemas")
    value["content_sha256"] = schemas.compute_artifact_content_sha256(value)
    return value


def test_status_index_and_json_modules_exist_for_red_gate() -> None:
    expected = [RUNTIME_DIR / name for name in ("jsonio.py", "status.py", "indexes.py")]
    missing = [path for path in expected if not path.is_file()]
    assert not missing, f"Task 6 authority/cache modules are missing: {missing}"


def test_canonical_json_bytes_and_digest_are_exact(jsonio) -> None:
    payload = {"z": 1, "汉": "字", "a": [True, None]}
    encoded = jsonio.canonical_json_bytes(payload)
    assert encoded == '{"a":[true,null],"z":1,"汉":"字"}\n'.encode("utf-8")
    assert jsonio.sha256_bytes(encoded) == (
        "8e4b97656db32255225abfad51fb2faa59a809fba3f0ed09c57bbe36f52d927e"
    )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"[]\n", "object"),
        (b"\xff", "utf-8|UTF-8"),
        (b"{bad json", "json|JSON"),
    ],
)
def test_load_json_object_rejects_non_object_and_malformed_input(
    jsonio, tmp_path: Path, content: bytes, message: str
) -> None:
    target = tmp_path / "bad.json"
    target.write_bytes(content)
    with pytest.raises((TypeError, ValueError), match=message):
        jsonio.load_json_object(target)


def test_atomic_write_failure_preserves_target_and_cleans_own_temporary(
    jsonio, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old\n")

    def fail_replace(source, destination):
        raise OSError("injected replace failure")

    monkeypatch.setattr(jsonio.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected"):
        jsonio.atomic_write_bytes(target, b"new\n")

    assert target.read_bytes() == b"old\n"
    assert list(tmp_path.glob(f".{target.name}.tmp-*")) == []


def test_path_lock_closes_handle_when_unlock_fails_after_success(
    jsonio, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock_path = tmp_path / "success.lock"
    opened = []
    real_open = Path.open

    def tracking_open(path: Path, *args, **kwargs):
        handle = real_open(path, *args, **kwargs)
        if Path(path) == lock_path:
            opened.append(handle)
        return handle

    unlock_error = OSError("injected unlock failure")

    def fail_unlock(handle) -> None:
        raise unlock_error

    monkeypatch.setattr(Path, "open", tracking_open)
    monkeypatch.setattr(jsonio, "_unlock_file", fail_unlock)
    caught = None
    try:
        with jsonio._exclusive_path_lock(lock_path):
            pass
    except BaseException as error:
        caught = error
    assert opened
    was_closed = opened[-1].closed
    if not was_closed:
        opened[-1].close()

    assert caught is unlock_error
    assert was_closed


def test_path_lock_preserves_body_error_and_records_unlock_failure(
    jsonio, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock_path = tmp_path / "body-error.lock"
    opened = []
    real_open = Path.open

    def tracking_open(path: Path, *args, **kwargs):
        handle = real_open(path, *args, **kwargs)
        if Path(path) == lock_path:
            opened.append(handle)
        return handle

    body_error = RuntimeError("primary body failure")
    unlock_error = OSError("secondary unlock failure")

    def fail_unlock(handle) -> None:
        raise unlock_error

    monkeypatch.setattr(Path, "open", tracking_open)
    monkeypatch.setattr(jsonio, "_unlock_file", fail_unlock)
    caught = None
    try:
        with jsonio._exclusive_path_lock(lock_path):
            raise body_error
    except BaseException as error:
        caught = error
    assert opened
    was_closed = opened[-1].closed
    if not was_closed:
        opened[-1].close()

    notes = getattr(body_error, "__notes__", ())
    has_unlock_diagnostic = (
        body_error.__context__ is unlock_error
        or body_error.__cause__ is unlock_error
        or any("unlock" in note.lower() for note in notes)
    )
    assert caught is body_error
    assert was_closed
    assert has_unlock_diagnostic


def test_local_lock_registry_reclaims_thousands_of_idle_paths(
    jsonio, tmp_path: Path
) -> None:
    baseline = len(jsonio._LOCAL_LOCKS)
    for number in range(3000):
        jsonio._local_lock_for(tmp_path / f"registry-{number}.lock")
    gc.collect()

    assert len(jsonio._LOCAL_LOCKS) <= baseline + 8


def test_local_lock_registry_returns_one_lock_under_same_path_contention(
    jsonio, tmp_path: Path
) -> None:
    lock_path = tmp_path / "shared.lock"
    barrier = Barrier(32)

    def contender():
        barrier.wait()
        return jsonio._local_lock_for(lock_path)

    with ThreadPoolExecutor(max_workers=32) as executor:
        locks = list(executor.map(lambda _: contender(), range(32)))

    assert len({id(lock) for lock in locks}) == 1


def test_append_jsonl_locked_never_interleaves_concurrent_lines(
    jsonio, tmp_path: Path
) -> None:
    target = tmp_path / "events.jsonl"

    def writer(worker: int) -> None:
        for sequence in range(20):
            jsonio.append_jsonl_locked(
                target, {"worker": worker, "sequence": sequence, "text": "并发"}
            )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(writer, range(8)))

    raw_lines = target.read_bytes().splitlines(keepends=True)
    assert len(raw_lines) == 160
    assert all(line.endswith(b"\n") for line in raw_lines)
    decoded = [json.loads(line) for line in raw_lines]
    assert {(item["worker"], item["sequence"]) for item in decoded} == {
        (worker, sequence) for worker in range(8) for sequence in range(20)
    }
    assert all(line == jsonio.canonical_json_bytes(json.loads(line)) for line in raw_lines)


def test_append_jsonl_locked_is_atomic_across_sustained_subprocess_writers(
    jsonio, tmp_path: Path
) -> None:
    target = tmp_path / "subprocess-events.jsonl"
    gate = tmp_path / "jsonl-subprocess.gate"
    child_code = """
from pathlib import Path
import sys
import time

sys.path.insert(0, sys.argv[1])
from ultra_runtime.jsonio import append_jsonl_locked

target = Path(sys.argv[2])
gate = Path(sys.argv[3])
worker = int(sys.argv[4])
count = int(sys.argv[5])
deadline = time.monotonic() + 10
while not gate.exists():
    if time.monotonic() >= deadline:
        raise TimeoutError("subprocess JSONL gate was not released")
    time.sleep(0.005)
for sequence in range(count):
    append_jsonl_locked(
        target,
        {"sequence": sequence, "text": "multiprocess", "worker": worker},
    )
"""
    worker_count = 4
    lines_per_worker = 40
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-c",
                child_code,
                str(SCRIPTS_DIR),
                str(target),
                str(gate),
                str(worker),
                str(lines_per_worker),
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for worker in range(worker_count)
    ]
    try:
        gate.write_bytes(b"go\n")
        for process in processes:
            _, stderr = process.communicate(timeout=45)
            assert process.returncode == 0, stderr
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    raw_lines = target.read_bytes().splitlines(keepends=True)
    assert len(raw_lines) == worker_count * lines_per_worker
    assert all(line.endswith(b"\n") for line in raw_lines)
    decoded = [json.loads(line) for line in raw_lines]
    assert {(item["worker"], item["sequence"]) for item in decoded} == {
        (worker, sequence)
        for worker in range(worker_count)
        for sequence in range(lines_per_worker)
    }
    assert all(
        line == jsonio.canonical_json_bytes(json.loads(line))
        for line in raw_lines
    )


def test_status_transition_table_is_frozen(runtime_modules) -> None:
    _, _, status_module, _ = runtime_modules
    assert status_module.RUN_STATUS_TRANSITIONS == {
        "created": frozenset(
            {"running", "blocked", "needs_attention", "failed", "cancelled"}
        ),
        "running": frozenset(
            {
                "interrupted",
                "blocked",
                "needs_attention",
                "failed",
                "cancelled",
                "complete",
            }
        ),
        "interrupted": frozenset(
            {"running", "blocked", "needs_attention", "failed", "cancelled"}
        ),
        "blocked": frozenset(
            {"running", "interrupted", "needs_attention", "failed", "cancelled"}
        ),
        "needs_attention": frozenset(
            {"running", "interrupted", "blocked", "failed", "cancelled"}
        ),
        "failed": frozenset(),
        "cancelled": frozenset(),
        "complete": frozenset(),
    }


def test_status_store_create_read_transition_and_closed_serialization(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, now)

    assert created.schema_id == "crossframe.ultra.v82.run-status"
    assert created.schema_version == 1
    assert created.run_id == layout.run_dir.name
    assert created.version_binding == _runtime_module(
        "constants"
    ).current_version_binding()
    with pytest.raises(TypeError):
        created.version_binding["runtime_version"] = "9.9.9"
    assert created.generated_at == "2026-08-02T03:04:05Z"
    assert created.phase_id == "U0"
    assert created.status == "created"
    assert created.previous_status is None
    assert created.current_phase == "U0"
    assert created.last_complete_phase is None
    assert created.reason is None
    assert created.tools_allowed is False
    assert created.validation_passed is False
    assert created.created_at == "2026-08-02T03:04:05Z"
    assert created.updated_at == "2026-08-02T03:04:05Z"
    assert created.revision == 0
    assert store.read() == created
    persisted = jsonio.load_json_object(layout.run_dir / "run-status.json")
    assert set(persisted) == STATUS_AUTHORITY_FIELDS
    assert persisted["phase_id"] == persisted["current_phase"]
    assert persisted["generated_at"] == persisted["updated_at"]
    assert persisted["content_sha256"] == _runtime_module(
        "schemas"
    ).compute_artifact_content_sha256(persisted)
    _runtime_module("schemas").validate_instance(
        "ultra-run-status.schema.json", persisted
    )

    running = store.transition(
        created,
        "running",
        now + timedelta(seconds=1),
        current_phase="U0",
        reason="started",
    )
    assert running.status == "running"
    assert running.revision == 1
    assert running.phase_id == running.current_phase == "U0"
    assert running.previous_status == "created"
    assert running.tools_allowed is True
    assert store.read() == running


def test_status_replace_is_atomic_and_rejects_stale_cas(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, now)
    running = store.transition(created, "running", now + timedelta(seconds=1))
    with pytest.raises(RuntimeError, match="CAS|stale|revision|updated"):
        store.transition(
            created,
            "failed",
            now + timedelta(seconds=2),
            reason="stale",
        )
    assert store.read() == running


def test_status_illegal_and_terminal_transitions_never_revive(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, created = _create_status(status_module, layout, now)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="transition|created|complete"):
        store.transition(created, "complete", now + timedelta(seconds=1))

    running = store.transition(created, "running", now + timedelta(seconds=1))
    with pytest.raises((TypeError, ValueError, RuntimeError), match="U12|complete|closure|ordinary"):
        store.transition(running, "complete", now + timedelta(seconds=2))
    with pytest.raises((TypeError, ValueError, RuntimeError), match="U12|complete|closure|ordinary"):
        store.transition(
            running,
            "complete",
            now + timedelta(seconds=2),
            current_phase="U12",
            last_complete_phase="U12",
            validation_passed=True,
        )
    assert store.read() == running


def test_status_replace_rejects_resealed_complete_without_durable_u12_closure(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, base)
    running = store.transition(created, "running", base + timedelta(seconds=1))
    replacement_object = status_module._record_to_object(running)
    replacement_object.update(
        status="complete",
        previous_status="running",
        current_phase="U12",
        last_complete_phase="U12",
        phase_id="U12",
        validation_passed=True,
        tools_allowed=False,
        reason="caller fabricated completion",
        updated_at="2026-08-02T03:04:07Z",
        generated_at="2026-08-02T03:04:07Z",
        revision=2,
    )
    _rehash_status(replacement_object)
    replacement = status_module._record_from_object(
        replacement_object, layout.run_dir.name
    )

    with pytest.raises((TypeError, ValueError, RuntimeError), match="complete|U12|closure|ordinary"):
        store.replace(running, replacement)

    assert store.read() == running


def test_cancelled_status_rejects_all_ordinary_replacements(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, created = _create_status(status_module, layout, now)
    cancelled = store.transition(
        created, "cancelled", now + timedelta(seconds=1), reason="operator cancelled"
    )
    assert cancelled.tools_allowed is False

    with pytest.raises((TypeError, ValueError, RuntimeError), match="cancelled|terminal|transition"):
        store.transition(cancelled, "running", now + timedelta(seconds=2))
    assert store.read() == cancelled


def test_status_rejects_naive_non_utc_and_non_monotonic_times(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store = status_module.RunStatusStore(layout)
    with pytest.raises((TypeError, ValueError)):
        store.create(datetime(2026, 8, 2, 3, 4, 5))

    now = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    created = store.create(now)
    with pytest.raises((TypeError, ValueError, RuntimeError), match="after|monotonic|updated"):
        store.transition(created, "running", now)


def test_status_read_rejects_open_or_corrupt_authority(runtime_modules, tmp_path: Path) -> None:
    paths_module, jsonio, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, _ = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    authority = jsonio.load_json_object(store.path)
    authority["unexpected"] = "not closed"
    jsonio.atomic_write_json(store.path, authority)
    with pytest.raises((TypeError, ValueError, RuntimeError), match="field|closed|unexpected"):
        store.read()


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
def test_status_read_rejects_noncanonical_or_control_bearing_utc_timestamps(
    runtime_modules, tmp_path: Path, noncanonical: str
) -> None:
    paths_module, jsonio, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, _ = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    value = jsonio.load_json_object(store.path)
    value["created_at"] = noncanonical
    jsonio.atomic_write_json(store.path, value)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="canonical|timestamp|UTC"):
        store.read()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("phase_id", "U1", "phase|current"),
        ("generated_at", "2026-08-02T03:04:06Z", "generated|updated"),
        ("content_sha256", "0" * 64, "content_sha256|hash"),
    ),
)
def test_status_read_rejects_self_inconsistent_or_stale_authority(
    runtime_modules,
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    paths_module, jsonio, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, _ = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    authority = jsonio.load_json_object(store.path)
    authority[field] = value
    if field != "content_sha256":
        _rehash_status(authority)
    jsonio.atomic_write_json(store.path, authority)

    with pytest.raises((TypeError, ValueError, RuntimeError), match=message):
        store.read()


def test_status_replace_requires_previous_status_to_match_cas_authority(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, base)
    running = store.transition(created, "running", base + timedelta(seconds=1))
    replacement_object = status_module._record_to_object(running)
    replacement_object.update(
        status="failed",
        previous_status="created",
        tools_allowed=False,
        updated_at="2026-08-02T03:04:07Z",
        generated_at="2026-08-02T03:04:07Z",
        revision=2,
    )
    _rehash_status(replacement_object)
    replacement = status_module._record_from_object(
        replacement_object, layout.run_dir.name
    )

    with pytest.raises(RuntimeError, match="previous_status|previous status"):
        store.replace(running, replacement)
    assert store.read() == running


def test_status_authority_rejects_caller_selected_version_binding(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, status_module, _ = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    store, _ = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    authority = jsonio.load_json_object(store.path)
    authority["version_binding"]["runtime_version"] = "9.9.9"
    _rehash_status(authority)
    jsonio.atomic_write_json(store.path, authority)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="version|binding|authority"):
        store.read()


def test_index_rebuild_never_writes_noncanonical_timestamp_to_markdown(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    injected = "2026-08-02\u202803:04:05Z"
    store, _ = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    authority = jsonio.load_json_object(store.path)
    authority["created_at"] = injected
    _rehash_status(authority)
    jsonio.atomic_write_json(store.path, authority)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="canonical|timestamp|authority"):
        indexes_module.IndexStore(layout.root).rebuild()

    for markdown_path in (
        layout.root / "START-HERE.md",
        layout.run_dir / "START-HERE.md",
    ):
        assert not markdown_path.exists()


def _seed_index_runs(paths_module, status_module, tmp_path: Path):
    root_holder = tmp_path / "authority"
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)

    complete_layout = _layout(
        paths_module, root_holder, "20260802T030405Z-000000000001"
    )
    complete_store, complete_created = _create_status(
        status_module, complete_layout, base
    )
    complete_running = complete_store.transition(
        complete_created, "running", base + timedelta(seconds=1)
    )
    complete_object = status_module._record_to_object(complete_running)
    complete_object.update(
        status="complete",
        previous_status="running",
        current_phase="U12",
        last_complete_phase="U12",
        phase_id="U12",
        validation_passed=True,
        tools_allowed=False,
        updated_at="2026-08-02T03:04:07Z",
        generated_at="2026-08-02T03:04:07Z",
        revision=2,
    )
    _rehash_status(complete_object)
    _runtime_module("jsonio").atomic_write_json(
        complete_store.path, complete_object
    )
    complete = complete_store.read()

    attention_layout = _layout(
        paths_module, root_holder, "20260802T030406Z-000000000002"
    )
    attention_store, attention_created = _create_status(
        status_module, attention_layout, base + timedelta(seconds=3)
    )
    attention = attention_store.transition(
        attention_created,
        "needs_attention",
        base + timedelta(seconds=4),
        reason="manual review",
    )

    failed_layout = _layout(
        paths_module, root_holder, "20260802T030407Z-000000000003"
    )
    failed_store, failed_created = _create_status(
        status_module, failed_layout, base + timedelta(seconds=5)
    )
    failed_running = failed_store.transition(
        failed_created, "running", base + timedelta(seconds=6)
    )
    failed = failed_store.transition(
        failed_running,
        "failed",
        base + timedelta(seconds=7),
        reason="validator failed",
    )
    return {
        "root": complete_layout.root,
        "complete": (complete_layout, complete_store, complete),
        "attention": (attention_layout, attention_store, attention),
        "failed": (failed_layout, failed_store, failed),
    }


def test_index_rebuild_uses_only_authority_and_preserves_latest_complete(
    runtime_modules, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    seeded = _seed_index_runs(paths_module, status_module, tmp_path)
    index_store = indexes_module.IndexStore(seeded["root"])
    monkeypatch.setattr(
        indexes_module, "_verify_complete_authority", lambda layout: None
    )

    index_store.rebuild()

    assert index_store.read_pointer("latest")["run_id"] == seeded["failed"][2].run_id
    assert (
        index_store.read_pointer("latest-complete")["run_id"]
        == seeded["complete"][2].run_id
    )
    assert (
        index_store.read_pointer("latest-needs-attention")["run_id"]
        == seeded["attention"][2].run_id
    )
    rows = [
        json.loads(line)
        for line in (seeded["root"] / "index/runs.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [row["run_id"] for row in rows] == [
        seeded["complete"][2].run_id,
        seeded["attention"][2].run_id,
        seeded["failed"][2].run_id,
    ]
    assert all(set(row) == INDEX_PROJECTION_FIELDS for row in rows)
    assert all("content_sha256" not in row for row in rows)


def test_index_rebuild_snapshot_blocks_authority_change_until_publish_finishes(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    running = status_store.transition(
        created, "running", base + timedelta(seconds=1)
    )
    index_store = indexes_module.IndexStore(layout.root)

    publication_reached = Event()
    allow_publication = Event()
    transition_finished = Event()
    real_atomic_write_bytes = indexes_module.atomic_write_bytes

    def pause_first_publication(path: Path, value: bytes) -> None:
        if path == index_store.runs_path and not publication_reached.is_set():
            publication_reached.set()
            if not allow_publication.wait(timeout=5):
                raise TimeoutError("test did not release index publication")
        real_atomic_write_bytes(path, value)

    def transition_to_failed():
        try:
            return status_store.transition(
                running,
                "failed",
                base + timedelta(seconds=2),
                reason="changed during rebuild",
            )
        finally:
            transition_finished.set()

    monkeypatch.setattr(
        indexes_module, "atomic_write_bytes", pause_first_publication
    )
    executor = ThreadPoolExecutor(max_workers=2)
    rebuild_future = executor.submit(index_store.rebuild)
    transition_future = None
    try:
        assert publication_reached.wait(timeout=2)
        transition_future = executor.submit(transition_to_failed)
        assert not transition_finished.wait(timeout=0.3), (
            "authority changed after scanning but before cache publication"
        )
    finally:
        allow_publication.set()
        executor.shutdown(wait=True)

    assert rebuild_future.result() is None
    assert transition_future is not None
    assert transition_future.result().status == "failed"
    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="projection|authority|status|stale",
    ):
        index_store.read_pointer("latest")


def test_index_pointer_reader_never_observes_mixed_cache_generation(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    running = status_store.transition(
        created, "running", base + timedelta(seconds=1)
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    attention = status_store.transition(
        running, "needs_attention", base + timedelta(seconds=2)
    )

    runs_replaced = Event()
    allow_remaining_generation = Event()
    reader_finished = Event()
    real_atomic_write_bytes = indexes_module.atomic_write_bytes

    def pause_after_runs_replace(path: Path, value: bytes) -> None:
        real_atomic_write_bytes(path, value)
        if path == index_store.runs_path and not runs_replaced.is_set():
            runs_replaced.set()
            if not allow_remaining_generation.wait(timeout=5):
                raise TimeoutError("test did not release index generation")

    def read_latest():
        try:
            return index_store.read_pointer("latest")
        finally:
            reader_finished.set()

    monkeypatch.setattr(
        indexes_module, "atomic_write_bytes", pause_after_runs_replace
    )
    executor = ThreadPoolExecutor(max_workers=2)
    rebuild_future = executor.submit(index_store.rebuild)
    reader_future = None
    try:
        assert runs_replaced.wait(timeout=2)
        reader_future = executor.submit(read_latest)
        assert not reader_finished.wait(timeout=0.3), (
            "pointer reader observed a partially published cache generation"
        )
    finally:
        allow_remaining_generation.set()
        executor.shutdown(wait=True)

    assert rebuild_future.result() is None
    assert reader_future is not None
    latest = reader_future.result()
    assert latest is not None
    assert latest["status"] == "needs_attention"
    assert latest["revision"] == attention.revision
    rows = [
        json.loads(line)
        for line in index_store.runs_path.read_text(encoding="utf-8").splitlines()
    ]
    assert rows == [latest]
    assert index_store.read_pointer("latest-needs-attention") == latest


def test_index_rebuild_repairs_corrupt_cache_byte_for_byte(
    runtime_modules, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    seeded = _seed_index_runs(paths_module, status_module, tmp_path)
    root = seeded["root"]
    store = indexes_module.IndexStore(root)
    monkeypatch.setattr(
        indexes_module, "_verify_complete_authority", lambda layout: None
    )
    store.rebuild()
    tracked = [
        root / "START-HERE.md",
        root / "index/runs.jsonl",
        root / "index/latest.json",
        root / "index/latest-complete.json",
        root / "index/latest-needs-attention.json",
        *(item[0].run_dir / "START-HERE.md" for item in seeded.values() if isinstance(item, tuple)),
    ]
    expected = {path: path.read_bytes() for path in tracked}

    (root / "index/runs.jsonl").write_bytes(b"corrupt")
    (root / "index/latest.json").write_bytes(b"[]")
    (root / "index/latest-complete.json").unlink()
    (root / "START-HERE.md").write_text("sensitive stale cache", encoding="utf-8")
    store.rebuild()

    assert {path: path.read_bytes() for path in tracked} == expected


def test_latest_needs_attention_pointer_is_removed_when_no_candidate_remains(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    root_holder = tmp_path / "authority"
    layout = _layout(
        paths_module, root_holder, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    attention = status_store.transition(
        created, "needs_attention", base + timedelta(seconds=1)
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    assert index_store.read_pointer("latest-needs-attention") is not None

    status_store.transition(attention, "running", base + timedelta(seconds=2))
    index_store.rebuild()

    assert index_store.read_pointer("latest-needs-attention") is None
    assert not (layout.root / "index/latest-needs-attention.json").exists()


def test_start_here_files_never_copy_sensitive_input_title_query_or_reason(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    secret = "SENSITIVE TITLE QUERY INPUT 绝密"
    store, created = _create_status(
        status_module,
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    store.transition(
        created,
        "needs_attention",
        datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
        reason=secret,
    )
    layout.input_dir.mkdir(parents=True)
    jsonio.atomic_write_json(
        layout.input_dir / "request.json",
        {"title": secret, "query": secret, "input": secret},
    )

    indexes_module.IndexStore(layout.root).rebuild()

    root_start = (layout.root / "START-HERE.md").read_text(encoding="utf-8")
    run_start = (layout.run_dir / "START-HERE.md").read_text(encoding="utf-8")
    assert secret not in root_start
    assert secret not in run_start
    for neutral in (
        layout.run_dir.name,
        "needs_attention",
        "2026-08-02T03:04:05Z",
        "2026-08-02T03:04:06Z",
    ):
        assert neutral in root_start or neutral in run_start
    assert "run-status.json" in run_start
    assert "index/latest.json" in root_start


def test_index_projection_redacts_reason_without_changing_authority(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, base)
    secret = "private query and failure detail 绝密"
    attention = store.transition(
        created,
        "needs_attention",
        base + timedelta(seconds=1),
        reason=secret,
    )
    index_store = indexes_module.IndexStore(layout.root)

    index_store.rebuild()

    assert store.read() == attention
    assert store.read().reason == secret
    rows = [
        json.loads(line)
        for line in index_store.runs_path.read_text(encoding="utf-8").splitlines()
    ]
    assert set(rows[0]) == INDEX_PROJECTION_FIELDS
    assert set(index_store.read_pointer("latest")) == INDEX_PROJECTION_FIELDS
    assert set(index_store.read_pointer("latest-needs-attention")) == INDEX_PROJECTION_FIELDS
    assert "reason" not in rows[0]
    assert secret.encode("utf-8") not in index_store.runs_path.read_bytes()
    assert secret.encode("utf-8") not in (
        layout.root / "index/latest.json"
    ).read_bytes()


def test_index_rebuild_refuses_corrupt_authority_instead_of_hiding_it(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, _, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    layout.run_dir.mkdir(parents=True)
    (layout.run_dir / "run-status.json").write_bytes(b"{broken")

    with pytest.raises((TypeError, ValueError, RuntimeError), match="JSON|json|authority|status"):
        indexes_module.IndexStore(layout.root).rebuild()


def test_index_rebuild_rejects_status_only_forgery_as_non_authoritative(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, _, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    layout.run_dir.mkdir(parents=True)
    jsonio.atomic_write_json(
        layout.run_dir / "run-status.json", {"status": "complete"}
    )

    with pytest.raises((TypeError, ValueError, RuntimeError), match="authority|status|closed"):
        indexes_module.IndexStore(layout.root).rebuild()
    assert not (layout.root / "index/latest-complete.json").exists()


def test_index_rebuild_rejects_resealed_complete_without_durable_u12_authority(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    store, created = _create_status(status_module, layout, base)
    running = store.transition(created, "running", base + timedelta(seconds=1))
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    latest_complete = layout.root / "index/latest-complete.json"
    latest_complete.write_bytes(b"latest-complete sentinel\n")
    tracked = {
        path: path.read_bytes()
        for path in (
            layout.root / "START-HERE.md",
            layout.root / "index/runs.jsonl",
            layout.root / "index/latest.json",
            latest_complete,
            layout.root / "index/generation-manifest.json",
        )
    }

    forged = status_module._record_to_object(running)
    forged.update(
        status="complete",
        previous_status="running",
        current_phase="U12",
        last_complete_phase="U12",
        phase_id="U12",
        validation_passed=True,
        tools_allowed=False,
        reason="resealed without U12 event or checkpoint",
        updated_at="2026-08-02T03:04:07Z",
        generated_at="2026-08-02T03:04:07Z",
        revision=2,
    )
    _rehash_status(forged)
    jsonio.atomic_write_json(store.path, forged)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="U12|journal|completion|authority"):
        index_store.rebuild()

    assert {path: path.read_bytes() for path in tracked} == tracked


@pytest.mark.parametrize("pointer_name", ("latest", "latest-complete"))
def test_read_pointer_rejects_self_consistent_complete_cache_without_u12_authority(
    runtime_modules,
    tmp_path: Path,
    pointer_name: str,
) -> None:
    _, jsonio, _, indexes_module = runtime_modules
    run_id = "20260802T030405Z-000000000001"
    projection = {
        "run_id": run_id,
        "status": "complete",
        "created_at": "2026-08-02T03:04:05Z",
        "updated_at": "2026-08-02T03:04:07Z",
        "revision": 2,
    }
    store = indexes_module.IndexStore(tmp_path)
    store.index_dir.mkdir(parents=True)
    runs_bytes = jsonio.canonical_json_bytes(projection)
    pointer_bytes = {
        "latest.json": jsonio.canonical_json_bytes(projection),
        "latest-complete.json": jsonio.canonical_json_bytes(projection),
        "latest-needs-attention.json": None,
    }
    jsonio.atomic_write_bytes(store.runs_path, runs_bytes)
    jsonio.atomic_write_bytes(
        store.index_dir / "latest.json", pointer_bytes["latest.json"]
    )
    jsonio.atomic_write_bytes(
        store.index_dir / "latest-complete.json",
        pointer_bytes["latest-complete.json"],
    )
    files = indexes_module.IndexStore._cache_file_hashes(
        runs_bytes, pointer_bytes
    )
    jsonio.atomic_write_json(
        store.generation_manifest_path,
        indexes_module._generation_manifest(files),
    )

    with pytest.raises((TypeError, ValueError, RuntimeError), match="complete|status|journal|U12|authority"):
        store.read_pointer(pointer_name)


def test_read_pointer_rejects_stale_noncomplete_status_projection(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    attention = status_store.transition(
        created,
        "needs_attention",
        base + timedelta(seconds=1),
        reason="operator review required",
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    assert (
        index_store.read_pointer("latest-needs-attention")["status"]
        == attention.status
    )

    current = status_store.transition(
        attention,
        "running",
        base + timedelta(seconds=2),
    )

    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="projection|authority|status|stale",
    ):
        index_store.read_pointer("latest-needs-attention")
    assert status_store.read() == current


def test_read_pointer_rejects_stale_noncomplete_revision_with_same_status(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    cached_running = status_store.transition(
        created,
        "running",
        base + timedelta(seconds=1),
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    cached = index_store.read_pointer("latest")
    assert cached["status"] == cached_running.status
    assert cached["revision"] == cached_running.revision

    interrupted = status_store.transition(
        cached_running,
        "interrupted",
        base + timedelta(seconds=2),
        reason="restart boundary",
    )
    current_running = status_store.transition(
        interrupted,
        "running",
        base + timedelta(seconds=3),
    )
    assert current_running.status == cached_running.status
    assert current_running.revision > cached_running.revision

    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="projection|authority|status|stale|revision",
    ):
        index_store.read_pointer("latest")
    assert status_store.read() == current_running


def test_read_pointer_rejects_cached_null_when_authoritative_candidate_appears(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    running = status_store.transition(
        created,
        "running",
        base + timedelta(seconds=1),
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    assert index_store.read_pointer("latest-needs-attention") is None

    attention = status_store.transition(
        running,
        "needs_attention",
        base + timedelta(seconds=2),
        reason="new canonical attention candidate",
    )
    cache_paths = (
        index_store.runs_path,
        index_store.generation_manifest_path,
        index_store.index_dir / "latest.json",
        index_store.index_dir / "latest-complete.json",
        index_store.index_dir / "latest-needs-attention.json",
    )
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in cache_paths
    }

    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="pointer|authority|candidate|stale|projection",
    ):
        index_store.read_pointer("latest-needs-attention")

    assert status_store.read() == attention
    assert {
        path: path.read_bytes() if path.is_file() else None
        for path in cache_paths
    } == before


def test_read_pointer_rejects_cached_latest_when_newer_authoritative_run_appears(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    root_holder = tmp_path / "authority"
    first_layout = _layout(
        paths_module, root_holder, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    first_store, first_created = _create_status(
        status_module, first_layout, base
    )
    first_running = first_store.transition(
        first_created,
        "running",
        base + timedelta(seconds=1),
    )
    index_store = indexes_module.IndexStore(first_layout.root)
    index_store.rebuild()
    assert index_store.read_pointer("latest")["run_id"] == first_running.run_id

    second_layout = _layout(
        paths_module, root_holder, "20260802T030407Z-000000000002"
    )
    second_store, second_created = _create_status(
        status_module,
        second_layout,
        base + timedelta(seconds=2),
    )
    cache_paths = (
        index_store.runs_path,
        index_store.generation_manifest_path,
        index_store.index_dir / "latest.json",
        index_store.index_dir / "latest-complete.json",
        index_store.index_dir / "latest-needs-attention.json",
    )
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in cache_paths
    }

    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="pointer|authority|candidate|stale|projection",
    ):
        index_store.read_pointer("latest")

    assert second_store.read() == second_created
    assert {
        path: path.read_bytes() if path.is_file() else None
        for path in cache_paths
    } == before


def _seed_durable_complete_index(runtime_modules, tmp_path: Path):
    paths_module, jsonio, status_module, indexes_module = runtime_modules
    constants = _runtime_module("constants")
    deliverables = _runtime_module("deliverables")
    schemas = _runtime_module("schemas")
    state_machine = _runtime_module("state_machine")
    run_id = "20260802T030405Z-000000000001"
    transaction_id = "20260802T030420Z-bbbbbbbbbbbb"
    layout = _layout(paths_module, tmp_path, run_id)
    binding = dict(constants.current_version_binding())
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)

    input_path = layout.input_dir / "request.txt"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"frozen request\n")
    input_sha256 = jsonio.sha256_bytes(input_path.read_bytes())
    contract_path = layout.artifacts_dir / "ultra-run-contract.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_bytes(b'{"contract":"sealed"}\n')
    contract_sha256 = jsonio.sha256_bytes(contract_path.read_bytes())
    source_sha256 = "1" * 64
    evidence_cutoff = "2026-08-02T03:04:05Z"

    authority = {
        "schema_id": "crossframe.ultra.v82.recovery-authority",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": binding,
        "source_sha256": source_sha256,
        "input_artifact_hashes": [input_sha256],
        "input_snapshot_sha256": input_sha256,
        "evidence_cutoff": evidence_cutoff,
        "run_contract_sha256": contract_sha256,
        "input_refs": [
            {
                "path": "input/request.txt",
                "sha256": input_sha256,
                "media_type": "text/plain",
            }
        ],
        "content_sha256": "0" * 64,
    }
    authority["content_sha256"] = schemas.compute_artifact_content_sha256(
        authority
    )
    jsonio.atomic_write_json(
        layout.recovery_dir / "run-authority.json", authority
    )

    publication = deliverables.publication_paths(layout, transaction_id)
    payloads = {
        publication.manifest_path: b'{"kind":"manifest"}\n',
        publication.article_path: b"# complete article\n",
        publication.dossier_path: b"# complete dossier\n",
        publication.artifact_index_path: b"# complete artifact index\n",
    }
    for official, payload in payloads.items():
        official.parent.mkdir(parents=True, exist_ok=True)
        official.write_bytes(payload)
        staged = deliverables._staged_path(publication, official)
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(payload)
    report_path = (
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(b'{"kind":"validator-report"}\n')
    checkpoint_paths = (
        publication.manifest_path,
        report_path,
        publication.article_path,
        publication.dossier_path,
        publication.artifact_index_path,
    )
    u12_outputs = [
        jsonio.sha256_bytes(path.read_bytes()) for path in checkpoint_paths
    ]

    output_counts = {
        "U1": 1,
        "U2": 1,
        "U3": 1,
        "U4": 1,
        "U5": 2,
        "U6": 1,
        "U7": 2,
        "U8": 2,
        "U9": 3,
        "U10": 2,
        "U11": 5,
    }
    events = []
    parent_sha256 = "0" * 64
    for ordinal in range(13):
        phase_id = f"U{ordinal}"
        timestamp = (
            (base + timedelta(seconds=ordinal + 2))
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        if phase_id == "U0":
            outputs = [contract_sha256]
        elif phase_id == "U12":
            outputs = u12_outputs
        else:
            outputs = [
                jsonio.sha256_bytes(
                    f"{phase_id}-output-{index}".encode("ascii")
                )
                for index in range(output_counts[phase_id])
            ]
        event = {
            "schema_id": state_machine.PHASE_EVENT_SCHEMA_ID,
            "schema_version": 1,
            "run_id": run_id,
            "version_binding": binding,
            "generated_at": timestamp,
            "content_sha256": "0" * 64,
            "phase_id": phase_id,
            "event_type": "phase-completed",
            "parent_event_sha256": parent_sha256,
            "input_artifact_hashes": [input_sha256],
            "output_artifact_hashes": outputs,
            "source_sha256": source_sha256,
            "evidence_cutoff": evidence_cutoff,
            "run_contract_sha256": contract_sha256,
            "timestamp": timestamp,
            "status": "complete",
            "failure_code": None,
            "invalidated_phases": [],
            "event_sha256": "0" * 64,
        }
        event["content_sha256"] = (
            state_machine._compute_event_content_sha256(event)
        )
        event["event_sha256"] = state_machine.compute_event_sha256(event)
        events.append(event)
        parent_sha256 = event["event_sha256"]
    jsonio.atomic_write_bytes(
        layout.recovery_dir / "phase-events.jsonl",
        b"".join(jsonio.canonical_json_bytes(event) for event in events),
    )

    checkpoint = {
        "schema_id": "crossframe.ultra.v82.recovery-checkpoint",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": binding,
        "generated_at": "2026-08-02T03:04:20Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "boundary_kind": "phase",
        "boundary_id": "U12",
        "boundary_ordinal": 0,
        "phase_event_sha256": events[-1]["event_sha256"],
        "artifact_hashes": [
            {
                "path": path.relative_to(layout.run_dir).as_posix(),
                "sha256": jsonio.sha256_bytes(path.read_bytes()),
                "media_type": (
                    "application/json"
                    if path.suffix == ".json"
                    else "text/markdown"
                ),
            }
            for path in checkpoint_paths
        ],
        "evidence_cutoff": evidence_cutoff,
        "completed_boundary": True,
        "resumable": True,
    }
    checkpoint["content_sha256"] = schemas.compute_artifact_content_sha256(
        checkpoint
    )
    checkpoint_bytes = jsonio.canonical_json_bytes(checkpoint)
    checkpoint_path = layout.recovery_dir / "checkpoints" / (
        f"{jsonio.sha256_bytes(checkpoint_bytes)}.json"
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_bytes(checkpoint_bytes)

    journal = deliverables._journal_object(
        layout,
        publication,
        transaction_id=transaction_id,
        state="complete",
        payloads=payloads,
        previous={official: None for official in payloads},
        precheck_passed=True,
        postcheck_passed=True,
        failure=None,
    )
    journal["u12_event_sha256"] = events[-1]["event_sha256"]
    journal["u12_checkpoint_content_sha256"] = checkpoint[
        "content_sha256"
    ]
    jsonio.atomic_write_json(publication.journal_path, journal)

    status_store, created = _create_status(status_module, layout, base)
    running = status_store.transition(
        created,
        "running",
        base + timedelta(seconds=1),
    )
    complete = status_module._record_to_object(running)
    complete.update(
        status="complete",
        previous_status="running",
        current_phase="U12",
        last_complete_phase="U12",
        phase_id="U12",
        validation_passed=True,
        tools_allowed=False,
        reason="durable U12 closure",
        updated_at="2026-08-02T03:04:21Z",
        generated_at="2026-08-02T03:04:21Z",
        revision=2,
    )
    _rehash_status(complete)
    jsonio.atomic_write_json(status_store.path, complete)

    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    return layout, index_store, status_store.read()


def _recovery_tree_snapshot(layout) -> dict[str, bytes | None]:
    return {
        path.relative_to(layout.recovery_dir).as_posix(): (
            None if path.is_dir() else path.read_bytes()
        )
        for path in sorted(layout.recovery_dir.rglob("*"))
    }


def test_read_pointer_never_quarantines_malformed_recovery_checkpoint(
    runtime_modules, tmp_path: Path
) -> None:
    layout, index_store, complete = _seed_durable_complete_index(
        runtime_modules, tmp_path
    )
    malformed = layout.recovery_dir / "checkpoints" / f"{'f' * 64}.json"
    malformed.write_bytes(b'{"schema_id":')
    before = _recovery_tree_snapshot(layout)

    pointer = index_store.read_pointer("latest-complete")

    assert pointer is not None and pointer["run_id"] == complete.run_id
    assert _recovery_tree_snapshot(layout) == before


def test_read_pointer_rejects_unknown_names(runtime_modules, tmp_path: Path) -> None:
    _, _, _, indexes_module = runtime_modules
    with pytest.raises((TypeError, ValueError)):
        indexes_module.IndexStore(tmp_path).read_pointer("../outside")


def test_index_rebuild_failure_after_runs_replace_invalidates_old_cache(
    runtime_modules,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed pointer publication must never leave an older generation readable."""

    paths_module, _, status_module, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    base = datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc)
    status_store, created = _create_status(status_module, layout, base)
    running = status_store.transition(
        created, "running", base + timedelta(seconds=1)
    )
    index_store = indexes_module.IndexStore(layout.root)
    index_store.rebuild()
    assert index_store.read_pointer("latest")["status"] == "running"

    changed = status_store.transition(
        running,
        "needs_attention",
        base + timedelta(seconds=2),
        reason="injected publication failure",
    )
    real_write_pointer = index_store._write_pointer

    def fail_latest_pointer(name: str, record) -> None:
        if name == "latest":
            raise OSError("injected pointer publication failure")
        real_write_pointer(name, record)

    monkeypatch.setattr(index_store, "_write_pointer", fail_latest_pointer)
    with pytest.raises(OSError, match="injected pointer publication failure"):
        index_store.rebuild()

    rows = [
        json.loads(line)
        for line in index_store.runs_path.read_text(encoding="utf-8").splitlines()
    ]
    assert rows == [
        {
            **rows[0],
            "run_id": changed.run_id,
            "status": "needs_attention",
            "revision": changed.revision,
        }
    ]
    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="rebuild|generation|manifest|cache",
    ):
        index_store.read_pointer("latest")
