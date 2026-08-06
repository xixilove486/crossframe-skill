from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Collection, Mapping

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
REFERENCES = ROOT / "skills" / "crossframe-ultra" / "references"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.concept_closure import (
    ConceptClosureError,
    validate_concept_closure,
)
from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import (
    compute_artifact_content_sha256,
    validate_phase_artifact,
)


RUN_ID = "ultra-world-fixture-run"
EVIDENCE_ARTIFACT_SHA256 = (
    "dd16c63fde4626d4db4c82736f67e18ecaed9b5817d2f5cb342bc23ccc947982"
)
WORLD_ARTIFACT_SHA256 = (
    "053716f0de6b642d2bc53b82862761c5815402005ecaad3e2f0abfc5103cc746"
)
TRANSFORMATION_ARTIFACT_SHA256 = (
    "76bc58745c59ea40566e17ad2324cfbd737d4f7fcd4a92ce2c179b42f8288084"
)
REGISTRY_SHA256 = (
    "8c88d2b3d47c378b7beccd74082f8b460f5e91780f18aae1fd74d3a26242ff6d"
)
ROUTE_MAP_SHA256 = (
    "b4b14305303db066f1ecc7bfd1f8e5703925632131f13aba0cd9955e6534b20f"
)
CONTRACT_MAP_SHA256 = (
    "f21f844022d7b67aae1596c154cfe75ecb7b000b0d7959533b71c41c2293e84e"
)
SOURCE_MANIFEST_SHA256 = (
    "1c22cda241473ecb3654e37ee9890b975457bb098334ab5c0f85d2775abf6725"
)
VERSION_BINDING: dict[str, object] = {
    "framework_version": "8.2",
    "framework_revision": "v8.2-r1",
    "framework_raw_sha256": (
        "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
    ),
    "framework_semantic_sha256": (
        "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
    ),
    "runtime_version": "1.1.0",
    "artifact_schema_version": 2,
    "compiler_version": "1.0.0",
    "validator_version": "1.1.0",
    "article_contract_version": "1.1.0",
    "source_tree_sha256": (
        "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
    ),
}
REQUIRED_ROUTES = (
    "V82-ROUTE-CIRCLE-NESTING",
    "V82-ROUTE-NETWORK-PROPAGATION",
)
EXPECTED_REQUIRED_CONCEPTS = {"V82-M02", "V82-M03"}
EXPECTED_REQUIRED_CONTRACTS = {
    "V82-CONTRACT-RECURSIVE-INFERENCE",
    "V82-CONTRACT-TRANSFORMATION",
    "V82-CONTRACT-WORLD-VOLUME",
}
EXPECTED_REQUIRED_REQUIREMENTS = {
    "V82-REQ-M02-EXECUTION",
    "V82-REQ-RAC-MEMBERSHIP",
    "V82-REQ-RCC-RELATION",
    "V82-REQ-SP-AXES",
}
STATUS_BY_CONCEPT = {
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
RATIONALE_BY_CONCEPT = {
    "V82-M01": (
        "Aggregation is retained because the ledger keeps actor, circle, and position "
        "states separate instead of backfilling the represented whole into a member."
    ),
    "V82-M02": (
        "The containment graph establishes descriptive nesting, while no preregistered "
        "cross-layer causal root yet authorizes a causal or conversion branch."
    ),
    "V82-M03": (
        "Directed channels expose a candidate propagation path, but the frozen record "
        "does not yet separate timed transmission and loss from synchronized context."
    ),
    "V82-M04": (
        "No selected route supplies a frozen longitudinal window, lag rule, or cumulative "
        "composition, so temporal accumulation is outside this run's applicability."
    ),
    "V82-M05": (
        "The supplied charter claim records no persistent change to roles, resources, "
        "decision rules, or later transfers, so institutional writeback is rejected."
    ),
    "V82-M06": (
        "The retained multi-location state and interaction channels support reviewing a "
        "target-scale pattern without reducing it to a single represented location."
    ),
    "V82-M07": (
        "The association delegation remains a user claim without an independently valid "
        "atomic authorization tuple, so representation cannot expand the J axis."
    ),
    "V82-M08": (
        "Representation translations explicitly preserve lineage, register task-relative "
        "loss, and attach effects to local variables, satisfying bounded abstraction."
    ),
    "V82-M09": (
        "No source-to-target domain mapping, prohibited mapping, or independent target "
        "instance is registered, so horizontal analogy transfer is rejected."
    ),
}
PENDING_BRANCH_BY_CONCEPT = {
    "V82-M02": {
        "condition": (
            "A causal nesting branch remains unresolved until a preregistered G4 "
            "root-instance distinguishes boundary membership from cross-layer conversion."
        ),
        "required_evidence": [
            "A preregistered G4 subtype with one frozen success criterion.",
            "Observations that separate boundary and interface facts from causal increment.",
        ],
    },
    "V82-M03": {
        "condition": (
            "Propagation remains unresolved until the candidate directed path's timing "
            "and loss are separated from shared-environment synchronization."
        ),
        "required_evidence": [
            "Time-stamped edge observations for both candidate and alternative paths.",
            "A path-interruption comparison measuring direction, delay, and transmission loss.",
        ],
    },
}
ASCII_ROMAN_ORDINALS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
UNICODE_ROMAN_ORDINALS = ("Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ")
ENGLISH_CARDINAL_ORDINALS = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)
ENGLISH_POSITION_ORDINALS = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
)
CHINESE_ORDINALS = (
    "第一",
    "第二",
    "第三",
    "第四",
    "第五",
    "第六",
    "第七",
    "第八",
    "第九",
)
FORMAT_SEPARATORS = (
    "\u200b",
    "\u200c",
    "\u200d",
    "\u200e",
    "\u200f",
    "\u2060",
    "\u2063",
    "\ufeff",
    "\u061c",
)
ROMAN_REGRESSION_HASHES = {
    "ascii": (
        "ee225ab6a84212618b6c1a9d44e7d76b57f5deb1fa94c262c938c4e6b343aa0d",
        "e0925ade676611e8f260e0c752bae8328f51e5f1c606736c7fdde75b5fc2ecba",
    ),
    "wrapped": (
        "d3be96a35b76f9b6f261db23b4d8dc814c064da28ca1a96bcd2d1bb5986dd391",
        "895f064dfc2a2287cdd65f812fce491cf02045bea6135c391c60c7e852e6aeeb",
    ),
    "unicode": (
        "eccc3ea59359338ba74e4bf3362541152bd9f32128eee21a650446f1d6cb9e7f",
        "9a4e696fa9dcd964bc9f8490fa4db6650e3389d5564ce2c7d4385b1fbbe0f493",
    ),
    "ascii-punctuation": (
        "8501cd20a1a3f1dcf912d843b1195169083d280755b1c46caaa94c794b16f153",
        "46b20906814eff47412cec73cbcced308c2464d4a39de810d9c129c56d893ebd",
    ),
    "cjk-punctuation": (
        "5b359b3341daf39aea96ce28198fa1f33eb6f9310a277add5e4f60d069307c9b",
        "e988fe07e54ef39b599171ceba0322c4346293c9f0612b7b9e2678cf7502d25f",
    ),
    "word-nonregression": (
        "149f1e8e8a752ffa863520ccfdabce3e6db2f109fead02be403bc6a60a3be1af",
        "95ed56e947261355261682dcf16ad1d90e430c4420585a66d37c7d1847ec577a",
    ),
    "english-cardinal": (
        "2ec5614a2fb17b9bb98103a204caf29b6ace5a4489e6b026228648d75ad3edea",
        "7e3ca7f372b865856d934833baef6f1a76fd4212dd0a31800d54bf904e400c1b",
    ),
    "english-ordinal": (
        "f5192689c4018d1361fb677adea6ecd27c000c0d3f124f91f05ab7aa672900ce",
        "53312683d2fa453f65deacd1c34e71180a702619d6f34ce087321404829c3136",
    ),
    "chinese-ordinal": (
        "4c2ecfff17d3fe8127df9cf028582c70d6159f1a3a4f7911caafcd297e405faf",
        "9acf7d19e45d4745846de312dfbf5da4e25481a7630f7f6e731394759ff179f5",
    ),
    "format-invisible": (
        "638f2444c09ce31d43a7f4c8aedbd1dc2a854d811abbcd0e96a665fc9b03f35b",
        "db9cc97fed0810e97593f3d93c0188a0aabb70bf39d75ddf42358597e4598bd4",
    ),
}
AUTHORITY_REGRESSION_HASHES = {
    "contract-schema-invalid": {
        "authority": "0e2f98bc8b8b93273068d26c2bf201a53974c1e69866ee915ec9091a527588ff",
        "content": "e96b6db4aced6735ca1d270eb88e1c4beda86d7e62dab0f8a1f82bc7f5f42184",
        "artifact": "96b6883c62e133e7cb51d21aa35007585a8b88b3c33e1fdb84b7134d00536caa",
    },
    "contract-metadata-mismatch": {
        "authority": "051fc4dd2723af5337471b3062e04154868b5900a313f2a509f7a65c6c98d38a",
        "content": "dd69c5d5d085bd4f07288f2cd99f6a09027f0494ebd28619e4a6eab470c56479",
        "artifact": "4c65a8dc21a2fcf87e589513623d77e0a5f6f6453a95a2f8016fe2100347810f",
    },
    "contract-duplicate-file": {
        "authority": "34d9e80f57add3bec9d87af65287484ba86cdd53a565fc4099ace501b6694795",
        "content": "8b98d6ce06b7b1171d91ee967411933e5a6aad3ce7bd17684f4ae9da800f47f4",
        "artifact": "2f6921f98857ce710781631634981043f7ab9f905bd3093bb457a997cb713c89",
    },
    "contract-escaped-source-ref": {
        "authority": "389337e59249fcec77942ec5c02a42cec7c3c9a5fbeb538f4f52f4dad6a411b4",
        "content": "85b905aa31cd8119cdd66fe70b6a37e668ae54440d8fece27dcd601f9c893b14",
        "artifact": "93388a7a0aeae6c6c31f4f7e8f5f477d4d83d87620e375c218afa1d625b50710",
    },
    "route-empty-required": {
        "authority": "9aed85be5ee25ffab9b12cf625e863def995a7a447690d3f32ebedd6365dbd68",
        "content": "86ea091dddb576f5b369889f72bce9d0c19038d04ea45c8c1d2fe0d1c264c4b7",
        "artifact": "3c2436c9542bcc01eec4939e13bbc2b42492e811a739e86d5d318f44199ce0a1",
    },
    "route-uncovered-concept": {
        "authority": "4a7bd10c34c03e45c08c401e0089cf8501fa45844a29f383058a8dfac100afb0",
        "content": "f5254abb36f1498c918f0a0f74a0dbc5fee3207f108d4dd75e68a881559dc2dd",
        "artifact": "bf2652cc0a423202d422ba0c5bfef7f97a24eb36e7b41db14bfae1914bbf3606",
    },
    "route-owner-omission": {
        "authority": "29b9f015a63943c4ed156ac5867b0bed5209440d7d8df6cc1332019cb03d6e1e",
        "content": "c0dd89673df682334351b791100bc703c805ac752277834bbca8407f9a96afcb",
        "artifact": "cb7c93e23de405c0caf5b20653ea8b29f12846024adcab2a7bf65638a60da977",
    },
    "route-unknown-requirement": {
        "authority": "f98b39fa45ef44bcc4b396993566d94fb350cb4bac97724fee0f36fafd2e33de",
        "content": "57ba8045994473cfd46b287674fc9c7d3d5a5f7e1c3667c55924e3945be25101",
        "artifact": "d153b31e44c154202e71bc23584665f12cd85b98c524f5e39109dc7403b10b4f",
    },
    "registry-dangling-neighbor": {
        "authority": "9acd74756bc2a60850b17d542e44e9be59bf48a22e8bb050f92673cff657f0f6",
        "content": "d3d51492c60fc9d801666f3d0abeebbaf82329548c4b53233a7acc6769932c04",
        "artifact": "7cb637c2e5f73a176aaebe41085280526669e7a1faddbe27de8cfdbb833a524a",
    },
    "registry-dangling-prerequisite": {
        "authority": "e612f78aead05756c91cd4d804670413f4d4a0689967cf222450dcb559129024",
        "content": "e7de11c5573dcf4b01ff7a3013a00fa20aa4803004fd07365209ba6fb3e86dd3",
        "artifact": "35968b5c1e8a6dd1aa83deb7c64f6534ef7902e2255d3d5c73a8cdbd4ded1aa6",
    },
    "registry-dangling-conflict": {
        "authority": "938f20e17abe3822b6a93b4c8ce00b62d080921c30377d50e6f0d58f09c53a85",
        "content": "95830dcdc7a609bc2d2e2b272a412fcf398296729900452f4f9b3d39908164d7",
        "artifact": "721b4c6205f8600811863448415ffa29ba5e486d0a11327d24bc609141d4ab3d",
    },
    "registry-missing-neighbor-backlink": {
        "authority": "2d9a413912706964d12873386ddbda406710ad763b3c5f7cf316e34cbb0be633",
        "content": "bb1ee383128d394eff28ef0656e4e5e81b2803334f373a1bb1dd0e0bcc5d5d42",
        "artifact": "f964a6dfa81cd5b46a38f04e4a326416de8921ffe053296604f801353ff37361",
    },
    "registry-missing-conflict-backlink": {
        "authority": "d9a2bfa0f26bbf45e12ba67417100a29678771095fd3bb751a32bcead2b2085c",
        "content": "07918852eb1e7655d9b1378e8eb35c788aecac61f8761ea574016a99c129f0ab",
        "artifact": "04be3aafccb006dcdf49b901f0cf72834fb90133bfb8739c5b741ff3f1a74dd9",
    },
    "registry-invalid-source-anchor": {
        "authority": "d0c05c265cea5e1ed2db36ccebe50d68351d4fc08998db1d9b1adb9bacd6048c",
        "content": "79aeb07448273cdb6d9f90b5e14f5155c42554d2328a8ba2b7f9b0c2c432421f",
        "artifact": "eb86b0ea84d6057a042e02ef1178f384f5462601e6f3db7e6ed08e8036f06791",
    },
    "registry-semantic-unsupported": {
        "authority": "65b455ff90526169f7f25f73235a2280cbcfdb0af67bfaad9dd09cc8a815cbc7",
        "content": "e81164d4011695d6b543ae9e71c459d1199a17c0b61852bd70c551c309c4fcfd",
        "artifact": "8385625ab384ac5729673178753289090fecb7c9ae2d04e4e345da633c7653c0",
    },
    "contract-semantic-unsupported": {
        "authority": "6680c3aab17a3c0168d5c7db3a0414d99f76746bb8ba6ab02e5939f311802335",
        "content": "9d8e11d00428016af064b58cff0baa7df234bfdf57da9aba4d2c70f63a5e269a",
        "artifact": "fcb50df8ed53bdf41df5f3a94619acd01362638f4abbb11b887f1d68a520d5eb",
    },
    "route-semantic-unsupported": {
        "authority": "6792e81039b9d9291be785b14eaf31ef5fcd097852bd2f1a372cf40aa0978836",
        "content": "216ced81668ae8b0bedffee7cf62b67ce50a4e916966e2aa9756f2f19333736d",
        "artifact": "d049248d26d2d5e8636837e523dcd9a5baf297ff5006933676da8b03b1f87d0c",
    },
    "registry-neighbor-route-incomplete": {
        "authority": "51c9cf0e995c8db228e08a858e57413c12fe72a27f48e499ec3dcb66c9661a68",
        "content": "e69d825cc33b12d8bd8bc833651a1fd50381cdd23a09c606215e1b2b7d05a323",
        "artifact": "482732b1e9670c1cd45805b184108c55c1f35547f2e3a2c95bbd8c0a3b9c66af",
    },
    "registry-neighbor-route-complete": {
        "authority": "51c9cf0e995c8db228e08a858e57413c12fe72a27f48e499ec3dcb66c9661a68",
        "content": "2cc363ae9f6e1c33c0e5e267d400cc180a55c604236c597db1a2552c77505538",
        "artifact": "d1acf7093320f227caf20906f2bd142c25f6d1ca3403532956b4839755302e72",
    },
}


