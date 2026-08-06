from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from types import SimpleNamespace

from tests.pytest_import_guard import pytest
from tests.ultra_capability_support import (
    capability_attestation_for_contract,
    default_capability_requirements,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ULTRA_SCRIPTS = REPO_ROOT / "skills/crossframe-ultra/scripts"
FIXTURES = REPO_ROOT / "tests/fixtures/ultra-runtime"
RUN_ENTROPY = b"ultra-validation-authority-template"
RUN_ID = f"20260804T000000Z-{hashlib.sha256(RUN_ENTROPY).hexdigest()[:12]}"
STAMP = "2026-08-04T00:00:00Z"
RUN_CONTRACT_PATH = "artifacts/ultra-run-contract.json"
HOST_CAPABILITY_ATTESTATION_PATH = (
    "artifacts/U00-U03-evidence/U00-host-capability-attestation.json"
)
HOST_CAPABILITY_ATTESTATION_SCHEMA_ID = (
    "crossframe.ultra.v82.host-capability-attestation"
)
EVIDENCE_LINEAGE_PATH = (
    "artifacts/U00-U03-evidence/U00-evidence-lineage.json"
)
EVIDENCE_LINEAGE_SCHEMA_ID = "crossframe.ultra.v82.evidence-lineage"
EXTRA_U0_PATH = "artifacts/U00-U03-evidence/unexpected-u0-artifact.json"
CAPABILITY_ATTESTATION_SHA256 = "c" * 64
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
        locks=importlib.import_module("ultra_runtime.locks"),
        paths=importlib.import_module("ultra_runtime.paths"),
        recovery=importlib.import_module("ultra_runtime.recovery"),
        schemas=importlib.import_module("ultra_runtime.schemas"),
        source_integrity=importlib.import_module("ultra_runtime.source_integrity"),
        state_machine=importlib.import_module("ultra_runtime.state_machine"),
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


def test_validation_selects_only_active_repair_generation_phase_authority() -> None:
    runtime = load_validation_runtime()
    phases = tuple(f"U{number}" for number in range(12))
    original_events = [
        {
            "phase_id": phase_id,
            "status": "complete",
            "event_sha256": f"old-{phase_id}",
        }
        for phase_id in phases
    ]
    invalidation = {
        "phase_id": "U10",
        "status": "invalidated",
        "reset_from_phase": "U10",
        "generation": 1,
        "event_sha256": "repair-invalidation",
    }
    replacements = [
        {
            "phase_id": phase_id,
            "status": "complete",
            "generation": 1,
            "event_sha256": f"new-{phase_id}",
        }
        for phase_id in ("U10", "U11")
    ]
    checkpoints = [
        {
            "phase_id": event["phase_id"],
            "boundary_kind": "phase",
            "phase_event_sha256": event["event_sha256"],
        }
        for event in (*original_events, *replacements)
    ]

    active_events, active_checkpoints = (
        runtime.validation._active_phase_checkpoints(
            runtime.recovery,
            (*original_events, invalidation, *replacements),
            checkpoints,
        )
    )

    assert [event["event_sha256"] for event in active_events] == [
        *(f"old-U{number}" for number in range(10)),
        "new-U10",
        "new-U11",
    ]
    assert [checkpoint["phase_event_sha256"] for checkpoint in active_checkpoints] == [
        *(f"old-U{number}" for number in range(10)),
        "new-U10",
        "new-U11",
    ]


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


_AUTHORITATIVE_TEMPLATE: Path | None = None


def _phase_events(run_dir: Path) -> list[dict[str, object]]:
    path = run_dir / "recovery/phase-events.jsonl"
    events = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
    assert all(isinstance(event, dict) for event in events)
    return events


def _phase_chain_head(run_dir: Path, phase_id: str = "U11") -> str:
    matches = [
        event
        for event in _phase_events(run_dir)
        if event.get("phase_id") == phase_id and event.get("status") == "complete"
    ]
    assert len(matches) == 1
    digest = matches[0].get("event_sha256")
    assert isinstance(digest, str)
    return digest


def _persist_u1_read_plan(modules: SimpleNamespace, layout: object) -> None:
    authority = load_json(layout.recovery_dir / "run-authority.json")
    source_lock_path = layout.recovery_dir / "u1-authority/source-lock.json"
    source_lock_sha256 = hashlib.sha256(source_lock_path.read_bytes()).hexdigest()
    u0_event = next(
        event for event in _phase_events(layout.run_dir) if event["phase_id"] == "U0"
    )
    source_manifest = modules.source_integrity.load_source_manifest(
        REPO_ROOT / "skills/crossframe-ultra/references/source-manifest.json",
        expected_sha256=str(authority["source_sha256"]),
    )
    read_plan = modules.source_integrity.build_read_plan(
        source_manifest,
        promoted_semantic_snapshot_sha256=source_manifest.semantic_sha256,
        source_manifest_sha256=source_manifest.sha256,
        source_lock_sha256=source_lock_sha256,
        parent_event_sha256=str(u0_event["event_sha256"]),
    )
    write_json(layout.recovery_dir / "u1-authority/read-plan.json", read_plan)


def _strip_template_to_u11(modules: SimpleNamespace, layout: object) -> None:
    events_path = layout.recovery_dir / "phase-events.jsonl"
    events = [event for event in _phase_events(layout.run_dir) if event["phase_id"] != "U12"]
    events_path.write_bytes(b"".join(canonical_bytes(event) for event in events))
    for path in (layout.recovery_dir / "checkpoints").glob("*.json"):
        if load_json(path).get("phase_id") == "U12":
            path.unlink()
    shutil.rmtree(layout.delivery_dir, ignore_errors=True)
    shutil.rmtree(layout.validation_dir, ignore_errors=True)
    (layout.recovery_dir / "publish-transaction.json").unlink(missing_ok=True)
    (layout.artifacts_dir / "ultra-artifact-manifest.json").unlink(missing_ok=True)


def _authoritative_template(tmp_path: Path) -> Path:
    global _AUTHORITATIVE_TEMPLATE
    if _AUTHORITATIVE_TEMPLATE is not None:
        return _AUTHORITATIVE_TEMPLATE
    from tests.run_ultra_fixed_root_smoke import run_fixed_root_smoke

    modules = load_validation_runtime()
    template_root = (tmp_path.parent / "ultra-validation-authority-template").resolve()
    policy = modules.paths.RootPolicy(
        production_root=template_root / "prod",
        test_root=template_root / "test",
    )
    release = load_json(
        REPO_ROOT / "skills/crossframe-ultra/references/release-manifest.json"
    )
    declared_tree = {
        str(item["path"]): str(item["sha256"])
        for item in release["release_artifacts"]
    }
    original_tree_hashes = modules.source_integrity.canonical_skill_tree_hashes
    modules.source_integrity.canonical_skill_tree_hashes = lambda _root: dict(
        declared_tree
    )
    original_validate_run_from_disk = modules.validation.validate_run_from_disk

    def validate_run_with_read_plan(
        repo: Path, run_mode: object, run_id: str
    ) -> bytes:
        layout = modules.paths.build_run_layout(run_mode, run_id, policy)
        read_plan_path = layout.recovery_dir / "u1-authority/read-plan.json"
        if not read_plan_path.is_file():
            _persist_u1_read_plan(modules, layout)
        return original_validate_run_from_disk(repo, run_mode, run_id)

    modules.validation.validate_run_from_disk = validate_run_with_read_plan
    try:
        result = run_fixed_root_smoke(
            root_policy=policy,
            started_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
            run_entropy=RUN_ENTROPY,
            transaction_entropy=b"ultra-validation-authority-transaction",
        )
    finally:
        modules.validation.validate_run_from_disk = original_validate_run_from_disk
        modules.source_integrity.canonical_skill_tree_hashes = original_tree_hashes
    assert result["run_id"] == RUN_ID
    layout = modules.paths.build_run_layout(modules.paths.RunMode.TEST, RUN_ID, policy)
    _strip_template_to_u11(modules, layout)
    _persist_u1_read_plan(modules, layout)
    validator_hash = modules.validation.validator_set_sha256(REPO_ROOT)
    manifest = modules.artifacts.build_artifact_manifest(
        layout,
        phase_chain_head_sha256=_phase_chain_head(layout.run_dir),
        validator_set_sha256=validator_hash,
        generated_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
    )
    write_json(layout.artifacts_dir / "ultra-artifact-manifest.json", manifest)
    _AUTHORITATIVE_TEMPLATE = layout.run_dir
    return layout.run_dir


def refresh_manifest(run: BuiltRun) -> dict[str, object]:
    manifest = run.modules.artifacts.build_artifact_manifest(
        run.layout,
        phase_chain_head_sha256=_phase_chain_head(run.run_dir),
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
    layout.run_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_authoritative_template(tmp_path), layout.run_dir)
    monkeypatch.setattr(modules.validation, "default_root_policy", lambda: policy)

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


@contextmanager
def _owned_validation_lease(run: BuiltRun):
    lease = run.modules.locks.acquire_run_lease(
        run.layout,
        datetime(2026, 8, 4, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    try:
        yield lease
    finally:
        run.modules.locks.release_run_lease(run.layout, lease)


def persisted_u1_authority_args(run: BuiltRun) -> dict[str, object]:
    disk_authority = run.modules.validation._load_verified_disk_authority(
        run.layout,
        load_json(run.manifest_path),
    )
    run_authority = disk_authority["run_authority"]
    events = disk_authority["events"]
    refs_by_phase = disk_authority["refs_by_phase"]
    assert isinstance(run_authority, dict)
    assert isinstance(events, tuple)
    assert isinstance(refs_by_phase, dict)
    u0_event = next(event for event in events if event["phase_id"] == "U0")
    u1_refs = refs_by_phase["U1"]
    assert isinstance(u1_refs, dict)
    source_manifest = run.modules.source_integrity.load_source_manifest(
        REPO_ROOT / "skills/crossframe-ultra/references/source-manifest.json",
        expected_sha256=str(run_authority["source_sha256"]),
    )
    expected_inputs: list[dict[str, str]] = []
    for item in run_authority["input_refs"]:
        assert isinstance(item, dict)
        relative = PurePosixPath(str(item["path"]))
        assert relative.parts[0] == "input"
        expected_inputs.append(
            {
                "path": PurePosixPath(*relative.parts[1:]).as_posix(),
                "sha256": str(item["sha256"]),
                "media_type": str(item["media_type"]),
            }
        )
    read_events = [
        json.loads(row)
        for row in run.path(
            "artifacts/U00-U03-evidence/ultra-read-events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert all(isinstance(event, dict) for event in read_events)
    return {
        "repo": REPO_ROOT,
        "run_layout": run.layout,
        "manifest": source_manifest,
        "source_lock": load_json(
            run.path("recovery/u1-authority/source-lock.json")
        ),
        "read_plan": load_json(run.path("recovery/u1-authority/read-plan.json")),
        "coverage": load_json(
            run.path("recovery/u1-authority/source-coverage.json")
        ),
        "read_events": read_events,
        "expected_run_id": RUN_ID,
        "expected_run_mode": "test",
        "expected_version_binding": run.modules.constants.current_version_binding(),
        "expected_parent_event_sha256": str(u0_event["event_sha256"]),
        "expected_evidence_cutoff": str(run_authority["evidence_cutoff"]),
        "expected_inputs": expected_inputs,
        "expected_request_sha256": str(
            load_json(run.path("artifacts/ultra-run-contract.json"))["request_sha256"]
        ),
        "expected_source_lock_sha256": str(
            u1_refs["recovery/u1-authority/source-lock.json"]
        ),
        "expected_read_plan_sha256": str(
            u1_refs["recovery/u1-authority/read-plan.json"]
        ),
        "expected_read_coverage_sha256": str(
            u1_refs["recovery/u1-authority/source-coverage.json"]
        ),
    }


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


def stubbed_disk_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    checkpoint_u0_paths: tuple[str, ...] = (RUN_CONTRACT_PATH,),
    manifest_u0_paths: tuple[str, ...] = (
        RUN_CONTRACT_PATH,
        HOST_CAPABILITY_ATTESTATION_PATH,
    ),
    contract_capability_sha256: str = CAPABILITY_ATTESTATION_SHA256,
    manifest_capability_sha256: str = CAPABILITY_ATTESTATION_SHA256,
) -> tuple[SimpleNamespace, object, dict[str, object]]:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=(tmp_path / "prod").resolve(),
        test_root=(tmp_path / "test").resolve(),
    )
    layout = modules.paths.build_run_layout(modules.paths.RunMode.TEST, RUN_ID, policy)
    request_bytes = b"evidence-child request\n"
    new_evidence_bytes = b"new evidence candidate\n"
    request_path = layout.input_dir / "request.bin"
    new_evidence_path = layout.input_dir / "new-evidence.bin"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_bytes(request_bytes)
    new_evidence_path.write_bytes(new_evidence_bytes)
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    new_evidence_sha256 = hashlib.sha256(new_evidence_bytes).hexdigest()
    run_contract = {
        "capability_attestation_sha256": contract_capability_sha256,
        "request_sha256": request_sha256,
        "evidence_cutoff": STAMP,
    }
    write_json(layout.run_dir / RUN_CONTRACT_PATH, run_contract)
    run_contract_sha256 = hashlib.sha256(
        (layout.run_dir / RUN_CONTRACT_PATH).read_bytes()
    ).hexdigest()

    def authority_sha256(path: str) -> str:
        if path == RUN_CONTRACT_PATH:
            return run_contract_sha256
        if path == HOST_CAPABILITY_ATTESTATION_PATH:
            return manifest_capability_sha256
        return "d" * 64

    refs_by_phase: dict[str, dict[str, str]] = {
        "U0": {
            path: authority_sha256(path)
            for path in checkpoint_u0_paths
        },
        "U1": {
            "recovery/u1-authority/source-lock.json": "1" * 64,
            "recovery/u1-authority/read-plan.json": "2" * 64,
            "recovery/u1-authority/source-coverage.json": "3" * 64,
        },
    }
    for number in range(2, 12):
        phase_id = f"U{number}"
        refs_by_phase[phase_id] = {
            f"artifacts/{phase_id}-authority.json": f"{number + 4:064x}",
        }

    events = tuple(
        {
            "run_id": RUN_ID,
            "phase_id": f"U{number}",
            "status": "complete",
            "event_sha256": f"{number + 32:064x}",
            "evidence_cutoff": STAMP,
            "input_artifact_hashes": [request_sha256, new_evidence_sha256],
            "output_artifact_hashes": (
                [run_contract_sha256] if number == 0 else []
            ),
        }
        for number in range(12)
    )
    checkpoints_dir = layout.recovery_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True)
    for event in events:
        phase_id = str(event["phase_id"])
        checkpoint = {
            "phase_id": phase_id,
            "boundary_kind": "phase",
            "boundary_ordinal": 0,
            "generation": 0,
            "phase_event_sha256": event["event_sha256"],
            "artifact_hashes": [
                {"path": path, "sha256": digest}
                for path, digest in refs_by_phase[phase_id].items()
            ],
        }
        encoded = canonical_bytes(checkpoint)
        (checkpoints_dir / f"{hashlib.sha256(encoded).hexdigest()}.json").write_bytes(
            encoded
        )

    monkeypatch.setattr(modules.recovery, "_validate_layout", lambda _layout: None)
    monkeypatch.setattr(
        modules.recovery,
        "_validate_authority",
        lambda _layout: ({"run_id": RUN_ID}, "resume"),
    )
    monkeypatch.setattr(
        modules.recovery,
        "_read_events",
        lambda *_args, **_kwargs: events,
    )
    monkeypatch.setattr(
        modules.recovery,
        "_validate_checkpoint",
        lambda _layout, checkpoint, **_kwargs: dict(checkpoint),
    )
    monkeypatch.setattr(
        modules.recovery,
        "_validate_evidence_fork_authority",
        lambda _layout, **_kwargs: {},
    )

    manifest_artifacts = [
        {
            "schema_id": (
                "crossframe.ultra.v82.run-contract"
                if path == RUN_CONTRACT_PATH
                else HOST_CAPABILITY_ATTESTATION_SCHEMA_ID
                if path == HOST_CAPABILITY_ATTESTATION_PATH
                else "crossframe.ultra.v82.unexpected-u0-artifact"
            ),
            "phase_id": "U0",
            "path": path,
            "sha256": authority_sha256(path),
        }
        for path in manifest_u0_paths
    ]
    for number in range(2, 12):
        phase_id = f"U{number}"
        manifest_artifacts.extend(
            {
                "schema_id": "crossframe.ultra.v82.fixture-authority",
                "phase_id": phase_id,
                "path": path,
                "sha256": digest,
            }
            for path, digest in refs_by_phase[phase_id].items()
        )
    manifest = {
        "artifacts": manifest_artifacts,
        "phase_chain_head_sha256": events[-1]["event_sha256"],
    }
    return modules, layout, manifest


def add_finalized_evidence_lineage(
    modules: SimpleNamespace,
    layout: object,
    manifest: dict[str, object],
) -> dict[str, object]:
    request_bytes = (layout.input_dir / "request.bin").read_bytes()
    new_evidence_bytes = (layout.input_dir / "new-evidence.bin").read_bytes()
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    new_evidence_sha256 = hashlib.sha256(new_evidence_bytes).hexdigest()
    pending = {
        "schema_id": EVIDENCE_LINEAGE_SCHEMA_ID,
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": modules.constants.current_version_binding(),
        "generated_at": STAMP,
        "content_sha256": "0" * 64,
        "phase_id": "U0",
        "parent_run_id": "20260803T000000Z-abcdef123456",
        "parent_u3_event_sha256": "7" * 64,
        "parent_evidence_sha256": "8" * 64,
        "parent_evidence_cutoff": "2026-08-03T00:00:00Z",
        "evidence_cutoff": STAMP,
        "inherited_input_refs": [
            {
                "path": "input/request.bin",
                "sha256": request_sha256,
                "media_type": "application/octet-stream",
            }
        ],
        "new_evidence_ref": {
            "path": "input/new-evidence.bin",
            "sha256": new_evidence_sha256,
            "media_type": "application/octet-stream",
        },
        "status": "pending-u0-attestation",
    }
    pending["content_sha256"] = modules.schemas.compute_artifact_content_sha256(
        pending
    )
    pending_path = layout.recovery_dir / "evidence-lineage-request.json"
    write_json(pending_path, pending)
    run_contract_path = layout.run_dir / RUN_CONTRACT_PATH
    finalized = {
        **{
            field: copy.deepcopy(pending[field])
            for field in (
                "schema_id",
                "schema_version",
                "run_id",
                "version_binding",
                "phase_id",
                "parent_run_id",
                "parent_u3_event_sha256",
                "parent_evidence_sha256",
                "parent_evidence_cutoff",
                "evidence_cutoff",
                "inherited_input_refs",
                "new_evidence_ref",
            )
        },
        "generated_at": "2026-08-04T00:00:01Z",
        "content_sha256": "0" * 64,
        "lineage_request_sha256": hashlib.sha256(
            pending_path.read_bytes()
        ).hexdigest(),
        "request_sha256": request_sha256,
        "capability_attestation_sha256": CAPABILITY_ATTESTATION_SHA256,
        "run_contract_sha256": hashlib.sha256(
            run_contract_path.read_bytes()
        ).hexdigest(),
        "u0_phase_event_sha256": f"{32:064x}",
        "status": "finalized-u0-admission",
    }
    finalized["content_sha256"] = modules.schemas.compute_artifact_content_sha256(
        finalized
    )
    finalized_path = layout.run_dir / EVIDENCE_LINEAGE_PATH
    write_json(finalized_path, finalized)
    manifest["artifacts"].append(
        {
            "schema_id": EVIDENCE_LINEAGE_SCHEMA_ID,
            "phase_id": "U0",
            "path": EVIDENCE_LINEAGE_PATH,
            "sha256": hashlib.sha256(finalized_path.read_bytes()).hexdigest(),
        }
    )
    return finalized


def test_host_capability_attestation_is_a_known_structured_artifact(
    tmp_path: Path,
) -> None:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=(tmp_path / "prod").resolve(),
        test_root=(tmp_path / "test").resolve(),
    )
    layout = modules.paths.build_run_layout(modules.paths.RunMode.TEST, RUN_ID, policy)
    contract = {
        "request_sha256": "a" * 64,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "sensitivity": "public",
        "retention": "retain",
        "outbound_permission": "allowed",
        "evidence_cutoff": STAMP,
        "capabilities": default_capability_requirements(),
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }
    attestation = capability_attestation_for_contract(
        run_id=RUN_ID,
        version_binding=modules.constants.current_version_binding(),
        contract=contract,
        generated_at=STAMP,
    )
    attestation_path = layout.run_dir / HOST_CAPABILITY_ATTESTATION_PATH
    attestation_path.parent.mkdir(parents=True)
    attestation_path.write_bytes(attestation.artifact_bytes)
    manifest = {
        "artifacts": [
            {
                "schema_id": HOST_CAPABILITY_ATTESTATION_SCHEMA_ID,
                "phase_id": "U0",
                "path": HOST_CAPABILITY_ATTESTATION_PATH,
            }
        ]
    }
    issues: dict[str, list[tuple[str, str]]] = {"artifact-integrity": []}

    loaded = modules.validation._load_structured_artifacts(
        layout,
        manifest,
        issues,
    )

    assert issues == {"artifact-integrity": []}
    assert loaded == {HOST_CAPABILITY_ATTESTATION_SCHEMA_ID: [attestation.document]}


def test_disk_authority_accepts_fixed_u0_manifest_only_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
    )

    authority = modules.validation._load_verified_disk_authority(layout, manifest)

    assert authority["refs_by_phase"]["U0"] == {
        RUN_CONTRACT_PATH: hashlib.sha256(
            (layout.run_dir / RUN_CONTRACT_PATH).read_bytes()
        ).hexdigest()
    }


