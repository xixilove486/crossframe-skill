"""Validate the closed CrossFrame Ultra v8.2 knowledge authority."""

from __future__ import annotations

# Keep the direct canonical entry point safe before importing argparse,
# jsonschema, or any other path-resolved module.  The isolated child retains
# site-packages (jsonschema is required) while removing the script directory,
# cwd, and environment-dependent import paths.
import os as _bootstrap_os
import sys as _bootstrap_sys


def _bootstrap_isolated_entrypoint() -> None:
    if __name__ != "__main__" or getattr(_bootstrap_sys.flags, "isolated", 0):
        return
    canonical = _bootstrap_os.path.abspath(__file__)
    argv = [
        _bootstrap_sys.executable,
        "-I",
        "-B",
        canonical,
        *_bootstrap_sys.argv[1:],
    ]
    raise SystemExit(
        _bootstrap_os.spawnv(_bootstrap_os.P_WAIT, _bootstrap_sys.executable, argv)
    )


_bootstrap_isolated_entrypoint()

import argparse
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import types

from jsonschema import Draft202012Validator


FRAMEWORK_REVISION = "v8.2"
RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
LEGACY_V80_SHA256 = "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
EXPECTED_SOURCE_CHECKER_SHA256 = "96ab4688bd88458cf6a83028811a9ee3ee43c0b1dad2ad2039c9a54eb0068287"
MAX_KNOWLEDGE_FILE_BYTES = 1024 * 1024
# Every authority read, including the frozen source-checker bytes, is bounded
# by the same one-MiB per-file ceiling.
MAX_AUTHORITY_FILE_BYTES = MAX_KNOWLEDGE_FILE_BYTES
MAX_KNOWLEDGE_SNAPSHOT_BYTES = 4 * 1024 * 1024

ULTRA_RELATIVE = Path("skills/crossframe-ultra")
REFERENCES_RELATIVE = ULTRA_RELATIVE / "references"
SCHEMAS_RELATIVE = ULTRA_RELATIVE / "schemas"
REGISTRY_RELATIVE = REFERENCES_RELATIVE / "concept-registry/v8.2-concept-registry.json"
REGISTRY_INDEX_RELATIVE = REFERENCES_RELATIVE / "concept-registry/index.md"
CONTRACT_MAP_RELATIVE = REFERENCES_RELATIVE / "concept-contracts/v8.2-contract-map.json"
ROUTE_MAP_RELATIVE = REFERENCES_RELATIVE / "v8.2-route-map.json"

SCHEMA_FILES = {
    "source": "ultra-source-manifest.schema.json",
    "registry": "ultra-concept-registry.schema.json",
    "contracts": "ultra-contract-map.schema.json",
    "routes": "ultra-route-map.schema.json",
}
CONTRACT_FILES = frozenset(
    {
        "core-kernel-contracts.json",
        "transformation-contracts.json",
        "world-volume-contracts.json",
        "recursive-inference-contracts.json",
        "judgment-governance-contracts.json",
    }
)
EXPECTED_CONTRACT_HASHES = {
    "core-kernel-contracts.json": "36e744fb55de92ee8d9cb503816db929c5b4872c21465a94ba0733236d032160",
    "transformation-contracts.json": "9b03a4375b5ff29a9cbbaa17724acb28e8937c47cc14744f3ca03a5e8bf1a97d",
    "world-volume-contracts.json": "76136718dc95b25c2a46b8af00d497d95a5ca6ecec975ab4826cb2fac5bcaef7",
    "recursive-inference-contracts.json": "58c0d59521b979d7b249fb119a8b0af8d5436e125d09e0706f58ccc7d693331c",
    "judgment-governance-contracts.json": "20ab08e9f070a84805be0a871bc25dab1440bf46ebb0b4423f5db141da5a9f4f",
}
EXPECTED_AUTHORITY_HASHES = {
    "skills/crossframe-ultra/references/concept-registry/v8.2-concept-registry.json": "8c88d2b3d47c378b7beccd74082f8b460f5e91780f18aae1fd74d3a26242ff6d",
    "skills/crossframe-ultra/references/concept-registry/index.md": "48a9c90f9d6b1f08588a0b61f1ab343439175c92652c6d9899eb10c4d844b9df",
    "skills/crossframe-ultra/references/concept-contracts/v8.2-contract-map.json": "9c243893a7879346b4c2b8959398d6172b62df9354891184304df79b1ba7508c",
    "skills/crossframe-ultra/references/v8.2-route-map.json": "2e01bf18eb740daa8d9a07cb8bf3c78e467ee76baadcbdf12e697ad4be415b4a",
    "skills/crossframe-ultra/schemas/ultra-source-manifest.schema.json": "8e3dbf483987a99ca61a159bd723a134129242789ca848657741b8982ee690ca",
    "skills/crossframe-ultra/schemas/ultra-concept-registry.schema.json": "b254564eafbb8c8a949ff82499d4f706e6b2d7eb4e84120269d24aad048990fa",
    "skills/crossframe-ultra/schemas/ultra-contract-map.schema.json": "96423ed983d04a1693ac66f5ef003d097bb323c2a69294facbfee28e09fa3dca",
    "skills/crossframe-ultra/schemas/ultra-route-map.schema.json": "9ac0cf3368c76df6c1b0992ab3bb7cbf77ee30eb7ce90a70d8226dcabadb93c0",
}
CONCEPT_FIELDS = frozenset(
    {
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
    }
)
CONTRACT_DOCUMENT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "framework_version",
        "framework_revision",
        "raw_sha256",
        "semantic_sha256",
        "contract_id",
        "responsibility",
        "source_anchors",
        "concept_ids",
        "clauses",
    }
)
CONTRACT_ENTRY_FIELDS = frozenset(
    {"contract_id", "file", "file_sha256", "concept_ids", "source_anchors"}
)
ROUTE_FIELDS = frozenset(
    {"route_id", "task", "source_anchors", "concept_ids", "contract_ids"}
)
ALLOWED_INFERENCE_INTERFACES = frozenset(
    {
        "CAUSAL",
        "E",
        "G3",
        "G4",
        "J",
        "K",
        "N0",
        "O",
        "Q",
        "Rac",
        "Rcc",
        "Residuals",
        "SP",
        "T",
        "Unknowns",
        "W",
    }
)

ANCHOR_RE = re.compile(r"^V82-(?:P[0-9]{4}|T[0-9]{3})$")
CONCEPT_ID_RE = re.compile(r"^V82-[A-Z][A-Z0-9-]*$")
CONTRACT_ID_RE = re.compile(r"^V82-CONTRACT-[A-Z0-9-]+$")
ROUTE_ID_RE = re.compile(r"^V82-ROUTE-[A-Z0-9-]+$")
OLD_ANCHOR_RE = re.compile(r"\bV8-[PT][0-9]{3,4}\b", re.IGNORECASE)
FORBIDDEN_SIBLING_TERMS = (
    "crossframe-casebook",
    "crossframe-critical",
    "crossframe-debate",
    "crossframe-dialogue",
    "crossframe-essay",
    "crossframe-history",
    "crossframe-inquiry",
    "crossframe-promax",
    "crossframe-max",
    "crossframe-notebook",
    "crossframe-org",
    "crossframe-public",
    "crossframe-review",
    "crossframe-suite",
    "crossframe-teach",
    "skills/crossframe-promax",
    "skills\\crossframe-promax",
    "promax",
    "crossframe max",
)

