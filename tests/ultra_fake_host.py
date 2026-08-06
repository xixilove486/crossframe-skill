from __future__ import annotations

import copy
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
import re
import shutil
import socket
import sys
from typing import Mapping, Sequence


_START = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
_FIXTURE_STAMP = "2026-08-02T12:00:00Z"
_BASE_EVIDENCE_IDS = (
    "EVIDENCE-ROSTER-ATLAS",
    "EVIDENCE-ASSOCIATION-CHARTER",
    "EVIDENCE-INTERVIEW-ONE",
)
_REQUIRED_ROUTES = (
    "V82-ROUTE-CIRCLE-NESTING",
    "V82-ROUTE-NETWORK-PROPAGATION",
)
_CONCEPT_STATUS = {
    "V82-M01": "applied",
    "V82-M02": "unknown-pending",
    "V82-M03": "unknown-pending",
    "V82-M04": "not-applicable",
    "V82-M05": "tested-rejected",
    "V82-M06": "applied",
    "V82-M07": "tested-rejected",
    "V82-M08": "applied",
    "V82-M09": "tested-rejected",
}
_ACTION_KINDS = (
    "active",
    "delay",
    "probe",
    "exit-or-transfer",
    "maintain-status-quo",
    "no-action",
)


def _runtime_module(repo_root: Path, name: str):
    scripts = str(repo_root / "skills/crossframe-ultra/scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module(f"ultra_runtime.{name}")


def _load_cli(repo_root: Path):
    path = repo_root / "skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py"
    spec = importlib.util.spec_from_file_location(
        "ultra_fake_host_public_cli",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("public Ultra CLI cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"fixture must be a JSON object: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: object) -> bytes:
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


def _canonical_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def _action_completion_time(action: object) -> str:
    issued = datetime.fromisoformat(
        str(action.document["issued_at"]).replace("Z", "+00:00")
    )
    return _canonical_timestamp(issued + timedelta(seconds=1))


def canonical_receipt(
    action: object,
    *,
    execution_id: str,
    completed_at: str,
    provider: Mapping[str, object] | None = None,
    tool: Mapping[str, object] | None = None,
    include_attempts: bool = False,
) -> dict[str, object]:
    """Build an independent receipt from runtime-owned action bindings."""

    result_path = action.result_path
    receipt: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": copy.deepcopy(action.document["version_binding"]),
        "phase_id": action.document["phase_id"],
        "action_kind": action.document["action_kind"],
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": _sha256_bytes(result_path.read_bytes()),
        "execution_id": execution_id,
        "completed_at": completed_at,
    }
    if provider is not None:
        receipt["provider"] = copy.deepcopy(dict(provider))
    if tool is not None:
        receipt["tool"] = copy.deepcopy(dict(tool))
    if include_attempts:
        receipt["execution_status"] = "complete"
        receipt["attempts"] = [
            {"attempt": 1, "status": "success", "error": None}
        ]
    receipt["receipt_sha256"] = _sha256_bytes(_canonical_bytes(receipt))
    return receipt


def _replace_values(value: object, replacements: Mapping[str, str]) -> object:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_values(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_values(item, replacements)
            for key, item in value.items()
        }
    return copy.deepcopy(value)


def _apply_record_text(
    value: object,
    record_text: Mapping[str, object],
) -> None:
    if isinstance(value, list):
        for item in value:
            _apply_record_text(item, record_text)
        return
    if not isinstance(value, dict):
        return
    identities = {
        item
        for key, item in value.items()
        if key.endswith("_id") and isinstance(item, str)
    }
    for identity in identities:
        updates = record_text.get(identity)
        if not isinstance(updates, Mapping):
            continue
        for field, replacement in updates.items():
            if field in value and isinstance(replacement, str):
                value[field] = replacement
    for item in value.values():
        _apply_record_text(item, record_text)


def _downgrade_observed_evidence_to_reported(value: object) -> None:
    if isinstance(value, list):
        for item in value:
            _downgrade_observed_evidence_to_reported(item)
        return
    if not isinstance(value, dict):
        return
    if value.get("information_identity") == "observed":
        value["information_identity"] = "reported"
        if value.get("status") == "observed":
            value["status"] = "supported-hypothesis"
    for item in value.values():
        _downgrade_observed_evidence_to_reported(item)


def _rehash(repo_root: Path, document: Mapping[str, object]) -> dict[str, object]:
    schemas = _runtime_module(repo_root, "schemas")
    snapshot = copy.deepcopy(dict(document))
    snapshot["content_sha256"] = schemas.compute_artifact_content_sha256(snapshot)
    return snapshot


def _release_artifacts(skill_root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(skill_root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(skill_root)
        if (
            any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts)
            or relative.as_posix() == "references/release-manifest.json"
            or path.name == ".v8-full-source.lock"
        ):
            continue
        if path.is_file():
            records.append(
                {
                    "path": relative.as_posix(),
                    "sha256": _sha256_bytes(path.read_bytes()),
                    "media_type": "application/octet-stream",
                }
            )
    return records


def _test_authority_repo(repo_root: Path, runtime_root: Path) -> Path:
    constants = _runtime_module(repo_root, "constants")
    schemas = _runtime_module(repo_root, "schemas")
    authority = runtime_root / "authority-repo"
    skill_root = authority / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(repo_root / "skills/crossframe-ultra", skill_root)
    wrapper = authority / "scripts/check_crossframe_ultra_artifacts.py"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / "scripts/check_crossframe_ultra_artifacts.py", wrapper)
    source = _load_object(skill_root / "references/source-manifest.json")
    manifest: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.release-manifest",
        "schema_version": 1,
        "run_id": "ultra-release-v8.2-r1",
        "version_binding": constants.current_version_binding(),
        "generated_at": _FIXTURE_STAMP,
        "release_id": "ultra-v8.2-r1-runtime-1.1.0",
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
        "release_artifacts": _release_artifacts(skill_root),
        "built_at": _FIXTURE_STAMP,
        "validated_at": _FIXTURE_STAMP,
        "content_sha256": "0" * 64,
    }
    manifest["content_sha256"] = schemas.compute_artifact_content_sha256(
        manifest
    )
    (skill_root / "references/release-manifest.json").write_bytes(
        _canonical_bytes(manifest)
    )
    return authority


