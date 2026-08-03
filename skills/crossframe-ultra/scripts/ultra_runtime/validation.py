from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import copy
from pathlib import Path
import re
from typing import Any

from .artifacts import (
    MANIFEST_FILENAME,
    PARTIAL_ARTICLE_PATH,
    READ_EVENTS_PATH,
    ArtifactManifestError,
    validate_artifact_manifest,
)
from .constants import current_version_binding
from .jsonio import (
    atomic_write_bytes,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import (
    RunLayout,
    RunMode,
    assert_safe_descendant,
    build_run_layout,
    default_root_policy,
)
from .schemas import (
    compute_artifact_content_sha256,
    validate_instance,
    validate_phase_artifact,
)


_SCHEMAS_BY_ID = {
    "crossframe.ultra.v82.evidence-ledger": "ultra-evidence-ledger.schema.json",
    "crossframe.ultra.v82.world-volume": "ultra-world-volume.schema.json",
    "crossframe.ultra.v82.claim-mechanism-graph": "ultra-claim-mechanism-graph.schema.json",
    "crossframe.ultra.v82.recursive-state": "ultra-recursive-state.schema.json",
    "crossframe.ultra.v82.recursive-lineage": "ultra-recursive-lineage.schema.json",
    "crossframe.ultra.v82.semantic-coverage": "ultra-semantic-coverage.schema.json",
}
_CHECK_ORDER = (
    "manifest-integrity",
    "artifact-integrity",
    "source-read-coverage",
    "semantic-tamper-resistance",
    "article-coverage",
    "publication-boundary",
    "privacy-logs",
)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"Authorization\s*:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:password|passwd|secret)\s*[=:]\s*\S+", re.IGNORECASE),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _checked_repo(repo: Path) -> Path:
    if not isinstance(repo, Path):
        raise TypeError("repo must be a pathlib.Path")
    resolved = repo.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("repo must be an existing directory")
    required = resolved / "skills/crossframe-ultra/scripts/ultra_runtime/validation.py"
    if not required.is_file():
        raise ValueError("repo does not contain the CrossFrame Ultra validator")
    return resolved


def validator_set_sha256(repo: Path) -> str:
    root = _checked_repo(repo)
    runtime = root / "skills/crossframe-ultra/scripts/ultra_runtime"
    relative_files = [
        "skills/crossframe-ultra/references/source-manifest.json",
        "skills/crossframe-ultra/scripts/ultra_runtime/artifacts.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/validation.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/constants.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/jsonio.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/paths.py",
        "skills/crossframe-ultra/scripts/ultra_runtime/schemas.py",
    ]
    relative_files.extend(
        path.relative_to(root).as_posix()
        for path in sorted((root / "skills/crossframe-ultra/schemas").glob("*.json"))
    )
    hashes: dict[str, str] = {}
    for relative in relative_files:
        path = root / Path(relative)
        if not path.is_file():
            raise ValueError(f"validator-set authority is missing: {relative}")
        hashes[relative] = sha256_bytes(path.read_bytes())
    if runtime != Path(__file__).resolve().parent and root == _repo_root():
        raise ValueError("validator runtime path is not bound to the selected repository")
    return sha256_bytes(canonical_json_bytes(hashes))


def _issue(
    issues: dict[str, list[tuple[str, str]]],
    check_id: str,
    error_code: str,
    artifact: str,
) -> None:
    issues[check_id].append((error_code, artifact))


def _artifact_path(layout: RunLayout, relative: str) -> Path:
    candidate = layout.run_dir / Path(relative)
    assert_safe_descendant(layout.root, candidate)
    try:
        candidate.relative_to(layout.run_dir)
    except (ValueError, OSError) as error:
        raise ValueError(f"artifact path escapes its run: {relative}") from error
    return candidate


