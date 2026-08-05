from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("ultra_v82_knowledge_isolation_regression", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_import_isolation_keeps_builtin_sys_module_and_executable() -> None:
    checker = _load_checker()
    isolation = checker._ImportIsolation(ROOT)
    assert isolation._inside_repo("built-in") is False
    assert isolation._module_is_repo_loaded(sys) is False
    assert sys.executable
    assert checker.validate_knowledge(ROOT) == []
    assert sys.executable


def test_regular_reader_uses_current_budget_constant(monkeypatch) -> None:
    checker = _load_checker()
    target = ROOT / "skills/crossframe-ultra/references/concept-contracts/world-volume-contracts.json"
    original = checker.MAX_KNOWLEDGE_FILE_BYTES
    monkeypatch.setattr(checker, "MAX_KNOWLEDGE_FILE_BYTES", 1)
    try:
        try:
            checker._read_regular(target, ROOT)
        except ValueError as error:
            assert "safety limit" in str(error) or "budget" in str(error)
        else:
            raise AssertionError("runtime budget override was ignored")
    finally:
        monkeypatch.setattr(checker, "MAX_KNOWLEDGE_FILE_BYTES", original)


def test_extra_contract_file_is_rejected(tmp_path: Path) -> None:
    import shutil

    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    extra = copied / "skills/crossframe-ultra/references/concept-contracts/extra.json"
    extra.write_text("{}\n", encoding="utf-8", newline="\n")
    checker = _load_checker()
    assert any("contract" in error.lower() and "extra" in error.lower() for error in checker.validate_knowledge(copied))
