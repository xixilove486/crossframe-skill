from __future__ import annotations

import importlib
import hashlib
import json
import subprocess
import sys
from collections import UserDict
from pathlib import Path
from types import SimpleNamespace
from types import MappingProxyType
from typing import Any

from tests.pytest_import_guard import pytest
from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = ROOT / "skills/crossframe-ultra"
RUNTIME_SCRIPTS = ULTRA_ROOT / "scripts"
MATRIX_PATH = ULTRA_ROOT / "references/compatibility-matrix.json"

RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
TREE_SHA256 = "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
RELEASE_EPOCH = "2026-08-06T08:53:37Z"
BASE_COMMIT = "f0e808d3bef871895b166abbecae73ca3c9afa8f"
LEGACY_V1_SCHEMA_NAMES = (
    "ultra-article-review.schema.json",
    "ultra-claim-mechanism-graph.schema.json",
    "ultra-common.schema.json",
    "ultra-compatibility-matrix.schema.json",
    "ultra-evidence-ledger.schema.json",
    "ultra-phase-event.schema.json",
    "ultra-read-event.schema.json",
    "ultra-recovery-checkpoint.schema.json",
    "ultra-release-manifest.schema.json",
    "ultra-run-contract.schema.json",
    "ultra-run-status.schema.json",
    "ultra-semantic-coverage.schema.json",
    "ultra-validator-report.schema.json",
    "ultra-verdict.schema.json",
)


