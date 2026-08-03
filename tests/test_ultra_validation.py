from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ULTRA_SCRIPTS = REPO_ROOT / "skills/crossframe-ultra/scripts"
FIXTURES = REPO_ROOT / "tests/fixtures/ultra-runtime"
RUN_ID = "20260804T000000Z-0123456789ab"
STAMP = "2026-08-04T00:00:00Z"
PHASE_HEAD = "a" * 64
UNIT_KINDS = (
    "claim",
    "evidence",
    "unknown",
    "circle-relation",
    "scale-transform",
    "translation-loss",
    "mechanism",
    "branch",
    "residual",
    "forecast",
    "verdict",
    "action",
    "reversal-condition",
)


def load_validation_runtime() -> SimpleNamespace:
    scripts = str(ULTRA_SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    for name in ("artifacts", "validation"):
        assert importlib.util.find_spec(f"ultra_runtime.{name}") is not None, (
            f"missing Task 12 fresh-validation module: ultra_runtime.{name}"
        )
    return SimpleNamespace(
        artifacts=importlib.import_module("ultra_runtime.artifacts"),
        validation=importlib.import_module("ultra_runtime.validation"),
        constants=importlib.import_module("ultra_runtime.constants"),
        jsonio=importlib.import_module("ultra_runtime.jsonio"),
        paths=importlib.import_module("ultra_runtime.paths"),
        schemas=importlib.import_module("ultra_runtime.schemas"),
    )


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_tree(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def seal_fixture(modules: SimpleNamespace, name: str) -> dict[str, object]:
    value = load_json(FIXTURES / name)
    value["run_id"] = RUN_ID
    value["version_binding"] = modules.constants.current_version_binding()
    value["generated_at"] = STAMP
    value["content_sha256"] = modules.schemas.compute_artifact_content_sha256(value)
    return value


def _coverage(modules: SimpleNamespace, article_bytes: bytes) -> dict[str, object]:
    excerpts = [f"ULTRA-COVERAGE-{index:02d} establishes {kind}." for index, kind in enumerate(UNIT_KINDS, 1)]
    value: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.semantic-coverage",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": modules.constants.current_version_binding(),
        "generated_at": STAMP,
        "content_sha256": "0" * 64,
        "phase_id": "U11",
        "output_plan_artifact_sha256": "b" * 64,
        "semantic_universe_sha256": "c" * 64,
        "article_sha256": hashlib.sha256(article_bytes).hexdigest(),
        "required_unit_kinds": list(UNIT_KINDS),
        "mappings": [
            {
                "unit_id": f"UNIT-{index:02d}",
                "unit_kind": kind,
                "section_id": f"SECTION-{index:02d}",
                "normalized_excerpt": excerpt,
                "source_refs": [f"SOURCE-{index:02d}"],
            }
            for index, (kind, excerpt) in enumerate(zip(UNIT_KINDS, excerpts), 1)
        ],
        "missing_unit_ids": [],
        "coverage_percent": 100,
        "coverage_complete": True,
    }
    value["content_sha256"] = modules.schemas.compute_artifact_content_sha256(value)
    return value


def _article_bytes() -> bytes:
    lines = ["# CrossFrame Ultra partial article", ""]
    lines.extend(
        f"ULTRA-COVERAGE-{index:02d} establishes {kind}."
        for index, kind in enumerate(UNIT_KINDS, 1)
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _read_events(modules: SimpleNamespace) -> bytes:
    source_path = REPO_ROOT / "skills/crossframe-ultra/references/source-manifest.json"
    source = load_json(source_path)
    source_manifest_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    binding = modules.constants.current_version_binding()
    rows: list[bytes] = []
    for unit in source["source_units"]:
        event: dict[str, object] = {
            "schema_id": "crossframe.ultra.v82.read-event",
            "schema_version": 1,
            "run_id": RUN_ID,
            "version_binding": binding,
            "generated_at": STAMP,
            "content_sha256": unit["sha256"],
            "phase_id": "U1",
            "source_unit_id": unit["unit_id"],
            "source_kind": unit["kind"],
            "source_ordinal": unit["ordinal"],
            "source_manifest_sha256": source_manifest_sha256,
            "promoted_semantic_snapshot_sha256": binding["framework_semantic_sha256"],
            "source_lock_sha256": "d" * 64,
            "parent_event_sha256": "e" * 64,
            "receipt_sha256": hashlib.sha256(
                f"{RUN_ID}:{unit['unit_id']}:receipt".encode("utf-8")
            ).hexdigest(),
            "reader_mode": "full-source",
            "execution_identity": {
                "kind": "host-process",
                "process_id": 1,
                "executable": "python",
                "user": "fixture-user",
            },
            "read_at": STAMP,
        }
        event["read_event_sha256"] = canonical_sha256(event)
        rows.append(canonical_bytes(event))
    return b"".join(rows)


@dataclass
class BuiltRun:
    modules: SimpleNamespace
    layout: object
    repo: Path
    manifest_path: Path
    validator_set_sha256: str
    policy: object

    @property
    def run_dir(self) -> Path:
        return self.layout.run_dir

    def path(self, relative: str) -> Path:
        return self.run_dir / Path(relative)


def refresh_manifest(run: BuiltRun) -> dict[str, object]:
    manifest = run.modules.artifacts.build_artifact_manifest(
        run.layout,
        phase_chain_head_sha256=PHASE_HEAD,
        validator_set_sha256=run.validator_set_sha256,
        generated_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
    )
    write_json(run.manifest_path, manifest)
    return manifest


def build_valid_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> BuiltRun:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=(tmp_path / "prod").resolve(),
        test_root=(tmp_path / "test").resolve(),
    )
    layout = modules.paths.build_run_layout(modules.paths.RunMode.TEST, RUN_ID, policy)
    layout.run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(modules.validation, "default_root_policy", lambda: policy)

    files = {
        "artifacts/U00-U03-evidence/ultra-read-events.jsonl": _read_events(modules),
        "artifacts/U00-U03-evidence/ultra-evidence-ledger.json": canonical_bytes(
            seal_fixture(modules, "evidence-ledger-valid.json")
        ),
        "artifacts/U04-U05-world-volume/ultra-world-volume.json": canonical_bytes(
            seal_fixture(modules, "world-volume-valid.json")
        ),
        "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json": canonical_bytes(
            seal_fixture(modules, "claim-mechanism-graph-valid.json")
        ),
        "artifacts/U06-U08-inference/recursive-state-NODE-MAIN-ORDER-1.json": canonical_bytes(
            seal_fixture(modules, "recursive-state-valid.json")
        ),
        "artifacts/U06-U08-inference/ultra-recursive-lineage.json": canonical_bytes(
            seal_fixture(modules, "recursive-lineage-valid.json")
        ),
    }
    article = _article_bytes()
    files["work/authoring/article.partial.md"] = article
    files["artifacts/U09-U10-verdict/U11-semantic-coverage.json"] = canonical_bytes(
        _coverage(modules, article)
    )
    for relative, raw in files.items():
        path = layout.run_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    validator_hash = modules.validation.validator_set_sha256(REPO_ROOT)
    run = BuiltRun(
        modules=modules,
        layout=layout,
        repo=REPO_ROOT,
        manifest_path=layout.artifacts_dir / "ultra-artifact-manifest.json",
        validator_set_sha256=validator_hash,
        policy=policy,
    )
    refresh_manifest(run)
    return run


def parse_report(raw: bytes) -> dict[str, object]:
    value = json.loads(raw.decode("utf-8"))
    assert isinstance(value, dict)
    return value


def report_error_codes(report: dict[str, object]) -> set[str]:
    return {
        code
        for check in report["checks"]
        for code in check["error_codes"]
    }


def test_disk_fresh_validation_is_canonical_read_only_and_schema_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    before = file_tree(run.run_dir)

    report_bytes = run.modules.validation.validate_run_from_disk(
        REPO_ROOT, run.modules.paths.RunMode.TEST, RUN_ID
    )
    report = parse_report(report_bytes)

    assert report_bytes == canonical_bytes(report)
    assert report["overall_status"] == "pass"
    assert report["fresh_context"] is True
    assert report["manifest_sha256"] == hashlib.sha256(
        run.manifest_path.read_bytes()
    ).hexdigest()
    run.modules.schemas.validate_phase_artifact(
        "ultra-validator-report.schema.json",
        report,
        expected_schema_id="crossframe.ultra.v82.validator-report",
        expected_run_id=RUN_ID,
        expected_version_binding=run.modules.constants.current_version_binding(),
        expected_phase_id="U12",
    )
    assert file_tree(run.run_dir) == before
    assert not (run.run_dir / ".writer-lease.json").exists()
    assert not run.layout.validation_current_dir.exists()
    assert not run.layout.validation_attempts_dir.exists()


def test_parent_commits_exact_child_bytes_and_rejects_edited_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    report_bytes = run.modules.validation.validate_run_from_disk(
        REPO_ROOT, run.modules.paths.RunMode.TEST, RUN_ID
    )
    report = parse_report(report_bytes)
    manifest_sha = str(report["manifest_sha256"])

    committed = run.modules.validation.commit_validation_attempt(
        run.layout,
        attempt_id=str(report["attempt_id"]),
        report_bytes=report_bytes,
        expected_manifest_sha256=manifest_sha,
        expected_validator_set_sha256=run.validator_set_sha256,
    )
    attempt_path = (
        run.layout.validation_attempts_dir
        / str(report["attempt_id"])
        / "ultra-validator-report.json"
    )
    current_path = run.layout.validation_current_dir / "ultra-validator-report.json"
    assert committed == report
    assert attempt_path.read_bytes() == report_bytes
    assert current_path.read_bytes() == report_bytes

    edited = copy.deepcopy(report)
    edited["overall_status"] = "fail"
    edited["content_sha256"] = run.modules.schemas.compute_artifact_content_sha256(edited)
    with pytest.raises(ValueError, match="fresh|report|bytes|status"):
        run.modules.validation.commit_validation_attempt(
            run.layout,
            attempt_id=str(report["attempt_id"]),
            report_bytes=canonical_bytes(edited),
            expected_manifest_sha256=manifest_sha,
            expected_validator_set_sha256=run.validator_set_sha256,
        )


def test_parent_rejects_stale_report_after_manifest_generation_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    stale_bytes = run.modules.validation.validate_run_from_disk(
        REPO_ROOT, run.modules.paths.RunMode.TEST, RUN_ID
    )
    stale = parse_report(stale_bytes)
    article = run.path("work/authoring/article.partial.md")
    article.write_bytes(article.read_bytes() + b"changed after validation\n")
    refresh_manifest(run)

    with pytest.raises(ValueError, match="stale|manifest|fresh"):
        run.modules.validation.commit_validation_attempt(
            run.layout,
            attempt_id=str(stale["attempt_id"]),
            report_bytes=stale_bytes,
            expected_manifest_sha256=str(stale["manifest_sha256"]),
            expected_validator_set_sha256=run.validator_set_sha256,
        )


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    (("cross-run", "ULTRA-CROSS-RUN-MANIFEST"), ("out-of-root", "ULTRA-PATH-ESCAPE")),
)
def test_manifest_tamper_is_reported_without_following_unsafe_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    error_code: str,
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    manifest = load_json(run.manifest_path)
    outside = run.run_dir.parent / "outside-sentinel.json"
    outside.write_text("sentinel", encoding="utf-8")
    if mutation == "cross-run":
        manifest["run_id"] = "20260804T000000Z-ffffffffffff"
    else:
        manifest["artifacts"][0]["path"] = "../outside-sentinel.json"
    manifest["content_sha256"] = run.modules.schemas.compute_artifact_content_sha256(manifest)
    write_json(run.manifest_path, manifest)

    report = parse_report(
        run.modules.validation.validate_run_from_disk(
            REPO_ROOT, run.modules.paths.RunMode.TEST, RUN_ID
        )
    )
    assert report["overall_status"] == "fail"
    assert error_code in report_error_codes(report)
    assert outside.read_text(encoding="utf-8") == "sentinel"


