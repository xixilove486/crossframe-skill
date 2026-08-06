from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills/crossframe-ultra"
SKILL_SCRIPTS = ULTRA / "scripts"
BUILDER_PATH = SKILL_SCRIPTS / "build_crossframe_ultra_release_manifest.py"
ROOT_BUILDER_PATH = ROOT / "scripts/build_crossframe_ultra_release_manifest.py"
MANIFEST_PATH = ULTRA / "references/release-manifest.json"
STAMP = "2026-08-02T00:00:00Z"


def _load_builder():
    assert BUILDER_PATH.is_file(), f"canonical builder is missing: {BUILDER_PATH}"
    if str(SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SKILL_SCRIPTS))
    name = "_task14_crossframe_ultra_release_builder"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _declared_hashes(document: dict[str, object]) -> dict[str, str]:
    artifacts = document["release_artifacts"]
    assert isinstance(artifacts, list)
    return {str(item["path"]): str(item["sha256"]) for item in artifacts}


def _copy_task_surface(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(ULTRA, repo / "skills/crossframe-ultra")
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT_BUILDER_PATH, repo / "scripts/build_crossframe_ultra_release_manifest.py")
    return repo


def test_builder_reuses_the_existing_hash_binding_schema_and_atomic_write_authorities() -> None:
    builder = _load_builder()
    from ultra_runtime import constants, jsonio, schemas, source_integrity

    assert builder.canonical_skill_tree_hashes is source_integrity.canonical_skill_tree_hashes
    assert builder.compute_artifact_content_sha256 is schemas.compute_artifact_content_sha256
    assert builder.current_version_binding is constants.current_version_binding
    assert builder.validate_instance is schemas.validate_instance
    assert builder.atomic_write_json is jsonio.atomic_write_json


def test_manifest_is_deterministic_schema_valid_and_exactly_covers_the_canonical_tree() -> None:
    builder = _load_builder()
    from ultra_runtime.constants import current_version_binding
    from ultra_runtime.schemas import compute_artifact_content_sha256, validate_instance
    from ultra_runtime.source_integrity import canonical_skill_tree_hashes

    first = builder.build_release_manifest(ROOT)
    second = builder.build_release_manifest(ROOT)
    assert first == second
    assert first["release_id"] == "ultra-v8.2-r1-runtime-1.1.0"
    binding = first["version_binding"]
    assert binding == current_version_binding()
    assert binding["runtime_version"] == "1.1.0"
    assert binding["artifact_schema_version"] == 2
    assert binding["compiler_version"] == "1.0.0"
    assert binding["validator_version"] == "1.1.0"
    assert binding["article_contract_version"] == "1.1.0"
    assert first["generated_at"] == STAMP
    assert first["built_at"] == STAMP
    assert first["validated_at"] == STAMP
    assert first["release_state"] == "stable"
    assert first["framework_source"]["path"] == "references/source-manifest.json"
    assert first["content_sha256"] == compute_artifact_content_sha256(first)
    validate_instance("ultra-release-manifest.schema.json", first)

    expected = canonical_skill_tree_hashes(ULTRA)
    assert _declared_hashes(first) == expected
    assert list(_declared_hashes(first)) == sorted(expected)
    assert "references/release-manifest.json" not in expected
    assert all(item["media_type"] == "application/octet-stream" for item in first["release_artifacts"])


def test_builder_write_is_atomic_repeatable_and_root_wrapper_detects_staleness(
    tmp_path: Path,
) -> None:
    _load_builder()
    repo = _copy_task_surface(tmp_path)
    canonical = repo / "skills/crossframe-ultra/scripts/build_crossframe_ultra_release_manifest.py"
    root_wrapper = repo / "scripts/build_crossframe_ultra_release_manifest.py"
    manifest = repo / "skills/crossframe-ultra/references/release-manifest.json"

    write = subprocess.run(
        [sys.executable, "-B", str(canonical), "--repo", str(repo), "--write"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert write.returncode == 0, write.stderr
    first_bytes = manifest.read_bytes()
    parsed = json.loads(first_bytes.decode("utf-8"))
    assert parsed["content_sha256"]

    rewrite = subprocess.run(
        [sys.executable, "-B", str(canonical), "--repo", str(repo), "--write"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert rewrite.returncode == 0, rewrite.stderr
    assert manifest.read_bytes() == first_bytes

    check = subprocess.run(
        [sys.executable, "-B", str(root_wrapper), "--repo", str(repo), "--check"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert check.returncode == 0, check.stderr

    skill = repo / "skills/crossframe-ultra/SKILL.md"
    skill.write_bytes(skill.read_bytes() + b"\n")
    stale = subprocess.run(
        [sys.executable, "-B", str(root_wrapper), "--repo", str(repo), "--check"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert stale.returncode == 1
    assert "stale" in (stale.stdout + stale.stderr).casefold()


def test_fixed_exclusions_do_not_change_the_manifest_and_links_fail_closed(
    tmp_path: Path,
) -> None:
    builder = _load_builder()
    repo = _copy_task_surface(tmp_path)
    skill = repo / "skills/crossframe-ultra"
    baseline = builder.build_release_manifest(repo)

    (skill / "references/.v8-full-source.lock").write_text("ignored", encoding="utf-8")
    (skill / "scripts/__pycache__").mkdir(exist_ok=True)
    (skill / "scripts/__pycache__/ignored.pyc").write_bytes(b"ignored")
    (skill / ".pytest_cache").mkdir(exist_ok=True)
    (skill / ".pytest_cache/ignored").write_bytes(b"ignored")
    assert builder.build_release_manifest(repo) == baseline

    target = tmp_path / "outside.py"
    target.write_text("pass\n", encoding="utf-8")
    link = skill / "scripts/linked.py"
    try:
        os.symlink(target, link)
    except (NotImplementedError, OSError):
        pytest.skip("host does not permit creation of a test symlink")
    with pytest.raises(Exception, match="symlink|reparse|unsafe"):
        builder.build_release_manifest(repo)


def test_committed_release_manifest_matches_a_fresh_build() -> None:
    builder = _load_builder()
    assert MANIFEST_PATH.is_file(), f"release manifest is missing: {MANIFEST_PATH}"
    committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert committed == builder.build_release_manifest(ROOT)
