from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
from threading import Lock
from typing import Any, BinaryIO, Iterator
from weakref import WeakValueDictionary

from check_crossframe_ultra_v82_source import MAX_ISOLATED_REQUEST_BYTES


class _LocalPathLock:
    __slots__ = ("lock", "__weakref__")

    def __init__(self) -> None:
        self.lock = Lock()


_LOCAL_LOCKS_GUARD = Lock()
_LOCAL_LOCKS: WeakValueDictionary[str, _LocalPathLock] = WeakValueDictionary()
AUTHORITY_SNAPSHOT_LOCK_FILENAME = ".authority-snapshot.lock"
RUN_LIFECYCLE_LOCK_FILENAME = ".run-lifecycle.lock"
DEFAULT_MAX_JSON_BYTES = MAX_ISOLATED_REQUEST_BYTES
DEFAULT_MAX_JSON_CONTAINER_ITEMS = DEFAULT_MAX_JSON_BYTES
DEFAULT_MAX_JSON_DEPTH = sys.getrecursionlimit()


def canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"value is not canonical JSON: {error}") from error
    return (text + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise TypeError("sha256_bytes requires bytes")
    return hashlib.sha256(value).hexdigest()


def _fsync_directory(directory: Path) -> None:
    if not hasattr(os, "fsync"):
        return
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError:
            return
    finally:
        os.close(descriptor)


def _open_unique_temporary(target: Path) -> tuple[int, Path]:
    for _ in range(64):
        temporary = target.parent / (
            f".{target.name}.tmp-{os.getpid()}-{secrets.token_hex(12)}"
        )
        try:
            descriptor = os.open(
                temporary,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            continue
        return descriptor, temporary
    raise FileExistsError(f"cannot allocate unique temporary file beside {target}")


def atomic_write_bytes(path: Path, value: bytes) -> None:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    if not isinstance(value, bytes):
        raise TypeError("atomic_write_bytes requires bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = _open_unique_temporary(path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            if hasattr(os, "fsync"):
                os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, value: object) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))


def _strict_limit(value: object, *, name: str, default: int) -> int:
    if value is None:
        return default
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _validate_json_structure(
    value: object,
    *,
    max_container_items: int,
    max_depth: int,
) -> None:
    container_items = 0
    try:
        stack: list[tuple[Iterator[object], int]] = [(iter((value,)), 0)]
        while stack:
            children, depth = stack[-1]
            try:
                current = next(children)
            except StopIteration:
                stack.pop()
                continue
            if not isinstance(current, (dict, list)):
                continue
            container_items += len(current)
            if container_items > max_container_items:
                raise ValueError(
                    "JSON container member count exceeds the configured container limit"
                )
            if depth > max_depth:
                raise ValueError("JSON nesting depth exceeds the configured depth limit")
            nested = current.values() if isinstance(current, dict) else current
            stack.append((iter(nested), depth + 1))
    except (MemoryError, RecursionError) as error:
        raise ValueError(
            "JSON resource/depth limit exceeded while checking structure"
        ) from error


def load_json_object(
    path: Path,
    *,
    max_bytes: int | None = None,
    max_container_items: int | None = None,
    max_depth: int | None = None,
) -> dict[str, object]:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    byte_limit = _strict_limit(
        max_bytes,
        name="max_bytes",
        default=DEFAULT_MAX_JSON_BYTES,
    )
    container_limit = _strict_limit(
        max_container_items,
        name="max_container_items",
        default=DEFAULT_MAX_JSON_CONTAINER_ITEMS,
    )
    depth_limit = _strict_limit(
        max_depth,
        name="max_depth",
        default=DEFAULT_MAX_JSON_DEPTH,
    )
    try:
        if path.stat().st_size > byte_limit:
            raise ValueError(
                f"JSON byte length exceeds the configured byte limit at {path}"
            )
        raw = path.read_bytes()
    except MemoryError as error:
        raise ValueError(f"JSON memory/resource limit exceeded at {path}") from error
    return load_json_object_bytes(
        raw,
        source=str(path),
        max_bytes=byte_limit,
        max_container_items=container_limit,
        max_depth=depth_limit,
    )


