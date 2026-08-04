from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
SOURCE_MANIFEST = ROOT / "skills/crossframe-ultra/references/source-manifest.json"
SOURCE_MANIFEST_SHA256 = (
    "1c22cda241473ecb3654e37ee9890b975457bb098334ab5c0f85d2775abf6725"
)
RUN_ID = "20260802T000000Z-4f6d87c20a11"
STAMP = "2026-08-02T00:00:00Z"
PARENT_EVENT_SHA256 = "1" * 64
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _canonical(value: object) -> bytes:
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


LOCKED_INPUT_SHA256 = hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
_LOCKED_INPUTS = [
    {
        "path": "AGENTS.md",
        "sha256": LOCKED_INPUT_SHA256,
        "media_type": "text/markdown",
    }
]
INPUT_SNAPSHOT_SHA256 = hashlib.sha256(_canonical(_LOCKED_INPUTS)).hexdigest()


def _hash_without(value: dict[str, object], *fields: str) -> str:
    payload = copy.deepcopy(value)
    for field in fields:
        payload.pop(field, None)
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _binding() -> dict[str, object]:
    return {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20",
        "framework_semantic_sha256": "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0",
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "compiler_version": "1.0.0",
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
        "source_tree_sha256": "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187",
    }


def _inputs() -> list[dict[str, str]]:
    return copy.deepcopy(_LOCKED_INPUTS)


def _run_layout(root: Path, *, run_id: str = RUN_ID):
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

    policy = RootPolicy(root / "production-control", root / "test-control")
    layout = build_run_layout(RunMode.TEST, run_id, policy)
    layout.input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "AGENTS.md", layout.input_dir / "AGENTS.md")
    return layout


def _snapshot(module):
    return module.load_source_manifest(
        SOURCE_MANIFEST,
        expected_sha256=SOURCE_MANIFEST_SHA256,
    )


def _release_artifacts(repo: Path) -> list[dict[str, str]]:
    skill_root = repo / "skills/crossframe-ultra"
    result: list[dict[str, str]] = []
    for path in sorted(skill_root.rglob("*")):
        relative = path.relative_to(skill_root)
        if (
            any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts)
            or relative.as_posix() == "references/release-manifest.json"
            or path.name == ".v8-full-source.lock"
        ):
            continue
        if path.is_file():
            result.append(
                {
                    "path": relative.as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "media_type": "application/octet-stream",
                }
            )
    return result


def _write_release_manifest(repo: Path, path: Path) -> dict[str, object]:
    source = json.loads(
        (repo / "skills/crossframe-ultra/references/source-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.release-manifest",
        "schema_version": 1,
        "run_id": "release-authority-test",
        "version_binding": _binding(),
        "generated_at": STAMP,
        "release_id": "ultra-v8.2-r1",
        "release_state": "stable",
        "stable_pointer": "references/source-manifest.json",
        "framework_source": {
            "path": "references/source-manifest.json",
            "raw_sha256": source["raw_sha256"],
            "semantic_sha256": source["semantic_sha256"],
            "alternate_raw_packages": [],
        },
        "compiler": {
            "normalization_algorithm": "ultra-semantic-normalization",
            "normalization_version": "1.0.0",
        },
        "source_counts": {
            "paragraphs": source["paragraph_count"],
            "headings": source["heading_count"],
            "tables": source["table_count"],
            "concepts": source["concept_count"],
            "contracts": source["contract_count"],
            "source_units": source["source_unit_count"],
        },
        "release_artifacts": _release_artifacts(repo),
        "built_at": STAMP,
        "validated_at": STAMP,
    }
    document["content_sha256"] = _hash_without(document, "content_sha256")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(document))
    return document


class ExternalReadBatch:
    def __init__(self, events, receipts):
        self._events = tuple(copy.deepcopy(event) for event in events)
        self._receipts = tuple(receipts)

    @property
    def events(self):
        return tuple(copy.deepcopy(event) for event in self._events)

    @property
    def receipts(self):
        return self._receipts


def _source_lock(module, prerequisite_measurement, run_layout):
    artifact = module.build_source_lock(
        run_id=RUN_ID,
        version_binding=_binding(),
        generated_at=STAMP,
        prerequisite_measurement=prerequisite_measurement,
        parent_event_sha256=PARENT_EVENT_SHA256,
        evidence_cutoff=STAMP,
        run_layout=run_layout,
        inputs=_inputs(),
    )
    validation = module.validate_source_lock(
        artifact,
        prerequisite_measurement=prerequisite_measurement,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_parent_event_sha256=PARENT_EVENT_SHA256,
        expected_evidence_cutoff=STAMP,
        expected_inputs=_inputs(),
        run_layout=run_layout,
    )
    return artifact, validation


