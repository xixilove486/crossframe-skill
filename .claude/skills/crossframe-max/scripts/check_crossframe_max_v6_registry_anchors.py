from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ANCHOR_RE = re.compile(r"`([^`]+\.md)`\s+`(P\d{4})(?:-P?(\d{4}))?`")
SOURCE_RE = re.compile(r"^<!-- source_paragraph:(P\d{4}) style=.* -->$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def source_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SOURCE_RE.match(line)
        if match:
            ids.add(match.group(1))
    return ids


def ids_for_range(start: str, end_digits: str | None) -> list[str]:
    start_n = int(start[1:])
    end_n = int(end_digits) if end_digits else start_n
    if end_n < start_n:
        raise ValueError(f"invalid descending range: {start}-P{end_n:04d}")
    return [f"P{i:04d}" for i in range(start_n, end_n + 1)]


def normalize_dash(value: str) -> str:
    return value.replace("—", "-").replace("–", "-")


def registry_concepts(registry_text: str) -> set[str]:
    concepts: set[str] = set()
    for line in registry_text.splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        columns = [column.strip().strip("`") for column in line.strip().strip("|").split("|")]
        if not columns:
            continue
        concept = columns[0]
        if concept and concept not in {"concept", "concept / gate", "anchor", "outcome"}:
            concepts.add(concept)
    return concepts


def route_required_concepts(route_map: Path) -> set[str]:
    concepts: set[str] = set()
    current_field: str | None = None
    for raw_line in route_map.read_text(encoding="utf-8").splitlines():
        field_match = re.match(r"^    ([a-z_]+):\s*$", raw_line)
        if field_match:
            current_field = field_match.group(1)
            continue
        item_match = re.match(r"^      -\s+(.+?)\s*$", raw_line)
        if item_match and current_field == "required_concepts":
            concepts.add(item_match.group(1).strip().strip("\"'"))
    return concepts


def contract_headings(path: Path) -> set[str]:
    headings: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading = match.group(1)
        headings.add(heading)
        headings.add(normalize_dash(heading))
    return headings


def check(repo: Path) -> list[str]:
    errors: list[str] = []
    max_root = repo / "skills" / "crossframe-max"
    registry = max_root / "references" / "concept-registry" / "index.md"
    route_map = max_root / "references" / "v6-route-map.yaml"
    contract_map_path = max_root / "references" / "concept-contracts" / "v6-contract-map.json"
    contract_file = max_root / "references" / "concept-contracts" / "v6-core-contracts.md"
    source_dir = max_root / "references" / "v6-full-source"
    if not registry.exists():
        return [f"missing registry: {registry}"]
    if not source_dir.is_dir():
        return [f"missing v6 full-source directory: {source_dir}"]

    cache: dict[str, set[str]] = {}
    registry_text = registry.read_text(encoding="utf-8")
    for match in ANCHOR_RE.finditer(registry_text):
        file_name, start, end_digits = match.groups()
        path = source_dir / file_name
        if not path.exists():
            errors.append(f"missing anchor file: {file_name}")
            continue
        if file_name not in cache:
            cache[file_name] = source_ids(path)
        try:
            needed = ids_for_range(start, end_digits)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        missing = [pid for pid in needed if pid not in cache[file_name]]
        if missing:
            errors.append(f"{registry}: {file_name} missing paragraph ids: {', '.join(missing[:12])}")
    if "P0585-P0621" in registry_text and "条件势场" in registry_text:
        errors.append("registry still contains suspicious 条件势场 P0585-P0621 anchor")
    if contract_map_path.exists() and route_map.exists() and contract_file.exists():
        try:
            contract_map = json.loads(contract_map_path.read_text(encoding="utf-8")).get("contracts", {})
        except json.JSONDecodeError as exc:
            errors.append(f"{contract_map_path}: invalid JSON: {exc}")
            contract_map = {}
        concepts = registry_concepts(registry_text)
        required = route_required_concepts(route_map)
        headings = contract_headings(contract_file)
        for concept in sorted(contract_map):
            if concept not in concepts:
                errors.append(f"v6-contract-map.json: contract concept missing from registry: {concept}")
        for concept in sorted(required):
            entry = contract_map.get(concept)
            if not isinstance(entry, dict):
                errors.append(f"v6-contract-map.json: missing route-required concept: {concept}")
                continue
            contract_id = entry.get("contract_id")
            if not isinstance(contract_id, str) or "#" not in contract_id:
                errors.append(f"v6-contract-map.json: {concept} invalid contract_id")
                continue
            heading = contract_id.split("#", 1)[1]
            if heading not in headings and normalize_dash(heading) not in headings:
                errors.append(f"v6-contract-map.json: {concept} contract heading missing: {heading}")
    else:
        for path in [route_map, contract_map_path, contract_file]:
            if not path.exists():
                errors.append(f"missing contract closure file: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check crossframe-max concept-registry source anchors.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    args = parser.parse_args()
    errors = check(Path(args.repo).resolve())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ok: crossframe-max registry anchors resolve to v6 full-source paragraphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