def test_disk_authority_accepts_finalized_evidence_child_u0_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
    )
    finalized = add_finalized_evidence_lineage(modules, layout, manifest)

    authority = modules.validation._load_verified_disk_authority(layout, manifest)

    assert authority["evidence_lineage"] == finalized
    assert set(
        record["path"]
        for record in manifest["artifacts"]
        if record["phase_id"] == "U0"
    ) == {
        RUN_CONTRACT_PATH,
        HOST_CAPABILITY_ATTESTATION_PATH,
        EVIDENCE_LINEAGE_PATH,
    }


def test_finalized_evidence_lineage_is_a_known_structured_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
    )
    finalized = add_finalized_evidence_lineage(modules, layout, manifest)
    lineage_record = next(
        record
        for record in manifest["artifacts"]
        if record["path"] == EVIDENCE_LINEAGE_PATH
    )
    issues: dict[str, list[tuple[str, str]]] = {"artifact-integrity": []}

    loaded = modules.validation._load_structured_artifacts(
        layout,
        {"artifacts": [lineage_record]},
        issues,
    )

    assert issues == {"artifact-integrity": []}
    assert loaded == {EVIDENCE_LINEAGE_SCHEMA_ID: [finalized]}


def test_disk_authority_rejects_rehashed_lineage_with_wrong_u0_event_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
    )
    finalized = add_finalized_evidence_lineage(modules, layout, manifest)
    finalized["u0_phase_event_sha256"] = "f" * 64
    finalized["content_sha256"] = modules.schemas.compute_artifact_content_sha256(
        finalized
    )
    finalized_path = layout.run_dir / EVIDENCE_LINEAGE_PATH
    write_json(finalized_path, finalized)
    lineage_record = next(
        record
        for record in manifest["artifacts"]
        if record["path"] == EVIDENCE_LINEAGE_PATH
    )
    lineage_record["sha256"] = hashlib.sha256(
        finalized_path.read_bytes()
    ).hexdigest()

    with pytest.raises(modules.validation._AuthorityDAGError) as captured:
        modules.validation._load_verified_disk_authority(layout, manifest)

    assert captured.value.phase_id == "U0"