def _read_events(module, snapshot, source_lock_sha256: str, repo: Path):
    return module.capture_authority_read_diagnostic(
        repo,
        run_id=RUN_ID,
        version_binding=_binding(),
        manifest=snapshot,
        source_lock_sha256=source_lock_sha256,
        parent_event_sha256=PARENT_EVENT_SHA256,
        reader_mode="full-source",
        read_at=STAMP,
    )


@pytest.fixture(scope="module")
def prerequisite_context(tmp_path_factory):
    import ultra_runtime.source_integrity as module

    fixture_root = tmp_path_factory.mktemp("u1-host-authority")
    authority_repo = fixture_root / "repo"
    skill_root = authority_repo / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", skill_root)
    shutil.copy2(ROOT / "AGENTS.md", authority_repo / "AGENTS.md")
    jsonio = skill_root / "scripts/ultra_runtime/jsonio.py"
    jsonio.write_bytes(jsonio.read_bytes().replace(b"\r\n", b"\n"))
    release_path = fixture_root / "release-manifest.json"
    document = _write_release_manifest(authority_repo, release_path)
    measurement = module.measure_u1_prerequisites(
        authority_repo,
        manifest=module.load_source_manifest(
            skill_root / "references/source-manifest.json",
            expected_sha256=SOURCE_MANIFEST_SHA256,
        ),
        release_manifest_path=release_path,
        run_mode="test",
    )
    assert measurement.ready
    run_layout = _run_layout(fixture_root / "base-run-authority")
    return {
        "fixture_root": fixture_root,
        "repo": authority_repo,
        "release_path": release_path,
        "document": document,
        "measurement": measurement,
        "run_layout": run_layout,
    }


def test_source_lock_uses_the_validated_run_layout_input_root(
    prerequisite_context,
    monkeypatch,
):
    import ultra_runtime.source_integrity as module

    layout = _run_layout(prerequisite_context["fixture_root"] / "run-authority")
    artifact = module.build_source_lock(
        run_id=RUN_ID,
        version_binding=_binding(),
        generated_at=STAMP,
        prerequisite_measurement=prerequisite_context["measurement"],
        parent_event_sha256=PARENT_EVENT_SHA256,
        evidence_cutoff=STAMP,
        run_layout=layout,
        inputs=_inputs(),
    )
    validation = module.validate_source_lock(
        artifact,
        prerequisite_measurement=prerequisite_context["measurement"],
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_parent_event_sha256=PARENT_EVENT_SHA256,
        expected_evidence_cutoff=STAMP,
        expected_inputs=_inputs(),
        run_layout=layout,
    )
    assert validation.input_root == layout.input_dir.resolve()
    assert validation.input_root != prerequisite_context["repo"].resolve()

    with pytest.raises(TypeError):
        module.build_source_lock(
            run_id=RUN_ID,
            version_binding=_binding(),
            generated_at=STAMP,
            prerequisite_measurement=prerequisite_context["measurement"],
            parent_event_sha256=PARENT_EVENT_SHA256,
            evidence_cutoff=STAMP,
            input_root=prerequisite_context["repo"],
            inputs=_inputs(),
        )

    other_layout = _run_layout(
        prerequisite_context["fixture_root"] / "other-run-authority",
        run_id="20260802T000001Z-5a7e9c31b022",
    )
    with pytest.raises(module.SourceLockError, match="layout|run|input"):
        module.validate_source_lock(
            artifact,
            prerequisite_measurement=prerequisite_context["measurement"],
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
            expected_evidence_cutoff=STAMP,
            expected_inputs=_inputs(),
            run_layout=other_layout,
        )

    traversing = [
        {
            "path": "../AGENTS.md",
            "sha256": LOCKED_INPUT_SHA256,
            "media_type": "text/markdown",
        }
    ]
    with pytest.raises(module.SourceLockError, match="escape|path"):
        module.build_source_lock(
            run_id=RUN_ID,
            version_binding=_binding(),
            generated_at=STAMP,
            prerequisite_measurement=prerequisite_context["measurement"],
            parent_event_sha256=PARENT_EVENT_SHA256,
            evidence_cutoff=STAMP,
            run_layout=layout,
            inputs=traversing,
        )

    import ultra_runtime.paths as paths

    monkeypatch.setattr(
        paths,
        "_is_reparse_point",
        lambda candidate: candidate == layout.input_dir,
    )
    with pytest.raises(module.SourceLockError, match="layout|input|reparse"):
        module.build_source_lock(
            run_id=RUN_ID,
            version_binding=_binding(),
            generated_at=STAMP,
            prerequisite_measurement=prerequisite_context["measurement"],
            parent_event_sha256=PARENT_EVENT_SHA256,
            evidence_cutoff=STAMP,
            run_layout=layout,
            inputs=_inputs(),
        )


