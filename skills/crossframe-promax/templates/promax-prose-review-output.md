# Prose review 生成合同

产物：`promax-prose-review.json`
生成阶段：`P10`
Schema：`promax-prose-review.schema.json`
生成角色：`prose_fidelity_auditor`

本工件是内部成文审校，不是第五份公开长文。角色必须先实际读取当前 `promax-essay.md`、`promax-position.locked.json` 与 `promax-output-plan.locked.json`，只生成 review，不改写任何输入。

## 根对象

根对象关闭字段，只包含：

- `schema_id`：`crossframe.promax.v8.prose-review`。
- `schema_version`：`1`。
- `run_id`、`source_snapshot_sha256`：绑定当前运行与冻结源。
- `essay_sha256`：当前 `promax-essay.md` 实际 UTF-8 字节的 SHA-256。
- `position_sha256`：当前 position 语义 JSON 的 canonical SHA-256。
- `output_plan_sha256`：当前 output plan 语义 JSON 的 canonical SHA-256。
- `article_type`：必须等于 `reader_projection.article_type`。
- `technique_ids`：顺序与 `reader_projection.selected_techniques` 完全一致。
- `required_beat_mappings`：逐项证明每个 reader beat 已在正文出现。
- `dimensions`：恰好十一项审校维度。
- `overall_status`：`pass` 或 `fail`，由十一维状态共同决定。
- `reviewed_at`：带时区的审校完成时间。

模型负责写 `article_type`、`technique_ids`、beat 映射、十一维证据、修复目标与总体状态。runtime 可以在字段缺失时注入 run/source 绑定、三个实际散列与 `reviewed_at`；模型若已写出冲突值，runtime 必须拒绝，不能覆盖冲突。

## required_beat_mappings

每个 P9 `reader_beats[]` 必须且只能映射一次。每项只含：

- `beat_id`：与 P9 完全相同。
- `section_ids`：集合与该 beat 的冻结 section IDs 完全相同。
- `evidence_excerpts`：至少一条正文逐字短摘。

正文逐字短摘必须真实存在于当前 essay，每条至少包含 8 个实质字符、最多 240 个字符，并且在正文中唯一出现。不得写总结、改写、占位词、可匹配多处的通用片段或不存在的理想句。映射覆盖全部 beats 后才能通过。

## 十一维审校

`dimensions` 必须恰好包含以下键：

1. `reality_entry`：文章是否从读者可识别的现实矛盾进入。
2. `argument_dependency`：段落是否沿主张、机制、证据与结论的依赖推进。
3. `v8_concept_fidelity`：核心概念是否使用权威中文名并保持定义边界。
4. `evidence_binding`：事实、案例和推断是否能回到当前证据。
5. `strongest_counterposition`：是否重建而非稻草化最强反方。
6. `fair_comparison`：正反解释是否使用同一比较维度。
7. `position_recommendation_consistency`：正文立场与 P8 position/recommendation 是否一致。
8. `withdrawal_action_boundary`：是否写清撤回条件、行动上限与授权边界。
9. `house_voice`：是否保持 CrossFrame ProMax 的耐心、明确、有限判断声口。
10. `model_flavor_independence`：正文是否摆脱特定模型的套话、标签堆砌与统一腔调。
11. `audit_leakage`：正文是否没有泄漏机器 ID、字段台账、运行脚手架或审校过程。

每维只含 `status`、`evidence_excerpts`、`repair_target`。`status=pass` 时至少给一条正文逐字短摘且 `repair_target=null`；`status=fail` 时可无摘录，但必须写非空修复目标，指向 P9 或 P10 的具体修复。

通过维度不能共用一条万能摘录。设通过维度数为 N，不同正文逐字短摘至少为 `ceil(2N/3)`；十一维全部通过时即至少 8 条。任一短摘最多复用于两个通过维度，不同通过维度的摘录集合不得完全相同。摘录还必须与所证明的维度直接相关。

runtime 会把每条摘录按所在句区归一化。不同通过维度的句区组合不得完全相同，任一句区最多支撑两个通过维度；十一维全部通过时至少需要 8 个不同句区组合。不能通过切出同一句的多个片段绕过摘录多样性要求。

只有十一维全部通过时 `overall_status=pass`。任一维失败则总体失败，按 `repair_target` 回修后重新生成 review，并重新绑定当前 essay、position 与 output plan 散列。
