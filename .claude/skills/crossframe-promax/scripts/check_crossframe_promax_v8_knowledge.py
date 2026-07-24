from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata
from urllib.parse import unquote

from jsonschema import Draft202012Validator


SNAPSHOT_SHA256 = "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
CANONICAL_CONCEPT_COUNT = 709
CANONICAL_INVENTORY_SHA256 = "e30de5dc667c0a4075c205f61f00aab729a7683ba6c70abb4c137a612d6b5635"
REGISTRY_FILE_SHA256 = "a9f2e57c3fb7147aaab8a291f5ebaf130ada5abb84ae58c0ca1797bb7a3d5b6f"
CONTRACT_MAP_FILE_SHA256 = "601a739c5ce8f994e4832e1e1d57973be52c2522d2c2f464ee403a73cae65c8e"
ROUTE_MAP_FILE_SHA256 = "ef084b0cd98fd6de01dd40f2701b4b010f3041e83f5e38c68556e9288f2c2fd0"
BINDING_INVENTORY_SHA256 = "f68a403aac09143c4057fac030070b4866106db1dd750d022d5f321427ab2d48"
SEMANTIC_COVERAGE_SHA256 = "54d3910dac39c71b64adae363907f9442f9d7ffcbbd23939ee4b0d9f2b48a92c"
CONCEPT_SEMANTIC_SHA256 = "c306710628498553cb53709ea51a40ab969021580713310637be37403b1a42ce"
ROUTE_SEMANTIC_SHA256 = "eb52863b417fb5566a23e2aab00aedab229d728b699d83543e341778a117a510"
SCHEMA_FILE_SHA256 = {
    "source": "74f24b3da3186525a79b4eddec8c1e9ddb2f7755211bb89fc32bf81ccc5b0ff6",
    "registry": "9f77a096eba132a02f57883b7a662df34e59285e2b186711eaffce4914a33b4d",
    "contracts": "3c0bf440900cf92067f02567078655994992c5c1efb2d8144889dae0497a8037",
    "routes": "c44ac7d75d942a25c8960942f3e2fe97a71cbb0f03847696b101b9f81d4e5557",
}
HV_SOURCE_CARD_SCHEMA_ID = "crossframe-promax-v8-human-variable-source-card/1.0.0"
HV_SOURCE_CARD_SHA256 = {
    "V8-CANON-HV01": "05a4321aa97e897ed2175b612c754642f4fbed6d12273c15b187d59fa3d261d3",
    "V8-CANON-HV02": "fe7cd8269a5dd2ae1971f40ef5cdddd8a99ad2b8d3af2e5bc8b05cd27c0d24c6",
    "V8-CANON-HV03": "4ca87e904c9b79f209ba6086d5eaeee572179fdf149331f10c4851206d8562dd",
    "V8-CANON-HV04": "cbc3811171dd029c9674f22bbebedffebbd1391f88351905c525950ff562ef94",
    "V8-CANON-HV05": "dfc1dc9682e4f737ac2cbfe020ed466bd0242a02c8426d4b84eacc798565d287",
    "V8-CANON-HV06": "3c3f1e6bbbf5ecf41ff723c144a733f6567561b2b9a462456b0a578daad1e481",
    "V8-CANON-HV07": "28de39579e664462f9e8c4b3e2f9659fa917a590b5ed74782878784cd001582f",
    "V8-CANON-HV08": "2f26ceff316c36d6a7117fee5e301dc7fd38400aa88bb776c59d2c497ea8f67b",
    "V8-CANON-HV09": "5f03d8e5624ecc9e6a2072d3223eccf17e417dccaddc998ed4c5af2a23cc4ede",
    "V8-CANON-HV10": "d22ff0b2a70c1472b73be3ef4b334da2ac7b89a11b7fd2b2b2f16ae46a61e848",
    "V8-CANON-HV11": "e07fe90611974917bfce08072c44b0e89014d57c8f74bf67ebe57fe1048cfb94",
}
HV_ROUTE_DEPENDENCY_SHA256 = "9709a14f2715b19dd9b7e1a214d4cacba2d5de51015d427cc4d6f45e68eecec9"

CONTRACTS = {
    "v8_actor_state_contracts": (
        "actor-state-contracts.json",
        "11bbd5a920732b2ff9cf7969ac0af70eeb6056f2bdeef51f3f43a4f68cfbfb6d",
        97,
        114,
    ),
    "v8_multicircle_contracts": (
        "multicircle-contracts.json",
        "dd2bf24cef5584839ab26a72878fb2102ab498c56d59297479de449921649964",
        110,
        125,
    ),
    "v8_simulation_forecast_contracts": (
        "simulation-forecast-contracts.json",
        "c0d652560bb1ac25714f806020888ce89ac502a51185885a6e997e7901d08c1d",
        150,
        168,
    ),
}

ROUTE_SOURCES = {
    "V8-ROUTE-01-GUIDE": "01-guide.md",
    "V8-ROUTE-02-BOUNDARY": "02-boundary-method.md",
    "V8-ROUTE-03-GRAMMAR": "03-universal-grammar.md",
    "V8-ROUTE-04-ROOT": "04-root-assumptions.md",
    "V8-ROUTE-05-SCALE": "05-scale-transformation.md",
    "V8-ROUTE-06-OPERATION": "06-operation-evolution.md",
    "V8-ROUTE-07-HUMAN": "07-human-world.md",
    "V8-ROUTE-08-PROTOTYPE": "08-human-state-prototype.md",
    "V8-ROUTE-09-ACTOR": "09-actor-state-personality.md",
    "V8-ROUTE-10-MULTICIRCLE": "10-multicircle-joint-state.md",
    "V8-ROUTE-11-SIMULATION": "11-event-dynamic-deduction.md",
    "V8-ROUTE-12-FORECAST": "12-conditional-forecast-choice.md",
    "V8-ROUTE-13-TOOLS": "13-interface-tools.md",
    "V8-ROUTE-14-NORMATIVE": "14-normative-selection.md",
    "V8-ROUTE-15-INTERVENTION": "15-intervention-applications.md",
    "V8-ROUTE-16-GOVERNANCE": "16-governance.md",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, errors: list[str], label: str) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot load JSON: {exc}")
        return None


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def semantic_pointer_inventory(payload: Any) -> tuple[list[str], list[str]]:
    pointers: list[str] = []
    leaves: list[str] = []

    def walk(node: Any, pointer: str) -> None:
        pointers.append(pointer)
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{pointer}/{pointer_escape(key)}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{pointer}/{index}")
        else:
            leaves.append(pointer)

    for key, value in payload.items():
        if key not in {"schema_id", "schema_version"}:
            walk(value, f"/{pointer_escape(key)}")
    return pointers, leaves


def resolve_pointer(value: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON pointer must start with slash")
    current = value
    for raw_token in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            raise ValueError("invalid JSON pointer escape")
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError("invalid JSON array index")
            current = current[int(token)]
        else:
            current = current[token]
    return current


ENUM_PARENT_POINTERS = {
    "/variable_states",
    "/privacy_levels",
    "/relation_kinds",
    "/relation_transition_results",
    "/condition_channels",
    "/clock_kinds",
    "/event_kinds",
    "/variable_candidate_ledger_schema/allowed_states",
    "/required_option_kinds",
}


def expected_binding_role(pointer: str) -> str:
    tail = pointer.rsplit("/", 1)[-1]
    if pointer == "/scope":
        return "domain"
    if (
        pointer == "/guards"
        or pointer.startswith("/guards/")
        or pointer == "/personality_hypothesis_contract/forbidden_outputs"
        or pointer.startswith("/personality_hypothesis_contract/forbidden_outputs/")
    ):
        return "forbidden"
    if pointer == "/authorization_policy":
        return "action_ceiling"
    if pointer in ENUM_PARENT_POINTERS:
        return "enum_set"
    if pointer == "/timescale_bands" or re.fullmatch(
        r"/timescale_bands/(?:0|[1-9][0-9]*)", pointer
    ):
        return "record_schema"
    if tail == "examples" or "/examples/" in pointer:
        return "example"
    if pointer.rsplit("/", 1)[0] in ENUM_PARENT_POINTERS:
        return "enum_value"
    if tail == "required_fields":
        return "constraint"
    if "/required_fields/" in pointer:
        return "required_field"
    if tail.endswith("_schema") or tail.endswith("_contract"):
        return "record_schema"
    if tail in {"name", "definition"}:
        return "definition"
    return "constraint"


def binding_inventory_sha256(contract_map: dict[str, Any]) -> str:
    rows = []
    for contract in contract_map.get("contracts", []):
        for binding in contract.get("bindings", []):
            rows.append([
                contract.get("contract_id"),
                binding.get("json_pointer"),
                binding.get("concept_id"),
                binding.get("binding_role"),
                [
                    [anchor.get("anchor_id"), anchor.get("source_file")]
                    for anchor in binding.get("source_anchors", [])
                ],
            ])
    encoded = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":")) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def concept_semantic_sha256(registry: dict[str, Any]) -> str:
    return canonical_json_sha256(registry.get("concepts", []))


def route_semantic_sha256(route_map: dict[str, Any]) -> str:
    return canonical_json_sha256(route_map.get("routes", []))


def semantic_coverage_sha256(contract_map: dict[str, Any]) -> str:
    rows = []
    for contract in contract_map.get("contracts", []):
        contract_id = contract.get("contract_id")
        for binding in contract.get("bindings", []):
            rows.append([
                "bound",
                contract_id,
                binding.get("json_pointer"),
                binding.get("concept_id"),
                binding.get("binding_role"),
                [
                    [anchor.get("anchor_id"), anchor.get("source_file")]
                    for anchor in binding.get("source_anchors", [])
                ],
            ])
        for unbound in contract.get("unbound_semantic_pointers", []):
            rows.append([
                "unbound",
                contract_id,
                unbound.get("json_pointer"),
                unbound.get("reason_code"),
                unbound.get("runtime_requirement"),
            ])
    encoded = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":")) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