class AlwaysEqual:
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


class AlwaysEqualStr(str):
    def __new__(cls, value: str = "0" * 64) -> AlwaysEqualStr:
        return super().__new__(cls, value)

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    __hash__ = str.__hash__


class RouteAlias(str):
    def __new__(cls, target: str, ordinal: int) -> RouteAlias:
        instance = super().__new__(cls, f"ATTACKER-ROUTE-{ordinal}")
        instance.target = target
        return instance

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    def __hash__(self) -> int:
        return hash(self.target)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def load_fixture(name: str) -> dict[str, Any]:
    return load_json(FIXTURES / name)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def rehash_artifact(value: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(value))
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return snapshot


def write_authority_json(path: Path, value: Mapping[str, object]) -> str:
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def route_closure(
    registry: Mapping[str, object],
    route_map: Mapping[str, object],
    required_route_ids: Collection[str],
) -> tuple[set[str], set[str], set[str]]:
    assert registry["concepts"]
    assert route_map["routes"]
    assert tuple(required_route_ids) == REQUIRED_ROUTES
    return (
        set(EXPECTED_REQUIRED_CONCEPTS),
        set(EXPECTED_REQUIRED_CONTRACTS),
        set(EXPECTED_REQUIRED_REQUIREMENTS),
    )


def make_concept_document(
    evidence: Mapping[str, object],
    world: Mapping[str, object],
    transformations: Mapping[str, object],
    *,
    required_route_ids: Collection[str] = REQUIRED_ROUTES,
) -> dict[str, Any]:
    registry = load_json(REFERENCES / "concept-registry" / "v8.2-concept-registry.json")
    route_map = load_json(REFERENCES / "v8.2-route-map.json")
    routes = {record["route_id"]: record for record in route_map["routes"]}
    required_concepts, required_contracts, required_requirements = route_closure(
        registry,
        route_map,
        required_route_ids,
    )
    evidence_cycle = (
        "EVIDENCE-ROSTER-ATLAS",
        "EVIDENCE-ASSOCIATION-CHARTER",
        "EVIDENCE-INTERVIEW-ONE",
    )
    transform_cycle = tuple(
        record["transform_id"] for record in transformations["transformations"]
    )
    dispositions: list[dict[str, object]] = []
    obligations: list[dict[str, object]] = []
    for index, concept in enumerate(registry["concepts"], start=1):
        concept_id = concept["concept_id"]
        status = STATUS_BY_CONCEPT[concept_id]
        concept_routes = sorted(
            route_id
            for route_id in required_route_ids
            if concept_id in routes[route_id]["concept_ids"]
        )
        contract_ids = sorted(
            {
                contract_id
                for route_id in concept_routes
                for contract_id in routes[route_id]["contract_ids"]
            }
        )
        requirement_ids = sorted(
            {
                requirement_id
                for route_id in concept_routes
                for requirement_id in routes[route_id]["requirement_ids"]
            }
        )
        if status == "not-applicable":
            evidence_ids: list[str] = []
            unknown_ids: list[str] = []
            transformation_ids: list[str] = []
            obligation_ids: list[str] = []
            condition_branch = None
        else:
            evidence_ids = [evidence_cycle[(index - 1) % len(evidence_cycle)]]
            unknown_ids = ["UNKNOWN-ADAPTATION"] if status == "unknown-pending" else []
            transformation_ids = [transform_cycle[(index - 1) % len(transform_cycle)]]
            obligation_id = f"OBLIGATION-{concept_id}"
            obligation_ids = [obligation_id]
            if status == "unknown-pending":
                branch_id = f"BRANCH-{concept_id}"
                branch_authority = PENDING_BRANCH_BY_CONCEPT[concept_id]
                condition_branch: dict[str, object] | None = {
                    "branch_id": branch_id,
                    "condition": branch_authority["condition"],
                    "evidence_plan": {
                        "plan_id": f"PLAN-{concept_id}",
                        "required_evidence": list(branch_authority["required_evidence"]),
                    },
                }
            else:
                branch_id = None
                condition_branch = None
            obligations.append(
                {
                    "obligation_id": obligation_id,
                    "concept_id": concept_id,
                    "status": status,
                    "semantic_unit_id": f"SEMANTIC-UNIT-{concept_id}",
                    "evidence_ids": list(evidence_ids),
                    "unknown_ids": list(unknown_ids),
                    "transformation_ids": list(transformation_ids),
                    "route_ids": list(concept_routes),
                    "contract_ids": list(contract_ids),
                    "requirement_ids": list(requirement_ids),
                    "condition_branch_id": branch_id,
                }
            )
        dispositions.append(
            {
                "concept_id": concept_id,
                "status": status,
                "rationale": RATIONALE_BY_CONCEPT[concept_id],
                "route_required": concept_id in required_concepts,
                "neighbor_concept_ids": list(concept["required_neighbors"]),
                "route_ids": list(concept_routes),
                "contract_ids": list(contract_ids),
                "requirement_ids": list(requirement_ids),
                "obligation_ids": list(obligation_ids),
                "evidence_ids": list(evidence_ids),
                "unknown_ids": list(unknown_ids),
                "transformation_ids": list(transformation_ids),
                "condition_branch": condition_branch,
            }
        )
    document: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.concept-disposition",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": copy.deepcopy(VERSION_BINDING),
        "generated_at": "2026-08-02T09:00:00Z",
        "content_sha256": "0" * 64,
        "phase_id": "U5",
        "evidence_artifact_sha256": EVIDENCE_ARTIFACT_SHA256,
        "evidence_content_sha256": evidence["content_sha256"],
        "world_volume_artifact_sha256": WORLD_ARTIFACT_SHA256,
        "world_volume_content_sha256": world["content_sha256"],
        "transformation_ledger_artifact_sha256": TRANSFORMATION_ARTIFACT_SHA256,
        "transformation_ledger_content_sha256": transformations["content_sha256"],
        "registry_sha256": REGISTRY_SHA256,
        "route_map_sha256": ROUTE_MAP_SHA256,
        "contract_map_sha256": CONTRACT_MAP_SHA256,
        "required_route_ids": sorted(required_route_ids),
        "required_contract_ids": sorted(required_contracts),
        "required_requirement_ids": sorted(required_requirements),
        "dispositions": dispositions,
        "semantic_obligations": obligations,
        "unvisited_concept_ids": [],
        "closure_complete": True,
    }
    return rehash_artifact(document)