def test_disk_authority_rejects_pending_only_evidence_child_before_u1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
    )
    add_finalized_evidence_lineage(modules, layout, manifest)
    (layout.run_dir / EVIDENCE_LINEAGE_PATH).unlink()
    manifest["artifacts"] = [
        record
        for record in manifest["artifacts"]
        if record["path"] != EVIDENCE_LINEAGE_PATH
    ]

    with pytest.raises(modules.validation._AuthorityDAGError) as captured:
        modules.validation._load_verified_disk_authority(layout, manifest)

    assert captured.value.phase_id == "U0"


@pytest.mark.parametrize(
    "manifest_u0_paths",
    (
        (RUN_CONTRACT_PATH,),
        (HOST_CAPABILITY_ATTESTATION_PATH,),
        (RUN_CONTRACT_PATH, HOST_CAPABILITY_ATTESTATION_PATH, EXTRA_U0_PATH),
    ),
    ids=("missing-attestation", "missing-run-contract", "unexpected-extra"),
)
def test_disk_authority_rejects_non_exact_u0_manifest_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_u0_paths: tuple[str, ...],
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
        manifest_u0_paths=manifest_u0_paths,
    )

    with pytest.raises(modules.validation._AuthorityDAGError) as captured:
        modules.validation._load_verified_disk_authority(layout, manifest)

    assert captured.value.phase_id == "U0"