SEMANTIC_UNIT_SPLIT_RE = re.compile(
    r"[\uff0c,\u3002\uff1b;\uff1a:\uff01!\uff1f?]+|(?=\u5e76\u4e14|\u4f46\u662f|\u7136\u800c|\u5426\u5219)"
)
SEMANTIC_CONNECTOR_RE = re.compile(
    r"^(?:\u5e76\u4e14|\u5e76|\u4e14|\u4f46\u662f|\u4f46|\u5374|\u800c|\u7136\u800c|\u540c\u65f6|\u5426\u5219|\u53cd\u8fc7\u6765|\u56e0\u6b64|\u4e5f)"
)
CURATED_SEMANTIC_EVIDENCE = {
    "\u56de\u8fd4\u53ea\u91cd\u5f00\u5ba1\u67e5": ("\u56de\u8fd4", "\u590d\u6838", "\u56de\u5230"),
    "\u5224\u65ad\u4e24\u4e2a\u5019\u9009\u5708\u5c42\u662f\u5426\u6784\u6210\u5d4c\u5957\u5173\u7cfb": ("\u5708\u5c42", "\u5d4c\u5957"),
    "\u4fdd\u7559\u5177\u4f53\u5305\u542b\u57fa\u51c6\u5c40\u90e8\u5dee\u5f02\u4e0e\u884c\u52a8\u4e0a\u9650": (
        "\u5305\u542b\u7684\u57fa\u51c6",
        "\u4e0d\u662f\u540c\u4e00\u5173\u7cfb",
        "\u4e0d\u80fd\u76f4\u63a5\u4ee3\u8868",
    ),
    "acrccrac\u5c40\u90e8m\u03c8qetspwkunknowns\u4e0eresiduals\u7684\u8054\u5408\u72b6\u6001\u8fb9\u754c": (
        "\u884c\u52a8\u8005\u96c6\u5408a",
        "\u5708\u5c42\u5173\u7cfbrcc",
        "\u6210\u5458\u4e0e\u89d2\u8272\u6620\u5c04rac",
        "\u672a\u77e5",
        "\u6b8b\u5dee",
    ),
    "\u8ffd\u8e2a\u8de8\u5708\u5c42\u7f51\u7edc\u4f20\u64ad\u7684\u8def\u5f84\u65f6\u5ef6\u635f\u8017\u66ff\u4ee3\u8def\u5f84\u4e0e\u9012\u5f52\u5206\u652f": (
        "\u6cbf\u65f6\u95f4\u5316\u8def\u5f84\u4f20\u5bfc",
        "\u5019\u9009\u4e0e\u66ff\u4ee3\u8def\u5f84",
        "\u65f6\u5ef6\u548c\u635f\u8017",
        "\u53ea\u751f\u6210\u5019\u9009",
    ),
    "\u5ba1\u8ba1\u591a\u5bf9\u4e00\u8868\u793a\u4e2d\u7684\u6765\u6e90\u8bef\u5dee\u4e0d\u53ef\u6062\u590d\u4fe1\u606f\u7f3a\u5931\u8eab\u4efd\u4e0e\u884c\u52a8\u4e0a\u9650": (
        "\u591a\u5bf9\u4e00\u8868\u793a\u538b\u7f29",
        "\u6e90\u6750\u6599",
        "\u8bef\u5dee",
        "\u4e0d\u53ef\u6062\u590d\u4fe1\u606f",
        "\u9ad8\u635f\u5931\u8868\u793a\u4e0d\u5f97\u652f\u6301\u9ad8\u5f71\u54cd\u884c\u52a8",
    ),
}
CURATED_SEMANTIC_GROUPS = (
    (
        (
            "在登记逐单位映射权重缺失替代规则与异质性后重现总体",
            "总体属性回填为个体属性",
            "聚合支持直接转化为成员处置",
            "只报告总体而删除尾部次序协方差局部时序或少数位置可见度",
            "须与多对一表示压缩区分",
            "m01固定单位总体分区",
            "合理替代聚合规则造成方向反转",
            "只能登记当前分区与聚合规则下的总体",
        ),
        ("单位总体分区聚合", "逐单位映射", "不得据总体结果直接处置成员"),
    ),
    (
        (
            "必须声明具体包含基准",
            "在已声明基准上记录局部或全部包含",
            "单父树",
            "外层规则自动代表所有内层位置",
            "用子圈层状态直接代表上层",
            "成员角色合同资源会计制度管辖或空间中的具体包含依据",
            "只有部分共享成员但不存在包含时应登记为重叠",
            "无法证明任何具体包含依据",
            "只能描述包含关系",
            "不能自动推出价值优先级或行动授权",
        ),
        ("圈层部分或全部包含", "必须说明包含的基准", "子圈层的状态不能直接代表上层"),
    ),
    (
        (
            "在已登记路径时延与损耗上记录条件传播",
            "连接或同步直接等同于传播支持",
            "中心性替代意图责任或处置权限",
            "只保留终点影响并声称恢复了传播次序",
            "须与共同环境或同步变化区分",
            "候选路径与替代路径分别登记",
            "切断候选路径后结果不变且零结论门未通过时保持未决",
            "节点边方向采样边界或路径时间次序无法追踪",
            "只能描述有证据的传播路径",
            "不能由中心性推出意图责任或处置权限",
        ),
        ("沿时间化路径传导", "候选与替代路径", "中心性不等于意图责任或处置权限"),
    ),
    (
        (
            "在冻结时间基准窗口与组合规则后登记累积衰减或恢复",
            "控制后效应消失直接写成无累积",
            "基础时间组合预先证明g3",
            "结果后更换窗口或忽略共同趋势季节与队列",
            "时间组合与历史条件增量分开",
            "后者另链g3instance",
            "时间基准基线窗口时滞持久阈值累积或衰减或恢复规则及替代窗口",
            "效应随合理替代窗口改变且正向支持不足",
            "时间基准窗口时滞或组合规则未在结果前冻结",
            "只能登记冻结窗口内的纵向组合",
            "不能自动推出历史条件增量或现实行动授权",
        ),
        ("带窗口的纵向组合", "累积衰减恢复规则", "只有历史项在控制当前状态后仍提供条件增量"),
    ),
    (
        (
            "在记录角色资源决策规则或后续转移持久改变时登记制度化事实",
            "制度存在替代法律有效规范正当保护成立或应继续",
            "治理失败抹掉已经存在的制度事实",
            "把法律有效性治理质量或规范正当性伪装成institutionalfact",
            "制度事实制度因果效应制度对象转换和制度干预转换必须选择独立支路",
            "记录角色资源决策规则或后续转移的可追踪持久改变",
            "只有制度声明而没有任何持久写回",
            "无法证明任何制度字段发生持久改变",
            "只能区分制度事实及其支路",
            "制度存在不能推出合法正当充分保护或应继续",
        ),
        ("持久制度写回", "制度事实上存在", "institutionalfact"),
    ),
    (
        (
            "在同一指标上比较互动生成目标模式与预登记简单加和模型",
            "宏观模式反推唯一微观原因",
            "涌现自动证明下行因果",
            "简单加和模型表现相当但零结论门未通过时宣布加和已经足够",
            "目标尺度模式与下行约束分开",
            "后者另链g4或causal实例",
            "源单位互动规则目标对象目标模式同指标的预登记简单加和模型",
            "简单加和模型在同一指标上表现相当且充分性或等价门通过",
            "源单位互动规则目标模式或比较模型不可追踪",
            "只能登记目标尺度模式的条件支持",
            "不能自动推出下行因果或行动授权",
        ),
        ("互动生成目标尺度模式", "预登记简单加和模型", "不能自动证明下行因果"),
    ),
    (
        (
            "无授权时记录实际代行及其影响和责任",
            "仅在授权元组独立有效性证据与jauthorization同时通过时登记j转移",
            "多数可见性影响力自称或实际控制替代有效委托",
            "实际代行自动扩展j轴",
            "把代表性主张实际代行授权有效性与j转移混成一支",
            "representationclaimactualactsdelegationvalidity与jtransfer必须选择独立支路",
            "代表主张实际代行事实争议状态委托记录结构化授权元组与独立有效性证据",
            "自称代表或实际控制但不存在有效授权",
            "代表主体代行动作或授权来源无法识别",
            "前三支不能改变j",
            "只有有效jtransfer才能在原子授权范围内扩展权限",
        ),
        ("代表事实分类与可选授权转移", "实际代行及其影响和责任", "jauthorization同时通过"),
    ),
    (
        (
            "在来源算法误差与任务不变量可追踪时登记多对一表示",
            "unknownnotapplicablenotobservable或withheldforprotection压成不存在",
            "高损失表示支持高影响行动",
            "只保留压缩结果而删除算法版本阈值误差和不可恢复信息",
            "须与单位总体分区聚合区分",
            "m08的对象是多对一表示",
            "压缩后无法区分不同缺失身份或保护性不公开",
            "源材料算法版本误差或任务不变量无法追踪",
            "压缩结果也不能把缺失身份改写为不存在",
        ),
        ("多对一表示压缩", "误差不可恢复信息", "高损失表示不得支持高影响行动"),
    ),
    (
        (
            "把源域材料作为目标域的可检验候选",
            "源域支持替代独立目标实例",
            "类比生成目标领域行动授权",
            "目标证据不足时宣布目标机制不存在",
            "映射差异断裂禁止映射目标责任链和j轴差异分别登记",
            "源目标映射差异断裂禁止映射目标责任链j轴差异与独立目标实例",
            "独立目标实例不支持源域类比产生的候选",
            "源目标映射禁止映射或目标责任链无法登记",
            "类比只能生成目标候选",
            "不能生成目标真值目标机制不存在的证明或行动授权",
        ),
        ("跨领域类比迁移", "源域材料只生成目标候选", "类比不生成目标领域行动授权"),
    ),
)
CURATED_SEMANTIC_GROUPS += (
    (
        (
            "共同内核五层责任六条方法公理信息身份与推论边界",
            "共同内核只统一论证责任与边界",
            "不要求不同权威文本使用相同章法制品数量或编号",
            "五层稳定引用分别是定义层方法公理层根一至根四论一至论十二和治理不变量",
            "六条共同方法公理约束任务相对表示信息身份转义损失表示闭合与路径等价模拟再入和规范授权",
            "模拟递归不得提升认识地位",
            "事实前瞻和能力不得生成价值责任或授权",
        ),
        ("共同内核只统一论证责任与边界", "信息身份不得静默升级", "事实前瞻和能力不生成价值责任与授权"),
    ),
    (
        (
            "尺度变换圈层关系变换表示或表述转义任务相关损失有效变量闭合与残差回返",
            "九种算子各有独有semanticsignature",
            "尺度变换圈层关系变换和表示或表述转义必须拆成有序记录",
            "嵌套必须声明成员角色资源会计制度管辖或空间等具体包含基准",
            "不允许用子圈层状态代表上层",
            "源任务中可区分而目标表示中不可区分的差异登记为任务相关损失",
            "不得断言必然有损",
            "异常必须保留回返地址",
            "回返只重开审查",
            "往返重构也不能替代预先声明的保持项损失容限与目标侧结果",
            "有效变量必须绑定任务与失效边界",
            "目标表示不默认闭合",
            "出现条件增量时只能登记记忆噪声迟滞未解析项或残差候选",
        ),
        ("每个算子都有独有semanticsignature", "必须拆成有序记录", "目标表示不默认动力闭合"),
    ),
    (
        (
            "联合对象明确包含行动者a圈层c圈层关系rcc成员与角色映射rac物质状态m体验意义状态ψ通道与约束q事件流e多时钟t尺度剖面sp证据状态w与同一性判据k",
            "联合对象必须保留局部差异和跨边界通道",
            "不得把所有相关对象合并为一个超圈层或宣称更高主体",
            "冻结快照必须记录关系成员映射mψ通道约束多时钟尺度剖面未知残差和k",
            "保留观察支持候选争议未知或不适用等状态",
        ),
        ("联合对象的价值在于保留局部差异和跨边界通道", "行动者集合a圈层集合c", "快照是推演的冻结起点"),
    ),
    (
        (
            "一至三阶递归谱系分支合并剪枝停止局部可预测性与按阶评价",
            "不得用单一递归标签混写",
            "默认探索上限为三阶",
            "第二阶检查行动集合与反馈的改变",
            "第三阶检查制度化锁定反转溢出和生成条件改变",
            "条件不足必须提前停止",
            "每次再入都记录父运行与父路径继承假设新增条件损失未知残差返回路径和停止原因",
            "子运行继承未解决项且不得把模拟起点改写为现实",
            "每阶保留主要竞争低概率高后果和残差路径",
            "合并必须满足同一性与状态等价条件",
            "剪枝需事前声明并保留被剪记录",
            "同一性适用域闭合分支敏感性残差增量校准权利授权或三阶上限任一停止条件触发时必须停止或降级",
            "可预测性只能在明确对象与资源边界内主张",
            "一至三阶分别冻结分别评价并与浅阶和简单延续比较",
            "不得把内部递归内容升级为现实证据",
        ),
        ("三个正交维度", "默认探索上限", "停止或降级"),
    ),
    (
        (
            "证据身份",
            "事实前瞻价值责任与授权分离",
            "行动上限及框架治理",
            "报告观测模型信念模拟证据与授权保持不同身份",
            "任何产物不得静默跨越来源建模前瞻评价授权和执行责任",
            "推演前瞻和有限选择使用不同合同",
            "事实不自行选择价值或制造授权",
            "现实行动必须经过事实规范方案与有限执行的独立转换",
            "证据增强只能提高描述判断上限",
            "授权前只允许补证或保护性保全",
            "最终行动上限取描述规范保护方案管辖可逆性和期限的最窄交集",
            "框架不能自证现实安全或行动授权",
            "断言必须登记证据反证替代解释撤回条件和行动上限",
            "反例必须写回文本流程或行动上限",
        ),
        ("信息身份不得静默升级", "事实不自行选择价值", "最终行动上限取描述上限"),
    ),
    (
        ("审计单位到总体的分区聚合异质性与成员处置上限",),
        ("单位总体分区聚合", "异质性", "不得据总体结果直接处置成员"),
    ),
    (
        ("在冻结窗口内比较累积衰减恢复规则与历史增量边界",),
        ("带窗口的纵向组合", "累积衰减恢复规则", "历史项在控制当前状态后仍提供条件增量"),
    ),
    (
        ("区分制度事实法律有效规范正当保护与继续授权",),
        ("制度事实上存在", "法律有效", "是否应继续"),
    ),
    (
        ("比较互动生成目标模式与简单加和模型", "隔离下行因果"),
        ("互动生成目标尺度模式", "预登记简单加和模型", "不能自动证明下行因果"),
    ),
    (
        ("分开代表主张实际代行委托有效性与j轴权限转移",),
        ("代表性主张", "实际代行事实", "j轴权限转移"),
    ),
    (
        ("把跨领域类比限制为目标候选", "要求独立目标证据与授权"),
        ("跨领域类比迁移", "源域材料只生成目标候选", "独立目标实例"),
    ),
)
for _units, _markers in CURATED_SEMANTIC_GROUPS:
    for _unit in _units:
        CURATED_SEMANTIC_EVIDENCE.setdefault(_unit, _markers)