@pytest.fixture(scope="module")
def read_batch(explicit_read_context):
    return (
        explicit_read_context["module"],
        explicit_read_context["snapshot"],
        explicit_read_context["lock"],
        explicit_read_context["lock_seal"],
        ExternalReadBatch(
            explicit_read_context["events"],
            explicit_read_context["receipts"],
        ),
    )


def _audit(module, snapshot, validation, batch):
    return module.audit_read_capture(
        batch.events,
        snapshot,
        receipts=batch.receipts,
        promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_source_lock_sha256=validation.artifact_sha256,
        expected_parent_event_sha256=PARENT_EVENT_SHA256,
    )


def _replace_event(events, index: int, **changes):
    changed = list(events)
    event = copy.deepcopy(changed[index])
    event.update(changes)
    event["read_event_sha256"] = _hash_without(event, "read_event_sha256")
    changed[index] = event
    return changed


def test_source_manifest_and_read_plan_bind_exact_4753_units_without_claiming_reads(
    prerequisite_context,
):
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    source_lock, validation = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    plan = module.build_read_plan(
        snapshot,
        promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        source_lock_sha256=validation.artifact_sha256,
        parent_event_sha256=PARENT_EVENT_SHA256,
    )
    assert plan["source_unit_count"] == 4753
    assert plan["paragraph_count"] == 4631
    assert plan["table_count"] == 122
    assert len(plan["source_units"]) == 4753
    assert "read_events" not in plan
    assert source_lock["source_manifest_sha256"] == SOURCE_MANIFEST_SHA256


def test_source_lock_producer_passes_public_schema_and_recomputes_both_hash_roles(
    prerequisite_context,
):
    import ultra_runtime.source_integrity as module
    from ultra_runtime.schemas import validate_instance

    artifact, validation = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    validate_instance("ultra-source-lock.schema.json", artifact)
    assert artifact["content_sha256"] == _hash_without(artifact, "content_sha256")
    assert validation.content_sha256 == artifact["content_sha256"]
    assert validation.artifact_sha256 == hashlib.sha256(_canonical(artifact)).hexdigest()
    assert validation.free_space_reserve_bytes == 1 << 30
    assert validation.free_space_status == "available"


@pytest.mark.parametrize(
    ("free_bytes", "ready", "status"),
    (
        ((1 << 30) - 1, False, "insufficient"),
        (1 << 30, True, "available"),
        ((1 << 30) + 1, True, "available"),
    ),
)
def test_u1_measurement_uses_the_host_owned_free_space_reserve_boundary(
    monkeypatch,
    prerequisite_context,
    free_bytes,
    ready,
    status,
):
    import ultra_runtime.source_integrity as module

    usage = type("Usage", (), {"free": free_bytes})()
    monkeypatch.setattr(module.shutil, "disk_usage", lambda _path: usage)
    manifest = module.load_source_manifest(
        prerequisite_context["repo"]
        / "skills/crossframe-ultra/references/source-manifest.json",
        expected_sha256=SOURCE_MANIFEST_SHA256,
    )
    measurement = module.measure_u1_prerequisites(
        prerequisite_context["repo"],
        manifest=manifest,
        release_manifest_path=prerequisite_context["release_path"],
        run_mode="test",
    )
    assert measurement.free_space_reserve_bytes == 1 << 30
    assert measurement.free_space_status == status
    assert measurement.ready is ready
    assert ("free_space_reserve" in measurement.missing) is (not ready)
    with pytest.raises(TypeError):
        module.measure_u1_prerequisites(
            prerequisite_context["repo"],
            manifest=manifest,
            release_manifest_path=prerequisite_context["release_path"],
            run_mode="test",
            reserve_bytes=0,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "swapped-valid-sha",
        "self-selected-parent",
        "cross-source",
        "cross-input",
        "cross-cutoff",
    ),
)
def test_source_lock_rejects_resealed_semantic_or_external_authority_drift(
    mutation, prerequisite_context
):
    import ultra_runtime.source_integrity as module
    from ultra_runtime.schemas import validate_instance

    artifact, _ = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    changed = copy.deepcopy(artifact)
    if mutation == "swapped-valid-sha":
        changed["release_manifest_sha256"], changed["compatibility_matrix_sha256"] = (
            changed["compatibility_matrix_sha256"],
            changed["release_manifest_sha256"],
        )
    elif mutation == "self-selected-parent":
        changed["parent_event_sha256"] = "9" * 64
    elif mutation == "cross-source":
        changed["source_manifest_sha256"] = "8" * 64
    elif mutation == "cross-input":
        changed["inputs"][0]["sha256"] = "7" * 64
        changed["input_snapshot_sha256"] = hashlib.sha256(
            _canonical(changed["inputs"])
        ).hexdigest()
    else:
        changed["evidence_cutoff"] = "2026-08-01T00:00:00Z"
    changed["content_sha256"] = _hash_without(changed, "content_sha256")
    validate_instance("ultra-source-lock.schema.json", changed)
    with pytest.raises(module.SourceLockError, match="authority|parent|expected"):
        module.validate_source_lock(
            changed,
            prerequisite_measurement=prerequisite_context["measurement"],
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
            expected_evidence_cutoff=STAMP,
            expected_inputs=_inputs(),
            run_layout=prerequisite_context["run_layout"],
        )


