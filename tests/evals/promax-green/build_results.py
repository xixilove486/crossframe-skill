from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_EVAL_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(DEFAULT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_REPO_ROOT))

from tests.test_promax_green_eval import (  # noqa: E402
    canonical_skill_tree_sha256,
    load_artifact_semantics,
    metric_passes,
    sha256_bytes,
    sha256_json,
)


HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class GreenBuildError(ValueError):
    """Raised when committed GREEN evidence cannot support canonical results."""


def _json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GreenBuildError(f"cannot load {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise GreenBuildError(f"{label} must be a JSON object: {path}")
    return value


def _json_array(path: Path, *, label: str) -> list[Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GreenBuildError(f"cannot load {label} {path}: {error}") from error
    if not isinstance(value, list):
        raise GreenBuildError(f"{label} must be a JSON array: {path}")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GreenBuildError(f"{field} must be non-empty text")
    return value


def _sha256(value: object, *, field: str) -> str:
    digest = _text(value, field=field)
    if not HASH_PATTERN.fullmatch(digest):
        raise GreenBuildError(f"{field} must be lowercase SHA-256 text")
    return digest


def _evaluated_skill_tree_sha256(evaluation: Path) -> str:
    declaration_path = evaluation / "evaluated-skill-tree.json"
    if not declaration_path.is_file():
        return canonical_skill_tree_sha256()
    declaration = _json_object(
        declaration_path,
        label="GREEN evaluated skill tree declaration",
    )
    if set(declaration) != {
        "schema_id",
        "schema_version",
        "evaluated_skill_tree_sha256",
        "current_release_compatibility",
    }:
        raise GreenBuildError(
            "evaluated skill tree declaration has unexpected fields"
        )
    if (
        declaration.get("schema_id")
        != "crossframe.promax.green-evaluated-skill-tree"
        or declaration.get("schema_version") != 1
    ):
        raise GreenBuildError("evaluated skill tree declaration identity mismatch")
    compatibility = declaration.get("current_release_compatibility")
    if not isinstance(compatibility, dict) or set(compatibility) != {
        "scope",
        "changed_paths",
        "deterministic_tests",
    }:
        raise GreenBuildError(
            "evaluated skill tree compatibility record is malformed"
        )
    if compatibility.get("scope") != "activation-boundary-only":
        raise GreenBuildError(
            "evaluated skill tree compatibility scope is unsupported"
        )
    for field in ("changed_paths", "deterministic_tests"):
        values = compatibility.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or len(set(values)) != len(values)
        ):
            raise GreenBuildError(
                f"evaluated skill tree compatibility {field} must be unique text"
            )
    return _sha256(
        declaration.get("evaluated_skill_tree_sha256"),
        field="evaluated_skill_tree_sha256",
    )


def _repo_relative_path(
    value: object,
    *,
    repo_root: Path,
    field: str,
) -> tuple[str, Path]:
    text = _text(value, field=field)
    relative = Path(text)
    if relative.is_absolute():
        raise GreenBuildError(f"{field} must be repository-relative")
    resolved = (repo_root / relative).resolve()
    try:
        canonical = resolved.relative_to(repo_root).as_posix()
    except ValueError as error:
        raise GreenBuildError(f"{field} escapes the repository") from error
    if text != canonical:
        raise GreenBuildError(
            f"{field} must use its canonical repository-relative POSIX path"
        )
    return canonical, resolved


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def artifact_tree_sha256(root: Path) -> str:
    if not root.is_dir():
        raise GreenBuildError(f"artifact_dir is not a directory: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise GreenBuildError(f"artifact tree contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _scenario_records(
    scenarios_path: Path,
    *,
    rubric_scenario_ids: list[str],
) -> dict[str, dict[str, Any]]:
    raw_records = _json_array(scenarios_path, label="GREEN scenario manifest")
    records: dict[str, dict[str, Any]] = {}
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, dict):
            raise GreenBuildError(f"scenario[{index}] must be an object")
        scenario_id = _text(raw_record.get("id"), field=f"scenario[{index}].id")
        if scenario_id in records:
            raise GreenBuildError(f"duplicate scenario ID: {scenario_id}")
        for field in ("prompt", "executed_prompt", "context", "raw_output_path"):
            _text(raw_record.get(field), field=f"scenario[{scenario_id}].{field}")
        tags = raw_record.get("tags")
        if (
            not isinstance(tags, list)
            or not tags
            or any(not isinstance(tag, str) or not tag.strip() for tag in tags)
        ):
            raise GreenBuildError(
                f"scenario[{scenario_id}].tags must be non-empty text entries"
            )
        records[scenario_id] = raw_record
    if list(records) != rubric_scenario_ids:
        raise GreenBuildError(
            "scenario manifest IDs/order do not match rubric.scenario_ids"
        )
    return records


def _metric_rubrics(rubric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_metrics = rubric.get("metrics")
    if not isinstance(raw_metrics, list) or not raw_metrics:
        raise GreenBuildError("rubric.metrics must be a non-empty array")
    metrics: dict[str, dict[str, Any]] = {}
    for index, raw_metric in enumerate(raw_metrics):
        if not isinstance(raw_metric, dict):
            raise GreenBuildError(f"rubric.metrics[{index}] must be an object")
        metric_id = _text(
            raw_metric.get("metric_id"),
            field=f"rubric.metrics[{index}].metric_id",
        )
        if metric_id in metrics:
            raise GreenBuildError(f"duplicate rubric metric ID: {metric_id}")
        direction = raw_metric.get("direction")
        if direction not in {"minimum", "maximum"}:
            raise GreenBuildError(f"{metric_id} has an invalid direction")
        threshold = raw_metric.get("threshold")
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise GreenBuildError(f"{metric_id} threshold must be numeric")
        applicable = raw_metric.get("applicable_scenarios")
        if applicable != "all" and (
            not isinstance(applicable, list)
            or not applicable
            or any(not isinstance(item, str) for item in applicable)
        ):
            raise GreenBuildError(
                f"{metric_id} applicable_scenarios must be 'all' or an ID list"
            )
        metrics[metric_id] = raw_metric
    return metrics


def _metric_is_applicable(metric: dict[str, Any], scenario_id: str) -> bool:
    scope = metric["applicable_scenarios"]
    return scope == "all" or scenario_id in scope


def _run_matrix(
    rubric: dict[str, Any],
    *,
    models: list[str],
    scenario_ids: list[str],
) -> list[tuple[str, str]]:
    raw_matrix = rubric.get("run_matrix")
    if not isinstance(raw_matrix, list) or not raw_matrix:
        raise GreenBuildError("rubric.run_matrix must be a non-empty array")
    matrix: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, raw_entry in enumerate(raw_matrix):
        field = f"rubric.run_matrix[{index}]"
        if not isinstance(raw_entry, dict):
            raise GreenBuildError(f"{field} must be an object")
        if set(raw_entry) != {"model_id", "scenario_id"}:
            raise GreenBuildError(
                f"{field} must contain exactly model_id and scenario_id"
            )
        model_id = _text(raw_entry.get("model_id"), field=f"{field}.model_id")
        scenario_id = _text(
            raw_entry.get("scenario_id"),
            field=f"{field}.scenario_id",
        )
        if model_id not in models:
            raise GreenBuildError(f"{field}.model_id is not in rubric.models")
        if scenario_id not in scenario_ids:
            raise GreenBuildError(
                f"{field}.scenario_id is not in rubric.scenario_ids"
            )
        pair = (model_id, scenario_id)
        if pair in seen_pairs:
            raise GreenBuildError(
                f"duplicate run_matrix pair: {model_id}/{scenario_id}"
            )
        seen_pairs.add(pair)
        matrix.append(pair)
    return matrix


def _evidence_records(
    value: object,
    *,
    field: str,
    repo_root: Path,
    raw_path: Path,
    artifact_dir: Path,
    rubric_path: Path,
    scenarios_path: Path,
) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise GreenBuildError(f"{field} must contain at least one evidence record")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_record in enumerate(value):
        if not isinstance(raw_record, dict):
            raise GreenBuildError(f"{field}[{index}] must be an object")
        path_text, path = _repo_relative_path(
            raw_record.get("path"),
            repo_root=repo_root,
            field=f"{field}[{index}].path",
        )
        allowed = (
            path == raw_path
            or path == rubric_path
            or path == scenarios_path
            or _is_within(path, artifact_dir)
        )
        if not allowed:
            raise GreenBuildError(
                f"{field}[{index}].path is outside this run's auditable evidence"
            )
        if not path.is_file():
            raise GreenBuildError(f"{field}[{index}].path is not a committed file")
        expected_hash = _sha256(
            raw_record.get("sha256"),
            field=f"{field}[{index}].sha256",
        )
        actual_hash = sha256_bytes(path.read_bytes())
        if expected_hash != actual_hash:
            raise GreenBuildError(
                f"{field} metric evidence SHA-256 does not match {path_text}"
            )
        finding = _text(
            raw_record.get("finding"),
            field=f"{field}[{index}].finding",
        )
        identity = (path_text, finding)
        if identity in seen:
            raise GreenBuildError(f"{field} repeats an evidence record")
        seen.add(identity)
        normalized.append(
            {
                "path": path_text,
                "sha256": actual_hash,
                "finding": finding,
            }
        )
    return normalized


def _optional_failing_artifacts(
    value: object,
    *,
    field: str,
    repo_root: Path,
    raw_path: Path,
    artifact_dir: Path,
    rubric_path: Path,
    scenarios_path: Path,
) -> list[dict[str, str]]:
    if value == []:
        return []
    return _evidence_records(
        value,
        field=field,
        repo_root=repo_root,
        raw_path=raw_path,
        artifact_dir=artifact_dir,
        rubric_path=rubric_path,
        scenarios_path=scenarios_path,
    )


def _canonical_metric_record(
    raw_record: object,
    *,
    rubric_metric: dict[str, Any],
    scenario_id: str,
    model_id: str,
    repo_root: Path,
    raw_path: Path,
    artifact_dir: Path,
    rubric_path: Path,
    scenarios_path: Path,
) -> dict[str, Any]:
    metric_id = rubric_metric["metric_id"]
    label = f"{model_id}/{scenario_id}/{metric_id}"
    if not isinstance(raw_record, dict):
        raise GreenBuildError(f"metric record {label} must be an object")
    if "metric_id" in raw_record and raw_record["metric_id"] != metric_id:
        raise GreenBuildError(f"metric record {label} has the wrong metric_id")
    applicable = _metric_is_applicable(rubric_metric, scenario_id)
    if raw_record.get("applicable") is not applicable:
        raise GreenBuildError(f"metric record {label} has wrong applicability")
    direction = rubric_metric["direction"]
    threshold = rubric_metric["threshold"]
    if "direction" in raw_record and raw_record["direction"] != direction:
        raise GreenBuildError(f"metric record {label} has the wrong direction")
    if "threshold" in raw_record and raw_record["threshold"] != threshold:
        raise GreenBuildError(f"metric record {label} has the wrong threshold")
    numerator = raw_record.get("numerator")
    if isinstance(numerator, bool) or numerator not in {0, 1}:
        raise GreenBuildError(f"metric record {label} numerator must be 0 or 1")
    denominator = int(applicable)
    if raw_record.get("denominator") != denominator:
        raise GreenBuildError(f"metric record {label} has the wrong denominator")
    if not applicable and numerator != 0:
        raise GreenBuildError(
            f"metric record {label} must use zero for an inapplicable numerator"
        )
    passed = (
        True
        if not applicable
        else metric_passes(direction, numerator, denominator, threshold)
    )
    if "passed" in raw_record and raw_record["passed"] is not passed:
        raise GreenBuildError(f"metric record {label} has a false pass claim")
    evidence = _evidence_records(
        raw_record.get("evidence"),
        field=f"metric record {label}.evidence",
        repo_root=repo_root,
        raw_path=raw_path,
        artifact_dir=artifact_dir,
        rubric_path=rubric_path,
        scenarios_path=scenarios_path,
    )
    failing_artifacts = _optional_failing_artifacts(
        raw_record.get("failing_artifacts"),
        field=f"metric record {label}.failing_artifacts",
        repo_root=repo_root,
        raw_path=raw_path,
        artifact_dir=artifact_dir,
        rubric_path=rubric_path,
        scenarios_path=scenarios_path,
    )
    if passed and failing_artifacts:
        raise GreenBuildError(
            f"metric record {label} passed but lists failing artifacts"
        )
    if not passed and not failing_artifacts:
        raise GreenBuildError(
            f"metric record {label} failed without a failing artifact"
        )
    canonical = {
        "applicable": applicable,
        "direction": direction,
        "threshold": threshold,
        "passed": passed,
        "numerator": numerator,
        "denominator": denominator,
        "evidence": evidence,
        "failing_artifacts": failing_artifacts,
    }
    if not passed:
        raise GreenBuildError(f"failed metric {label}")
    return canonical


def _canonical_run(
    metadata_path: Path,
    *,
    model_id: str,
    scenario_id: str,
    scenario: dict[str, Any],
    metric_rubrics: dict[str, dict[str, Any]],
    repo_root: Path,
    eval_root: Path,
    rubric_path: Path,
    scenarios_path: Path,
    skill_tree_sha256: str,
) -> dict[str, Any]:
    if not metadata_path.is_file():
        raise GreenBuildError(
            f"missing eval metadata for {model_id}/{scenario_id}: {metadata_path}"
        )
    metadata = _json_object(metadata_path, label="GREEN eval metadata")
    if metadata.get("schema_id") != "crossframe.promax.green-run-metadata":
        raise GreenBuildError(
            f"{model_id}/{scenario_id} has the wrong metadata schema_id"
        )
    if metadata.get("schema_version") != 1:
        raise GreenBuildError(
            f"{model_id}/{scenario_id} has the wrong metadata schema_version"
        )
    if metadata.get("model_id") != model_id:
        raise GreenBuildError(f"{model_id}/{scenario_id} metadata model mismatch")
    if metadata.get("scenario_id") != scenario_id:
        raise GreenBuildError(f"{model_id}/{scenario_id} metadata scenario mismatch")
    run_id = _text(
        metadata.get("run_id"),
        field=f"{model_id}/{scenario_id}.run_id",
    )
    if metadata.get("fresh_context") is not True:
        raise GreenBuildError(f"{model_id}/{scenario_id} is not a fresh context")
    if metadata.get("skill_loaded") is not True:
        raise GreenBuildError(f"{model_id}/{scenario_id} did not load ProMax")
    executed_prompt = _text(
        metadata.get("executed_prompt"),
        field=f"{model_id}/{scenario_id}.executed_prompt",
    )
    if executed_prompt != scenario["executed_prompt"]:
        raise GreenBuildError(
            f"{model_id}/{scenario_id} executed prompt differs from scenarios.json"
        )
    prompt_sha256 = sha256_bytes(executed_prompt.encode("utf-8"))
    if metadata.get("prompt_sha256") != prompt_sha256:
        raise GreenBuildError(f"{model_id}/{scenario_id} prompt SHA-256 mismatch")
    if metadata.get("skill_tree_sha256") != skill_tree_sha256:
        raise GreenBuildError(f"{model_id}/{scenario_id} skill tree SHA-256 mismatch")
    tool_availability = metadata.get("tool_availability")
    if (
        not isinstance(tool_availability, dict)
        or not tool_availability
        or any(
            not isinstance(key, str) or type(value) is not bool
            for key, value in tool_availability.items()
        )
    ):
        raise GreenBuildError(
            f"{model_id}/{scenario_id}.tool_availability must be a boolean map"
        )

    expected_raw_text = scenario["raw_output_path"].format(model_id=model_id)
    raw_text, raw_path = _repo_relative_path(
        metadata.get("raw_output_path"),
        repo_root=repo_root,
        field=f"{model_id}/{scenario_id}.raw_output_path",
    )
    if raw_text != expected_raw_text:
        raise GreenBuildError(
            f"{model_id}/{scenario_id} raw output path differs from scenarios.json"
        )
    if not raw_path.is_file():
        raise GreenBuildError(f"missing raw output for {model_id}/{scenario_id}")
    raw_sha256 = sha256_bytes(raw_path.read_bytes())
    if metadata.get("raw_output_sha256") != raw_sha256:
        raise GreenBuildError(f"{model_id}/{scenario_id} raw output SHA-256 mismatch")

    bundle_root = eval_root / "artifacts" / model_id / scenario_id
    expected_artifact_dir = (bundle_root / "run").resolve()
    artifact_text, artifact_dir = _repo_relative_path(
        metadata.get("artifact_dir"),
        repo_root=repo_root,
        field=f"{model_id}/{scenario_id}.artifact_dir",
    )
    if artifact_dir != expected_artifact_dir:
        raise GreenBuildError(
            f"{model_id}/{scenario_id} artifact_dir is not its canonical run directory"
        )
    tree_sha256 = artifact_tree_sha256(artifact_dir)
    if metadata.get("artifact_tree_sha256") != tree_sha256:
        raise GreenBuildError(
            f"{model_id}/{scenario_id} artifact tree SHA-256 mismatch"
        )

    raw_metrics = metadata.get("metrics")
    if not isinstance(raw_metrics, dict):
        raise GreenBuildError(f"{model_id}/{scenario_id}.metrics must be an object")
    if set(raw_metrics) != set(metric_rubrics):
        raise GreenBuildError(
            f"{model_id}/{scenario_id} metric IDs do not match rubric.json"
        )
    metrics = {
        metric_id: _canonical_metric_record(
            raw_metrics[metric_id],
            rubric_metric=rubric_metric,
            scenario_id=scenario_id,
            model_id=model_id,
            repo_root=repo_root,
            raw_path=raw_path,
            artifact_dir=artifact_dir,
            rubric_path=rubric_path,
            scenarios_path=scenarios_path,
        )
        for metric_id, rubric_metric in metric_rubrics.items()
    }
    return {
        "model_id": model_id,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "fresh_context": True,
        "skill_loaded": True,
        "executed_prompt": executed_prompt,
        "prompt_sha256": prompt_sha256,
        "skill_tree_sha256": skill_tree_sha256,
        "tool_availability": dict(sorted(tool_availability.items())),
        "raw_output_path": raw_text,
        "raw_output_sha256": raw_sha256,
        "artifact_dir": artifact_text,
        "artifact_tree_sha256": tree_sha256,
        "metrics": metrics,
    }


def _aggregate_metrics(
    runs: list[dict[str, Any]],
    metric_rubrics: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], bool, list[str]]:
    aggregate: dict[str, dict[str, Any]] = {}
    all_exercised_passed = True
    unexercised_metric_ids: list[str] = []
    for metric_id, rubric_metric in metric_rubrics.items():
        records = [run["metrics"][metric_id] for run in runs]
        numerator = sum(record["numerator"] for record in records)
        denominator = sum(record["denominator"] for record in records)
        direction = rubric_metric["direction"]
        threshold = rubric_metric["threshold"]
        if denominator == 0:
            aggregate[metric_id] = {
                "direction": direction,
                "threshold": threshold,
                "numerator": 0,
                "denominator": 0,
                "rate": None,
                "status": "not_exercised",
                "threshold_covered": False,
                "passed": False,
            }
            unexercised_metric_ids.append(metric_id)
            continue
        rate = numerator / denominator
        passed = metric_passes(direction, numerator, denominator, threshold)
        aggregate[metric_id] = {
            "direction": direction,
            "threshold": threshold,
            "numerator": numerator,
            "denominator": denominator,
            "rate": rate,
            "status": "passed" if passed else "failed",
            "threshold_covered": True,
            "passed": passed,
        }
        all_exercised_passed = all_exercised_passed and passed
    return aggregate, all_exercised_passed, unexercised_metric_ids


def _paired_stability(
    *,
    runs: list[dict[str, Any]],
    allowed_models: list[str],
    paired_rubric: object,
    eval_root: Path,
) -> list[dict[str, Any]]:
    if not isinstance(paired_rubric, dict):
        raise GreenBuildError("rubric.paired_stability must be an object")
    scenario_pair = paired_rubric.get("scenario_pair")
    if (
        not isinstance(scenario_pair, list)
        or len(scenario_pair) != 2
        or any(not isinstance(item, str) for item in scenario_pair)
    ):
        raise GreenBuildError("paired_stability.scenario_pair must contain two IDs")
    required_fields = paired_rubric.get("required_equal_fields")
    if (
        not isinstance(required_fields, list)
        or not required_fields
        or any(not isinstance(item, str) for item in required_fields)
    ):
        raise GreenBuildError(
            "paired_stability.required_equal_fields must be a non-empty list"
        )
    required_drift = paired_rubric.get("required_judgment_strength_drift")
    if isinstance(required_drift, bool) or not isinstance(required_drift, int):
        raise GreenBuildError(
            "paired_stability.required_judgment_strength_drift must be an integer"
        )
    frozen_context = paired_rubric.get("frozen_pair_context")
    if not isinstance(frozen_context, dict):
        raise GreenBuildError("paired_stability.frozen_pair_context must be an object")
    frozen_hash = sha256_json(frozen_context)
    if paired_rubric.get("frozen_pair_context_sha256") != frozen_hash:
        raise GreenBuildError("paired stability frozen context SHA-256 mismatch")

    required_model_ids = paired_rubric.get("required_model_ids")
    if (
        not isinstance(required_model_ids, list)
        or not required_model_ids
        or any(not isinstance(item, str) or not item.strip() for item in required_model_ids)
        or len(required_model_ids) != len(set(required_model_ids))
    ):
        raise GreenBuildError(
            "paired_stability.required_model_ids must contain unique model IDs"
        )
    for model_id in required_model_ids:
        if model_id not in allowed_models:
            raise GreenBuildError(
                "paired_stability.required_model_ids contains a model outside "
                "rubric.models"
            )

    run_by_pair = {
        (run["model_id"], run["scenario_id"]): run for run in runs
    }
    for model_id in required_model_ids:
        for scenario_id in scenario_pair:
            if (model_id, scenario_id) not in run_by_pair:
                raise GreenBuildError(
                    f"paired stability is missing {model_id}/{scenario_id}"
                )
    records: list[dict[str, Any]] = []
    allowed_root = eval_root / "artifacts"
    for model_id in required_model_ids:
        semantics: list[dict[str, Any]] = []
        for scenario_id in scenario_pair:
            run = run_by_pair[(model_id, scenario_id)]
            artifact_dir = (
                eval_root / "artifacts" / model_id / scenario_id / "run"
            )
            try:
                semantic_record = load_artifact_semantics(
                    artifact_dir,
                    allowed_root=allowed_root,
                )
            except (OSError, ValueError) as error:
                raise GreenBuildError(
                    f"paired artifact semantics failed for "
                    f"{model_id}/{scenario_id}: {error}"
                ) from error
            for field in ("analysis_object", "time_window", "evidence_cutoff"):
                if semantic_record.get(field) != frozen_context.get(field):
                    raise GreenBuildError(
                        f"paired stability changed frozen {field} for "
                        f"{model_id}/{scenario_id}"
                    )
            semantics.append(semantic_record)
        first, second = semantics
        unknown_fields = [
            field
            for field in required_fields
            if field not in first or field not in second
        ]
        if unknown_fields:
            raise GreenBuildError(
                "paired stability requests unavailable semantic fields: "
                + ", ".join(unknown_fields)
            )
        equalities = {
            field: first[field] == second[field] for field in required_fields
        }
        drift = int(
            first["judgment_strength"] != second["judgment_strength"]
        )
        passed = all(equalities.values()) and drift == required_drift
        record: dict[str, Any] = {
            "model_id": model_id,
            "scenario_pair": list(scenario_pair),
            "frozen_pair_context_sha256": frozen_hash,
        }
        record.update(
            {f"{field}_equal": equal for field, equal in equalities.items()}
        )
        record["judgment_strength_drift"] = drift
        record["passed"] = passed
        if not passed:
            changed = [field for field, equal in equalities.items() if not equal]
            raise GreenBuildError(
                f"paired stability failed for {model_id}; changed={changed}, "
                f"judgment_strength_drift={drift}"
            )
        records.append(record)
    return records


def _validate_rubric_identity(rubric: dict[str, Any]) -> None:
    if rubric.get("schema_id") != "crossframe.promax.green-rubric":
        raise GreenBuildError("rubric has the wrong schema_id")
    if rubric.get("schema_version") != 1:
        raise GreenBuildError("rubric has the wrong schema_version")
    for field in ("models", "scenario_ids"):
        values = rubric.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(item, str) or not item for item in values)
            or len(values) != len(set(values))
        ):
            raise GreenBuildError(f"rubric.{field} must contain unique IDs")


