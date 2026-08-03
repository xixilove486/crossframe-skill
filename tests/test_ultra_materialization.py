from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
MATERIALIZATION_PATH = RUNTIME_DIR / "materialization.py"

EXPECTED_AUTHORING_SLOTS = (
    "U01-read-events.jsonl",
    "U02-retrieval-ledger.json",
    "U03-evidence-ledger.json",
    "U04-world-volume.json",
    "U05-transformation-ledger.json",
    "U05-concept-disposition.json",
    "U06-claim-mechanism-graph.json",
    "U07-recursive-states/<node-id>.json",
    "U07-recursive-lineage.json",
    "U08-order-evaluation.json",
    "U08-red-team-report.json",
    "U09-verdict.json",
    "U09-action-ranking.json",
    "U09-forecast-ledger.json",
    "U10-framework-gap-ledger.json",
    "U10-output-plan.json",
    "U11-semantic-coverage.json",
    "article/packets/<packet-id>.md",
    "U11-article-review.json",
    "完整推演档案.md",
)


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def runtime():
    if not MATERIALIZATION_PATH.is_file():
        pytest.skip(f"Task 13 runtime is not implemented: {MATERIALIZATION_PATH}")
    return _module("materialization"), _module("paths"), _module("jsonio")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(
        paths.RunMode.TEST,
        "20260802T030405Z-000000000013",
        policy,
    )


def test_task13_materialization_module_exists_for_red_gate() -> None:
    assert MATERIALIZATION_PATH.is_file(), MATERIALIZATION_PATH


def test_prepare_returns_only_the_frozen_model_owned_slots(runtime, tmp_path: Path) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)

    prepared = materialization.prepare_authoring(layout)

    assert tuple(prepared.relative_slots) == EXPECTED_AUTHORING_SLOTS
    assert prepared.authoring_dir == layout.authoring_dir
    assert prepared.control_path == layout.artifacts_dir / "ultra-materialization-control.json"
    assert prepared.control_path.is_file()
    control = jsonio.load_json_object(prepared.control_path)
    assert control == materialization.build_materialization_control(layout)
    assert control["run_id"] == layout.run_dir.name
    assert control["authoring_slots"] == list(EXPECTED_AUTHORING_SLOTS)
    assert all(
        path == layout.authoring_dir or layout.authoring_dir in path.parents
        for path in prepared.slot_paths
    )
    assert not any(path.is_file() for path in prepared.slot_paths)
    assert not (layout.authoring_dir / "article.partial.md").exists()
    assert not (layout.authoring_dir / "U09-forecast-resolution.json").exists()
    assert list(layout.delivery_dir.glob("*")) == []


def test_discovery_freezes_recursive_and_cross_phase_dependency_order(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    authored = (
        "U09-forecast-ledger.json",
        "U08-red-team-report.json",
        "U09-action-ranking.json",
        "U07-recursive-states/node-z.json",
        "U09-verdict.json",
        "U08-order-evaluation.json",
        "U07-recursive-lineage.json",
        "U07-recursive-states/node-a.json",
    )
    for relative in authored:
        target = layout.authoring_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"{}\n")

    discovered = materialization.discover_authoring_inputs(layout)
    names = tuple(path.relative_to(layout.authoring_dir).as_posix() for path in discovered)

    assert names.index("U07-recursive-states/node-a.json") < names.index(
        "U07-recursive-lineage.json"
    )
    assert names.index("U07-recursive-states/node-z.json") < names.index(
        "U07-recursive-lineage.json"
    )
    assert names.index("U07-recursive-states/node-a.json") < names.index(
        "U07-recursive-states/node-z.json"
    )
    assert names.index("U08-order-evaluation.json") < names.index(
        "U08-red-team-report.json"
    )
    assert names.index("U09-verdict.json") < names.index(
        "U09-action-ranking.json"
    )
    assert names.index("U09-verdict.json") < names.index(
        "U09-forecast-ledger.json"
    )