CURATED_SEMANTIC_EVIDENCE.update(
    {
        "共同内核五层责任六条方法公理信息身份与推论边界": ("同一内核只统一论证责任与边界", "方法公理层", "信息身份不得静默升级"),
        "共同内核只统一论证责任与边界": ("同一内核只统一论证责任与边界",),
        "不要求不同权威文本使用相同章法制品数量或编号": ("不要求使用同一章法制品数量或编号",),
        "五层稳定引用分别是定义层方法公理层根一至根四论一至论十二和治理不变量": ("定义层", "方法公理层", "根一至根四", "论一至论十二", "治理不变量"),
        "六条共同方法公理约束任务相对表示信息身份转义损失表示闭合与路径等价模拟再入和规范授权": ("任务相对性", "信息身份不得静默升级", "模拟再入不得提升认识地位"),
        "模拟递归不得提升认识地位": ("模拟再入不得提升认识地位",),
        "事实前瞻和能力不得生成价值责任或授权": ("事实前瞻和能力不生成价值责任与授权",),
        "报告观测模型信念模拟证据与授权保持不同身份": ("报告不能自动成为观测", "模型信念不能自动成为事实", "模拟不能自动成为证据或授权"),
        "任何产物不得静默跨越来源建模前瞻评价授权和执行责任": ("来源建模前瞻评价授权和执行责任不得由一个产物自动跨越",),
        "推演前瞻和有限选择使用不同合同": ("把二者分成不同合同", "有限选择"),
        "事实不自行选择价值或制造授权": ("事实不自行选择价值", "不自行制造授权"),
        "现实行动必须经过事实规范方案与有限执行的独立转换": ("任何从解释或诊断转入现实行动的流程都必须经过四次转换", "有限执行"),
        "证据增强只能提高描述判断上限": ("证据增强可以提高描述判断的上限",),
        "授权前只允许补证或保护性保全": ("行动上限是不行动或补证", "最多允许保护性可逆的保全"),
        "最终行动上限取描述规范保护方案管辖可逆性和期限的最窄交集": ("最终行动上限取描述上限", "可逆性和到期时间的最窄交集"),
        "框架不能自证现实安全或行动授权": ("框架不能用自己的语言证明自己安全", "不产生现实行动授权"),
        "断言必须登记证据反证替代解释撤回条件和行动上限": ("记断言文本", "证据反证替代解释撤回条件行动上限"),
        "反例必须写回文本流程或行动上限": ("反例只被归档而不改文本流程或行动上限",),
        "不得用单一递归标签混写": ("三者不得用一个递归词混写",),
        "默认探索上限为三阶": ("把三阶设为默认探索上限",),
        "第二阶检查行动集合与反馈的改变": ("第二阶考察第一阶状态如何改变行动集合", "反馈和适应"),
        "第三阶检查制度化锁定反转溢出和生成条件改变": ("第三阶考察制度化锁定反转", "生成条件本身的改变"),
        "条件不足必须提前停止": ("条件不足时必须提前停止",),
        "每次再入都记录父运行与父路径继承假设新增条件损失未知残差返回路径和停止原因": ("每次再入前都执行一次转义审计", "父运行父路径", "继承假设新增条件", "返回路径和停止原因"),
        "子运行继承未解决项且不得把模拟起点改写为现实": ("子运行必须继承父运行尚未解决的未知损失和残差", "模拟起点不得改写成当前现实"),
        "每阶保留主要竞争低概率高后果和残差路径": ("每阶至少保留当前主要路径", "低概率高后果路径和残差出口"),
        "合并必须满足同一性与状态等价条件": ("只有对象同一性保持", "关键状态在预定容差内等价"),
        "剪枝需事前声明并保留被剪记录": ("剪枝规则必须事前声明", "保留被剪分支"),
        "同一性适用域闭合分支敏感性残差增量校准权利授权或三阶上限任一停止条件触发时必须停止或降级": ("出现对象或尺度同一性失效", "触及权利或授权边界", "到达第三阶上限时停止或降级"),
        "可预测性只能在明确对象与资源边界内主张": ("任何可预测性主张都必须绑定对象", "计算和观测资源"),
        "一至三阶分别冻结分别评价并与浅阶和简单延续比较": ("第一第二第三阶分别冻结并分别评价", "更浅阶次加简单延续比较"),
        "不得把内部递归内容升级为现实证据": ("不能自造现实证据", "模型内部的推理内容"),
        "九种算子各有独有semanticsignature": ("每个算子都有独有semanticsignature",),
        "尺度变换圈层关系变换和表示或表述转义必须拆成有序记录": ("三者可以同时发生但必须拆成有序记录",),
        "源任务中可区分而目标表示中不可区分的差异登记为任务相关损失": ("源任务中可区分的源状态", "目标表示中无法区分", "登记任务相关损失"),
        "不得断言必然有损": ("不是必然有损",),
        "异常必须保留回返地址": ("异常出现时回到哪个父记录或合同",),
        "往返重构也不能替代预先声明的保持项损失容限与目标侧结果": ("往返重构可以作为检验", "预先声明的保持项损失容限和目标侧结果"),
        "有效变量必须绑定任务与失效边界": ("有效变量", "必须绑定对象尺度时间窗任务", "失效与退役"),
        "目标表示不默认闭合": ("目标表示不默认动力闭合",),
        "出现条件增量时只能登记记忆噪声迟滞未解析项或残差候选": ("出现增量时", "登记为记忆噪声迟滞未解析项或残差候选"),
        "联合对象明确包含行动者a圈层c圈层关系rcc成员与角色映射rac物质状态m体验意义状态ψ通道与约束q事件流e多时钟t尺度剖面sp证据状态w与同一性判据k": ("行动者集合a", "圈层关系rcc", "同一性判据k"),
        "联合对象必须保留局部差异和跨边界通道": ("联合对象的价值在于保留局部差异和跨边界通道",),
        "不得把所有相关对象合并为一个超圈层或宣称更高主体": ("不是把所有相关对象装进一个大圈层", "不是宣称存在一个更高主体"),
        "冻结快照必须记录关系成员映射mψ通道约束多时钟尺度剖面未知残差和k": ("快照是推演的冻结起点", "关系和成员映射", "未知残差和同一性判据"),
        "保留观察支持候选争议未知或不适用等状态": ("观察到得到支持的假设候选争议未知或不适用",),
        "默认": ("描述性嵌套只检验边界成员重叠退出和接口映射",),
    }
)