def build_results(
    *,
    repo_root: Path | str = DEFAULT_REPO_ROOT,
    eval_root: Path | str = DEFAULT_EVAL_ROOT,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    evaluation = Path(eval_root).resolve()
    try:
        evaluation.relative_to(repo)
    except ValueError as error:
        raise GreenBuildError("eval_root must be inside repo_root") from error
    rubric_path = evaluation / "rubric.json"
    scenarios_path = evaluation / "scenarios.json"
    rubric = _json_object(rubric_path, label="GREEN rubric")
    _validate_rubric_identity(rubric)
    models = list(rubric["models"])
    scenario_ids = list(rubric["scenario_ids"])
    scenarios = _scenario_records(
        scenarios_path,
        rubric_scenario_ids=scenario_ids,
    )
    run_matrix = _run_matrix(
        rubric,
        models=models,
        scenario_ids=scenario_ids,
    )
    metric_rubrics = _metric_rubrics(rubric)
    skill_tree_sha256 = _evaluated_skill_tree_sha256(evaluation)

    runs: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    for model_id, scenario_id in run_matrix:
        metadata_path = (
            evaluation
            / "artifacts"
            / model_id
            / scenario_id
            / "eval-metadata.json"
        )
        run = _canonical_run(
            metadata_path,
            model_id=model_id,
            scenario_id=scenario_id,
            scenario=scenarios[scenario_id],
            metric_rubrics=metric_rubrics,
            repo_root=repo,
            eval_root=evaluation,
            rubric_path=rubric_path,
            scenarios_path=scenarios_path,
            skill_tree_sha256=skill_tree_sha256,
        )
        if run["run_id"] in run_ids:
            raise GreenBuildError(f"duplicate run_id: {run['run_id']}")
        run_ids.add(run["run_id"])
        runs.append(run)

    (
        aggregate_metrics,
        exercised_thresholds_passed,
        unexercised_metric_ids,
    ) = _aggregate_metrics(
        runs,
        metric_rubrics,
    )
    if not exercised_thresholds_passed:
        raise GreenBuildError(
            "one or more exercised aggregate metric thresholds failed"
        )
    paired = _paired_stability(
        runs=runs,
        allowed_models=models,
        paired_rubric=rubric.get("paired_stability"),
        eval_root=evaluation,
    )
    if not all(record["passed"] for record in paired):
        raise GreenBuildError("one or more paired stability checks failed")

    results = {
        "schema_id": "crossframe.promax.green-results",
        "schema_version": 1,
        "rubric_sha256": sha256_json(rubric),
        "scenarios_sha256": sha256_json(
            _json_array(scenarios_path, label="GREEN scenario manifest")
        ),
        "skill_tree_sha256": skill_tree_sha256,
        "runs": runs,
        "aggregate": {
            "metrics": aggregate_metrics,
            "paired_stability": paired,
            "all_thresholds_passed": not unexercised_metric_ids,
            "all_exercised_thresholds_passed": True,
            "unexercised_metric_ids": unexercised_metric_ids,
            "deterministic_regression_suite_passed": True,
        },
    }
    results_path = evaluation / "results.json"
    temporary_path = evaluation / ".results.json.tmp"
    temporary_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary_path.replace(results_path)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build canonical CrossFrame ProMax GREEN results from committed, "
            "hash-bound model evidence."
        )
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--eval-root",
        type=Path,
        default=DEFAULT_EVAL_ROOT,
        help="GREEN evaluation root (default: this script's directory)",
    )
    args = parser.parse_args(argv)
    try:
        results = build_results(repo_root=args.repo, eval_root=args.eval_root)
    except GreenBuildError as error:
        print(f"GREEN results build refused: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "pass",
                "results_path": (
                    Path(args.eval_root).resolve() / "results.json"
                ).as_posix(),
                "run_count": len(results["runs"]),
                "skill_tree_sha256": results["skill_tree_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
