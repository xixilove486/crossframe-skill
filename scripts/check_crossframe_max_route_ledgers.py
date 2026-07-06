from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path
from typing import Any


ROUTE_LIST_FIELDS = {
    "required_layers",
    "required_concepts",
    "required_outputs",
    "forbidden_outputs",
}

LEDGER_ROUTE_FIELDS = {
    "required_layers": "route_required_layers",
    "required_concepts": "route_required_concepts",
    "required_outputs": "route_required_outputs",
}

ARTIFACTS_TO_SCAN = [
    "max-artifact-manifest.md",
    "max-dossier.md",
    "max-essay.md",
    "max-continuation-ledger.md",
    "max-continuation-index.md",
    "max-output-plan.locked.md",
]

PRESENT_FALSE_RE = re.compile(
    r'(?:present\s*["\']?\s*[:=]\s*false|absent\s*["\']?\s*[:=]\s*true)',
    re.IGNORECASE,
)
PARAGRAPH_RANGE_RE = re.compile(r"P(\d{4})(?:-P?(\d{4}))?")
ANCHOR_WITH_FILE_RE = re.compile(r"`([^`]+\.md)`\s+`(P\d{4})(?:-P?(\d{4}))?`")
VALIDATOR_NAME = "check_crossframe_max_route_ledgers"