def _load_structured_artifacts(
    layout: RunLayout,
    manifest: Mapping[str, Any],
    issues: dict[str, list[tuple[str, str]]],
) -> dict[str, list[dict[str, object]]]:
    loaded: dict[str, list[dict[str, object]]] = {}
    for record in manifest["artifacts"]:
        schema_id = str(record["schema_id"])
        if schema_id in {
            "crossframe.ultra.v82.read-event",
            "crossframe.ultra.v82.article-partial",
            "crossframe.ultra.v82.authoring-document",
        }:
            continue
        relative = str(record["path"])
        schema_name = _SCHEMAS_BY_ID.get(schema_id)
        if schema_name is None:
            _issue(
                issues,
                "artifact-integrity",
                "ULTRA-UNKNOWN-ARTIFACT",
                relative,
            )
            continue
        try:
            document = load_json_object(_artifact_path(layout, relative))
            validate_phase_artifact(
                schema_name,
                document,
                expected_schema_id=schema_id,
                expected_run_id=layout.run_dir.name,
                expected_version_binding=current_version_binding(),
                expected_phase_id=str(record["phase_id"]),
            )
        except Exception:
            if schema_id == "crossframe.ultra.v82.world-volume":
                code = "ULTRA-WORLD-FLATTENING"
                check = "semantic-tamper-resistance"
            elif schema_id == "crossframe.ultra.v82.recursive-state":
                code = "ULTRA-LINEAGE-LOSS"
                check = "semantic-tamper-resistance"
            elif schema_id == "crossframe.ultra.v82.claim-mechanism-graph":
                code = "ULTRA-EMPTY-RIVAL" if _has_empty_rival(document) else "ULTRA-ARTIFACT-SCHEMA"
                check = "semantic-tamper-resistance" if code == "ULTRA-EMPTY-RIVAL" else "artifact-integrity"
            else:
                code = "ULTRA-ARTIFACT-SCHEMA"
                check = "artifact-integrity"
            _issue(issues, check, code, relative)
            loaded.setdefault(schema_id, []).append(document)
            continue
        loaded.setdefault(schema_id, []).append(document)
    return loaded


def _has_empty_rival(graph: Mapping[str, Any]) -> bool:
    claims = {
        item.get("claim_id"): item
        for item in graph.get("claims", [])
        if isinstance(item, Mapping)
    }
    mechanisms = {
        item.get("mechanism_id"): item
        for item in graph.get("mechanisms", [])
        if isinstance(item, Mapping)
    }
    rivals = [
        item
        for item in graph.get("explanations", [])
        if isinstance(item, Mapping) and item.get("kind") == "strongest-rival"
    ]
    if len(rivals) != 1:
        return True
    rival = rivals[0]
    claim_ids = rival.get("claim_ids")
    mechanism_ids = rival.get("mechanism_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        return True
    if not isinstance(mechanism_ids, list) or not mechanism_ids:
        return True
    return any(
        not isinstance(claims.get(item, {}).get("statement"), str)
        or not claims[item]["statement"].strip()
        for item in claim_ids
    ) or any(
        not isinstance(mechanisms.get(item, {}).get("description"), str)
        or not mechanisms[item]["description"].strip()
        for item in mechanism_ids
    )


def _marker_stuffed(text: object) -> bool:
    if not isinstance(text, str):
        return False
    words = re.findall(r"[A-Za-z0-9_-]+", text.casefold())
    if len(words) < 64:
        return False
    counts = Counter(words)
    return max(counts.values()) / len(words) >= 0.5 or len(counts) / len(words) < 0.08


def _validate_claim_semantics(
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    evidence_docs = loaded.get("crossframe.ultra.v82.evidence-ledger", [])
    graph_docs = loaded.get("crossframe.ultra.v82.claim-mechanism-graph", [])
    identities: dict[str, str] = {}
    for evidence in evidence_docs:
        for item in evidence.get("entries", []):
            if isinstance(item, Mapping):
                evidence_id = item.get("evidence_id")
                identity = item.get("identity")
                if isinstance(evidence_id, str) and isinstance(identity, str):
                    identities[evidence_id] = identity
    for graph in graph_docs:
        if _has_empty_rival(graph):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-EMPTY-RIVAL",
                "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
            )
        strings = [
            item.get(field)
            for collection, field in (("claims", "statement"), ("mechanisms", "description"))
            for item in graph.get(collection, [])
            if isinstance(item, Mapping)
        ]
        if any(_marker_stuffed(value) for value in strings):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-MARKER-STUFFING",
                "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
            )
        for claim in graph.get("claims", []):
            if not isinstance(claim, Mapping) or claim.get("identity") != "observed":
                continue
            refs = claim.get("evidence_refs", [])
            if isinstance(refs, list) and any(
                identities.get(ref) == "simulated" for ref in refs
            ):
                _issue(
                    issues,
                    "semantic-tamper-resistance",
                    "ULTRA-SIMULATION-AS-FACT",
                    "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
                )
                break


