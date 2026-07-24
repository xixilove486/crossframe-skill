# Red-team report 生成合同

产物：`promax-red-team-report.json`
生成阶段：`P7`
Schema：`promax-red-team-report.schema.json`

`schema_id` 固定为 `crossframe.promax.v8.red-team-report`，`schema_version=1`。根对象只包含 `schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`central_claim_id`、`attacks`、`stability_checks`、`revision_summary`、`completed_at`。

## 攻击集合

对中心 claim、对象边界、机制、路径、预测和建议前提进行最强攻击。至少实质检验下列十二个 `attack_class`，不可用同一句泛化质疑批量填充：

1. `object_reification`
2. `boundary_error`
3. `scale_transformation_error`
4. `personality_overinference`
5. `circle_reification`
6. `stage_model_misuse`
7. `baseline_leakage`
8. `path_storytelling`
9. `uncalibrated_probability`
10. `prediction_authorization_leakage`
11. `inaction_zero_cost`
12. `decision_irrelevant_counterexample`

## 每条 `attacks[]`

闭合字段为 `attack_id`、`attack_class`、`target_id`、`challenge`、`counterevidence_refs`、`strongest_counterposition`、`result`、`revision`、`position_impact`。

- `attack_id` 使用唯一 `ATTACK-*`；`target_id` 必须能回到 claim、机制、路径、对象或建议前提。
- `challenge` 提出能改变判断的具体攻击，不写表演性反对。
- `strongest_counterposition` 以完整命题表达最强反方；后续 position 必须逐字携带最高影响攻击的反方核心。
- `result` 只能是 `survived`、`survived_with_revision`、`rejected`、`unresolved`。
- `revision` 即使结果为 survived 也要说明保留理由或边界；`survived_with_revision` 的修正必须进入 position 的理由或撤回条件。
- `position_impact` 只能是 `none`、`low`、`medium`、`high`、`decisive`。

`revision_summary` 逐项汇总真正改变 claim、概念状态、强度、路径排序或行动上限的修正，并记录 red-team 连续两轮无实质新增的结果；不得用“已完成攻击”代替内容。

## 成对立场稳定性

每条 `stability_checks[]` 闭合字段为：`prompt_pair_id`、`pro_prompt`、`anti_prompt`、`pro_prompt_sha256`、`anti_prompt_sha256`、`evidence_basis_sha256_before`、`evidence_basis_sha256_after`、`semantic_problem_sha256_before`、`semantic_problem_sha256_after`、`central_position_id_before`、`central_position_id_after`、`central_statement_sha256_before`、`central_statement_sha256_after`、`relation_to_proposition_before`、`relation_to_proposition_after`、`judgment_strength_before`、`judgment_strength_after`、`option_ranking_before`、`option_ranking_after`、`option_kind_ranking_before`、`option_kind_ranking_after`、`option_semantic_ranking_before`、`option_semantic_ranking_after`、`normative_selection_basis_sha256_before`、`normative_selection_basis_sha256_after`、`position_drift`、`explanation`。

- `PROMAX-STANCE-NEUTRAL-KEY`：正反诱导必须复用由对象、待检验命题和时间窗组成的语义问题键；证据截止点独立冻结。中心 ID 只在本轮稳定；语义键、中心 statement 散列和命题关系共同防止同一标签下偷换相反结论。
- `prompt_pair_id` 使用唯一 `PAIR-*`。`pro_prompt` 与 `anti_prompt` 保存实际成对诱导文本；对应散列必须由规范 JSON 字符串重算且二者不同，禁止提交两个无来源的任意散列。
- `evidence_basis_sha256_before` 与 `evidence_basis_sha256_after` 都必须等于 checker 从实际 run contract、local-world model 与 retrieval ledger 重算的冻结证据基线，不能由报告自行声明。
- 判断强度只能是 `tentative`、`moderate`、`strong`、`indeterminate`。
- 无新证据时，问题键、position ID、中心语义、命题关系、判断强度、具体方案排序、行动类别投影、方案语义投影和规范选择基础必须前后一致，`position_drift=none`。
- `normative_selection_basis_sha256_before/after` 由 control plane 对 `selection_review_wrapper` 的 N 前提、价值冲突签名、PF、受影响/低权力位置计数、O1—O4、管辖审查边界、least-harm、proportionality、ranking policy 与 declared eligibility 重算；其中具体 option ID 替换为去 ID 的方案语义散列，运行时间与本轮标签不得污染跨运行比较。
- 成对探针不得改变证据；`position_drift` 只能是 `none`。新证据必须走检索写回、阶段重置和新的冻结状态。
- `central_position_id_after` 与 `judgment_strength_after` 必须成为 P8 locked position 的值。
- 若 run contract 不要求建议，前后 rankings 都必须为 `[]`；若要求建议，`option_ranking_after` 必须与 P8 recommendation 的完整 ranking 相等。
- `explanation` 必须说明证据与状态变化的对应关系，不得与登记状态矛盾。

`completed_at` 不得早于 claim graph 的 `updated_at`。封存后 P8 才能形成 position；不得让用户赞成或反对本身成为证据。
