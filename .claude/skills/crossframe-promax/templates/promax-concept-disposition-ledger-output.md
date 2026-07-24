# Concept disposition ledger 生成合同

产物：`promax-concept-disposition-ledger.json`
生成阶段：`P4`
Schema：`promax-concept-disposition.schema.json`

该 ledger 必须对当前 registry 的全部 709 个 canonical concepts 给出终态，不能只登记命中的术语。`schema_id` 固定为 `crossframe.promax.v8.concept-disposition`，`schema_version=1`；run、snapshot 与 `registry_sha256` 必须绑定当前已验证资产。

## 根字段

`schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`registry_sha256`、`route_ids`、`dispositions`、`unchecked_concept_ids`、`closure_complete`、`completed_at` 全部必填。

- `route_ids`：精确登记本轮 required route IDs；每个 ID 使用 `V8-ROUTE-##-*`，不得自造 route。
- `dispositions`：与 registry concept IDs 一一对应，数量和集合完全相等。
- `unchecked_concept_ids`：闭包完成时必须为 `[]`。
- `closure_complete`：只有 registry、route-required 与 neighbor closure 全部完成时才能为 `true`。

## 每条 disposition

每条记录只能包含：`concept_id`、`status`、`rationale`、`evidence_refs`、`required_neighbor_ids`、`misuses_excluded`、`output_section_ids`、`pending_evidence`。

`status` 只能取：

- `applied`：前提成立，按权威定义实际参与解释；`evidence_refs` 非空，`output_section_ids` 必须指向后续 locked output plan。
- `tested_rejected`：已检验但前提不成立；`evidence_refs` 非空，理由必须说明拒绝测试。
- `not_applicable`：对象或尺度条件使其不适用；理由必须给出结构化排除条件。
- `unknown_pending`：概念相关但关键条件未知；`pending_evidence` 至少一项，并进入条件分支和补证计划。

## 精确闭包

1. `required_neighbor_ids` 必须逐项、同序复制 registry 记录，不可仅写本轮认为重要的邻接概念。
2. `misuses_excluded` 必须同序合并 registry 的 `common_misuses` 与 `forbidden_substitutions_or_generalizations`，去重但不改写原文。
3. 每个 required route 的 `required_concept_ids` 与 `neighbor_closure_ids` 都必须在 dispositions 中有终态。
4. `rationale` 必须使用该概念的 v8 精确定义解释其当前作用或排除理由，不能以常识同名词替换。
5. 每个 `applied` 的 `output_section_ids` 先使用稳定 SECTION ID；P9 必须反向生成完全相同的章节集合。
6. provisional 变量不得使用 `V8-CANON-*` 命名，也不得混入 canonical concept inventory。

## 封存前检查

用 schema 校验，再执行 `validate_concept_closure()`。只有 concept ID 集合相等、全终态、route/neighbor 闭合、误用边界精确且未检查集合为空时，才可写入 P4 phase event。
