from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Iterator, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
for import_root in (REPO_ROOT, SCRIPTS_DIR):
    value = str(import_root)
    if value not in sys.path:
        sys.path.insert(0, value)

from tests.ultra_closed_fixture_support import (  # noqa: E402
    CLOSED_ORGANIZATION_CASE,
    write_closed_u4_u10_authoring,
    write_closed_u11_authoring,
)
from tests.ultra_capability_support import (  # noqa: E402
    capability_attestation_for_contract,
    default_capability_requirements,
)
from ultra_runtime import artifacts  # noqa: E402
from ultra_runtime import constants  # noqa: E402
from ultra_runtime import deliverables  # noqa: E402
from ultra_runtime import evidence  # noqa: E402
from ultra_runtime import indexes  # noqa: E402
from ultra_runtime import jsonio  # noqa: E402
from ultra_runtime import materialization  # noqa: E402
from ultra_runtime import paths  # noqa: E402
from ultra_runtime import recovery  # noqa: E402
from ultra_runtime import retrieval  # noqa: E402
from ultra_runtime import source_integrity  # noqa: E402
from ultra_runtime import state_machine  # noqa: E402
from ultra_runtime import status  # noqa: E402
from ultra_runtime import validation  # noqa: E402


def _canonical_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("started_at must be timezone-aware UTC")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.isoformat(timespec=timespec).replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_files(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    if not root.is_dir():
        raise ValueError(f"snapshot root is not a directory: {root}")
    return {
        path.relative_to(root).as_posix(): _sha256_file(path)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def _production_surface(root: Path) -> tuple[dict[str, object], str]:
    start_here = root / "START-HERE.md"
    if start_here.exists() and not start_here.is_file():
        raise ValueError("production START-HERE surface is not a regular file")
    index_dir = root / "index"
    if index_dir.exists() and not index_dir.is_dir():
        raise ValueError("production index surface is not a directory")
    snapshot: dict[str, object] = {
        "start_here_sha256": (
            _sha256_file(start_here) if start_here.is_file() else None
        ),
        "index_exists": index_dir.is_dir(),
        "index_files": _snapshot_files(index_dir),
    }
    digest = jsonio.sha256_bytes(jsonio.canonical_json_bytes(snapshot))
    return snapshot, digest


def _existing_run_outputs(root: Path) -> dict[str, str]:
    return _snapshot_files(root / "runs")


def _without_new_run(
    snapshot: Mapping[str, str],
    *,
    run_relative: str,
) -> dict[str, str]:
    prefix = run_relative.rstrip("/") + "/"
    return {
        relative: digest
        for relative, digest in snapshot.items()
        if not relative.startswith(prefix)
    }


def _run_contract(request_sha256: str, evidence_cutoff: str) -> dict[str, object]:
    return {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": evidence_cutoff,
        "capabilities": default_capability_requirements(),
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }


def _u1_coverage_payload(
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    parent_event_sha256: str,
    source_lock_sha256: str,
    receipts: tuple[object, ...],
    events: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "artifact_type": "crossframe.ultra.v82.u1-source-coverage",
        "run_id": run_id,
        "version_binding": dict(version_binding),
        "parent_event_sha256": parent_event_sha256,
        "source_lock_sha256": source_lock_sha256,
        "receipt_sha256s": [receipt.receipt_sha256 for receipt in receipts],
        "read_event_sha256s": [str(event["read_event_sha256"]) for event in events],
    }


def _write_checkpoint(
    layout: paths.RunLayout,
    store: state_machine.PhaseStore,
    phase_id: str,
    artifact_paths: tuple[Path, ...],
    now: datetime,
) -> dict[str, object]:
    return recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id=phase_id,
        boundary_ordinal=0,
        artifact_paths=artifact_paths,
        now=now,
    )


def _establish_u0_u3(
    repo_root: Path,
    layout: paths.RunLayout,
    *,
    started_at: datetime,
) -> state_machine.PhaseStore:
    request_path = layout.input_dir / "request.bin"
    metadata_path = layout.input_dir / "request-metadata.json"
    request_bytes = jsonio.canonical_json_bytes(
        {
            "analysis_kind": "closed-input",
            "claim": CLOSED_ORGANIZATION_CASE["order_2"]["condition"],
            "material": json.dumps(
                CLOSED_ORGANIZATION_CASE,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
    )
    jsonio.atomic_write_bytes(request_path, request_bytes)
    jsonio.atomic_write_json(
        metadata_path,
        {
            "request_sha256": jsonio.sha256_bytes(request_bytes),
            "request_size": len(request_bytes),
        },
    )
    layout.logs_dir.mkdir(parents=True, exist_ok=True)
    request_sha256 = jsonio.sha256_bytes(request_bytes)
    input_paths = tuple(sorted((request_path, metadata_path), key=lambda path: path.name))
    locked_inputs = [
        {
            "path": path.name,
            "sha256": _sha256_file(path),
            "media_type": (
                "application/json"
                if path.suffix.casefold() == ".json"
                else "application/octet-stream"
            ),
        }
        for path in input_paths
    ]
    input_snapshot_sha256 = jsonio.sha256_bytes(
        jsonio.canonical_json_bytes(locked_inputs)
    )
    evidence_cutoff = _canonical_utc(started_at)
    binding = constants.current_version_binding()
    source_manifest_path = (
        repo_root / "skills/crossframe-ultra/references/source-manifest.json"
    )
    manifest = source_integrity.load_source_manifest(
        source_manifest_path,
        expected_sha256=_sha256_file(source_manifest_path),
    )
    measurement = source_integrity.measure_u1_prerequisites(
        repo_root,
        manifest=manifest,
        release_manifest_path=(
            repo_root
            / "skills/crossframe-ultra/references/release-manifest.json"
        ),
        run_mode="test",
    )
    if not measurement.ready:
        raise RuntimeError(
            "closed smoke U1 prerequisites are not ready: "
            + ", ".join(measurement.missing)
        )

    created = status.RunStatusStore(layout).create(started_at)
    materialization.seal_request_intake_authority(
        layout,
        request_sha256=request_sha256,
        request_size=len(request_bytes),
        created_at=created.created_at,
    )
    run_contract = _run_contract(request_sha256, evidence_cutoff)
    capability_attestation = capability_attestation_for_contract(
        run_id=layout.run_dir.name,
        version_binding=binding,
        contract=run_contract,
        generated_at=evidence_cutoff,
    )
    run_contract["capability_attestation_sha256"] = (
        capability_attestation.artifact_sha256
    )
    store = state_machine.PhaseStore(
        run_id=layout.run_dir.name,
        version_binding=binding,
        source_sha256=manifest.sha256,
        input_artifact_hashes=tuple(item["sha256"] for item in locked_inputs),
        input_snapshot_sha256=input_snapshot_sha256,
        evidence_cutoff=evidence_cutoff,
        now=started_at,
        run_contract=run_contract,
        capability_attestation=capability_attestation,
        source_repository=repo_root,
        u1_prerequisite_measurement=measurement,
        run_layout=layout,
    )

    u0_event = store.complete(
        "U0",
        artifact_hashes=(store.run_contract_artifact_sha256,),
    )
    run_contract_path = layout.artifacts_dir / "ultra-run-contract.json"
    capability_attestation_path = (
        layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json"
    )
    jsonio.atomic_write_bytes(
        capability_attestation_path,
        capability_attestation.artifact_bytes,
    )
    jsonio.atomic_write_json(run_contract_path, dict(store.run_contract))
    _write_checkpoint(
        layout,
        store,
        "U0",
        (run_contract_path,),
        started_at + timedelta(seconds=1),
    )

    source_lock = source_integrity.build_source_lock(
        run_id=store.run_id,
        version_binding=binding,
        generated_at=evidence_cutoff,
        prerequisite_measurement=measurement,
        parent_event_sha256=u0_event["event_sha256"],
        evidence_cutoff=evidence_cutoff,
        run_layout=layout,
        inputs=locked_inputs,
    )
    source_lock_seal = source_integrity.validate_source_lock(
        source_lock,
        prerequisite_measurement=measurement,
        expected_run_id=store.run_id,
        expected_version_binding=binding,
        expected_parent_event_sha256=u0_event["event_sha256"],
        expected_evidence_cutoff=evidence_cutoff,
        expected_inputs=locked_inputs,
        run_layout=layout,
    )
    session = source_integrity.open_source_read_session(
        repo_root,
        run_id=store.run_id,
        version_binding=binding,
        manifest=manifest,
        source_lock_sha256=source_lock_seal.artifact_sha256,
        parent_event_sha256=u0_event["event_sha256"],
        reader_mode="full-source",
        read_at=evidence_cutoff,
    )
    receipts = tuple(
        source_integrity.capture_source_unit_read(session, unit["unit_id"])[1]
        for unit in manifest.document["source_units"]
    )
    read_events = tuple(
        source_integrity.make_read_event(
            run_id=store.run_id,
            version_binding=binding,
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=source_lock_seal.artifact_sha256,
            parent_event_sha256=u0_event["event_sha256"],
            receipt=receipt,
        )
        for receipt in receipts
    )
    read_audit = source_integrity.audit_read_capture(
        read_events,
        manifest,
        receipts=receipts,
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        expected_run_id=store.run_id,
        expected_version_binding=binding,
        expected_source_lock_sha256=source_lock_seal.artifact_sha256,
        expected_parent_event_sha256=u0_event["event_sha256"],
    )
    u1_authority = source_integrity.validate_u1_authority(
        source_lock_seal,
        read_audit,
    )
    store.complete(
        "U1",
        artifact_hashes=(
            u1_authority.source_lock_artifact_sha256,
            u1_authority.read_coverage_artifact_sha256,
        ),
        u1_authority=u1_authority,
    )
    u1_authority_dir = layout.recovery_dir / "u1-authority"
    source_lock_path = u1_authority_dir / "source-lock.json"
    source_coverage_path = u1_authority_dir / "source-coverage.json"
    jsonio.atomic_write_json(source_lock_path, source_lock)
    source_coverage = _u1_coverage_payload(
        run_id=store.run_id,
        version_binding=binding,
        parent_event_sha256=u0_event["event_sha256"],
        source_lock_sha256=source_lock_seal.artifact_sha256,
        receipts=receipts,
        events=read_events,
    )
    jsonio.atomic_write_json(source_coverage_path, source_coverage)
    if _sha256_file(source_coverage_path) != read_audit.artifact_sha256:
        raise RuntimeError("U1 source coverage artifact differs from its authority")
    read_events_path = (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    )
    jsonio.atomic_write_bytes(
        read_events_path,
        b"".join(jsonio.canonical_json_bytes(event) for event in read_events),
    )
    _write_checkpoint(
        layout,
        store,
        "U1",
        (source_lock_path, source_coverage_path),
        started_at + timedelta(seconds=2),
    )

    decision = retrieval.assess_retrieval_eligibility(
        "If A then B.",
        phase_store=store,
        pure_logic=True,
    )
    retrieval_ledger = retrieval.build_retrieval_ledger(
        decision,
        generated_at=evidence_cutoff,
        phase_store=store,
    )
    retrieval_seal = retrieval.validate_retrieval_ledger(
        retrieval_ledger,
        phase_store=store,
        expected_run_id=store.run_id,
        expected_version_binding=binding,
        expected_phase_id="U2",
        expected_u1_parent_event_sha256=store.events[-1]["event_sha256"],
        expected_request_sha256=request_sha256,
        expected_decision_sha256=decision.decision_sha256,
        expected_authorization_sha256=None,
    )
    store.complete(
        "U2",
        artifact_hashes=(retrieval_seal.artifact_sha256,),
        retrieval_authority=retrieval_seal,
    )
    retrieval_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    jsonio.atomic_write_json(retrieval_path, retrieval_ledger)
    _write_checkpoint(
        layout,
        store,
        "U2",
        (retrieval_path,),
        started_at + timedelta(seconds=3),
    )

    evidence_fixture = json.loads(
        (
            repo_root
            / "tests/fixtures/ultra-runtime/evidence-ledger-valid.json"
        ).read_text("utf-8")
    )
    for entry in evidence_fixture["entries"]:
        store.append_evidence(entry)
    evidence_seal = evidence.validate_evidence_artifact(
        store.evidence_artifact,
        expected_run_id=store.run_id,
        expected_version_binding=binding,
        expected_phase_id="U3",
        expected_evidence_cutoff=store.evidence_cutoff,
    )
    store.complete(
        "U3",
        artifact_hashes=(evidence_seal.artifact_sha256,),
        evidence_authority=evidence_seal,
    )
    evidence_path = (
        layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    jsonio.atomic_write_json(evidence_path, store.evidence_artifact)
    _write_checkpoint(
        layout,
        store,
        "U3",
        (evidence_path,),
        started_at + timedelta(seconds=4),
    )
    return store


@contextmanager
def _selected_validation_policy(
    policy: paths.RootPolicy,
) -> Iterator[None]:
    original = validation.default_root_policy
    validation.default_root_policy = lambda: policy
    try:
        yield
    finally:
        validation.default_root_policy = original


def _subprocess_fresh_validation(
    repo_root: Path,
    run_id: str,
) -> bytes:
    checker = (
        repo_root
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(checker),
            "--repo",
            str(repo_root),
            "--mode",
            "test",
            "--run-id",
            run_id,
            "--json",
        ],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    if completed.returncode not in {0, 1} or not completed.stdout:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"fresh validator failed with {completed.returncode}: {detail}"
        )
    jsonio.load_json_object_bytes(
        completed.stdout,
        source="fixed-root fresh validator stdout",
    )
    return completed.stdout


def _start_here_resolves(layout: paths.RunLayout) -> bool:
    root_start = layout.root / "START-HERE.md"
    run_start = layout.run_dir / "START-HERE.md"
    navigation = (
        f"runs/{layout.run_dir.name[:4]}/{layout.run_dir.name[4:6]}/"
        f"{layout.run_dir.name}/START-HERE.md"
    )
    if not root_start.is_file() or not run_start.is_file():
        return False
    if navigation not in root_start.read_text("utf-8"):
        return False
    if not (layout.root / Path(navigation)).is_file():
        return False
    run_text = run_start.read_text("utf-8")
    required = {
        "run-status.json": layout.run_dir / "run-status.json",
        "input/": layout.input_dir,
        "authoring/": layout.authoring_dir,
        "artifacts/": layout.artifacts_dir,
        "delivery/": layout.delivery_dir,
        "validation/": layout.validation_dir,
        "recovery/": layout.recovery_dir,
        "logs/": layout.logs_dir,
    }
    return all(label in run_text and target.exists() for label, target in required.items())


def run_fixed_root_smoke(
    *,
    root_policy: paths.RootPolicy | None = None,
    started_at: datetime | None = None,
    run_entropy: bytes | None = None,
    transaction_entropy: bytes | None = None,
) -> dict[str, object]:
    repo_root = REPO_ROOT.resolve(strict=True)
    fixed_policy = paths.default_root_policy()
    policy = fixed_policy if root_policy is None else root_policy
    if not isinstance(policy, paths.RootPolicy):
        raise TypeError("root_policy must be a RootPolicy")
    start = datetime.now(timezone.utc) if started_at is None else started_at
    _canonical_utc(start)
    selected_run_entropy = secrets.token_bytes(32) if run_entropy is None else run_entropy
    selected_transaction_entropy = (
        secrets.token_bytes(32)
        if transaction_entropy is None
        else transaction_entropy
    )
    if not isinstance(selected_run_entropy, bytes) or not isinstance(
        selected_transaction_entropy, bytes
    ):
        raise TypeError("smoke entropy values must be bytes")
    run_id = paths.create_run_id(start, selected_run_entropy)
    layout = paths.build_run_layout(paths.RunMode.TEST, run_id, policy)
    if layout.run_dir.exists():
        raise FileExistsError(f"fixed-root smoke run already exists: {run_id}")

    production_before, production_before_sha = _production_surface(
        policy.production_root
    )
    existing_runs_before = _existing_run_outputs(policy.test_root)
    staging_before = _snapshot_files(policy.test_root / ".staging")
    _establish_u0_u3(repo_root, layout, started_at=start)

    resumed = recovery.resume_run(
        layout,
        now=start + timedelta(seconds=5),
    )
    phase_store = resumed.phase_store
    if phase_store is None or phase_store.current_phase != "U3":
        raise RuntimeError("closed smoke did not recover the U3 authority")
    if not phase_store.evidence_frozen:
        raise RuntimeError("closed smoke recovered mutable U3 evidence")

    materialization.prepare_authoring(layout)
    output_authority = write_closed_u4_u10_authoring(repo_root, layout)
    try:
        materialization.materialize_u4_u11(
            repo_root,
            layout,
            phase_store,
            now=start + timedelta(seconds=6),
            create_checkpoint=recovery.create_checkpoint,
        )
    except ValueError as error:
        if "packet count" not in str(error):
            raise
    else:
        raise RuntimeError("closed smoke U10 boundary accepted absent article packets")

    sealed_plan = jsonio.load_json_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    u11_time = start + timedelta(seconds=7)
    write_closed_u11_authoring(
        repo_root,
        layout,
        sealed_plan,
        output_authority,
        generated_at=_canonical_utc(u11_time),
    )
    bundle = materialization.materialize_u4_u11(
        repo_root,
        layout,
        phase_store,
        now=u11_time,
        create_checkpoint=recovery.create_checkpoint,
    )
    if bundle.phase_events[-1]["phase_id"] != "U11":
        raise RuntimeError("closed smoke did not reach U11")

    expected_official = (
        layout.artifacts_dir / "ultra-artifact-manifest.json",
        layout.delivery_dir / "CrossFrame-Ultra-完整文章.md",
        layout.delivery_dir / "完整推演档案.md",
        layout.delivery_dir / "工件索引.md",
    )
    pre_u12_official_absent = not any(path.exists() for path in expected_official)
    if not pre_u12_official_absent:
        raise RuntimeError("official delivery exists before the U12 publish boundary")

    use_subprocess = policy == fixed_policy
    complete_time = start + timedelta(seconds=8)
    with _selected_validation_policy(policy):
        def fresh_check(stage: str) -> bytes:
            if stage not in {"pre-publish", "post-publish"}:
                raise ValueError(f"unexpected validation stage: {stage}")
            article_path = layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
            if stage == "pre-publish" and article_path.exists():
                raise RuntimeError("official article exists during pre-publish validation")
            if stage == "post-publish" and not article_path.is_file():
                raise RuntimeError("official article is absent during post-publish validation")
            if use_subprocess:
                return _subprocess_fresh_validation(repo_root, run_id)
            return validation.validate_run_from_disk(
                repo_root,
                paths.RunMode.TEST,
                run_id,
            )

        def commit_report(stage: str, report_bytes: bytes) -> object:
            if stage not in {"pre-publish", "post-publish"}:
                raise ValueError(f"unexpected validation commit stage: {stage}")
            report = jsonio.load_json_object_bytes(
                report_bytes,
                source=f"{stage} fixed-root validator report",
            )
            return validation.commit_validation_attempt(
                layout,
                attempt_id=report["attempt_id"],
                report_bytes=report_bytes,
                expected_manifest_sha256=report["manifest_sha256"],
                expected_validator_set_sha256=report["validator_set_sha256"],
            )

        complete = materialization.materialize_complete_run(
            repo_root,
            paths.RunMode.TEST,
            run_id,
            policy=policy,
            now=complete_time,
            entropy=selected_transaction_entropy,
            fresh_check=fresh_check,
            commit_report=commit_report,
        )

    final_status = status.RunStatusStore(layout).read()
    if (
        complete.status != "complete"
        or final_status.status != "complete"
        or final_status.current_phase != "U12"
        or final_status.last_complete_phase != "U12"
        or final_status.validation_passed is not True
        or final_status.tools_allowed is not False
    ):
        raise RuntimeError("fixed-root smoke did not close complete U12 status")
    checkpoint = recovery.select_resume_checkpoint(layout)
    if checkpoint["phase_id"] != "U12":
        raise RuntimeError("latest recovery checkpoint is not U12")
    checkpoints = recovery.load_checkpoints(layout)
    phase_checkpoint_ids = [
        str(item["phase_id"])
        for item in checkpoints
        if item.get("boundary_kind") == "phase"
    ]
    expected_phases = [f"U{number}" for number in range(13)]
    if phase_checkpoint_ids != expected_phases:
        raise RuntimeError(
            f"phase checkpoint chain differs: {phase_checkpoint_ids}"
        )
    phase_events = [
        json.loads(line)
        for line in (
            layout.recovery_dir / "phase-events.jsonl"
        ).read_text("utf-8").splitlines()
    ]
    phase_ids = [
        str(event["phase_id"])
        for event in phase_events
        if event.get("status") == "complete"
    ]
    if phase_ids != expected_phases:
        raise RuntimeError(f"phase event chain differs: {phase_ids}")

    manifest = artifacts.validate_artifact_manifest(
        layout,
        complete.manifest_path,
    )
    validator_report = jsonio.load_json_object(
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    manifest_sha256 = _sha256_file(complete.manifest_path)
    if (
        validator_report.get("overall_status") != "pass"
        or validator_report.get("fresh_context") is not True
        or validator_report.get("manifest_sha256") != manifest_sha256
        or validator_report.get("validator_set_sha256")
        != manifest.get("validator_set_sha256")
    ):
        raise RuntimeError("fresh validator report is stale or not passing")
    journal = jsonio.load_json_object(
        layout.recovery_dir / "publish-transaction.json"
    )
    if journal.get("state") != "complete" or journal.get("postcheck_passed") is not True:
        raise RuntimeError("publish transaction is not complete")
    publication = deliverables.publication_paths(
        layout,
        str(journal["transaction_id"]),
    )
    run_staging = layout.root_staging_dir / run_id
    staging_clean = (
        not publication.staging_dir.exists()
        and (not run_staging.exists() or not any(run_staging.rglob("*")))
    )
    if not staging_clean:
        raise RuntimeError("fixed-root smoke left transaction staging content")

    delivery_sha256: dict[str, str] = {}
    for record in manifest["delivery_artifacts"]:
        relative = str(record["path"])
        delivery_path = layout.run_dir / Path(relative)
        digest = _sha256_file(delivery_path)
        if digest != record["sha256"]:
            raise RuntimeError(f"delivery hash differs from manifest: {relative}")
        delivery_sha256[delivery_path.name] = digest
    if set(delivery_sha256) != {
        "CrossFrame-Ultra-完整文章.md",
        "完整推演档案.md",
        "工件索引.md",
    }:
        raise RuntimeError("manifest does not bind the three fixed delivery files")

    latest_complete = indexes.IndexStore(layout.root).read_pointer(
        "latest-complete"
    )
    latest_complete_run_id = (
        None if latest_complete is None else latest_complete.get("run_id")
    )
    if latest_complete_run_id != run_id:
        raise RuntimeError("latest-complete does not point to the new smoke run")
    start_here_resolved = _start_here_resolves(layout)
    if not start_here_resolved:
        raise RuntimeError("START-HERE navigation does not resolve")

    run_relative = layout.run_dir.relative_to(layout.root / "runs").as_posix()
    existing_runs_after = _without_new_run(
        _existing_run_outputs(policy.test_root),
        run_relative=run_relative,
    )
    staging_after = {
        relative: digest
        for relative, digest in _snapshot_files(
            policy.test_root / ".staging"
        ).items()
        if not relative.startswith(run_id + "/")
    }
    existing_test_outputs_preserved = (
        existing_runs_after == existing_runs_before
        and staging_after == staging_before
    )
    if not existing_test_outputs_preserved:
        raise RuntimeError("pre-existing test-root outputs changed during smoke")

    production_after, production_after_sha = _production_surface(
        policy.production_root
    )
    if production_after != production_before:
        raise RuntimeError("production START-HERE or index surface changed during smoke")

    return {
        "run_id": run_id,
        "run_dir": str(layout.run_dir.resolve()),
        "test_root": str(layout.root.resolve()),
        "canonical_skill_root": str(
            (repo_root / "skills/crossframe-ultra").resolve()
        ),
        "status": final_status.status,
        "phase_ids": phase_ids,
        "phase_checkpoint_ids": phase_checkpoint_ids,
        "u12_checkpoint_content_sha256": checkpoint["content_sha256"],
        "pre_u12_official_absent": pre_u12_official_absent,
        "validator_overall_status": validator_report["overall_status"],
        "validator_fresh_context": validator_report["fresh_context"],
        "validator_attempt_id": validator_report["attempt_id"],
        "manifest_sha256": manifest_sha256,
        "manifest_official_delivery_published": manifest[
            "official_delivery_published"
        ],
        "publish_transaction_state": journal["state"],
        "delivery_sha256": delivery_sha256,
        "latest_complete_run_id": latest_complete_run_id,
        "start_here_resolved": start_here_resolved,
        "staging_clean": staging_clean,
        "existing_test_outputs_preserved": existing_test_outputs_preserved,
        "production_surface_before_sha256": production_before_sha,
        "production_surface_after_sha256": production_after_sha,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        print(
            "usage: python -B tests/run_ultra_fixed_root_smoke.py",
            file=sys.stderr,
        )
        return 2
    try:
        result = run_fixed_root_smoke()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ("main", "run_fixed_root_smoke")
