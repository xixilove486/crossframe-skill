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