class DuplicateKeyError(ValueError):
    """Raised when an authority JSON document contains a duplicate key."""


def _deduplicate(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw_json(item) for item in value]
    return value


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(metadata, "st_file_attributes", 0) & reparse)


def _safe_repo(repo: Path) -> Path:
    repo = Path(os.path.abspath(repo))
    if not repo.is_dir():
        raise ValueError(f"repository root is not a directory: {repo}")
    if _is_link_or_reparse(repo):
        raise ValueError(f"repository root is a symlink or reparse point: {repo}")
    return repo


def _assert_safe_path(path: Path, repo: Path) -> None:
    path = Path(os.path.abspath(path))
    repo = Path(os.path.abspath(repo))
    try:
        path.relative_to(repo)
    except ValueError as error:
        raise ValueError(f"path escapes repository: {path}") from error
    current = path
    while True:
        if current.exists() and _is_link_or_reparse(current):
            raise ValueError(f"path contains symlink or reparse point: {current}")
        if current == repo:
            return
        parent = current.parent
        if parent == current:
            raise ValueError(f"repository ancestor was not reached: {repo}")
        current = parent


def _windows_final_path(handle: object) -> str:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_final_path = kernel32.GetFinalPathNameByHandleW
    get_final_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    get_final_path.restype = wintypes.DWORD
    capacity = 32768
    while True:
        buffer = ctypes.create_unicode_buffer(capacity)
        length = get_final_path(handle, buffer, capacity, 0)
        if length == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        if length < capacity:
            value = buffer.value
            break
        capacity = length + 1
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.abspath(value))


def _read_regular_windows(path: Path, repo: Path, max_bytes: int) -> bytes:
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", FILETIME),
            ("ftLastAccessTime", FILETIME),
            ("ftLastWriteTime", FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    get_info = kernel32.GetFileInformationByHandle
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
    get_info.restype = wintypes.BOOL
    read_file = kernel32.ReadFile
    read_file.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    read_file.restype = wintypes.BOOL

    FILE_READ_ATTRIBUTES = 0x0080
    GENERIC_READ = 0x80000000
    FILE_SHARE_CONTENT = 0x00000001 | 0x00000002
    FILE_SHARE_ALL = FILE_SHARE_CONTENT | 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
    FILE_ATTRIBUTE_DIRECTORY = 0x0010
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    invalid_handle = wintypes.HANDLE(-1).value

    def open_handle(target: Path, access: int, flags: int, share: int):
        handle = create_file(
            str(target),
            access,
            share,
            None,
            OPEN_EXISTING,
            flags,
            None,
        )
        if handle == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def information(handle: object) -> BY_HANDLE_FILE_INFORMATION:
        value = BY_HANDLE_FILE_INFORMATION()
        if not get_info(handle, ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    def identity(value: BY_HANDLE_FILE_INFORMATION) -> tuple[int, ...]:
        return (
            value.dwVolumeSerialNumber,
            value.nFileIndexHigh,
            value.nFileIndexLow,
            value.nFileSizeHigh,
            value.nFileSizeLow,
            value.ftLastWriteTime.dwHighDateTime,
            value.ftLastWriteTime.dwLowDateTime,
        )

    relative = Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(repo)))
    directory_handles: list[object] = []
    pinned_directories: list[tuple[object, str]] = []
    repo_handle = open_handle(
        repo,
        FILE_READ_ATTRIBUTES,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        FILE_SHARE_CONTENT,
    )
    directory_handles.append(repo_handle)
    file_handle = None
    try:
        repo_info = information(repo_handle)
        if not repo_info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY:
            raise ValueError(f"repository root is not a directory: {repo}")
        if repo_info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"repository root is a reparse point: {repo}")
        repo_final = _windows_final_path(repo_handle)
        requested_repo = os.path.normcase(os.path.abspath(str(repo)))
        if repo_final != requested_repo:
            raise ValueError(
                "repository handle does not match requested path: "
                f"expected {requested_repo}, got {repo_final}"
            )
        pinned_directories.append((repo_handle, repo_final))
        for index in range(1, len(relative.parts)):
            requested_directory = repo.joinpath(*relative.parts[:index])
            directory_handle = open_handle(
                requested_directory,
                FILE_READ_ATTRIBUTES,
                FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
                FILE_SHARE_CONTENT,
            )
            directory_handles.append(directory_handle)
            directory_info = information(directory_handle)
            if not directory_info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY:
                raise ValueError(
                    f"authority ancestor is not a directory: {requested_directory}"
                )
            if directory_info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError(
                    f"authority ancestor is a reparse point: {requested_directory}"
                )
            expected_directory = os.path.normcase(
                os.path.join(repo_final, *relative.parts[:index])
            )
            actual_directory = _windows_final_path(directory_handle)
            if actual_directory != expected_directory:
                raise ValueError(
                    "authority ancestor handle does not match requested path: "
                    f"expected {expected_directory}, got {actual_directory}"
                )
            pinned_directories.append((directory_handle, expected_directory))
        file_handle = open_handle(
            path,
            GENERIC_READ | FILE_READ_ATTRIBUTES,
            FILE_FLAG_OPEN_REPARSE_POINT,
            FILE_SHARE_ALL,
        )
        before = information(file_handle)
        if before.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError(f"authority path is not a regular non-reparse file: {path}")
        target_final = _windows_final_path(file_handle)
        expected_target = os.path.normcase(os.path.join(repo_final, *relative.parts))
        if target_final != expected_target:
            raise ValueError(
                "authority file handle does not match requested path: "
                f"expected {expected_target}, got {target_final}"
            )
        size = (before.nFileSizeHigh << 32) | before.nFileSizeLow
        if size > max_bytes:
            raise ValueError(
                f"authority file exceeds safety limit: {size} > {max_bytes}"
            )
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            requested = min(1024 * 1024, remaining)
            buffer = ctypes.create_string_buffer(requested)
            received = wintypes.DWORD()
            if not read_file(file_handle, buffer, requested, ctypes.byref(received), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if received.value == 0:
                break
            chunks.append(buffer.raw[: received.value])
            remaining -= received.value
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            raise ValueError("authority file grew beyond the safety limit while being read")
        for pinned_handle, expected_directory in pinned_directories:
            actual_directory = _windows_final_path(pinned_handle)
            if actual_directory != expected_directory:
                raise ValueError(
                    "authority ancestor changed while being read: "
                    f"expected {expected_directory}, got {actual_directory}"
                )
        actual_target = _windows_final_path(file_handle)
        if actual_target != expected_target:
            raise ValueError(
                "authority file final path changed while being read: "
                f"expected {expected_target}, got {actual_target}"
            )
        after = information(file_handle)
        if identity(before) != identity(after) or len(payload) != size:
            raise ValueError(f"authority file changed while being read: {path}")
        return payload
    finally:
        if file_handle is not None:
            close_handle(file_handle)
        for directory_handle in reversed(directory_handles):
            close_handle(directory_handle)


def _posix_fd_matches_requested_path(fd: int, requested: Path) -> None:
    """Verify that a pinned descriptor still names the requested path.

    Descriptor-relative, O_NOFOLLOW traversal protects the read from a
    symlink/junction substitution, but a POSIX directory can still be renamed
    after it is opened.  Where procfs exposes the kernel's final descriptor
    path, compare it byte-for-byte (modulo the platform's case rules).  On
    systems without procfs, fall back to an identity comparison against the
    non-following requested path and fail closed when that cannot be obtained.
    """
    requested = Path(os.path.abspath(requested))
    proc_link = Path("/proc/self/fd") / str(fd)
    try:
        actual = os.readlink(proc_link)
    except (OSError, ValueError):
        actual = None
    if actual is not None:
        actual_path = os.path.normcase(os.path.abspath(os.fsdecode(actual)))
        expected_path = os.path.normcase(str(requested))
        if actual_path != expected_path:
            raise ValueError(
                "pinned descriptor final path does not match requested path: "
                f"expected {expected_path}, got {actual_path}"
            )
        return
    try:
        expected_info = os.stat(requested, follow_symlinks=False)
        actual_info = os.fstat(fd)
    except OSError as error:
        raise ValueError(
            f"cannot verify pinned descriptor requested path: {requested}: {error}"
        ) from error
    if (
        expected_info.st_dev,
        expected_info.st_ino,
        expected_info.st_mode,
    ) != (
        actual_info.st_dev,
        actual_info.st_ino,
        actual_info.st_mode,
    ):
        raise ValueError(
            "pinned descriptor identity does not match requested path: "
            f"{requested}"
        )


def _read_regular_posix(path: Path, repo: Path, max_bytes: int) -> bytes:
    relative = Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(repo)))
    parts = relative.parts
    if not parts:
        raise ValueError(f"authority path does not name a file: {path}")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if (
        not nofollow
        or not directory_flag
        or os.open not in getattr(os, "supports_dir_fd", ())
    ):
        raise ValueError("anchored no-follow file reads are unavailable on this platform")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    directory_flags = flags | directory_flag
    directory_fd = os.open(repo, directory_flags)
    directory_fds: list[int] = [directory_fd]
    file_fd: int | None = None
    try:
        root_info = os.fstat(directory_fd)
        if not stat.S_ISDIR(root_info.st_mode):
            raise ValueError(f"repository root is not a directory: {repo}")
        _posix_fd_matches_requested_path(directory_fd, repo)
        requested_directories = [Path(repo)]
        for component in parts[:-1]:
            next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            directory_fds.append(next_fd)
            directory_fd = next_fd
            if not stat.S_ISDIR(os.fstat(directory_fd).st_mode):
                raise ValueError(f"authority ancestor is not a directory: {component}")
            requested_directories.append(requested_directories[-1] / component)
            _posix_fd_matches_requested_path(directory_fd, requested_directories[-1])
        file_fd = os.open(parts[-1], flags, dir_fd=directory_fd)
        _posix_fd_matches_requested_path(file_fd, path)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"authority path is not a regular file: {path}")
        if before.st_size > max_bytes:
            raise ValueError(
                f"authority file exceeds safety limit: {before.st_size} > "
                f"{max_bytes}"
            )
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(file_fd, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            raise ValueError("authority file grew beyond the safety limit while being read")
        after = os.fstat(file_fd)
        for pinned_fd, requested_directory in zip(
            directory_fds,
            requested_directories,
        ):
            _posix_fd_matches_requested_path(pinned_fd, requested_directory)
        _posix_fd_matches_requested_path(file_fd, path)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after or len(payload) != before.st_size:
            raise ValueError(f"authority file changed while being read: {path}")
        return payload
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def _read_regular(
    path: Path,
    repo: Path,
    *,
    max_bytes: int | None = None,
) -> bytes:
    if max_bytes is None:
        max_bytes = MAX_KNOWLEDGE_FILE_BYTES
    if max_bytes < 1:
        raise ValueError("authority read budget is exhausted")
    _assert_safe_path(path, repo)
    if os.name == "nt":
        return _read_regular_windows(Path(path), Path(repo), max_bytes)
    return _read_regular_posix(Path(path), Path(repo), max_bytes)


def _pairs_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _strict_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite JSON number is forbidden: {value}")
    return parsed


def _parse_json_bytes(payload: bytes, label: str, errors: list[str]) -> object | None:
    try:
        text = payload.decode("utf-8")
        if text.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is forbidden")
        return json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_non_finite_json_constant,
            parse_float=_strict_json_float,
        )
    except Exception as error:
        errors.append(f"{label}: cannot load authority JSON: {error}")
        return None