def concept_kwargs(
    *,
    repo: Path,
    evidence: Mapping[str, object],
    world: Mapping[str, object],
    transformations: Mapping[str, object],
    required_route_ids: Collection[str] = REQUIRED_ROUTES,
    expected_registry_sha256: str = REGISTRY_SHA256,
    expected_route_map_sha256: str = ROUTE_MAP_SHA256,
    expected_contract_map_sha256: str = CONTRACT_MAP_SHA256,
    expected_source_manifest_sha256: str = SOURCE_MANIFEST_SHA256,
) -> dict[str, object]:
    return {
        "repo": repo,
        "evidence_ledger": evidence,
        "world_volume": world,
        "transformation_ledger": transformations,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_artifact_sha256": EVIDENCE_ARTIFACT_SHA256,
        "expected_world_volume_artifact_sha256": WORLD_ARTIFACT_SHA256,
        "expected_transformation_ledger_artifact_sha256": TRANSFORMATION_ARTIFACT_SHA256,
        "expected_registry_sha256": expected_registry_sha256,
        "expected_route_map_sha256": expected_route_map_sha256,
        "expected_contract_map_sha256": expected_contract_map_sha256,
        "expected_source_manifest_sha256": expected_source_manifest_sha256,
        "required_route_ids": required_route_ids,
    }


