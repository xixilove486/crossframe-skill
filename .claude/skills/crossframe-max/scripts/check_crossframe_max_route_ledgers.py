from __future__ import annotations

import argparse
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


def parse_registry_concepts(path: Path) -> tuple[set[str], list[str]]:
    if not path.exists():
        return set(), [f"missing concept registry: {path}"]
    concepts: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        columns = [column.strip().strip("`") for column in line.strip().strip("|").split("|")]
        if not columns:
            continue
        concept = columns[0]
        if concept in {"concept", "concept / gate", "anchor", "outcome"}:
            continue
        if concept:
            concepts.add(concept)
    return concepts, []


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


def check_concept_hits(data: Any, route: dict[str, list[str]], registry_concepts: set[str], errors: list[str]) -> set[str]:
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
            "contract_id",
        ]:
            if not hit.get(field):
                errors.append(f"max-concept-hit-ledger.json: {label} missing {field}")
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
    check_route_registry_closure(routes, registry_concepts, errors)
    read_plan = read_json(workspace / "max-read-plan.json", errors)
    concept_hits = read_json(workspace / "max-concept-hit-ledger.json", errors)
    claims = read_json(workspace / "max-claim-ledger.json", errors)
    audits = read_json(workspace / "max-evidence-reasoning-audit.json", errors)
    route_key, route = check_route_plan(read_plan, route_version, routes, errors)
    if not route:
        return errors
    seen_concepts = check_concept_hits(concept_hits, route, registry_concepts, errors)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check crossframe-max route and design ledgers.")
    parser.add_argument("--workspace", default=".", help="Directory containing max route ledger JSON files.")
    parser.add_argument("--skill-root", default=None, help="Path to crossframe-max skill root.")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else default_skill_root()
    errors = check(workspace, skill_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ok: crossframe-max route ledgers passed route-map checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