class _KnowledgeSnapshot:
    def __init__(self, repo: Path, errors: list[str]) -> None:
        self.repo = repo
        self.errors = errors
        self.payloads: dict[str, bytes] = {}
        self.total_bytes = 0

    def capture(self, relative: Path) -> None:
        label = relative.as_posix()
        if label in self.payloads:
            return
        remaining = MAX_KNOWLEDGE_SNAPSHOT_BYTES - self.total_bytes
        read_limit = min(MAX_KNOWLEDGE_FILE_BYTES, remaining)
        try:
            payload = _read_regular(
                self.repo / relative,
                self.repo,
                max_bytes=read_limit,
            )
        except Exception as error:
            self.errors.append(
                f"{label}: cannot capture authority snapshot within knowledge "
                f"budgets (file={MAX_KNOWLEDGE_FILE_BYTES}, "
                f"total={MAX_KNOWLEDGE_SNAPSHOT_BYTES}): {error}"
            )
            return
        self.payloads[label] = payload
        self.total_bytes += len(payload)

    def bytes(self, relative: Path) -> bytes | None:
        return self.payloads.get(relative.as_posix())

    def json(self, relative: Path) -> object | None:
        label = relative.as_posix()
        payload = self.payloads.get(label)
        if payload is None:
            return None
        return _parse_json_bytes(payload, label, self.errors)


def _capture_knowledge_snapshot(repo: Path, errors: list[str]) -> _KnowledgeSnapshot:
    snapshot = _KnowledgeSnapshot(repo, errors)
    paths = [
        REGISTRY_RELATIVE,
        REGISTRY_INDEX_RELATIVE,
        CONTRACT_MAP_RELATIVE,
        ROUTE_MAP_RELATIVE,
        *(SCHEMAS_RELATIVE / name for name in SCHEMA_FILES.values()),
        *(
            REFERENCES_RELATIVE / "concept-contracts" / name
            for name in sorted(CONTRACT_FILES)
        ),
    ]
    for relative in paths:
        snapshot.capture(relative)
    return snapshot


def _validate_contract_directory_closure(repo: Path, errors: list[str]) -> None:
    """Reject authority contract files outside the frozen six-file set."""
    directory = repo / REFERENCES_RELATIVE / "concept-contracts"
    expected = set(CONTRACT_FILES) | {CONTRACT_MAP_RELATIVE.name}
    seen: set[str] = set()
    try:
        _assert_safe_path(directory, repo)
        with os.scandir(directory) as entries:
            for entry in entries:
                path = directory / entry.name
                if _is_link_or_reparse(path):
                    errors.append(
                        f"contract directory contains symlink or reparse point: {entry.name}"
                    )
                    continue
                if not entry.is_file(follow_symlinks=False):
                    errors.append(
                        f"contract directory contains non-regular entry: {entry.name}"
                    )
                    continue
                seen.add(entry.name)
    except (OSError, ValueError) as error:
        errors.append(f"contract directory cannot be inspected safely: {error}")
        return
    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    if missing or extra:
        errors.append(
            "contract directory closure mismatch: "
            f"missing={missing}, extra={extra}"
        )


class _ImportIsolation:
    """Temporarily remove repository paths and repository-loaded modules."""

    def __init__(self, repo: Path) -> None:
        self.repo = Path(os.path.realpath(os.path.abspath(repo)))
        self.original_path: list[str] | None = None
        self.removed_modules: dict[str, object] = {}

    def _inside_repo(self, value: object) -> bool:
        if not isinstance(value, str) or not value:
            return False
        # Module specs use non-path sentinels for built-ins and frozen
        # modules.  Treating ``built-in`` as a relative path would resolve it
        # under the repository and accidentally remove ``sys`` (and its
        # executable attribute) from sys.modules during isolation.
        if value in {"built-in", "frozen", "namespace"}:
            return False
        if not os.path.isabs(value) and not any(
            separator in value for separator in ("/", "\\")
        ) and not re.match(r"^[A-Za-z]:", value):
            return False
        try:
            candidate = Path(os.path.realpath(os.path.abspath(value)))
            candidate.relative_to(self.repo)
        except (OSError, ValueError):
            return False
        return True

    def _module_is_repo_loaded(self, module: object) -> bool:
        origins: list[object] = [getattr(module, "__file__", None)]
        spec = getattr(module, "__spec__", None)
        origins.append(getattr(spec, "origin", None))
        module_path = getattr(module, "__path__", None)
        if module_path is not None:
            try:
                origins.extend(module_path)
            except TypeError:
                pass
        return any(self._inside_repo(origin) for origin in origins)

    def __enter__(self) -> "_ImportIsolation":
        self.original_path = list(sys.path)
        safe_path: list[str] = []
        for entry in self.original_path:
            candidate = entry or os.curdir
            if not self._inside_repo(candidate):
                safe_path.append(entry)
        sys.path[:] = safe_path
        for module_name, module in list(sys.modules.items()):
            if self._module_is_repo_loaded(module):
                self.removed_modules[module_name] = module
                del sys.modules[module_name]
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        for module_name, module in self.removed_modules.items():
            current = sys.modules.get(module_name)
            if current is not None:
                del sys.modules[module_name]
            sys.modules[module_name] = module
        if self.original_path is not None:
            sys.path[:] = self.original_path


_SOURCE_MODULE_SEQUENCE = 0


def _module_from_source(
    name: str,
    path: Path,
    payload: bytes,
    *,
    repo: Path | None = None,
) -> object:
    global _SOURCE_MODULE_SEQUENCE

    source = payload.decode("utf-8")
    _SOURCE_MODULE_SEQUENCE += 1
    module_name = (
        f"{name}_{sha256(payload).hexdigest()}_"
        f"{os.getpid()}_{_SOURCE_MODULE_SEQUENCE}"
    )
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__spec__ = None
    isolation = _ImportIsolation(repo or Path(path).parent)
    with isolation:
        sys.modules[module_name] = module
        try:
            exec(compile(source, str(path), "exec"), module.__dict__)
        finally:
            # The dynamic module is intentionally never resident after exec,
            # including the exceptional path.
            sys.modules.pop(module_name, None)
    return module