@pytest.mark.parametrize(
    "checkpoint_u0_paths",
    ((), (RUN_CONTRACT_PATH, EXTRA_U0_PATH)),
    ids=("missing-run-contract", "unexpected-extra"),
)
def test_disk_authority_rejects_non_exact_u0_checkpoint_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    checkpoint_u0_paths: tuple[str, ...],
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
        checkpoint_u0_paths=checkpoint_u0_paths,
    )

    with pytest.raises(modules.validation._AuthorityDAGError) as captured:
        modules.validation._load_verified_disk_authority(layout, manifest)

    assert captured.value.phase_id == "U0"


def test_disk_authority_rejects_u0_attestation_hash_not_bound_by_run_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules, layout, manifest = stubbed_disk_authority(
        tmp_path,
        monkeypatch,
        contract_capability_sha256="e" * 64,
    )

    with pytest.raises(modules.validation._AuthorityDAGError) as captured:
        modules.validation._load_verified_disk_authority(layout, manifest)

    assert captured.value.phase_id == "U0"


def test_validator_set_binds_every_runtime_and_u1_authority_checker(
    tmp_path: Path,
) -> None:
    isolated_repo = tmp_path / "repo"
    isolated_skill = isolated_repo / "skills/crossframe-ultra"
    shutil.copytree(REPO_ROOT / "skills/crossframe-ultra", isolated_skill)
    isolated_scripts = isolated_repo / "scripts"
    isolated_scripts.mkdir()
    shutil.copy2(
        REPO_ROOT / "scripts/check_crossframe_ultra_artifacts.py",
        isolated_scripts / "check_crossframe_ultra_artifacts.py",
    )
    modules = load_validation_runtime()
    dependencies = (
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py",
        "scripts/check_crossframe_ultra_artifacts.py",
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py",
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/errors.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/evidence.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/status.py",
    )

    baseline = modules.validation.validator_set_sha256(isolated_repo)
    for relative in dependencies:
        path = isolated_repo / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        try:
            assert modules.validation.validator_set_sha256(isolated_repo) != baseline
        finally:
            path.write_bytes(original)