@pytest.fixture
def evidence() -> dict[str, Any]:
    authority = load_fixture("evidence-ledger-valid.json")
    authority["run_id"] = RUN_ID
    return rehash_artifact(authority)


@pytest.fixture
def world() -> dict[str, Any]:
    return load_fixture("world-volume-valid.json")


@pytest.fixture
def transformations() -> dict[str, Any]:
    return load_fixture("transformation-valid.json")


@pytest.fixture
def document(
    evidence: Mapping[str, object],
    world: Mapping[str, object],
    transformations: Mapping[str, object],
) -> dict[str, Any]:
    return make_concept_document(evidence, world, transformations)


def validate_document(
    document: Mapping[str, object],
    evidence: Mapping[str, object],
    world: Mapping[str, object],
    transformations: Mapping[str, object],
    *,
    repo: Path = ROOT,
    required_route_ids: Collection[str] = REQUIRED_ROUTES,
    expected_registry_sha256: str = REGISTRY_SHA256,
    expected_route_map_sha256: str = ROUTE_MAP_SHA256,
    expected_contract_map_sha256: str = CONTRACT_MAP_SHA256,
    expected_source_manifest_sha256: str = SOURCE_MANIFEST_SHA256,
) -> frozenset[str]:
    return validate_concept_closure(
        document,
        **concept_kwargs(
            repo=repo,
            evidence=evidence,
            world=world,
            transformations=transformations,
            required_route_ids=required_route_ids,
            expected_registry_sha256=expected_registry_sha256,
            expected_route_map_sha256=expected_route_map_sha256,
            expected_contract_map_sha256=expected_contract_map_sha256,
            expected_source_manifest_sha256=expected_source_manifest_sha256,
        ),
    )


def test_concept_document_is_real_schema_valid_u5_artifact(
    document: dict[str, Any],
) -> None:
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    assert canonical_sha256(document) != document["content_sha256"]
    assert "section_assignment" not in document
    assert all("section_assignment" not in item for item in document["dispositions"])


def test_validate_concept_closure_public_keyword_order_is_frozen() -> None:
    signature = inspect.signature(validate_concept_closure)
    assert tuple(signature.parameters) == (
        "document",
        "repo",
        "evidence_ledger",
        "world_volume",
        "transformation_ledger",
        "expected_run_id",
        "expected_version_binding",
        "expected_source_manifest_sha256",
        "expected_evidence_artifact_sha256",
        "expected_world_volume_artifact_sha256",
        "expected_transformation_ledger_artifact_sha256",
        "expected_registry_sha256",
        "expected_route_map_sha256",
        "expected_contract_map_sha256",
        "required_route_ids",
    )
    parameters = tuple(signature.parameters.values())
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in parameters[1:]
    )
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert signature.return_annotation == "frozenset[str]"


def test_complete_registry_route_neighbor_and_obligation_closure_returns_retained_units(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    before = copy.deepcopy((document, evidence, world, transformations))
    retained = validate_document(document, evidence, world, transformations)
    expected = {
        obligation["semantic_unit_id"]
        for obligation in document["semantic_obligations"]
    }
    assert retained == frozenset(expected)
    rejected_units = {
        obligation["semantic_unit_id"]
        for obligation in document["semantic_obligations"]
        if obligation["status"] == "tested-rejected"
    }
    assert rejected_units
    assert rejected_units.issubset(retained)
    registry = load_json(REFERENCES / "concept-registry" / "v8.2-concept-registry.json")
    assert {item["concept_id"] for item in document["dispositions"]} == {
        item["concept_id"] for item in registry["concepts"]
    }
    assert (document, evidence, world, transformations) == before


@pytest.mark.parametrize(
    ("keyword", "replacement"),
    [
        ("expected_run_id", "wrong-run"),
        ("expected_version_binding", {**VERSION_BINDING, "validator_version": "9"}),
        ("expected_evidence_artifact_sha256", "a" * 64),
        ("expected_world_volume_artifact_sha256", "b" * 64),
        ("expected_transformation_ledger_artifact_sha256", "c" * 64),
        ("expected_registry_sha256", "d" * 64),
        ("expected_route_map_sha256", "e" * 64),
        ("expected_contract_map_sha256", "f" * 64),
        ("expected_source_manifest_sha256", "1" * 64),
    ],
)
def test_concept_producer_rejects_wrong_external_expected_authority(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    keyword: str,
    replacement: object,
) -> None:
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=evidence,
        world=world,
        transformations=transformations,
    )
    kwargs[keyword] = replacement
    with pytest.raises(ConceptClosureError):
        validate_concept_closure(document, **kwargs)


@pytest.mark.parametrize(
    "attacker",
    [AlwaysEqual(), AlwaysEqualStr()],
    ids=("arbitrary-always-equal", "always-equal-str-subclass"),
)
@pytest.mark.parametrize(
    "keyword",
    (
        "expected_source_manifest_sha256",
        "expected_evidence_artifact_sha256",
        "expected_world_volume_artifact_sha256",
        "expected_transformation_ledger_artifact_sha256",
        "expected_registry_sha256",
        "expected_route_map_sha256",
        "expected_contract_map_sha256",
    ),
)
def test_concept_public_hash_authority_rejects_equality_attackers(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    attacker: object,
    keyword: str,
) -> None:
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=evidence,
        world=world,
        transformations=transformations,
    )
    kwargs[keyword] = attacker
    with pytest.raises(ConceptClosureError):
        validate_concept_closure(document, **kwargs)