def _load_source_checker(repo: Path):
    path = repo / ULTRA_RELATIVE / "scripts/check_crossframe_ultra_v82_source.py"
    payload = _read_regular(path, repo)
    actual_hash = sha256(payload).hexdigest()
    if actual_hash != EXPECTED_SOURCE_CHECKER_SHA256:
        raise ValueError(
            "source authority checker hash mismatch: "
            f"expected {EXPECTED_SOURCE_CHECKER_SHA256}, got {actual_hash}"
        )
    module = _module_from_source(
        "ultra_v82_knowledge_source_checker",
        path,
        payload,
        repo=repo,
    )
    expected_bindings = {
        "RAW_SHA256": RAW_SHA256,
        "SEMANTIC_SHA256": SEMANTIC_SHA256,
    }
    for name, expected in expected_bindings.items():
        if getattr(module, name, None) != expected:
            raise ValueError(f"source authority checker binding mismatch: {name}")
    return module


def _closed_schema_errors(schema: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(schema, dict):
        object_schema = schema.get("type") == "object" or "properties" in schema
        if object_schema and schema.get("additionalProperties") is not False:
            errors.append(f"{path}: object schema is open")
        for key, value in schema.items():
            errors.extend(_closed_schema_errors(value, f"{path}/{key}"))
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            errors.extend(_closed_schema_errors(value, f"{path}/{index}"))
    return errors


def _validate_schema(
    label: str,
    schema: object,
    instance: object,
    errors: list[str],
) -> None:
    if not isinstance(schema, dict):
        errors.append(f"{label}: schema root must be an object")
        return
    schema_id = schema.get("$id")
    if not isinstance(schema_id, str) or not schema_id.startswith(
        "https://crossframe.local/schemas/ultra-"
    ):
        errors.append(f"{label}: schema $id is outside the Ultra namespace")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{label}: schema is not Draft 2020-12")
    errors.extend(f"{label}: {error}" for error in _closed_schema_errors(schema))
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        errors.append(f"{label}: invalid Draft 2020-12 schema: {error}")
        return
    validator = Draft202012Validator(schema)
    try:
        validation_errors = sorted(
            validator.iter_errors(instance),
            key=lambda item: tuple(str(part) for part in item.path),
        )
    except Exception as error:
        errors.append(f"{label}: schema evaluation failed closed: {error}")
        return
    for error in validation_errors:
        location = "/".join(str(part) for part in error.path) or "$"
        errors.append(f"{label}: instance violation at {location}: {error.message}")


def _validate_contract_document_schema(
    schema: object,
    document: object,
    label: str,
    errors: list[str],
) -> None:
    if (
        not isinstance(schema, dict)
        or not isinstance(schema.get("$defs"), dict)
        or "contractDocument" not in schema["$defs"]
    ):
        errors.append(f"{label} contract document schema: contract $defs are unavailable")
        return
    wrapper = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": schema["$defs"],
        "$ref": "#/$defs/contractDocument",
    }
    try:
        validator = Draft202012Validator(wrapper)
        validation_errors = sorted(
            validator.iter_errors(document),
            key=lambda item: tuple(str(part) for part in item.path),
        )
    except Exception as error:
        errors.append(f"{label} contract document schema: evaluation failed closed: {error}")
        return
    for error in validation_errors:
        location = "/".join(str(part) for part in error.path) or "$"
        errors.append(
            f"{label} contract document schema: instance violation at "
            f"{location}: {error.message}"
        )


def _version_errors(label: str, value: Mapping[str, object]) -> list[str]:
    expected = {
        "framework_version": "v8.2",
        "framework_revision": FRAMEWORK_REVISION,
        "raw_sha256": RAW_SHA256,
        "semantic_sha256": SEMANTIC_SHA256,
    }
    return [
        f"{label}: {key} mismatch"
        for key, expected_value in expected.items()
        if value.get(key) != expected_value
    ]


def _source_records_from_snapshot(
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
    errors: list[str],
) -> dict[str, str]:
    records: dict[str, str] = {}
    for paragraph in paragraphs:
        anchor = paragraph.get("anchor")
        text_value = paragraph.get("text")
        if isinstance(anchor, str) and isinstance(text_value, str):
            if anchor in records:
                errors.append(f"source authority: duplicate anchor {anchor}")
            records[anchor] = text_value
    for table in tables:
        anchor = table.get("anchor")
        rows = table.get("rows")
        if isinstance(anchor, str) and isinstance(rows, list):
            if anchor in records:
                errors.append(f"source authority: duplicate anchor {anchor}")
            records[anchor] = "\n".join(
                " | ".join(str(cell) for cell in row)
                for row in rows
                if isinstance(row, list)
            )
    return records


def _validated_source_snapshot(
    source_checker: object,
    repo: Path,
    errors: list[str],
) -> tuple[Mapping[str, object] | None, dict[str, str]]:
    try:
        public_api = getattr(source_checker, "validate_committed_source_snapshot", None)
        if not callable(public_api):
            raise RuntimeError("validated committed source snapshot API is unavailable")
        # The source checker is a frozen dynamic module.  Keep its public call
        # under the same import isolation used during exec so lazy stdlib
        # imports cannot resolve a repository-local shadow module.
        with _ImportIsolation(repo):
            snapshot = public_api(repo)
        source_errors = list(getattr(snapshot, "errors", ()))
        manifest = getattr(snapshot, "manifest", None)
        paragraphs = getattr(snapshot, "paragraphs", ())
        tables = getattr(snapshot, "tables", ())
    except Exception as error:
        errors.append(f"source authority checker failed: {error}")
        return None, {}
    errors.extend(f"source authority: {error}" for error in source_errors)
    if not isinstance(manifest, Mapping):
        errors.append("source authority: validated source manifest is unavailable")
        return None, {}
    if not isinstance(paragraphs, Sequence) or not isinstance(tables, Sequence):
        errors.append("source authority: validated source records are unavailable")
        return manifest, {}
    thawed_manifest = _thaw_json(manifest)
    thawed_paragraphs = _thaw_json(paragraphs)
    thawed_tables = _thaw_json(tables)
    if (
        not isinstance(thawed_manifest, dict)
        or not isinstance(thawed_paragraphs, list)
        or not isinstance(thawed_tables, list)
    ):
        errors.append("source authority: frozen source snapshot cannot be materialized")
        return None, {}
    return thawed_manifest, _source_records_from_snapshot(
        thawed_paragraphs,
        thawed_tables,
        errors,
    )