def test_runtime_overwrites_model_owned_envelope_and_validates_closed_schema(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    source = layout.authoring_dir / "U04-world-volume.json"
    document = json.loads(
        (REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json").read_text(
            "utf-8"
        )
    )
    document.update(
        {
            "schema_id": "model.forged.schema",
            "run_id": "model-controlled-run",
            "version_binding": {"runtime_version": "999.0.0"},
            "generated_at": "1999-01-01T00:00:00Z",
            "phase_id": "U12",
            "content_sha256": "f" * 64,
        }
    )
    source.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    sealed = materialization.seal_authoring_artifact(
        layout,
        source,
        generated_at=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
    )

    assert sealed["schema_id"] == "crossframe.ultra.v82.world-volume"
    assert sealed["run_id"] == layout.run_dir.name
    assert sealed["phase_id"] == "U4"
    assert sealed["generated_at"] == "2026-08-02T03:04:06Z"
    assert sealed["version_binding"] == _module("constants").current_version_binding()
    assert sealed["content_sha256"] == _module(
        "schemas"
    ).compute_artifact_content_sha256(sealed)
    assert jsonio.load_json_object(source) == sealed

    document = dict(sealed)
    document["model_runtime_field"] = "must not cross the boundary"
    source.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(Exception, match="field|schema|unevaluated|Additional"):
        materialization.seal_authoring_artifact(
            layout,
            source,
            generated_at=datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
        )


def test_runtime_rebinds_parent_run_identity_and_nested_output_plan_hashes(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    generated_at = datetime(2026, 8, 2, 3, 4, 8, tzinfo=timezone.utc)

    recursive_source = (
        layout.authoring_dir / "U07-recursive-states/NODE-MAIN-ORDER-1.json"
    )
    recursive_source.write_bytes(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/recursive-state-valid.json"
        ).read_bytes()
    )
    recursive = materialization.seal_authoring_artifact(
        layout,
        recursive_source,
        generated_at=generated_at,
    )
    assert recursive["parent_run_id"] == layout.run_dir.name

    authority = json.loads(
        (
            REPO_ROOT
            / "tests/fixtures/ultra-runtime/article-packets/frozen-upstream-authority.json"
        ).read_text("utf-8")
    )
    required_paths = (
        "artifacts/U09-U10-verdict/U09-verdict.json",
        "artifacts/U09-U10-verdict/U09-action-ranking.json",
    )
    old_hashes = tuple(record["sha256"] for record in authority["required_artifacts"])
    new_hashes = []
    for ordinal, relative in enumerate(required_paths, start=1):
        target = layout.run_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"frozen artifact {ordinal}\n".encode("utf-8"))
        new_hashes.append(hashlib.sha256(target.read_bytes()).hexdigest())
    required_artifacts = [
        {
            "path": relative,
            "sha256": old_hash,
            "media_type": "application/json",
        }
        for relative, old_hash in zip(required_paths, old_hashes, strict=True)
    ]
    article = _module("article")
    plan = article.build_output_plan_artifact(
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at="2026-08-02T03:04:08Z",
        u9_parent_event_sha256="9" * 64,
        article_path="work/authoring/article.partial.md",
        sections=authority["sections"],
        appendices=authority["appendices"],
        required_artifacts=required_artifacts,
        semantic_universe=authority["semantic_universe"],
        blind_recovery_expectations=authority["blind_recovery_expectations"],
    )
    plan_source = layout.authoring_dir / "U10-output-plan.json"
    plan_source.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    sealed = materialization.seal_authoring_artifact(
        layout,
        plan_source,
        generated_at=generated_at,
    )

    assert [record["sha256"] for record in sealed["required_artifacts"]] == new_hashes
    assert {
        digest
        for entry in (*sealed["sections"], *sealed["appendices"])
        for digest in entry["dependency_hashes"]
    } == set(new_hashes)
    assert {
        unit["authority_artifact_sha256"]
        for unit in sealed["semantic_universe"]
    } == set(new_hashes)
    assert sealed["semantic_universe_sha256"] == _module("jsonio").sha256_bytes(
        _module("jsonio").canonical_json_bytes(sealed["semantic_universe"])
    )


def test_output_plan_dependencies_must_resolve_inside_the_artifacts_namespace(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    outside = layout.input_dir / "request.bin"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_bytes(b"request\n")
    authority = json.loads(
        (
            REPO_ROOT
            / "tests/fixtures/ultra-runtime/article-packets/frozen-upstream-authority.json"
        ).read_text("utf-8")
    )
    authority["required_artifacts"][0]["path"] = "input/request.bin"
    plan_source = layout.authoring_dir / "U10-output-plan.json"
    plan_source.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="artifacts"):
        materialization.seal_authoring_artifact(
            layout,
            plan_source,
            generated_at=datetime(2026, 8, 2, 3, 4, 9, tzinfo=timezone.utc),
        )


def test_materialization_rejects_a_forged_layout_outside_the_selected_root(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    forged = paths.RunLayout(
        root=layout.root,
        root_staging_dir=layout.root_staging_dir,
        run_dir=tmp_path / "escape",
        input_dir=layout.input_dir,
        authoring_dir=layout.authoring_dir,
        artifacts_dir=layout.artifacts_dir,
        delivery_dir=layout.delivery_dir,
        validation_dir=layout.validation_dir,
        validation_current_dir=layout.validation_current_dir,
        validation_attempts_dir=layout.validation_attempts_dir,
        recovery_dir=layout.recovery_dir,
        logs_dir=layout.logs_dir,
    )

    with pytest.raises((TypeError, ValueError), match="outside|layout|root|run"):
        materialization.prepare_authoring(forged)