def test_unrelated_owned_root_cannot_authorize_the_locked_input_and_validation_is_nonmutating(
    prerequisite_context,
):
    import ultra_runtime.source_integrity as module

    artifact, _ = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    before = copy.deepcopy(artifact)
    with pytest.raises(TypeError):
        module.validate_source_lock(
            artifact,
            prerequisite_measurement=prerequisite_context["measurement"],
            input_root=prerequisite_context["repo"] / "skills",
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
            expected_evidence_cutoff=STAMP,
            expected_inputs=_inputs(),
        )
    assert artifact == before


def test_source_and_u1_authority_seals_are_issuer_only():
    import ultra_runtime.source_integrity as module

    with pytest.raises(TypeError):
        module.U1PrerequisiteMeasurement(ready=True)
    with pytest.raises(TypeError):
        module.SourceLockValidation(run_id=RUN_ID)
    with pytest.raises(TypeError):
        module.U1AuthoritySeal(run_id=RUN_ID)


def test_exact_locked_input_host_acl_unknown_is_recorded_without_raw_acl_injection(
    monkeypatch, prerequisite_context
):
    import ultra_runtime.source_integrity as module
    from ultra_runtime.schemas import validate_instance

    monkeypatch.delattr(module.os, "getuid", raising=False)
    monkeypatch.setattr(module, "_windows_current_user_owns", lambda _path: None)
    monkeypatch.setattr(module.os, "access", lambda _path, _mode: True)
    artifact, validation = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    validate_instance("ultra-source-lock.schema.json", artifact)
    assert artifact["acl_status"] == "unknown"
    assert validation.acl_status == "unknown"


def test_raw_acl_string_is_not_an_accepted_source_lock_authority(prerequisite_context):
    import ultra_runtime.source_integrity as module

    with pytest.raises(TypeError):
        module.build_source_lock(
            run_id=RUN_ID,
            version_binding=_binding(),
            generated_at=STAMP,
            prerequisite_measurement=prerequisite_context["measurement"],
            parent_event_sha256=PARENT_EVENT_SHA256,
            evidence_cutoff=STAMP,
            run_layout=prerequisite_context["run_layout"],
            inputs=_inputs(),
            acl_status="verified-current-user",
        )


@pytest.mark.parametrize(
    "forbidden_name,forbidden_value",
    (
        ("source_release_id", "caller-release"),
        ("source_manifest_sha256", "1" * 64),
        ("release_manifest_sha256", "2" * 64),
        ("compatibility_matrix_sha256", "3" * 64),
        ("knowledge_report_sha256", "4" * 64),
        ("skill_tree_sha256", "5" * 64),
    ),
)
def test_raw_caller_release_and_role_hash_kwargs_are_rejected(
    forbidden_name, forbidden_value, prerequisite_context
):
    import ultra_runtime.source_integrity as module

    arguments = {
        "run_id": RUN_ID,
        "version_binding": _binding(),
        "generated_at": STAMP,
        "prerequisite_measurement": prerequisite_context["measurement"],
        "parent_event_sha256": PARENT_EVENT_SHA256,
        "evidence_cutoff": STAMP,
        "run_layout": prerequisite_context["run_layout"],
        "inputs": _inputs(),
        forbidden_name: forbidden_value,
    }
    with pytest.raises(TypeError):
        module.build_source_lock(**arguments)


def test_repository_u1_measurement_verifies_current_release_authority():
    import ultra_runtime.source_integrity as module

    measurement = module.measure_u1_prerequisites(ROOT, manifest=_snapshot(module))
    assert measurement.ready
    assert measurement.missing == ()
    assert {"release_manifest", "skill_tree_hash"} <= set(measurement.verified)
    skill_tree_sha256 = measurement.skill_tree_sha256
    assert isinstance(skill_tree_sha256, str)
    assert len(skill_tree_sha256) == 64
    assert all(character in "0123456789abcdef" for character in skill_tree_sha256)