def _string_list(
    value: object,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{label}: must be a string array")
        return []
    if not allow_empty and not value:
        errors.append(f"{label}: must not be empty")
    if len(value) != len(set(value)):
        errors.append(f"{label}: contains duplicates")
    return list(value)


def _validate_anchors(
    anchors: object,
    label: str,
    source_records: Mapping[str, str],
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    values = _string_list(anchors, f"{label} source anchors", errors, allow_empty=allow_empty)
    for anchor in values:
        if ANCHOR_RE.fullmatch(anchor) is None:
            errors.append(f"{label}: invalid v8.2 source anchor {anchor}")
        elif anchor not in source_records:
            errors.append(f"{label}: missing source anchor {anchor}")
    return values


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _normalized_exact_in_source(value: str, source_texts: Sequence[str]) -> bool:
    normalized = _normalize_text(value)
    if not normalized:
        return False
    return any(normalized in _normalize_text(source) for source in source_texts)


def _semantic_units(statement: str) -> list[str]:
    units: list[str] = []
    for part in SEMANTIC_UNIT_SPLIT_RE.split(statement):
        candidate = SEMANTIC_CONNECTOR_RE.sub("", part.strip()).strip()
        if _normalize_text(candidate):
            units.append(candidate)
    return units


def _semantic_unit_supported(unit: str, source_texts: Sequence[str]) -> bool:
    normalized = _normalize_text(unit)
    normalized_sources = [_normalize_text(text) for text in source_texts]
    if not normalized or not normalized_sources:
        return False
    if any(normalized in source for source in normalized_sources):
        return True
    required = CURATED_SEMANTIC_EVIDENCE.get(normalized)
    return bool(required) and all(
        any(
            _normalize_text(marker) in source
            for source in normalized_sources
        )
        for marker in required
    )


def _unsupported_semantic_units(
    statement: str,
    source_texts: Sequence[str],
) -> list[str]:
    units = _semantic_units(statement)
    if not units:
        return [statement]
    return [
        unit for unit in units if not _semantic_unit_supported(unit, source_texts)
    ]


def _definition_supported(
    definition: str,
    canonical_name: str,
    source_texts: Sequence[str],
) -> bool:
    candidate = definition
    for prefix in (canonical_name + "的", canonical_name + "是", canonical_name):
        if candidate.startswith(prefix):
            candidate = candidate[len(prefix) :]
            break
    return not _unsupported_semantic_units(candidate, source_texts)


def _validate_concepts(
    registry: Mapping[str, object],
    source_records: Mapping[str, str],
    errors: list[str],
) -> dict[str, Mapping[str, object]]:
    errors.extend(_version_errors("concept registry", registry))
    if registry.get("canonical_namespace") != "V82-":
        errors.append("concept registry: canonical namespace must be V82-")
    if registry.get("provisional_namespace") != "ULTRA-PROV-":
        errors.append("concept registry: provisional namespace must be ULTRA-PROV-")
    concepts = registry.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append("concept registry: concepts must be a non-empty list")
        return {}
    if registry.get("concept_count") != len(concepts):
        errors.append("concept registry: concept_count mismatch")
    result: dict[str, Mapping[str, object]] = {}
    canonical_names: set[str] = set()
    for index, concept in enumerate(concepts):
        label = f"concept[{index}]"
        if not isinstance(concept, dict):
            errors.append(f"{label}: record must be an object")
            continue
        if set(concept) != CONCEPT_FIELDS:
            errors.append(f"{label}: fields are not closed")
        concept_id = concept.get("concept_id")
        canonical_zh = concept.get("canonical_zh")
        if not isinstance(concept_id, str) or CONCEPT_ID_RE.fullmatch(concept_id) is None:
            errors.append(f"{label}: canonical concept ID is outside V82 namespace")
            continue
        if concept_id.startswith("ULTRA-PROV-"):
            errors.append(f"{label}: provisional ID entered canonical registry")
        if concept_id in result:
            errors.append(f"concept registry: duplicate concept ID {concept_id}")
        result[concept_id] = concept
        if not isinstance(canonical_zh, str) or not canonical_zh.strip():
            errors.append(f"{concept_id}: canonical_zh is empty")
        canonical_key = _normalize_text(canonical_zh) if isinstance(canonical_zh, str) else ""
        if canonical_key and canonical_key in canonical_names:
            errors.append(f"concept registry: duplicate canonical Chinese name {canonical_zh}")
        elif canonical_key:
            canonical_names.add(canonical_key)
        anchors = _validate_anchors(
            concept.get("source_anchors"), concept_id, source_records, errors
        )
        source_texts = [source_records[anchor] for anchor in anchors if anchor in source_records]
        definition = concept.get("definition")
        if (
            not isinstance(definition, str)
            or not isinstance(canonical_zh, str)
            or not _definition_supported(definition, canonical_zh, source_texts)
        ):
            errors.append(f"{concept_id}: definition is unsupported by source anchor text")
        if isinstance(canonical_zh, str) and source_texts:
            if not _normalized_exact_in_source(canonical_zh, source_texts):
                errors.append(f"{concept_id}: canonical Chinese name is unsupported by source anchors")
        for field in (
            "prerequisites",
            "required_neighbors",
            "conflicts",
        ):
            _string_list(concept.get(field), f"{concept_id} {field}", errors)
        for field in (
            "allowed_inferences",
            "forbidden_substitutions",
            "common_misuses",
            "disambiguation_conditions",
            "evidence_requirements",
            "counterexamples",
            "withdrawal_conditions",
        ):
            statements = _string_list(
                concept.get(field),
                f"{concept_id} {field}",
                errors,
            )
            for statement_index, statement in enumerate(statements):
                unsupported = _unsupported_semantic_units(statement, source_texts)
                if unsupported:
                    errors.append(
                        f"{concept_id} {field}[{statement_index}]: unsupported by "
                        f"source anchor text: {unsupported}"
                    )
        interfaces = _string_list(
            concept.get("inference_interfaces"),
            f"{concept_id} inference_interfaces",
            errors,
        )
        for interface in interfaces:
            if interface not in ALLOWED_INFERENCE_INTERFACES:
                errors.append(
                    f"{concept_id} inference_interfaces: unsupported interface token {interface}"
                )
        action_ceiling = concept.get("action_ceiling")
        if not isinstance(action_ceiling, str) or not action_ceiling:
            errors.append(f"{concept_id}: action_ceiling is empty")
        else:
            unsupported = _unsupported_semantic_units(action_ceiling, source_texts)
            if unsupported:
                errors.append(
                    f"{concept_id} action_ceiling: unsupported by source anchor text: "
                    f"{unsupported}"
                )
    concept_ids = set(result)
    for concept_id, concept in result.items():
        for field in ("prerequisites", "required_neighbors", "conflicts"):
            values = concept.get(field, [])
            if not isinstance(values, list):
                continue
            for target in values:
                if target not in concept_ids:
                    errors.append(f"{concept_id}: dangling {field} reference {target}")
        for target in concept.get("required_neighbors", []):
            if target in result and concept_id not in result[target].get("required_neighbors", []):
                errors.append(f"{concept_id}: missing neighbor backlink from {target}")
        for target in concept.get("conflicts", []):
            if target in result and concept_id not in result[target].get("conflicts", []):
                errors.append(f"{concept_id}: missing conflict backlink from {target}")
    return result


def _validate_contracts(
    contract_map: Mapping[str, object],
    contract_documents: Mapping[str, tuple[bytes, object]],
    contract_schema: object,
    concepts: Mapping[str, Mapping[str, object]],
    source_records: Mapping[str, str],
    errors: list[str],
) -> tuple[set[str], dict[str, set[str]]]:
    errors.extend(_version_errors("contract map", contract_map))
    entries = contract_map.get("contracts")
    if not isinstance(entries, list):
        errors.append("contract map: contracts must be a list")
        return set(), {}
    if contract_map.get("contract_count") != len(entries):
        errors.append("contract map: contract_count mismatch")
    found_files: set[str] = set()
    contract_ids: set[str] = set()
    contract_concepts: dict[str, set[str]] = {}
    covered_concepts: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"contract map entry[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: must be an object")
            continue
        if set(entry) != CONTRACT_ENTRY_FIELDS:
            errors.append(f"{label}: fields are not closed")
        contract_id = entry.get("contract_id")
        file_name = entry.get("file")
        if not isinstance(contract_id, str) or CONTRACT_ID_RE.fullmatch(contract_id) is None:
            errors.append(f"{label}: invalid contract ID")
            continue
        if contract_id in contract_ids:
            errors.append(f"contract map: duplicate contract ID {contract_id}")
        contract_ids.add(contract_id)
        if not isinstance(file_name, str) or file_name not in CONTRACT_FILES:
            errors.append(f"{contract_id}: unexpected contract file {file_name}")
            continue
        if file_name in found_files:
            errors.append(f"contract map: duplicate contract file {file_name}")
        found_files.add(file_name)
        captured = contract_documents.get(file_name)
        if captured is None:
            errors.append(f"{contract_id}: contract file is absent from the authority snapshot")
            continue
        file_bytes, document = captured
        actual_hash = sha256(file_bytes).hexdigest()
        if entry.get("file_sha256") != actual_hash:
            errors.append(f"{contract_id}: contract file hash mismatch")
        if actual_hash != EXPECTED_CONTRACT_HASHES[file_name]:
            errors.append(f"{contract_id}: fixed contract hash mismatch")
        _validate_contract_document_schema(
            contract_schema,
            document,
            contract_id,
            errors,
        )
        if not isinstance(document, dict):
            continue
        if set(document) != CONTRACT_DOCUMENT_FIELDS:
            errors.append(f"{contract_id}: contract document fields are not closed")
        errors.extend(_version_errors(contract_id, document))
        if document.get("contract_id") != contract_id:
            errors.append(f"{contract_id}: contract document ID mismatch")
        entry_concepts = _string_list(
            entry.get("concept_ids"), f"{contract_id} map concept IDs", errors
        )
        document_concepts = _string_list(
            document.get("concept_ids"), f"{contract_id} document concept IDs", errors
        )
        if entry_concepts != document_concepts:
            errors.append(f"{contract_id}: concept backlinks differ between map and document")
        contract_concepts[contract_id] = set(entry_concepts)
        for concept_id in entry_concepts:
            if concept_id not in concepts:
                errors.append(f"{contract_id}: dangling contract concept reference {concept_id}")
            covered_concepts.add(concept_id)
        map_anchors = _validate_anchors(
            entry.get("source_anchors"), f"{contract_id} map", source_records, errors
        )
        document_anchors = _validate_anchors(
            document.get("source_anchors"), f"{contract_id} document", source_records, errors
        )
        if map_anchors != document_anchors:
            errors.append(f"{contract_id}: source anchor backlinks differ between map and document")
        responsibility = document.get("responsibility")
        responsibility_sources = [
            source_records[anchor]
            for anchor in document_anchors
            if anchor in source_records
        ]
        if not isinstance(responsibility, str):
            errors.append(f"{contract_id}: responsibility must be a string")
        else:
            unsupported = _unsupported_semantic_units(
                responsibility,
                responsibility_sources,
            )
            if unsupported:
                errors.append(
                    f"{contract_id}: responsibility is unsupported by source anchor text: "
                    f"{unsupported}"
                )
        clauses = document.get("clauses")
        if not isinstance(clauses, list) or not clauses:
            errors.append(f"{contract_id}: clauses must be a non-empty list")
            continue
        clause_ids: set[str] = set()
        for clause_index, clause in enumerate(clauses):
            clause_label = f"{contract_id} clause[{clause_index}]"
            if not isinstance(clause, dict) or set(clause) != {
                "clause_id",
                "statement",
                "source_anchors",
            }:
                errors.append(f"{clause_label}: fields are not closed")
                continue
            clause_id = clause.get("clause_id")
            if not isinstance(clause_id, str) or re.fullmatch(
                r"V82-CLAUSE-[A-Z0-9]+(?:-[A-Z0-9]+)*", clause_id
            ) is None:
                errors.append(f"{clause_label}: invalid clause ID")
            elif clause_id in clause_ids:
                errors.append(f"{contract_id}: duplicate clause ID {clause_id}")
            else:
                clause_ids.add(clause_id)
            anchors = _validate_anchors(
                clause.get("source_anchors"), clause_label, source_records, errors
            )
            statement = clause.get("statement")
            source_texts = [source_records[a] for a in anchors if a in source_records]
            unsupported = (
                _unsupported_semantic_units(statement, source_texts)
                if isinstance(statement, str)
                else [str(statement)]
            )
            if unsupported:
                errors.append(f"{clause_label}: statement is unsupported by source anchor text")
    if found_files != CONTRACT_FILES:
        errors.append(
            "contract map: fixed contract file closure mismatch; "
            f"missing={sorted(CONTRACT_FILES - found_files)}, extra={sorted(found_files - CONTRACT_FILES)}"
        )
    missing_backlinks = set(concepts) - covered_concepts
    if missing_backlinks:
        errors.append(f"contract map: concepts missing contract backlinks: {sorted(missing_backlinks)}")
    return contract_ids, contract_concepts


def _validate_routes(
    route_map: Mapping[str, object],
    concepts: Mapping[str, Mapping[str, object]],
    contract_ids: set[str],
    contract_concepts: Mapping[str, set[str]],
    source_records: Mapping[str, str],
    errors: list[str],
) -> None:
    errors.extend(_version_errors("route map", route_map))
    routes = route_map.get("routes")
    if not isinstance(routes, list) or not routes:
        errors.append("route map: routes must be a non-empty list")
        return
    if route_map.get("route_count") != len(routes):
        errors.append("route map: route_count mismatch")
    seen_routes: set[str] = set()
    covered_concepts: set[str] = set()
    covered_contracts: set[str] = set()
    concept_route_counts: dict[str, int] = {concept_id: 0 for concept_id in concepts}
    for index, route in enumerate(routes):
        label = f"route[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{label}: record must be an object")
            continue
        if set(route) != ROUTE_FIELDS:
            errors.append(f"{label}: fields are not closed")
        route_id = route.get("route_id")
        if not isinstance(route_id, str) or ROUTE_ID_RE.fullmatch(route_id) is None:
            errors.append(f"{label}: invalid route ID")
            continue
        if route_id in seen_routes:
            errors.append(f"route map: duplicate route ID {route_id}")
        seen_routes.add(route_id)
        task = route.get("task")
        if not isinstance(task, str) or not task:
            errors.append(f"{route_id}: task is empty")
        anchors = _validate_anchors(
            route.get("source_anchors"), route_id, source_records, errors
        )
        task_sources = [
            source_records[anchor] for anchor in anchors if anchor in source_records
        ]
        unsupported = (
            _unsupported_semantic_units(task, task_sources)
            if isinstance(task, str)
            else [str(task)]
        )
        if unsupported:
            errors.append(f"{route_id}: route task is unsupported by source anchor text")
        route_concepts = _string_list(
            route.get("concept_ids"), f"{route_id} concept IDs", errors, allow_empty=False
        )
        route_contracts = _string_list(
            route.get("contract_ids"), f"{route_id} contract IDs", errors, allow_empty=False
        )
        for concept_id in route_concepts:
            if concept_id not in concepts:
                errors.append(f"{route_id}: dangling route concept reference {concept_id}")
            else:
                concept_route_counts[concept_id] += 1
            covered_concepts.add(concept_id)
        for contract_id in route_contracts:
            if contract_id not in contract_ids:
                errors.append(f"{route_id}: dangling route contract reference {contract_id}")
            covered_contracts.add(contract_id)
        valid_route_concepts = set(route_concepts) & set(concepts)
        expected_contracts = {
            contract_id
            for contract_id, supported_concepts in contract_concepts.items()
            if valid_route_concepts & supported_concepts
        }
        actual_contracts = set(route_contracts) & contract_ids
        if actual_contracts != expected_contracts:
            errors.append(
                f"{route_id}: concept-contract compatibility mismatch; "
                f"missing={sorted(expected_contracts - actual_contracts)}, "
                f"unrelated={sorted(actual_contracts - expected_contracts)}"
            )
    if covered_concepts != set(concepts):
        errors.append(
            "route map: concept closure mismatch; "
            f"missing={sorted(set(concepts) - covered_concepts)}, "
            f"extra={sorted(covered_concepts - set(concepts))}"
        )
    if covered_contracts != contract_ids:
        errors.append(
            "route map: contract closure mismatch; "
            f"missing={sorted(contract_ids - covered_contracts)}, "
            f"extra={sorted(covered_contracts - contract_ids)}"
        )
    invalid_partition = {
        concept_id: count
        for concept_id, count in concept_route_counts.items()
        if count != 1
    }
    if invalid_partition or len(routes) != len(concepts):
        errors.append(
            "route map: concept route partition mismatch; "
            f"route_count={len(routes)}, concept_count={len(concepts)}, "
            f"memberships={invalid_partition}"
        )


