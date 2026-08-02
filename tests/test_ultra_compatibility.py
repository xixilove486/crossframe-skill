from __future__ import annotations

import importlib
import json
import sys
from collections import UserDict
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest
from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = ROOT / "skills/crossframe-ultra"
RUNTIME_SCRIPTS = ULTRA_ROOT / "scripts"
MATRIX_PATH = ULTRA_ROOT / "references/compatibility-matrix.json"

RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
TREE_SHA256 = "c" * 64


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
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "compiler_version": "1.0.0",
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
        "source_tree_sha256": TREE_SHA256,
    }
    value.update(changes)
    return value


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
    assert runtime.FRAMEWORK_VERSION == "8.2"
    assert runtime.FRAMEWORK_REVISION == "v8.2-r1"
    assert runtime.FRAMEWORK_RAW_SHA256 == RAW_SHA256
    assert runtime.FRAMEWORK_SEMANTIC_SHA256 == SEMANTIC_SHA256
    assert runtime.RUNTIME_VERSION == "1.0.0"
    assert runtime.ARTIFACT_SCHEMA_VERSION == 1
    assert runtime.COMPILER_VERSION == "1.0.0"
    assert runtime.VALIDATOR_VERSION == "1.0.0"
    assert runtime.ARTICLE_CONTRACT_VERSION == "1.0.0"
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
    schemas_module._load_compatibility_matrix_cached.cache_clear()
    try:
        with pytest.raises(runtime.UltraCompatibilityError):
            runtime.load_compatibility_matrix()
    finally:
        schemas_module._load_compatibility_matrix_cached.cache_clear()


def test_compatibility_is_mechanical() -> None:
    runtime = load_runtime()
    current = binding()
    cases = (
        (binding(), "resume"),
        (binding(runtime_version="0.9.0"), "read-only"),
        (binding(validator_version="1.1.0"), "read-only"),
        (binding(framework_revision="v8.2-r0"), "fork-required"),
        (binding(artifact_schema_version=0), "fork-required"),
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