def _validate_world_and_lineage(
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    for volume in loaded.get("crossframe.ultra.v82.world-volume", []):
        required = ("actors", "circles", "positions", "memberships", "local_distributions")
        if any(not isinstance(volume.get(field), list) or not volume[field] for field in required):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-WORLD-FLATTENING",
                "artifacts/U04-U05-world-volume/ultra-world-volume.json",
            )
        if any(key.startswith("global_") for key in volume):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-WORLD-FLATTENING",
                "artifacts/U04-U05-world-volume/ultra-world-volume.json",
            )
    for state in loaded.get("crossframe.ultra.v82.recursive-state", []):
        inherited = (
            "inherited_fact_ids",
            "inherited_unknown_ids",
            "inherited_loss_ids",
            "inherited_residual_ids",
        )
        if any(not isinstance(state.get(field), list) or not state[field] for field in inherited):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-LINEAGE-LOSS",
                "artifacts/U06-U08-inference",
            )


def _validate_read_events(
    repo: Path,
    layout: RunLayout,
    manifest: Mapping[str, Any],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    records = [
        item
        for item in manifest["artifacts"]
        if item["schema_id"] == "crossframe.ultra.v82.read-event"
    ]
    if len(records) != 1 or records[0]["path"] != READ_EVENTS_PATH:
        _issue(
            issues,
            "source-read-coverage",
            "ULTRA-READ-COVERAGE",
            READ_EVENTS_PATH,
        )
        return
    source_path = repo / "skills/crossframe-ultra/references/source-manifest.json"
    try:
        source = load_json_object(source_path)
        validate_instance("ultra-source-manifest.schema.json", source)
        source_manifest_sha256 = sha256_bytes(source_path.read_bytes())
        rows = _artifact_path(layout, READ_EVENTS_PATH).read_bytes().splitlines()
    except Exception:
        _issue(
            issues,
            "source-read-coverage",
            "ULTRA-READ-COVERAGE",
            READ_EVENTS_PATH,
        )
        return
    units = source["source_units"]
    if len(rows) != len(units):
        _issue(
            issues,
            "source-read-coverage",
            "ULTRA-READ-COVERAGE",
            READ_EVENTS_PATH,
        )
        return
    receipts: set[str] = set()
    for row, unit in zip(rows, units):
        try:
            event = load_json_object_bytes(row, source=READ_EVENTS_PATH)
            event_hash = event.get("read_event_sha256")
            unsigned = dict(event)
            unsigned.pop("read_event_sha256", None)
            authority_ok = (
                event.get("schema_id") == "crossframe.ultra.v82.read-event"
                and event.get("schema_version") == 1
                and event.get("run_id") == layout.run_dir.name
                and event.get("version_binding") == current_version_binding()
                and event.get("phase_id") == "U1"
                and event.get("source_manifest_sha256") == source_manifest_sha256
                and event.get("promoted_semantic_snapshot_sha256")
                == current_version_binding()["framework_semantic_sha256"]
                and event_hash == sha256_bytes(canonical_json_bytes(unsigned))
            )
            unit_ok = (
                event.get("source_unit_id") == unit["unit_id"]
                and event.get("source_kind") == unit["kind"]
                and event.get("source_ordinal") == unit["ordinal"]
                and event.get("content_sha256") == unit["sha256"]
            )
            receipt = event.get("receipt_sha256")
            receipt_ok = (
                isinstance(receipt, str)
                and re.fullmatch(r"[0-9a-f]{64}", receipt) is not None
                and receipt not in receipts
            )
        except Exception:
            authority_ok = unit_ok = receipt_ok = False
            receipt = None
        if not authority_ok or not receipt_ok:
            _issue(
                issues,
                "source-read-coverage",
                "ULTRA-READ-COVERAGE",
                READ_EVENTS_PATH,
            )
            return
        if not unit_ok:
            _issue(
                issues,
                "source-read-coverage",
                "ULTRA-SOURCE-MISMATCH",
                READ_EVENTS_PATH,
            )
            return
        receipts.add(str(receipt))


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _validate_article_coverage(
    layout: RunLayout,
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    coverage_docs = loaded.get("crossframe.ultra.v82.semantic-coverage", [])
    article_path = _artifact_path(layout, PARTIAL_ARTICLE_PATH)
    if len(coverage_docs) != 1 or not article_path.is_file():
        _issue(
            issues,
            "article-coverage",
            "ULTRA-COVERAGE-MISSING",
            PARTIAL_ARTICLE_PATH,
        )
        return
    coverage = coverage_docs[0]
    article_bytes = article_path.read_bytes()
    if coverage.get("article_sha256") != sha256_bytes(article_bytes):
        _issue(
            issues,
            "article-coverage",
            "ULTRA-ARTICLE-HASH",
            PARTIAL_ARTICLE_PATH,
        )
    try:
        article = _normalized(article_bytes.decode("utf-8", errors="strict"))
    except UnicodeDecodeError:
        article = ""
    mappings = coverage.get("mappings", [])
    missing = [
        item
        for item in mappings
        if not isinstance(item, Mapping)
        or not isinstance(item.get("normalized_excerpt"), str)
        or _normalized(str(item["normalized_excerpt"])) not in article
    ]
    if (
        coverage.get("coverage_complete") is not True
        or coverage.get("coverage_percent") != 100
        or coverage.get("missing_unit_ids") != []
        or missing
    ):
        _issue(
            issues,
            "article-coverage",
            "ULTRA-COVERAGE-MISSING",
            "work/authoring/U11-semantic-coverage.json",
        )


def _validate_logs(
    layout: RunLayout, issues: dict[str, list[tuple[str, str]]]
) -> None:
    if not layout.logs_dir.exists():
        return
    for path in sorted(layout.logs_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            assert_safe_descendant(layout.root, path)
            raw = path.read_bytes()
        except (OSError, TypeError, ValueError):
            _issue(issues, "privacy-logs", "ULTRA-SECRET-LOG", "logs")
            return
        if len(raw) > 4 * 1024 * 1024:
            _issue(issues, "privacy-logs", "ULTRA-SECRET-LOG", "logs")
            return
        text = raw.decode("utf-8", errors="replace")
        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            _issue(
                issues,
                "privacy-logs",
                "ULTRA-SECRET-LOG",
                path.relative_to(layout.run_dir).as_posix(),
            )
            return


def _report_checks(
    issues: Mapping[str, list[tuple[str, str]]]
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for check_id in _CHECK_ORDER:
        records = issues[check_id]
        checks.append(
            {
                "validator_id": check_id,
                "status": "fail" if records else "pass",
                "error_codes": sorted({code for code, _ in records}),
                "artifact_refs": sorted({artifact for _, artifact in records}),
            }
        )
    return checks


def validate_run_from_disk(
    repo: Path,
    mode: RunMode,
    run_id: str,
) -> bytes:
    root = _checked_repo(repo)
    if not isinstance(mode, RunMode):
        raise TypeError("mode must be a RunMode")
    layout = build_run_layout(mode, run_id, default_root_policy())
    manifest_path = layout.artifacts_dir / MANIFEST_FILENAME
    issues: dict[str, list[tuple[str, str]]] = {
        check_id: [] for check_id in _CHECK_ORDER
    }
    try:
        raw_manifest = manifest_path.read_bytes()
        manifest_document = load_json_object(manifest_path)
    except Exception:
        raw_manifest = b""
        manifest_document = {}
    manifest_sha = sha256_bytes(raw_manifest)
    manifest: dict[str, object] | None = None
    try:
        manifest = validate_artifact_manifest(layout, manifest_path)
    except ArtifactManifestError as error:
        target_check = (
            "publication-boundary"
            if error.error_code == "ULTRA-PREMATURE-PUBLISH"
            else "manifest-integrity"
        )
        _issue(issues, target_check, error.error_code, error.artifact)
    except Exception:
        _issue(
            issues,
            "manifest-integrity",
            "ULTRA-MANIFEST-INVALID",
            "artifacts/ultra-artifact-manifest.json",
        )

    validator_hash = validator_set_sha256(root)
    if manifest is not None:
        if manifest["validator_set_sha256"] != validator_hash:
            _issue(
                issues,
                "manifest-integrity",
                "ULTRA-VALIDATOR-SET-MISMATCH",
                "artifacts/ultra-artifact-manifest.json",
            )
        loaded = _load_structured_artifacts(layout, manifest, issues)
        _validate_read_events(root, layout, manifest, issues)
        _validate_claim_semantics(loaded, issues)
        _validate_world_and_lineage(loaded, issues)
        _validate_article_coverage(layout, loaded, issues)
    _validate_logs(layout, issues)

    checks = _report_checks(issues)
    status = "fail" if any(check["status"] != "pass" for check in checks) else "pass"
    generated_at = manifest_document.get("generated_at")
    if not isinstance(generated_at, str):
        generated_at = "1970-01-01T00:00:00Z"
    report: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.validator-report",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": current_version_binding(),
        "generated_at": generated_at,
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "attempt_id": f"fresh-{manifest_sha[:16]}",
        "manifest_sha256": manifest_sha,
        "validator_set_sha256": validator_hash,
        "checks": checks,
        "overall_status": status,
        "validated_at": generated_at,
        "fresh_context": True,
    }
    report["content_sha256"] = compute_artifact_content_sha256(report)
    validate_phase_artifact(
        "ultra-validator-report.schema.json",
        report,
        expected_schema_id="crossframe.ultra.v82.validator-report",
        expected_run_id=run_id,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    return canonical_json_bytes(report)


def _mode_for_layout(layout: RunLayout) -> RunMode:
    policy = default_root_policy()
    if layout.root == policy.production_root:
        return RunMode.PRODUCTION
    if layout.root == policy.test_root:
        return RunMode.TEST
    raise ValueError("layout root is not one of the fixed root policy authorities")


def _validated_report_bytes(
    layout: RunLayout,
    report_bytes: bytes,
    *,
    attempt_id: str,
    manifest_sha256: str,
    validator_hash: str,
) -> dict[str, object]:
    if not isinstance(report_bytes, bytes):
        raise TypeError("report_bytes must be bytes")
    try:
        report = load_json_object_bytes(
            report_bytes, source="fresh child validator report"
        )
        validate_phase_artifact(
            "ultra-validator-report.schema.json",
            report,
            expected_schema_id="crossframe.ultra.v82.validator-report",
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_phase_id="U12",
        )
    except Exception as error:
        raise ValueError(f"fresh validator report is invalid: {error}") from error
    if report_bytes != canonical_json_bytes(report):
        raise ValueError("fresh validator report bytes are not canonical")
    if report["attempt_id"] != attempt_id:
        raise ValueError("fresh validator report attempt_id differs from parent slot")
    if report["manifest_sha256"] != manifest_sha256:
        raise ValueError("fresh validator report is stale for the current manifest")
    if report["validator_set_sha256"] != validator_hash:
        raise ValueError("fresh validator report uses another validator generation")
    expected_status = (
        "pass"
        if all(check["status"] == "pass" for check in report["checks"])
        else "blocked"
        if any(check["status"] == "blocked" for check in report["checks"])
        else "fail"
    )
    if report["overall_status"] != expected_status:
        raise ValueError("fresh validator report overall status contradicts its checks")
    return report


def commit_validation_attempt(
    layout: RunLayout,
    *,
    attempt_id: str,
    report_bytes: bytes,
    expected_manifest_sha256: str,
    expected_validator_set_sha256: str,
) -> dict[str, object]:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    if not isinstance(attempt_id, str) or re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", attempt_id
    ) is None:
        raise ValueError("attempt_id is not a safe identifier")
    for value, name in (
        (expected_manifest_sha256, "expected_manifest_sha256"),
        (expected_validator_set_sha256, "expected_validator_set_sha256"),
    ):
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"{name} must be a SHA-256 digest")

    manifest_path = layout.artifacts_dir / MANIFEST_FILENAME
    manifest = validate_artifact_manifest(layout, manifest_path)
    current_manifest_sha = sha256_bytes(manifest_path.read_bytes())
    if current_manifest_sha != expected_manifest_sha256:
        raise ValueError("stale validator report: manifest generation changed")
    current_validator_hash = validator_set_sha256(_repo_root())
    if (
        manifest["validator_set_sha256"] != expected_validator_set_sha256
        or current_validator_hash != expected_validator_set_sha256
    ):
        raise ValueError("validator-set generation changed before report commit")
    report = _validated_report_bytes(
        layout,
        report_bytes,
        attempt_id=attempt_id,
        manifest_sha256=current_manifest_sha,
        validator_hash=current_validator_hash,
    )
    fresh_bytes = validate_run_from_disk(
        _repo_root(), _mode_for_layout(layout), layout.run_dir.name
    )
    if fresh_bytes != report_bytes:
        raise ValueError("parent report bytes differ from fresh disk validation")

    attempt_path = (
        layout.validation_attempts_dir
        / attempt_id
        / "ultra-validator-report.json"
    )
    current_path = layout.validation_current_dir / "ultra-validator-report.json"
    for path in (attempt_path, current_path):
        assert_safe_descendant(layout.root, path)
    if attempt_path.exists() and attempt_path.read_bytes() != report_bytes:
        raise ValueError("validation attempt slot already contains different bytes")
    atomic_write_bytes(attempt_path, report_bytes)
    if attempt_path.read_bytes() != report_bytes:
        raise ValueError("validation attempt changed during durable write")
    _validated_report_bytes(
        layout,
        attempt_path.read_bytes(),
        attempt_id=attempt_id,
        manifest_sha256=current_manifest_sha,
        validator_hash=current_validator_hash,
    )
    atomic_write_bytes(current_path, report_bytes)
    if current_path.read_bytes() != report_bytes:
        raise ValueError("validation/current changed during atomic replacement")
    return copy.deepcopy(report)
