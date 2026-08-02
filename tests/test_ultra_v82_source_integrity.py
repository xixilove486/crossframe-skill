from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
)


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
    assert callable(checker.validate_committed_source_tree)
    assert callable(checker.validate_against_docx)
    assert callable(checker.main)


def test_committed_authority_tree_is_self_consistent() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    errors = checker.validate_committed_source_tree(ROOT)
    assert errors == [], errors


def test_source_aware_validation_accepts_the_exact_v82_docx() -> None:
    assert checker is not None, "Task3 checker is not implemented"
    source_docx = Path(r"E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx")
    assert source_docx.is_file()
    errors = checker.validate_against_docx(ROOT, source_docx)
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
