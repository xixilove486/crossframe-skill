from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re

from .constants import RUN_STATUSES
from .errors import UltraRuntimeError
from .jsonio import (
    AUTHORITY_SNAPSHOT_LOCK_FILENAME,
    _exclusive_path_lock,
    _fsync_directory,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .paths import RunLayout, _validate_run_id, assert_safe_descendant
from .status import (
    RunStatusRecord,
    _parse_utc,
    _record_from_object,
)


_POINTER_NAMES = frozenset(
    {"latest", "latest-complete", "latest-needs-attention"}
)
_POINTER_FILES = {
    "latest": "latest.json",
    "latest-complete": "latest-complete.json",
    "latest-needs-attention": "latest-needs-attention.json",
}
_GENERATION_MANIFEST_FILENAME = "generation-manifest.json"
GENERATION_MANIFEST_FILENAME = _GENERATION_MANIFEST_FILENAME
_GENERATION_SCHEMA = "crossframe.ultra.index-generation.v1"
_GENERATION_FIELDS = frozenset({"schema", "generation_id", "files"})
_GENERATION_FILE_NAMES = frozenset(
    {"runs.jsonl", "latest.json", "latest-complete.json", "latest-needs-attention.json"}
)
_SHA256_PATTERN = re.compile(r"\A[0-9a-f]{64}\Z", re.ASCII)
_PROJECTION_FIELDS = frozenset(
    {"run_id", "status", "created_at", "updated_at", "revision"}
)


class IndexError(UltraRuntimeError, RuntimeError):
    pass


def _record_to_projection(record: RunStatusRecord) -> dict[str, object]:
    return {
        "run_id": record.run_id,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "revision": record.revision,
    }


def _projection_from_object(value: dict[str, object]) -> dict[str, object]:
    if set(value) != _PROJECTION_FIELDS:
        raise ValueError("index status projection must be a closed neutral object")
    run_id = value["run_id"]
    status = value["status"]
    revision = value["revision"]
    if not isinstance(run_id, str):
        raise ValueError("index status projection run_id must be a string")
    _validate_run_id(run_id)
    if not isinstance(status, str) or status not in RUN_STATUSES:
        raise ValueError("index status projection status is invalid")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("index status projection revision is invalid")
    created_at = _parse_utc(value["created_at"], "created_at")
    updated_at = _parse_utc(value["updated_at"], "updated_at")
    if updated_at < created_at:
        raise ValueError("index status projection updated_at precedes created_at")
    return {
        "run_id": run_id,
        "status": status,
        "created_at": str(value["created_at"]),
        "updated_at": str(value["updated_at"]),
        "revision": revision,
    }


def _generation_id(files: dict[str, str | None]) -> str:
    return sha256_bytes(
        canonical_json_bytes({"schema": _GENERATION_SCHEMA, "files": files})
    )


def _generation_manifest(files: dict[str, str | None]) -> dict[str, object]:
    return {
        "schema": _GENERATION_SCHEMA,
        "generation_id": _generation_id(files),
        "files": files,
    }


def _run_layout(root: Path, run_dir: Path) -> RunLayout:
    return RunLayout(
        root=root,
        root_staging_dir=root / ".staging",
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


def _verify_complete_authority(layout: RunLayout) -> None:
    from .deliverables import verify_completed_u12_transaction

    verify_completed_u12_transaction(layout)


class IndexStore:
    def __init__(self, root: Path):
        if not isinstance(root, Path):
            raise TypeError("root must be a pathlib.Path")
        if not root.is_absolute():
            raise ValueError("index root must be absolute")
        self.root = root
        self.index_dir = root / "index"
        self.runs_path = self.index_dir / "runs.jsonl"
        self.lock_path = self.index_dir / ".rebuild.lock"
        self.generation_manifest_path = (
            self.index_dir / _GENERATION_MANIFEST_FILENAME
        )
        # Keep a descriptive alias available to callers that refer to the marker
        # as the current generation rather than as a manifest.
        self.generation_path = self.generation_manifest_path
        self.authority_lock_path = root / AUTHORITY_SNAPSHOT_LOCK_FILENAME
        assert_safe_descendant(root, self.index_dir)
        assert_safe_descendant(root, self.runs_path)
        assert_safe_descendant(root, self.lock_path)
        assert_safe_descendant(self.root, self.generation_manifest_path)
        assert_safe_descendant(root, self.authority_lock_path)

    def _pointer_path(self, name: str) -> Path:
        if not isinstance(name, str) or name not in _POINTER_NAMES:
            raise ValueError(f"unknown index pointer name: {name!r}")
        path = self.index_dir / f"{name}.json"
        assert_safe_descendant(self.root, path)
        return path

    def _scan_authorities(self) -> list[tuple[Path, RunStatusRecord]]:
        runs_dir = self.root / "runs"
        assert_safe_descendant(self.root, runs_dir)
        if not runs_dir.exists():
            return []
        records: list[tuple[Path, RunStatusRecord]] = []
        for status_path in sorted(runs_dir.glob("*/*/*/run-status.json")):
            assert_safe_descendant(self.root, status_path)
            run_id = status_path.parent.name
            try:
                _validate_run_id(run_id)
                relative = status_path.relative_to(self.root)
                if relative.parts != (
                    "runs",
                    run_id[:4],
                    run_id[4:6],
                    run_id,
                    "run-status.json",
                ):
                    raise ValueError("run status authority is in the wrong bundle path")
                value = load_json_object(status_path)
                record = _record_from_object(value, run_id)
                if record.status == "complete":
                    _verify_complete_authority(
                        _run_layout(self.root, status_path.parent)
                    )
            except (OSError, TypeError, ValueError, RuntimeError) as error:
                raise IndexError(
                    f"invalid run-status authority at {status_path}: {error}"
                ) from error
            records.append((status_path.parent, record))
        records.sort(key=lambda item: (_parse_utc(item[1].updated_at, "updated_at"), item[1].run_id))
        return records

    @staticmethod
    def _latest(
        records: list[tuple[Path, RunStatusRecord]],
        status: str | None = None,
    ) -> RunStatusRecord | None:
        candidates = [
            record
            for _, record in records
            if status is None or record.status == status
        ]
        return candidates[-1] if candidates else None

    def _write_pointer(self, name: str, record: RunStatusRecord | None) -> None:
        path = self._pointer_path(name)
        if record is None:
            try:
                path.unlink()
            except FileNotFoundError:
                return
            _fsync_directory(path.parent)
            return
        atomic_write_json(path, _record_to_projection(record))

    def _expected_pointer_bytes(
        self, records: list[tuple[Path, RunStatusRecord]]
    ) -> dict[str, bytes | None]:
        return {
            _POINTER_FILES["latest"]: (
                None
                if (record := self._latest(records)) is None
                else canonical_json_bytes(_record_to_projection(record))
            ),
            _POINTER_FILES["latest-complete"]: (
                None
                if (record := self._latest(records, "complete")) is None
                else canonical_json_bytes(_record_to_projection(record))
            ),
            _POINTER_FILES["latest-needs-attention"]: (
                None
                if (record := self._latest(records, "needs_attention")) is None
                else canonical_json_bytes(_record_to_projection(record))
            ),
        }

    @staticmethod
    def _cache_file_hashes(
        runs_bytes: bytes, pointer_bytes: dict[str, bytes | None]
    ) -> dict[str, str | None]:
        if not isinstance(runs_bytes, bytes):
            raise TypeError("runs cache must be bytes")
        if set(pointer_bytes) != {
            "latest.json",
            "latest-complete.json",
            "latest-needs-attention.json",
        }:
            raise ValueError("pointer cache set is incomplete")
        return {
            "runs.jsonl": sha256_bytes(runs_bytes),
            **{
                name: None if value is None else sha256_bytes(value)
                for name, value in pointer_bytes.items()
            },
        }

    def _read_generation_manifest(self) -> dict[str, object]:
        path = self.generation_manifest_path
        assert_safe_descendant(self.root, path)
        try:
            raw = path.read_bytes()
        except FileNotFoundError as error:
            raise IndexError(
                "index cache needs rebuild: generation manifest is missing"
            ) from error
        except OSError as error:
            raise IndexError(
                f"index cache needs rebuild: cannot read generation manifest: {path}"
            ) from error
        try:
            value = load_json_object(path)
        except (OSError, TypeError, ValueError) as error:
            raise IndexError(
                f"index cache needs rebuild: generation manifest is corrupt: {path}"
            ) from error
        if canonical_json_bytes(value) != raw:
            raise IndexError(
                "index cache needs rebuild: generation manifest is not canonical"
            )
        if set(value) != _GENERATION_FIELDS:
            raise IndexError(
                "index cache needs rebuild: generation manifest fields are invalid"
            )
        if value["schema"] != _GENERATION_SCHEMA:
            raise IndexError(
                "index cache needs rebuild: generation manifest schema is invalid"
            )
        generation_id = value["generation_id"]
        if (
            not isinstance(generation_id, str)
            or _SHA256_PATTERN.fullmatch(generation_id) is None
        ):
            raise IndexError(
                "index cache needs rebuild: generation manifest id is invalid"
            )
        files = value["files"]
        if not isinstance(files, dict) or set(files) != _GENERATION_FILE_NAMES:
            raise IndexError(
                "index cache needs rebuild: generation manifest file set is invalid"
            )
        typed_files: dict[str, str | None] = {}
        for name in sorted(_GENERATION_FILE_NAMES):
            digest = files[name]
            if digest is not None and (
                not isinstance(digest, str)
                or _SHA256_PATTERN.fullmatch(digest) is None
            ):
                raise IndexError(
                    f"index cache needs rebuild: invalid hash for {name}"
                )
            typed_files[name] = digest
        if generation_id != _generation_id(typed_files):
            raise IndexError(
                "index cache needs rebuild: generation manifest id does not match files"
            )
        return {
            "schema": _GENERATION_SCHEMA,
            "generation_id": generation_id,
            "files": typed_files,
        }

    def _read_cache_file(self, path: Path, name: str) -> bytes:
        assert_safe_descendant(self.root, path)
        try:
            return path.read_bytes()
        except FileNotFoundError as error:
            raise IndexError(
                f"index cache needs rebuild: generation file is missing: {name}"
            ) from error
        except OSError as error:
            raise IndexError(
                f"index cache needs rebuild: cannot read generation file: {name}"
            ) from error

    @staticmethod
    def _decode_runs(
        raw: bytes,
    ) -> list[dict[str, object]]:
        if not isinstance(raw, bytes):
            raise TypeError("runs cache must be bytes")
        if raw == b"":
            return []
        records: list[dict[str, object]] = []
        for line in raw.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise IndexError(
                    "index cache needs rebuild: runs.jsonl has a partial line"
                )
            try:
                value = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise IndexError(
                    "index cache needs rebuild: runs.jsonl contains invalid JSON"
                ) from error
            if not isinstance(value, dict):
                raise IndexError(
                    "index cache needs rebuild: runs.jsonl rows must be objects"
                )
            if canonical_json_bytes(value) != line:
                raise IndexError(
                    "index cache needs rebuild: runs.jsonl is not canonical"
                )
            try:
                record = _projection_from_object(value)
            except (TypeError, ValueError, RuntimeError) as error:
                raise IndexError(
                    "index cache needs rebuild: invalid runs.jsonl projection row"
                ) from error
            records.append(record)
        if len({str(record["run_id"]) for record in records}) != len(records):
            raise IndexError(
                "index cache needs rebuild: runs.jsonl contains duplicate run IDs"
            )
        expected_order = sorted(
            records,
            key=lambda record: (
                _parse_utc(record["updated_at"], "updated_at"),
                str(record["run_id"]),
            ),
        )
        if records != expected_order:
            raise IndexError(
                "index cache needs rebuild: runs.jsonl rows are not in canonical order"
            )
        return records

    def _validate_generation(self) -> dict[str, dict[str, object] | None]:
        manifest = self._read_generation_manifest()
        files = manifest["files"]
        assert isinstance(files, dict)
        runs_raw = self._read_cache_file(self.runs_path, "runs.jsonl")
        if sha256_bytes(runs_raw) != files["runs.jsonl"]:
            raise IndexError(
                "index cache needs rebuild: runs.jsonl hash does not match generation"
            )
        records = self._decode_runs(runs_raw)
        projections = {str(record["run_id"]): record for record in records}
        pointers: dict[str, dict[str, object] | None] = {}
        for name, filename in _POINTER_FILES.items():
            path = self._pointer_path(name)
            expected_hash = files[filename]
            if expected_hash is None:
                if path.exists():
                    raise IndexError(
                        f"index cache needs rebuild: unexpected {filename} in generation"
                    )
                pointers[name] = None
                continue
            raw = self._read_cache_file(path, filename)
            if sha256_bytes(raw) != expected_hash:
                raise IndexError(
                    f"index cache needs rebuild: {filename} hash does not match generation"
                )
            try:
                value = load_json_object(path)
            except (OSError, TypeError, ValueError) as error:
                raise IndexError(
                    f"index cache needs rebuild: {filename} is corrupt"
                ) from error
            if canonical_json_bytes(value) != raw:
                raise IndexError(
                    f"index cache needs rebuild: {filename} is not canonical"
                )
            try:
                projection = _projection_from_object(value)
            except (TypeError, ValueError, RuntimeError) as error:
                raise IndexError(
                    f"index cache needs rebuild: {filename} is invalid"
                ) from error
            run_id = str(projection["run_id"])
            if projections.get(run_id) != projection:
                raise IndexError(
                    f"index cache needs rebuild: {filename} does not match runs.jsonl"
                )
            pointers[name] = projection

        def expected_pointer(status: str | None) -> dict[str, object] | None:
            candidates = [
                record
                for record in records
                if status is None or record["status"] == status
            ]
            return None if not candidates else candidates[-1]

        expected = {
            "latest": expected_pointer(None),
            "latest-complete": expected_pointer("complete"),
            "latest-needs-attention": expected_pointer("needs_attention"),
        }
        if pointers != expected:
            raise IndexError(
                "index cache needs rebuild: pointers do not match runs.jsonl generation"
            )
        return pointers

    def _invalidate_generation_manifest(self) -> None:
        try:
            self.generation_manifest_path.unlink()
        except FileNotFoundError:
            return
        except OSError:
            return
        try:
            _fsync_directory(self.generation_manifest_path.parent)
        except OSError:
            return

    @staticmethod
    def _run_start_here(record: RunStatusRecord) -> bytes:
        text = (
            "# CrossFrame Ultra run\n\n"
            f"- run_id: {record.run_id}\n"
            f"- status: {record.status}\n"
            f"- created_at: {record.created_at}\n"
            f"- updated_at: {record.updated_at}\n"
            "- status authority: run-status.json\n"
            "- input: input/\n"
            "- authoring: work/authoring/\n"
            "- artifacts: artifacts/\n"
            "- delivery: delivery/\n"
            "- validation: validation/\n"
            "- recovery: recovery/\n"
            "- logs: logs/\n"
        )
        return text.encode("utf-8")

    @staticmethod
    def _root_start_here(records: list[tuple[Path, RunStatusRecord]]) -> bytes:
        lines = [
            "# CrossFrame Ultra runs",
            "",
            "- run index: index/runs.jsonl",
            "- latest: index/latest.json",
            "- latest complete: index/latest-complete.json",
            "- latest needs attention: index/latest-needs-attention.json",
            "",
            "## Runs",
            "",
        ]
        for _, record in records:
            navigation = (
                f"runs/{record.run_id[:4]}/{record.run_id[4:6]}/"
                f"{record.run_id}/START-HERE.md"
            )
            lines.append(
                f"- {record.run_id} | {record.status} | {record.created_at} | "
                f"{record.updated_at} | {navigation}"
            )
        return ("\n".join(lines) + "\n").encode("utf-8")

    def rebuild(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        with _exclusive_path_lock(self.authority_lock_path):
            assert_safe_descendant(self.root, self.authority_lock_path)
            with _exclusive_path_lock(self.lock_path):
                assert_safe_descendant(self.root, self.index_dir)
                records = self._scan_authorities()
                runs_bytes = b"".join(
                    canonical_json_bytes(_record_to_projection(record))
                    for _, record in records
                )
                pointer_records = {
                    "latest": self._latest(records),
                    "latest-complete": self._latest(records, "complete"),
                    "latest-needs-attention": self._latest(
                        records, "needs_attention"
                    ),
                }
                pointer_bytes = self._expected_pointer_bytes(records)
                atomic_write_bytes(self.runs_path, runs_bytes)
                for name in _POINTER_FILES:
                    self._write_pointer(name, pointer_records[name])
                for run_dir, record in records:
                    start_here = run_dir / "START-HERE.md"
                    assert_safe_descendant(self.root, start_here)
                    atomic_write_bytes(start_here, self._run_start_here(record))
                root_start_here = self.root / "START-HERE.md"
                assert_safe_descendant(self.root, root_start_here)
                atomic_write_bytes(
                    root_start_here, self._root_start_here(records)
                )
                files = self._cache_file_hashes(runs_bytes, pointer_bytes)
                manifest = _generation_manifest(files)
                try:
                    atomic_write_json(self.generation_manifest_path, manifest)
                    self._validate_generation()
                except BaseException:
                    self._invalidate_generation_manifest()
                    raise

    def read_pointer(self, name: str) -> dict[str, object] | None:
        path = self._pointer_path(name)
        with _exclusive_path_lock(self.authority_lock_path):
            assert_safe_descendant(self.root, self.authority_lock_path)
            with _exclusive_path_lock(self.lock_path):
                assert_safe_descendant(self.root, self.lock_path)
                pointers = self._validate_generation()
                records = self._scan_authorities()
                value = pointers[name]
                expected = self._expected_pointer_bytes(records)[
                    _POINTER_FILES[name]
                ]
                cached = (
                    None if value is None else canonical_json_bytes(value)
                )
                if cached != expected:
                    raise IndexError(
                        f"index pointer {name} is stale: cached value differs from "
                        "the run-status authority candidate set"
                    )
                if value is None:
                    return None
                return value
