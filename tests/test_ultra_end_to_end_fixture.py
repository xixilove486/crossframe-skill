from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
TEMPLATE_DIR = REPO_ROOT / "skills/crossframe-ultra/templates"
RUN_ID = "20260802T000000Z-0123456789ab"

TEMPLATE_MARKERS = {
    "ultra-run-status-output.md": ("run_id", "phase", "validation", "continuation"),
    "ultra-world-volume-output.md": ("boundary", "node", "channel", "clock"),
    "ultra-transformation-ledger-output.md": ("rule", "effect", "provenance"),
    "ultra-concept-disposition-output.md": ("concept", "disposition", "justification"),
    "ultra-claim-mechanism-output.md": ("claim", "mechanism", "edge", "unknown"),
    "ultra-recursive-state-output.md": ("node", "parent", "state", "channel"),
    "ultra-recursive-lineage-output.md": ("lineage", "parent", "order-2", "order-3"),
    "ultra-order-evaluation-output.md": ("order-2", "reversal", "order-3", "lock-in"),
    "ultra-retrieval-output.md": ("query", "source", "result", "cutoff"),
    "ultra-red-team-output.md": ("rival", "counter", "residual", "confidence"),
    "ultra-verdict-output.md": ("fact", "prediction", "value", "responsibility", "authorization"),
    "ultra-action-ranking-output.md": ("action", "rank", "constraint", "indicator"),
    "ultra-forecast-output.md": ("forecast", "indicator", "window", "resolution"),
    "ultra-framework-gap-output.md": ("gap", "framework", "boundary", "disposition"),
    "ultra-dossier-output.md": ("推演", "证据", "机制", "撤回条件"),
    "ultra-artifact-index-output.md": ("artifact", "sha256", "phase", "path"),
    "ultra-validator-report-output.md": ("validator", "manifest", "passed", "error"),
    "ultra-repair-plan-output.md": ("attempt", "repair", "reset", "bounded"),
}

CLOSED_ORGANIZATION_CASE = {
    "case_id": "org-delay-multiparent",
    "material_closed": True,
    "parents": ["care-constraint", "incentive-system", "resource-allocation"],
    "channels": [
        {"channel_id": "formal-schedule", "clock": "weekly", "latency_days": 2},
        {"channel_id": "care-load", "clock": "event-driven", "latency_days": 11},
    ],
    "order_2": {
        "effect": "reversal",
        "condition": "formal escalation increases hidden care-load displacement",
    },
    "order_3": {
        "effect": "lock-in",
        "condition": "promotion metrics reward the escalation pattern",
    },
    "rival": {
        "explanation_id": "individual-execution-deficit",
        "confidence": "low",
    },
    "verdict_kinds": [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ],
}


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"ultra_runtime.{name}")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)


class RecordingPhaseStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = [
            (phase, (phase.lower() * 32)[:64]) for phase in ("U0", "U1", "U2", "U3")
        ]

    def complete(self, phase_id: str, *, artifact_hashes, **kwargs):
        digests = tuple(artifact_hashes)
        assert digests and all(len(digest) == 64 for digest in digests)
        self.calls.append((phase_id, digests))
        return {
            "phase_id": phase_id,
            "event_sha256": (phase_id.lower() * 32)[:64],
            "artifact_hashes": list(digests),
        }


def test_all_eighteen_task13_templates_exist_and_freeze_semantic_fields() -> None:
    assert len(TEMPLATE_MARKERS) == 18
    for filename, markers in TEMPLATE_MARKERS.items():
        path = TEMPLATE_DIR / filename
        assert path.is_file(), path
        raw = path.read_bytes()
        assert raw.endswith(b"\n")
        assert b"\r\n" not in raw
        text = raw.decode("utf-8").casefold()
        assert text.startswith("# ")
        for marker in markers:
            assert marker.casefold() in text, f"{filename}: missing {marker}"


def test_closed_fixture_contract_has_the_required_structural_stressors() -> None:
    case = CLOSED_ORGANIZATION_CASE
    assert case["material_closed"] is True
    assert len(case["parents"]) >= 2
    assert len(case["channels"]) == 2
    assert len({channel["clock"] for channel in case["channels"]}) == 2
    assert case["order_2"]["effect"] == "reversal"
    assert case["order_3"]["effect"] == "lock-in"
    assert case["rival"]["confidence"] == "low"
    assert case["verdict_kinds"] == [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ]


