# Local world model 生成合同

产物：`promax-local-world-model.locked.json`
生成阶段：`P3`
Schema：`promax-local-world-model.schema.json`

按闭合 JSON 对象生成，不得增加字段。`schema_id` 固定为 `crossframe.promax.v8.local-world-model`，`schema_version` 固定为 `1`，`phase_id` 固定为 `P3`；`run_id` 与 `source_snapshot_sha256` 必须复制当前 run contract，`locked_at` 必须是带时区的 RFC 3339 时间。

## 根字段

`schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`phase_id`、`object_boundary`、`actor_records`、`circle_candidates`、`scale_profile`、`material_channel`、`experiential_meaning_channel`、`M_state`、`Psi_state`、`clocks`、`events`、`evidence_cutoff`、`unknowns`、`residuals`、`identity_criteria`、`action_limits`、`authorization_limits`、`locked_at` 全部必填。

## 嵌套记录

- `object_boundary`：`object_id` 使用 `OBJ-*`；同时写 `name`、非空 `in_scope`、非空 `out_of_scope`。边界必须能被后续证据推翻或重新冻结。
- `actor_records[]`：`actor_id` 使用 `ACTOR-*`；写 `label`、非空 `roles`、`observed_state`、`inferred_state`、非空 `inference_limits`。一次行为不得直接升级为稳定人格。
- `circle_candidates[]`：`circle_id` 使用 `CIRCLE-*`；写 `label`、`membership_basis`、`reification_risks`。候选可以为空数组，但每个已列候选都必须有可观察成员依据。
- `scale_profile`：写 `focal_scale`、非空 `included_scales`、`excluded_scales`、非空 `transformation_limits`；跨尺度结论必须说明变换条件。
- `material_channel` 与 `experiential_meaning_channel`：各写非空 `state`、`observables`、`unknowns`，不得互相替代。
- `M_state` 与 `Psi_state`：各写 `description`、`evidence_refs`、`uncertainties`；说明证据与推断的距离。
- `clocks[]`：`clock_id` 使用 `CLOCK-*`；写 `label`、`current_time`、ISO 8601 `horizon`、ISO 8601 `lag`。至少一条。
- `events[]`：`event_id` 使用 `EVENT-*`；`event_type` 只能是 `observed`、`reported`、`inferred`、`counterfactual`；另写 `time`、`description`、`evidence_refs`。
- `unknowns[]`：`unknown_id` 使用 `UNKNOWN-*`；写 `question`、`decision_impact`、`retrieval_plan`，把缺失材料转成可区分排序的补证任务。
- `residuals[]`：`residual_id` 使用 `RESIDUAL-*`；写不能被当前模型吸收的 `description` 与 `handling`。
- `identity_criteria[]`：至少一条，每条包含 `criterion` 与可执行 `test`。
- `action_limits`、`authorization_limits`：均为非空字符串数组，必须明确分析、预测与现实授权的边界。

## 封存前检查

1. 所有 ID 唯一，数组无重复项，字符串具有实质内容。
2. `evidence_cutoff` 不晚于 `locked_at`；事件和证据引用可追溯到冻结输入。
3. 已知事实、报告、推断、反事实和未知项没有混写。
4. 对象边界、尺度变换、圈层实体化、人格推断和授权风险都有显式限制。
5. 用 schema validator 校验后再写入 P3 phase event；不得手写父散列或事件散列。
