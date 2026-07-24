# Output plan 生成合同

产物：`promax-output-plan.locked.json`
生成阶段：`P9`
Schema：`promax-output-plan.schema.json`

`schema_id` 固定为 `crossframe.promax.v8.output-plan`，`schema_version=2`。根对象只包含 `schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`sections`、`reader_projection`、`required_artifacts`、`unexpanded_branch_ids`、`coverage_complete`、`locked_at`。

## 每个 section

`sections[]` 至少一项。每项使用唯一 `section_id`，并登记：

- `title`：读者可辨认的中文章节标题。
- `concept_ids`：本节负责解释的 applied canonical concepts。
- `claim_ids`：本节负责转译的 claim graph claims。
- `mechanism_ids`、`path_node_ids`：本节实际展开的机制与路径节点；无对应项时可省略。
- `example_ids`、`counterexample_ids`：本节负责交付的相似案例与失效反例。
- `judgment_ids`：本节承载的 position/recommendation locks。
- `artifact_paths`：承载本节语义的公开长文路径，至少一项。

`artifact_paths` 只能指向 `promax-dossier.md`、`promax-concept-atlas.md`、`promax-case-and-countercase.md`、`promax-essay.md`。内部审校、control-plane 文件和 manifest 不能冒充正文承载位置。

## reader_projection

`reader_projection` 是从机器锁到读者文章的冻结投影，必须由模型在 P9 写出，且只包含：

- `article_type`：从 schema 允许的文章类型中选择一种。
- `house_voice_id`：固定为 `crossframe-promax`。
- `thesis_claim_id`：正文中心命题对应的现有 claim ID。
- `core_concept_ids`：正文会以权威中文名解释的核心概念，至少一项。
- `atlas_only_concept_ids`：只在 concept atlas 闭合、不在正文点名的 applied concepts。
- `selected_techniques`：三至五项；前 3 项必须按 `article_type` 路由的固定顺序列出三张 `tier=core`，随后可列 0–2 张 `tier=auxiliary`。auxiliary 只能从同一路由的 `auxiliary_candidates` 中选择。每项写明唯一 `technique_id`、实际 `paragraph_action` 和承载它的 `section_ids`。
- `reader_beats`：按信息依赖排列的读者段落任务。每项写明唯一 `beat_id`、自然语言 `function`，以及真实 `section_ids`、`claim_ids`、`mechanism_ids`、`evidence_refs`、`core_concept_ids`、`technique_ids`。

`core_concept_ids` 与 `atlas_only_concept_ids` 必须互斥，二者并集必须精确等于 P4 的 applied concepts。所有 beat 与 technique 引用必须来自当前 P4/P5/P9 集合；`thesis_claim_id` 必须被至少一个 beat 承载。技法是段落动作，不是正文中要展示的标签。

九种 `article_type` 的固定 core 顺序和 `auxiliary_candidates` 以 `references/prose-routing-map.md` 为准；schema 与 runtime 会拒绝未知技法、错体裁 core、乱序 core 和路由外 auxiliary。

reader beats 至少覆盖：现实入口、中心命题、机制依赖、证据或案例、同维正反比较、最强反方、明确立场、撤回条件、行动边界和有余味的结尾。可以合并相邻功能，但不能用一个含混 beat 代替全部依赖。

## 双向覆盖

1. 所有 sections 的 `concept_ids` 并集必须与 P4 的 applied 集合完全相等；每个 applied concept 的 `output_section_ids` 反向等于包含它的 SECTION IDs。
2. 所有 `claim_ids` 并集必须与 claim graph 的全部 claim IDs 完全相等。
3. `example_ids` 与 case artifact 的 `relation=similar` IDs 完全相等；每个机制至少两个。
4. `counterexample_ids` 与 case artifact 的 `relation=failure` IDs 完全相等；每个机制至少一个。
5. 建议被请求时，全部 sections 中的 `judgment_ids` 总计且仅出现 `POSITION-LOCK`、`RECOMMENDATION-LOCK` 各一次；未请求时只出现 `POSITION-LOCK` 一次。

## 必需产物与未展开分支

`required_artifacts` 至少包含且通常精确使用四份公开语义交付：

- `promax-dossier.md`
- `promax-concept-atlas.md`
- `promax-case-and-countercase.md`
- `promax-essay.md`

`promax-prose-review.json` 是 P10 内部审校工件，不进入 `required_artifacts` 或最终公开 `artifact_links`。

严格完成时 `coverage_complete=true` 且 `unexpanded_branch_ids=[]`。若 artifact run 因容量保留未展开分支，设置 `coverage_complete=false`，逐项登记稳定 branch ID，并写入 continuation。

## 封存前检查

先执行 schema 与 reader projection 语义校验，再锁定当前对象、概念、claims、机制、证据、体裁、reader beats 和技法。P10 只能忠实转译这个 plan；若正文结构或核心映射错误，回到 P9 重写并重新锁定。