PHASE_DOWNSTREAM = {
    "read_plan": [
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-board.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "concept_hit": [
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "claim": [
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "audit": [
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "final_markdown": [],
    "repository_maintenance": [],
}


@dataclass(frozen=True)
class ValidationError:
    error_id: str
    validator: str
    error_type: str
    severity: str
    artifact: str
    field: str | None
    message: str
    affected_phase: str
    repair_action: str
    downstream_reset: list[str]
    final_output_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_dash(value: str) -> str:
    return value.replace("—", "-").replace("–", "-")


def default_skill_root() -> Path:
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "crossframe-max":
        return script_path.parent.parent
    return script_path.parents[1] / "skills" / "crossframe-max"


def read_json(path: Path, errors: list[str]) -> Any:
    if not path.exists():
        errors.append(f"missing route-ledger artifact: {path.name}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return None


def parse_route_map(path: Path) -> tuple[str | None, dict[str, dict[str, list[str]]], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return None, {}, [f"missing route map: {path}"]
    version: str | None = None
    routes: dict[str, dict[str, list[str]]] = {}
    current_route: str | None = None
    current_field: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("version:"):
            version = line.split(":", 1)[1].strip().strip("\"'")
            continue
        route_match = re.match(r"^  ([a-z_]+):\s*$", line)
        if route_match:
            current_route = route_match.group(1)
            routes[current_route] = {field: [] for field in ROUTE_LIST_FIELDS}
            current_field = None
            continue
        if current_route is None:
            continue
        field_match = re.match(r"^    ([a-z_]+):\s*$", line)
        if field_match:
            field = field_match.group(1)
            current_field = field if field in ROUTE_LIST_FIELDS else None
            continue
        item_match = re.match(r"^      -\s+(.+?)\s*$", line)
        if item_match and current_field:
            routes[current_route][current_field].append(item_match.group(1).strip().strip("\"'"))
    if not version:
        errors.append("v6-route-map.yaml: missing version")
    return version, routes, errors


def normalize_paragraph_range(value: str) -> str | None:
    match = PARAGRAPH_RANGE_RE.search(value)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    if end < start:
        return None
    return f"P{start:04d}-P{end:04d}"


def normalize_file_anchor(match: re.Match[str]) -> str:
    file_name, start, end_digits = match.groups()
    range_value = normalize_paragraph_range(f"{start}-{end_digits or start}")
    return f"{file_name}:{range_value}" if range_value else f"{file_name}:{start}"


def paragraph_range_tuple(value: str) -> tuple[int, int] | None:
    match = PARAGRAPH_RANGE_RE.search(value)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    if end < start:
        return None
    return start, end


def paragraph_id_number(value: str) -> int | None:
    match = re.fullmatch(r"P(\d{4})", value)
    if not match:
        return None
    return int(match.group(1))


def ranges_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def any_range_overlap(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> bool:
    return any(ranges_overlap(left_range, right_range) for left_range in left for right_range in right)


def parse_registry_entries(path: Path) -> tuple[set[str], dict[str, set[str]], list[str]]:
    if not path.exists():
        return set(), {}, [f"missing concept registry: {path}"]
    concepts: set[str] = set()
    anchor_map: dict[str, set[str]] = {}
    errors: list[str] = []
    current_section: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            continue
        if not line.startswith("|") or "---" in line:
            continue
        columns = [column.strip().strip("`") for column in line.strip().strip("|").split("|")]
        if not columns:
            continue
        concept = columns[0]
        if concept in {"concept", "concept / gate", "anchor", "outcome"}:
            continue
        anchor_column: str | None = None
        if current_section == "Core Concept Entries" and len(columns) >= 3:
            anchor_column = columns[2]
        elif current_section == "Operational Concept Anchors" and len(columns) >= 2:
            anchor_column = columns[1]
        else:
            continue
        if not concept:
            continue
        concepts.add(concept)
        file_ranges = {normalize_file_anchor(match) for match in ANCHOR_WITH_FILE_RE.finditer(anchor_column)}
        ranges = file_ranges or {
            normalized
            for normalized in (normalize_paragraph_range(match.group(0)) for match in PARAGRAPH_RANGE_RE.finditer(anchor_column))
            if normalized
        }
        if not ranges:
            errors.append(f"concept-registry/index.md: {concept} missing parseable source anchor range")
            continue
        anchor_map[concept] = ranges
    return concepts, anchor_map, errors


def parse_registry_concepts(path: Path) -> tuple[set[str], list[str]]:
    concepts, _anchor_map, errors = parse_registry_entries(path)
    return concepts, errors


def parse_registry_anchor_map(path: Path) -> tuple[dict[str, set[str]], list[str]]:
    _concepts, anchor_map, errors = parse_registry_entries(path)
    return anchor_map, errors


def parse_contract_headings(path: Path) -> tuple[set[str], list[str]]:
    if not path.exists():
        return set(), [f"missing concept contracts: {path}"]
    headings: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("## "):
            continue
        heading = line.removeprefix("## ").strip()
        if heading == "Contract Format":
            continue
        headings.add(heading)
        headings.add(normalize_dash(heading))
    return headings, []


def parse_contract_map(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not path.exists():
        return {}, [f"missing contract map: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"v6-contract-map.json: invalid JSON: {exc}"]
    if not isinstance(data, dict) or not isinstance(data.get("contracts"), dict):
        return {}, ["v6-contract-map.json: contracts must be an object"]
    contracts: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for concept, entry in data["contracts"].items():
        if not isinstance(concept, str) or not isinstance(entry, dict):
            errors.append("v6-contract-map.json: each contract entry must be an object keyed by concept_id")
            continue
        contract_id = entry.get("contract_id")
        if not isinstance(contract_id, str) or "#" not in contract_id:
            errors.append(f"v6-contract-map.json: {concept} missing contract_id with heading anchor")
            continue
        contracts[concept] = entry
    return contracts, errors


def check_route_registry_closure(
    routes: dict[str, dict[str, list[str]]], registry_concepts: set[str], errors: list[str]
) -> None:
    for route_key, route in sorted(routes.items()):
        missing = sorted(set(route.get("required_concepts", [])) - registry_concepts)
        if missing:
            errors.append(
                f"v6-route-map.yaml: route {route_key} required_concepts missing from concept registry: "
                + ", ".join(missing)
            )


def check_contract_map_closure(
    routes: dict[str, dict[str, list[str]]],
    contract_map: dict[str, dict[str, Any]],
    contract_headings: set[str],
    errors: list[str],
) -> None:
    required_concepts = sorted({concept for route in routes.values() for concept in route.get("required_concepts", [])})
    for concept in required_concepts:
        entry = contract_map.get(concept)
        if not entry:
            errors.append(f"v6-contract-map.json: missing contract map entry for route concept: {concept}")
            continue
        contract_id = entry.get("contract_id")
        if not isinstance(contract_id, str) or "#" not in contract_id:
            errors.append(f"v6-contract-map.json: {concept} contract_id must include heading anchor")
            continue
        contract_file, heading = contract_id.split("#", 1)
        if contract_file != "v6-core-contracts.md":
            errors.append(f"v6-contract-map.json: {concept} contract_id must target v6-core-contracts.md")
        if heading not in contract_headings and normalize_dash(heading) not in contract_headings:
            errors.append(f"v6-contract-map.json: {concept} contract_id heading not found: {heading}")


def require_list(data: dict[str, Any], field: str, label: str, errors: list[str]) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(f"{label}: missing {field}")
        return []
    return value


def check_route_plan(read_plan: Any, route_version: str | None, routes: dict[str, dict[str, list[str]]], errors: list[str]) -> tuple[str | None, dict[str, list[str]]]:
    if not isinstance(read_plan, dict):
        errors.append("max-read-plan.json: root must be an object")
        return None, {}
    route_key = read_plan.get("route_key")
    if not isinstance(route_key, str) or not route_key:
        errors.append("max-read-plan.json: missing route_key")
        return None, {}
    route = routes.get(route_key)
    if route is None:
        errors.append(f"max-read-plan.json: route_key not found in v6-route-map.yaml: {route_key}")
        return route_key, {}
    if route_version and read_plan.get("route_map_version") != route_version:
        errors.append(f"max-read-plan.json: route_map_version must be {route_version}")
    for route_field, ledger_field in LEDGER_ROUTE_FIELDS.items():
        actual = set(require_list(read_plan, ledger_field, "max-read-plan.json", errors))
        missing = sorted(set(route.get(route_field, [])) - actual)
        if missing:
            errors.append(f"max-read-plan.json: missing route {route_field}: {', '.join(missing)}")
    forbidden_checks = read_plan.get("route_forbidden_outputs_checked")
    if not isinstance(forbidden_checks, list):
        errors.append("max-read-plan.json: missing route_forbidden_outputs_checked")
    else:
        by_output = {
            item.get("forbidden_output"): item
            for item in forbidden_checks
            if isinstance(item, dict) and isinstance(item.get("forbidden_output"), str)
        }
        for forbidden in route.get("forbidden_outputs", []):
            item = by_output.get(forbidden)
            if item is None:
                errors.append(f"max-read-plan.json: missing forbidden output check: {forbidden}")
                continue
            if item.get("checked") is not True:
                errors.append(f"max-read-plan.json: forbidden output check not marked checked: {forbidden}")
            if item.get("present") is not False:
                errors.append(f"max-read-plan.json: forbidden output must be absent: {forbidden}")
    return route_key, route


def parse_ledger_ranges(value: Any, label: str, concept_id: str, field: str, errors: list[str]) -> list[tuple[int, int]]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: {concept_id} missing {field}")
        return []
    ranges: list[tuple[int, int]] = []
    for item in value:
        if not isinstance(item, str):
            errors.append(f"{label}: {concept_id} {field} must contain strings")
            continue
        parsed = paragraph_range_tuple(item)
        if parsed is None:
            errors.append(f"{label}: {concept_id} has invalid {field}: {item}")
            continue
        ranges.append(parsed)
    return ranges


def parse_source_paragraph_ids(value: Any, label: str, concept_id: str, errors: list[str]) -> list[int]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: {concept_id} missing source_paragraph_ids")
        return []
    ids: list[int] = []
    for item in value:
        if not isinstance(item, str):
            errors.append(f"{label}: {concept_id} source_paragraph_ids must contain strings")
            continue
        parsed = paragraph_id_number(item)
        if parsed is None:
            errors.append(f"{label}: {concept_id} has invalid source_paragraph_id: {item}")
            continue
        ids.append(parsed)
    return ids


def check_contract_id(
    contract_id: Any,
    concept_id: str,
    contract_headings: set[str],
    contract_map: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if not isinstance(contract_id, str) or not contract_id:
        errors.append(f"max-concept-hit-ledger.json: {concept_id} missing contract_id")
        return
    if "#" not in contract_id:
        errors.append(f"max-concept-hit-ledger.json: {concept_id} contract_id must include heading anchor")
        return
    contract_file, heading = contract_id.split("#", 1)
    if contract_file != "v6-core-contracts.md":
        errors.append(f"max-concept-hit-ledger.json: {concept_id} contract_id must target v6-core-contracts.md")
    expected = contract_map.get(concept_id, {}).get("contract_id")
    if isinstance(expected, str) and contract_id != expected:
        errors.append(
            f"max-concept-hit-ledger.json: {concept_id} contract_id must equal v6-contract-map.json entry: {expected}"
        )
    if heading not in contract_headings and normalize_dash(heading) not in contract_headings:
        errors.append(f"max-concept-hit-ledger.json: {concept_id} contract_id heading not found: {heading}")


def check_concept_hit_source_anchors(
    hit: dict[str, Any],
    concept_id: str,
    registry_anchor_map: dict[str, set[str]],
    errors: list[str],
) -> None:
    expected_values = registry_anchor_map.get(concept_id)
    if not expected_values:
        errors.append(f"max-concept-hit-ledger.json: {concept_id} missing registry source anchors")
        return
    expected_ranges = [parsed for parsed in (paragraph_range_tuple(value) for value in expected_values) if parsed]
    registry_ranges = parse_ledger_ranges(
        hit.get("source_ranges_from_registry"),
        "max-concept-hit-ledger.json",
        concept_id,
        "source_ranges_from_registry",
        errors,
    )
    read_ranges = parse_ledger_ranges(
        hit.get("source_ranges_read"),
        "max-concept-hit-ledger.json",
        concept_id,
        "source_ranges_read",
        errors,
    )
    source_ids = parse_source_paragraph_ids(
        hit.get("source_paragraph_ids"), "max-concept-hit-ledger.json", concept_id, errors
    )
    if registry_ranges and not any_range_overlap(registry_ranges, expected_ranges):
        errors.append(
            f"max-concept-hit-ledger.json: {concept_id} source_ranges_from_registry does not match registry anchors"
        )
    if read_ranges and not any_range_overlap(read_ranges, expected_ranges):
        errors.append(f"max-concept-hit-ledger.json: {concept_id} source_ranges_read does not overlap registry anchors")
    for source_id in source_ids:
        if read_ranges and not any(start <= source_id <= end for start, end in read_ranges):
            errors.append(f"max-concept-hit-ledger.json: {concept_id} source_paragraph_ids not covered by source_ranges_read")
        if not any(start <= source_id <= end for start, end in expected_ranges):
            errors.append(f"max-concept-hit-ledger.json: {concept_id} source_paragraph_ids not covered by registry anchors")


def check_concept_hits(
    data: Any,
    route: dict[str, list[str]],
    registry_concepts: set[str],
    registry_anchor_map: dict[str, set[str]],
    contract_headings: set[str],
    contract_map: dict[str, dict[str, Any]],
    errors: list[str],
) -> set[str]:
    if not isinstance(data, dict) or not isinstance(data.get("concept_hits"), list):
        errors.append("max-concept-hit-ledger.json: concept_hits must be a list")
        return set()
    seen: set[str] = set()
    for idx, hit in enumerate(data["concept_hits"], start=1):
        if not isinstance(hit, dict):
            errors.append(f"max-concept-hit-ledger.json: hit {idx} must be an object")
            continue
        concept_id = hit.get("concept_id")
        label = concept_id if isinstance(concept_id, str) and concept_id else f"hit {idx}"
        if not isinstance(concept_id, str) or not concept_id:
            errors.append(f"max-concept-hit-ledger.json: hit {idx} missing concept_id")
            continue
        seen.add(concept_id)
        if concept_id not in registry_concepts:
            errors.append(f"max-concept-hit-ledger.json: {label} not found in concept registry")
        for field in [
            "registry_anchor",
            "trigger_variable",
            "source_ranges_from_registry",
            "source_ranges_read",
            "source_paragraph_ids",
        ]:
            if not hit.get(field):
                errors.append(f"max-concept-hit-ledger.json: {label} missing {field}")
        check_contract_id(hit.get("contract_id"), concept_id, contract_headings, contract_map, errors)
        check_concept_hit_source_anchors(hit, concept_id, registry_anchor_map, errors)
        if hit.get("contract_checked") is not True:
            errors.append(f"max-concept-hit-ledger.json: {label} contract_checked must be true")
    missing = sorted(set(route.get("required_concepts", [])) - seen)
    if missing:
        errors.append(f"max-concept-hit-ledger.json: missing route required concepts: {', '.join(missing)}")
    return seen


def check_claims(
    data: Any, route_key: str | None, route: dict[str, list[str]], errors: list[str]
) -> tuple[set[str], set[str], set[str]]:
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        errors.append("max-claim-ledger.json: claims must be a list")
        return set(), set(), set()
    claim_ids: set[str] = set()
    design_ids: set[str] = set()
    covered_concepts: set[str] = set()
    for idx, claim in enumerate(data["claims"], start=1):
        if not isinstance(claim, dict):
            errors.append(f"max-claim-ledger.json: claim {idx} must be an object")
            continue
        claim_id = claim.get("claim_id", f"claim {idx}")
        if isinstance(claim_id, str):
            claim_ids.add(claim_id)
        for field in [
            "claim_type",
            "source_anchor",
            "evidence_status",
            "concept_ids",
            "action_limit",
        ]:
            if not claim.get(field):
                errors.append(f"max-claim-ledger.json: {claim_id} missing {field}")
        if isinstance(claim.get("concept_ids"), list):
            covered_concepts.update(concept for concept in claim["concept_ids"] if isinstance(concept, str))
        if route_key == "skill_design":
            for field in ["v6_rule_ids", "design_decision_id"]:
                if not claim.get(field):
                    errors.append(f"max-claim-ledger.json: {claim_id} missing {field}")
        if isinstance(claim.get("design_decision_id"), str):
            design_ids.add(claim["design_decision_id"])
    missing_concepts = sorted(set(route.get("required_concepts", [])) - covered_concepts)
    if missing_concepts:
        errors.append(f"max-claim-ledger.json: route concepts missing from concept_ids: {', '.join(missing_concepts)}")
    return claim_ids, design_ids, covered_concepts


def check_audits(data: Any, claim_ids: set[str], design_ids: set[str], errors: list[str]) -> tuple[set[str], set[str]]:
    if not isinstance(data, dict) or not isinstance(data.get("audits"), list):
        errors.append("max-evidence-reasoning-audit.json: audits must be a list")
        return set(), set()
    audit_claim_ids: set[str] = set()
    audit_design_ids: set[str] = set()
    for idx, audit in enumerate(data["audits"], start=1):
        if not isinstance(audit, dict):
            errors.append(f"max-evidence-reasoning-audit.json: audit {idx} must be an object")
            continue
        claim_id = audit.get("claim_id", f"audit {idx}")
        if isinstance(claim_id, str):
            audit_claim_ids.add(claim_id)
        if isinstance(audit.get("design_decision_id"), str):
            audit_design_ids.add(audit["design_decision_id"])
        for field in ["counterevidence", "calibration_rounds", "final_strength", "withdrawal_condition"]:
            if not audit.get(field):
                errors.append(f"max-evidence-reasoning-audit.json: {claim_id} missing {field}")
    missing_claim_audits = sorted(claim_ids - audit_claim_ids)
    if missing_claim_audits:
        errors.append(f"max-evidence-reasoning-audit.json: final claims missing audits: {', '.join(missing_claim_audits)}")
    missing_design_audits = sorted(design_ids - audit_design_ids)
    if missing_design_audits:
        errors.append(
            f"max-evidence-reasoning-audit.json: design decisions missing audits: {', '.join(missing_design_audits)}"
        )
    return audit_claim_ids, audit_design_ids


def markdown_lines_for_forbidden_scan(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_code_block = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block or stripped.startswith(">"):
            continue
        normalized = stripped.replace("`", "")
        if PRESENT_FALSE_RE.search(normalized):
            continue
        lines.append((line_no, normalized))
    return lines


def check_forbidden_outputs(workspace: Path, route: dict[str, list[str]], errors: list[str]) -> None:
    forbidden_outputs = route.get("forbidden_outputs", [])
    if not forbidden_outputs:
        return
    for filename in ARTIFACTS_TO_SCAN:
        path = workspace / filename
        if not path.exists() or not path.is_file():
            continue
        scan_lines = markdown_lines_for_forbidden_scan(path.read_text(encoding="utf-8"))
        for forbidden in forbidden_outputs:
            for line_no, line in scan_lines:
                if forbidden in line:
                    errors.append(f"{filename}:{line_no}: forbidden output appears as final artifact text: {forbidden}")
                    break


def check(workspace: Path, skill_root: Path) -> list[str]:
    errors: list[str] = []
    route_version, routes, route_errors = parse_route_map(skill_root / "references" / "v6-route-map.yaml")
    errors.extend(route_errors)
    registry_concepts, registry_errors = parse_registry_concepts(skill_root / "references" / "concept-registry" / "index.md")
    errors.extend(registry_errors)
    registry_anchor_map, registry_anchor_errors = parse_registry_anchor_map(
        skill_root / "references" / "concept-registry" / "index.md"
    )
    errors.extend(registry_anchor_errors)
    contract_headings, contract_errors = parse_contract_headings(
        skill_root / "references" / "concept-contracts" / "v6-core-contracts.md"
    )
    errors.extend(contract_errors)
    contract_map, contract_map_errors = parse_contract_map(
        skill_root / "references" / "concept-contracts" / "v6-contract-map.json"
    )
    errors.extend(contract_map_errors)
    check_route_registry_closure(routes, registry_concepts, errors)
    check_contract_map_closure(routes, contract_map, contract_headings, errors)
    read_plan = read_json(workspace / "max-read-plan.json", errors)
    concept_hits = read_json(workspace / "max-concept-hit-ledger.json", errors)
    claims = read_json(workspace / "max-claim-ledger.json", errors)
    audits = read_json(workspace / "max-evidence-reasoning-audit.json", errors)
    route_key, route = check_route_plan(read_plan, route_version, routes, errors)
    if not route:
        return errors
    seen_concepts = check_concept_hits(
        concept_hits, route, registry_concepts, registry_anchor_map, contract_headings, contract_map, errors
    )
    claim_ids, design_ids, claim_concepts = check_claims(claims, route_key, route, errors)
    missing_claim_hits = sorted(claim_concepts - seen_concepts)
    if missing_claim_hits:
        errors.append(f"max-claim-ledger.json: concept_ids missing concept hits: {', '.join(missing_claim_hits)}")
    check_audits(audits, claim_ids, design_ids, errors)
    if route_key == "skill_design":
        if not design_ids:
            errors.append("max-claim-ledger.json: skill_design route requires design_decision_id")
    check_forbidden_outputs(workspace, route, errors)
    return errors


def extract_artifact(message: str) -> str:
    for token in [
        "max-read-plan.json",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-evidence-reasoning-audit.json",
        "max-dossier.md",
        "max-essay.md",
        "v6-route-map.yaml",
        "v6-contract-map.json",
        "concept-registry/index.md",
    ]:
        if token in message:
            return token
    return "workspace"


def classify_message(message: str) -> tuple[str, str, str, str | None]:
    lowered = message.lower()
    if "invalid json" in lowered:
        return "invalid_json", "create_missing_artifact", "read_plan", None
    if "missing route-ledger artifact" in message:
        return "missing_artifact", "create_missing_artifact", "read_plan", None
    if "required_concepts missing from concept registry" in message or "missing route required concepts" in message:
        return "route_registry_closure_failed", "regenerate_concept_hit_and_downstream", "concept_hit", "route_required_concepts"
    if "route_key" in message or "route_map_version" in message or "missing route " in message or "forbidden output check" in message:
        return "route_plan_mismatch", "regenerate_output_plan_and_final_markdown", "read_plan", None
    if "not found in concept registry" in message:
        return "concept_registry_missing", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_id"
    if "source_ranges_from_registry does not match" in message or "source_ranges_read does not overlap" in message:
        return "concept_source_anchor_mismatch", "regenerate_concept_hit_and_downstream", "concept_hit", "source_ranges_from_registry"
    if "source_paragraph_ids not covered" in message:
        return "source_paragraph_not_in_read_range", "regenerate_concept_hit_and_downstream", "concept_hit", "source_paragraph_ids"
    if "contract_id" in message or "v6-contract-map.json" in message:
        return "concept_contract_missing", "repository_maintenance_required", "repository_maintenance", "contract_id"
    if "concept_ids missing concept hits" in message:
        return "claim_missing_concept_hit", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_ids"
    if "final claims missing audits" in message or "design decisions missing audits" in message:
        return "claim_missing_audit", "regenerate_audit_and_downstream", "audit", "claim_id"
    if "missing evidence_chain" in message or "evidence chain" in lowered:
        return "evidence_chain_missing", "regenerate_audit_and_downstream", "audit", "evidence_chain"
    if "missing counterevidence" in message or "counterevidence_status" in message:
        return "counterevidence_missing", "regenerate_audit_and_downstream", "audit", "counterevidence"
    if "forbidden output appears" in message:
        return "forbidden_output_present", "regenerate_markdown_only", "final_markdown", None
    return "route_plan_mismatch", "regenerate_output_plan_and_final_markdown", "read_plan", None


def check_structured(workspace: Path, skill_root: Path) -> list[ValidationError]:
    errors = check(workspace, skill_root)
    structured: list[ValidationError] = []
    for index, message in enumerate(errors, start=1):
        error_type, repair_action, affected_phase, field = classify_message(message)
        structured.append(
            ValidationError(
                error_id=f"route-{index:04d}",
                validator=VALIDATOR_NAME,
                error_type=error_type,
                severity="error",
                artifact=extract_artifact(message),
                field=field,
                message=message,
                affected_phase=affected_phase,
                repair_action=repair_action,
                downstream_reset=list(PHASE_DOWNSTREAM.get(affected_phase, [])),
                final_output_allowed=False,
            )
        )
    return structured


def validator_report(workspace: Path, errors: list[ValidationError]) -> dict[str, Any]:
    return {
        "report_version": "v1",
        "workspace": str(workspace),
        "passed": not errors,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "validators": [VALIDATOR_NAME],
        "errors": [error.to_dict() for error in errors],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check crossframe-max route and design ledgers.")
    parser.add_argument("--workspace", default=".", help="Directory containing max route ledger JSON files.")
    parser.add_argument("--skill-root", default=None, help="Path to crossframe-max skill root.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable validator report.")
    parser.add_argument(
        "--write-report",
        nargs="?",
        const="",
        default=None,
        help="Write max-validator-report.json; optional explicit path.",
    )
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else default_skill_root()
    structured_errors = check_structured(workspace, skill_root)
    report = validator_report(workspace, structured_errors)
    if args.write_report is not None:
        report_path = Path(args.write_report).resolve() if args.write_report else workspace / "max-validator-report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if structured_errors else 0
    errors = [error.message for error in structured_errors]
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ok: crossframe-max route ledgers passed route-map checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
