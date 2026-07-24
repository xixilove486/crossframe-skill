# Output plan 生成合同

产物：`promax-output-plan.locked.json`
生成阶段：`P9`
Schema：`promax-output-plan.schema.json`

`schema_id` 固定为 `crossframe.promax.v8.output-plan`，`schema_version=1`。根对象只包含 `schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`sections`、`required_artifacts`、`unexpanded_branch_ids`、`coverage_complete`、`locked_at`。

## 每个 section

`sections[]` 至少一项，每条只含：

- `section_id`：唯一 `SECTION-*`。
- `title`：最终交付中可识别的中文章节标题。
- `concept_ids`：本节负责解释的 applied canonical concepts。
- `claim_ids`：本节负责表达的 claim graph claims。
- `example_ids`：本节负责交付的 similar case IDs。
- `counterexample_ids`：本节负责交付的 failure case IDs。
- `judgment_ids`：本节负责的 position/recommendation locks。
- `artifact_paths`：承载本节的现有长文路径，至少一项。

`artifact_paths` 只能指向当前四份语义交付：`promax-dossier.md`、`promax-concept-atlas.md`、`promax-case-and-countercase.md`、`promax-essay.md`。不能把 control-plane 文件当作正文承载位置。

## 双向覆盖

1. 所有 sections 的 `concept_ids` 并集必须与 P4 的 `status=applied` 集合完全相等；每个 applied concept 的 `output_section_ids` 必须反向等于包含它的 SECTION IDs。
2. 所有 `claim_ids` 并集必须与 claim graph 的全部 claim IDs 完全相等。
3. `example_ids` 与 case artifact 的 `relation=similar` IDs 完全相等；每个机制至少两个。
4. `counterexample_ids` 与 case artifact 的 `relation=failure` IDs 完全相等；每个机制至少一个。
5. 建议被请求时，全部 sections 中的 `judgment_ids` 总计且仅出现 `POSITION-LOCK`、`RECOMMENDATION-LOCK` 各一次；未请求时只出现 `POSITION-LOCK` 一次。

## 必需产物与未展开分支

`required_artifacts` 至少包含且通常精确使用四份语义交付路径：

- `promax-dossier.md`
- `promax-concept-atlas.md`
- `promax-case-and-countercase.md`
- `promax-essay.md`

严格完成时 `coverage_complete=true` 且 `unexpanded_branch_ids=[]`。若 artifact run 因容量保留未展开分支，`coverage_complete=false`，逐项登记稳定 branch ID，并把后续交付写入 continuation；不得把“未展开”当作省略理由。

## 封存前检查

确认所有 ID 与上游工件精确匹配，章节均有实际承载路径，建议意图闭合。schema 通过后锁定；P10 的文字与 manifest 必须反向证明本 plan，而不能在写作时自行改 plan。