def test_task3_validator_binds_sealed_request_and_read_plan_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=(tmp_path / "prod").resolve(),
        test_root=(tmp_path / "test").resolve(),
    )
    layout = modules.paths.build_run_layout(modules.paths.RunMode.TEST, RUN_ID, policy)
    monkeypatch.setattr(modules.validation, "default_root_policy", lambda: policy)
    request_sha256 = "1" * 64
    parent_event_sha256 = "2" * 64
    run_contract = {"request_sha256": request_sha256}
    source_lock = {"authority": "source-lock"}
    read_plan = {"authority": "read-plan"}
    source_coverage = {"authority": "source-coverage"}
    read_event = {"source_unit_id": "V82-P0001"}
    paths = {
        "recovery/u1-authority/source-lock.json": source_lock,
        "recovery/u1-authority/read-plan.json": read_plan,
        "recovery/u1-authority/source-coverage.json": source_coverage,
        "artifacts/ultra-run-contract.json": run_contract,
    }
    for relative, document in paths.items():
        write_json(layout.run_dir / relative, document)
    read_events_path = layout.run_dir / modules.artifacts.READ_EVENTS_PATH
    read_events_path.parent.mkdir(parents=True, exist_ok=True)
    read_events_path.write_bytes(canonical_bytes(read_event))

    captured: dict[str, object] = {}

    def capture_persisted_authority(**kwargs: object) -> None:
        captured.update(kwargs)

    source_manifest = object()
    monkeypatch.setattr(
        modules.source_integrity,
        "load_source_manifest",
        lambda *_args, **_kwargs: source_manifest,
    )
    monkeypatch.setattr(
        modules.source_integrity,
        "_validate_persisted_u1_authority",
        capture_persisted_authority,
    )
    u1_refs = {
        relative: hashlib.sha256((layout.run_dir / relative).read_bytes()).hexdigest()
        for relative in (
            "recovery/u1-authority/source-lock.json",
            "recovery/u1-authority/read-plan.json",
            "recovery/u1-authority/source-coverage.json",
        )
    }
    authority = {
        "run_authority": {
            "source_sha256": "3" * 64,
            "run_contract_sha256": hashlib.sha256(
                (layout.run_dir / "artifacts/ultra-run-contract.json").read_bytes()
            ).hexdigest(),
            "evidence_cutoff": STAMP,
            "input_refs": [
                {
                    "path": "input/request.md",
                    "sha256": "4" * 64,
                    "media_type": "text/markdown",
                }
            ],
        },
        "events": (
            {
                "phase_id": "U0",
                "event_sha256": parent_event_sha256,
            },
        ),
        "refs_by_phase": {"U1": u1_refs},
    }
    manifest = {
        "artifacts": [
            {
                "schema_id": "crossframe.ultra.v82.read-event",
                "path": modules.artifacts.READ_EVENTS_PATH,
            }
        ]
    }
    issues: dict[str, list[tuple[str, str]]] = {"source-read-coverage": []}

    modules.validation._validate_read_events(
        REPO_ROOT,
        layout,
        manifest,
        authority,
        issues,
    )

    assert issues == {"source-read-coverage": []}
    assert captured["manifest"] is source_manifest
    assert captured["expected_request_sha256"] == request_sha256
    assert captured["expected_source_lock_sha256"] == u1_refs[
        "recovery/u1-authority/source-lock.json"
    ]
    assert captured["expected_read_plan_sha256"] == u1_refs[
        "recovery/u1-authority/read-plan.json"
    ]
    assert captured["expected_read_coverage_sha256"] == u1_refs[
        "recovery/u1-authority/source-coverage.json"
    ]
