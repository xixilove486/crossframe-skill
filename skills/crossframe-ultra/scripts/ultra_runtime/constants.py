from __future__ import annotations


FRAMEWORK_VERSION = "8.2"
FRAMEWORK_REVISION = "v8.2-r1"
FRAMEWORK_RAW_SHA256 = (
    "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
)
FRAMEWORK_SEMANTIC_SHA256 = (
    "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
)
RUNTIME_VERSION = "1.0.0"
ARTIFACT_SCHEMA_VERSION = 1
COMPILER_VERSION = "1.0.0"
VALIDATOR_VERSION = "1.0.0"
ARTICLE_CONTRACT_VERSION = "1.0.0"
SOURCE_TREE_SHA256 = (
    "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
)
VERSION_BINDING_FIELDS = (
    "framework_version",
    "framework_revision",
    "framework_raw_sha256",
    "framework_semantic_sha256",
    "runtime_version",
    "artifact_schema_version",
    "compiler_version",
    "validator_version",
    "article_contract_version",
    "source_tree_sha256",
)
PHASES = tuple(f"U{number}" for number in range(13))
RUN_STATUSES = (
    "created",
    "running",
    "interrupted",
    "blocked",
    "needs_attention",
    "failed",
    "cancelled",
    "complete",
)


def current_version_binding() -> dict[str, object]:
    return {
        "framework_version": FRAMEWORK_VERSION,
        "framework_revision": FRAMEWORK_REVISION,
        "framework_raw_sha256": FRAMEWORK_RAW_SHA256,
        "framework_semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
        "runtime_version": RUNTIME_VERSION,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "compiler_version": COMPILER_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "article_contract_version": ARTICLE_CONTRACT_VERSION,
        "source_tree_sha256": SOURCE_TREE_SHA256,
    }
