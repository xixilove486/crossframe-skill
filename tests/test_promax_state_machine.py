from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import warnings


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.errors import (
    CanonicalJSONError,
    JSONDocumentError,
    PhaseCASMismatch,
    PhaseHistoryError,
    PhaseLockBusy,
    PhaseParentHashError,
    PhaseReplayError,
    PhaseTransitionError,
    RunBindingError,
    StaleArtifactError,
)
from promax_runtime.jsonio import (
    canonical_json_bytes,
    load_json,
    load_jsonl,
    sha256_json,
)
from promax_runtime.state_machine import (
    PHASES,
    V8_SOURCE_SNAPSHOT_SHA256,
    PhaseState,
    RunBinding,
    append_phase_event,
    build_reset_event,
    downstream_phases,
    seal_phase_event,
    validate_phase_history,
)
import promax_runtime.state_machine as state_machine


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def valid_binding(**overrides: str) -> RunBinding:
    values = {
        "run_id": "promax-run-001",
        "run_nonce": "nonce-" + "7" * 42,
        "request_sha256": digest("frozen user request"),
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
    }
    values.update(overrides)
    return RunBinding(**values)


def empty_state(binding: RunBinding | None = None) -> PhaseState:
    return validate_phase_history([], expected_binding=binding or valid_binding())


def most_recent_artifact(state: PhaseState) -> dict[str, str]:
    if not state.completed_phases:
        return {}
    owner = state.completed_phases[-1]
    candidates = {
        path: value
        for path, value in state.active_artifact_hashes.items()
        if state.artifact_owner_phases[path] == owner
    }
    if not candidates:
        raise AssertionError(f"phase {owner} has no active output artifact")
    path = sorted(candidates)[0]
    return {path: candidates[path]}


def next_event(
    state: PhaseState,
    phase_id: str,
    *,
    output_label: str | None = None,
    input_artifact_hashes: dict[str, str] | None = None,
) -> dict[str, object]:
    return seal_phase_event(
        state,
        phase_id,
        input_artifact_hashes=(
            most_recent_artifact(state)
            if input_artifact_hashes is None
            else input_artifact_hashes
        ),
        output_artifact_hashes={
            f"artifacts/{phase_id.lower()}.json": digest(
                output_label or f"{phase_id}-output"
            )
        },
    )


def extend(
    events: list[dict[str, object]],
    event: dict[str, object],
    binding: RunBinding | None = None,
) -> PhaseState:
    events.append(event)
    return validate_phase_history(events, expected_binding=binding or valid_binding())


def rehash(event: dict[str, object]) -> dict[str, object]:
    mutated = copy.deepcopy(event)
    mutated.pop("event_sha256", None)
    mutated["event_sha256"] = sha256_json(mutated)
    return mutated