def test_production_measurement_rejects_release_override_and_test_measurement(
    prerequisite_context,
):
    import ultra_runtime.source_integrity as module

    release_path = prerequisite_context["release_path"]
    test_measurement = prerequisite_context["measurement"]
    with pytest.raises(module.SourceLockError, match="production|override"):
        module.measure_u1_prerequisites(
            ROOT,
            manifest=_snapshot(module),
            release_manifest_path=release_path,
            run_mode="production",
        )
    assert test_measurement.run_mode == "test"


def test_test_mode_release_fixture_binds_real_bytes_full_tree_and_all_roles(
    prerequisite_context,
):
    release_path = prerequisite_context["release_path"]
    document = prerequisite_context["document"]
    measurement = prerequisite_context["measurement"]
    authority_repo = prerequisite_context["repo"]
    expected_tree = {
        item["path"]: item["sha256"] for item in _release_artifacts(authority_repo)
    }
    assert measurement.ready
    assert measurement.source_release_id == document["release_id"]
    assert measurement.source_manifest_sha256 == SOURCE_MANIFEST_SHA256
    assert measurement.release_manifest_sha256 == hashlib.sha256(
        release_path.read_bytes()
    ).hexdigest()
    assert measurement.compatibility_matrix_sha256 == hashlib.sha256(
        (ROOT / "skills/crossframe-ultra/references/compatibility-matrix.json").read_bytes()
    ).hexdigest()
    assert measurement.skill_tree_sha256 == hashlib.sha256(
        _canonical(expected_tree)
    ).hexdigest()
    assert len(document["release_artifacts"]) == len(expected_tree)


def test_test_mode_release_fixture_rejects_incomplete_tree_coverage(tmp_path):
    import ultra_runtime.source_integrity as module

    release_path = tmp_path / "release-manifest.json"
    document = _write_release_manifest(ROOT, release_path)
    document["release_artifacts"].pop()
    document["content_sha256"] = _hash_without(document, "content_sha256")
    release_path.write_bytes(_canonical(document))
    measurement = module.measure_u1_prerequisites(
        ROOT,
        manifest=_snapshot(module),
        release_manifest_path=release_path,
        run_mode="test",
    )
    assert not measurement.ready
    assert "skill_tree_hash" in measurement.missing


@pytest.mark.parametrize(
    "mutation",
    ("release-manifest", "compatibility-matrix", "knowledge", "skill-file"),
)
def test_stale_prerequisite_measurement_rejects_each_mutated_host_role(
    tmp_path, mutation
):
    import ultra_runtime.source_integrity as module

    copied_repo = tmp_path / "repo"
    copied_skill = copied_repo / "skills/crossframe-ultra"
    copied_skill.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", copied_skill)
    copied_jsonio = copied_skill / "scripts/ultra_runtime/jsonio.py"
    copied_jsonio.write_bytes(copied_jsonio.read_bytes().replace(b"\r\n", b"\n"))
    release_path = tmp_path / "release-manifest.json"
    _write_release_manifest(copied_repo, release_path)
    copied_snapshot = module.load_source_manifest(
        copied_skill / "references/source-manifest.json",
        expected_sha256=SOURCE_MANIFEST_SHA256,
    )
    measurement = module.measure_u1_prerequisites(
        copied_repo,
        manifest=copied_snapshot,
        release_manifest_path=release_path,
        run_mode="test",
    )
    assert measurement.ready

    if mutation == "release-manifest":
        target = release_path
        document = json.loads(target.read_text(encoding="utf-8"))
        document["validated_at"] = "2026-08-02T00:00:01Z"
        document["content_sha256"] = _hash_without(document, "content_sha256")
        target.write_bytes(_canonical(document))
    elif mutation == "compatibility-matrix":
        target = copied_skill / "references/compatibility-matrix.json"
        document = json.loads(target.read_text(encoding="utf-8"))
        document["generated_at"] = "2026-08-02T08:00:01Z"
        document["content_sha256"] = _hash_without(document, "content_sha256")
        target.write_bytes(_canonical(document))
    elif mutation == "knowledge":
        target = copied_skill / "references/v8.2-route-map.json"
        document = json.loads(target.read_text(encoding="utf-8"))
        document["generated_at"] = "2026-08-02T00:00:01Z"
        if "content_sha256" in document:
            document["content_sha256"] = _hash_without(document, "content_sha256")
        target.write_bytes(_canonical(document))
    else:
        target = copied_skill / "scripts/ultra_runtime/article.py"
        target.write_bytes(target.read_bytes() + b"\nstale skill bytes\n")

    with pytest.raises(module.SourceLockError, match="stale|ready|authority|host"):
        module.verify_u1_prerequisites(measurement)


