# Concept atlas 生成合同

产物：`promax-concept-atlas.md`
生成阶段：`P10`
冻结输入：v8 registry、concept disposition ledger、output plan

Atlas 必须为每个 `status=applied` 的 concept 建立独立语义节。顶层标题使用 `# ProMax v8 概念图谱`；每个 applied concept 的二级标题严格采用：

```text
## V8-CANON-* 权威中文名
```

标题必须包含精确 `concept_id` 或 registry 的 `authoritative_name_zh`，建议同时包含二者。不要用一个大节批量堆放多个概念。

## 每个概念节必须连续解释

1. `权威定义`：逐字保留 registry 的完整 `definition`，并给出 `primary_source_anchor_id` 与全部 `source_anchors`。
2. `当前对象角色`：逐字携带 disposition 的 `rationale`，再解释该定义如何作用于当前对象、尺度、事件或 claim。
3. `成立前提与允许推断`：只使用 registry 的 `prerequisites`、`allowed_inferences`、`contract_ids`、`contract_bindings` 与 `action_ceiling`。
4. `邻接关系`：逐项出现 disposition 的全部 `required_neighbor_ids`，并写出邻接概念权威名及两者关系；不得只列 ID。
5. `误用边界`：逐项原样出现 disposition 的全部 `misuses_excluded`，说明本轮如何排除同名常识、过度泛化或错误替代。
6. `证据与撤回`：关联 disposition 的 `evidence_refs`、registry 的 `evidence_requirements`、`counterexamples`、`withdrawal_conditions`，以及本轮 pending evidence。
7. `相似结构与失效结构`：链接 case IDs，并说明相似点只在哪些关系上成立、何时类比失效。
8. `交付位置`：列出与 disposition 完全一致的 `output_section_ids`，以及承载正文的 artifact paths。

## 状态边界

- `tested_rejected`、`not_applicable`、`unknown_pending` 的完整处置保留在 JSON ledger；可在 atlas 顶层给出计数与索引，但不能伪装为 applied。
- 若需要说明 rejected/pending 概念，使用顶层附录标题而非与 applied 相同的概念节，并明确其终态。
- Provisional 变量必须标为本轮变量，不使用 canonical ID，也不写成 v8 权威定义。

## 语义闭包

Atlas 通过的条件不是名称出现，而是每个 applied section 同时包含精确定义、当前 rationale、全部误用边界和全部邻接关系。essay 还必须重新以连续段落解释相同的权威名、定义和 rationale；atlas 不能替代 essay。