@pytest.mark.parametrize(
    "keyword",
    (
        "expected_source_manifest_sha256",
        "expected_evidence_artifact_sha256",
        "expected_world_volume_artifact_sha256",
        "expected_transformation_ledger_artifact_sha256",
        "expected_registry_sha256",
        "expected_route_map_sha256",
        "expected_contract_map_sha256",
    ),
)
def test_concept_public_hash_authority_requires_lowercase_64_hex(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    keyword: str,
) -> None:
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=evidence,
        world=world,
        transformations=transformations,
    )
    kwargs[keyword] = "A" * 64
    with pytest.raises(ConceptClosureError):
        validate_concept_closure(document, **kwargs)


@pytest.mark.parametrize("authority_kind", ("run-id", "version-binding"))
def test_concept_public_scalar_authority_rejects_equality_overrides(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    authority_kind: str,
) -> None:
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=evidence,
        world=world,
        transformations=transformations,
    )
    if authority_kind == "run-id":
        kwargs["expected_run_id"] = AlwaysEqualStr("attacker-run")
    else:
        kwargs["expected_version_binding"] = {
            **VERSION_BINDING,
            "validator_version": AlwaysEqualStr("attacker-version"),
        }
    with pytest.raises(ConceptClosureError):
        validate_concept_closure(document, **kwargs)


@pytest.mark.parametrize(
    "artifact_name", ("document", "evidence", "world", "transformations")
)
@pytest.mark.parametrize("artifact_field", ("run-id", "version-binding"))
def test_concept_artifact_authority_fields_require_native_json_strings(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    artifact_name: str,
    artifact_field: str,
) -> None:
    values = {
        "document": copy.deepcopy(document),
        "evidence": copy.deepcopy(evidence),
        "world": copy.deepcopy(world),
        "transformations": copy.deepcopy(transformations),
    }
    target = values[artifact_name]
    preserve_canonical_text = artifact_name != "document"
    if artifact_field == "run-id":
        text = target["run_id"] if preserve_canonical_text else "attacker-run"
        target["run_id"] = AlwaysEqualStr(text)
    else:
        text = (
            target["version_binding"]["runtime_version"]
            if preserve_canonical_text
            else "attacker-runtime"
        )
        target["version_binding"]["runtime_version"] = AlwaysEqualStr(text)
    values[artifact_name] = rehash_artifact(target)
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=values["evidence"],
        world=values["world"],
        transformations=values["transformations"],
    )

    with pytest.raises(ConceptClosureError):
        validate_concept_closure(values["document"], **kwargs)


def test_required_route_ids_reject_hash_and_equality_overriding_aliases(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    aliases = tuple(
        RouteAlias(route_id, ordinal)
        for ordinal, route_id in enumerate(REQUIRED_ROUTES, start=1)
    )
    kwargs = concept_kwargs(
        repo=ROOT,
        evidence=evidence,
        world=world,
        transformations=transformations,
        required_route_ids=aliases,
    )
    with pytest.raises(ConceptClosureError):
        validate_concept_closure(document, **kwargs)


@pytest.mark.parametrize("upstream", ["evidence", "world", "transformations"])
def test_mutated_rehashed_upstream_is_rejected_by_external_full_artifact_hash(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    upstream: str,
) -> None:
    values = {
        "evidence": copy.deepcopy(evidence),
        "world": copy.deepcopy(world),
        "transformations": copy.deepcopy(transformations),
    }
    if upstream == "evidence":
        values[upstream]["entries"][0]["statement"] = "replacement"
    elif upstream == "world":
        values[upstream]["actors"][0]["label"] = "replacement"
    else:
        values[upstream]["transformations"][0]["input_identity"]["value"] = "replacement"
    values[upstream] = rehash_artifact(values[upstream])
    with pytest.raises(ConceptClosureError):
        validate_document(
            document,
            values["evidence"],
            values["world"],
            values["transformations"],
        )


def test_swapped_content_and_artifact_roles_are_rejected_even_when_document_rehashed(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    broken = copy.deepcopy(document)
    for prefix in ("evidence", "world_volume", "transformation_ledger"):
        artifact_key = f"{prefix}_artifact_sha256"
        content_key = f"{prefix}_content_sha256"
        broken[artifact_key], broken[content_key] = broken[content_key], broken[artifact_key]
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("required_route_ids", ["V82-ROUTE-CIRCLE-NESTING"]),
        ("required_contract_ids", ["V82-CONTRACT-TRANSFORMATION"]),
        ("required_requirement_ids", ["V82-REQ-SP-AXES"]),
    ],
)
def test_top_level_required_sets_equal_external_route_closure(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(document)
    broken[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "unvisited"])