def _validate_isolation(
    snapshot: _KnowledgeSnapshot,
    paths: Sequence[Path],
    errors: list[str],
) -> None:
    for relative in paths:
        payload = snapshot.bytes(relative)
        if payload is None:
            errors.append(f"source isolation: authority snapshot is missing {relative.as_posix()}")
            continue
        try:
            text = payload.decode("utf-8")
        except UnicodeError as error:
            errors.append(f"source isolation: cannot inspect {relative}: {error}")
            continue
        label = relative.as_posix()
        if OLD_ANCHOR_RE.search(text):
            errors.append(f"source isolation: legacy V8-P/V8-T anchor in {label}")
        if LEGACY_V80_SHA256 in text:
            errors.append(f"source isolation: v8.0 source hash in {label}")
        lowered = text.casefold()
        for term in FORBIDDEN_SIBLING_TERMS:
            if term.casefold() in lowered:
                errors.append(f"source isolation: sibling theory reference {term} in {label}")


def _validate_frozen_authority_hashes(
    snapshot: _KnowledgeSnapshot,
    errors: list[str],
) -> None:
    for relative, expected in EXPECTED_AUTHORITY_HASHES.items():
        payload = snapshot.bytes(Path(relative))
        if payload is None:
            errors.append(f"frozen authority: snapshot is missing {relative}")
            continue
        actual = sha256(payload).hexdigest()
        if actual != expected:
            errors.append(
                f"frozen authority hash mismatch: {relative}: expected {expected}, got {actual}"
            )


def validate_knowledge(repo: Path) -> list[str]:
    """Validate schemas, evidence binding, graph closure, hashes and isolation."""
    errors: list[str] = []
    try:
        repo = _safe_repo(Path(repo))
        _assert_safe_path(repo / ULTRA_RELATIVE, repo)
    except ValueError as error:
        return [str(error)]
    snapshot = _capture_knowledge_snapshot(repo, errors)
    _validate_contract_directory_closure(repo, errors)
    _validate_frozen_authority_hashes(snapshot, errors)
    try:
        source_checker = _load_source_checker(repo)
        source_manifest, source_records = _validated_source_snapshot(
            source_checker,
            repo,
            errors,
        )
    except Exception as error:
        errors.append(f"source authority checker failed: {error}")
        source_manifest, source_records = None, {}

    schema_documents: dict[str, object] = {}
    for role, name in SCHEMA_FILES.items():
        schema_documents[role] = snapshot.json(SCHEMAS_RELATIVE / name)
    registry = snapshot.json(REGISTRY_RELATIVE)
    contract_map = snapshot.json(CONTRACT_MAP_RELATIVE)
    route_map = snapshot.json(ROUTE_MAP_RELATIVE)
    contract_documents: dict[str, tuple[bytes, object]] = {}
    for name in sorted(CONTRACT_FILES):
        relative = REFERENCES_RELATIVE / "concept-contracts" / name
        payload = snapshot.bytes(relative)
        document = snapshot.json(relative)
        if payload is not None:
            contract_documents[name] = (payload, document)

    isolation_paths = [
        REGISTRY_RELATIVE,
        REGISTRY_INDEX_RELATIVE,
        CONTRACT_MAP_RELATIVE,
        ROUTE_MAP_RELATIVE,
        *(
            REFERENCES_RELATIVE / "concept-contracts" / name
            for name in sorted(CONTRACT_FILES)
        ),
        *(SCHEMAS_RELATIVE / name for name in SCHEMA_FILES.values()),
    ]
    _validate_isolation(snapshot, isolation_paths, errors)
    if not all(
        isinstance(item, Mapping)
        for item in (source_manifest, registry, contract_map, route_map)
    ):
        return _deduplicate(errors)

    assert isinstance(source_manifest, Mapping)
    assert isinstance(registry, Mapping)
    assert isinstance(contract_map, Mapping)
    assert isinstance(route_map, Mapping)
    _validate_schema(
        "source manifest schema",
        schema_documents["source"],
        _thaw_json(source_manifest),
        errors,
    )
    _validate_schema("concept registry schema", schema_documents["registry"], registry, errors)
    _validate_schema("contract map schema", schema_documents["contracts"], contract_map, errors)
    _validate_schema("route map schema", schema_documents["routes"], route_map, errors)
    concepts = _validate_concepts(registry, source_records, errors)
    contract_ids, contract_concepts = _validate_contracts(
        contract_map,
        contract_documents,
        schema_documents["contracts"],
        concepts,
        source_records,
        errors,
    )
    _validate_routes(
        route_map,
        concepts,
        contract_ids,
        contract_concepts,
        source_records,
        errors,
    )
    return _deduplicate(errors)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the closed CrossFrame Ultra v8.2 knowledge authority."
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        errors = validate_knowledge(args.repo)
    except Exception as error:
        errors = [f"knowledge checker failure: {error}"]
    result = {
        "valid": not errors,
        "framework_revision": FRAMEWORK_REVISION,
        "raw_sha256": RAW_SHA256,
        "semantic_sha256": SEMANTIC_SHA256,
        "errors": errors,
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif errors:
        print("CrossFrame Ultra v8.2 knowledge authority: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("CrossFrame Ultra v8.2 knowledge authority: OK")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
