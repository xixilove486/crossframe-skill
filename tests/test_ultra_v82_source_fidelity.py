from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORLD_CONTRACT = (
    ROOT
    / "skills/crossframe-ultra/references/concept-contracts/world-volume-contracts.json"
)
CONTRACT_MAP = (
    ROOT / "skills/crossframe-ultra/references/concept-contracts/v8.2-contract-map.json"
)
ROUTE_MAP = ROOT / "skills/crossframe-ultra/references/v8.2-route-map.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_world_volume_contract_closes_wk_identity_and_local_distribution() -> None:
    document = _load(WORLD_CONTRACT)
    responsibility = document["responsibility"]
    assert "W" in responsibility and "K" in responsibility
    assert "物质状态 M" in responsibility and "体验—意义状态 Ψ" in responsibility

    clauses = {clause["clause_id"]: clause for clause in document["clauses"]}
    assert clauses["V82-CLAUSE-WORLD-WK-IDENTITY"]["source_anchors"]
    assert clauses["V82-CLAUSE-WORLD-LOCAL-DISTRIBUTION"]["source_anchors"]
    assert "信息身份" in clauses["V82-CLAUSE-WORLD-WK-IDENTITY"]["statement"]
    assert "成员关系" in clauses["V82-CLAUSE-WORLD-LOCAL-DISTRIBUTION"]["statement"]
    assert clauses["V82-CLAUSE-WORLD-GRAPH-CEILING"]["source_anchors"] == [
        "V82-P1929"
    ]


def test_contract_map_and_network_route_include_all_source_fidelity_anchors() -> None:
    contract_map = _load(CONTRACT_MAP)
    world = next(
        item
        for item in contract_map["contracts"]
        if item["contract_id"] == "V82-CONTRACT-WORLD-VOLUME"
    )
    assert {"V82-P0998", "V82-P1014", "V82-P1015"}.issubset(
        set(world["source_anchors"])
    )

    route_map = _load(ROUTE_MAP)
    route = next(
        item
        for item in route_map["routes"]
        if item["route_id"] == "V82-ROUTE-NETWORK-PROPAGATION"
    )
    assert {"V82-P2117", "V82-P2118", "V82-P2120"}.issubset(
        set(route["source_anchors"])
    )