def canonical_content_sha256(value: dict[str, Any]) -> str:
    import hashlib

    payload = json.loads(json.dumps(value))
    payload.pop("content_sha256", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256((canonical + "\n").encode("utf-8")).hexdigest()


def clear_legacy_cache(function: object) -> None:
    cache_clear = getattr(function, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()


def load_runtime():
    scripts = str(RUNTIME_SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module("ultra_runtime")


def binding(**changes: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": RAW_SHA256,
        "framework_semantic_sha256": SEMANTIC_SHA256,
        "runtime_version": "1.1.0",
        "artifact_schema_version": 2,
        "compiler_version": "1.0.0",
        "validator_version": "1.1.0",
        "article_contract_version": "1.1.0",
        "source_tree_sha256": TREE_SHA256,
    }
    value.update(changes)
    return value


def v1_binding(**changes: Any) -> dict[str, Any]:
    value = binding(
        runtime_version="1.0.0",
        artifact_schema_version=1,
        validator_version="1.0.0",
        article_contract_version="1.0.0",
    )
    value.update(changes)
    return value


def tree_hash(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def mutate_rule_policy(matrix: dict[str, Any], case: str) -> None:
    rules = matrix["rules"]
    by_kind = {rule["match_kind"]: rule for rule in rules}
    if case == "duplicate-rule-id":
        rules[1]["rule_id"] = rules[0]["rule_id"]
    elif case == "duplicate-priority":
        rules[1]["priority"] = rules[0]["priority"]
    elif case == "multiple-fallbacks":
        rules[0].update(
            match_kind="fallback",
            allowed_mismatch_fields=[],
            result="reject",
        )
    elif case == "fallback-not-last":
        rules.insert(0, rules.pop())
    elif case == "fallback-resume":
        by_kind["fallback"]["result"] = "resume"
    elif case == "exact-read-only":
        by_kind["exact"]["result"] = "read-only"
    elif case == "migration-resume":
        by_kind["known-migration"]["result"] = "resume"
    elif case == "read-only-framework-field":
        by_kind["mismatch-subset"]["allowed_mismatch_fields"].append(
            "framework_revision"
        )
    elif case == "mismatch-subset-resume":
        by_kind["mismatch-subset"]["result"] = "resume"
    else:
        raise AssertionError(f"unknown matrix mutation: {case}")


INVALID_MATRIX_POLICY_CASES = (
    "duplicate-rule-id",
    "duplicate-priority",
    "multiple-fallbacks",
    "fallback-not-last",
    "fallback-resume",
    "exact-read-only",
    "migration-resume",
    "read-only-framework-field",
    "mismatch-subset-resume",
)

INVALID_MATRIX_SCHEMA_CASES = (
    "fallback-resume",
    "exact-read-only",
    "migration-resume",
    "read-only-framework-field",
    "mismatch-subset-resume",
)


def test_frozen_constants_are_exact() -> None:
    runtime = load_runtime()
    constants = importlib.import_module("ultra_runtime.constants")
    assert runtime.FRAMEWORK_VERSION == "8.2"
    assert runtime.FRAMEWORK_REVISION == "v8.2-r1"
    assert runtime.FRAMEWORK_RAW_SHA256 == RAW_SHA256
    assert runtime.FRAMEWORK_SEMANTIC_SHA256 == SEMANTIC_SHA256
    assert runtime.RUNTIME_VERSION == "1.1.0"
    assert runtime.ARTIFACT_SCHEMA_VERSION == 2
    assert runtime.COMPILER_VERSION == "1.0.0"
    assert runtime.VALIDATOR_VERSION == "1.1.0"
    assert runtime.ARTICLE_CONTRACT_VERSION == "1.1.0"
    assert constants.SOURCE_TREE_SHA256 == TREE_SHA256
    assert constants.current_version_binding() == binding()
    assert runtime.PHASES == tuple(f"U{number}" for number in range(13))
    assert runtime.RUN_STATUSES == (
        "created",
        "running",
        "interrupted",
        "blocked",
        "needs_attention",
        "failed",
        "cancelled",
        "complete",
    )


def test_current_runtime_binding_is_v2_without_framework_drift() -> None:
    runtime = load_runtime()
    current = importlib.import_module("ultra_runtime.constants").current_version_binding()

    assert current == binding()
    assert runtime.RUNTIME_VERSION == "1.1.0"
    assert runtime.ARTIFACT_SCHEMA_VERSION == 2
    assert runtime.VALIDATOR_VERSION == "1.1.0"
    assert runtime.ARTICLE_CONTRACT_VERSION == "1.1.0"
    assert runtime.COMPILER_VERSION == "1.0.0"
    assert runtime.FRAMEWORK_RAW_SHA256 == RAW_SHA256
    assert runtime.FRAMEWORK_SEMANTIC_SHA256 == SEMANTIC_SHA256


def test_completed_v1_is_read_only_and_in_progress_v1_requires_child() -> None:
    runtime = load_runtime()

    assert (
        runtime.resolve_compatibility(
            v1_binding(), binding(), run_status="complete"
        )
        == "read-only"
    )
    assert (
        runtime.resolve_compatibility(
            v1_binding(), binding(), run_status="running"
        )
        == "fork-required"
    )


def test_legacy_v1_schema_snapshots_are_exact_start_commit_bytes() -> None:
    runtime = load_runtime()
    legacy_root = runtime.legacy_schema_root()

    assert tuple(path.name for path in sorted(legacy_root.glob("*.schema.json"))) == (
        LEGACY_V1_SCHEMA_NAMES
    )
    for schema_name in LEGACY_V1_SCHEMA_NAMES:
        relative = f"skills/crossframe-ultra/schemas/{schema_name}"
        expected = subprocess.run(
            ["git", "show", f"{BASE_COMMIT}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert (legacy_root / schema_name).read_bytes() == expected


def test_legacy_v1_run_status_rejects_v2_only_fork_authority() -> None:
    runtime = load_runtime()
    status = {
        "schema_id": "crossframe.ultra.v82.run-status",
        "schema_version": 1,
        "run_id": "ultra-run-20260802-0001",
        "version_binding": v1_binding(),
        "generated_at": "2026-08-02T08:00:00Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "fork_authority_sha256": "a" * 64,
        "status": "complete",
        "previous_status": "running",
        "current_phase": "U12",
        "last_complete_phase": "U12",
        "reason": None,
        "tools_allowed": False,
        "validation_passed": True,
        "updated_at": "2026-08-02T08:00:00Z",
        "created_at": "2026-08-02T07:00:00Z",
        "revision": 13,
    }

    with pytest.raises(ValidationError):
        runtime.validate_legacy_v1_instance(
            "ultra-run-status.schema.json",
            status,
        )


def test_v1_read_only_validation_uses_legacy_registry_without_writing(
    tmp_path: Path,
) -> None:
    runtime = load_runtime()
    run_dir = tmp_path / "legacy-complete-run"
    run_id = "ultra-run-20260802-0001"
    status = {
        "schema_id": "crossframe.ultra.v82.run-status",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": v1_binding(),
        "generated_at": "2026-08-02T08:00:00Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "status": "complete",
        "previous_status": "running",
        "current_phase": "U12",
        "last_complete_phase": "U12",
        "reason": None,
        "tools_allowed": False,
        "validation_passed": True,
        "updated_at": "2026-08-02T08:00:00Z",
        "created_at": "2026-08-02T07:00:00Z",
        "revision": 13,
    }
    status["content_sha256"] = canonical_content_sha256(status)
    verdict = json.loads(
        (ROOT / "tests/fixtures/ultra-runtime/verdict-valid.json").read_text(
            encoding="utf-8"
        )
    )
    verdict.update(
        run_id=run_id,
        version_binding=v1_binding(),
        generated_at="2026-08-02T08:00:00Z",
    )
    verdict["content_sha256"] = canonical_content_sha256(verdict)
    run_dir.mkdir()
    (run_dir / "run-status.json").write_text(
        json.dumps(status, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    artifact_path = run_dir / "artifacts/U09-U10-verdict/U09-verdict.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(
        json.dumps(verdict, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    read_event = {
        "schema_id": "crossframe.ultra.v82.read-event",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": v1_binding(),
        "generated_at": "2026-08-02T07:30:00Z",
        "content_sha256": "a" * 64,
        "phase_id": "U1",
        "source_unit_id": "V82-P0001",
        "source_kind": "paragraph",
        "source_ordinal": 1,
        "source_manifest_sha256": "b" * 64,
        "promoted_semantic_snapshot_sha256": "c" * 64,
        "source_lock_sha256": "d" * 64,
        "parent_event_sha256": "e" * 64,
        "receipt_sha256": "f" * 64,
        "reader_mode": "full-source",
        "execution_identity": {
            "kind": "host-process",
            "process_id": 1234,
            "executable": "/usr/bin/python3",
            "user": "fixture-user",
        },
        "read_at": "2026-08-02T07:30:00Z",
        "read_event_sha256": "0" * 64,
    }
    read_event_payload = dict(read_event)
    read_event_payload.pop("read_event_sha256")
    read_event["read_event_sha256"] = hashlib.sha256(
        (
            json.dumps(
                read_event_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    read_events_path = run_dir / "artifacts/U00-U03-evidence/ultra-read-events.jsonl"
    read_events_path.parent.mkdir(parents=True, exist_ok=True)
    read_events_path.write_text(
        json.dumps(
            read_event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    before = tree_hash(run_dir)

    report = runtime.validate_legacy_run_read_only(
        SimpleNamespace(run_dir=run_dir)
    )

    assert report["overall_status"] == "pass"
    assert report["compatibility"] == "read-only"
    assert report["validated_artifact_count"] == 3
    assert tree_hash(run_dir) == before


def test_v1_release_manifest_remains_valid_under_the_legacy_registry() -> None:
    runtime = load_runtime()
    legacy_release = json.loads(
        subprocess.run(
            [
                "git",
                "show",
                f"{BASE_COMMIT}:skills/crossframe-ultra/references/release-manifest.json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )

    runtime.validate_legacy_v1_instance(
        "ultra-release-manifest.schema.json",
        legacy_release,
    )


def test_compatibility_matrix_is_schema_valid_and_mechanically_loaded() -> None:
    runtime = load_runtime()
    matrix = runtime.load_compatibility_matrix()
    assert matrix == json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    runtime.validate_instance("ultra-compatibility-matrix.schema.json", matrix)
    assert matrix["allowed_results"] == [
        "resume",
        "read-only",
        "fork-required",
        "reject",
    ]
    assert matrix["version_binding"] == binding()
    assert matrix["generated_at"] == RELEASE_EPOCH
    assert matrix["content_sha256"] == canonical_content_sha256(matrix)
    assert len(set(matrix["content_sha256"])) > 1
    assert [rule["priority"] for rule in matrix["rules"]] == sorted(
        rule["priority"] for rule in matrix["rules"]
    )
    assert {rule["result"] for rule in matrix["rules"]} == set(
        matrix["allowed_results"]
    )
    forbidden = {"downgrade", "ProMax", "Max", "migrate-in-place"}
    assert forbidden.isdisjoint(
        {
            str(value)
            for rule in matrix["rules"]
            for value in rule.values()
            if not isinstance(value, list)
        }
    )


@pytest.mark.parametrize("case", INVALID_MATRIX_SCHEMA_CASES)
def test_matrix_schema_rejects_unsafe_rule_contracts(case: str) -> None:
    runtime = load_runtime()
    matrix = runtime.load_compatibility_matrix()
    mutate_rule_policy(matrix, case)
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-compatibility-matrix.schema.json", matrix)


@pytest.mark.parametrize("case", INVALID_MATRIX_POLICY_CASES)
def test_matrix_loader_rejects_unsafe_rule_policy(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = load_runtime()
    schemas_module = importlib.import_module("ultra_runtime.schemas")
    matrix = runtime.load_compatibility_matrix()
    mutate_rule_policy(matrix, case)
    matrix_path = tmp_path / "compatibility-matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    monkeypatch.setattr(
        schemas_module,
        "_compatibility_matrix_path",
        lambda: matrix_path,
    )
    clear_legacy_cache(schemas_module._load_compatibility_matrix_cached)
    try:
        with pytest.raises(runtime.UltraCompatibilityError):
            runtime.load_compatibility_matrix()
    finally:
        clear_legacy_cache(schemas_module._load_compatibility_matrix_cached)


def test_compatibility_is_mechanical() -> None:
    runtime = load_runtime()
    current = binding()
    cases = (
        (binding(), "resume"),
        (binding(runtime_version="0.9.0"), "read-only"),
        (binding(validator_version="1.0.0"), "read-only"),
        (v1_binding(), "fork-required"),
        (binding(framework_revision="v8.2-r0"), "reject"),
        (binding(artifact_schema_version=0), "reject"),
        (binding(artifact_schema_version=999), "reject"),
    )
    for recorded, expected in cases:
        assert runtime.resolve_compatibility(recorded, current) == expected
        assert (
            runtime.resolve_compatibility(
                {"recorded": recorded, "current": current}
            )
            == expected
        )


def test_well_formed_placeholder_tree_is_not_current_authority() -> None:
    runtime = load_runtime()
    placeholder = binding(source_tree_sha256="c" * 64)
    assert runtime.resolve_compatibility(placeholder, placeholder) == "reject"


def test_matrix_single_field_drift_is_rejected_after_cache_fill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = load_runtime()
    schemas_module = importlib.import_module("ultra_runtime.schemas")
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    matrix_path = tmp_path / "compatibility-matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    monkeypatch.setattr(
        schemas_module,
        "_compatibility_matrix_path",
        lambda: matrix_path,
    )
    clear_legacy_cache(schemas_module._load_compatibility_matrix_cached)

    runtime.load_compatibility_matrix()
    matrix["version_binding"]["source_tree_sha256"] = "e" * 64
    matrix["content_sha256"] = canonical_content_sha256(matrix)
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    with pytest.raises(runtime.UltraCompatibilityError):
        runtime.load_compatibility_matrix()


def test_constants_single_field_drift_invalidates_matrix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = load_runtime()
    constants = importlib.import_module("ultra_runtime.constants")
    schemas_module = importlib.import_module("ultra_runtime.schemas")
    clear_legacy_cache(schemas_module._load_compatibility_matrix_cached)
    monkeypatch.setattr(constants, "RUNTIME_VERSION", "1.1.1")

    with pytest.raises(runtime.UltraCompatibilityError):
        runtime.load_compatibility_matrix()


def test_reject_priority_precedes_readable_or_migration_rules() -> None:
    runtime = load_runtime()
    current = binding()
    cases = (
        binding(runtime_version="0.9.0", framework_version="9.0"),
        binding(runtime_version="0.9.0", framework_raw_sha256="a" * 64),
        binding(framework_revision="v8.2-r99"),
        binding(artifact_schema_version=999, validator_version="0.9.0"),
        binding(artifact_schema_version=0, framework_raw_sha256="a" * 64),
        binding(artifact_schema_version=0, source_tree_sha256="b" * 64),
        binding(source_tree_sha256="b" * 64),
        binding(compiler_version="9.0.0"),
    )
    for recorded in cases:
        assert runtime.resolve_compatibility(recorded, current) == "reject"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("framework_raw_sha256", "a" * 64),
        ("framework_semantic_sha256", "b" * 64),
        ("source_tree_sha256", "b" * 64),
    ),
    ids=("unknown-raw", "unknown-semantic", "unknown-tree"),
)
def test_known_framework_migration_requires_exact_old_hashes_and_tree(
    field: str,
    value: Any,
) -> None:
    runtime = load_runtime()
    current = binding()
    recorded = binding(framework_revision="v8.2-r0", **{field: value})
    assert runtime.resolve_compatibility(recorded, current) == "reject"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("framework_version", "9.0"),
        ("artifact_schema_version", 999),
        ("framework_raw_sha256", "a" * 64),
        ("framework_semantic_sha256", "b" * 64),
        ("source_tree_sha256", "d" * 64),
    ),
    ids=(
        "unknown-framework",
        "unknown-schema",
        "unknown-raw",
        "unknown-semantic",
        "unknown-tree",
    ),
)
def test_matching_unknown_current_bindings_are_never_resumable(
    field: str,
    value: Any,
) -> None:
    runtime = load_runtime()
    unsupported = binding(**{field: value})
    assert runtime.resolve_compatibility(unsupported, unsupported) == "reject"


def test_known_migrations_bind_complete_exact_from_and_to_records() -> None:
    runtime = load_runtime()
    matrix = runtime.load_compatibility_matrix()
    expected_fields = set(binding())
    for migration_kind in ("framework_revisions", "artifact_schemas"):
        for migration in matrix["known_migrations"][migration_kind]:
            assert set(migration) == {"from_binding", "to_binding", "result"}
            assert set(migration["from_binding"]) == expected_fields
            assert set(migration["to_binding"]) == expected_fields


def test_corrupt_missing_or_extra_binding_is_rejected() -> None:
    runtime = load_runtime()
    current = binding()
    corrupt_cases = []

    missing = binding()
    del missing["validator_version"]
    corrupt_cases.append(missing)

    extra = binding(extra=True)
    corrupt_cases.append(extra)

    bad_hash = binding(framework_raw_sha256="xyz")
    corrupt_cases.append(bad_hash)

    bad_version = binding(runtime_version="latest")
    corrupt_cases.append(bad_version)

    for recorded in corrupt_cases:
        assert runtime.resolve_compatibility(recorded, current) == "reject"


def test_compatibility_rejects_non_mapping_and_malformed_single_case() -> None:
    runtime = load_runtime()
    assert runtime.resolve_compatibility({"recorded": binding()}) == "reject"
    assert runtime.resolve_compatibility({"current": binding()}) == "reject"
    assert runtime.resolve_compatibility({"recorded": binding(), "current": binding(), "extra": 1}) == "reject"
    assert runtime.resolve_compatibility({"recorded": "bad", "current": binding()}) == "reject"


def test_compatibility_snapshots_general_mapping_inputs() -> None:
    runtime = load_runtime()
    recorded = UserDict(binding(runtime_version="0.9.0"))
    current = MappingProxyType(binding())
    assert runtime.resolve_compatibility(recorded, current) == "read-only"

    case = UserDict(
        {
            "recorded": MappingProxyType(binding()),
            "current": UserDict(binding()),
        }
    )
    assert runtime.resolve_compatibility(case) == "resume"


@pytest.mark.parametrize(
    "invalid_semver",
    (
        "1.0.0-..",
        "1.0.0-01",
        "1.0.0-a..b",
        "1.0.0-alpha.",
        "1.0.0+build..1",
    ),
)
@pytest.mark.parametrize("field", ("runtime_version", "validator_version"))
def test_malformed_semver_is_rejected_not_read_only(
    field: str,
    invalid_semver: str,
) -> None:
    runtime = load_runtime()
    assert (
        runtime.resolve_compatibility(
            binding(**{field: invalid_semver}),
            binding(),
        )
        == "reject"
    )


@pytest.mark.parametrize(
    "valid_semver",
    (
        "0.0.0",
        "1.0.0-0",
        "1.0.0-alpha.1+build.5",
        "1.0.0+build.5",
    ),
)
def test_complete_semver_2_versions_are_readable(valid_semver: str) -> None:
    runtime = load_runtime()
    assert (
        runtime.resolve_compatibility(
            binding(runtime_version=valid_semver),
            binding(),
        )
        == "read-only"
    )


def test_source_revision_promotion_records_alternate_raw_without_new_revision() -> None:
    runtime = load_runtime()
    result = runtime.resolve_source_revision_promotion(
        current_revision="v8.2-r1",
        current_raw_sha256=RAW_SHA256,
        current_semantic_sha256=SEMANTIC_SHA256,
        candidate_raw_sha256="a" * 64,
        candidate_semantic_sha256=SEMANTIC_SHA256,
    )
    assert result == {
        "action": "record-alternate-raw-package",
        "current_revision": "v8.2-r1",
        "target_revision": "v8.2-r1",
        "alternate_raw_sha256": "a" * 64,
        "build_beside_current": False,
        "requires_validation": False,
        "promote_stable_after_validation": False,
        "overwrite_existing_release": False,
    }


def test_source_semantic_change_requires_beside_build_validation_and_promotion() -> None:
    runtime = load_runtime()
    result = runtime.resolve_source_revision_promotion(
        current_revision="v8.2-r1",
        current_raw_sha256=RAW_SHA256,
        current_semantic_sha256=SEMANTIC_SHA256,
        candidate_raw_sha256="a" * 64,
        candidate_semantic_sha256="b" * 64,
    )
    assert result == {
        "action": "build-new-immutable-revision",
        "current_revision": "v8.2-r1",
        "target_revision": "v8.2-r2",
        "alternate_raw_sha256": None,
        "build_beside_current": True,
        "requires_validation": True,
        "promote_stable_after_validation": True,
        "overwrite_existing_release": False,
    }


def test_source_revision_promotion_rejects_corrupt_hashes_and_revision() -> None:
    runtime = load_runtime()
    with pytest.raises(runtime.UltraCompatibilityError):
        runtime.resolve_source_revision_promotion(
            current_revision="latest",
            current_raw_sha256=RAW_SHA256,
            current_semantic_sha256=SEMANTIC_SHA256,
            candidate_raw_sha256="a" * 64,
            candidate_semantic_sha256="b" * 64,
        )
    with pytest.raises(runtime.UltraCompatibilityError):
        runtime.resolve_source_revision_promotion(
            current_revision="v8.2-r1",
            current_raw_sha256=RAW_SHA256,
            current_semantic_sha256=SEMANTIC_SHA256,
            candidate_raw_sha256="bad",
            candidate_semantic_sha256=SEMANTIC_SHA256,
        )


@pytest.mark.parametrize("revision", (None, 82, b"v8.2-r1"))
def test_source_revision_promotion_wraps_non_string_revision(
    revision: object,
) -> None:
    runtime = load_runtime()
    with pytest.raises(runtime.UltraCompatibilityError):
        runtime.resolve_source_revision_promotion(
            current_revision=revision,
            current_raw_sha256=RAW_SHA256,
            current_semantic_sha256=SEMANTIC_SHA256,
            candidate_raw_sha256="a" * 64,
            candidate_semantic_sha256=SEMANTIC_SHA256,
        )


def test_matrix_schema_rejects_unknown_nested_rule_fields() -> None:
    runtime = load_runtime()
    matrix = runtime.load_compatibility_matrix()
    broken = json.loads(json.dumps(matrix))
    broken["rules"][0]["fallback_runtime"] = "Max"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-compatibility-matrix.schema.json", broken)
