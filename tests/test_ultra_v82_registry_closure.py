from __future__ import annotations

import copy
from collections import Counter
import hashlib
import importlib.util
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator
from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills" / "crossframe-ultra"
LEGACY_V80_SHA256 = "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"


def load_checker():
    path = ULTRA / "scripts" / "check_crossframe_ultra_v82_knowledge.py"
    spec = importlib.util.spec_from_file_location("ultra_knowledge_checker", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def copy_authority_repo(tmp_path: Path) -> Path:
    copied = tmp_path / "repo"
    copied_ultra = copied / "skills" / "crossframe-ultra"
    copied_ultra.parent.mkdir(parents=True)
    shutil.copytree(
        ULTRA,
        copied_ultra,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    copied_scripts = copied / "scripts"
    copied_scripts.mkdir()
    shutil.copy2(ROOT / "scripts/check_crossframe_ultra_v82_knowledge.py", copied_scripts)
    return copied


def run_checker(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "scripts/check_crossframe_ultra_v82_knowledge.py"),
            "--repo",
            str(repo),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_authority_registry_contains_source_supported_m02_operator_fixture() -> None:
    registry = load_json(
        ULTRA / "references" / "concept-registry" / "v8.2-concept-registry.json"
    )
    concepts = {record["concept_id"]: record for record in registry["concepts"]}
    assert set(concepts) >= {f"V82-M{number:02d}" for number in range(1, 10)}
    operator = concepts["V82-M02"]
    assert operator["canonical_zh"] == "嵌套"
    assert operator["concept_type"] == "scale-transformation-operator"
    assert operator["source_anchors"] == [
        "V82-P0938",
        "V82-P0939",
        "V82-P0940",
        "V82-P0941",
        "V82-P0942",
    ]
    assert operator["definition"] == "签名是“边界—成员嵌入”。"
    assert "V82-P1800" not in operator["source_anchors"]
    assert {
        "concept_id",
        "canonical_zh",
        "concept_type",
        "responsibility_layer",
        "definition",
        "source_anchors",
        "prerequisites",
        "allowed_inferences",
        "forbidden_substitutions",
        "common_misuses",
        "required_neighbors",
        "conflicts",
        "disambiguation_conditions",
        "evidence_requirements",
        "counterexamples",
        "withdrawal_conditions",
        "inference_interfaces",
        "action_ceiling",
    } == set(operator)


def test_knowledge_checker_accepts_clean_authority_tree() -> None:
    checker = load_checker()
    assert checker.validate_knowledge(ROOT) == []


@pytest.mark.parametrize(
    ("initial_encoding", "as_json"),
    (("cp1252", False), ("utf-8", True)),
    ids=("cp1252-diagnostic", "utf8-json"),
)
def test_knowledge_checker_main_emits_utf8_for_text_and_json_streams(
    monkeypatch: pytest.MonkeyPatch,
    initial_encoding: str,
    as_json: bool,
) -> None:
    checker = load_checker()
    diagnostic = "中文诊断"
    output = BytesIO()
    stream = TextIOWrapper(output, encoding=initial_encoding, newline="\n")
    arguments = ["--repo", str(ROOT)]
    if as_json:
        arguments.append("--json")

    with monkeypatch.context() as patch:
        patch.setattr(checker, "validate_knowledge", lambda _repo: [diagnostic])
        patch.setattr(checker.sys, "stdout", stream)
        exit_code = checker.main(arguments)
        stream.flush()
        configured_encoding = stream.encoding
        payload = output.getvalue()

    assert exit_code == 1
    assert configured_encoding == "utf-8"
    decoded = payload.decode("utf-8")
    if as_json:
        assert json.loads(decoded)["errors"] == [diagnostic]
    else:
        assert decoded == (
            "CrossFrame Ultra v8.2 knowledge authority: FAIL\n"
            f"- {diagnostic}\n"
        )


def test_validator_consumes_each_knowledge_file_from_one_bytes_snapshot(
    monkeypatch,
) -> None:
    checker = load_checker()
    registry = (ROOT / checker.REGISTRY_RELATIVE).resolve()
    contract = (
        ROOT
        / checker.REFERENCES_RELATIVE
        / "concept-contracts/core-kernel-contracts.json"
    ).resolve()
    original_reader = checker._read_regular
    calls: Counter[Path] = Counter()

    def changing_reader(path: Path, repo: Path, **options) -> bytes:
        resolved = Path(path).resolve()
        calls[resolved] += 1
        payload = original_reader(path, repo, **options)
        if resolved == registry and calls[resolved] > 1:
            value = json.loads(payload.decode("utf-8"))
            value["concepts"][0]["definition"] += "；这条虚构结论必然授权一切行动。"
            return (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        if resolved == contract and calls[resolved] > 1:
            value = json.loads(payload.decode("utf-8"))
            value["schema_id"] = "crossframe.ultra.v8.2.contract-bypass"
            return (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        return payload

    monkeypatch.setattr(checker, "_read_regular", changing_reader)
    assert checker.validate_knowledge(ROOT) == []
    expected_once = {
        (ROOT / checker.REGISTRY_RELATIVE).resolve(),
        (ROOT / checker.REGISTRY_INDEX_RELATIVE).resolve(),
        (ROOT / checker.CONTRACT_MAP_RELATIVE).resolve(),
        (ROOT / checker.ROUTE_MAP_RELATIVE).resolve(),
        (
            ROOT
            / checker.ULTRA_RELATIVE
            / "scripts/check_crossframe_ultra_v82_source.py"
        ).resolve(),
        (ROOT / checker.JSONIO_RELATIVE).resolve(),
        *(
            (ROOT / checker.SCHEMAS_RELATIVE / name).resolve()
            for name in checker.SCHEMA_FILES.values()
        ),
        *(
            (
                ROOT
                / checker.REFERENCES_RELATIVE
                / "concept-contracts"
                / name
            ).resolve()
            for name in checker.CONTRACT_FILES
        ),
    }
    assert calls[registry] == 1
    assert calls[contract] == 1
    assert {path: calls[path] for path in expected_once} == {
        path: 1 for path in expected_once
    }


def test_knowledge_snapshot_budgets_fail_closed(monkeypatch) -> None:
    checker = load_checker()
    monkeypatch.setattr(checker, "MAX_KNOWLEDGE_FILE_BYTES", 1024)
    file_errors = checker.validate_knowledge(ROOT)
    assert any("knowledge budgets" in error for error in file_errors)
    assert any("file=1024" in error for error in file_errors)

    monkeypatch.setattr(checker, "MAX_KNOWLEDGE_FILE_BYTES", 1024 * 1024)
    monkeypatch.setattr(checker, "MAX_KNOWLEDGE_SNAPSHOT_BYTES", 20 * 1024)
    total_errors = checker.validate_knowledge(ROOT)
    assert any("knowledge budgets" in error for error in total_errors)
    assert any("total=20480" in error for error in total_errors)


def test_regular_reader_enforces_one_mibibyte_default_with_limit_plus_one(
    tmp_path: Path,
) -> None:
    checker = load_checker()
    repo = tmp_path / "repo"
    repo.mkdir()
    exact = repo / "exact.bin"
    exact_payload = b"x" * (1024 * 1024)
    exact.write_bytes(exact_payload)
    assert checker.MAX_KNOWLEDGE_FILE_BYTES == 1024 * 1024
    assert checker._read_regular(exact, repo) == exact_payload

    oversized = repo / "oversized.bin"
    oversized.write_bytes(exact_payload + b"!")
    with pytest.raises(ValueError, match="exceeds safety limit"):
        checker._read_regular(oversized, repo)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_authority_json_rejects_non_finite_constants(
    tmp_path: Path,
    constant: str,
) -> None:
    copied = copy_authority_repo(tmp_path)
    registry = copied / (
        "skills/crossframe-ultra/references/concept-registry/"
        "v8.2-concept-registry.json"
    )
    original = registry.read_text(encoding="utf-8")
    mutated = original.replace('"schema_version": 1', f'"schema_version": {constant}', 1)
    assert mutated != original
    registry.write_text(mutated, encoding="utf-8", newline="\n")

    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "non-finite json constant" in output.casefold()


def test_authority_json_rejects_utf8_bom(tmp_path: Path) -> None:
    copied = copy_authority_repo(tmp_path)
    registry = copied / (
        "skills/crossframe-ultra/references/concept-registry/"
        "v8.2-concept-registry.json"
    )
    registry.write_bytes(b"\xef\xbb\xbf" + registry.read_bytes())

    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "bom is forbidden" in output.casefold()


def test_knowledge_checker_reuses_strict_jsonio_resource_limits() -> None:
    checker = load_checker()
    source_checker = checker._load_source_checker(ROOT)
    loader = checker._load_strict_json_loader(ROOT, source_checker)

    with pytest.raises(ValueError, match="nesting depth"):
        loader(
            b'{"value":' + b"[" * 12 + b"0" + b"]" * 12 + b"}",
            source="depth-probe",
            max_bytes=1024,
            max_container_items=100,
            max_depth=4,
        )
    with pytest.raises(ValueError, match="container member count"):
        loader(
            b'{"value":[0,1,2,3]}',
            source="container-probe",
            max_bytes=1024,
            max_container_items=3,
            max_depth=16,
        )
    with pytest.raises(ValueError, match="invalid UTF-8"):
        loader(
            b'{"value":"\xff"}',
            source="utf8-probe",
            max_bytes=1024,
            max_container_items=100,
            max_depth=16,
        )
    with pytest.raises(ValueError, match="non-finite JSON number"):
        loader(
            b'{"value":1e400}',
            source="overflow-probe",
            max_bytes=1024,
            max_container_items=100,
            max_depth=16,
        )


def test_semantic_support_is_exact_per_source_or_explicit_curated_unit(
    monkeypatch,
) -> None:
    checker = load_checker()
    assert checker._semantic_unit_supported("甲乙", ["前文甲乙后文"])
    assert not checker._semantic_unit_supported("甲乙", ["前文甲", "乙后文"])
    assert not checker._semantic_unit_supported("甲丙", ["前文甲乙后文"])

    monkeypatch.setitem(
        checker.CURATED_SEMANTIC_EVIDENCE,
        checker._normalize_text("固定整理单位"),
        ("甲乙", "丙丁"),
    )
    assert checker._semantic_unit_supported(
        "固定整理单位",
        ["这里含甲乙", "另一锚点含丙丁"],
    )
    assert not checker._semantic_unit_supported(
        "固定整理单位",
        ["这里只到甲", "乙在另一锚点且另有丙丁"],
    )


def test_semantic_support_rejects_every_unsupported_fixed_unit() -> None:
    checker = load_checker()
    assert checker._unsupported_semantic_units(
        "签名是边界成员嵌入；恶",
        ["签名是边界成员嵌入"],
    ) == ["恶"]


def test_source_snapshot_requires_public_frozen_api_without_private_fallback() -> None:
    checker = load_checker()
    private_called = False

    class PrivateOnlyChecker:
        def _validate_committed_source_snapshot(self, repo: Path) -> object:
            nonlocal private_called
            private_called = True
            return object()

    errors: list[str] = []
    manifest, records = checker._validated_source_snapshot(
        PrivateOnlyChecker(),
        ROOT,
        errors,
    )
    assert manifest is None
    assert records == {}
    assert not private_called
    assert any("public" in error or "API" in error for error in errors)


def test_contract_document_validation_requires_named_defs_entry() -> None:
    checker = load_checker()
    schema = load_json(ULTRA / "schemas/ultra-contract-map.schema.json")
    schema["$defs"].pop("contractDocument", None)
    errors: list[str] = []
    checker._validate_contract_document_schema(
        schema,
        {},
        "V82-CONTRACT-PROBE",
        errors,
    )
    assert any("contract $defs" in error for error in errors)


def test_checker_rejects_all_required_closure_mutations(tmp_path: Path) -> None:
    copied = copy_authority_repo(tmp_path)
    registry_relative = Path(
        "skills/crossframe-ultra/references/concept-registry/v8.2-concept-registry.json"
    )
    contracts_relative = Path(
        "skills/crossframe-ultra/references/concept-contracts/v8.2-contract-map.json"
    )
    routes_relative = Path(
        "skills/crossframe-ultra/references/v8.2-route-map.json"
    )
    schema_relative = Path(
        "skills/crossframe-ultra/schemas/ultra-concept-registry.schema.json"
    )

    def missing_anchor(data: dict) -> None:
        data["concepts"][0]["source_anchors"].clear()

    def unsupported_definition(data: dict) -> None:
        data["concepts"][0]["definition"] = "这是一条与所引源文本完全无关的虚构定义。"

    def supported_clause_plus_fiction(data: dict) -> None:
        data["concepts"][0]["definition"] += "；并且它必然证明一切行动都已获得授权。"

    def fabricated_allowed_inference(data: dict) -> None:
        data["concepts"][0]["allowed_inferences"].append(
            "这一概念必然证明宇宙中的一切行动都已获得授权"
        )

    def fabricated_action_ceiling(data: dict) -> None:
        data["concepts"][0]["action_ceiling"] = (
            "这一概念必然证明宇宙中的一切行动都已获得授权"
        )

    def dangling_neighbor(data: dict) -> None:
        data["concepts"][0]["required_neighbors"].append("V82-M999")

    def dangling_conflict(data: dict) -> None:
        data["concepts"][0]["conflicts"].append("V82-M998")

    def duplicate_id(data: dict) -> None:
        data["concepts"].append(copy.deepcopy(data["concepts"][0]))
        data["concept_count"] = len(data["concepts"])

    def duplicate_name(data: dict) -> None:
        data["concepts"][1]["canonical_zh"] = data["concepts"][0]["canonical_zh"]

    def provisional_collision(data: dict) -> None:
        data["concepts"][0]["concept_id"] = "ULTRA-PROV-M01"

    def legacy_hash(data: dict) -> None:
        data["raw_sha256"] = LEGACY_V80_SHA256

    def sibling_theory(data: dict) -> None:
        data["concepts"][0]["definition"] += " crossframe-promax theory"

    def altered_contract_hash(data: dict) -> None:
        data["contracts"][0]["file_sha256"] = "0" * 64

    def dangling_contract_concept(data: dict) -> None:
        data["contracts"][0]["concept_ids"].append("V82-M997")

    def dangling_route_concept(data: dict) -> None:
        data["routes"][0]["concept_ids"].append("V82-M996")

    def dangling_route_contract(data: dict) -> None:
        data["routes"][0]["contract_ids"].append("V82-CONTRACT-MISSING")

    def unsupported_route(data: dict) -> None:
        data["routes"][0]["task"] = "这是一条与所引源文本完全无关的虚构路线。"

    def supported_route_plus_fiction(data: dict) -> None:
        data["routes"][0]["task"] += "；并且它必然证明一切行动都已获得授权。"

    def unsupported_default_route(data: dict) -> None:
        data["routes"][1]["task"] = "默认：" + data["routes"][1]["task"]

    def unrelated_route_contract(data: dict) -> None:
        data["routes"][0]["contract_ids"].append("V82-CONTRACT-WORLD-VOLUME")

    def missing_compatible_route_contract(data: dict) -> None:
        data["routes"][0]["contract_ids"].remove("V82-CONTRACT-CORE-KERNEL")

    def missing_route_backlink(data: dict) -> None:
        concept_id = load_json(copied / registry_relative)["concepts"][0]["concept_id"]
        for route in data["routes"]:
            route["concept_ids"] = [
                value for value in route["concept_ids"] if value != concept_id
            ]

    def collapsed_routes(data: dict) -> None:
        all_concepts = sorted(
            {
                concept_id
                for route in data["routes"]
                for concept_id in route["concept_ids"]
            }
        )
        all_contracts = sorted(
            {
                contract_id
                for route in data["routes"]
                for contract_id in route["contract_ids"]
            }
        )
        data["routes"] = [data["routes"][0]]
        data["routes"][0]["concept_ids"] = all_concepts
        data["routes"][0]["contract_ids"] = all_contracts
        data["route_count"] = 1

    def open_schema(data: dict) -> None:
        data["additionalProperties"] = True

    scenarios = (
        (registry_relative, missing_anchor, "source anchor"),
        (registry_relative, unsupported_definition, "unsupported"),
        (registry_relative, supported_clause_plus_fiction, "unsupported"),
        (registry_relative, fabricated_allowed_inference, "allowed_inferences"),
        (registry_relative, fabricated_action_ceiling, "action_ceiling"),
        (registry_relative, dangling_neighbor, "neighbor"),
        (registry_relative, dangling_conflict, "conflict"),
        (registry_relative, duplicate_id, "duplicate"),
        (registry_relative, duplicate_name, "duplicate"),
        (registry_relative, provisional_collision, "namespace"),
        (registry_relative, legacy_hash, "raw_sha256"),
        (registry_relative, sibling_theory, "sibling theory"),
        (contracts_relative, altered_contract_hash, "contract"),
        (contracts_relative, dangling_contract_concept, "contract"),
        (routes_relative, dangling_route_concept, "route"),
        (routes_relative, dangling_route_contract, "route"),
        (routes_relative, unsupported_route, "unsupported"),
        (routes_relative, supported_route_plus_fiction, "unsupported"),
        (routes_relative, unsupported_default_route, "unsupported"),
        (routes_relative, unrelated_route_contract, "compatibility"),
        (routes_relative, missing_compatible_route_contract, "compatibility"),
        (routes_relative, missing_route_backlink, "closure"),
        (routes_relative, collapsed_routes, "partition"),
        (schema_relative, open_schema, "open"),
    )
    for relative, mutator, needle in scenarios:
        path = copied / relative
        original = path.read_bytes()
        data = json.loads(original.decode("utf-8"))
        mutator(data)
        write_json(path, data)
        result = run_checker(copied)
        output = result.stdout + result.stderr
        assert result.returncode != 0, (relative, output)
        assert needle.casefold() in output.casefold(), (relative, needle, output)
        path.write_bytes(original)

    contract_path = copied / (
        "skills/crossframe-ultra/references/concept-contracts/core-kernel-contracts.json"
    )
    map_path = copied / contracts_relative
    contract_original = contract_path.read_bytes()
    map_original = map_path.read_bytes()
    contract = json.loads(contract_original.decode("utf-8"))
    contract["responsibility"] += "（篡改）"
    write_json(contract_path, contract)
    contract_map = json.loads(map_original.decode("utf-8"))
    contract_map["contracts"][0]["file_sha256"] = hashlib.sha256(
        contract_path.read_bytes()
    ).hexdigest()
    write_json(map_path, contract_map)
    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "fixed contract hash" in output.casefold()
    contract_path.write_bytes(contract_original)
    map_path.write_bytes(map_original)

    contract = json.loads(contract_original.decode("utf-8"))
    contract["schema_id"] = "crossframe.ultra.v8.2.contract-bypass"
    contract["responsibility"] = 7
    write_json(contract_path, contract)
    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "contract document schema" in output.casefold()
    contract_path.write_bytes(contract_original)

    contract = json.loads(contract_original.decode("utf-8"))
    contract["clauses"][0]["statement"] += (
        "；并且它必然证明一切行动都已获得授权。"
    )
    write_json(contract_path, contract)
    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "statement is unsupported" in output.casefold()
    contract_path.write_bytes(contract_original)

    registry_path = copied / registry_relative
    registry_original = registry_path.read_bytes()
    registry_text = registry_original.decode("utf-8")
    registry_path.write_text(
        registry_text.replace(
            "{",
            '{\n  "schema_id": "duplicate-key-must-fail",',
            1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    result = run_checker(copied)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "duplicate json key" in output.casefold()
    registry_path.write_bytes(registry_original)


def test_contract_hashes_are_byte_exact() -> None:
    contract_map = load_json(
        ULTRA / "references" / "concept-contracts" / "v8.2-contract-map.json"
    )
    for entry in contract_map["contracts"]:
        path = ULTRA / "references" / "concept-contracts" / entry["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["file_sha256"]


def test_all_authority_json_documents_use_closed_draft_2020_12_schemas() -> None:
    for name in (
        "ultra-source-manifest.schema.json",
        "ultra-concept-registry.schema.json",
        "ultra-contract-map.schema.json",
        "ultra-route-map.schema.json",
    ):
        schema = load_json(ULTRA / "schemas" / name)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].startswith("https://crossframe.local/schemas/ultra-")
        assert schema["additionalProperties"] is False
