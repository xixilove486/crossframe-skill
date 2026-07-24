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
- `stance_projection`：把 P8 锁定判断投影为自然正文。`relation_to_proposition`、`judgment_strength` 必须逐项复制 P8；`center_thesis_text`、`withdrawal_text`、`action_ceiling_text` 必须是将出现在正文中的完整自然句。建议被请求时，还须复制 `preferred_option_id/kind` 与 `second_option_id/kind`，并分别冻结含“首选/优先”与“次选/再决定”关系的 `preferred_option_text`、`second_option_text`；未请求时六个方案字段全部为 `null`。这些 ID 只留在内部计划，正文只出现自然句。
- `core_concept_ids`：正文会以权威中文名解释的核心概念，至少一项。
- `atlas_only_concept_ids`：只在 concept atlas 闭合、不在正文点名的 applied concepts。
- `core_concept_bindings`：与 `core_concept_ids` 一一对应。每项包含 `concept_id`、2–4 个 `reader_anchor_terms`、1–3 条 `source_support_spans`、0–3 条 `source_misuse_spans` 和一条 `reader_explanation`。support span 必须完整复制该概念的一条 v8 `definition` 或 `allowed_inferences`；misuse span 必须完整复制 registry 的具体误用边界；`reader_explanation` 是将逐字进入正文的自然解释句，必须包含权威中文名和全部锚词。锚词每项 2–24 个字符，不得用“结构、关系、条件、问题、当前、对象、概念、机制、状态、行动、证据”等通用词冒充概念语义。
- `selected_techniques`：三至五项；前 3 项必须按 `article_type` 路由的固定顺序列出三张 `tier=core`，随后可列 0–2 张 `tier=auxiliary`。auxiliary 只能从同一路由的 `auxiliary_candidates` 中选择。每项写明唯一 `technique_id`、实际 `paragraph_action` 和承载它的 `section_ids`。
- `reader_beats`：按信息依赖排列的读者段落任务。每项写明唯一 `beat_id`、自然语言 `function`、一个或两个 `action_ids`，以及真实 `section_ids`、`claim_ids`、`mechanism_ids`、`evidence_refs`、`core_concept_ids`、`technique_ids`。每个 beat 至少携带一项 claim；同一 beat 内的 mechanism 和 evidence 必须能回到该 beat 的 claim。

`core_concept_ids` 与 `atlas_only_concept_ids` 必须互斥，二者并集必须精确等于 P4 的 applied concepts；`core_concept_bindings` 的 concept IDs 必须精确等于 `core_concept_ids`。所有 beat 与 technique 引用必须来自当前 P4/P5/P9 集合；全部核心概念、已选技法、计划机制和 claim-bound evidence 必须由 beats 闭合，`thesis_claim_id` 必须被至少一个 beat 承载。技法是段落动作，不是正文中要展示的标签。

九种 `article_type` 的固定 core 顺序和 `auxiliary_candidates` 以 `references/prose-routing-map.md` 为准；schema 与 runtime 会拒绝未知技法、错体裁 core、乱序 core 和路由外 auxiliary。

`reader_beats[].action_ids` 展开后必须恰好得到以下八个动作，每个动作出现一次且顺序不可改变：

1. `reality_entry`：现实入口；
2. `center_thesis`：中心命题；
3. `mechanism_progression`：机制递进；
4. `same_dimension_comparison`：同维正反比较；
5. `strongest_counterposition`：最强反方；
6. `explicit_position`：明确立场；
7. `withdrawal_action_boundary`：撤回条件与行动边界；
8. `resonant_close`：余味结尾。

一个 beat 只能承载一个动作，或合并这条序列中相邻的两个动作；不得跨动作合并、倒序、重复、漏项，也不得用含混的 `function` 替代 `action_ids`。

## 双向覆盖

1. 所有 sections 的 `concept_ids` 并集必须与 P4 的 applied 集合完全相等；每个 applied concept 的 `output_section_ids` 反向等于包含它的 SECTION IDs。
2. 所有 `claim_ids` 并集必须与 claim graph 的全部 claim IDs 完全相等。
3. `example_ids` 与 case artifact 的 `relation=similar` IDs 完全相等；每个机制至少两个。
4. `counterexample_ids` 与 case artifact 的 `relation=failure` IDs 完全相等；每个机制至少一个。
5. 建议被请求时，全部 sections 中的 `judgment_ids` 总计且仅出现 `POSITION-LOCK`、`RECOMMENDATION-LOCK` 各一次；未请求时只出现 `POSITION-LOCK` 一次。

## 必需产物与未展开分支

`required_artifacts` 必须且只能包含以下四份公开语义交付：

- `promax-dossier.md`
- `promax-concept-atlas.md`
- `promax-case-and-countercase.md`
- `promax-essay.md`

`promax-prose-review.json` 是 P10 内部审校工件，不进入 `required_artifacts` 或最终公开 `artifact_links`。

严格完成时 `coverage_complete=true` 且 `unexpanded_branch_ids=[]`。若 artifact run 因容量保留未展开分支，设置 `coverage_complete=false`，逐项登记稳定 branch ID，并写入 continuation。

## 封存前检查

先执行 schema 与 reader projection 语义校验，再锁定当前对象、概念、claims、机制、证据、体裁、reader beats 和技法。P10 只能忠实转译这个 plan；若正文结构或核心映射错误，回到 P9 重写并重新锁定。