def test_manifest_replacement_between_stat_and_open_is_rejected(tmp_path, monkeypatch):
    import ultra_runtime.source_integrity as module

    target = tmp_path / "source-manifest.json"
    target.write_bytes(SOURCE_MANIFEST.read_bytes())
    replacement = tmp_path / "replacement.json"
    replacement.write_text("{}", encoding="utf-8")
    original_open = Path.open
    replaced = False

    def replace_then_open(path, *args, **kwargs):
        nonlocal replaced
        if path == target and not replaced:
            replaced = True
            replacement.replace(target)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", replace_then_open)
    with pytest.raises(
        module.SourceManifestError,
        match="changed.*(?:read|replaced)|invalid source manifest",
    ):
        module.load_source_manifest(target)


def test_committed_receipts_bind_real_body_reader_identity_mode_and_timestamp(
    explicit_read_context,
):
    module = explicit_read_context["module"]
    snapshot = explicit_read_context["snapshot"]
    receipts = explicit_read_context["receipts"]
    assert len(receipts) == 4753
    assert receipts[0].content_sha256 == snapshot.document["source_units"][0]["sha256"]
    assert receipts[0].execution_identity == module.execution_identity()
    assert receipts[0].reader_mode == "full-source"
    assert receipts[0].read_at == STAMP
    assert receipts[0].receipt_sha256 != receipts[0].content_sha256


def test_replacement_source_body_cannot_mint_a_receipt(tmp_path):
    import ultra_runtime.source_integrity as module

    copied_repo = tmp_path / "replacement-repo"
    copied_skill = copied_repo / "skills/crossframe-ultra"
    copied_skill.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", copied_skill)
    source = copied_skill / "references/v8.2-full-source/00-source-envelope.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nreplacement body\n", encoding="utf-8")
    with pytest.raises(module.SourceCoverageError, match="validation|source|manifest"):
        module.open_source_read_session(
            copied_repo,
            manifest=_snapshot(module),
            run_id=RUN_ID,
            version_binding=_binding(),
            source_lock_sha256="8" * 64,
            parent_event_sha256=PARENT_EVENT_SHA256,
            reader_mode="full-source",
            read_at=STAMP,
        )


def test_read_event_uses_manifest_content_external_receipt_and_separate_event_seal(read_batch):
    module, snapshot, _lock, validation, batch = read_batch
    from ultra_runtime.schemas import validate_instance

    first = batch.events[0]
    validate_instance("ultra-read-event.schema.json", first)
    assert first["content_sha256"] == snapshot.document["source_units"][0]["sha256"]
    assert first["receipt_sha256"] == batch.receipts[0].receipt_sha256
    assert first["receipt_sha256"] != first["content_sha256"]
    assert first["source_lock_sha256"] == validation.artifact_sha256
    assert first["read_event_sha256"] == _hash_without(first, "read_event_sha256")


def test_read_event_cannot_be_minted_without_external_receipt_authority(
    prerequisite_context,
):
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    _lock, validation = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    with pytest.raises(TypeError):
        module.make_read_event(
            run_id=RUN_ID,
            version_binding=_binding(),
            source_unit=snapshot.document["source_units"][0],
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            source_manifest_sha256=snapshot.sha256,
            source_lock_sha256=validation.artifact_sha256,
            parent_event_sha256=PARENT_EVENT_SHA256,
        )


def test_deterministic_unit_id_receipt_and_caller_selected_expected_map_are_rejected(read_batch):
    module, snapshot, _lock, validation, batch = read_batch
    forged = copy.deepcopy(batch.events)
    forged[0]["receipt_sha256"] = _sha(
        f"external-read-receipt:{forged[0]['source_unit_id']}"
    )
    forged[0]["read_event_sha256"] = _hash_without(
        forged[0], "read_event_sha256"
    )
    tampered_batch = copy.copy(batch)
    object.__setattr__(tampered_batch, "_events", tuple(forged))
    with pytest.raises(module.SourceCoverageError, match="receipt|capture|trusted"):
        _audit(module, snapshot, validation, tampered_batch)

    with pytest.raises(TypeError):
        module.audit_read_capture(
            batch.events,
            snapshot,
            receipts=batch.receipts,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_source_lock_sha256=validation.artifact_sha256,
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
            expected_receipt_sha256s={
                event["source_unit_id"]: event["receipt_sha256"]
                for event in batch.events
            },
        )