def test_fresh_claim_semantics_reuses_the_support_scope_validator() -> None:
    modules = load_validation_runtime()
    evidence = seal_fixture(modules, "evidence-ledger-valid.json")
    graph = seal_fixture(modules, "claim-mechanism-graph-valid.json")
    roster = next(
        entry
        for entry in evidence["entries"]
        if entry["evidence_id"] == "EVIDENCE-ROSTER-ATLAS"
    )
    graph["claims"][0]["statement"] = roster["cannot_prove"]
    loaded = {
        "crossframe.ultra.v82.evidence-ledger": [evidence],
        "crossframe.ultra.v82.claim-mechanism-graph": [graph],
    }
    issues = {check_id: [] for check_id in modules.validation._CHECK_ORDER}

    modules.validation._validate_claim_semantics(loaded, issues)

    assert any(
        code == "ULTRA-EVIDENCE-HOLLOW"
        for code, _ in issues["semantic-tamper-resistance"]
    )
def test_validator_report_layers_separate_deterministic_adversarial_and_semantic() -> None:
    modules = load_validation_runtime()
    build_layers = getattr(modules.validation, "_build_validation_layers", None)
    assert callable(build_layers)
    issues = {check_id: [] for check_id in modules.validation._CHECK_ORDER}

    passing = build_layers(issues, semantic_review_status="pass")

    assert [row["layer_id"] for row in passing] == [
        "deterministic",
        "adversarial",
        "fresh-semantic",
    ]
    assert [row["status"] for row in passing] == ["pass", "pass", "pass"]

    issues["semantic-tamper-resistance"].append(
        ("ULTRA-EVIDENCE-HOLLOW", "artifacts/U06")
    )
    failing = build_layers(issues, semantic_review_status="fail")
    assert [row["status"] for row in failing] == ["pass", "fail", "fail"]


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


def test_persisted_u1_authority_reconstruction_returns_an_issuer_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    arguments = persisted_u1_authority_args(run)

    seal = run.modules.source_integrity._validate_persisted_u1_authority(
        **arguments
    )

    assert type(seal) is run.modules.source_integrity.U1AuthoritySeal
    assert run.modules.source_integrity.verify_u1_authority_seal(seal) is seal
    assert seal.source_lock_artifact_sha256 == arguments[
        "expected_source_lock_sha256"
    ]
    assert seal.read_plan_artifact_sha256 == arguments[
        "expected_read_plan_sha256"
    ]
    assert seal.read_coverage_artifact_sha256 == arguments[
        "expected_read_coverage_sha256"
    ]


