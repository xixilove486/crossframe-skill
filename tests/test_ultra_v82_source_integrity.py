from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
)
SOURCE_DOCX = Path(r"E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx")


def _require_source_docx() -> Path:
    if not SOURCE_DOCX.is_file():
        pytest.skip(f"external v8.2 source is unavailable: {SOURCE_DOCX}")
    return SOURCE_DOCX


def _load_checker():
    if not CHECKER_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("ultra_v82_source_checker", CHECKER_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


def test_checker_exposes_read_only_validation_api() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    assert callable(checker.validate_committed_source_snapshot)
    assert callable(checker.validate_committed_source_tree)
    assert callable(checker.validate_against_docx)
    assert callable(checker.main)
    assert not hasattr(checker, "generate_authority_tree")
    assert not hasattr(checker, "_write_tree_files")
    assert not hasattr(checker, "_render_authority_files")
    assert not hasattr(checker, "_render_index_files")
    assert not hasattr(checker, "_manifest_payload")


def test_verified_snapshot_exposes_one_frozen_authority_view() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    snapshot = checker.validate_committed_source_snapshot(ROOT)
    assert snapshot.errors == ()
    assert snapshot.manifest_bytes == (
        ROOT / "skills/crossframe-ultra/references/source-manifest.json"
    ).read_bytes()
    assert snapshot.manifest is not None
    assert snapshot.manifest["raw_sha256"] == checker.RAW_SHA256
    assert snapshot.compiler_bytes == (
        ROOT
        / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
    ).read_bytes()
    assert set(snapshot.files) == checker.EXPECTED_TREE_FILES
    assert len(snapshot.paragraphs) == checker.EXPECTED_PARAGRAPHS
    assert len(snapshot.tables) == checker.EXPECTED_TABLES
    with pytest.raises(TypeError):
        snapshot.files["not-authority.md"] = b"tamper"
    with pytest.raises(TypeError):
        snapshot.paragraphs[0]["text"] = "tamper"
    with pytest.raises(TypeError):
        snapshot.manifest["compiler"]["sha256"] = "tamper"
    with pytest.raises(AttributeError):
        snapshot.manifest["files"].append({"path": "tamper"})
    with pytest.raises(TypeError):
        snapshot.tables[0]["rows"][0][0] = "tamper"


def test_committed_snapshot_reads_each_authority_file_once(monkeypatch: pytest.MonkeyPatch) -> None:
    assert checker is not None, "Task3 checker is not implemented"
    original = checker._read_regular_file
    counts: dict[Path, int] = {}

    def counted(path: Path, *args, **kwargs) -> bytes:
        absolute = Path(os.path.abspath(path))
        counts[absolute] = counts.get(absolute, 0) + 1
        return original(path, *args, **kwargs)

    monkeypatch.setattr(checker, "_read_regular_file", counted)
    snapshot = checker.validate_committed_source_snapshot(ROOT)
    assert snapshot.errors == ()
    expected = {
        Path(os.path.abspath(ROOT / checker.MANIFEST_RELATIVE)),
        Path(os.path.abspath(ROOT / snapshot.manifest["compiler"]["path"])),
        *(
            Path(os.path.abspath(ROOT / checker.SOURCE_TREE_RELATIVE / relative))
            for relative in checker.EXPECTED_TREE_FILES
        ),
    }
    assert set(counts) == expected
    assert all(counts[path] == 1 for path in expected)


def test_authority_byte_budgets_are_explicit_and_cover_the_frozen_inputs() -> None:
    assert checker.MAX_SOURCE_TREE_FILE_BYTES == 2 * 1024 * 1024
    assert checker.MAX_SOURCE_TREE_BYTES == 8 * 1024 * 1024
    assert checker.MAX_SOURCE_MANIFEST_BYTES == 2 * 1024 * 1024
    assert checker.MAX_SOURCE_COMPILER_BYTES == 1 * 1024 * 1024
    assert checker.MAX_CAPTURED_AUTHORITY_BYTES == 12 * 1024 * 1024
    assert checker.MAX_SOURCE_DOCX_BYTES == 8 * 1024 * 1024
    assert checker.MAX_SOURCE_TREE_ENTRIES == 256
    assert checker.MAX_SOURCE_TREE_DEPTH == 2

    tree = ROOT / checker.SOURCE_TREE_RELATIVE
    tree_files = tuple(path for path in tree.rglob("*") if path.is_file())
    assert max(path.stat().st_size for path in tree_files) < checker.MAX_SOURCE_TREE_FILE_BYTES
    assert sum(path.stat().st_size for path in tree_files) < checker.MAX_SOURCE_TREE_BYTES
    assert (ROOT / checker.MANIFEST_RELATIVE).stat().st_size < checker.MAX_SOURCE_MANIFEST_BYTES
    assert (
        ROOT / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
    ).stat().st_size < checker.MAX_SOURCE_COMPILER_BYTES


def test_initial_oversize_is_rejected_before_the_read_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = tmp_path / "authority.bin"
    authority.write_bytes(b"x" * 17)
    callback_called = False

    def forbidden_read(_self) -> bytes:
        nonlocal callback_called
        callback_called = True
        raise AssertionError("oversize input must be rejected before reading")

    monkeypatch.setattr(checker._AnchoredRegularFile, "read_all", forbidden_read)
    with pytest.raises(ValueError, match="exceeds.*limit|limit.*exceeds"):
        checker._read_regular_file(
            authority,
            anchor=tmp_path,
            max_bytes=16,
            label="test authority",
        )
    assert callback_called is False


def test_bounded_chunk_reader_never_consumes_beyond_initial_size_plus_one() -> None:
    requests: list[int] = []

    def growing_read(amount: int) -> bytes:
        requests.append(amount)
        return b"x" * amount

    payload = checker._read_bounded_chunks(
        growing_read,
        initial_size=4,
        max_bytes=8,
    )
    assert payload == b"x" * 5
    assert sum(requests) == 5


def test_growth_after_open_is_rejected_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = tmp_path / "authority.bin"
    authority.write_bytes(b"safe")
    callback_calls = 0

    def grew_after_open() -> bytes:
        nonlocal callback_calls
        callback_calls += 1
        return b"x" * 9

    opened = checker._AnchoredRegularFile(
        final_path=authority,
        identity=(1, 2),
        size=4,
        _read_and_verify=grew_after_open,
    )

    @contextmanager
    def fake_open(*_args, **_kwargs):
        yield opened

    monkeypatch.setattr(checker, "_open_anchored_regular_file", fake_open)
    with pytest.raises(ValueError, match="grew|exceeds|changed"):
        checker._read_regular_file(
            authority,
            anchor=tmp_path,
            max_bytes=8,
            label="test authority",
        )
    assert callback_calls == 1


def test_source_tree_total_budget_rejects_before_adding_the_excess_file(
    tmp_path: Path,
) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a.md").write_bytes(b"a" * 4)
    (tree / "b.md").write_bytes(b"b" * 4)

    files, errors = checker._walk_regular_tree(
        tree,
        anchor=tree,
        max_file_bytes=8,
        max_total_bytes=7,
    )
    assert files == {"a.md": b"a" * 4}
    assert any("total" in error.lower() and "limit" in error.lower() for error in errors)


def test_tree_walk_consumes_direntry_metadata_before_scan_handle_closes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    payload = tree / "record.md"
    payload.write_bytes(b"authority")
    state = {"closed": False}

    class LifetimeBoundEntry:
        name = payload.name

        def _require_open(self) -> None:
            if state["closed"]:
                raise OSError(9, "Bad file descriptor")

        def stat(self, *, follow_symlinks: bool = True):
            self._require_open()
            return payload.stat(follow_symlinks=follow_symlinks)

        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            self._require_open()
            return payload.is_dir()

        def is_file(self, *, follow_symlinks: bool = True) -> bool:
            self._require_open()
            return payload.is_file()

    class LifetimeBoundScandir:
        def __enter__(self):
            return iter((LifetimeBoundEntry(),))

        def __exit__(self, _error_type, _error, _traceback) -> None:
            state["closed"] = True

    class LifetimeBoundDirectory:
        def scandir(self) -> LifetimeBoundScandir:
            return LifetimeBoundScandir()

    @contextmanager
    def fake_open_anchored_directory(*_args, **_kwargs):
        yield LifetimeBoundDirectory()

    monkeypatch.setattr(
        checker,
        "_open_anchored_directory",
        fake_open_anchored_directory,
    )

    files, errors = checker._walk_regular_tree(tree, anchor=tree)

    assert state["closed"] is True
    assert files == {"record.md": b"authority"}
    assert errors == []


def test_authority_tree_rejects_unknown_directory_without_descending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "known.md").write_bytes(b"known")
    unknown = tree / "unknown"
    unknown.mkdir()
    hidden = unknown / "payload.md"
    hidden.write_bytes(b"must-not-be-read")
    reads: list[Path] = []
    original = checker._read_regular_file

    def tracked(path: Path, *args, **kwargs) -> bytes:
        reads.append(Path(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(checker, "_read_regular_file", tracked)
    files, errors = checker._walk_regular_tree(
        tree,
        anchor=tree,
        expected_files=frozenset({"known.md"}),
    )

    assert files == {"known.md": b"known"}
    assert hidden not in reads
    assert any("unknown directory" in error.lower() for error in errors)


def test_authority_tree_rejects_more_than_256_entries(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    for number in range(checker.MAX_SOURCE_TREE_ENTRIES + 1):
        (tree / f"entry-{number:03d}.md").write_bytes(b"")

    _files, errors = checker._walk_regular_tree(tree, anchor=tree)

    assert any("entry" in error.lower() and "256" in error for error in errors)


def test_authority_tree_rejects_depth_beyond_two_before_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = tmp_path / "tree"
    payload = tree / "allowed" / "nested" / "payload.md"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"must-not-be-read")
    reads: list[Path] = []
    original = checker._read_regular_file

    def tracked(path: Path, *args, **kwargs) -> bytes:
        reads.append(Path(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(checker, "_read_regular_file", tracked)
    _files, errors = checker._walk_regular_tree(
        tree,
        anchor=tree,
        expected_files=frozenset({"allowed/nested/payload.md"}),
    )

    assert payload not in reads
    assert any("depth" in error.lower() and "2" in error for error in errors)


def test_captured_authority_total_budget_is_enforced_before_compiler_read(
    committed_copy: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = committed_copy / checker.SOURCE_TREE_RELATIVE
    tree_size = sum(path.stat().st_size for path in tree.rglob("*") if path.is_file())
    manifest_size = (committed_copy / checker.MANIFEST_RELATIVE).stat().st_size
    compiler_path = (
        committed_copy
        / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
    )
    compiler_size = compiler_path.stat().st_size
    monkeypatch.setattr(
        checker,
        "MAX_CAPTURED_AUTHORITY_BYTES",
        tree_size + manifest_size + compiler_size - 1,
    )
    original = checker._AnchoredRegularFile.read_all

    def guarded_read(opened) -> bytes:
        if opened.final_path == Path(os.path.abspath(compiler_path)):
            raise AssertionError("captured total oversize must reject before compiler read")
        return original(opened)

    monkeypatch.setattr(checker._AnchoredRegularFile, "read_all", guarded_read)
    errors = checker.validate_committed_source_tree(committed_copy)

    assert any("captured" in error.lower() and "limit" in error.lower() for error in errors)


def test_committed_authority_tree_is_self_consistent() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    errors = checker.validate_committed_source_tree(ROOT)
    assert errors == [], errors


def test_source_aware_validation_accepts_the_exact_v82_docx() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    errors = checker.validate_against_docx(ROOT, _require_source_docx())
    assert errors == [], errors


@pytest.fixture()
def committed_copy(tmp_path: Path) -> Path:
    """Make a minimal repository copy suitable for corruption/replay tests."""
    repo = tmp_path / "repo"
    references = repo / "skills/crossframe-ultra/references"
    references.mkdir(parents=True)
    shutil.copy2(ROOT / "skills/crossframe-ultra/references/source-manifest.json", references)
    shutil.copytree(
        ROOT / "skills/crossframe-ultra/references/v8.2-full-source",
        references / "v8.2-full-source",
    )
    compiler = repo / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
    compiler.parent.mkdir(parents=True)
    shutil.copy2(
        ROOT / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py",
        compiler,
    )
    return repo


def _manifest(repo: Path) -> dict:
    return json.loads(
        (repo / "skills/crossframe-ultra/references/source-manifest.json").read_text(
            encoding="utf-8"
        )
    )


def _refresh_file_inventory(repo: Path) -> None:
    tree = repo / "skills/crossframe-ultra/references/v8.2-full-source"
    files, errors = checker._walk_regular_tree(tree)
    assert errors == []
    manifest_path = repo / "skills/crossframe-ultra/references/source-manifest.json"
    manifest = _manifest(repo)
    manifest["files"] = checker._expected_file_entries(files)
    manifest["source_tree_merkle_root"] = checker._tree_merkle_root(files)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _replace_json_block(path: Path, marker: str, payload: object) -> None:
    text = path.read_text(encoding="utf-8")
    if marker == "canonical":
        pattern = re.compile(
            r"(<!-- canonical-records:start -->\n```json\n)(.*?)(\n```\n<!-- canonical-records:end -->)",
            re.DOTALL,
        )
    elif marker == "rows":
        pattern = re.compile(
            r"(<!-- table-rows:start -->\n```json\n)(.*?)(\n```\n<!-- table-rows:end -->)",
            re.DOTALL,
        )
    else:
        pattern = re.compile(
            r"(<!-- cell-paragraph-anchors:start -->\n```json\n)(.*?)(\n```\n<!-- cell-paragraph-anchors:end -->)",
            re.DOTALL,
        )
    replacement = r"\1" + json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + r"\3"
    changed, count = pattern.subn(replacement, text, count=1)
    assert count == 1
    path.write_text(changed, encoding="utf-8", newline="\n")


def test_equal_count_paragraph_mutation_is_rejected(committed_copy: Path) -> None:
    path = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/01-guide.md"
    text = path.read_text(encoding="utf-8")
    payload_match = re.search(
        r"<!-- canonical-records:start -->\n```json\n(.*?)\n```\n<!-- canonical-records:end -->",
        text,
        re.DOTALL,
    )
    assert payload_match
    payload = json.loads(payload_match.group(1))
    payload["paragraphs"][0]["text"] += "（篡改）"
    _replace_json_block(path, "canonical", payload)
    assert checker.validate_committed_source_tree(committed_copy)


def test_reordered_table_cells_are_rejected(committed_copy: Path) -> None:
    path = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/tables/V82-T001.md"
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- canonical-records:start -->\n```json\n(.*?)\n```\n<!-- canonical-records:end -->",
        text,
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    payload["rows"][0][0], payload["rows"][0][1] = payload["rows"][0][1], payload["rows"][0][0]
    _replace_json_block(path, "canonical", payload)
    _replace_json_block(path, "rows", payload["rows"])
    _refresh_file_inventory(committed_copy)
    assert any("table" in error.lower() for error in checker.validate_committed_source_tree(committed_copy))


def test_wrong_cell_paragraph_binding_is_rejected(committed_copy: Path) -> None:
    path = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/tables/V82-T001.md"
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- canonical-records:start -->\n```json\n(.*?)\n```\n<!-- canonical-records:end -->",
        text,
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    first = payload["cell_paragraph_ordinals"][0][0][0]
    payload["cell_paragraph_ordinals"][0][0][0] = payload["cell_paragraph_ordinals"][0][1][0]
    payload["cell_paragraph_ordinals"][0][1][0] = first
    _replace_json_block(path, "canonical", payload)
    _replace_json_block(path, "cells", payload["cell_paragraph_ordinals"])
    _refresh_file_inventory(committed_copy)
    assert any("binding" in error.lower() or "table" in error.lower() for error in checker.validate_committed_source_tree(committed_copy))


def test_duplicate_or_missing_anchor_is_rejected(committed_copy: Path) -> None:
    path = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/01-guide.md"
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- canonical-records:start -->\n```json\n(.*?)\n```\n<!-- canonical-records:end -->",
        text,
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    duplicate = payload["paragraphs"][1]["anchor"]
    payload["paragraphs"][2]["anchor"] = duplicate
    _replace_json_block(path, "canonical", payload)
    text = path.read_text(encoding="utf-8")
    text = text.replace("source-paragraph:V82-P0352", "source-paragraph:V82-P0351", 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    _refresh_file_inventory(committed_copy)
    assert any("anchor" in error.lower() for error in checker.validate_committed_source_tree(committed_copy))


def test_manifest_missing_extra_and_stale_hashes_are_rejected(committed_copy: Path) -> None:
    tree = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source"
    (tree / "01-guide.md").unlink()
    (tree / "unexpected.md").write_text("unexpected", encoding="utf-8")
    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("missing generated file" in error for error in errors)
    assert any("unexpected generated file" in error for error in errors)

    # Restore the tree, then corrupt a manifest byte hash without touching the
    # source files; the checker must distrust the manifest rather than accept it.
    shutil.copy2(ROOT / "skills/crossframe-ultra/references/v8.2-full-source/01-guide.md", tree)
    (tree / "unexpected.md").unlink()
    manifest = _manifest(committed_copy)
    manifest["files"][0]["sha256"] = "0" * 64
    (committed_copy / "skills/crossframe-ultra/references/source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    assert any("manifest" in error.lower() for error in checker.validate_committed_source_tree(committed_copy))


def test_old_v8_anchor_injection_and_partial_promotion_are_rejected(committed_copy: Path) -> None:
    index = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/00-index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\nlegacy V8-P0001\n", encoding="utf-8", newline="\n")
    _refresh_file_inventory(committed_copy)
    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("old V8-P" in error for error in errors)

    index.write_text(index.read_text(encoding="utf-8").replace("legacy V8-P0001", ""), encoding="utf-8", newline="\n")
    (committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/20-appendix-d-common-kernel-mapping.md").unlink()
    assert any("missing generated file" in error for error in checker.validate_committed_source_tree(committed_copy))


def test_reparse_or_symlink_entry_is_rejected(committed_copy: Path) -> None:
    target = committed_copy / "skills/crossframe-ultra/references/v8.2-full-source/00-index.md"
    external = committed_copy / "outside.md"
    external.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        target.unlink()
        target.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this workstation")
    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("symlink" in error.lower() or "reparse" in error.lower() for error in errors)


def _tree_state(root: Path) -> dict[str, tuple[str, int, int, str | None]]:
    state: dict[str, tuple[str, int, int, str | None]] = {}
    for path in sorted(root.rglob("*")):
        metadata = path.lstat()
        relative = path.relative_to(root).as_posix()
        if path.is_file() and not path.is_symlink():
            digest = sha256(path.read_bytes()).hexdigest()
            kind = "file"
        elif path.is_dir() and not path.is_symlink():
            digest = None
            kind = "directory"
        else:
            digest = None
            kind = "link"
        state[relative] = (kind, metadata.st_size, metadata.st_mtime_ns, digest)
    return state


def _recursive_file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_whole_tree_validation_is_read_only_and_writes_no_bytecode(
    committed_copy: Path,
) -> None:
    before = _tree_state(committed_copy)
    before_hashes = _recursive_file_hashes(committed_copy)
    snapshot = checker.validate_committed_source_snapshot(committed_copy)
    after = _tree_state(committed_copy)
    assert snapshot.errors == ()
    assert after == before
    assert _recursive_file_hashes(committed_copy) == before_hashes
    assert not list(committed_copy.rglob("*.pyc"))
    assert not list(committed_copy.rglob("__pycache__"))


def test_validate_paths_do_not_call_mutating_filesystem_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority_tree = ROOT / checker.SOURCE_TREE_RELATIVE
    source_docx = _require_source_docx()
    before_hashes = _recursive_file_hashes(authority_tree)

    def forbidden_mutation(*_args, **_kwargs):
        raise AssertionError("read-only checker attempted a filesystem mutation")

    for owner, name in (
        (Path, "write_bytes"),
        (Path, "write_text"),
        (Path, "mkdir"),
        (Path, "unlink"),
        (Path, "replace"),
        (os, "mkdir"),
        (os, "unlink"),
        (os, "replace"),
        (shutil, "rmtree"),
    ):
        monkeypatch.setattr(owner, name, forbidden_mutation)

    assert checker.validate_committed_source_tree(ROOT) == []
    assert checker.validate_against_docx(ROOT, source_docx) == []
    assert _recursive_file_hashes(authority_tree) == before_hashes


def test_manifest_duplicate_key_is_rejected(committed_copy: Path) -> None:
    manifest_path = committed_copy / checker.MANIFEST_RELATIVE
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace(
        '  "schema_version": 1,',
        '  "schema_version": 1,\n  "schema_version": 1,',
        1,
    )
    manifest_path.write_text(text, encoding="utf-8", newline="\n")

    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("duplicate" in error.lower() and "schema_version" in error for error in errors)


def test_manifest_non_finite_number_is_rejected(committed_copy: Path) -> None:
    manifest_path = committed_copy / checker.MANIFEST_RELATIVE
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace('  "schema_version": 1,', '  "schema_version": NaN,', 1)
    manifest_path.write_text(text, encoding="utf-8", newline="\n")

    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("non-finite" in error.lower() for error in errors)


def test_manifest_utf8_bom_is_rejected(committed_copy: Path) -> None:
    manifest_path = committed_copy / checker.MANIFEST_RELATIVE
    manifest_path.write_bytes(b"\xef\xbb\xbf" + manifest_path.read_bytes())

    errors = checker.validate_committed_source_tree(committed_copy)
    assert any("bom" in error.lower() for error in errors)


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        ('{"value": 1, "value": 2}', "duplicate"),
        ('\ufeff{"value": 1}', "bom"),
        ('{"value": NaN}', "non-finite"),
        ('{"value": Infinity}', "non-finite"),
        ('{"value": -Infinity}', "non-finite"),
    ),
)
def test_canonical_record_json_is_strict_at_every_json_extension(
    payload: str,
    message: str,
) -> None:
    content = (
        "<!-- canonical-records:start -->\n"
        "```json\n"
        f"{payload}\n"
        "```\n"
        "<!-- canonical-records:end -->"
    )
    errors: list[str] = []

    assert checker._canonical_block(content, "canonical", errors) is None
    assert any(message in error.lower() for error in errors)


@pytest.mark.parametrize(
    ("marker", "payload", "message"),
    (
        ("rows", '[{"value": 1, "value": 2}]', "duplicate"),
        ("rows", '\ufeff[]', "bom"),
        ("cells", '[NaN]', "non-finite"),
        ("cells", '[Infinity]', "non-finite"),
    ),
)
def test_table_display_json_blocks_use_the_strict_decoder(
    marker: str,
    payload: str,
    message: str,
) -> None:
    expected = {
        "anchor": "V82-T001",
        "rows": [],
        "cell_paragraph_ordinals": [],
    }
    rows = payload if marker == "rows" else "[]"
    cells = payload if marker == "cells" else "[]"
    content = (
        f"Raw SHA256: `{checker.RAW_SHA256}`\n"
        f"Semantic SHA256: `{checker.SEMANTIC_SHA256}`\n"
        "<!-- canonical-records:start -->\n"
        "```json\n"
        f"{json.dumps(expected)}\n"
        "```\n"
        "<!-- canonical-records:end -->\n"
        "<!-- table-rows:start -->\n"
        "```json\n"
        f"{rows}\n"
        "```\n"
        "<!-- table-rows:end -->\n"
        "<!-- cell-paragraph-anchors:start -->\n"
        "```json\n"
        f"{cells}\n"
        "```\n"
        "<!-- cell-paragraph-anchors:end -->\n"
    )
    errors: list[str] = []

    checker._validate_table_file(
        content,
        expected,
        checker.RAW_SHA256,
        checker.SEMANTIC_SHA256,
        errors,
    )

    assert any(message in error.lower() for error in errors)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ('  "schema_version": 1,', '  "schema_version": true,'),
        ('  "normalization_version": 1,', '  "normalization_version": 1.0,'),
        ('      "ordinal": 1,', '      "ordinal": true,'),
    ),
)
def test_manifest_rejects_numeric_type_confusion(
    committed_copy: Path,
    old: str,
    new: str,
) -> None:
    manifest_path = committed_copy / checker.MANIFEST_RELATIVE
    text = manifest_path.read_text(encoding="utf-8")
    assert old in text
    manifest_path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

    assert checker.validate_committed_source_tree(committed_copy)


def test_compiler_execution_leaves_no_mutable_module_cache_or_sys_modules_entry() -> None:
    before = set(sys.modules)

    snapshot = checker.validate_committed_source_snapshot(ROOT)

    assert snapshot.errors == ()
    assert not hasattr(checker, "_TASK2_COMPILERS")
    assert not hasattr(checker, "_load_task2_compiler")
    created = set(sys.modules) - before
    assert not any(name.startswith("ultra_v82_task2_compiler_") for name in created)


@pytest.mark.parametrize(
    "shadow_relative",
    (
        "pathlib.py",
        "zipfile.py",
        "threading.py",
        "xml/__init__.py",
    ),
)
def test_isolated_cli_rejects_repo_script_shadowing(
    committed_copy: Path,
    tmp_path: Path,
    shadow_relative: str,
) -> None:
    root_wrapper = committed_copy / "scripts/check_crossframe_ultra_v82_source.py"
    root_wrapper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_v82_source.py", root_wrapper)
    checker_copy = (
        committed_copy
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
    )
    shutil.copy2(CHECKER_PATH, checker_copy)
    marker = tmp_path / f"shadow-{shadow_relative.replace('/', '-')}.txt"
    shadow = root_wrapper.parent / Path(shadow_relative)
    shadow.parent.mkdir(parents=True, exist_ok=True)
    canonical_marker = tmp_path / f"canonical-shadow-{shadow_relative.replace('/', '-')}.txt"
    canonical_shadow = checker_copy.parent / Path(shadow_relative)
    canonical_shadow.parent.mkdir(parents=True, exist_ok=True)
    for target, target_marker in ((shadow, marker), (canonical_shadow, canonical_marker)):
        target.write_text(
            f"open({str(target_marker)!r}, 'w', encoding='utf-8').write('executed')\n"
            "raise RuntimeError('shadow module executed')\n",
            encoding="utf-8",
            newline="\n",
        )

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(root_wrapper),
            "--repo",
            str(committed_copy),
            "--json",
        ],
        cwd=root_wrapper.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert not marker.exists(), result.stderr or result.stdout
    assert not canonical_marker.exists(), result.stderr or result.stdout
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report == {"errors": [], "ok": True}
    assert set(report) == {"errors", "ok"}
    assert not list(committed_copy.rglob("*.pyc"))
    assert not list(committed_copy.rglob("__pycache__"))


@pytest.mark.parametrize(
    "entrypoint",
    (
        ROOT / "scripts/check_crossframe_ultra_v82_source.py",
        CHECKER_PATH,
    ),
    ids=("root-wrapper", "canonical-checker"),
)
def test_unisolated_cli_entrypoints_fail_closed(entrypoint: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(entrypoint), "--repo", str(ROOT), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 2, result.stdout or result.stderr
    assert json.loads(result.stdout) == {
        "errors": [
            "trusted source validation requires direct Python startup flags -I -S -B"
        ],
        "ok": False,
    }


def test_isolated_wrapper_preserves_spaced_argv_and_propagates_child_exit_7(
    tmp_path: Path,
) -> None:
    spaced_repo = tmp_path / "wrapper repository with spaces"
    root_wrapper = spaced_repo / "scripts/check_crossframe_ultra_v82_source.py"
    canonical_checker = (
        spaced_repo
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
    )
    root_wrapper.parent.mkdir(parents=True)
    canonical_checker.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_v82_source.py", root_wrapper)
    canonical_checker.write_text(
        "\n".join(
            (
                "import json",
                "import sys",
                "print(json.dumps({",
                "    'argv': sys.argv[1:],",
                "    'isolated': bool(sys.flags.isolated),",
                "    'no_site': bool(sys.flags.no_site),",
                "    'dont_write_bytecode': bool(sys.flags.dont_write_bytecode),",
                "}, sort_keys=True))",
                "raise SystemExit(7)",
                "",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    repo_argument = tmp_path / "authority repository argument with spaces"
    source_docx = tmp_path / "source document with spaces.docx"
    repo_argument.mkdir()
    source_docx.write_bytes(b"fake source for argv preservation")
    expected_argv = [
        "--repo",
        str(repo_argument),
        "--source-docx",
        str(source_docx),
        "--json",
    ]

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(root_wrapper),
            *expected_argv,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 7, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "argv": expected_argv,
        "dont_write_bytecode": True,
        "isolated": True,
        "no_site": True,
    }


def test_unisolated_wrapper_fails_closed_after_sitecustomize_has_run(
    tmp_path: Path,
) -> None:
    spaced_repo = tmp_path / "bootstrap repository with spaces"
    root_wrapper = spaced_repo / "scripts/check_crossframe_ultra_v82_source.py"
    canonical_checker = (
        spaced_repo
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
    )
    root_wrapper.parent.mkdir(parents=True)
    canonical_checker.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_v82_source.py", root_wrapper)
    child_marker = tmp_path / "canonical checker executed.txt"
    canonical_checker.write_text(
        f"open({str(child_marker)!r}, 'w', encoding='utf-8').write('executed')\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
        newline="\n",
    )
    python_path = tmp_path / "python path with spaces"
    python_path.mkdir()
    marker = tmp_path / "sitecustomize executed.txt"
    (python_path / "sitecustomize.py").write_text(
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('executed')\n",
        encoding="utf-8",
        newline="\n",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(python_path)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, str(root_wrapper), "--repo", str(spaced_repo), "--json"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert marker.read_text(encoding="utf-8") == "executed"
    assert not child_marker.exists()
    assert result.returncode == 2, result.stdout or result.stderr
    assert json.loads(result.stdout)["ok"] is False

    marker.unlink()
    isolated = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(root_wrapper),
            "--repo",
            str(spaced_repo),
            "--json",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert isolated.returncode == 0, isolated.stdout or isolated.stderr
    assert child_marker.read_text(encoding="utf-8") == "executed"
    assert not marker.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics")
def test_windows_reader_rejects_an_intermediate_junction(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "payload.txt").write_bytes(b"outside")
    anchor = tmp_path / "anchor"
    anchor.mkdir()
    junction = anchor / "redirect"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr or result.stdout}")
    with pytest.raises(ValueError, match="reparse|junction|symlink"):
        checker._read_regular_file(junction / "payload.txt", anchor=anchor)


@pytest.mark.skipif(os.name != "nt", reason="Windows handle sharing semantics")
def test_windows_reader_handle_pins_final_path_and_identity(tmp_path: Path) -> None:
    target = tmp_path / "authority.txt"
    target.write_bytes(b"authority")
    replacement = tmp_path / "replacement.txt"
    replacement.write_bytes(b"replacement")
    with checker._open_anchored_regular_file(target, anchor=tmp_path) as opened:
        assert opened.final_path == Path(os.path.abspath(target))
        assert opened.size == len(b"authority")
        assert opened.identity
        with pytest.raises(OSError):
            os.replace(replacement, target)
        assert opened.read_all() == b"authority"