def load_json_object_bytes(
    raw: bytes,
    *,
    source: str,
    max_bytes: int | None = None,
    max_container_items: int | None = None,
    max_depth: int | None = None,
) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError("raw JSON document must be bytes")
    if not isinstance(source, str) or not source:
        raise TypeError("JSON source must be a non-empty string")
    byte_limit = _strict_limit(
        max_bytes,
        name="max_bytes",
        default=DEFAULT_MAX_JSON_BYTES,
    )
    container_limit = _strict_limit(
        max_container_items,
        name="max_container_items",
        default=DEFAULT_MAX_JSON_CONTAINER_ITEMS,
    )
    depth_limit = _strict_limit(
        max_depth,
        name="max_depth",
        default=DEFAULT_MAX_JSON_DEPTH,
    )
    try:
        if len(raw) > byte_limit:
            raise ValueError(
                f"JSON byte length exceeds the configured byte limit at {source}"
            )
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError(f"UTF-8 BOM is forbidden in JSON object at {source}")
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(f"invalid UTF-8 JSON object at {source}: {error}") from error
    except (MemoryError, RecursionError) as error:
        raise ValueError(
            f"JSON memory/resource/depth limit exceeded while preprocessing object at {source}"
        ) from error
    try:
        value = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_unique_json_object,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON object at {source}: {error}") from error
    except (MemoryError, RecursionError) as error:
        raise ValueError(
            f"JSON resource/depth limit exceeded while parsing object at {source}"
        ) from error
    if not isinstance(value, dict):
        raise TypeError(f"JSON value at {source} must be an object")
    _validate_json_structure(
        value,
        max_container_items=container_limit,
        max_depth=depth_limit,
    )
    return value


def _lock_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _unlock_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _local_lock_for(path: Path) -> _LocalPathLock:
    key = os.path.normcase(str(path.resolve(strict=False)))
    with _LOCAL_LOCKS_GUARD:
        entry = _LOCAL_LOCKS.get(key)
        if entry is None:
            entry = _LocalPathLock()
            _LOCAL_LOCKS[key] = entry
        return entry


def _attach_cleanup_diagnostic(
    primary: BaseException, cleanup: BaseException, action: str
) -> None:
    message = (
        f"{action} failed during lock cleanup: "
        f"{type(cleanup).__name__}: {cleanup}"
    )
    add_note = getattr(primary, "add_note", None)
    if add_note is not None:
        add_note(message)
        return
    try:
        primary.__context__ = cleanup
    except (AttributeError, TypeError):
        return


@contextmanager
def _exclusive_path_lock(lock_path: Path) -> Iterator[None]:
    local_entry = _local_lock_for(lock_path)
    with local_entry.lock:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b", buffering=0)
        locked = False
        primary_error: BaseException | None = None
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\x00")
                handle.flush()
                if hasattr(os, "fsync"):
                    os.fsync(handle.fileno())
            _lock_file(handle)
            locked = True
            try:
                yield
            except BaseException as error:
                primary_error = error
                raise
        except BaseException as error:
            if primary_error is None:
                primary_error = error
            raise
        finally:
            unlock_error: BaseException | None = None
            if locked:
                try:
                    _unlock_file(handle)
                except BaseException as error:
                    unlock_error = error
            close_error: BaseException | None = None
            try:
                handle.close()
            except BaseException as error:
                close_error = error

            if primary_error is not None:
                if unlock_error is not None:
                    _attach_cleanup_diagnostic(
                        primary_error, unlock_error, "unlock"
                    )
                if close_error is not None:
                    _attach_cleanup_diagnostic(primary_error, close_error, "close")
            elif unlock_error is not None:
                if close_error is not None:
                    _attach_cleanup_diagnostic(unlock_error, close_error, "close")
                raise unlock_error
            elif close_error is not None:
                raise close_error


def append_jsonl_locked(path: Path, value: object) -> None:
    if not isinstance(value, dict):
        raise TypeError("JSONL entries must be objects")
    encoded = canonical_json_bytes(value)
    lock_path = path.parent / f".{path.name}.lock"
    with _exclusive_path_lock(lock_path):
        previous = path.read_bytes() if path.exists() else b""
        if previous and not previous.endswith(b"\n"):
            raise ValueError(f"existing JSONL file ends with a partial line: {path}")
        atomic_write_bytes(path, previous + encoded)