@pytest.mark.parametrize("extra_kind", ("duplicate", "invalid", "unknown"))
def test_read_audit_rejects_valid_receipt_set_plus_any_extra_receipt(read_batch, extra_kind):
    module, snapshot, _lock, validation, batch = read_batch
    receipts = list(batch.receipts)
    if extra_kind == "duplicate":
        receipts.append(receipts[0])
    elif extra_kind == "invalid":
        receipts.append(object())
    else:
        unknown = copy.copy(receipts[0])
        unit = unknown.source_unit
        unit["unit_id"] = "V82-P9999"
        unit["ordinal"] = 9999
        object.__setattr__(unknown, "_source_unit", unit)
        receipts.append(unknown)
    tampered_batch = copy.copy(batch)
    object.__setattr__(tampered_batch, "_receipts", tuple(receipts))
    with pytest.raises(module.SourceCoverageError, match="receipt|4,753|known"):
        _audit(module, snapshot, validation, tampered_batch)


def test_full_read_audit_authorizes_exact_unique_4753_unit_coverage(read_batch):
    module, snapshot, _lock, validation, batch = read_batch
    audit = _audit(module, snapshot, validation, batch)
    assert (audit.total, audit.paragraphs, audit.tables, audit.complete) == (
        4753,
        4631,
        122,
        True,
    )
    assert audit.authorizes_phase
    assert len(audit.artifact_sha256) == 64


@pytest.mark.parametrize(
    "mutation",
    (
        "missing",
        "duplicate",
        "unexpected",
        "cross-snapshot",
        "replay",
        "runtime-synthesized",
        "manifest-content-drift",
        "swapped-upstream-authority",
    ),
)
def test_read_audit_rejects_incomplete_replayed_or_resealed_false_authority(
    read_batch,
    mutation,
):
    module, snapshot, _lock, validation, batch = read_batch
    changed = list(batch.events)
    if mutation == "missing":
        changed.pop()
    elif mutation == "duplicate":
        changed.append(copy.deepcopy(changed[-1]))
    elif mutation == "replay":
        changed[-1] = copy.deepcopy(changed[0])
    elif mutation == "unexpected":
        changed = _replace_event(
            changed,
            0,
            source_unit_id="V82-P9999",
            source_ordinal=9999,
            content_sha256="8" * 64,
            receipt_sha256="7" * 64,
        )
    elif mutation == "cross-snapshot":
        changed = _replace_event(
            changed,
            0,
            promoted_semantic_snapshot_sha256="8" * 64,
        )
    elif mutation == "runtime-synthesized":
        changed = _replace_event(
            changed,
            0,
            receipt_sha256=_sha("runtime-self-attestation"),
        )
    elif mutation == "manifest-content-drift":
        changed = _replace_event(changed, 0, content_sha256="8" * 64)
    else:
        changed = _replace_event(
            changed,
            0,
            source_lock_sha256=PARENT_EVENT_SHA256,
            parent_event_sha256=validation.artifact_sha256,
        )
    tampered_batch = copy.copy(batch)
    object.__setattr__(tampered_batch, "_events", tuple(changed))
    with pytest.raises(module.SourceCoverageError):
        _audit(module, snapshot, validation, tampered_batch)


def test_u1_authority_seal_rejects_swapped_valid_source_lock_and_read_boundaries(
    read_batch, prerequisite_context
):
    module, snapshot, _lock, validation, batch = read_batch
    audit = _audit(module, snapshot, validation, batch)
    authority = module.validate_u1_authority(validation, audit)
    assert authority.authorizes_phase
    assert authority.source_lock_artifact_sha256 == validation.artifact_sha256
    assert authority.read_coverage_artifact_sha256 == audit.artifact_sha256
    assert authority.free_space_reserve_bytes == 1 << 30
    assert authority.free_space_status == "available"

    other_lock, other_validation = _source_lock(
        module,
        prerequisite_context["measurement"],
        prerequisite_context["run_layout"],
    )
    assert other_lock == _lock
    object.__setattr__(other_validation, "parent_event_sha256", "9" * 64)
    with pytest.raises(module.SourceLockError, match="boundary|parent|authority"):
        module.validate_u1_authority(other_validation, audit)