def test_persisted_u1_source_lock_rejects_live_skill_tree_drift(
    tmp_path: Path,
) -> None:
    modules = load_validation_runtime()
    isolated_repo = tmp_path / "repo"
    isolated_skill = isolated_repo / "skills/crossframe-ultra"
    shutil.copytree(REPO_ROOT / "skills/crossframe-ultra", isolated_skill)
    release_builder = isolated_skill / "scripts/build_crossframe_ultra_release_manifest.py"
    rebuilt = subprocess.run(
        [sys.executable, "-B", str(release_builder), "--repo", str(isolated_repo), "--write"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert rebuilt.returncode == 0, rebuilt.stderr

    source_manifest_path = isolated_skill / "references/source-manifest.json"
    source_manifest = modules.source_integrity.load_source_manifest(
        source_manifest_path,
        expected_sha256=hashlib.sha256(source_manifest_path.read_bytes()).hexdigest(),
    )
    release_manifest_path = isolated_skill / "references/release-manifest.json"
    measurement = modules.source_integrity.measure_u1_prerequisites(
        isolated_repo,
        manifest=source_manifest,
        release_manifest_path=release_manifest_path,
        run_mode="test",
    )
    assert measurement.ready, measurement.missing

    policy = modules.paths.RootPolicy(
        production_root=(tmp_path / "prod").resolve(),
        test_root=(tmp_path / "test").resolve(),
    )
    layout = modules.paths.build_run_layout(
        modules.paths.RunMode.TEST,
        RUN_ID,
        policy,
    )
    layout.input_dir.mkdir(parents=True)
    request = canonical_bytes({"request": "bind the live canonical skill tree"})
    request_path = layout.input_dir / "request.json"
    request_path.write_bytes(request)
    expected_inputs = [
        {
            "path": request_path.name,
            "sha256": hashlib.sha256(request).hexdigest(),
            "media_type": "application/json",
        }
    ]
    parent_event_sha256 = "a" * 64
    binding = modules.constants.current_version_binding()
    source_lock = modules.source_integrity.build_source_lock(
        run_id=RUN_ID,
        version_binding=binding,
        generated_at=STAMP,
        prerequisite_measurement=measurement,
        parent_event_sha256=parent_event_sha256,
        evidence_cutoff=STAMP,
        run_layout=layout,
        inputs=expected_inputs,
    )
    arguments = {
        "repo": isolated_repo,
        "manifest": source_manifest,
        "expected_run_id": RUN_ID,
        "expected_run_mode": "test",
        "expected_version_binding": binding,
        "expected_parent_event_sha256": parent_event_sha256,
        "expected_evidence_cutoff": STAMP,
        "expected_inputs": expected_inputs,
        "run_layout": layout,
    }
    assert modules.source_integrity._validate_persisted_source_lock(
        source_lock,
        **arguments,
    ) == canonical_sha256(source_lock)

    checker = isolated_skill / "scripts/check_crossframe_ultra_artifacts.py"
    checker.write_bytes(checker.read_bytes() + b"\n")

    with pytest.raises(
        modules.source_integrity.SourceLockError,
        match="canonical skill tree",
    ):
        modules.source_integrity._validate_persisted_source_lock(
            source_lock,
            **arguments,
        )


def test_parent_commits_exact_child_bytes_and_rejects_edited_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = build_valid_run(tmp_path, monkeypatch)
    report_bytes = run.modules.validation.validate_run_from_disk(
        REPO_ROOT, run.modules.paths.RunMode.TEST, RUN_ID
    )
    report = parse_report(report_bytes)
    manifest_sha = str(report["manifest_sha256"])

    with _owned_validation_lease(run) as lease:
        committed = run.modules.validation.commit_validation_attempt(
            run.layout,
            attempt_id=str(report["attempt_id"]),
            report_bytes=report_bytes,
            expected_manifest_sha256=manifest_sha,
            expected_validator_set_sha256=run.validator_set_sha256,
            lease=lease,
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
        edited["content_sha256"] = run.modules.schemas.compute_artifact_content_sha256(
            edited
        )
        with pytest.raises(ValueError, match="fresh|report|bytes|status"):
            run.modules.validation.commit_validation_attempt(
                run.layout,
                attempt_id=str(report["attempt_id"]),
                report_bytes=canonical_bytes(edited),
                expected_manifest_sha256=manifest_sha,
                expected_validator_set_sha256=run.validator_set_sha256,
                lease=lease,
            )


def test_validation_commit_requires_current_lease_owner_before_any_write(
    tmp_path: Path,
) -> None:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=tmp_path / "production",
        test_root=tmp_path / "test",
    )
    layout = modules.paths.build_run_layout(
        modules.paths.RunMode.TEST,
        RUN_ID,
        policy,
    )
    layout.run_dir.mkdir(parents=True)
    attempt_id = "lease-owner-boundary"
    attempt_path = (
        layout.validation_attempts_dir
        / attempt_id
        / "ultra-validator-report.json"
    )
    current_path = layout.validation_current_dir / "ultra-validator-report.json"
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in (attempt_path, current_path)
    }
    owner = modules.locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 4, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    foreign = modules.locks.Lease(
        run_id=owner.run_id,
        owner_pid=owner.owner_pid,
        owner_nonce="foreign-owner-nonce-000000000000",
        acquired_at=owner.acquired_at,
        heartbeat_at=owner.heartbeat_at,
        expires_at=owner.expires_at,
    )
    try:
        with pytest.raises(modules.locks.LeaseOwnershipError):
            modules.validation.commit_validation_attempt(
                layout,
                attempt_id=attempt_id,
                report_bytes=b"foreign lease must fail before report parsing\n",
                expected_manifest_sha256="a" * 64,
                expected_validator_set_sha256="b" * 64,
                lease=foreign,
            )
    finally:
        modules.locks.release_run_lease(layout, owner)

    for path, previous in before.items():
        if previous is None:
            assert not path.exists()
        else:
            assert path.read_bytes() == previous


def test_validation_commit_rejects_existing_cancel_intent_before_any_write(
    tmp_path: Path,
) -> None:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=tmp_path / "production",
        test_root=tmp_path / "test",
    )
    layout = modules.paths.build_run_layout(
        modules.paths.RunMode.TEST,
        RUN_ID,
        policy,
    )
    layout.run_dir.mkdir(parents=True)
    attempt_id = "cancel-intent-boundary"
    attempt_path = (
        layout.validation_attempts_dir
        / attempt_id
        / "ultra-validator-report.json"
    )
    current_path = layout.validation_current_dir / "ultra-validator-report.json"
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in (attempt_path, current_path)
    }
    lease = modules.locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 4, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    try:
        modules.locks.request_cancel(
            layout,
            reason="cancel before validation commit",
            now=datetime(2026, 8, 4, 0, 0, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(modules.locks.CancelledRunError):
            modules.validation.commit_validation_attempt(
                layout,
                attempt_id=attempt_id,
                report_bytes=b"cancel intent must fail before report parsing\n",
                expected_manifest_sha256="a" * 64,
                expected_validator_set_sha256="b" * 64,
                lease=lease,
            )
    finally:
        modules.locks.release_run_lease(layout, lease)

    for path, previous in before.items():
        if previous is None:
            assert not path.exists()
        else:
            assert path.read_bytes() == previous


def _validation_commit_boundary_harness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    attempt_id: str,
) -> SimpleNamespace:
    modules = load_validation_runtime()
    policy = modules.paths.RootPolicy(
        production_root=tmp_path / "production",
        test_root=tmp_path / "test",
    )
    layout = modules.paths.build_run_layout(
        modules.paths.RunMode.TEST,
        RUN_ID,
        policy,
    )
    layout.run_dir.mkdir(parents=True)
    manifest_path = modules.artifacts.validation_manifest_path(layout)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = b"fixed validation manifest generation\n"
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    validator_sha256 = "d" * 64
    report_bytes = b"fixed fresh validator report bytes\n"
    monkeypatch.setattr(modules.validation, "default_root_policy", lambda: policy)
    monkeypatch.setattr(
        modules.validation,
        "validate_artifact_manifest",
        lambda selected_layout, selected_path: {
            "validator_set_sha256": validator_sha256
        },
    )
    monkeypatch.setattr(
        modules.validation,
        "validator_set_sha256",
        lambda repo: validator_sha256,
    )
    monkeypatch.setattr(
        modules.validation,
        "_validated_report_bytes",
        lambda *args, **kwargs: {"attempt_id": attempt_id},
    )
    lease = modules.locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 4, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    attempt_path = (
        layout.validation_attempts_dir
        / attempt_id
        / "ultra-validator-report.json"
    )
    current_path = layout.validation_current_dir / "ultra-validator-report.json"
    return SimpleNamespace(
        modules=modules,
        layout=layout,
        lease=lease,
        lease_path=layout.run_dir / ".writer-lease.json",
        lease_bytes=(layout.run_dir / ".writer-lease.json").read_bytes(),
        attempt_id=attempt_id,
        attempt_path=attempt_path,
        current_path=current_path,
        report_bytes=report_bytes,
        manifest_sha256=manifest_sha256,
        validator_sha256=validator_sha256,
    )


def _replace_with_foreign_lease(harness: SimpleNamespace) -> None:
    lease = harness.lease
    harness.modules.jsonio.atomic_write_json(
        harness.lease_path,
        {
            "run_id": lease.run_id,
            "owner_pid": lease.owner_pid,
            "owner_nonce": "foreign-owner-nonce-000000000000",
            "acquired_at": lease.acquired_at,
            "heartbeat_at": lease.heartbeat_at,
            "expires_at": lease.expires_at,
        },
    )


@pytest.mark.parametrize("authority_loss", ("cancel", "foreign-owner"))
def test_validation_commit_rechecks_authority_after_fresh_disk_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    authority_loss: str,
) -> None:
    harness = _validation_commit_boundary_harness(
        tmp_path,
        monkeypatch,
        attempt_id=f"fresh-boundary-{authority_loss}",
    )

    def fresh_validation(*args: object) -> bytes:
        if authority_loss == "cancel":
            harness.modules.locks.request_cancel(
                harness.layout,
                reason="cancel after fresh validation",
                now=datetime(2026, 8, 4, 0, 0, 1, tzinfo=timezone.utc),
            )
        else:
            _replace_with_foreign_lease(harness)
        return harness.report_bytes

    monkeypatch.setattr(
        harness.modules.validation,
        "validate_run_from_disk",
        fresh_validation,
    )
    expected_error = (
        harness.modules.locks.CancelledRunError
        if authority_loss == "cancel"
        else harness.modules.locks.LeaseOwnershipError
    )
    try:
        with pytest.raises(expected_error):
            harness.modules.validation.commit_validation_attempt(
                harness.layout,
                attempt_id=harness.attempt_id,
                report_bytes=harness.report_bytes,
                expected_manifest_sha256=harness.manifest_sha256,
                expected_validator_set_sha256=harness.validator_sha256,
                lease=harness.lease,
            )
    finally:
        if authority_loss == "foreign-owner":
            harness.modules.jsonio.atomic_write_bytes(
                harness.lease_path,
                harness.lease_bytes,
            )
        harness.modules.locks.release_run_lease(harness.layout, harness.lease)

    assert not harness.attempt_path.exists()
    assert not harness.current_path.exists()