def _load_checker(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_child_checker_writes_only_report_bytes_to_stdout(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    modules = load_validation_runtime()
    checker_path = REPO_ROOT / "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py"
    assert checker_path.is_file(), "missing Task 12 child checker"
    checker = _load_checker(checker_path, "_ultra_child_checker_test")
    expected = canonical_bytes({"overall_status": "pass", "report": "canonical"})
    monkeypatch.setattr(checker, "validate_run_from_disk", lambda *args: expected)

    assert checker.main(
        ["--repo", str(REPO_ROOT), "--mode", "test", "--run-id", RUN_ID, "--json"]
    ) == 0
    assert capsysbinary.readouterr() == (expected, b"")
    assert modules is not None


def test_root_wrapper_is_a_transparent_forwarder() -> None:
    child = REPO_ROOT / "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py"
    root = REPO_ROOT / "scripts/check_crossframe_ultra_artifacts.py"
    assert child.is_file(), "missing Task 12 child checker"
    assert root.is_file(), "missing Task 12 root checker wrapper"
    child_help = subprocess.run(
        [sys.executable, "-B", str(child), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    root_help = subprocess.run(
        [sys.executable, "-B", str(root), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    assert root_help.returncode == child_help.returncode == 0
    assert root_help.stdout == child_help.stdout
    assert root_help.stderr == child_help.stderr == b""