EXPECTED_BOUND_CONCEPT_IDS: dict[str, dict[str, list[str]]] = {'v8_actor_state_contracts': {'/actor_record_schema': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/0': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/1': ['V8-CANON-D0-T'],
                              '/actor_record_schema/required_fields/2': ['V8-CANON-D0-SP'],
                              '/actor_record_schema/required_fields/3': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/actor_record_schema/required_fields/4': ['V8-CANON-ROLE-ACTIVATION'],
                              '/actor_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/6': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/7': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                                         'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                                         'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                                         'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                                         'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/actor_record_schema/required_fields/8': ['V8-CANON-ACTOR-STATE'],
                              '/guards': ['V8-CANON-ACTOR-STATE'],
                              '/guards/0': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/guards/1': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                            'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                            'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/guards/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/guards/3': ['V8-CANON-ROLE-ACTIVATION'],
                              '/guards/4': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                            'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                            'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                            'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                            'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/guards/5': ['V8-CANON-CORE-TERM-AUTHORIZATION'],
                              '/guards/6': ['V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/personality_hypothesis_contract': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/0': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/1': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/3': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/4': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/personality_hypothesis_contract/required_fields/10': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/personality_hypothesis_contract/required_fields/11': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/12': ['V8-CANON-D0-T'],
                              '/personality_hypothesis_contract/required_fields/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/3': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/4': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/5': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/6': ['V8-CANON-D0-T'],
                              '/personality_hypothesis_contract/required_fields/7': ['V8-CANON-SOURCE-CONTRACT'],
                              '/personality_hypothesis_contract/required_fields/8': ['V8-CANON-E4'],
                              '/personality_hypothesis_contract/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/personality_hypothesis_contract/status': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/privacy_levels': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                  'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                  'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                  'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                  'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/privacy_levels/0': ['V8-CANON-VOCAB-PRIVACY-PUBLIC'],
                              '/privacy_levels/1': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED'],
                              '/privacy_levels/2': ['V8-CANON-VOCAB-PRIVACY-SENSITIVE'],
                              '/privacy_levels/3': ['V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE'],
                              '/privacy_levels/4': ['V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/scope': ['V8-CANON-ACTOR-STATE'],
                              '/timescale_bands': ['V8-CANON-VOCAB-ACTOR-BAND-FAST',
                                                   'V8-CANON-VOCAB-ACTOR-BAND-MEDIUM',
                                                   'V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/definition': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/id': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/name': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/1': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/definition': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/id': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/name': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/2': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/definition': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/id': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/name': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/variable_record_schema': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/10': ['V8-CANON-E4'],
                              '/variable_record_schema/required_fields/11': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/variable_record_schema/required_fields/12': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_record_schema/required_fields/13': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                                             'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                                             'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                                             'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                                             'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/variable_record_schema/required_fields/14': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/15': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/3': ['V8-CANON-VOCAB-ACTOR-BAND-FAST',
                                                                            'V8-CANON-VOCAB-ACTOR-BAND-MEDIUM',
                                                                            'V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/variable_record_schema/required_fields/4': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/6': ['V8-CANON-D0-T'],
                              '/variable_record_schema/required_fields/7': ['V8-CANON-SOURCE-CONTRACT'],
                              '/variable_record_schema/required_fields/8': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/9': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/state_upgrade_rule': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/variable_record_schema/unknown_rule': ['V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states/0': ['V8-CANON-VOCAB-ACTOR-STATE-OBSERVED'],
                              '/variable_states/1': ['V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/variable_states/2': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE'],
                              '/variable_states/3': ['V8-CANON-VOCAB-ACTOR-STATE-CONTESTED'],
                              '/variable_states/4': ['V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states/5': ['V8-CANON-VOCAB-ACTOR-STATE-RETIRED']},
 'v8_multicircle_contracts': {'/circle_record_schema': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/object_rule': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/0': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/10': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/circle_record_schema/required_fields/11': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/12': ['V8-CANON-D0-T'],
                              '/circle_record_schema/required_fields/13': ['V8-CANON-D0-SP'],
                              '/circle_record_schema/required_fields/14': ['V8-CANON-D0-K'],
                              '/circle_record_schema/required_fields/15': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/circle_record_schema/required_fields/16': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/circle_record_schema/required_fields/17': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/2': ['V8-CANON-D0-B'],
                              '/circle_record_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/4': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/5': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/6': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/7': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/8': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/9': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/clock_kinds': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                               'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                               'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                               'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                               'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/clock_kinds/0': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE'],
                              '/clock_kinds/1': ['V8-CANON-VOCAB-CLOCK-INTERACTION'],
                              '/clock_kinds/2': ['V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/clock_kinds/3': ['V8-CANON-VOCAB-CLOCK-INSTITUTIONAL'],
                              '/clock_kinds/4': ['V8-CANON-VOCAB-CLOCK-LONG-TERM'],
                              '/condition_channels': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                      'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/condition_channels/0': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/condition_channels/1': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/event_touch_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/asynchronous_rule': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/event_touch_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/event_touch_schema/required_fields/3': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/4': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                        'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/event_touch_schema/required_fields/5': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                        'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                        'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                        'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                        'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/event_touch_schema/required_fields/6': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/8': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/guards': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/guards/0': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/guards/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/guards/2': ['V8-CANON-CROSS-CHANNEL-BRIDGE-M-PSI-CLOSED-LOOP',
                                            'V8-CANON-CROSS-CHANNEL-BRIDGE-M-TO-PSI',
                                            'V8-CANON-CROSS-CHANNEL-BRIDGE-PSI-TO-M',
                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/guards/3': ['V8-CANON-ACTOR-CIRCLE-DIRECTION-ACTOR-TO-CIRCLE',
                                            'V8-CANON-ACTOR-CIRCLE-DIRECTION-BIDIRECTIONAL-FEEDBACK',
                                            'V8-CANON-ACTOR-CIRCLE-DIRECTION-CIRCLE-TO-ACTOR'],
                              '/guards/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/guards/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/1': ['V8-CANON-D0-T'],
                              '/joint_state_schema/required_fields/10': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                         'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                         'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                         'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                         'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/joint_state_schema/required_fields/11': ['V8-CANON-D0-SP'],
                              '/joint_state_schema/required_fields/12': ['V8-CANON-D0-T'],
                              '/joint_state_schema/required_fields/13': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/14': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/15': ['V8-CANON-D0-K'],
                              '/joint_state_schema/required_fields/16': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/2': ['V8-CANON-ACTOR-STATE'],
                              '/joint_state_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/joint_state_schema/required_fields/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/6': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/joint_state_schema/required_fields/7': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/joint_state_schema/required_fields/8': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                        'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/joint_state_schema/required_fields/9': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/1': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/10': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/membership_record_schema/required_fields/3': ['V8-CANON-ROLE-ACTIVATION'],
                              '/membership_record_schema/required_fields/4': ['V8-CANON-D0-T'],
                              '/membership_record_schema/required_fields/5': ['V8-CANON-D0-T'],
                              '/membership_record_schema/required_fields/6': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/8': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/9': ['V8-CANON-SOURCE-CONTRACT'],
                              '/relation_kinds': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_kinds/0': ['V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL'],
                              '/relation_kinds/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-NESTED'],
                              '/relation_kinds/2': ['V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING'],
                              '/relation_kinds/3': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING'],
                              '/relation_kinds/4': ['V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE'],
                              '/relation_kinds/5': ['V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_record_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/nested_rule': ['V8-CANON-VOCAB-CIRCLE-RELATION-NESTED'],
                              '/relation_record_schema/parallel_rule': ['V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL'],
                              '/relation_record_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_record_schema/required_fields/10': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/11': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/relation_record_schema/required_fields/12': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/relation_record_schema/required_fields/13': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/14': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_record_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/relation_record_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/relation_record_schema/required_fields/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/6': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/relation_record_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/8': ['V8-CANON-D0-T'],
                              '/relation_record_schema/required_fields/9': ['V8-CANON-D0-T'],
                              '/relation_record_schema/transformation_rule': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED'],
                              '/relation_transition_results': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_transition_results/0': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED'],
                              '/relation_transition_results/1': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED'],
                              '/relation_transition_results/2': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_transition_results/3': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED'],
                              '/relation_transition_results/4': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED'],
                              '/relation_transition_results/5': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED'],
                              '/relation_transition_results/6': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN'],
                              '/scope': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT']},
 'v8_simulation_forecast_contracts': {'/authorization_policy': ['V8-CANON-FORECAST-ACTION-CEILING',
                                                                'V8-CANON-O3',
                                                                'V8-CANON-SCALE-AXIS-J'],
                                      '/baseline_policy': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/event_kinds': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL',
                                                       'V8-CANON-VOCAB-EVENT-OBSERVED',
                                                       'V8-CANON-VOCAB-EVENT-PLANNED',
                                                       'V8-CANON-VOCAB-EVENT-REPORTED',
                                                       'V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_kinds/0': ['V8-CANON-VOCAB-EVENT-OBSERVED'],
                                      '/event_kinds/1': ['V8-CANON-VOCAB-EVENT-REPORTED'],
                                      '/event_kinds/2': ['V8-CANON-VOCAB-EVENT-PLANNED'],
                                      '/event_kinds/3': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL'],
                                      '/event_kinds/4': ['V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_record_schema/required_fields/1': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL',
                                                                                 'V8-CANON-VOCAB-EVENT-OBSERVED',
                                                                                 'V8-CANON-VOCAB-EVENT-PLANNED',
                                                                                 'V8-CANON-VOCAB-EVENT-REPORTED',
                                                                                 'V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_record_schema/required_fields/11': ['V8-CANON-E4'],
                                      '/event_record_schema/required_fields/13': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/14': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/event_record_schema/required_fields/2': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/4': ['V8-CANON-SOURCE-CONTRACT'],
                                      '/event_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                                      '/event_record_schema/required_fields/6': ['V8-CANON-CIRCLE-CANDIDATE'],
                                      '/event_record_schema/required_fields/7': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                                 'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                                      '/event_record_schema/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/forecast_record_schema': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/comparison_rule': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/forecast_record_schema/metric_rule': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION',
                                                                              'V8-CANON-FORECAST-EVALUATION-COVERAGE'],
                                      '/forecast_record_schema/required_fields': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/0': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/1': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/10': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/forecast_record_schema/required_fields/11': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/12': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION'],
                                      '/forecast_record_schema/required_fields/13': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/14': ['V8-CANON-FORECAST-SIGNAL-EARLY'],
                                      '/forecast_record_schema/required_fields/15': ['V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/forecast_record_schema/required_fields/16': ['V8-CANON-FORECAST-SIGNAL-TRIGGER'],
                                      '/forecast_record_schema/required_fields/17': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/18': ['V8-CANON-DF9'],
                                      '/forecast_record_schema/required_fields/19': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/2': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/20': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/forecast_record_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/4': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/5': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/6': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/7': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/8': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/forecast_record_schema/required_fields/9': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/guards': ['V8-CANON-DF9',
                                                  'V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST',
                                                  'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE',
                                                  'V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/guards/0': ['V8-CANON-BRANCHING-PATH-GRAPH',
                                                    'V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/guards/1': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/guards/2': ['V8-CANON-DF9',
                                                    'V8-CANON-FORECAST-EVALUATION-CALIBRATION',
                                                    'V8-CANON-FORECAST-REGISTRY',
                                                    'V8-CANON-FORECAST-SIGNAL-TRIGGER',
                                                    'V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/guards/3': ['V8-CANON-FORECAST-ACTION-CEILING',
                                                    'V8-CANON-O3',
                                                    'V8-CANON-SCALE-AXIS-J'],
                                      '/guards/4': ['V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                    'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/guards/5': ['V8-CANON-DF9'],
                                      '/guards/6': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/option_record_schema': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/1': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-DELAYED-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER',
                                                                                  'V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO',
                                                                                  'V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/option_record_schema/required_fields/10': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/11': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/12': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/13': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/14': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/15': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/16': ['V8-CANON-SCALE-AXIS-J'],
                                      '/option_record_schema/required_fields/17': ['V8-CANON-DF8'],
                                      '/option_record_schema/required_fields/18': ['V8-CANON-DF8'],
                                      '/option_record_schema/required_fields/2': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/3': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/option_record_schema/required_fields/4': ['V8-CANON-N1',
                                                                                  'V8-CANON-N2',
                                                                                  'V8-CANON-N3',
                                                                                  'V8-CANON-N4',
                                                                                  'V8-CANON-N5'],
                                      '/option_record_schema/required_fields/5': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/6': ['V8-CANON-PF-1',
                                                                                  'V8-CANON-PF-10',
                                                                                  'V8-CANON-PF-2',
                                                                                  'V8-CANON-PF-3',
                                                                                  'V8-CANON-PF-4',
                                                                                  'V8-CANON-PF-5',
                                                                                  'V8-CANON-PF-6',
                                                                                  'V8-CANON-PF-7',
                                                                                  'V8-CANON-PF-8',
                                                                                  'V8-CANON-PF-9'],
                                      '/option_record_schema/required_fields/7': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/option_record_schema/required_fields/8': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/9': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/outcome_writeback_schema': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/1': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/10': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/11': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/12': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/13': ['V8-CANON-D0-T'],
                                      '/outcome_writeback_schema/required_fields/2': ['V8-CANON-D0-T'],
                                      '/outcome_writeback_schema/required_fields/3': ['V8-CANON-SOURCE-CONTRACT'],
                                      '/outcome_writeback_schema/required_fields/4': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/5': ['V8-CANON-VOCAB-FORECAST-RESULT-SUPPORTED',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-TARGET-INVALID',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNASSESSABLE',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNDECIDED',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNSUPPORTED'],
                                      '/outcome_writeback_schema/required_fields/6': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION'],
                                      '/outcome_writeback_schema/required_fields/7': ['V8-CANON-FORECAST-EVALUATION-BASELINE-GAIN',
                                                                                      'V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/outcome_writeback_schema/required_fields/8': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/9': ['V8-CANON-FORECAST-EVALUATION-DISTRIBUTIONAL-ERROR'],
                                      '/path_node_schema': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/dag_rule': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/10': ['V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/path_node_schema/required_fields/11': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/12': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/2': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/3': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/4': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/5': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/6': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                              'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                              'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                              'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                              'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                                      '/path_node_schema/required_fields/7': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/8': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/9': ['V8-CANON-FORECAST-SIGNAL-EARLY'],
                                      '/required_option_kinds': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-DELAYED-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER',
                                                                 'V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO',
                                                                 'V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/required_option_kinds/0': ['V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO'],
                                      '/required_option_kinds/1': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION'],
                                      '/required_option_kinds/2': ['V8-CANON-VOCAB-OPTION-DELAYED-ACTION'],
                                      '/required_option_kinds/3': ['V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/required_option_kinds/4': ['V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER'],
                                      '/required_option_kinds/5': ['V8-CANON-VOCAB-OPTION-NO-ACTION'],
                                      '/scope': ['V8-CANON-DF9',
                                                 'V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST',
                                                 'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE',
                                                 'V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/1': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/10': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/11': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/12': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/simulation_run_schema/required_fields/13': ['V8-CANON-FORECAST-SIGNAL-TRIGGER'],
                                      '/simulation_run_schema/required_fields/2': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                                      '/simulation_run_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/simulation_run_schema/required_fields/4': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/5': ['V8-CANON-SCALE-AXIS-J'],
                                      '/simulation_run_schema/required_fields/6': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/7': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/8': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/variable_candidate_ledger_schema': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/allowed_states': ['V8-CANON-VOCAB-LEDGER-PROPOSED',
                                                                                           'V8-CANON-VOCAB-LEDGER-REJECTED',
                                                                                           'V8-CANON-VOCAB-LEDGER-RETIRED',
                                                                                           'V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE',
                                                                                           'V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/allowed_states/0': ['V8-CANON-VOCAB-LEDGER-PROPOSED'],
                                      '/variable_candidate_ledger_schema/allowed_states/1': ['V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/allowed_states/2': ['V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE'],
                                      '/variable_candidate_ledger_schema/allowed_states/3': ['V8-CANON-VOCAB-LEDGER-REJECTED'],
                                      '/variable_candidate_ledger_schema/allowed_states/4': ['V8-CANON-VOCAB-LEDGER-RETIRED'],
                                      '/variable_candidate_ledger_schema/required_fields': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/1': ['V8-CANON-CANDIDATE-SOURCE-SYSTEM-RESIDUAL'],
                                      '/variable_candidate_ledger_schema/required_fields/10': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/variable_candidate_ledger_schema/required_fields/11': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/12': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/2': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/3': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/4': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/5': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/6': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/7': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/8': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/9': ['V8-CANON-VOCAB-LEDGER-PROPOSED',
                                                                                              'V8-CANON-VOCAB-LEDGER-REJECTED',
                                                                                              'V8-CANON-VOCAB-LEDGER-RETIRED',
                                                                                              'V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE',
                                                                                              'V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/truth_rule': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/writeback_policy': ['V8-CANON-DF9']}}

EXPECTED_UNBOUND_POINTERS: dict[str, set[str]] = {'v8_actor_state_contracts': {'/actor_record_schema/additional_fields',
                              '/actor_record_schema/required_fields/10',
                              '/actor_record_schema/required_fields/9',
                              '/closed',
                              '/personality_hypothesis_contract/required_fields/0',
                              '/variable_record_schema/additional_fields',
                              '/variable_record_schema/required_fields/0',
                              '/variable_record_schema/required_fields/2'},
 'v8_multicircle_contracts': {'/circle_record_schema/additional_fields',
                              '/circle_record_schema/required_fields/1',
                              '/closed',
                              '/event_touch_schema/additional_fields',
                              '/event_touch_schema/required_fields/0',
                              '/joint_state_schema/additional_fields',
                              '/joint_state_schema/required_fields/0',
                              '/joint_state_schema/schema_id',
                              '/membership_record_schema/additional_fields',
                              '/membership_record_schema/required_fields/0',
                              '/relation_record_schema/additional_fields',
                              '/relation_record_schema/required_fields/0'},
 'v8_simulation_forecast_contracts': {'/closed',
                                      '/event_record_schema',
                                      '/event_record_schema/additional_fields',
                                      '/event_record_schema/required_fields',
                                      '/event_record_schema/required_fields/0',
                                      '/event_record_schema/required_fields/10',
                                      '/event_record_schema/required_fields/12',
                                      '/event_record_schema/required_fields/8',
                                      '/forecast_record_schema/additional_fields',
                                      '/option_record_schema/additional_fields',
                                      '/option_record_schema/required_fields/0',
                                      '/outcome_writeback_schema/additional_fields',
                                      '/outcome_writeback_schema/required_fields/0',
                                      '/path_node_schema/additional_fields',
                                      '/path_node_schema/required_fields/0',
                                      '/path_node_schema/required_fields/1',
                                      '/simulation_run_schema/additional_fields',
                                      '/simulation_run_schema/propagation_rule',
                                      '/simulation_run_schema/required_fields/0',
                                      '/simulation_run_schema/required_fields/14',
                                      '/simulation_run_schema/required_fields/9',
                                      '/variable_candidate_ledger_schema/additional_fields',
                                      '/variable_candidate_ledger_schema/required_fields/0'}}

EXPECTED_OWNER_ORACLE_SHA256 = "5f049ab85f0da320e40a7c12d2fae4663e2fca634c664f134e3f81f5f1035be8"


def owner_oracle_sha256(owner_map: dict[str, dict[str, Any]]) -> str:
    rows = [
        [contract_id, pointer, sorted(owners)]
        for contract_id, pointer_map in owner_map.items()
        for pointer, owners in pointer_map.items()
    ]
    encoded = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":")) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()




def paragraph_index(source_root: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    marker = re.compile(r"<!-- source_paragraph:(V8-P\d{4}) style=[^ ]* -->\n")
    for path in sorted(source_root.glob("[01][0-9]-*.md")) + sorted(source_root.glob("0[1-9]-*.md")):
        if path.name.startswith("00-"):
            continue
        text = path.read_text(encoding="utf-8")
        matches = list(marker.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            prose = text[match.end():end].split("\n## Canonical Structure", 1)[0].strip()
            result[match.group(1)] = (path.name, prose)
    return result


def assert_schema_closed(node: Any, label: str, errors: list[str], location: str = "$") -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            if node.get("additionalProperties") is not False:
                errors.append(f"closed schema violation in {label} at {location}")
        for key, value in node.items():
            assert_schema_closed(value, label, errors, f"{location}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            assert_schema_closed(value, label, errors, f"{location}[{index}]")


def check_full_source_integrity(repo: Path) -> list[str]:
    path = repo / "skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py"
    if not path.is_file():
        return [f"source integrity checker missing: {path}"]
    module_name = "crossframe_promax_v8_full_source_dependency"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return [f"source integrity checker cannot load: {path}"]
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return [f"source integrity: {error}" for error in module.check_repository(repo, None)]
    except (OSError, RuntimeError, ValueError) as exc:
        return [f"source integrity checker failed: {exc}"]


def pollution_errors_for_text(text: str, path_label: str) -> list[str]:
    errors: list[str] = []
    ascii_identifier_ignorables = re.compile(
        r"(?<=[A-Za-z0-9_-])[\u200b\u200c\u200d\u2060\ufeff]+"
        r"(?=[A-Za-z0-9_-])"
    )

    def normalize_loader_surface_once(value: str) -> str:
        value = unquote(value, errors="replace")
        value = html.unescape(value)
        value = ascii_identifier_ignorables.sub("", value)
        return unicodedata.normalize("NFKC", value)

    normalized_path = normalize_loader_surface_once(
        path_label.replace("\\", "/").strip("/")
    )
    normalized_text = normalize_loader_surface_once(text)
    lowered_path = normalized_path.casefold()
    decoded_quoted_strings: list[str] = []
    if Path(lowered_path).suffix == ".json":
        json_string = re.compile(
            r'"(?:\\(?:["\\/bfnrt]|u[0-9A-Fa-f]{4})|[^"\\\x00-\x1f])*"'
        )
        for match in json_string.finditer(text):
            try:
                decoded = json.loads(match.group(0))
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(decoded, str):
                decoded_quoted_strings.append(normalize_loader_surface_once(decoded))
    elif Path(lowered_path).suffix in {".yaml", ".yml"}:
        yaml_double_quoted_scalar = re.compile(
            r'"(?:\\(?:["\\/bfnrt]|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|'
            r'x[0-9A-Fa-f]{2})|'
            r'[^"\\\x00-\x1f])*"'
        )
        yaml_hex_escape = re.compile(r"\\x([0-9A-Fa-f]{2})")
        yaml_long_unicode_escape = re.compile(r"\\U([0-9A-Fa-f]{8})")

        def yaml_long_unicode_to_json(match: re.Match[str]) -> str:
            codepoint = int(match.group(1), 16)
            if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                return match.group(0)
            return json.dumps(chr(codepoint), ensure_ascii=True)[1:-1]

        for match in yaml_double_quoted_scalar.finditer(text):
            json_compatible = yaml_long_unicode_escape.sub(
                yaml_long_unicode_to_json,
                match.group(0),
            )
            json_compatible = yaml_hex_escape.sub(
                lambda item: r"\u00" + item.group(1),
                json_compatible,
            )
            try:
                decoded = json.loads(json_compatible)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(decoded, str):
                decoded_quoted_strings.append(normalize_loader_surface_once(decoded))
    scan_surfaces = [normalized_text, normalized_path, *decoded_quoted_strings]
    plain_old_version = re.compile(r"(?i)(?<![A-Za-z0-9.])v(?:[0-7])(?:\.0)?(?![A-Za-z0-9])")
    dotted_old_version = re.compile(
        r"(?i)(?:framework|knowledge|contracts|crossframe)[._-]v(?:[0-7])(?:\.0)?(?![A-Za-z0-9])"
    )
    if any(
        pattern.search(candidate)
        for pattern in (plain_old_version, dotted_old_version)
        for candidate in scan_surfaces
    ):
        errors.append(f"pre-v8 version marker in {path_label}")

    version_family_word = "cross" + "frame"
    version_origin_word = "来" + "源"
    version_context = re.compile(
        rf"(?i)framework|knowledge|contracts?|{version_family_word}|source|"
        rf"{version_origin_word}|框架|知识"
    )
    standalone_prefixed_version = re.compile(
        r"(?i)(?<![A-Za-z0-9.])v(?P<version>\d+(?:\.\d+)*)(?![A-Za-z0-9]|\.\d)"
    )
    dotted_context_version = re.compile(
        rf"(?i)(?:framework|knowledge|contracts?|{version_family_word})[._-]v"
        r"(?P<version>\d+(?:\.\d+)*)(?![A-Za-z0-9]|\.\d)"
    )
    explicit_context_version = re.compile(
        rf"(?i)(?:framework|knowledge|contracts?|{version_family_word}|source|"
        rf"框架|知识|{version_origin_word})"
        r"[._ -]*(?:version|版本)[\s:=._-]*(?:v)?"
        r"(?P<version>\d+(?:\.\d+)*)(?![A-Za-z0-9]|\.\d)"
    )
    numeric_version_subject = (
        rf"(?:framework|knowledge|contracts?|{version_family_word}|source|"
        rf"框架|知识|概念定义|{version_origin_word})"
    )
    context_before_numeric_version = re.compile(
        rf"(?i){numeric_version_subject}"
        r"(?=[^\n]{0,32}(?:version|版本|版))[^\n\d]{0,32}"
        r"(?P<version>\d+(?:\.\d+)+)(?![\d.])"
    )
    numeric_before_context_version = re.compile(
        r"(?i)(?<![\d.])(?P<version>\d+(?:\.\d+)+)(?![\d.])"
        r"\s*(?:version|版本|版)[^\n\d]{0,16}"
        rf"{numeric_version_subject}"
    )
    marker_numeric_before_context = re.compile(
        r"(?i)(?:version|版本|版)[^\n\d]{0,8}"
        r"(?P<version>\d+(?:\.\d+)+)(?![\d.])[^\n\d]{0,16}"
        rf"{numeric_version_subject}"
    )
    legacy_numeric_version = re.compile(
        r"旧(?:版本?|版)[^\n\d]{0,8}"
        r"(?P<version>\d+(?:\.\d+)+)(?![\d.])"
    )

    def is_exact_v8(version: str) -> bool:
        return version.casefold().removeprefix("v") in {"8", "8.0"}

    version_surfaces = [
        *normalized_text.splitlines(),
        normalized_path,
        *decoded_quoted_strings,
    ]
    for candidate in version_surfaces:
        if version_context.search(candidate):
            for match in standalone_prefixed_version.finditer(candidate):
                if not is_exact_v8(match.group("version")):
                    errors.append(f"non-v8 version marker in {path_label}")
        for match in dotted_context_version.finditer(candidate):
            if not is_exact_v8(match.group("version")):
                errors.append(f"non-v8 version marker in {path_label}")
        for match in explicit_context_version.finditer(candidate):
            if not is_exact_v8(match.group("version")):
                errors.append(f"non-v8 version marker in {path_label}")
        for pattern in (
            context_before_numeric_version,
            numeric_before_context_version,
            marker_numeric_before_context,
            legacy_numeric_version,
        ):
            for match in pattern.finditer(candidate):
                if not is_exact_v8(match.group("version")):
                    errors.append(f"non-v8 version marker in {path_label}")

    inherited_path = re.compile(r"(?i)(?:^|[/\\])contracts[/\\]inherited(?:[/\\]|\b)")
    if any(inherited_path.search(candidate) for candidate in scan_surfaces):
        errors.append(f"inherited contract path in {path_label}")
    ancestry_word = "line" + "age"
    ancestry_path = re.compile(
        rf"(?i)(?:^|[/\\]){ancestry_word}(?:\.[^/\\]+|[/\\]|$)"
    )
    if any(ancestry_path.search(candidate) for candidate in scan_surfaces):
        errors.append(f"{ancestry_word} knowledge path in {path_label}")
    for candidate in scan_surfaces:
        for match in re.finditer(
            r"(?<![A-Za-z0-9-])(?:P\d{4}|T\d{3})(?![A-Za-z0-9])",
            candidate,
        ):
            errors.append(f"unprefixed source anchor {match.group(0)} in {path_label}")

    max_word = "m" + "ax"
    family_word = "cross" + "frame"
    route_skill_name = family_word + "-" + max_word
    other_skill = re.compile(
        rf"(?i)(?<![A-Za-z0-9]){family_word}[-_ ]+"
        r"(?P<name>[a-z0-9]+(?:[-_][a-z0-9]+)*)(?![A-Za-z0-9_])"
    )
    compact_other_skill = re.compile(
        rf"(?<![A-Za-z0-9])(?i:{family_word})"
        r"(?P<name>[A-Z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*)"
        r"(?![A-Za-z0-9_])"
    )
    max_skill_alias = re.compile(
        rf"(?i)(?<![A-Za-z0-9]){family_word}[-_ ]*{max_word}(?![A-Za-z0-9_])"
    )
    base_skill_alias = re.compile(
        rf"(?i)(?<![A-Za-z0-9_-]){family_word}"
        r"(?![-_ ]*promax\b)(?![A-Za-z0-9_-])"
    )
    base_skill_path = re.compile(
        rf"(?i)(?<![A-Za-z0-9_.-])skills[/\\]{family_word}(?=[/\\]|$)"
    )
    mirror_skill_path = re.compile(
        rf"(?i)(?<![A-Za-z0-9_.-])\.claude[/\\]skills[/\\]{family_word}"
        r"(?:[-_][a-z0-9]+(?:[-_][a-z0-9]+)*)?(?=[/\\]|$)"
    )
    knowledge_terms = re.compile(
        rf"(?i)knowledge\s+source|concept\s+definition|use\s+{max_word}|read\s+{max_word}|知识|概念定义|来源|采用|读取|补充|继承"
    )
    knowledge_surface = (
        lowered_path.startswith("references/")
        or "/references/" in lowered_path
        or "knowledge" in Path(lowered_path).name
        or "concept-registry" in lowered_path
    )
    control_surface = not knowledge_surface and lowered_path in {
        "skill.md",
        "routing.md",
        "activation.md",
        "design.md",
        "schemas/promax-run-contract.schema.json",
    }
    max_pattern = re.compile(rf"(?i)(?<![A-Za-z0-9_]){max_word}(?![A-Za-z0-9_])")
    schema_route_pattern = re.compile(
        rf'[ \t]*"const"[ \t]*:[ \t]*"{re.escape(route_skill_name)}"[ \t]*,?[ \t]*'
    )
    schema_route_literal_present = (
        lowered_path == "schemas/promax-run-contract.schema.json"
        and any(
            schema_route_pattern.fullmatch(candidate)
            for candidate in normalized_text.splitlines()
        )
    )
    candidate_lines = list(normalized_text.splitlines())
    candidate_lines.extend(decoded_quoted_strings)
    candidate_lines.append(normalized_path)
    for line_number, line in enumerate(candidate_lines, 1):
        unsafe_context = bool(knowledge_terms.search(line))
        sibling_matches = [
            *other_skill.finditer(line),
            *compact_other_skill.finditer(line),
        ]
        other_matches = [
            match
            for match in sibling_matches
            if not match.group("name").casefold().startswith("promax")
        ]
        has_max_alias = bool(max_skill_alias.search(line))
        has_forbidden_path = bool(
            base_skill_path.search(line) or mirror_skill_path.search(line)
        )
        has_base_alias = unsafe_context and bool(base_skill_alias.search(line))
        has_other = (
            bool(other_matches)
            or has_max_alias
            or has_forbidden_path
            or has_base_alias
        )
        has_max = bool(max_pattern.search(line)) or has_max_alias
        if not has_other and not has_max:
            continue
        has_routing = bool(re.search(r"(?i)routing|priority|wins|both\s+named|路由|优先|同时点名|禁止回退", line))
        has_promax = "promax" in line.lower()
        machine_priority = ("PROMAX-PRIORITY-OVER-" + max_word.upper()) in line or ("PROMAX-NO-FALLBACK-TO-" + max_word.upper()) in line
        if (
            not has_other
            and not has_max_alias
            and not (knowledge_surface or control_surface or unsafe_context)
        ):
            continue
        only_priority_other = all(
            match.group("name").casefold() == max_word for match in other_matches
        )
        schema_route_literal = (
            schema_route_literal_present
            and (
                schema_route_pattern.fullmatch(line) is not None
                or line == route_skill_name
            )
            and not unsafe_context
            and only_priority_other
        )
        allowed_priority = control_surface and (
            (has_routing and has_promax and not unsafe_context and only_priority_other)
            or (machine_priority and not unsafe_context and only_priority_other)
            or schema_route_literal
        ) and not has_forbidden_path and not has_base_alias
        if not allowed_priority:
            errors.append(
                f"other {family_word.title()} skill used as knowledge source "
                f"in {path_label}:{line_number}"
            )
    return list(dict.fromkeys(errors))


def scan_version_pollution(skill_root: Path) -> list[str]:
    errors: list[str] = []
    binary_suffixes = {
        ".7z", ".avi", ".bmp", ".doc", ".docx", ".gif", ".gz", ".ico",
        ".jpeg", ".jpg", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt",
        ".pptx", ".pyc", ".tar", ".tif", ".tiff", ".wav", ".webp", ".xls",
        ".xlsx", ".zip",
    }
    for path in sorted(skill_root.rglob("*")):
        relative = path.relative_to(skill_root)
        label = relative.as_posix()
        if any(part.casefold() == "__pycache__" for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(f"symbolic link is forbidden in skill assets: {label}")
            continue
        errors.extend(pollution_errors_for_text("", label))
        if not path.is_file():
            continue
        if path.suffix.casefold() in binary_suffixes:
            errors.append(f"binary asset prohibited by v8 version isolation: {label}")
            continue
        try:
            raw = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot scan {path}: {exc}")
            continue
        is_generation_lock = label == "references/.v8-full-source.lock"
        if b"\x00" in raw and not is_generation_lock:
            errors.append(f"NUL byte in text asset: {label}")
        if b"\x00" in raw:
            raw = raw.replace(b"\x00", b"")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            errors.append(f"unscannable non-UTF-8 text asset: {label}: {exc}")
            text = raw.decode("utf-8-sig", errors="ignore")
        errors.extend(pollution_errors_for_text(text, label))
    return errors


def parse_hv_route_source(raw_text: str) -> list[dict[str, str]]:
    field_names = (
        "claim_level", "when", "additional_inferential_requires",
        "additional_protocol_requires", "allowed_conclusion", "result_ceiling",
    )
    starts = list(re.finditer(r"(?:^|(?<=。))\d+\. route_id=([^；]+)；", raw_text))
    result: list[dict[str, str]] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(raw_text)
        fragment = raw_text[match.start():end].strip()
        route = {"route_id": match.group(1), "source_text": fragment}
        for field_index, field in enumerate(field_names):
            marker = f"{field}="
            start = fragment.index(marker) + len(marker)
            if field_index + 1 < len(field_names):
                stop = fragment.index(f"；{field_names[field_index + 1]}=", start)
                route[field] = fragment[start:stop].strip()
            else:
                route[field] = fragment[start:].strip()
        result.append(route)
    return result


def validate_hv_source_cards(
    concepts: dict[str, dict[str, Any]],
    anchors: dict[str, tuple[str, str]],
    errors: list[str],
) -> None:
    hv_ids = {
        concept_id
        for concept_id, concept in concepts.items()
        if concept.get("concept_type") == "human_variable_interface"
    }
    if hv_ids != set(HV_SOURCE_CARD_SHA256):
        errors.append("HV source-card concept inventory mismatch")
    card_ids = {concept_id for concept_id, concept in concepts.items() if "source_card" in concept}
    if card_ids != hv_ids:
        errors.append("source_card must exist for and only for HV01-HV11")
    route_count = 0
    route_dependency_rows: list[list[Any]] = []
    for concept_id in sorted(hv_ids & set(HV_SOURCE_CARD_SHA256)):
        concept = concepts[concept_id]
        card = concept.get("source_card")
        if not isinstance(card, dict):
            errors.append(f"HV source_card missing or malformed: {concept_id}")
            continue
        if card.get("schema_id") != HV_SOURCE_CARD_SCHEMA_ID or card.get("field_count") != 39:
            errors.append(f"HV source_card schema/count mismatch: {concept_id}")
        fields = card.get("fields")
        if not isinstance(fields, dict) or len(fields) != 39:
            errors.append(f"HV source_card 39-field closure mismatch: {concept_id}")
            continue
        digest_payload = {key: value for key, value in card.items() if key != "content_sha256"}
        expected_digest = HV_SOURCE_CARD_SHA256[concept_id]
        if card.get("content_sha256") != expected_digest or canonical_json_sha256(digest_payload) != expected_digest:
            errors.append(f"HV source_card content digest mismatch: {concept_id}")
        support_ids = {
            item.get("anchor_id")
            for item in concept.get("source_anchors", [])
            if isinstance(item, dict)
        }
        card_anchor = card.get("card_anchor", {})
        if not isinstance(card_anchor, dict) or card_anchor.get("anchor_id") not in support_ids:
            errors.append(f"HV source_card heading anchor missing from concept support: {concept_id}")
        elif card_anchor.get("anchor_id") not in anchors:
            errors.append(f"HV source_card heading anchor missing from source: {concept_id}")
        else:
            heading_source_file, heading_prose = anchors[card_anchor["anchor_id"]]
            expected_heading = f"{concept.get('authoritative_name_zh')}（完整接口卡）"
            if (
                card_anchor.get("source_file") != heading_source_file
                or heading_prose != expected_heading
            ):
                errors.append(f"HV source_card heading text/anchor mismatch: {concept_id}")
        malformed_field = False
        for field_name, field in fields.items():
            if not isinstance(field, dict):
                malformed_field = True
                continue
            for text_key, anchor_key in (("label_text", "label_anchor"), ("raw_value_text", "value_anchor")):
                source_anchor = field.get(anchor_key)
                if not isinstance(source_anchor, dict):
                    malformed_field = True
                    continue
                anchor_id = source_anchor.get("anchor_id")
                if anchor_id not in anchors:
                    errors.append(f"HV source_card anchor missing: {concept_id}:{field_name}:{anchor_id}")
                    continue
                source_file, prose = anchors[anchor_id]
                if source_anchor.get("source_file") != source_file or field.get(text_key) != prose:
                    errors.append(f"HV source_card text/anchor mismatch: {concept_id}:{field_name}")
                if anchor_id not in support_ids:
                    errors.append(f"HV source_card field anchor absent from source_anchors: {concept_id}:{field_name}")
        if malformed_field:
            errors.append(f"HV source_card field shape malformed: {concept_id}")
            continue

        raw = {key: value.get("raw_value_text") for key, value in fields.items()}
        project = lambda value: [] if value == "无（空集合）" else [value]
        if concept.get("definition") != raw.get("proposition"):
            errors.append(f"HV proposition/definition projection mismatch: {concept_id}")
        if concept.get("allowed_inferences") != [raw.get("allowed_inference")]:
            errors.append(f"HV allowed_inference projection mismatch: {concept_id}")
        if concept.get("prerequisites") != project(raw.get("inferential_requires")):
            errors.append(f"HV inferential prerequisite projection mismatch: {concept_id}")
        expected_forbidden = [
            *project(raw.get("prohibited_leap")),
            *project(raw.get("forbidden_elevation")),
        ]
        if concept.get("forbidden_substitutions_or_generalizations") != expected_forbidden:
            errors.append(f"HV forbidden projection mismatch: {concept_id}")
        if concept.get("evidence_requirements") != project(raw.get("evidence")):
            errors.append(f"HV evidence projection mismatch: {concept_id}")
        if concept.get("counterexamples") != project(raw.get("counterexamples")):
            errors.append(f"HV counterexample projection mismatch: {concept_id}")
        if concept.get("withdrawal_conditions") != []:
            errors.append(f"HV pause condition must not be rebound as withdrawal: {concept_id}")
        expected_action = None if raw.get("action_ceiling") == "无（空集合）" else raw.get("action_ceiling")
        if concept.get("action_ceiling") != expected_action:
            errors.append(f"HV action ceiling projection mismatch: {concept_id}")
        if concept.get("source_undefined_fields") != [
            "common_misuses", "conflicts_disambiguation",
            "withdrawal_conditions", "deduction_interfaces",
        ]:
            errors.append(f"HV source undefined closure mismatch: {concept_id}")

        try:
            parsed_routes = parse_hv_route_source(raw.get("conditional_support_routes", ""))
        except (AttributeError, ValueError):
            errors.append(f"HV conditional route source cannot be parsed: {concept_id}")
            continue
        structured_routes = concept.get("conditional_support_routes", [])
        if not isinstance(structured_routes, list) or len(structured_routes) != len(parsed_routes):
            errors.append(f"HV conditional route count mismatch: {concept_id}")
            continue
        route_count += len(structured_routes)
        for structured, parsed in zip(structured_routes, parsed_routes):
            if not isinstance(structured, dict):
                errors.append(f"HV conditional route shape malformed: {concept_id}")
                continue
            for field in (
                "route_id", "claim_level", "when", "additional_inferential_requires",
                "additional_protocol_requires", "allowed_conclusion", "result_ceiling",
                "source_text",
            ):
                if structured.get(field) != parsed.get(field):
                    errors.append(f"HV conditional route/source drift: {concept_id}:{structured.get('route_id')}")
                    break
            if structured.get("source_anchor") != fields["conditional_support_routes"].get("value_anchor"):
                errors.append(f"HV conditional route anchor drift: {concept_id}:{structured.get('route_id')}")
            required_ids = structured.get("required_concept_ids", [])
            if not isinstance(required_ids, list) or any(item not in concepts for item in required_ids):
                errors.append(f"HV conditional route dependency is dangling: {concept_id}:{structured.get('route_id')}")
            elif not set(required_ids).issubset(concept.get("required_neighbor_ids", [])):
                errors.append(f"HV conditional route dependency lacks neighbor backlink: {concept_id}:{structured.get('route_id')}")
            route_dependency_rows.append([
                structured.get("route_id"),
                sorted(required_ids) if isinstance(required_ids, list) else required_ids,
            ])
    if route_count != 31:
        errors.append(f"HV conditional route inventory must contain 31 routes, found {route_count}")
    if canonical_json_sha256(sorted(route_dependency_rows)) != HV_ROUTE_DEPENDENCY_SHA256:
        errors.append("HV conditional route dependency inventory mismatch")


def validate_family_and_collision_graph(
    concepts: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    families = {
        "V8-CANON-ROLE-ACTIVATION": {
            f"V8-CANON-ACTOR-CIRCLE-DIRECTION-{code}"
            for code in ("CIRCLE-TO-ACTOR", "ACTOR-TO-CIRCLE", "BIDIRECTIONAL-FEEDBACK")
        },
        "V8-CANON-MULTICIRCLE-JOINT-OBJECT": {
            f"V8-CANON-CROSS-CHANNEL-BRIDGE-{code}"
            for code in ("M-TO-PSI", "PSI-TO-M", "M-PSI-CLOSED-LOOP")
        },
        "V8-CANON-OMEGA-F-UPDATE": {
            f"V8-CANON-UPDATE-PROVENANCE-{code}"
            for code in ("DIRECT-OBSERVATION", "MECHANISM-INFERENCE", "SCENARIO-VALUE", "UNEXPLAINED-RESIDUAL")
        },
        "V8-CANON-CROSS-CIRCLE-CASCADE": {
            f"V8-CANON-CROSS-CIRCLE-CASCADE-{code}"
            for code in ("MEMBERSHIP", "RESOURCE", "MEANING", "INSTITUTIONAL", "PLATFORM")
        },
        "V8-CANON-VARIABLE-CANDIDATE-LEDGER": {
            f"V8-CANON-CANDIDATE-SOURCE-{code}"
            for code in ("SYSTEM-RESIDUAL", "PARTICIPANT-NARRATIVE", "CROSS-CASE-REPETITION", "MODEL-SEARCH", "AI-SUGGESTION")
        },
        "V8-CANON-BRANCHING-PATH-GRAPH": {
            *(f"V8-CANON-INFERENCE-MODE-{code}" for code in ("SCENARIO", "COUNTERFACTUAL", "SIMULATION")),
            *(f"V8-CANON-FORECAST-SIGNAL-{code}" for code in ("EARLY", "REVERSE", "TRIGGER")),
        },
        "V8-CANON-SIMPLE-FORECAST-BASELINE": {
            f"V8-CANON-FORECAST-EVALUATION-{code}"
            for code in ("CALIBRATION", "RESOLUTION", "COVERAGE", "BASELINE-GAIN", "DISTRIBUTIONAL-ERROR", "STABILITY")
        },
        "V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST": {
            f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}"
            for code in ("EXPLANATION-ONLY", "SIMULATION-ONLY", "REGISTERED-FORECAST", "NORMATIVE-NOT-PASSED", "EXTERNALLY-AUTHORIZED")
        },
        "V8-CANON-GOV-22": {
            f"V8-CANON-GOVERNANCE-DEBT-{code}"
            for code in ("OBJECT", "VARIABLE", "COMPLEXITY", "CALIBRATION", "POWER")
        },
        "V8-CANON-GOV-01": {
            f"V8-CANON-SELF-DIAGNOSIS-OBJECT-{code}"
            for code in ("DOCUMENT", "CONCEPT", "PRACTICE", "COMMUNITY")
        },
        "V8-CANON-GOV-02": {
            f"V8-CANON-CONSENSUS-COMPONENT-{code}"
            for code in ("ISSUE-REGISTRATION", "MATERIAL-DISCLOSURE", "AFFECTED-OBJECT-IDENTIFICATION", "DISSENT-ENTRY", "DECISION-GRADING", "MINORITY-OPINION-RETENTION")
        },
    }
    for parent_id, child_ids in families.items():
        family = {parent_id, *child_ids}
        if not family.issubset(concepts):
            errors.append(f"canonical family membership missing: {parent_id}")
            continue
        for source_id in family:
            if not (family - {source_id}).issubset(concepts[source_id].get("required_neighbor_ids", [])):
                errors.append(f"canonical family clique/backlink mismatch: {parent_id}:{source_id}")

    token_members: dict[str, set[str]] = {}
    for concept_id, concept in concepts.items():
        for token in concept.get("authoritative_wire_tokens", []):
            token_members.setdefault(token, set()).add(concept_id)
    clusters = [members for members in token_members.values() if len(members) > 1]
    clusters.extend((
        {"V8-CANON-SIMPLE-FORECAST-BASELINE", "V8-CANON-N0"},
        {"V8-CANON-INFERENCE-MODE-SIMULATION", "V8-CANON-VOCAB-EVENT-SIMULATED", "V8-CANON-VOCAB-OUTPUT-SIMULATION"},
        {"V8-CANON-UPDATE-PROVENANCE-DIRECT-OBSERVATION", "V8-CANON-VOCAB-EVENT-OBSERVED", "V8-CANON-VOCAB-ACTOR-STATE-OBSERVED"},
        {"V8-CANON-FORECAST-PUBLICATION-STATUS-EXPLANATION-ONLY", "V8-CANON-VOCAB-OUTPUT-EXPLANATION"},
        {"V8-CANON-FORECAST-PUBLICATION-STATUS-SIMULATION-ONLY", "V8-CANON-VOCAB-OUTPUT-SIMULATION"},
        {"V8-CANON-FORECAST-PUBLICATION-STATUS-REGISTERED-FORECAST", "V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST"},
        {"V8-CANON-FORECAST-REGISTRY", "V8-CANON-TOOL-FORECAST-REGISTRY"},
        {
            "V8-CANON-VOCAB-AXIS-RELATION-UNKNOWN",
            "V8-CANON-VOCAB-HSP-CLASSIFICATION-MODE-UNKNOWN",
            "V8-CANON-VOCAB-HSP-MISSING-STATUS-UNKNOWN",
            "V8-CANON-VOCAB-X0-RESULT-UNKNOWN",
            "V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN",
            "V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN",
            "V8-CANON-VOCAB-INFO-UNKNOWN",
        },
        {"V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE", "V8-CANON-VOCAB-X0-RESULT-CANDIDATE"},
        {"V8-CANON-VOCAB-GOV-FRAMEWORK-RETIRED", "V8-CANON-VOCAB-ACTOR-STATE-RETIRED", "V8-CANON-VOCAB-LEDGER-RETIRED"},
    ))
    for cluster in clusters:
        if not cluster.issubset(concepts):
            errors.append(f"semantic collision cluster member missing: {sorted(cluster)}")
            continue
        for source_id in cluster:
            conflict_ids = {
                item.get("concept_id")
                for item in concepts[source_id].get("conflicts_disambiguation", [])
            }
            if not (cluster - {source_id}).issubset(conflict_ids):
                errors.append(f"semantic collision clique mismatch: {source_id}")


def validate_fixed_high_risk_rows(
    concepts: dict[str, dict[str, Any]],
    anchors: dict[str, tuple[str, str]],
    errors: list[str],
) -> None:
    for code, anchor_id in (
        ("EXPLANATION-ONLY", "V8-P3293"),
        ("SIMULATION-ONLY", "V8-P3296"),
        ("REGISTERED-FORECAST", "V8-P3299"),
        ("NORMATIVE-NOT-PASSED", "V8-P3302"),
        ("EXTERNALLY-AUTHORIZED", "V8-P3305"),
    ):
        concept_id = f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}"
        expected = [anchors.get(anchor_id, (None, None))[1]]
        if concepts.get(concept_id, {}).get("forbidden_substitutions_or_generalizations") != expected:
            errors.append(f"publication status forbidden-row mismatch: {concept_id}")
    gov19 = concepts.get("V8-CANON-GOV-19", {})
    if anchors.get("V8-P3755", (None, None))[1] not in gov19.get("prerequisites", []):
        errors.append("GOV-19 version-log prerequisite mismatch")
    if "V8-CANON-VERSION-LOG" not in gov19.get("required_neighbor_ids", []):
        errors.append("GOV-19/VERSION-LOG neighbor mismatch")
    if "V8-CANON-GOV-19" not in concepts.get("V8-CANON-VERSION-LOG", {}).get("required_neighbor_ids", []):
        errors.append("VERSION-LOG/GOV-19 neighbor backlink mismatch")
    if concepts.get("V8-CANON-SJ3", {}).get("evidence_requirements") != [
        anchors.get("V8-P3457", (None, None))[1]
    ]:
        errors.append("SJ3 evidence requirement mismatch")
    contract_owner_anchors = {
        "V8-CANON-ACTOR-STATE": ("V8-P2565",),
        "V8-CANON-PERSONALITY-HYPOTHESIS": (
            "V8-P2613", "V8-P2614", "V8-P2615",
        ),
        "V8-CANON-MULTICIRCLE-JOINT-OBJECT": (
            "V8-P2772", "V8-P2782", "V8-P2889", "V8-P2891",
        ),
        "V8-CANON-VOCAB-OUTPUT-SIMULATION": ("V8-P2911", "V8-P2966"),
        "V8-CANON-FORECAST-REGISTRY": ("V8-P3122",),
        "V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE": ("V8-P3228",),
        "V8-CANON-DF9": ("V8-P3273",),
    }
    for concept_id, anchor_ids in contract_owner_anchors.items():
        for anchor_id in anchor_ids:
            source_file = anchors.get(anchor_id, (None, None))[0]
            if {"anchor_id": anchor_id, "source_file": source_file} not in concepts.get(
                concept_id, {}
            ).get("source_anchors", []):
                errors.append(f"contract owner support anchor mismatch: {concept_id}")


def check_repository(repo: Path | str) -> list[str]:
    repo = Path(repo).resolve()
    skill = repo / "skills/crossframe-promax"
    references = skill / "references"
    schemas_dir = skill / "schemas"
    errors: list[str] = []

    source_integrity_errors = check_full_source_integrity(repo)
    if source_integrity_errors:
        return source_integrity_errors

    paths = {
        "source": references / "source_manifest.json",
        "registry": references / "concept-registry/v8-concept-registry.json",
        "contracts": references / "concept-contracts/v8-contract-map.json",
        "routes": references / "v8-route-map.json",
    }
    schema_paths = {
        "source": schemas_dir / "v8-source-manifest.schema.json",
        "registry": schemas_dir / "v8-concept-registry.schema.json",
        "contracts": schemas_dir / "v8-contract-map.schema.json",
        "routes": schemas_dir / "v8-route-map.schema.json",
    }
    for label, path in {**paths, **{f"schema:{key}": value for key, value in schema_paths.items()}}.items():
        if not path.is_file():
            errors.append(f"missing {label}: {path}")
    if errors:
        return errors

    assets = {key: load_json(path, errors, key) for key, path in paths.items()}
    schemas = {key: load_json(path, errors, f"schema:{key}") for key, path in schema_paths.items()}
    if any(value is None for value in (*assets.values(), *schemas.values())):
        return errors

    schema_validation_start = len(errors)
    for label, schema in schemas.items():
        if sha256_file(schema_paths[label]) != SCHEMA_FILE_SHA256[label]:
            errors.append(f"{label} schema integrity hash mismatch")
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"invalid {label} schema: {exc}")
            continue
        assert_schema_closed(schema, label, errors)
        for issue in Draft202012Validator(schema).iter_errors(assets[label]):
            location = "/".join(str(item) for item in issue.absolute_path)
            errors.append(f"{label} schema validation at {location}: {issue.message}")
    if len(errors) != schema_validation_start:
        errors.extend(scan_version_pollution(skill))
        return errors

    registry = assets["registry"]
    contract_map = assets["contracts"]
    route_map = assets["routes"]
    source_manifest = assets["source"]
    for label, asset in (("source manifest", source_manifest), ("registry", registry), ("contract map", contract_map), ("route map", route_map)):
        if asset.get("snapshot_sha256") != SNAPSHOT_SHA256:
            errors.append(f"{label} snapshot hash does not match fixed v8 source")

    if sha256_file(paths["registry"]) != REGISTRY_FILE_SHA256:
        errors.append("definition/inference semantic registry integrity hash mismatch")
    if sha256_file(paths["contracts"]) != CONTRACT_MAP_FILE_SHA256:
        errors.append("contract map and binding integrity hash mismatch")
    if sha256_file(paths["routes"]) != ROUTE_MAP_FILE_SHA256:
        errors.append("route map integrity hash mismatch")
    if concept_semantic_sha256(registry) != CONCEPT_SEMANTIC_SHA256:
        errors.append("definition/inference and semantic-role inventory digest mismatch")
    if route_semantic_sha256(route_map) != ROUTE_SEMANTIC_SHA256:
        errors.append("route semantic inventory digest mismatch")

    concept_rows = registry.get("concepts", [])
    ids = [item.get("concept_id") for item in concept_rows if isinstance(item, dict)]
    names = [item.get("authoritative_name_zh") for item in concept_rows if isinstance(item, dict)]
    actual_inventory = hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")).hexdigest() if all(isinstance(item, str) for item in ids) else ""
    if len(concept_rows) != CANONICAL_CONCEPT_COUNT or registry.get("concept_count") != CANONICAL_CONCEPT_COUNT:
        errors.append("canonical inventory count mismatch")
    if actual_inventory != CANONICAL_INVENTORY_SHA256 or registry.get("concept_inventory_sha256") != actual_inventory:
        errors.append("canonical inventory digest mismatch")
    if len(ids) != len(set(ids)):
        errors.append("duplicate canonical concept ID")
    if len(names) != len(set(names)):
        errors.append("duplicate authoritative concept name")
    for concept_id in ids:
        if not isinstance(concept_id, str) or not concept_id.startswith("V8-CANON-") or concept_id.startswith("PROMAX-PROV-"):
            errors.append(f"canonical namespace collision: {concept_id}")

    concepts = {item.get("concept_id"): item for item in concept_rows if isinstance(item, dict) and isinstance(item.get("concept_id"), str)}
    try:
        anchors = paragraph_index(references / "v8-full-source")
    except (OSError, UnicodeError) as exc:
        errors.append(f"source anchor index failure: {exc}")
        anchors = {}
    for concept_id, concept in concepts.items():
        support_parts = []
        support_anchor_ids = set()
        for anchor in concept.get("source_anchors", []):
            anchor_id = anchor.get("anchor_id")
            support_anchor_ids.add(anchor_id)
            if anchor_id not in anchors:
                errors.append(f"anchor missing for {concept_id}: {anchor_id}")
                continue
            source_file, prose = anchors[anchor_id]
            if anchor.get("source_file") != source_file:
                errors.append(f"anchor source mismatch for {concept_id}: {anchor_id}")
            support_parts.append(prose)
        support = "\n".join(support_parts)
        if concept.get("primary_source_anchor_id") not in support_anchor_ids:
            errors.append(f"primary source anchor missing from support for {concept_id}")
        if concept.get("definition") not in support:
            errors.append(f"definition is unsupported by anchors for {concept_id}")
        for inference in concept.get("allowed_inferences", []):
            if inference not in support:
                errors.append(f"inference is unsupported by anchors for {concept_id}")
        for token in concept.get("authoritative_wire_tokens", []):
            if token not in support:
                errors.append(f"authoritative wire token is unsupported by anchors for {concept_id}: {token}")
        for field in (
            "prerequisites", "forbidden_substitutions_or_generalizations",
            "common_misuses", "evidence_requirements", "counterexamples",
            "withdrawal_conditions",
        ):
            for excerpt in concept.get(field, []):
                if excerpt not in support:
                    errors.append(f"semantic role excerpt is unsupported for {concept_id}:{field}")
        action_ceiling = concept.get("action_ceiling")
        if action_ceiling is not None and action_ceiling not in support:
            errors.append(f"action ceiling is unsupported by anchors for {concept_id}")
        for interface in concept.get("deduction_interfaces", []):
            if interface.get("relation") not in support or interface.get("output_ceiling") not in support:
                errors.append(f"deduction semantic excerpt is unsupported for {concept_id}")
        fallback_fragments = (
            "源锚点声明的对象、窗口与适用条件", "泛化到源锚点未覆盖",
            "字段完整误当作经验成立", "构成反例或不适用例",
            "源锚点的必要条件、对象同一性或证据门失效", "must-read-neighbor",
            "不因相邻或同路线而互换",
        )
        serialized_concept = json.dumps(concept, ensure_ascii=False)
        if any(fragment in serialized_concept for fragment in fallback_fragments):
            errors.append(f"generic semantic filler is forbidden for {concept_id}")
        neighbors = concept.get("required_neighbor_ids", [])
        if concept_id in neighbors:
            errors.append(f"self neighbor forbidden for {concept_id}")
        for neighbor_id in neighbors:
            if neighbor_id not in concepts:
                errors.append(f"dangling neighbor {neighbor_id} from {concept_id}")
            elif concept_id not in concepts[neighbor_id].get("required_neighbor_ids", []):
                errors.append(f"neighbor backlink missing: {concept_id} <-> {neighbor_id}")
        conflict_ids = [item.get("concept_id") for item in concept.get("conflicts_disambiguation", [])]
        if len(conflict_ids) != len(set(conflict_ids)):
            errors.append(f"duplicate conflict target for {concept_id}")
        for conflict in concept.get("conflicts_disambiguation", []):
            target_id = conflict.get("concept_id")
            if target_id not in concepts:
                errors.append(f"dangling conflict target {target_id} from {concept_id}")
            else:
                disambiguation = conflict.get("disambiguation")
                if not isinstance(disambiguation, str) or disambiguation not in support:
                    errors.append(
                        "conflict disambiguation is unsupported by own source anchors: "
                        f"{concept_id}->{target_id}"
                    )
                reverse_ids = {
                    item.get("concept_id")
                    for item in concepts[target_id].get("conflicts_disambiguation", [])
                }
                if concept_id not in reverse_ids:
                    errors.append(f"conflict backlink missing: {concept_id}<->{target_id}")
                if target_id not in neighbors:
                    errors.append(f"conflict neighbor backlink missing: {concept_id}<->{target_id}")
        for interface in concept.get("deduction_interfaces", []):
            target_id = interface.get("target_concept_id")
            if target_id not in concepts:
                errors.append(f"dangling deduction interface {target_id} from {concept_id}")
        if concept.get("concept_type") != "human_variable_interface":
            expected_undefined = [
                field
                for field in (
                    "prerequisites", "forbidden_substitutions_or_generalizations",
                    "common_misuses", "conflicts_disambiguation", "evidence_requirements",
                    "counterexamples", "withdrawal_conditions", "deduction_interfaces",
                    "action_ceiling",
                )
                if concept.get(field) in ([], None)
            ]
            if concept.get("source_undefined_fields") != expected_undefined:
                errors.append(f"source undefined closure mismatch: {concept_id}")
            if concept.get("conditional_support_routes") != []:
                errors.append(f"conditional support routes are HV-only: {concept_id}")

    validate_hv_source_cards(concepts, anchors, errors)
    validate_family_and_collision_graph(concepts, errors)
    validate_fixed_high_risk_rows(concepts, anchors, errors)

    expected_global_ceiling = {
        "clauses": [
            anchors.get("V8-P0791", (None, None))[1],
            anchors.get("V8-P0854", (None, None))[1],
            anchors.get("V8-P3564", (None, None))[1],
        ],
        "source_anchors": [
            {"anchor_id": "V8-P0791", "source_file": "04-root-assumptions.md"},
            {"anchor_id": "V8-P0854", "source_file": "05-scale-transformation.md"},
            {"anchor_id": "V8-P3564", "source_file": "14-normative-selection.md"},
        ],
    }
    if registry.get("global_action_ceiling") != expected_global_ceiling:
        errors.append("global action ceiling exact source contract mismatch")

    contract_rows = contract_map.get("contracts", [])
    if len(contract_rows) != len({item.get("contract_id") for item in contract_rows}):
        errors.append("duplicate contract ID")
    contracts_by_id = {item.get("contract_id"): item for item in contract_rows}
    if set(contracts_by_id) != set(CONTRACTS):
        errors.append("authored contract inventory mismatch")
    registry_binding_rows: set[tuple[str, str, str, str]] = set()
    for concept_id, concept in concepts.items():
        bound_contracts = set()
        for binding in concept.get("contract_bindings", []):
            contract_id = binding.get("contract_id")
            bound_contracts.add(contract_id)
            registry_binding_rows.add((contract_id, binding.get("json_pointer"), concept_id, binding.get("binding_role")))
        if set(concept.get("contract_ids", [])) != bound_contracts:
            errors.append(f"contract binding backlink mismatch for {concept_id}")

    map_binding_rows: set[tuple[str, str, str, str]] = set()
    actual_binding_concepts: dict[tuple[str, str], set[str]] = {}
    actual_unbound_by_contract: dict[str, set[str]] = {}
    for contract_id, (filename, expected_sha, expected_leaves, expected_pointers_count) in CONTRACTS.items():
        contract = contracts_by_id.get(contract_id)
        if contract is None:
            continue
        contract_path = references / "concept-contracts" / filename
        if not contract_path.is_file():
            errors.append(f"missing authored contract: {filename}")
            continue
        actual_sha = sha256_file(contract_path)
        if actual_sha != expected_sha or contract.get("sha256") != expected_sha:
            errors.append(f"authored contract byte hash mismatch: {contract_id}")
        payload = load_json(contract_path, errors, f"authored contract {contract_id}")
        if payload is None:
            continue
        if payload.get("schema_id") != contract_id:
            errors.append(f"authored contract schema ID mismatch: {contract_id}")
        if contract.get("path") != f"concept-contracts/{filename}":
            errors.append(f"authored contract path mismatch: {contract_id}")
        if contract.get("scope") != payload.get("scope"):
            errors.append(f"contract scope mismatch: {contract_id}")
        expected_pointers, leaf_pointers = semantic_pointer_inventory(payload)
        if len(leaf_pointers) != expected_leaves or len(expected_pointers) != expected_pointers_count:
            errors.append(f"authored contract semantic tree changed: {contract_id}")
        bindings = contract.get("bindings", [])
        actual_pointers = {item.get("json_pointer") for item in bindings}
        unbound_rows = contract.get("unbound_semantic_pointers", [])
        unbound_pointers = {
            item.get("json_pointer") for item in unbound_rows if isinstance(item, dict)
        }
        actual_unbound_by_contract[contract_id] = unbound_pointers
        if contract.get("required_semantic_pointers") != expected_pointers:
            errors.append(f"semantic coverage mismatch: {contract_id}")
        if actual_pointers & unbound_pointers:
            errors.append(f"semantic pointer has both bound and unbound status: {contract_id}")
        if actual_pointers | unbound_pointers != set(expected_pointers):
            errors.append(f"semantic pointer coverage partition mismatch: {contract_id}")
        if len(unbound_pointers) != len(unbound_rows):
            errors.append(f"duplicate unbound semantic pointer status: {contract_id}")
        if unbound_pointers != EXPECTED_UNBOUND_POINTERS[contract_id]:
            errors.append(f"strict unbound pointer oracle mismatch: {contract_id}")
        for unbound in unbound_rows:
            pointer = unbound.get("json_pointer")
            if unbound.get("reason_code") != "no_distinct_v8_canonical_concept":
                errors.append(f"invalid unbound reason code: {contract_id}:{pointer}")
            if unbound.get("runtime_requirement") != "read_authored_contract_pointer_directly":
                errors.append(f"invalid unbound runtime requirement: {contract_id}:{pointer}")
            try:
                resolve_pointer(payload, pointer)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append(f"invalid unbound JSON pointer {contract_id}:{pointer}")
        for binding in bindings:
            pointer = binding.get("json_pointer")
            concept_id = binding.get("concept_id")
            role = binding.get("binding_role")
            try:
                resolve_pointer(payload, pointer)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append(f"invalid JSON pointer binding {contract_id}:{pointer}")
            expected_role = expected_binding_role(pointer) if isinstance(pointer, str) else None
            if role != expected_role:
                kind = "guard/rule/policy" if isinstance(pointer, str) and ("/guards" in pointer or "rule" in pointer or "policy" in pointer) else "contract"
                errors.append(f"{kind} binding role mismatch: {contract_id}:{pointer}")
            if concept_id not in concepts:
                errors.append(f"dangling contract binding concept: {concept_id}")
            else:
                if binding.get("source_anchors") != concepts[concept_id].get("source_anchors"):
                    errors.append(f"contract binding anchor backlink mismatch: {concept_id}")
            map_binding_rows.add((contract_id, pointer, concept_id, role))
            actual_binding_concepts.setdefault((contract_id, pointer), set()).add(concept_id)
        bound_ids = {item.get("concept_id") for item in bindings}
        if set(contract.get("concept_ids", [])) != bound_ids:
            errors.append(f"contract concept backlink mismatch: {contract_id}")
        for concept_id in contract.get("concept_ids", []):
            if concept_id not in concepts or contract_id not in concepts[concept_id].get("contract_ids", []):
                errors.append(f"contract backlink missing: {contract_id} -> {concept_id}")

    if map_binding_rows != registry_binding_rows:
        errors.append("contract pointer binding backlink mismatch between map and registry")
    expected_binding_keys = {
        (contract_id, pointer)
        for contract_id, pointer_map in EXPECTED_BOUND_CONCEPT_IDS.items()
        for pointer in pointer_map
    }
    if set(actual_binding_concepts) != expected_binding_keys:
        errors.append("strict contract owner pointer inventory mismatch")
    for contract_id, pointer_map in EXPECTED_BOUND_CONCEPT_IDS.items():
        for pointer, expected_ids in pointer_map.items():
            if actual_binding_concepts.get((contract_id, pointer)) != set(expected_ids):
                errors.append(f"strict contract owner oracle mismatch: {contract_id}:{pointer}")
    actual_owner_map = {
        contract_id: {
            pointer: sorted(actual_binding_concepts.get((contract_id, pointer), set()))
            for pointer in pointer_map
        }
        for contract_id, pointer_map in EXPECTED_BOUND_CONCEPT_IDS.items()
    }
    if (
        owner_oracle_sha256(EXPECTED_BOUND_CONCEPT_IDS) != EXPECTED_OWNER_ORACLE_SHA256
        or owner_oracle_sha256(actual_owner_map) != EXPECTED_OWNER_ORACLE_SHA256
    ):
        errors.append("strict contract owner oracle digest mismatch")
    if binding_inventory_sha256(contract_map) != BINDING_INVENTORY_SHA256:
        errors.append("canonical binding inventory digest mismatch")
    actual_coverage_digest = semantic_coverage_sha256(contract_map)
    if (
        actual_coverage_digest != SEMANTIC_COVERAGE_SHA256
        or contract_map.get("semantic_coverage_sha256") != actual_coverage_digest
    ):
        errors.append("semantic coverage inventory digest mismatch")

    route_rows = route_map.get("routes", [])
    route_ids = [item.get("route_id") for item in route_rows]
    source_sections = [item.get("source_section") for item in route_rows]
    if len(route_rows) != 16 or route_map.get("route_count") != 16:
        errors.append("route count must be exactly 16")
    if len(route_ids) != len(set(route_ids)):
        errors.append("duplicate route ID")
    if len(source_sections) != len(set(source_sections)):
        errors.append("duplicate route source section")
    actual_route_sources = {item.get("route_id"): item.get("source_section") for item in route_rows}
    if actual_route_sources != ROUTE_SOURCES:
        errors.append("route ID/source-section inventory mismatch")
    routes = {item.get("route_id"): item for item in route_rows}
    routed_ids: set[str] = set()
    for route_id, route in routes.items():
        required = set(route.get("required_concept_ids", []))
        closure = set(route.get("neighbor_closure_ids", []))
        if required & closure:
            errors.append(f"route required/closure overlap: {route_id}")
        expected_primary = {
            concept_id
            for concept_id, concept in concepts.items()
            if next(
                (
                    anchor.get("source_file")
                    for anchor in concept.get("source_anchors", [])
                    if anchor.get("anchor_id") == concept.get("primary_source_anchor_id")
                ),
                None,
            ) == route.get("source_section")
        }
        if required != expected_primary:
            errors.append(f"route primary seed ownership mismatch: {route_id}")
        for concept_id in required:
            if concept_id not in concepts:
                errors.append(f"dangling route seed: {route_id}:{concept_id}")
                continue
            primary_source_file = next(
                (
                    anchor.get("source_file")
                    for anchor in concepts[concept_id].get("source_anchors", [])
                    if anchor.get("anchor_id") == concepts[concept_id].get("primary_source_anchor_id")
                ),
                None,
            )
            if route.get("source_section") != primary_source_file:
                errors.append(f"route seed source mismatch: {route_id}:{concept_id}")
        reached = set(required)
        frontier = [item for item in required if item in concepts]
        while frontier:
            current = frontier.pop()
            for neighbor_id in concepts[current].get("required_neighbor_ids", []):
                if neighbor_id in concepts and neighbor_id not in reached:
                    reached.add(neighbor_id)
                    frontier.append(neighbor_id)
        if closure != reached - required:
            errors.append(f"route neighbor closure fixed-point mismatch: {route_id}")
        refs = required | closure
        for concept_id in refs:
            if concept_id not in concepts:
                errors.append(f"dangling route reference: {route_id}:{concept_id}")
            elif route_id not in concepts[concept_id].get("route_ids", []):
                errors.append(f"route backlink missing: {route_id}:{concept_id}")
        routed_ids.update(refs)
    for concept_id, concept in concepts.items():
        for route_id in concept.get("route_ids", []):
            route = routes.get(route_id)
            if route is None:
                errors.append(f"dangling route ID on concept: {concept_id}:{route_id}")
                continue
            refs = set(route.get("required_concept_ids", [])) | set(route.get("neighbor_closure_ids", []))
            if concept_id not in refs:
                errors.append(f"route backlink mismatch: {concept_id}:{route_id}")
        source_files = {item.get("source_file") for item in concept.get("source_anchors", [])}
        if not any(routes.get(route_id, {}).get("source_section") in source_files for route_id in concept.get("route_ids", [])):
            errors.append(f"concept lacks source-section route backlink: {concept_id}")
    if routed_ids != set(concepts):
        errors.append("route graph does not cover canonical inventory")

    errors.extend(scan_version_pollution(skill))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CrossFrame ProMax v8 knowledge assets")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args(argv)
    errors = check_repository(args.repo)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("CrossFrame ProMax v8 knowledge assets: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
