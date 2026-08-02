from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import gc
import importlib
import json
from pathlib import Path
import subprocess
import sys
from threading import Barrier, Event

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"


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

    assert created == status_module.RunStatusRecord(
        run_id=layout.run_dir.name,
        status="created",
        created_at="2026-08-02T03:04:05Z",
        updated_at="2026-08-02T03:04:05Z",
        revision=0,
        phase_id=None,
        reason=None,
    )
    assert store.read() == created
    assert set(jsonio.load_json_object(layout.run_dir / "run-status.json")) == {
        "run_id",
        "status",
        "created_at",
        "updated_at",
        "revision",
        "phase_id",
        "reason",
    }

    running = store.transition(
        created,
        "running",
        now + timedelta(seconds=1),
        phase_id="U0",
        reason="started",
    )
    assert running.status == "running"
    assert running.revision == 1
    assert running.phase_id == "U0"
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
    running = replace(
        created,
        status="running",
        updated_at="2026-08-02T03:04:06Z",
        revision=1,
        phase_id="U0",
    )

    assert store.replace(created, running) == running
    stale_replacement = replace(
        created,
        status="failed",
        updated_at="2026-08-02T03:04:07Z",
        revision=1,
        reason="stale",
    )
    with pytest.raises(RuntimeError, match="CAS|stale|revision|updated"):
        store.replace(created, stale_replacement)
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
    complete = store.transition(running, "complete", now + timedelta(seconds=2))
    with pytest.raises((TypeError, ValueError, RuntimeError), match="terminal|transition|complete"):
        store.transition(complete, "running", now + timedelta(seconds=3))
    assert store.read() == complete


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
    layout.run_dir.mkdir(parents=True)
    jsonio.atomic_write_json(
        layout.run_dir / "run-status.json",
        {
            "run_id": layout.run_dir.name,
            "status": "created",
            "created_at": "2026-08-02T03:04:05Z",
            "updated_at": "2026-08-02T03:04:05Z",
            "revision": 0,
            "phase_id": None,
            "reason": None,
            "unexpected": "not closed",
        },
    )
    with pytest.raises((TypeError, ValueError, RuntimeError), match="field|closed|unexpected"):
        status_module.RunStatusStore(layout).read()


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


def test_index_rebuild_never_writes_noncanonical_timestamp_to_markdown(
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, jsonio, _, indexes_module = runtime_modules
    layout = _layout(
        paths_module, tmp_path, "20260802T030405Z-000000000001"
    )
    layout.run_dir.mkdir(parents=True)
    injected = "2026-08-02\u202803:04:05Z"
    jsonio.atomic_write_json(
        layout.run_dir / "run-status.json",
        {
            "run_id": layout.run_dir.name,
            "status": "created",
            "created_at": injected,
            "updated_at": injected,
            "revision": 0,
            "phase_id": None,
            "reason": None,
        },
    )

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
    complete = complete_store.transition(
        complete_running, "complete", base + timedelta(seconds=2)
    )

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
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    seeded = _seed_index_runs(paths_module, status_module, tmp_path)
    index_store = indexes_module.IndexStore(seeded["root"])

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
    cached = index_store.read_pointer("latest")
    assert cached is not None
    assert cached["status"] == "running"
    assert cached["revision"] == running.revision


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
    runtime_modules, tmp_path: Path
) -> None:
    paths_module, _, status_module, indexes_module = runtime_modules
    seeded = _seed_index_runs(paths_module, status_module, tmp_path)
    root = seeded["root"]
    store = indexes_module.IndexStore(root)
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
    assert rows[0]["reason"] is None
    assert index_store.read_pointer("latest")["reason"] is None
    assert index_store.read_pointer("latest-needs-attention")["reason"] is None
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
            "reason": None,
        }
    ]
    with pytest.raises(
        (indexes_module.IndexError, RuntimeError, ValueError),
        match="rebuild|generation|manifest|cache",
    ):
        index_store.read_pointer("latest")