@pytest.fixture(scope="module")
def explicit_read_context(prerequisite_context):
    import ultra_runtime.source_integrity as module

    layout = _run_layout(
        prerequisite_context["fixture_root"] / "explicit-read-authority"
    )
    lock = module.build_source_lock(
        run_id=RUN_ID,
        version_binding=_binding(),
        generated_at=STAMP,
        prerequisite_measurement=prerequisite_context["measurement"],
        parent_event_sha256=PARENT_EVENT_SHA256,
        evidence_cutoff=STAMP,
        run_layout=layout,
        inputs=_inputs(),
    )
    lock_seal = module.validate_source_lock(
        lock,
        prerequisite_measurement=prerequisite_context["measurement"],
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_parent_event_sha256=PARENT_EVENT_SHA256,
        expected_evidence_cutoff=STAMP,
        expected_inputs=_inputs(),
        run_layout=layout,
    )
    snapshot = _snapshot(module)
    session = module.open_source_read_session(
        prerequisite_context["repo"],
        manifest=snapshot,
        run_id=RUN_ID,
        version_binding=_binding(),
        source_lock_sha256=lock_seal.artifact_sha256,
        parent_event_sha256=PARENT_EVENT_SHA256,
        reader_mode="full-source",
        read_at=STAMP,
    )
    assert not hasattr(session, "events")
    captures = tuple(
        module.capture_source_unit_read(session, unit["unit_id"])
        for unit in snapshot.document["source_units"]
    )
    records = tuple(capture[0] for capture in captures)
    receipts = tuple(capture[1] for capture in captures)
    assert len(records) == len(receipts) == 4753
    events = tuple(
        module.make_read_event(
            run_id=RUN_ID,
            version_binding=_binding(),
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            source_manifest_sha256=snapshot.sha256,
            source_lock_sha256=lock_seal.artifact_sha256,
            parent_event_sha256=PARENT_EVENT_SHA256,
            receipt=receipt,
        )
        for receipt in receipts
    )

    diagnostic = module.capture_authority_read_diagnostic(
        prerequisite_context["repo"],
        run_id=RUN_ID,
        version_binding=_binding(),
        manifest=snapshot,
        source_lock_sha256=lock_seal.artifact_sha256,
        parent_event_sha256=PARENT_EVENT_SHA256,
        reader_mode="full-source",
        read_at=STAMP,
    )
    return {
        "module": module,
        "snapshot": snapshot,
        "lock": lock,
        "lock_seal": lock_seal,
        "session": session,
        "records": records,
        "receipts": receipts,
        "events": events,
        "diagnostic": diagnostic,
    }


def test_only_explicit_one_unit_reads_can_authorize_external_read_events(
    explicit_read_context,
    monkeypatch,
):
    module = explicit_read_context["module"]
    snapshot = explicit_read_context["snapshot"]
    lock_seal = explicit_read_context["lock_seal"]
    session = explicit_read_context["session"]
    records = explicit_read_context["records"]
    receipts = explicit_read_context["receipts"]
    events = explicit_read_context["events"]
    diagnostic = explicit_read_context["diagnostic"]
    assert not hasattr(session, "events")
    assert len(records) == len(receipts) == 4753

    monkeypatch.setattr(
        module,
        "_capture_committed_read_receipts",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("bulk diagnostic must not participate in authority audit")
        ),
    )
    audit = module.audit_read_capture(
        events,
        snapshot,
        receipts=receipts,
        promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_source_lock_sha256=lock_seal.artifact_sha256,
        expected_parent_event_sha256=PARENT_EVENT_SHA256,
    )
    assert audit.complete and audit.authorizes_phase
    assert module.validate_u1_authority(lock_seal, audit).authorizes_phase

    with pytest.raises(module.SourceCoverageError, match="one-unit|receipt|diagnostic"):
        module.audit_read_capture(
            diagnostic.events,
            snapshot,
            receipts=diagnostic.receipts,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_source_lock_sha256=lock_seal.artifact_sha256,
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
        )


@pytest.mark.parametrize(
    "mutation",
    ("run", "parent", "source-lock", "receipt"),
)
def test_external_read_audit_rejects_swapped_one_unit_authority(
    explicit_read_context,
    mutation,
):
    module = explicit_read_context["module"]
    snapshot = explicit_read_context["snapshot"]
    lock_seal = explicit_read_context["lock_seal"]
    receipts = explicit_read_context["receipts"]
    events = copy.deepcopy(list(explicit_read_context["events"]))
    if mutation == "receipt":
        events[0]["receipt_sha256"] = receipts[1].receipt_sha256
    elif mutation == "run":
        events[0]["run_id"] = "20260802T000002Z-6b8fae42c033"
    elif mutation == "parent":
        events[0]["parent_event_sha256"] = "8" * 64
    else:
        events[0]["source_lock_sha256"] = "9" * 64
    events[0]["read_event_sha256"] = _hash_without(
        events[0], "read_event_sha256"
    )
    with pytest.raises(module.SourceCoverageError):
        module.audit_read_capture(
            events,
            snapshot,
            receipts=receipts,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_source_lock_sha256=lock_seal.artifact_sha256,
            expected_parent_event_sha256=PARENT_EVENT_SHA256,
        )