class ProMaxCanonicalJSONTests(unittest.TestCase):
    def test_canonical_json_is_utf8_compact_sorted_and_stable(self) -> None:
        value = {"z": [3, 2, 1], "a": "结构", "nested": {"b": True, "a": None}}
        expected = (
            '{"a":"结构","nested":{"a":null,"b":true},"z":[3,2,1]}'
        ).encode("utf-8")
        self.assertEqual(canonical_json_bytes(value), expected)
        self.assertEqual(sha256_json(value), hashlib.sha256(expected).hexdigest())

    def test_canonical_json_rejects_nonfinite_numbers_and_non_string_keys(self) -> None:
        for value in (
            {"value": float("nan")},
            {"value": float("inf")},
            {"value": float("-inf")},
            {1: "not a JSON object key"},
            {"value": "\ud800"},
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(CanonicalJSONError):
                    canonical_json_bytes(value)

    def test_json_loaders_reject_duplicate_keys_constants_and_blank_jsonl_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = root / "valid.json"
            valid.write_text('{"b":2,"a":1}\n', encoding="utf-8", newline="\n")
            self.assertEqual(load_json(valid), {"b": 2, "a": 1})

            duplicate = root / "duplicate.json"
            duplicate.write_text('{"a":1,"a":2}\n', encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(JSONDocumentError, "duplicate key"):
                load_json(duplicate)

            constant = root / "constant.json"
            constant.write_text('{"a":NaN}\n', encoding="utf-8", newline="\n")
            with self.assertRaises(JSONDocumentError):
                load_json(constant)

            lines = root / "events.jsonl"
            lines.write_text('{"a":1}\n\n{"b":2}\n', encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(JSONDocumentError, "blank JSONL record"):
                load_jsonl(lines)

    def test_jsonl_loader_requires_objects_and_a_complete_final_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_bytes(b'{"a":1}\n{"b":2}\n')
            self.assertEqual(load_jsonl(path), [{"a": 1}, {"b": 2}])

            path.write_bytes(b'{"a":1}\n[1,2]\n')
            with self.assertRaisesRegex(JSONDocumentError, "must be an object"):
                load_jsonl(path)

            path.write_bytes(b'{"a":1}')
            with self.assertRaisesRegex(JSONDocumentError, "newline"):
                load_jsonl(path)

    def test_jsonl_splits_only_lf_and_preserves_raw_unicode_line_separator(self) -> None:
        record = {"text": "before\u2028after"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            raw = canonical_json_bytes(record) + b"\n"
            self.assertIn("\u2028".encode("utf-8"), raw)
            path.write_bytes(raw)
            self.assertEqual(load_jsonl(path), [record])

    def test_json_loaders_reject_overflow_and_unpaired_surrogates_after_parse(self) -> None:
        invalid_documents = (
            b'{"nested":[1e9999]}\n',
            b'{"value":"\\ud800"}\n',
            b'{"\\udfff":"value"}\n',
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, raw in enumerate(invalid_documents):
                with self.subTest(index=index):
                    json_path = root / f"invalid-{index}.json"
                    jsonl_path = root / f"invalid-{index}.jsonl"
                    json_path.write_bytes(raw)
                    jsonl_path.write_bytes(raw)
                    with self.assertRaises(JSONDocumentError):
                        load_json(json_path)
                    with self.assertRaises(JSONDocumentError):
                        load_jsonl(jsonl_path)


class ProMaxPhaseStateTests(unittest.TestCase):
    def test_phase_inventory_and_downstream_boundaries_are_exact(self) -> None:
        self.assertEqual(PHASES, tuple(f"P{number}" for number in range(12)))
        self.assertEqual(downstream_phases("P0"), PHASES)
        self.assertEqual(downstream_phases("P7"), ("P7", "P8", "P9", "P10", "P11"))
        self.assertEqual(downstream_phases("P7", include_self=False), ("P8", "P9", "P10", "P11"))
        self.assertEqual(downstream_phases("P11"), ("P11",))
        with self.assertRaises(PhaseTransitionError):
            downstream_phases("P12")

    def test_empty_state_is_bound_and_exposes_immutable_structured_state(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        self.assertEqual(state.binding, binding)
        self.assertEqual(state.event_count, 0)
        self.assertIsNone(state.chain_head_sha256)
        self.assertEqual(state.completed_phases, ())
        self.assertEqual(dict(state.active_phase_hashes), {})
        self.assertEqual(dict(state.active_artifact_hashes), {})
        self.assertEqual(state.invalidated_phases, ())
        self.assertEqual(state.next_phase_id, "P0")
        with self.assertRaises(TypeError):
            state.active_phase_hashes["P0"] = "0" * 64

    def test_run_binding_rejects_weak_nonce_bad_hash_and_non_v8_source(self) -> None:
        invalid = (
            {"run_id": ""},
            {"run_nonce": "predictable"},
            {"request_sha256": "0" * 63},
            {"source_snapshot_sha256": "0" * 64},
        )
        for override in invalid:
            with self.subTest(override=override):
                with self.assertRaises(RunBindingError):
                    valid_binding(**override)

    def test_full_p0_through_p11_chain_has_exact_parent_and_event_links(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        events: list[dict[str, object]] = []

        for index, phase_id in enumerate(PHASES):
            event = next_event(state, phase_id)
            self.assertEqual(event["schema_id"], "crossframe.promax.v8.phase-event")
            self.assertEqual(event["event_index"], index)
            self.assertEqual(event["phase_id"], phase_id)
            self.assertEqual(event["previous_event_sha256"], state.chain_head_sha256)
            expected_parent = (
                None if index == 0 else state.active_phase_hashes[PHASES[index - 1]]
            )
            self.assertEqual(event["parent_phase_sha256"], expected_parent)
            self.assertEqual(
                event["input_phase_hashes"],
                {phase: state.active_phase_hashes[phase] for phase in PHASES[:index]},
            )
            state = extend(events, event, binding)

        self.assertEqual(state.completed_phases, PHASES)
        self.assertIsNone(state.next_phase_id)
        self.assertEqual(state.event_count, 12)
        self.assertEqual(state.chain_head_sha256, events[-1]["event_sha256"])

    def test_skipped_and_duplicate_phases_are_rejected_before_emission(self) -> None:
        state = empty_state()
        with self.assertRaisesRegex(PhaseTransitionError, "expected P0"):
            next_event(state, "P1")

        events: list[dict[str, object]] = []
        state = extend(events, next_event(state, "P0"))
        with self.assertRaisesRegex(PhaseTransitionError, "expected P1"):
            next_event(state, "P0", output_label="duplicate")

    def test_parent_hash_and_input_phase_lineage_are_independently_verified(self) -> None:
        binding = valid_binding()
        events: list[dict[str, object]] = []
        state = empty_state(binding)
        state = extend(events, next_event(state, "P0"), binding)
        event = next_event(state, "P1")

        wrong_parent = copy.deepcopy(event)
        wrong_parent["parent_phase_sha256"] = digest("wrong parent")
        wrong_parent = rehash(wrong_parent)
        with self.assertRaises(PhaseParentHashError):
            validate_phase_history([*events, wrong_parent], expected_binding=binding)

        wrong_lineage = copy.deepcopy(event)
        wrong_lineage["input_phase_hashes"]["P0"] = digest("stale P0")
        wrong_lineage = rehash(wrong_lineage)
        with self.assertRaises(StaleArtifactError):
            validate_phase_history([*events, wrong_lineage], expected_binding=binding)

    def test_schema_version_and_event_index_require_real_integers(self) -> None:
        binding = valid_binding()
        event = next_event(empty_state(binding), "P0")
        for field, replacement in (
            ("schema_version", 1.0),
            ("event_index", 0.0),
            ("schema_version", True),
            ("event_index", False),
        ):
            with self.subTest(field=field, replacement=replacement):
                forged = copy.deepcopy(event)
                forged[field] = replacement
                forged = rehash(forged)
                with self.assertRaises(PhaseHistoryError):
                    validate_phase_history([forged], expected_binding=binding)

    def test_binding_is_immutable_across_every_event(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        first = next_event(state, "P0")
        for field, replacement in (
            ("run_id", "other-run"),
            ("run_nonce", "other-" + "8" * 42),
            ("request_sha256", digest("other request")),
            ("source_snapshot_sha256", digest("not v8")),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(first)
                changed[field] = replacement
                changed = rehash(changed)
                with self.assertRaises((RunBindingError, PhaseHistoryError)):
                    validate_phase_history([changed], expected_binding=binding)

    def test_exact_reset_is_append_only_and_rerun_must_start_at_boundary(self) -> None:
        binding = valid_binding()
        events: list[dict[str, object]] = []
        state = empty_state(binding)
        for phase in PHASES[:5]:
            state = extend(events, next_event(state, phase), binding)
        old_event_bytes = canonical_json_bytes(events[3])

        reset = build_reset_event(state, "P3", reason="counterexample changes boundary")
        self.assertEqual(reset["previous_event_sha256"], state.chain_head_sha256)
        self.assertEqual(reset["invalidated_phases"], list(downstream_phases("P3")))
        self.assertEqual(reset["parent_phase_sha256"], state.active_phase_hashes["P2"])
        state = extend(events, reset, binding)

        self.assertEqual(canonical_json_bytes(events[3]), old_event_bytes)
        self.assertEqual(state.completed_phases, ("P0", "P1", "P2"))
        self.assertEqual(state.invalidated_phases, downstream_phases("P3"))
        self.assertEqual(state.next_phase_id, "P3")
        with self.assertRaisesRegex(PhaseTransitionError, "expected P3"):
            next_event(state, "P4", output_label="illegal skipped rerun")

        state = extend(events, next_event(state, "P3", output_label="P3-rerun"), binding)
        self.assertEqual(state.invalidated_phases, downstream_phases("P4"))
        state = extend(events, next_event(state, "P4", output_label="P4-rerun"), binding)
        self.assertEqual(state.invalidated_phases, downstream_phases("P5"))

    def test_reset_rejects_future_or_already_invalidated_boundary_and_forged_scope(self) -> None:
        binding = valid_binding()
        events: list[dict[str, object]] = []
        state = empty_state(binding)
        state = extend(events, next_event(state, "P0"), binding)

        with self.assertRaises(PhaseTransitionError):
            build_reset_event(state, "P1", reason="not completed")
        with self.assertRaises(PhaseTransitionError):
            build_reset_event(state, "P0", reason="")

        reset = build_reset_event(state, "P0", reason="request correction")
        forged = copy.deepcopy(reset)
        forged["invalidated_phases"] = ["P0", "P1"]
        forged = rehash(forged)
        with self.assertRaises(PhaseTransitionError):
            validate_phase_history([*events, forged], expected_binding=binding)

        state = extend(events, reset, binding)
        with self.assertRaises(PhaseTransitionError):
            build_reset_event(state, "P0", reason="already reset")

    def test_rerun_rejects_stale_artifact_hash_from_invalidated_generation(self) -> None:
        binding = valid_binding()
        events: list[dict[str, object]] = []
        state = empty_state(binding)
        state = extend(events, next_event(state, "P0", output_label="old P0"), binding)
        old_p0_artifact = most_recent_artifact(state)
        state = extend(
            events,
            build_reset_event(state, "P0", reason="request was materially corrected"),
            binding,
        )
        state = extend(events, next_event(state, "P0", output_label="new P0"), binding)

        with self.assertRaises(StaleArtifactError):
            next_event(
                state,
                "P1",
                output_label="P1 reading stale P0",
                input_artifact_hashes=old_p0_artifact,
            )

    def test_replayed_event_and_artifact_overwrite_are_rejected(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        first = next_event(state, "P0")
        state = validate_phase_history([first], expected_binding=binding)

        with self.assertRaises(PhaseReplayError):
            validate_phase_history([first, first], expected_binding=binding)

        active_path = next(iter(state.active_artifact_hashes))
        with self.assertRaises(PhaseTransitionError):
            seal_phase_event(
                state,
                "P1",
                input_artifact_hashes=most_recent_artifact(state),
                output_artifact_hashes={active_path: digest("overwrite")},
            )

        with self.assertRaises(PhaseTransitionError):
            seal_phase_event(
                state,
                "P1",
                input_artifact_hashes=most_recent_artifact(state),
                output_artifact_hashes={active_path.upper(): digest("case alias")},
            )

    def test_artifact_paths_must_have_one_unambiguous_posix_spelling(self) -> None:
        state = empty_state()
        for path in (
            ".",
            "./artifacts/p0.json",
            "artifacts/./p0.json",
            "artifacts//p0.json",
            "artifacts/p0.json/.",
            "C:relative.json",
            "artifacts/file.json:ads",
            "artifacts/bad?.json",
            "artifacts/bad*.json",
            "artifacts/bad|name.json",
            "artifacts/bad<name>.json",
            'artifacts/bad"name.json',
            "artifacts/delete\x7f.json",
            "artifacts/line\u2028separator.json",
            "artifacts/zero\u200bwidth.json",
            "artifacts/CON.json",
            "artifacts/com1.txt",
            "artifacts/e\u0301.json",
            "artifacts/trailing-dot.",
            "artifacts/trailing-space ",
            "artifacts/directory./p0.json",
            "artifacts/directory /p0.json",
        ):
            with self.subTest(path=path):
                with self.assertRaises(PhaseTransitionError):
                    seal_phase_event(
                        state,
                        "P0",
                        input_artifact_hashes={},
                        output_artifact_hashes={path: digest(path)},
                    )

    def test_runtime_artifact_interface_cannot_request_or_emit_hidden_cot(self) -> None:
        state = empty_state()
        forbidden_paths = (
            "artifacts/chain-of-thought.md",
            "artifacts/hidden_reasoning.json",
            "scratchpad/internal-monologue.txt",
        )
        for path in forbidden_paths:
            with self.subTest(path=path):
                with self.assertRaises(PhaseTransitionError):
                    seal_phase_event(
                        state,
                        "P0",
                        input_artifact_hashes={},
                        output_artifact_hashes={path: digest(path)},
                    )


class ProMaxAppendOnlyEventLogTests(unittest.TestCase):
    def test_append_writes_one_canonical_record_and_returns_validated_state(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        event = next_event(state, "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            result = append_phase_event(path, event, expected_head_sha256=None)

            self.assertEqual(path.read_bytes(), canonical_json_bytes(event) + b"\n")
            self.assertEqual(result.chain_head_sha256, event["event_sha256"])
            self.assertEqual(result.binding, binding)
            self.assertTrue(path.with_name(f".{path.name}.lock").is_file())

    def test_expected_head_cas_failure_preserves_every_existing_byte(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        first = next_event(state, "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            state = append_phase_event(path, first, expected_head_sha256=None)
            second = next_event(state, "P1")
            before = path.read_bytes()

            with self.assertRaises(PhaseCASMismatch):
                append_phase_event(
                    path,
                    second,
                    expected_head_sha256=digest("stale expected head"),
                )
            self.assertEqual(path.read_bytes(), before)

    def test_invalid_or_replayed_candidate_preserves_every_existing_byte(self) -> None:
        binding = valid_binding()
        first = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            state = append_phase_event(path, first, expected_head_sha256=None)
            before = path.read_bytes()

            for candidate in (first, {**next_event(state, "P1"), "event_sha256": "0" * 64}):
                with self.subTest(candidate=candidate["phase_id"]):
                    with self.assertRaises(PhaseHistoryError):
                        append_phase_event(
                            path,
                            candidate,
                            expected_head_sha256=state.chain_head_sha256,
                        )
                    self.assertEqual(path.read_bytes(), before)

    def test_exclusive_sidecar_lock_failure_preserves_event_log(self) -> None:
        binding = valid_binding()
        event = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            path.write_bytes(b"")
            before = path.read_bytes()
            held = state_machine._acquire_event_lock(
                path.with_name(f".{path.name}.lock")
            )
            try:
                with self.assertRaises(PhaseLockBusy):
                    append_phase_event(path, event, expected_head_sha256=None)
                self.assertEqual(path.read_bytes(), before)
            finally:
                state_machine._release_event_lock(held)

    def test_unlock_warning_policy_cannot_prevent_close_from_releasing_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / ".promax-phase-events.jsonl.lock"
            held = state_machine._acquire_event_lock(lock_path)
            with mock.patch.object(
                state_machine,
                "_unlock_event_file",
                side_effect=OSError("injected explicit unlock failure"),
            ):
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    state_machine._release_event_lock(held)

            replacement = state_machine._acquire_event_lock(lock_path)
            state_machine._release_event_lock(replacement)

    def test_tampered_existing_log_is_never_repaired_by_appending(self) -> None:
        binding = valid_binding()
        event = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            path.write_bytes(b'{"truncated":true}')
            before = path.read_bytes()

            with self.assertRaises(JSONDocumentError):
                append_phase_event(path, event, expected_head_sha256=None)
            self.assertEqual(path.read_bytes(), before)

    def test_semantically_equal_noncanonical_log_rewrite_is_rejected(self) -> None:
        binding = valid_binding()
        first = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            state = append_phase_event(path, first, expected_head_sha256=None)
            second = next_event(state, "P1")
            canonical = path.read_bytes()
            rewritten = canonical.replace(b"{", b"{ ", 1)
            self.assertNotEqual(rewritten, canonical)
            path.write_bytes(rewritten)

            with self.assertRaisesRegex(JSONDocumentError, "canonical"):
                append_phase_event(
                    path,
                    second,
                    expected_head_sha256=state.chain_head_sha256,
                )
            self.assertEqual(path.read_bytes(), rewritten)

    def test_failed_durable_append_rolls_back_to_the_exact_original_bytes(self) -> None:
        binding = valid_binding()
        state = empty_state(binding)
        first = next_event(state, "P0")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "promax-phase-events.jsonl"
            state = append_phase_event(path, first, expected_head_sha256=None)
            second = next_event(state, "P1")
            before = path.read_bytes()
            lock_path = path.with_name(f".{path.name}.lock")
            self.assertEqual(lock_path.read_bytes(), b"\x00")

            fsync_calls: list[int] = []

            def fail_append_sync_then_allow_rollback(descriptor: int) -> None:
                fsync_calls.append(descriptor)
                if len(fsync_calls) == 1:
                    raise OSError("injected append durability failure")

            with mock.patch.object(
                state_machine.os,
                "fsync",
                side_effect=fail_append_sync_then_allow_rollback,
            ):
                with self.assertRaises(PhaseHistoryError):
                    append_phase_event(
                        path,
                        second,
                        expected_head_sha256=state.chain_head_sha256,
                    )
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(fsync_calls), 2, "rollback must itself be fsynced")

    def test_first_log_creation_syncs_parent_and_directory_failure_is_rolled_back(self) -> None:
        binding = valid_binding()
        event = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "promax-phase-events.jsonl"
            lock_path = path.with_name(f".{path.name}.lock")
            lock_path.write_bytes(b"\x00")

            with mock.patch.object(
                state_machine,
                "_fsync_directory",
                return_value=True,
            ) as sync_directory:
                append_phase_event(path, event, expected_head_sha256=None)
            sync_directory.assert_called_once_with(root)

            path.unlink()
            calls = 0

            def fail_commit_then_allow_unlink_sync(_directory: Path) -> bool:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise OSError("injected parent directory sync failure")
                return True

            with mock.patch.object(
                state_machine,
                "_fsync_directory",
                side_effect=fail_commit_then_allow_unlink_sync,
            ):
                with self.assertRaises(PhaseHistoryError):
                    append_phase_event(path, event, expected_head_sha256=None)
            self.assertFalse(path.exists())
            self.assertEqual(calls, 2, "failed create must durably sync its unlink")

    def test_hardlinked_event_log_aliases_are_rejected_without_any_append(self) -> None:
        binding = valid_binding()
        first = next_event(empty_state(binding), "P0")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "promax-phase-events.jsonl"
            state = append_phase_event(original, first, expected_head_sha256=None)
            alias_parent = root / "alias"
            alias_parent.mkdir()
            alias = alias_parent / "promax-phase-events.jsonl"
            try:
                os.link(original, alias)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")
            self.assertTrue(os.path.samefile(original, alias))
            self.assertGreaterEqual(original.stat().st_nlink, 2)
            second = next_event(state, "P1")
            before = original.read_bytes()

            for path in (original, alias):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(PhaseHistoryError, "hardlink"):
                        append_phase_event(
                            path,
                            second,
                            expected_head_sha256=state.chain_head_sha256,
                        )
                    self.assertEqual(original.read_bytes(), before)
                    self.assertEqual(alias.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