class DeterministicFakeHost:
    """Offline provider adapter that writes only the current host result slot."""

    def __init__(self, repo_root: Path, fixture_root: Path) -> None:
        self.repo_root = repo_root
        self.fixture_root = fixture_root
        self.capabilities = _load_object(fixture_root / "capabilities.json")
        self.corpus = _load_object(fixture_root / "retrieval-corpus.json")
        self.evidence = _load_object(fixture_root / "evidence-candidates.json")
        self.semantic = _load_object(fixture_root / "semantic-review-result.json")
        self.submissions: list[dict[str, object]] = []

    def _provider(self, provider_id: str) -> dict[str, object]:
        providers = self.capabilities.get("providers")
        if not isinstance(providers, list):
            raise ValueError("capability fixture has no providers")
        for provider in providers:
            if isinstance(provider, Mapping) and provider.get("provider_id") == provider_id:
                return copy.deepcopy(dict(provider))
        raise ValueError(f"fixture provider is absent: {provider_id}")

    def _tool(self, tool_id: str) -> dict[str, object]:
        tools = self.capabilities.get("tools")
        if not isinstance(tools, list):
            raise ValueError("capability fixture has no tools")
        for tool in tools:
            if isinstance(tool, Mapping) and tool.get("tool_id") == tool_id:
                return copy.deepcopy(dict(tool))
        raise ValueError(f"fixture tool is absent: {tool_id}")

    def _capability_result(self, action: object, completed_at: str) -> dict[str, object]:
        return {
            "measured_availability": copy.deepcopy(
                self.capabilities["measured_availability"]
            ),
            "providers": copy.deepcopy(self.capabilities["providers"]),
            "tools": copy.deepcopy(self.capabilities["tools"]),
            "measured_at": completed_at,
            "proof_grade": self.capabilities["proof_grade"],
        }

    def _source_read_result(
        self,
        action: object,
        completed_at: str,
        execution_id: str,
    ) -> dict[str, object]:
        source_integrity = _runtime_module(self.repo_root, "source_integrity")
        payload = action.document["payload"]
        return {
            "schema_id": "crossframe.ultra.v82.source-read-result",
            "schema_version": 1,
            "action_sha256": action.action_sha256,
            "read_plan_sha256": payload["read_plan_sha256"],
            "reader_mode": payload["reader_mode"],
            "execution_id": execution_id,
            "read_at": completed_at,
            "items": [
                {
                    "source_unit_id": unit["source_unit_id"],
                    "source_unit_sha256": unit["source_unit_sha256"],
                    "receipt_sha256": source_integrity._host_read_item_sha256(
                        action_sha256=action.action_sha256,
                        read_plan_sha256=payload["read_plan_sha256"],
                        reader_mode=payload["reader_mode"],
                        execution_id=execution_id,
                        read_at=completed_at,
                        source_unit_id=unit["source_unit_id"],
                        source_unit_sha256=unit["source_unit_sha256"],
                    ),
                }
                for unit in payload["source_units"]
            ],
        }

    def _retrieval_result(
        self,
        action: object,
        execution_id: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        payload = action.document["payload"]
        queries = payload["queries"]
        if not isinstance(queries, list) or len(queries) != 1:
            raise ValueError("fixture expects one frozen retrieval query")
        query_sha256 = str(queries[0]["query_sha256"])
        provider = self._provider("fixture-local-provider")
        tool = self._tool("fixture-offline-retrieval")
        source_rows = self.corpus.get("sources")
        if not isinstance(source_rows, list) or len(source_rows) < 3:
            raise ValueError("offline retrieval corpus is incomplete")
        sources: list[dict[str, object]] = []
        entries: list[dict[str, object]] = []
        for ordinal, source in enumerate(source_rows, start=1):
            if not isinstance(source, Mapping):
                raise TypeError("offline retrieval source must be an object")
            content = str(source["content"])
            source_id = str(source["source_id"])
            sources.append(
                {
                    "source_id": source_id,
                    "query_sha256": query_sha256,
                    "url": source["url"],
                    "content": content,
                    "content_sha256": _sha256_bytes(content.encode("utf-8")),
                    "event_date": source["event_date"],
                    "publication_date": source["publication_date"],
                    "interest": source["interest"],
                    "upstream_lineage": copy.deepcopy(source["upstream_lineage"]),
                    "supported_claim": source["supported_claim"],
                    "cannot_prove": source["cannot_prove"],
                }
            )
            entries.append(
                {
                    "query_id": f"QUERY-AI-EMPLOYMENT-{ordinal}",
                    "query_sha256": query_sha256,
                    "direction": source["direction"],
                    "result_summary": source["supported_claim"],
                    "source_refs": [source_id],
                    "stop_reason": "offline-corpus-source-recorded",
                }
            )
        return (
            {
                "schema_id": "crossframe.ultra.v82.host-retrieval-result",
                "schema_version": 1,
                "action_sha256": action.action_sha256,
                "provider": provider,
                "tool": tool,
                "execution_id": execution_id,
                "queries": [
                    {"query_sha256": query_sha256, "status": "complete"}
                ],
                "sources": sources,
                "entries": entries,
            },
            provider,
            tool,
        )

    def _evidence_result(self, action: object) -> dict[str, object]:
        sources = self.corpus.get("sources")
        candidates = self.evidence.get("candidates")
        if not isinstance(sources, list) or not isinstance(candidates, list):
            raise ValueError("evidence fixture is incomplete")
        by_id = {
            str(source["source_id"]): source
            for source in sources
            if isinstance(source, Mapping)
        }
        admitted = {
            str(item["source_id"]): str(item["content_sha256"])
            for item in action.document["payload"]["admitted_sources"]
        }
        entries: list[dict[str, object]] = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                raise TypeError("evidence candidate must be an object")
            source_id = str(candidate["source_id"])
            source = by_id[source_id]
            content_sha256 = _sha256_bytes(str(source["content"]).encode("utf-8"))
            if admitted.get(source_id) != content_sha256:
                raise ValueError("evidence candidate is outside admitted U2 sources")
            entries.append(
                {
                    "evidence_id": candidate["evidence_id"],
                    "identity": "reported",
                    "statement": source["content"],
                    "source_refs": [source_id],
                    "observed_at": None,
                    "confidence": candidate["confidence"],
                    "event_date": source["event_date"],
                    "publication_date": source["publication_date"],
                    "interest": source["interest"],
                    "upstream_lineage": copy.deepcopy(source["upstream_lineage"]),
                    "supported_claim": source["supported_claim"],
                    "cannot_prove": source["cannot_prove"],
                    "attribution": {
                        "origin_kind": "source",
                        "origin_ref": source_id,
                        "content_sha256": content_sha256,
                        "span": None,
                        "proof_grade": "host-attested",
                    },
                }
            )
        return {
            "candidate_entries": entries,
            "verified_subagent_candidates": [],
        }

    def _semantic_result(
        self,
        action: object,
        execution_id: str,
        reviewed_at: str,
    ) -> dict[str, object]:
        reviewer = copy.deepcopy(self.semantic["reviewer"])
        reviewer["execution_id"] = execution_id
        rows = self.semantic.get("dimension_reviews")
        if not isinstance(rows, list):
            raise ValueError("semantic review fixture is incomplete")
        return {
            "schema_id": "crossframe.ultra.v82.host-semantic-review-result",
            "schema_version": 1,
            "action_sha256": action.action_sha256,
            "reviewed_at": reviewed_at,
            "reviewer": reviewer,
            "dimension_reviews": [
                {
                    **copy.deepcopy(dict(row)),
                    "status": "pass",
                }
                for row in rows
                if isinstance(row, Mapping)
            ],
        }

    def submit(self, layout: object, action: object) -> object:
        host_handshake = _runtime_module(self.repo_root, "host_handshake")
        jsonio = _runtime_module(self.repo_root, "jsonio")
        kind = str(action.document["action_kind"])
        completed_at = _action_completion_time(action)
        execution_id = f"fixture-{kind}-{len(self.submissions) + 1:03d}"
        provider = None
        tool = None
        include_attempts = False
        if kind == "capability-attestation":
            result = self._capability_result(action, completed_at)
        elif kind == "source-read":
            result = self._source_read_result(
                action,
                completed_at,
                execution_id,
            )
            provider = self._provider("fixture-local-provider")
            tool = self._tool("fixture-source-reader")
        elif kind == "retrieval":
            result, provider, tool = self._retrieval_result(action, execution_id)
            include_attempts = True
        elif kind == "evidence-authoring":
            result = self._evidence_result(action)
            provider = self._provider("fixture-author-provider")
            tool = self._tool("fixture-model-author")
            include_attempts = True
        elif kind == "semantic-review":
            result = self._semantic_result(
                action,
                execution_id,
                completed_at,
            )
            provider = self._provider("fixture-review-provider")
            tool = self._tool("fixture-fresh-semantic-review")
            include_attempts = True
        else:
            raise AssertionError(f"unexpected host action: {kind}")
        jsonio.atomic_write_json(action.result_path, result)
        receipt = canonical_receipt(
            action,
            execution_id=execution_id,
            completed_at=completed_at,
            provider=provider,
            tool=tool,
            include_attempts=include_attempts,
        )
        accepted = host_handshake.accept_host_result(
            layout,
            action=action,
            receipt=receipt,
        )
        accepted_path = (
            layout.recovery_dir
            / "host-results"
            / action.action_sha256
            / "accepted.json"
        )
        self.submissions.append(
            {
                "action_kind": kind,
                "phase_id": action.document["phase_id"],
                "action_sha256": action.action_sha256,
                "result_path": action.result_path,
                "result_sha256": receipt["result_sha256"],
                "accepted_path": accepted_path,
                "receipt_sha256": accepted.receipt_sha256,
                "execution_id": execution_id,
            }
        )
        return accepted


class FixtureAuthor:
    """Model-side author that writes only slots returned by public progress."""

    def __init__(self, repo_root: Path, fixture_root: Path) -> None:
        self.repo_root = repo_root
        self.fixture_root = fixture_root
        self.base_root = fixture_root.parent
        self.semantics = _load_object(fixture_root / "authoring-semantics.json")
        self.mapping_config = _load_object(fixture_root / "semantic-mappings.json")
        self.writes: list[str] = []
        self.coverage_mappings: list[dict[str, object]] = []

    def _base(self, name: str) -> dict[str, object]:
        replacements = {
            **self.semantics["evidence_id_map"],
            **self.semantics["source_id_map"],
        }
        document = _replace_values(
            _load_object(self.base_root / name),
            replacements,
        )
        if not isinstance(document, dict):
            raise TypeError("base authoring fixture must remain an object")
        _apply_record_text(document, self.semantics["record_text"])
        if name == "world-volume-valid.json":
            _downgrade_observed_evidence_to_reported(document)
        return _rehash(self.repo_root, document)

    def _write_json(self, layout: object, relative: str, value: object) -> None:
        jsonio = _runtime_module(self.repo_root, "jsonio")
        path = layout.authoring_dir / relative
        jsonio.atomic_write_json(path, value)
        self.writes.append(relative)

    def _write_text(self, layout: object, relative: str, value: str) -> None:
        path = layout.authoring_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8", newline="\n")
        self.writes.append(relative)

    def _concept_document(self, layout: object) -> dict[str, object]:
        evidence = _load_object(
            layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
        )
        world = _load_object(layout.authoring_dir / "U04-world-volume.json")
        transformations = _load_object(
            layout.authoring_dir / "U05-transformation-ledger.json"
        )
        registry = _load_object(
            self.repo_root
            / "skills/crossframe-ultra/references/concept-registry/v8.2-concept-registry.json"
        )
        route_map = _load_object(
            self.repo_root / "skills/crossframe-ultra/references/v8.2-route-map.json"
        )
        routes = {
            str(record["route_id"]): record
            for record in route_map["routes"]
            if isinstance(record, Mapping)
        }
        required_routes = [routes[route_id] for route_id in _REQUIRED_ROUTES]
        required_concepts = {
            str(value)
            for route in required_routes
            for value in route["concept_ids"]
        }
        required_contracts = sorted(
            {
                str(value)
                for route in required_routes
                for value in route["contract_ids"]
            }
        )
        required_requirements = sorted(
            {
                str(value)
                for route in required_routes
                for value in route["requirement_ids"]
            }
        )
        evidence_ids = [
            str(entry["evidence_id"])
            for entry in evidence["entries"]
            if isinstance(entry, Mapping)
        ]
        if len(evidence_ids) < 3:
            raise ValueError("concept fixture requires three admitted evidence IDs")
        transform_ids = [
            str(record["transform_id"])
            for record in transformations["transformations"]
            if isinstance(record, Mapping)
        ]
        rationales = self.semantics["concept_rationales"]
        dispositions: list[dict[str, object]] = []
        obligations: list[dict[str, object]] = []
        route_records = routes
        for index, concept in enumerate(registry["concepts"], start=1):
            concept_id = str(concept["concept_id"])
            status = _CONCEPT_STATUS[concept_id]
            concept_routes = sorted(
                route_id
                for route_id in _REQUIRED_ROUTES
                if concept_id in route_records[route_id]["concept_ids"]
            )
            contract_ids = sorted(
                {
                    str(contract_id)
                    for route_id in concept_routes
                    for contract_id in route_records[route_id]["contract_ids"]
                }
            )
            requirement_ids = sorted(
                {
                    str(requirement_id)
                    for route_id in concept_routes
                    for requirement_id in route_records[route_id]["requirement_ids"]
                }
            )
            if status == "not-applicable":
                selected_evidence: list[str] = []
                unknown_ids: list[str] = []
                selected_transforms: list[str] = []
                obligation_ids: list[str] = []
                condition_branch = None
            else:
                selected_evidence = [evidence_ids[(index - 1) % len(evidence_ids)]]
                unknown_ids = ["UNKNOWN-ADAPTATION"] if status == "unknown-pending" else []
                selected_transforms = [
                    transform_ids[(index - 1) % len(transform_ids)]
                ]
                obligation_id = f"OBLIGATION-{concept_id}"
                obligation_ids = [obligation_id]
                branch_id = (
                    f"BRANCH-{concept_id}"
                    if status == "unknown-pending"
                    else None
                )
                condition_branch = (
                    {
                        "branch_id": branch_id,
                        "condition": (
                            "只有新增的时序与边界证据区分描述关系和因果转换时，"
                            "该人工智能就业分支才可升级。"
                        ),
                        "evidence_plan": {
                            "plan_id": f"PLAN-{concept_id}",
                            "required_evidence": [
                                "同类岗位、相近采用强度下的时序比较。",
                                "能区分技术采用、行业周期和制度承接的中断检验。",
                            ],
                        },
                    }
                    if branch_id is not None
                    else None
                )
                obligations.append(
                    {
                        "obligation_id": obligation_id,
                        "concept_id": concept_id,
                        "status": status,
                        "semantic_unit_id": f"SEMANTIC-UNIT-{concept_id}",
                        "evidence_ids": selected_evidence,
                        "unknown_ids": unknown_ids,
                        "transformation_ids": selected_transforms,
                        "route_ids": concept_routes,
                        "contract_ids": contract_ids,
                        "requirement_ids": requirement_ids,
                        "condition_branch_id": branch_id,
                    }
                )
            dispositions.append(
                {
                    "concept_id": concept_id,
                    "status": status,
                    "rationale": rationales[concept_id],
                    "route_required": concept_id in required_concepts,
                    "neighbor_concept_ids": copy.deepcopy(
                        concept["required_neighbors"]
                    ),
                    "route_ids": concept_routes,
                    "contract_ids": contract_ids,
                    "requirement_ids": requirement_ids,
                    "obligation_ids": obligation_ids,
                    "evidence_ids": selected_evidence,
                    "unknown_ids": unknown_ids,
                    "transformation_ids": selected_transforms,
                    "condition_branch": condition_branch,
                }
            )
        constants = _runtime_module(self.repo_root, "constants")
        document = {
            "schema_id": "crossframe.ultra.v82.concept-disposition",
            "schema_version": 1,
            "run_id": layout.run_dir.name,
            "version_binding": constants.current_version_binding(),
            "generated_at": _FIXTURE_STAMP,
            "content_sha256": "0" * 64,
            "phase_id": "U5",
            "evidence_artifact_sha256": "1" * 64,
            "evidence_content_sha256": evidence["content_sha256"],
            "world_volume_artifact_sha256": "2" * 64,
            "world_volume_content_sha256": world["content_sha256"],
            "transformation_ledger_artifact_sha256": "3" * 64,
            "transformation_ledger_content_sha256": transformations[
                "content_sha256"
            ],
            "registry_sha256": "4" * 64,
            "route_map_sha256": "5" * 64,
            "contract_map_sha256": "6" * 64,
            "required_route_ids": sorted(_REQUIRED_ROUTES),
            "required_contract_ids": required_contracts,
            "required_requirement_ids": required_requirements,
            "dispositions": dispositions,
            "semantic_obligations": obligations,
            "unvisited_concept_ids": [],
            "closure_complete": True,
        }
        return _rehash(self.repo_root, document)

    def _recursive_documents(self) -> tuple[list[dict[str, object]], dict[str, object]]:
        base = self._base("recursive-state-valid.json")

        def derived(**changes: object) -> dict[str, object]:
            value = copy.deepcopy(base)
            value.update(changes)
            return _rehash(self.repo_root, value)

        states = [
            base,
            derived(
                node_id="NODE-MAIN-ORDER-2",
                parent_node_id="NODE-MAIN-ORDER-1",
                order=2,
                full_state_sha256="a9b46daf47867f0706406687ee5e23b05712cdf99a8a3f4e2b5b659999846ad4",
                event_id="EVENT-ACTION-SET-REVERSAL",
                mechanism_ids=["MECHANISM-WORKLOAD-ALLOCATION"],
                state_diff_sha256="7fa17563e075a39cf12c75e515ffe874977d940fe2d3a636ef9b3fc85f3bdd97",
                signal_ids=["SIGNAL-ACTION-REVERSAL"],
                evidence_identity="simulated-result",
                declared_evidence_grade="low",
            ),
            derived(
                node_id="NODE-MAIN-ORDER-3",
                parent_node_id="NODE-MAIN-ORDER-2",
                order=3,
                full_state_sha256="830f9e7149814e40ca028af7408b2f2afe2a1abd6a0207f2d30de9cdfeaa118b",
                event_id="EVENT-INSTITUTIONAL-LOCK-IN",
                mechanism_ids=["MECHANISM-COMBINED-PRESSURE"],
                state_diff_sha256="663a9e460d9fb3970411ec16d8140f49a48ad60637b96d8ae0ca437d2ca19d8f",
                signal_ids=["SIGNAL-INSTITUTIONAL-LOCK"],
                evidence_identity="simulated-result",
                declared_evidence_grade="low",
            ),
            derived(
                path_id="PATH-RIVAL",
                node_id="NODE-RIVAL-ORDER-1",
                parent_path_id="PATH-RIVAL",
                full_state_sha256="72949ab79e88afb8a38cff054a78404db2bfe55336c6c8faa860e67fc27cfc3c",
                event_id="EVENT-RIVAL-WORKLOAD",
                mechanism_ids=["MECHANISM-WORKLOAD-ALLOCATION"],
                state_diff_sha256="6ff419a803b41b17dd267ea22cfd8800072f3ae7f35d92558f6f7896e289f1fd",
                signal_ids=["SIGNAL-RIVAL-WORKLOAD"],
                evidence_identity="competing-explanation",
                declared_evidence_grade="low",
            ),
            derived(
                path_id="PATH-MIXTURE",
                node_id="NODE-MIXTURE-ORDER-1",
                parent_path_id="PATH-MIXTURE",
                full_state_sha256="596fe5666c335e9770a9ee1acbed81a7955bce822afaeac6f3f5f56384f0e544",
                event_id="EVENT-MIXTURE-PRESSURE",
                mechanism_ids=["MECHANISM-COMBINED-PRESSURE"],
                state_diff_sha256="f59670c1b37cd097540827cff040537593774c807ed9aec010c56579bab29973",
                signal_ids=["SIGNAL-MIXTURE-PRESSURE"],
                evidence_identity="competing-explanation",
                declared_evidence_grade="low",
            ),
            derived(
                path_id="PATH-RESIDUAL",
                node_id="NODE-RESIDUAL-ORDER-1",
                parent_path_id="PATH-RESIDUAL",
                full_state_sha256="d05dbb2b880d1c520c3cc9f84e973a62ef02fb83c0eff196c7aeb926bc6f9791",
                event_id="EVENT-RESIDUAL-PEER",
                mechanism_ids=["MECHANISM-PEER-RESIDUAL"],
                state_diff_sha256="ea7ade3f6cdc3be7a4c9294bf4991ab15c1ad6e1bc01071d2a92cdf2f6e1447a",
                signal_ids=["SIGNAL-RESIDUAL-PEER"],
                evidence_identity="unknown",
                declared_evidence_grade="unknown",
            ),
        ]
        state_hash_by_node = {
            str(state["node_id"]): _sha256_bytes(_canonical_bytes(state))
            for state in states
        }
        lineage = self._base("recursive-lineage-valid.json")
        for node in lineage["nodes"]:
            if isinstance(node, dict):
                node["recursive_state_artifact_sha256"] = state_hash_by_node[
                    str(node["node_id"])
                ]
        return states, _rehash(self.repo_root, lineage)

    def _verdict(self) -> dict[str, object]:
        verdict = self._base("verdict-valid.json")
        configured = self.semantics["verdict_text"]
        main = verdict["main_verdict"]
        main["proposition"] = configured["proposition"]
        main["scope"] = configured["scope"]
        main["rival_rejection_reasons"] = [
            configured["rival_rejection_reason"]
        ]
        main["reversal_conditions"] = [configured["reversal_condition"]]
        main["action_implication"] = configured["action_implication"]
        main["distributions"][0]["benefits"] = ["任务互补与更快的岗位转换"]
        main["distributions"][0]["harms"] = ["收入中断、技能折旧与议价下降"]
        main["distributions"][0]["responsibility"] = [
            "人工智能采用方与制度设计者监测可逆试点"
        ]
        main["distributions"][0]["spillovers"] = [
            "家庭照护和地区保障差异保持可见"
        ]
        propositions = {
            "fact": "固定来源记录了任务暴露、转岗损失与制度差异,但没有证明长期净就业方向。",
            "prediction": "制度承接薄弱时,人工智能任务重组更可能转化为收入中断和失业期延长。",
            "value": "生产率收益与过渡风险不应由议价能力最低的劳动者单边承担。",
            "responsibility": "采用人工智能的企业与培训、保障制度设计者先承担过渡与监测责任。",
            "authorization": "当前证据只授权有停止条件的培训、收入缓冲和岗位匹配试点。",
        }
        for row in verdict["five_verdicts"]:
            row["proposition"] = propositions[str(row["kind"])]
        verdict["assumptions"] = [configured["assumption"]]
        return _rehash(self.repo_root, verdict)

    def _action_ranking(self, verdict: Mapping[str, object]) -> dict[str, object]:
        constants = _runtime_module(self.repo_root, "constants")
        authorization = next(
            item
            for item in verdict["five_verdicts"]
            if item["kind"] == "authorization"
        )
        descriptions = self.semantics["action_descriptions"]
        document = {
            "schema_id": "crossframe.ultra.v82.action-ranking",
            "schema_version": 1,
            "run_id": verdict["run_id"],
            "version_binding": constants.current_version_binding(),
            "generated_at": _FIXTURE_STAMP,
            "phase_id": "U9",
            "verdict_artifact_sha256": _sha256_bytes(_canonical_bytes(verdict)),
            "considered_verdict_ids": [
                item["verdict_id"] for item in verdict["five_verdicts"]
            ],
            "requested_choice": True,
            "options": [
                {
                    "option_id": f"OPTION-{kind.upper()}",
                    "kind": kind,
                    "description": descriptions[kind],
                    "authorized": kind == "probe",
                    "authorization_verdict_id": (
                        authorization["verdict_id"] if kind == "probe" else None
                    ),
                    "benefits": ["产生可比较的转岗与收入恢复信息"],
                    "harms": ["占用有限财政、企业和劳动者时间"],
                    "requirements": ["保留证据边界与预注册比较指标"],
                    "rollback": "指标未改善或伤害阈值触发时退回冻结基线。",
                }
                for kind in _ACTION_KINDS
            ],
            "ranking": [
                "OPTION-PROBE",
                "OPTION-DELAY",
                "OPTION-ACTIVE",
                "OPTION-MAINTAIN-STATUS-QUO",
                "OPTION-EXIT-OR-TRANSFER",
                "OPTION-NO-ACTION",
            ],
            "preferred_option_id": "OPTION-PROBE",
            "second_option_id": "OPTION-DELAY",
            "switch_conditions": [
                "制度差异失去解释力或收入恢复没有改善时切换。"
            ],
            "stop_conditions": ["雇主工资压低或转岗伤害超过冻结阈值时停止。"],
            "no_action_consequences": [
                "转换成本继续集中于议价能力最低的劳动者。"
            ],
        }
        return _rehash(self.repo_root, document)

    def _gap(self, action: Mapping[str, object]) -> dict[str, object]:
        constants = _runtime_module(self.repo_root, "constants")
        configured = self.semantics["gap_text"]
        document = {
            "schema_id": "crossframe.ultra.v82.framework-gap-ledger",
            "schema_version": 1,
            "run_id": action["run_id"],
            "version_binding": constants.current_version_binding(),
            "generated_at": _FIXTURE_STAMP,
            "phase_id": "U10",
            "evidence_ledger_artifact_sha256": "1" * 64,
            "claim_mechanism_graph_artifact_sha256": "2" * 64,
            "recursive_lineage_artifact_sha256": "3" * 64,
            "order_evaluation_artifact_sha256": "4" * 64,
            "red_team_report_artifact_sha256": "5" * 64,
            "verdict_artifact_sha256": "6" * 64,
            "action_ranking_artifact_sha256": _sha256_bytes(
                _canonical_bytes(action)
            ),
            "forecast_ledger_artifact_sha256": "7" * 64,
            "candidates": [
                {
                    "gap_id": "GAP-LATENCY-CALIBRATION",
                    "description": configured["description"],
                    "evidence_refs": [
                        self.semantics["evidence_id_map"]["EVIDENCE-ROSTER-ATLAS"]
                    ],
                    "claim_ids": ["CLAIM-CHANNEL-CONSTRAINT"],
                    "mechanism_ids": ["MECHANISM-REVIEW-CHANNEL"],
                    "recursive_node_ids": ["NODE-MAIN-ORDER-1"],
                    "route_ids": ["ROUTE-CHANNEL"],
                    "concept_ids": ["V82-CONCEPT-CHANNEL"],
                    "future_revision_proposal": configured[
                        "future_revision_proposal"
                    ],
                    "status": "candidate",
                }
            ],
            "isolated_from_current_reasoning": True,
        }
        return _rehash(self.repo_root, document)

    def _forecast(self) -> dict[str, object]:
        forecast = self._base("forecast-valid.json")
        configured = self.semantics["forecast_text"]
        for row in forecast["forecasts"]:
            update = configured.get(str(row["forecast_id"]))
            if isinstance(update, Mapping):
                row.update(copy.deepcopy(dict(update)))
        return _rehash(self.repo_root, forecast)

    def _required_upstream(
        self,
        layout: object,
    ) -> tuple[list[dict[str, str]], dict[str, dict[str, object]], dict[str, str]]:
        fixed = [
            ("U03-evidence-ledger.json", "artifacts/U00-U03-evidence/U03-evidence-ledger.json"),
            ("U04-world-volume.json", "artifacts/U04-U05-world-volume/U04-world-volume.json"),
            ("U05-transformation-ledger.json", "artifacts/U04-U05-world-volume/U05-transformation-ledger.json"),
            ("U05-concept-disposition.json", "artifacts/U04-U05-world-volume/U05-concept-disposition.json"),
            ("U06-claim-mechanism-graph.json", "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json"),
        ]
        state_paths = sorted(
            (layout.artifacts_dir / "U06-U08-inference/U07-recursive-states").glob("*.json"),
            key=lambda path: str(_load_object(path)["node_id"]),
        )
        fixed.extend(
            (
                f"U07-recursive-states/{path.name}",
                path.relative_to(layout.run_dir).as_posix(),
            )
            for path in state_paths
        )
        fixed.extend(
            [
                ("U07-recursive-lineage.json", "artifacts/U06-U08-inference/U07-recursive-lineage.json"),
                ("U08-order-evaluation.json", "artifacts/U06-U08-inference/U08-order-evaluation.json"),
                ("U08-red-team-report.json", "artifacts/U06-U08-inference/U08-red-team-report.json"),
                ("U09-verdict.json", "artifacts/U09-U10-verdict/U09-verdict.json"),
                ("U09-action-ranking.json", "artifacts/U09-U10-verdict/U09-action-ranking.json"),
                ("U09-forecast-ledger.json", "artifacts/U09-U10-verdict/U09-forecast-ledger.json"),
            ]
        )
        records: list[dict[str, str]] = []
        documents: dict[str, dict[str, object]] = {}
        hashes: dict[str, str] = {}
        for authoring_relative, artifact_relative in fixed:
            path = layout.run_dir / artifact_relative
            document = _load_object(path)
            digest = _sha256_bytes(path.read_bytes())
            records.append(
                {
                    "path": artifact_relative,
                    "sha256": digest,
                    "media_type": "application/json",
                }
            )
            documents[authoring_relative] = document
            hashes[authoring_relative] = digest
        return records, documents, hashes

    def _output_plan(self, layout: object) -> dict[str, object]:
        article = _runtime_module(self.repo_root, "article")
        coverage = _runtime_module(self.repo_root, "coverage")
        constants = _runtime_module(self.repo_root, "constants")
        authority = _load_object(
            self.base_root / "article-packets/frozen-upstream-authority.json"
        )
        required, documents, hashes = self._required_upstream(layout)
        sections = copy.deepcopy(authority["sections"])
        appendices = copy.deepcopy(authority["appendices"])
        units = copy.deepcopy(authority["semantic_universe"])
        mappings = copy.deepcopy(authority["mappings"])
        entries = [*sections, *appendices]
        entry_by_id = {str(entry["section_id"]): entry for entry in entries}
        mapping_by_id = {str(item["unit_id"]): item for item in mappings}
        overrides = self.mapping_config["overrides"]
        base_authority = {
            "UNIT-MAIN-VERDICT": ("U06-claim-mechanism-graph.json", "CLAIM-CHANNEL-CONSTRAINT"),
            "UNIT-CONFIDENCE": ("U08-order-evaluation.json", "BASELINE-ORDER-1"),
            "UNIT-STEELMAN": ("U07-recursive-states/NODE-MIXTURE-ORDER-1.json", "NODE-MIXTURE-ORDER-1"),
            "UNIT-DECISIVE-EVIDENCE": ("U03-evidence-ledger.json", self.semantics["evidence_id_map"]["EVIDENCE-ASSOCIATION-CHARTER"]),
            "UNIT-UNKNOWN": ("U04-world-volume.json", "UNKNOWN-ADAPTATION"),
            "UNIT-CIRCLE-RELATION": ("U05-transformation-ledger.json", "TRANSFORM-CIRCLE-RELATION"),
            "UNIT-MECHANISM": ("U06-claim-mechanism-graph.json", "MECHANISM-REVIEW-CHANNEL"),
            "UNIT-RIVAL": ("U07-recursive-states/NODE-RIVAL-ORDER-1.json", "NODE-RIVAL-ORDER-1"),
            "UNIT-ORDER-1": ("U07-recursive-states/NODE-MAIN-ORDER-1.json", "NODE-MAIN-ORDER-1"),
            "UNIT-ORDER-2": ("U07-recursive-states/NODE-MAIN-ORDER-2.json", "NODE-MAIN-ORDER-2"),
            "UNIT-ORDER-3": ("U07-recursive-states/NODE-MAIN-ORDER-3.json", "NODE-MAIN-ORDER-3"),
            "UNIT-RESIDUAL": ("U07-recursive-states/NODE-RESIDUAL-ORDER-1.json", "NODE-RESIDUAL-ORDER-1"),
            "UNIT-FIVE-VERDICTS": ("U09-verdict.json", "VERDICT-FACT"),
            "UNIT-ACTION": ("U09-action-ranking.json", "OPTION-PROBE"),
            "UNIT-REVERSAL": ("U09-action-ranking.json", "OPTION-DELAY"),
            "UNIT-APPENDIX-MAPPING": ("U04-world-volume.json", "OMEGA-FIXTURE"),
            "UNIT-APPENDIX-BRANCHES": ("U07-recursive-lineage.json", "BRANCH-MAIN"),
            "UNIT-APPENDIX-FORECAST": ("U09-forecast-ledger.json", "FORECAST-BRANCH-SELECTION"),
            "UNIT-APPENDIX-SOURCES": ("U03-evidence-ledger.json", self.semantics["evidence_id_map"]["EVIDENCE-INTERVIEW-ONE"]),
            "UNIT-APPENDIX-GAPS": ("U08-red-team-report.json", "UNRESOLVED-PEER-CHANNEL"),
        }
        for unit in units:
            unit_id = str(unit["unit_id"])
            relative, locator = base_authority[unit_id]
            excerpt = str(overrides[unit_id])
            unit["authority_artifact_sha256"] = hashes[relative]
            unit["authority_locator"] = locator
            unit["normalized_semantic_text_sha256"] = _sha256_bytes(
                coverage.normalize_excerpt(excerpt).encode("utf-8")
            )
            mapping_by_id[unit_id]["normalized_excerpt"] = excerpt
            if unit_id == "UNIT-APPENDIX-SOURCES":
                mapping_by_id[unit_id]["source_refs"] = [locator]

        concept = documents["U05-concept-disposition.json"]
        for obligation in concept["semantic_obligations"]:
            unit_id = str(obligation["semantic_unit_id"])
            excerpt = str(overrides[unit_id])
            entry_by_id["reader-14"]["semantic_unit_ids"].append(unit_id)
            unit = {
                "unit_id": unit_id,
                "unit_kind": "claim",
                "status": obligation["status"],
                "affects_ranking": True,
                "used_in_reasoning": True,
                "promised_to_reader": True,
                "source_refs": [obligation["obligation_id"]],
                "authority_artifact_sha256": hashes[
                    "U05-concept-disposition.json"
                ],
                "authority_locator": obligation["obligation_id"],
                "normalized_semantic_text_sha256": _sha256_bytes(
                    coverage.normalize_excerpt(excerpt).encode("utf-8")
                ),
            }
            units.append(unit)
            mappings.append(
                {
                    "unit_id": unit_id,
                    "unit_kind": "claim",
                    "section_id": "reader-14",
                    "normalized_excerpt": excerpt,
                    "source_refs": [obligation["obligation_id"]],
                }
            )

        extra_units = self.mapping_config["extra_units"]
        for configured in extra_units:
            relative = str(configured["authority_relative_path"])
            unit_id = str(configured["unit_id"])
            excerpt = str(configured["normalized_excerpt"])
            unit = {
                "unit_id": unit_id,
                "unit_kind": configured["unit_kind"],
                "status": "used-in-reasoning",
                "affects_ranking": True,
                "used_in_reasoning": True,
                "promised_to_reader": True,
                "source_refs": copy.deepcopy(configured["source_refs"]),
                "authority_artifact_sha256": hashes[relative],
                "authority_locator": configured["authority_locator"],
                "normalized_semantic_text_sha256": _sha256_bytes(
                    coverage.normalize_excerpt(excerpt).encode("utf-8")
                ),
            }
            units.append(unit)
            section_id = str(configured["section_id"])
            entry_by_id[section_id]["semantic_unit_ids"].append(unit_id)
            mappings.append(
                {
                    "unit_id": unit_id,
                    "unit_kind": configured["unit_kind"],
                    "section_id": section_id,
                    "normalized_excerpt": excerpt,
                    "source_refs": copy.deepcopy(configured["source_refs"]),
                }
            )

        units_by_id = {str(unit["unit_id"]): unit for unit in units}
        for entry in entries:
            entry["dependency_hashes"] = list(
                dict.fromkeys(
                    str(units_by_id[unit_id]["authority_artifact_sha256"])
                    for unit_id in entry["semantic_unit_ids"]
                )
            )
        all_mappings = {str(item["unit_id"]): item for item in mappings}
        expectations = copy.deepcopy(authority["blind_recovery_expectations"])
        for expectation in expectations:
            unit_ids = expectation["semantic_unit_ids"]
            if len(unit_ids) != 1:
                raise ValueError("fixture blind expectation must bind one unit")
            excerpt = str(all_mappings[str(unit_ids[0])]["normalized_excerpt"])
            expectation["normalized_value_sha256"] = _sha256_bytes(
                coverage.normalize_excerpt(excerpt).encode("utf-8")
            )
        self.coverage_mappings = copy.deepcopy(mappings)
        return article.build_output_plan_artifact(
            run_id=layout.run_dir.name,
            version_binding=constants.current_version_binding(),
            generated_at=_FIXTURE_STAMP,
            u9_parent_event_sha256="0" * 64,
            article_path="work/authoring/article.partial.md",
            sections=sections,
            appendices=appendices,
            required_artifacts=required,
            semantic_universe=units,
            blind_recovery_expectations=expectations,
        )

    def _article_parts(self) -> tuple[str, ...]:
        text = (self.fixture_root / "article.md").read_text("utf-8").replace(
            "\r\n", "\n"
        )
        parts = tuple(
            match.group(0).strip() + "\n"
            for match in re.finditer(r"(?ms)^## .*?(?=^## |\Z)", text)
        )
        if len(parts) != 15:
            raise ValueError("open-world article must contain exactly 15 packets")
        return parts

    def _article_text(self) -> str:
        return "\n\n".join(part.strip() for part in self._article_parts()).rstrip() + "\n"

    def _write_u11_semantics(self, layout: object) -> None:
        article = _runtime_module(self.repo_root, "article")
        constants = _runtime_module(self.repo_root, "constants")
        coverage = _runtime_module(self.repo_root, "coverage")
        jsonio = _runtime_module(self.repo_root, "jsonio")
        materialization = _runtime_module(self.repo_root, "materialization")
        output_plan = _load_object(
            layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
        )
        packet_paths = tuple(
            sorted(
                (layout.authoring_dir / "article/packets").glob("*.md"),
                key=lambda path: path.name,
            )
        )
        packets = materialization._packet_mappings(output_plan, packet_paths)
        ordered = article.order_and_validate_packets(output_plan, packets)
        article_text = (
            "\n\n".join(str(packet["prose"]).strip() for packet in ordered).rstrip()
            + "\n"
        )
        if article_text != self._article_text():
            raise ValueError("packet assembly differs from the fixture article")
        plan_hash = _sha256_bytes(jsonio.canonical_json_bytes(output_plan))
        if not self.coverage_mappings:
            raise ValueError("U11 author lacks the U10 semantic mapping projection")
        coverage_document = coverage.build_semantic_coverage_artifact(
            article_text,
            output_plan,
            self.coverage_mappings,
            run_id=layout.run_dir.name,
            version_binding=constants.current_version_binding(),
            generated_at=_FIXTURE_STAMP,
            expected_output_plan_artifact_sha256=plan_hash,
        )
        coverage_hash = _sha256_bytes(
            jsonio.canonical_json_bytes(coverage_document)
        )
        review = coverage.build_article_review_artifact(
            article_text,
            output_plan,
            coverage_document,
            run_id=layout.run_dir.name,
            version_binding=constants.current_version_binding(),
            generated_at=_FIXTURE_STAMP,
            expected_output_plan_artifact_sha256=plan_hash,
            expected_coverage_artifact_sha256=coverage_hash,
        )
        self._write_json(layout, "U11-semantic-coverage.json", coverage_document)
        self._write_json(layout, "U11-article-review.json", review)
        dossier = (self.fixture_root / "dossier.md").read_text("utf-8")
        self._write_text(layout, "完整推演档案.md", dossier)

    @staticmethod
    def _matches_slot(relative: str, slot: str) -> bool:
        if slot == "U07-recursive-states/<node-id>.json":
            return (
                relative.startswith("U07-recursive-states/")
                and relative.endswith(".json")
                and "/" not in relative[len("U07-recursive-states/") :]
            )
        if slot == "article/packets/<packet-id>.md":
            return (
                relative.startswith("article/packets/")
                and relative.endswith(".md")
                and "/" not in relative[len("article/packets/") :]
            )
        return relative == slot

    def write(self, layout: object, action: Mapping[str, object]) -> None:
        if action.get("action_kind") != "authoring" or action.get("owner") != "model":
            raise ValueError("fixture author requires a model-owned authoring action")
        slots = [str(action["relative_path"])]
        additional = action.get("relative_paths")
        if isinstance(additional, list):
            slots = [str(value) for value in additional]
        before = len(self.writes)
        phase_id = str(action["phase_id"])
        if phase_id == "U4":
            self._write_json(layout, "U04-world-volume.json", self._base("world-volume-valid.json"))
        elif phase_id == "U5":
            self._write_json(layout, "U05-transformation-ledger.json", self._base("transformation-valid.json"))
            self._write_json(layout, "U05-concept-disposition.json", self._concept_document(layout))
        elif phase_id == "U6":
            self._write_json(layout, "U06-claim-mechanism-graph.json", self._base("claim-mechanism-graph-valid.json"))
        elif phase_id == "U7":
            states, lineage = self._recursive_documents()
            for state in states:
                self._write_json(
                    layout,
                    f"U07-recursive-states/{state['node_id']}.json",
                    state,
                )
            self._write_json(layout, "U07-recursive-lineage.json", lineage)
        elif phase_id == "U8":
            self._write_json(layout, "U08-order-evaluation.json", self._base("order-evaluation-valid.json"))
            self._write_json(layout, "U08-red-team-report.json", self._base("red-team-report-valid.json"))
        elif phase_id == "U9":
            verdict = self._verdict()
            self._write_json(layout, "U09-verdict.json", verdict)
            self._write_json(layout, "U09-action-ranking.json", self._action_ranking(verdict))
            self._write_json(layout, "U09-forecast-ledger.json", self._forecast())
        elif phase_id == "U10":
            action_ranking = _load_object(layout.authoring_dir / "U09-action-ranking.json")
            self._write_json(layout, "U10-framework-gap-ledger.json", self._gap(action_ranking))
            self._write_json(layout, "U10-output-plan.json", self._output_plan(layout))
        elif phase_id == "U11" and slots == ["article/packets/<packet-id>.md"]:
            for ordinal, prose in enumerate(self._article_parts(), start=1):
                self._write_text(
                    layout,
                    f"article/packets/packet-{ordinal:02d}.md",
                    prose,
                )
        elif phase_id == "U11":
            self._write_u11_semantics(layout)
        else:
            raise AssertionError(f"unexpected authoring phase: {phase_id}")
        written = self.writes[before:]
        if not written or any(
            not any(self._matches_slot(relative, slot) for slot in slots)
            for relative in written
        ):
            raise AssertionError(
                f"fixture author wrote outside returned slots: slots={slots}, writes={written}"
            )


class _Clock:
    def __init__(self) -> None:
        self.ordinal = 0

    def next(self) -> datetime:
        value = _START + timedelta(seconds=self.ordinal * 2)
        self.ordinal += 1
        return value


@contextmanager
def _forbid_network(calls: list[str]):
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo
    original_socket = socket.socket

    def denied(*args, **kwargs):
        calls.append(repr(args[0] if args else "network"))
        raise AssertionError("deterministic Ultra fixture attempted network access")

    class DeniedSocket(original_socket):
        def connect(self, address):
            return denied(address)

        def connect_ex(self, address):
            return denied(address)

    socket.create_connection = denied
    socket.getaddrinfo = denied
    socket.socket = DeniedSocket
    try:
        yield
    finally:
        socket.create_connection = original_create_connection
        socket.getaddrinfo = original_getaddrinfo
        socket.socket = original_socket


def _public_call(
    cli: object,
    argv: Sequence[str],
    *,
    policy: object,
    now: datetime,
    stdin_bytes: bytes = b"",
    entropy: bytes,
) -> dict[str, object]:
    stdout = StringIO()
    stderr = StringIO()
    result = cli.execute(
        list(argv),
        stdin=BytesIO(stdin_bytes),
        stdout=stdout,
        stderr=stderr,
        root_policy=policy,
        now=lambda: now,
        entropy=lambda: entropy,
    )
    if result != 0 or stderr.getvalue():
        raise AssertionError(
            f"public CLI call failed: result={result}, stderr={stderr.getvalue()}"
        )
    value = json.loads(stdout.getvalue())
    if not isinstance(value, dict):
        raise TypeError("public CLI response must be an object")
    return value


def _active_complete_events(path: Path) -> list[dict[str, object]]:
    active: list[dict[str, object]] = []
    for line in path.read_text("utf-8").splitlines():
        event = json.loads(line)
        if event["status"] == "complete":
            active.append(event)
        elif event["status"] == "invalidated":
            phase = str(event["reset_from_phase"])
            active = active[: int(phase[1:])]
    return active


def _quality_projection(
    fixture_root: Path,
    *,
    output_plan: Mapping[str, object],
    semantic_review: Mapping[str, object],
    coverage: Mapping[str, object],
    article_text: str,
) -> tuple[dict[str, str], dict[str, object]]:
    expected = _load_object(fixture_root / "expected-quality.json")
    units = {
        str(unit["unit_id"]): unit
        for unit in output_plan["semantic_universe"]
        if isinstance(unit, Mapping)
    }
    mappings = {
        str(mapping["unit_id"]): mapping
        for mapping in coverage["mappings"]
        if isinstance(mapping, Mapping)
    }
    dimensions = {
        str(row["dimension_id"]): row
        for row in semantic_review["dimension_reviews"]
        if isinstance(row, Mapping)
    }
    statuses: dict[str, str] = {}
    details: dict[str, object] = {}
    for name, projection in expected.items():
        if not isinstance(projection, Mapping):
            raise TypeError("quality projection must be an object")
        ids = tuple(str(value) for value in projection["semantic_ids"])
        if len(ids) != len(set(ids)) or len(ids) < 3:
            raise AssertionError(f"{name} semantic IDs are not distinct")
        locators = tuple(str(units[unit_id]["authority_locator"]) for unit_id in ids)
        if len(locators) != len(set(locators)):
            raise AssertionError(f"{name} authority locators are not distinct")
        spans: list[tuple[int, int]] = []
        for unit_id in ids:
            excerpt = str(mappings[unit_id]["normalized_excerpt"])
            start = article_text.find(excerpt)
            if start < 0 or article_text.find(excerpt, start + 1) >= 0:
                raise AssertionError(
                    f"{name} excerpt is absent or repeated: {unit_id}"
                )
            spans.append((start, start + len(excerpt)))
        if any(
            left[0] < right[1] and right[0] < left[1]
            for index, left in enumerate(spans)
            for right in spans[index + 1 :]
        ):
            raise AssertionError(f"{name} article spans overlap")
        dimension_ids = [str(projection["dimension_id"])]
        companion = projection.get("companion_dimension_id")
        if isinstance(companion, str):
            dimension_ids.append(companion)
        if any(dimensions[dimension]["status"] != "pass" for dimension in dimension_ids):
            raise AssertionError(f"{name} semantic review dimension failed")
        statuses[name] = "pass"
        details[name] = {
            "semantic_ids": ids,
            "authority_locators": locators,
            "article_spans": tuple(spans),
            "dimensions": tuple(dimension_ids),
        }
    return statuses, details


def run_open_world_ai_employment_fixture(
    repo_root: Path,
    fixture_root: Path,
    runtime_root: Path,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    fixture_root = fixture_root.resolve()
    runtime_root = runtime_root.resolve()
    if not fixture_root.is_dir():
        raise FileNotFoundError(f"open-world fixture is absent: {fixture_root}")
    authority_repo = _test_authority_repo(repo_root, runtime_root)
    cli = _load_cli(repo_root)
    paths = _runtime_module(repo_root, "paths")
    validation = _runtime_module(repo_root, "validation")
    source_integrity = _runtime_module(repo_root, "source_integrity")
    host_handshake = _runtime_module(repo_root, "host_handshake")
    recovery = _runtime_module(repo_root, "recovery")
    policy = paths.RootPolicy(
        runtime_root / "production-control",
        runtime_root / "test-control",
    )
    original_default_policy = validation.default_root_policy
    original_fresh_checker = cli._fresh_checker
    original_production_root = source_integrity.PRODUCTION_ROOT
    validation.default_root_policy = lambda: policy
    source_integrity.PRODUCTION_ROOT = policy.production_root
    cli._fresh_checker = lambda selected_repo, mode, run_id: (
        validation.validate_run_from_disk(selected_repo, mode, run_id)
    )
    common = ["--repo", str(authority_repo), "--mode", "test"]
    clock = _Clock()
    network_calls: list[str] = []
    fake_host = DeterministicFakeHost(repo_root, fixture_root)
    author = FixtureAuthor(repo_root, fixture_root)
    restart_checks: dict[str, bool] = {}
    request_bytes = (fixture_root / "request.txt").read_bytes()
    try:
        with _forbid_network(network_calls):
            started = _public_call(
                cli,
                ["start", *common, "--request-stdin"],
                policy=policy,
                now=clock.next(),
                stdin_bytes=request_bytes,
                entropy=b"open-world-ai-employment-start",
            )
            run_id = str(started["run_id"])
            layout = paths.build_run_layout(paths.RunMode.TEST, run_id, policy)
            prepared = _public_call(
                cli,
                ["prepare", *common, "--run-id", run_id],
                policy=policy,
                now=clock.next(),
                entropy=b"open-world-ai-employment-prepare",
            )
            pending_path = layout.recovery_dir / "pending-action.json"
            pending_before = pending_path.read_bytes()
            repeated_prepare = _public_call(
                cli,
                ["prepare", *common, "--run-id", run_id],
                policy=policy,
                now=clock.next(),
                entropy=b"open-world-ai-employment-prepare-repeat",
            )
            restart_checks["U0"] = (
                repeated_prepare["next_action"] == prepared["next_action"]
                and pending_path.read_bytes() == pending_before
            )
            response = repeated_prepare
            repeated_kinds: set[str] = {"capability-attestation"}
            for ordinal in range(1, 80):
                outcome = str(response["outcome"])
                if outcome == "awaiting-host-action":
                    pending = host_handshake.load_pending_action(layout)
                    if pending is None or pending.document != response["next_action"]:
                        raise AssertionError("public host wait differs from pending action")
                    kind = str(pending.document["action_kind"])
                    if kind in {"source-read", "semantic-review"} and kind not in repeated_kinds:
                        before = pending_path.read_bytes()
                        repeated = _public_call(
                            cli,
                            ["materialize", *common, "--run-id", run_id],
                            policy=policy,
                            now=clock.next(),
                            entropy=f"host-restart-{kind}".encode(),
                        )
                        restart_checks[
                            "U1-first" if kind == "source-read" else "semantic-review"
                        ] = (
                            repeated["next_action"] == response["next_action"]
                            and pending_path.read_bytes() == before
                        )
                        repeated_kinds.add(kind)
                        response = repeated
                        pending = host_handshake.load_pending_action(layout)
                        if pending is None:
                            raise AssertionError("pending host action disappeared on restart")
                    fake_host.submit(layout, pending)
                elif outcome == "awaiting-authoring":
                    action = response["next_action"]
                    if not isinstance(action, Mapping):
                        raise TypeError("authoring wait has no action")
                    if action["phase_id"] == "U4" and "U4" not in restart_checks:
                        repeated = _public_call(
                            cli,
                            ["materialize", *common, "--run-id", run_id],
                            policy=policy,
                            now=clock.next(),
                            entropy=b"authoring-restart-u4",
                        )
                        restart_checks["U4"] = repeated == response
                        response = repeated
                        action = response["next_action"]
                    author.write(layout, action)
                elif outcome == "complete":
                    break
                else:
                    raise AssertionError(f"unexpected public progress: {response}")
                response = _public_call(
                    cli,
                    ["materialize", *common, "--run-id", run_id],
                    policy=policy,
                    now=clock.next(),
                    entropy=f"open-world-materialize-{ordinal:03d}".encode(),
                )
            else:
                raise AssertionError("open-world fixture did not reach U12")
            if response["outcome"] != "complete":
                raise AssertionError(f"open-world fixture stopped early: {response}")
            phase_event_path = layout.recovery_dir / "phase-events.jsonl"
            before_terminal_events = phase_event_path.read_bytes()
            before_journal = (
                layout.recovery_dir / "publish-transaction.json"
            ).read_bytes()
            terminal_retry = _public_call(
                cli,
                ["materialize", *common, "--run-id", run_id],
                policy=policy,
                now=clock.next(),
                entropy=b"open-world-terminal-retry",
            )
            restart_checks["terminal"] = (
                terminal_retry["outcome"] == "complete"
                and phase_event_path.read_bytes() == before_terminal_events
                and (layout.recovery_dir / "publish-transaction.json").read_bytes()
                == before_journal
            )
    finally:
        validation.default_root_policy = original_default_policy
        cli._fresh_checker = original_fresh_checker
        source_integrity.PRODUCTION_ROOT = original_production_root

    if network_calls:
        raise AssertionError(f"offline fixture attempted network calls: {network_calls}")
    if not all(restart_checks.values()):
        raise AssertionError(f"restart/idempotence checks failed: {restart_checks}")
    if (layout.recovery_dir / "pending-action.json").exists():
        raise AssertionError("completed open-world run retains a pending host action")
    for submission in fake_host.submissions:
        result_path = submission["result_path"]
        accepted_path = submission["accepted_path"]
        if (
            not isinstance(result_path, Path)
            or not isinstance(accepted_path, Path)
            or _sha256_bytes(result_path.read_bytes()) != submission["result_sha256"]
            or not accepted_path.is_file()
            or _load_object(accepted_path)["receipt_sha256"]
            != submission["receipt_sha256"]
        ):
            raise AssertionError("accepted host action did not survive disk reread")

    phase_events = _active_complete_events(
        layout.recovery_dir / "phase-events.jsonl"
    )
    if [event["phase_id"] for event in phase_events] != [
        f"U{ordinal}" for ordinal in range(13)
    ]:
        raise AssertionError("open-world phase chain is incomplete or duplicated")
    for previous, current in zip(phase_events, phase_events[1:]):
        if current["parent_event_sha256"] != previous["event_sha256"]:
            raise AssertionError("open-world phase parent chain is discontinuous")
    checkpoints = recovery.load_checkpoints(layout)
    u1_read_plan = _load_object(layout.recovery_dir / "u1-authority/read-plan.json")
    u1_coverage = _load_object(
        layout.recovery_dir / "u1-authority/source-coverage.json"
    )
    read_events = (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    ).read_text("utf-8").splitlines()
    if len(read_events) != int(u1_read_plan["source_unit_count"]):
        raise AssertionError("U1 source-read coverage is incomplete")
    u2 = _load_object(
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    u2["query_count"] = len(u2["queries"])
    u3 = _load_object(
        layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    semantic_review = _load_object(
        layout.artifacts_dir / "U09-U10-verdict/U11-semantic-review.json"
    )
    coverage = _load_object(
        layout.artifacts_dir / "U09-U10-verdict/U11-semantic-coverage.json"
    )
    output_plan = _load_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    article_path = layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
    article_text = article_path.read_text("utf-8")
    quality, quality_details = _quality_projection(
        fixture_root,
        output_plan=output_plan,
        semantic_review=semantic_review,
        coverage=coverage,
        article_text=article_text,
    )
    validation_report = _load_object(
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    final_status = _load_object(layout.run_dir / "run-status.json")
    final_chat = _load_object(layout.run_dir / "final-chat.json")
    manifest = _load_object(layout.artifacts_dir / "ultra-artifact-manifest.json")
    if final_chat.get("article_path") != str(article_path.resolve()):
        raise AssertionError("final chat does not point to the official article")
    if not str(final_chat.get("center_judgment_summary", "")).strip():
        raise AssertionError("final chat has no substantive center judgment")
    if len(
        [
            digest
            for event in phase_events
            if event["phase_id"] == "U11"
            for digest in event["output_artifact_hashes"]
        ]
    ) != 6:
        raise AssertionError("U11 phase event must bind six current outputs")
    return {
        "status": final_status["status"],
        "outcome": response["outcome"],
        "request_profile": "open-world",
        "layout": layout,
        "authority_repo": authority_repo,
        "phase_events": phase_events,
        "checkpoints": checkpoints,
        "u1": {
            "read_plan": u1_read_plan,
            "coverage": u1_coverage,
            "read_event_count": len(read_events),
        },
        "u2": u2,
        "u3": u3,
        "semantic_review": semantic_review,
        "validation": validation_report,
        "manifest": manifest,
        "final_chat": final_chat,
        "article_path": article_path,
        "article_text": article_text,
        "quality": quality,
        "quality_details": quality_details,
        "host_submissions": fake_host.submissions,
        "authoring_writes": tuple(author.writes),
        "network_calls": tuple(network_calls),
        "restart_checks": restart_checks,
        "terminal_retry": terminal_retry,
    }


__all__ = (
    "DeterministicFakeHost",
    "FixtureAuthor",
    "canonical_receipt",
    "run_open_world_ai_employment_fixture",
)