def test_every_registry_concept_has_exactly_one_disposition(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    mutation: str,
) -> None:
    broken = copy.deepcopy(document)
    if mutation == "missing":
        broken["dispositions"].pop()
    elif mutation == "duplicate":
        broken["dispositions"].append(copy.deepcopy(broken["dispositions"][0]))
    elif mutation == "unknown":
        broken["dispositions"][0]["concept_id"] = "V82-MISSING"
    else:
        broken["closure_complete"] = False
        broken["unvisited_concept_ids"] = ["V82-M09"]
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("route_required", False),
        ("neighbor_concept_ids", ["V82-M01"]),
        ("route_ids", []),
        ("contract_ids", []),
        ("requirement_ids", []),
    ],
)
def test_each_disposition_equals_its_route_and_neighbor_closure(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(document)
    disposition = next(item for item in broken["dispositions"] if item["concept_id"] == "V82-M02")
    disposition[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("target", "field", "replacement"),
    [
        ("obligation", "concept_id", "V82-M03"),
        ("obligation", "status", "applied"),
        ("obligation", "route_ids", []),
        ("obligation", "contract_ids", []),
        ("obligation", "requirement_ids", []),
        ("obligation", "evidence_ids", []),
        ("obligation", "unknown_ids", []),
        ("obligation", "transformation_ids", []),
        ("obligation", "condition_branch_id", "BRANCH-V82-M03"),
        ("disposition", "obligation_ids", ["OBLIGATION-MISSING"]),
    ],
)
def test_obligation_is_not_orphaned_or_cross_concept_and_matches_every_field(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    target: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(document)
    if target == "obligation":
        record = next(item for item in broken["semantic_obligations"] if item["concept_id"] == "V82-M02")
    else:
        record = next(item for item in broken["dispositions"] if item["concept_id"] == "V82-M02")
    record[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


def test_orphan_semantic_obligation_is_rejected(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    broken = copy.deepcopy(document)
    orphan = copy.deepcopy(broken["semantic_obligations"][0])
    orphan["obligation_id"] = "OBLIGATION-ORPHAN"
    orphan["semantic_unit_id"] = "SEMANTIC-UNIT-ORPHAN"
    broken["semantic_obligations"].append(orphan)
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("concept_id", "field", "replacement"),
    [
        ("V82-M02", "condition_branch", None),
        ("V82-M01", "condition_branch", {
            "branch_id": "BRANCH-NONPENDING",
            "condition": "This branch is forbidden for a nonpending disposition.",
            "evidence_plan": {"plan_id": "PLAN-NONPENDING", "required_evidence": ["forbidden"]},
        }),
    ],
)
def test_pending_branch_is_exact_and_nonpending_branch_is_null(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    concept_id: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(document)
    record = next(item for item in broken["dispositions"] if item["concept_id"] == concept_id)
    record[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize("duplicate_kind", ["rationale", "obligation", "unit", "branch", "plan"])
def test_independent_dispositions_reject_shared_rationale_or_ids(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    duplicate_kind: str,
) -> None:
    broken = copy.deepcopy(document)
    dispositions = broken["dispositions"]
    obligations = broken["semantic_obligations"]
    if duplicate_kind == "rationale":
        dispositions[1]["rationale"] = f"  {dispositions[0]['rationale'].upper()}  "
    elif duplicate_kind == "obligation":
        dispositions[2]["obligation_ids"] = list(dispositions[1]["obligation_ids"])
    elif duplicate_kind == "unit":
        obligations[1]["semantic_unit_id"] = obligations[0]["semantic_unit_id"]
    elif duplicate_kind == "branch":
        pending = [item for item in dispositions if item["status"] == "unknown-pending"]
        pending[1]["condition_branch"]["branch_id"] = pending[0]["condition_branch"]["branch_id"]
    else:
        pending = [item for item in dispositions if item["status"] == "unknown-pending"]
        pending[1]["condition_branch"]["evidence_plan"]["plan_id"] = pending[0]["condition_branch"]["evidence_plan"]["plan_id"]
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize("copied_kind", ["rationale", "pending-branch"])
def test_concept_id_status_and_ordinal_substitution_cannot_hide_copied_boilerplate(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    copied_kind: str,
) -> None:
    broken = copy.deepcopy(document)
    dispositions = {record["concept_id"]: record for record in broken["dispositions"]}
    if copied_kind == "rationale":
        dispositions["V82-M01"]["rationale"] = (
            "Decision 1 for V82-M01 is applied because one generic route record remains."
        )
        dispositions["V82-M05"]["rationale"] = (
            "Decision 5 for V82-M05 is tested-rejected because one generic route record remains."
        )
    else:
        dispositions["V82-M02"]["condition_branch"]["condition"] = (
            "Pending condition 2 for V82-M02 is unknown-pending until one generic test."
        )
        dispositions["V82-M02"]["condition_branch"]["evidence_plan"][
            "required_evidence"
        ] = ["Evidence item 2 for V82-M02 must satisfy one generic test."]
        dispositions["V82-M03"]["condition_branch"]["condition"] = (
            "Pending condition 3 for V82-M03 is applied until one generic test."
        )
        dispositions["V82-M03"]["condition_branch"]["evidence_plan"][
            "required_evidence"
        ] = ["Evidence item 3 for V82-M03 must satisfy one generic test."]
    broken = rehash_artifact(broken)
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize("ordinal_style", ["ascii", "wrapped", "unicode"])
def test_roman_ordinal_variants_cannot_hide_nine_record_copied_rationales(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    ordinal_style: str,
) -> None:
    broken = copy.deepcopy(document)
    ordinals = (
        UNICODE_ROMAN_ORDINALS
        if ordinal_style == "unicode"
        else ASCII_ROMAN_ORDINALS
    )
    for ordinal, disposition in zip(ordinals, broken["dispositions"], strict=True):
        rendered = f"[{ordinal}]、" if ordinal_style == "wrapped" else ordinal
        disposition["rationale"] = (
            f"Disposition {rendered} for {disposition['concept_id']} is "
            f"{disposition['status']} under one copied closure rationale."
        )
    broken = rehash_artifact(broken)
    expected_content, expected_artifact = ROMAN_REGRESSION_HASHES[ordinal_style]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("ordinal_style", "ordinals"),
    [
        ("english-cardinal", ENGLISH_CARDINAL_ORDINALS),
        ("english-ordinal", ENGLISH_POSITION_ORDINALS),
        ("chinese-ordinal", CHINESE_ORDINALS),
    ],
)
def test_word_and_explicit_chinese_ordinals_cannot_hide_copied_rationales(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    ordinal_style: str,
    ordinals: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(document)
    for ordinal, disposition in zip(ordinals, broken["dispositions"], strict=True):
        disposition["rationale"] = (
            f"Disposition [{ordinal}] for {disposition['concept_id']} is "
            f"{disposition['status']} under one copied closure rationale."
        )
    broken = rehash_artifact(broken)
    expected_content, expected_artifact = ROMAN_REGRESSION_HASHES[ordinal_style]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


def test_unicode_format_invisibles_cannot_create_distinct_rationale_skeletons(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    broken = copy.deepcopy(document)
    for ordinal, invisible, disposition in zip(
        range(1, 10), FORMAT_SEPARATORS, broken["dispositions"], strict=True
    ):
        disposition["rationale"] = (
            f"Disposition {ordinal}{invisible} for {disposition['concept_id']} is "
            f"{disposition['status']} under one copied closure rationale."
        )
    broken = rehash_artifact(broken)
    expected_content, expected_artifact = ROMAN_REGRESSION_HASHES[
        "format-invisible"
    ]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


def test_roman_letter_substrings_inside_words_and_identifiers_remain_distinct(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    distinct = copy.deepcopy(document)
    distinct["dispositions"][0]["rationale"] = (
        "A civil ZONE-ONESELF inventory preserves the aggregation partition."
    )
    distinct["dispositions"][1]["rationale"] = (
        "A mix of milestone identifiers leaves the causal nesting branch unresolved."
    )
    distinct = rehash_artifact(distinct)
    expected_content, expected_artifact = ROMAN_REGRESSION_HASHES[
        "word-nonregression"
    ]
    assert distinct["content_sha256"] == expected_content
    assert canonical_sha256(distinct) == expected_artifact
    validate_document(distinct, evidence, world, transformations)


@pytest.mark.parametrize(
    ("punctuation_style", "separators"),
    [
        ("ascii-punctuation", (",", ";", ":", "!", "?", "/", "|", "+", "=")),
        ("cjk-punctuation", ("，", "；", "：", "！", "？", "、", "（", "）", "【")),
    ],
)
def test_punctuation_variants_cannot_create_independent_rationale_skeletons(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    punctuation_style: str,
    separators: tuple[str, ...],
) -> None:
    broken = copy.deepcopy(document)
    for ordinal, separator, disposition in zip(
        range(1, 10), separators, broken["dispositions"], strict=True
    ):
        disposition["rationale"] = (
            f"Disposition{separator}{ordinal}{separator}for{separator}"
            f"{disposition['concept_id']}{separator}is{separator}"
            f"{disposition['status']}{separator}under one copied closure rationale"
        )
    broken = rehash_artifact(broken)
    expected_content, expected_artifact = ROMAN_REGRESSION_HASHES[
        punctuation_style
    ]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


def test_semantic_comparison_operators_remain_distinct_rationale_tokens(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    distinct = copy.deepcopy(document)
    distinct["dispositions"][0]["rationale"] = (
        "V82-M01 applied comparison A > B establishes ordered evidence."
    )
    distinct["dispositions"][1]["rationale"] = (
        "V82-M02 unknown-pending comparison A < B establishes ordered evidence."
    )
    distinct = rehash_artifact(distinct)
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        distinct,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    assert validate_document(distinct, evidence, world, transformations)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("evidence_ids", ["EVIDENCE-MISSING"]),
        ("unknown_ids", ["UNKNOWN-MISSING"]),
        ("transformation_ids", ["TRANSFORM-MISSING"]),
    ],
)
def test_disposition_references_reach_sealed_u3_u4_u5_artifacts(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(document)
    broken["dispositions"][0][field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


@pytest.mark.parametrize(
    ("status", "field"),
    [
        ("applied", "evidence_ids"),
        ("applied", "transformation_ids"),
        ("tested-rejected", "evidence_ids"),
        ("tested-rejected", "transformation_ids"),
    ],
)
def test_substantive_dispositions_retain_evidence_and_transformation_bindings(
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    status: str,
    field: str,
) -> None:
    broken = copy.deepcopy(document)
    disposition = next(
        record for record in broken["dispositions"] if record["status"] == status
    )
    obligation = next(
        record
        for record in broken["semantic_obligations"]
        if record["concept_id"] == disposition["concept_id"]
    )
    disposition[field] = []
    obligation[field] = []
    broken = rehash_artifact(broken)
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(broken, evidence, world, transformations)


def copied_repo_with_references(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    target = repo / "skills" / "crossframe-ultra" / "references"
    target.parent.mkdir(parents=True)
    shutil.copytree(REFERENCES, target)
    return repo


def synchronized_registry_variant(
    repo: Path,
    document: Mapping[str, object],
    variant: str,
) -> tuple[dict[str, Any], str]:
    registry_path = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "concept-registry"
        / "v8.2-concept-registry.json"
    )
    registry = load_json(registry_path)
    concepts = {record["concept_id"]: record for record in registry["concepts"]}
    target = concepts["V82-M09"]
    broken = copy.deepcopy(dict(document))
    dispositions = {
        record["concept_id"]: record for record in broken["dispositions"]
    }
    if variant == "registry-dangling-neighbor":
        target["required_neighbors"] = ["V82-M10"]
        dispositions["V82-M09"]["neighbor_concept_ids"] = ["V82-M10"]
    elif variant == "registry-dangling-prerequisite":
        target["prerequisites"] = ["V82-M10"]
    elif variant == "registry-dangling-conflict":
        target["conflicts"] = ["V82-M10"]
    elif variant == "registry-missing-neighbor-backlink":
        target["required_neighbors"] = ["V82-M08"]
        dispositions["V82-M09"]["neighbor_concept_ids"] = ["V82-M08"]
    elif variant == "registry-missing-conflict-backlink":
        target["conflicts"] = ["V82-M08"]
    elif variant == "registry-invalid-source-anchor":
        target["source_anchors"][0] = "V82-P9999"
    elif variant == "registry-semantic-unsupported":
        target["canonical_zh"] = "伪造概念"
    elif variant in {
        "registry-neighbor-route-incomplete",
        "registry-neighbor-route-complete",
    }:
        concepts["V82-M01"]["required_neighbors"] = ["V82-M02"]
        concepts["V82-M02"]["required_neighbors"] = ["V82-M01"]
        dispositions["V82-M01"]["neighbor_concept_ids"] = ["V82-M02"]
        dispositions["V82-M02"]["neighbor_concept_ids"] = ["V82-M01"]
        dispositions["V82-M01"]["route_required"] = True
        if variant == "registry-neighbor-route-complete":
            obligations = {
                record["concept_id"]: record
                for record in broken["semantic_obligations"]
            }
            route_ids = ["V82-ROUTE-AGGREGATION"]
            contract_ids = [
                "V82-CONTRACT-CORE-KERNEL",
                "V82-CONTRACT-TRANSFORMATION",
            ]
            requirement_ids = ["V82-REQ-SP-AXES"]
            for record in (dispositions["V82-M01"], obligations["V82-M01"]):
                record["route_ids"] = list(route_ids)
                record["contract_ids"] = list(contract_ids)
                record["requirement_ids"] = list(requirement_ids)
            broken["required_contract_ids"] = sorted(
                set(broken["required_contract_ids"]) | set(contract_ids)
            )
    else:
        raise AssertionError(f"unknown registry variant: {variant}")
    authority_sha256 = write_authority_json(registry_path, registry)
    broken["registry_sha256"] = authority_sha256
    return rehash_artifact(broken), authority_sha256


def synchronized_route_variant(
    repo: Path,
    document: Mapping[str, object],
    variant: str,
) -> tuple[dict[str, Any], str]:
    route_path = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "v8.2-route-map.json"
    )
    route_map = load_json(route_path)
    routes = {record["route_id"]: record for record in route_map["routes"]}
    broken = copy.deepcopy(dict(document))
    dispositions = {
        record["concept_id"]: record for record in broken["dispositions"]
    }
    obligations = {
        record["concept_id"]: record for record in broken["semantic_obligations"]
    }
    if variant == "route-empty-required":
        routes["V82-ROUTE-CIRCLE-NESTING"]["concept_ids"] = []
        dispositions["V82-M02"]["route_required"] = False
        for record in (dispositions["V82-M02"], obligations["V82-M02"]):
            record["route_ids"] = []
            record["contract_ids"] = []
            record["requirement_ids"] = []
    elif variant == "route-uncovered-concept":
        routes["V82-ROUTE-LATERAL-TRANSFER"]["concept_ids"] = ["V82-M08"]
    elif variant == "route-owner-omission":
        route = routes["V82-ROUTE-CIRCLE-NESTING"]
        route["contract_ids"].remove("V82-CONTRACT-WORLD-VOLUME")
        for record in (dispositions["V82-M02"], obligations["V82-M02"]):
            record["contract_ids"] = list(route["contract_ids"])
    elif variant == "route-unknown-requirement":
        routes["V82-ROUTE-LATERAL-TRANSFER"]["requirement_ids"] = [
            "V82-REQ-UNKNOWN"
        ]
    elif variant == "route-semantic-unsupported":
        route_map["routes"][0]["task"] = (
            "这是一条与所引源文本完全无关的伪造路线。"
        )
    else:
        raise AssertionError(f"unknown route variant: {variant}")
    authority_sha256 = write_authority_json(route_path, route_map)
    broken["route_map_sha256"] = authority_sha256
    return rehash_artifact(broken), authority_sha256


def synchronized_contract_variant(
    repo: Path,
    document: Mapping[str, object],
    variant: str,
) -> tuple[dict[str, Any], str]:
    contracts_dir = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "concept-contracts"
    )
    contract_map_path = contracts_dir / "v8.2-contract-map.json"
    contract_map = load_json(contract_map_path)
    entries = {
        record["contract_id"]: record for record in contract_map["contracts"]
    }
    if variant == "contract-duplicate-file":
        source = entries["V82-CONTRACT-CORE-KERNEL"]
        target = entries["V82-CONTRACT-TRANSFORMATION"]
        target["file"] = source["file"]
        target["file_sha256"] = source["file_sha256"]
    else:
        entry = entries[
            "V82-CONTRACT-CORE-KERNEL"
            if variant == "contract-semantic-unsupported"
            else "V82-CONTRACT-TRANSFORMATION"
        ]
        contract_path = contracts_dir / entry["file"]
        contract = load_json(contract_path)
        if variant == "contract-schema-invalid":
            contract = {}
        elif variant == "contract-metadata-mismatch":
            contract["concept_ids"] = contract["concept_ids"][:-1]
        elif variant == "contract-escaped-source-ref":
            contract["machine_requirements"][0]["source_refs"].append("V82-P0001")
        elif variant == "contract-semantic-unsupported":
            contract["responsibility"] = (
                "这是一条与所引源文本完全无关的伪造责任说明。"
            )
        else:
            raise AssertionError(f"unknown contract variant: {variant}")
        entry["file_sha256"] = write_authority_json(contract_path, contract)
    authority_sha256 = write_authority_json(contract_map_path, contract_map)
    broken = copy.deepcopy(dict(document))
    broken["contract_map_sha256"] = authority_sha256
    return rehash_artifact(broken), authority_sha256


def assert_fixed_authority_variant(
    document: Mapping[str, object],
    authority_sha256: str,
    variant: str,
) -> None:
    expected = AUTHORITY_REGRESSION_HASHES[variant]
    assert authority_sha256 == expected["authority"]
    assert document["content_sha256"] == expected["content"]
    assert canonical_sha256(document) == expected["artifact"]
    validate_phase_artifact(
        "ultra-concept-disposition.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.concept-disposition",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("concept-registry") / "v8.2-concept-registry.json",
        Path("v8.2-route-map.json"),
        Path("concept-contracts") / "v8.2-contract-map.json",
    ],
)
def test_each_knowledge_authority_hash_is_recomputed_from_raw_file_bytes(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    relative_path: Path,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    target_path = repo / "skills" / "crossframe-ultra" / "references" / relative_path
    target_path.write_bytes(target_path.read_bytes() + b"\n")
    with pytest.raises(ConceptClosureError):
        validate_document(
            document,
            evidence,
            world,
            transformations,
            repo=repo,
        )


def test_contract_map_recomputes_each_listed_file_sha256(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    repo = copied_repo_with_references(tmp_path)
    contract_path = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "concept-contracts"
        / "transformation-contracts.json"
    )
    contract_path.write_bytes(contract_path.read_bytes() + b"\n")
    with pytest.raises(ConceptClosureError):
        validate_document(
            document,
            evidence,
            world,
            transformations,
            repo=repo,
        )


@pytest.mark.parametrize(
    "variant",
    [
        "registry-dangling-neighbor",
        "registry-dangling-prerequisite",
        "registry-dangling-conflict",
        "registry-missing-neighbor-backlink",
        "registry-missing-conflict-backlink",
        "registry-invalid-source-anchor",
    ],
)
def test_complete_registry_graph_and_source_anchor_authority_is_validated(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    variant: str,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    broken, authority_sha256 = synchronized_registry_variant(repo, document, variant)
    assert_fixed_authority_variant(broken, authority_sha256, variant)
    with pytest.raises(ConceptClosureError):
        validate_document(
            broken,
            evidence,
            world,
            transformations,
            repo=repo,
            expected_registry_sha256=AUTHORITY_REGRESSION_HASHES[variant][
                "authority"
            ],
        )


@pytest.mark.parametrize(
    ("variant", "should_accept"),
    [
        ("registry-neighbor-route-incomplete", False),
        ("registry-neighbor-route-complete", True),
    ],
)
def test_neighbor_closure_pulls_its_owner_route_contracts_and_requirements(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    variant: str,
    should_accept: bool,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    candidate, authority_sha256 = synchronized_registry_variant(
        repo, document, variant
    )
    assert_fixed_authority_variant(candidate, authority_sha256, variant)
    kwargs = {
        "repo": repo,
        "expected_registry_sha256": AUTHORITY_REGRESSION_HASHES[variant][
            "authority"
        ],
    }
    if should_accept:
        retained = validate_document(
            candidate,
            evidence,
            world,
            transformations,
            **kwargs,
        )
        assert retained == frozenset(
            record["semantic_unit_id"]
            for record in candidate["semantic_obligations"]
        )
    else:
        with pytest.raises(ConceptClosureError):
            validate_document(
                candidate,
                evidence,
                world,
                transformations,
                **kwargs,
            )


@pytest.mark.parametrize(
    "variant",
    [
        "route-empty-required",
        "route-uncovered-concept",
        "route-owner-omission",
        "route-unknown-requirement",
    ],
)
def test_complete_route_partition_and_requirement_owner_authority_is_validated(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    variant: str,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    broken, authority_sha256 = synchronized_route_variant(repo, document, variant)
    assert_fixed_authority_variant(broken, authority_sha256, variant)
    with pytest.raises(ConceptClosureError):
        validate_document(
            broken,
            evidence,
            world,
            transformations,
            repo=repo,
            expected_route_map_sha256=AUTHORITY_REGRESSION_HASHES[variant][
                "authority"
            ],
        )


@pytest.mark.parametrize(
    "variant",
    [
        "contract-schema-invalid",
        "contract-metadata-mismatch",
        "contract-duplicate-file",
        "contract-escaped-source-ref",
    ],
)
def test_contract_documents_and_map_relationships_are_validated_after_resealing(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    variant: str,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    broken, authority_sha256 = synchronized_contract_variant(repo, document, variant)
    assert_fixed_authority_variant(broken, authority_sha256, variant)
    with pytest.raises(ConceptClosureError):
        validate_document(
            broken,
            evidence,
            world,
            transformations,
            repo=repo,
            expected_contract_map_sha256=AUTHORITY_REGRESSION_HASHES[variant][
                "authority"
            ],
        )


@pytest.mark.parametrize(
    ("family", "variant", "expected_keyword"),
    [
        (
            "registry",
            "registry-semantic-unsupported",
            "expected_registry_sha256",
        ),
        (
            "contract",
            "contract-semantic-unsupported",
            "expected_contract_map_sha256",
        ),
        (
            "route",
            "route-semantic-unsupported",
            "expected_route_map_sha256",
        ),
    ],
)
def test_externally_resealed_authority_still_requires_source_semantic_support(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
    family: str,
    variant: str,
    expected_keyword: str,
) -> None:
    repo = copied_repo_with_references(tmp_path)
    builders = {
        "registry": synchronized_registry_variant,
        "contract": synchronized_contract_variant,
        "route": synchronized_route_variant,
    }
    broken, authority_sha256 = builders[family](repo, document, variant)
    assert_fixed_authority_variant(broken, authority_sha256, variant)
    fixed_expected = AUTHORITY_REGRESSION_HASHES[variant]["authority"]
    with pytest.raises(ConceptClosureError):
        validate_document(
            broken,
            evidence,
            world,
            transformations,
            repo=repo,
            **{expected_keyword: fixed_expected},
        )


def test_unlisted_contract_document_is_rejected_as_an_orphan(
    tmp_path: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    world: dict[str, Any],
    transformations: dict[str, Any],
) -> None:
    repo = copied_repo_with_references(tmp_path)
    contracts = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "concept-contracts"
    )
    shutil.copyfile(
        contracts / "core-kernel-contracts.json",
        contracts / "orphan-contract.json",
    )
    with pytest.raises(ConceptClosureError):
        validate_document(
            document,
            evidence,
            world,
            transformations,
            repo=repo,
        )