@pytest.mark.parametrize("authority_loss", ("cancel", "foreign-owner"))
def test_validation_commit_rechecks_authority_between_attempt_and_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    authority_loss: str,
) -> None:
    harness = _validation_commit_boundary_harness(
        tmp_path,
        monkeypatch,
        attempt_id=f"current-boundary-{authority_loss}",
    )
    monkeypatch.setattr(
        harness.modules.validation,
        "validate_run_from_disk",
        lambda *args: harness.report_bytes,
    )
    original_write = harness.modules.validation.atomic_write_bytes

    def mutate_after_attempt(path: Path, value: bytes) -> None:
        original_write(path, value)
        if path != harness.attempt_path:
            return
        if authority_loss == "cancel":
            harness.modules.locks.request_cancel(
                harness.layout,
                reason="cancel after validation attempt write",
                now=datetime(2026, 8, 4, 0, 0, 1, tzinfo=timezone.utc),
            )
        else:
            _replace_with_foreign_lease(harness)

    monkeypatch.setattr(
        harness.modules.validation,
        "atomic_write_bytes",
        mutate_after_attempt,
    )
    expected_error = (
        harness.modules.locks.CancelledRunError
        if authority_loss == "cancel"
        else harness.modules.locks.LeaseOwnershipError
    )
    try:
        with pytest.raises(expected_error):
            harness.modules.validation.commit_validation_attempt(
                harness.layout,
                attempt_id=harness.attempt_id,
                report_bytes=harness.report_bytes,
                expected_manifest_sha256=harness.manifest_sha256,
                expected_validator_set_sha256=harness.validator_sha256,
                lease=harness.lease,
            )
    finally:
        if authority_loss == "foreign-owner":
            harness.modules.jsonio.atomic_write_bytes(
                harness.lease_path,
                harness.lease_bytes,
            )
        harness.modules.locks.release_run_lease(harness.layout, harness.lease)

    assert harness.attempt_path.read_bytes() == harness.report_bytes
    assert not harness.current_path.exists()


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

    with _owned_validation_lease(run) as lease:
        with pytest.raises(ValueError, match="stale|manifest|fresh"):
            run.modules.validation.commit_validation_attempt(
                run.layout,
                attempt_id=str(stale["attempt_id"]),
                report_bytes=stale_bytes,
                expected_manifest_sha256=str(stale["manifest_sha256"]),
                expected_validator_set_sha256=run.validator_set_sha256,
                lease=lease,
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
