from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills" / "crossframe-ultra"
RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"


def load_checker():
    path = ULTRA / "scripts" / "check_crossframe_ultra_v82_knowledge.py"
    spec = importlib.util.spec_from_file_location("ultra_knowledge_checker_isolation", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def copy_checker_repo(tmp_path: Path) -> Path:
    copied = tmp_path / "repo"
    copied_ultra = copied / "skills/crossframe-ultra"
    copied_ultra.parent.mkdir(parents=True)
    shutil.copytree(
        ULTRA,
        copied_ultra,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    copied_scripts = copied / "scripts"
    copied_scripts.mkdir()
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_v82_knowledge.py", copied_scripts)
    return copied


def test_canonical_namespace_is_v82_only_and_provisional_is_separate() -> None:
    registry = load_json(
        ULTRA / "references" / "concept-registry" / "v8.2-concept-registry.json"
    )
    canonical_ids = [item["concept_id"] for item in registry["concepts"]]
    assert canonical_ids
    assert registry["canonical_namespace"] == "V82-"
    assert registry["provisional_namespace"] == "ULTRA-PROV-"
    assert all(item.startswith("V82-") for item in canonical_ids)
    assert not any(item.startswith(("V8-", "V80-", "ULTRA-PROV-")) for item in canonical_ids)
    serialized = json.dumps(registry, ensure_ascii=False).casefold()
    assert "crossframe-promax" not in serialized
    assert "crossframe-max" not in serialized


def test_knowledge_checker_imports_no_sibling_runtime() -> None:
    path = ULTRA / "scripts/check_crossframe_ultra_v82_knowledge.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert all("crossframe_promax" not in name.casefold() for name in imported)
    assert all("crossframe_max" not in name.casefold() for name in imported)


def test_source_checker_exec_uses_a_fresh_nonresident_module() -> None:
    checker = load_checker()
    assert checker.validate_knowledge(ROOT) == []
    assert not any(
        name.startswith("ultra_v82_knowledge_source_checker_")
        for name in sys.modules
    )


def test_all_authority_documents_are_bound_to_exact_v82_source() -> None:
    paths = [
        ULTRA / "references/concept-registry/v8.2-concept-registry.json",
        ULTRA / "references/concept-contracts/v8.2-contract-map.json",
        ULTRA / "references/v8.2-route-map.json",
        *sorted((ULTRA / "references/concept-contracts").glob("*-contracts.json")),
    ]
    for path in paths:
        value = load_json(path)
        assert value["framework_version"] == "v8.2"
        assert value["framework_revision"] == "v8.2"
        assert value["raw_sha256"] == RAW_SHA256
        assert value["semantic_sha256"] == SEMANTIC_SHA256


def test_route_map_closes_concepts_and_contracts() -> None:
    routes = load_json(ULTRA / "references" / "v8.2-route-map.json")
    registry = load_json(
        ULTRA / "references" / "concept-registry" / "v8.2-concept-registry.json"
    )
    contract_map = load_json(
        ULTRA / "references" / "concept-contracts" / "v8.2-contract-map.json"
    )
    concepts = {item["concept_id"] for item in registry["concepts"]}
    contracts = {item["contract_id"] for item in contract_map["contracts"]}
    route_concepts = {
        concept_id
        for route in routes["routes"]
        for concept_id in route.get("concept_ids", [])
    }
    route_contracts = {
        contract_id
        for route in routes["routes"]
        for contract_id in route.get("contract_ids", [])
    }
    assert route_concepts == concepts
    assert route_contracts == contracts
    assert all(route["source_anchors"] for route in routes["routes"])


def test_checker_api_and_json_cli_are_version_bound_and_read_only(tmp_path: Path) -> None:
    copied = copy_checker_repo(tmp_path)

    def repo_snapshot() -> dict[str, tuple[int, int, str]]:
        result: dict[str, tuple[int, int, str]] = {}
        for directory, names, files in os.walk(copied):
            names[:] = [
                name
                for name in names
                if name not in {".git", ".pytest_cache"}
            ]
            for name in files:
                path = Path(directory) / name
                relative = path.relative_to(copied).as_posix()
                payload = path.read_bytes()
                result[relative] = (
                    path.stat().st_mtime_ns,
                    len(payload),
                    hashlib.sha256(payload).hexdigest(),
                )
        return result

    before = repo_snapshot()
    script = copied / "scripts" / "check_crossframe_ultra_v82_knowledge.py"
    for extra_args in (("--json",), ()):
        result = subprocess.run(
            [sys.executable, str(script), "--repo", str(copied), *extra_args],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        if extra_args:
            payload = json.loads(result.stdout)
            assert payload["valid"] is True
            assert payload["framework_revision"] == "v8.2"
            assert payload["raw_sha256"] == RAW_SHA256
            assert payload["semantic_sha256"] == SEMANTIC_SHA256
        else:
            assert "knowledge authority: OK" in result.stdout
    after = repo_snapshot()
    assert before == after


def test_schema_snapshot_rejects_bare_sibling_theory_reference(tmp_path: Path) -> None:
    copied = copy_checker_repo(tmp_path)
    schema = copied / "skills/crossframe-ultra/schemas/ultra-route-map.schema.json"
    value = json.loads(schema.read_text(encoding="utf-8"))
    value["description"] = "ProMax theory and CrossFrame Max are authoritative."
    schema.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    script = copied / "scripts/check_crossframe_ultra_v82_knowledge.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repo", str(copied), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert any(
        "sibling theory" in error.casefold() or "frozen authority" in error.casefold()
        for error in payload["errors"]
    )


def test_modified_source_checker_is_rejected_before_execution(tmp_path: Path) -> None:
    copied = copy_checker_repo(tmp_path)
    source_checker = (
        copied
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
    )
    sentinel = copied / "source-checker-executed.txt"
    payload = source_checker.read_text(encoding="utf-8")
    source_checker.write_text(
        "from pathlib import Path\n"
        f"Path({str(sentinel)!r}).write_text('executed', encoding='utf-8')\n"
        + payload,
        encoding="utf-8",
        newline="\n",
    )
    script = copied / "scripts/check_crossframe_ultra_v82_knowledge.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repo", str(copied), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not sentinel.exists()
    response = json.loads(result.stdout)
    assert any("source authority checker hash mismatch" in error for error in response["errors"])


def test_dynamic_source_module_cannot_import_repo_shadowed_stdlib(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = repo / "shadow-import-executed.txt"
    shadow = repo / "statistics.py"
    shadow.write_text(
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('executed')\n"
        "__file__ = __file__\n",
        encoding="utf-8",
        newline="\n",
    )
    previous = sys.modules.pop("statistics", None)
    monkeypatch.syspath_prepend(str(repo))
    try:
        module = checker._module_from_source(
            "ultra_v82_isolation_probe",
            repo / "probe.py",
            b"import statistics\nstdlib_origin = statistics.__file__\n",
            repo=repo,
        )
    finally:
        sys.modules.pop("statistics", None)
        if previous is not None:
            sys.modules["statistics"] = previous
    assert not marker.exists()
    assert Path(module.stdlib_origin).resolve() != shadow.resolve()
    assert not any(repo.rglob("*.pyc"))


def test_dynamic_source_module_is_removed_after_exception(tmp_path: Path) -> None:
    checker = load_checker()
    payload = b"raise RuntimeError('probe')\n"
    prefix = "ultra_v82_exception_probe_"
    with pytest.raises(RuntimeError, match="probe"):
        checker._module_from_source(
            "ultra_v82_exception_probe",
            tmp_path / "probe.py",
            payload,
            repo=tmp_path,
        )
    assert not any(name.startswith(prefix) for name in sys.modules)


def test_root_wrapper_restarts_isolated_from_repo_shadowed_stdlib(
    tmp_path: Path,
) -> None:
    copied = copy_checker_repo(tmp_path)
    marker = copied / "wrapper-shadow-executed.txt"
    shadow = copied / "scripts" / "ctypes.py"
    shadow.write_text(
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('executed')\n",
        encoding="utf-8",
        newline="\n",
    )
    script = copied / "scripts/check_crossframe_ultra_v82_knowledge.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repo", str(copied), "--json"],
        cwd=copied,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["valid"] is True
    assert not marker.exists()
    assert not any(copied.rglob("*.pyc"))


def test_canonical_entrypoint_restarts_isolated_from_its_script_directory(
    tmp_path: Path,
) -> None:
    copied = copy_checker_repo(tmp_path)
    marker = copied / "canonical-shadow-executed.txt"
    shadow = copied / "skills/crossframe-ultra/scripts/ctypes.py"
    shadow.write_text(
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('executed')\n",
        encoding="utf-8",
        newline="\n",
    )
    script = copied / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repo", str(copied), "--json"],
        cwd=copied,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["valid"] is True
    assert not marker.exists()
    assert not any(copied.rglob("*.pyc"))


def test_ultra_byte_bound_paths_are_pinned_to_lf() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    required = {
        "/skills/crossframe-ultra/references/v8.2-full-source/** text eol=lf",
        "/skills/crossframe-ultra/references/source-manifest.json text eol=lf",
        "/skills/crossframe-ultra/references/concept-registry/** text eol=lf",
        "/skills/crossframe-ultra/references/concept-contracts/** text eol=lf",
        "/skills/crossframe-ultra/references/v8.2-route-map.json text eol=lf",
        "/skills/crossframe-ultra/schemas/** text eol=lf",
        "/skills/crossframe-ultra/scripts/ultra_runtime/jsonio.py text eol=lf",
        "/skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py text eol=lf",
        "/scripts/check_crossframe_ultra_v82_knowledge.py text eol=lf",
        "/tests/test_ultra_v82_registry_closure.py text eol=lf",
        "/tests/test_ultra_v82_version_isolation.py text eol=lf",
    }
    assert required <= set(attributes)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction race regression")
def test_windows_reader_rejects_ancestor_junction_swap(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    authority = repo / "authority"
    outside = tmp_path / "outside"
    authority.mkdir(parents=True)
    outside.mkdir()
    target = authority / "record.json"
    target.write_text('{"trusted": true}\n', encoding="utf-8")
    (outside / target.name).write_text('{"trusted": false}\n', encoding="utf-8")
    original_assert = checker._assert_safe_path
    swapped = False

    def swap_after_check(path: Path, root: Path) -> None:
        nonlocal swapped
        original_assert(path, root)
        if Path(path) == target and not swapped:
            swapped = True
            authority.rename(repo / "authority-original")
            result = subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(authority),
                    str(outside),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr

    monkeypatch.setattr(checker, "_assert_safe_path", swap_after_check)
    with pytest.raises(ValueError, match="repository|escape|reparse"):
        checker._read_regular(target, repo)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction source-checker regression")
def test_windows_junction_redirected_source_checker_never_executes_or_writes_pyc(
    tmp_path: Path,
) -> None:
    copied = copy_checker_repo(tmp_path)
    live = copied / "skills/crossframe-ultra/scripts"
    attacker = copied / "skills/crossframe-ultra/attacker-source-checker"
    shutil.copytree(live, attacker, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    marker = copied / "malicious-source-checker-executed.txt"
    malicious = attacker / "check_crossframe_ultra_v82_source.py"
    malicious.write_text(
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('executed')\n"
        + malicious.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    backup = copied / "skills/crossframe-ultra/scripts-original"
    live.rename(backup)
    link_result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(live), str(attacker)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert link_result.returncode == 0, link_result.stdout + link_result.stderr
    try:
        script = copied / "scripts/check_crossframe_ultra_v82_knowledge.py"
        result = subprocess.run(
            [sys.executable, str(script), "--repo", str(copied), "--json"],
            cwd=copied,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert not marker.exists()
        assert not any(copied.rglob("*.pyc"))
    finally:
        subprocess.run(
            ["cmd.exe", "/d", "/c", "rmdir", str(live)],
            capture_output=True,
            text=True,
            check=False,
        )
        backup.rename(live)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_windows_reader_rejects_internal_junction_substitution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    substitute = repo / "substitute"
    requested_parent = repo / "authority"
    substitute.mkdir(parents=True)
    (substitute / "record.json").write_text(
        '{"trusted": false}\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(requested_parent),
            str(substitute),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    monkeypatch.setattr(checker, "_assert_safe_path", lambda path, root: None)
    with pytest.raises(ValueError, match="reparse|requested path"):
        checker._read_regular(requested_parent / "record.json", repo)


@pytest.mark.skipif(os.name != "nt", reason="Windows pinned-handle final-path regression")
def test_windows_reader_rechecks_final_path_after_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    authority = repo / "authority"
    authority.mkdir(parents=True)
    target = authority / "record.json"
    target.write_text('{"trusted": true}\n', encoding="utf-8")
    original_final_path = checker._windows_final_path
    calls = 0

    def change_after_read(handle: object) -> str:
        nonlocal calls
        calls += 1
        value = original_final_path(handle)
        if calls >= 6:
            return value + "-changed"
        return value

    monkeypatch.setattr(checker, "_windows_final_path", change_after_read)
    with pytest.raises(ValueError, match="final path changed|ancestor changed"):
        checker._read_regular(target, repo)


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink race regression")
def test_posix_reader_rejects_ancestor_symlink_swap(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    authority = repo / "authority"
    outside = tmp_path / "outside"
    authority.mkdir(parents=True)
    outside.mkdir()
    target = authority / "record.json"
    target.write_text('{"trusted": true}\n', encoding="utf-8")
    (outside / target.name).write_text('{"trusted": false}\n', encoding="utf-8")
    original_assert = checker._assert_safe_path
    swapped = False

    def swap_after_check(path: Path, root: Path) -> None:
        nonlocal swapped
        original_assert(path, root)
        if Path(path) == target and not swapped:
            swapped = True
            authority.rename(repo / "authority-original")
            authority.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(checker, "_assert_safe_path", swap_after_check)
    with pytest.raises((OSError, ValueError)):
        checker._read_regular(target, repo)


@pytest.mark.skipif(os.name == "nt", reason="POSIX pinned-handle regression")
def test_posix_reader_rejects_renamed_pinned_ancestor_even_inside_repo(
    tmp_path: Path,
    monkeypatch,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    authority = repo / "authority"
    authority.mkdir(parents=True)
    target = authority / "record.json"
    target.write_text('{"trusted": true}\n', encoding="utf-8")
    original_open = os.open
    swapped = False

    def swap_after_ancestor_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if dir_fd is None:
            descriptor = original_open(path, flags, mode)
        else:
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == "authority" and dir_fd is not None and not swapped:
            swapped = True
            authority.rename(repo / "authority-original")
            authority.mkdir()
            target.write_text('{"trusted": false}\n', encoding="utf-8")
        return descriptor

    monkeypatch.setattr(os, "open", swap_after_ancestor_open)
    with pytest.raises(ValueError, match="requested path|changed|pinned"):
        checker._read_regular(target, repo)