def test_full_fixture_records_u0_u12_once_and_packet_checkpoints_are_not_phase_events(
    tmp_path: Path
) -> None:
    materialization_path = RUNTIME_DIR / "materialization.py"
    delivery_path = RUNTIME_DIR / "deliverables.py"
    if not materialization_path.is_file() or not delivery_path.is_file():
        pytest.skip("Task 13 materialization boundary is not implemented")
    materialization = _module("materialization")
    deliverables = _module("deliverables")
    paths = _module("paths")
    layout = _layout(paths, tmp_path)
    prepared = materialization.prepare_authoring(layout)
    store = RecordingPhaseStore()
    base_time = datetime(2026, 8, 2, tzinfo=timezone.utc)

    phase_files = {
        "U4": ["U04-world-volume.json"],
        "U5": ["U05-transformation-ledger.json", "U05-concept-disposition.json"],
        "U6": ["U06-claim-mechanism-graph.json"],
        "U7": ["U07-recursive-states/node-a.json", "U07-recursive-lineage.json"],
        "U8": ["U08-order-evaluation.json", "U08-red-team-report.json"],
        "U9": ["U09-verdict.json", "U09-action-ranking.json", "U09-forecast-ledger.json"],
        "U10": ["U10-framework-gap-ledger.json", "U10-output-plan.json"],
    }
    for phase, relatives in phase_files.items():
        artifact_paths: list[Path] = []
        for ordinal, relative in enumerate(relatives, start=1):
            target = prepared.authoring_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(
                    {
                        "case": CLOSED_ORGANIZATION_CASE,
                        "phase": phase,
                        "ordinal": ordinal,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            artifact_paths.append(target)
        materialization.record_materialized_phase(
            layout,
            store,
            phase,
            artifact_paths,
        )

    packet_paths = []
    for ordinal in range(1, 4):
        packet = layout.authoring_dir / "article/packets" / f"packet-{ordinal:02d}.md"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(f"## packet {ordinal}\n\ncase material\n", encoding="utf-8")
        packet_paths.append(packet)
    checkpoints: list[tuple[str, int, tuple[Path, ...]]] = []
    before_packet_events = tuple(store.calls)
    materialization.checkpoint_article_packets(
        layout,
        store,
        packet_paths,
        now=base_time,
        create_checkpoint=lambda layout, phase_store, **kwargs: checkpoints.append(
            (
                kwargs["boundary_id"],
                kwargs["boundary_ordinal"],
                tuple(kwargs["artifact_paths"]),
            )
        ),
    )
    assert store.calls == list(before_packet_events)
    assert [ordinal for _, ordinal, _ in checkpoints] == [1, 2, 3]

    u11_paths = (
        layout.authoring_dir / "U11-semantic-coverage.json",
        layout.authoring_dir / "U11-article-review.json",
        layout.authoring_dir / "article.partial.md",
        layout.authoring_dir / "完整推演档案.md",
        layout.artifacts_dir / "ultra-artifact-index.md",
    )
    for ordinal, target in enumerate(u11_paths, start=1):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"U11 fixture artifact {ordinal}\n", encoding="utf-8")
    materialization.record_materialized_phase(
        layout,
        store,
        "U11",
        u11_paths,
    )

    article = "# 完整文章\n\n组织激励与照护约束共同导致延期。\n".encode("utf-8")
    dossier = (layout.authoring_dir / "完整推演档案.md").read_bytes()
    index = "# 工件索引\n\nU0-U12\n".encode("utf-8")
    manifest = b'{"fixture":"manifest"}\n'
    publication = deliverables.publish_delivery(
        layout,
        transaction_id="20260802T000100Z-bbbbbbbbbbbb",
        article_bytes=article,
        dossier_bytes=dossier,
        artifact_index_bytes=index,
        manifest_bytes=manifest,
        fresh_check=lambda stage: (
            f'{{"overall_status":"pass","stage":"{stage}"}}\n'.encode("utf-8")
        ),
        commit_report=lambda stage, report: None,
        mark_needs_attention=lambda reason: pytest.fail(reason),
    )
    postcheck_report_path = (
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    postcheck_report_path.parent.mkdir(parents=True, exist_ok=True)
    postcheck_report_path.write_bytes(publication.postcheck_report_bytes)
    materialization.complete_u12(
        layout,
        store,
        manifest_path=publication.paths.manifest_path,
        postcheck_report_path=postcheck_report_path,
        delivery_paths=(
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        ),
        postcheck_passed=publication.postcheck_passed,
    )

    assert [phase for phase, _ in store.calls] == [f"U{number}" for number in range(13)]
    assert store.calls[-1][1] == tuple(
        __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        for path in (
            publication.paths.manifest_path,
            postcheck_report_path,
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        )
    )
    assert not (layout.authoring_dir / "U09-forecast-resolution.json").exists()
    assert publication.paths.article_path.is_file()
    assert publication.paths.dossier_path.is_file()
    assert publication.paths.artifact_index_path.is_file()
