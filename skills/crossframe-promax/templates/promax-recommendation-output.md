# Recommendation lock 生成合同

产物：`promax-recommendation.locked.json`
生成阶段：`P8`，在 position lock 之后
Schema：`promax-recommendation.schema.json`

先读取 run contract 的 `recommendation_required`，只能选择一个闭合分支。

## 未请求分支

当 `recommendation_required=false`，完整文件必须严格等于：

```json
{"status":"not_requested"}
```

不得增加 run binding、解释字段或方案。dossier 与 essay 也不得出现 `OPTION-*`、首选或推荐性语言。

## 必须建议分支

当 `recommendation_required=true`，根对象只包含：`schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`position_sha256`、`options`、`evaluation_dimensions`、`ranking`、`ranking_policy`、`ranking_evidence_refs`、`selection_review_wrapper`、`option_kind_ranking`、`option_record_hashes`、`option_semantic_ranking`、`preferred_option_id`、`second_option_id`、`no_action_option_id`、`switch_conditions`、`inaction_consequences`、`authorization_status`、`locked_at`。

- `schema_id` 固定为 `crossframe.promax.v8.recommendation`，`schema_version=1`。
- `position_sha256` 必须由当前 position 的规范 JSON 字节计算，不能手抄旧值。
- `locked_at` 必须严格晚于 position 的 `locked_at`。
- `evaluation_dimensions` 非空，至少覆盖结构解释力、风险、可逆性、时间、受影响位置与授权边界中实际相关维度。

## v8 方案记录

权威来源是 `references/concept-contracts/simulation-forecast-contracts.json#/option_record_schema`。每条 option 必须严格包含以下十九个字段，不得增加别名、摘要字段或 ProMax 自造字段：

1. `option_id`
2. `option_kind`
3. `description`
4. `forecast_refs`
5. `normative_premise_refs`
6. `affected_position_refs`
7. `rights_floor_refs`
8. `expected_paths`
9. `worst_acceptable_outcome`
10. `cross_circle_spillovers`
11. `distribution_of_costs_and_benefits`
12. `information_value`
13. `lock_in_risk`
14. `reversibility`
15. `resource_cost`
16. `authorized_actor_ref`
17. `authorization_record_ref`
18. `stop_conditions`
19. `rollback_and_remedy`

`option_kind` 必须来自 v8 的六类全集：`maintain_status_quo`、`active_action`、`delayed_action`、`probe_action`、`exit_or_transfer`、`no_action`。

- `option_id` 是本轮具体方案的稳定身份，不是 `option_kind` 的固定别名。动作、对象、地域、期限或其他冻结语义发生实质改变时，必须使用新 ID 或明确的新版本，禁止旧 ID 静默变形。
- 所有 `*_refs`、actor/ref 与 authorization/ref 必须解析到本轮真实记录。不得用装饰性字符串伪装语义闭包；缺少已授权主体或授权记录时，应登记可解析的 pending/unknown 记录，并保持建议有条件且待审。
- `expected_paths`、停止条件及 `rollback_and_remedy` 必须与相应预测路径、可观察信号和可恢复状态或不可逆边界相连。
- `worst_acceptable_outcome`、成本收益分配、跨圈层外溢、信息价值、锁定风险、可逆性与资源成本都必须逐方案实质填写，不能用同一段套话复制六次。

## ProMax 规范选择验证包装层

`selection_review_wrapper` 是 ProMax 为机器校验建立的闭合包装层，`wrapper_role` 必须逐字为 `promax_machine_verification_wrapper_not_v8_source_schema`。它不是 v8 原生 schema，也不得把 ProMax 字段冒充 v8 概念；其规范依据固定引用 `V8-P3561`、`V8-P3564`、`V8-P3569`—`V8-P3575`、`V8-P3580`—`V8-P3581`、`V8-P3584`、`V8-P3587`—`V8-P3589`、`V8-P3596`、`V8-P3598`—`V8-P3599`、`V8-P3601`—`V8-P3602`。

- `selection_type` 只能是 `SEL-AGT` 或 `SEL-GOV`；推荐分支禁止把 `SEL-SYS` 人格化为决策主体。`selection_status` 固定为 `under_review`。
- `public_value_premises` 必须登记唯一的 `N1` 否决门和至少一个 `N2`—`N5` 正向目标或约束。每个 option 的 `normative_premise_refs` 必须解析到这里，且全部实际使用前提必须闭合覆盖。
- `value_conflicts`、`unresolved_dissent_refs`、`rights_floor`、`affected_positions`、`low_power_position_ids` 分别冻结冲突、异议、PF-1—PF-10、所有受影响位置和低权力位置；不得用平均收益删除局部损害。
- `jurisdiction_review_boundary` 只登记首选方案的管辖审查边界，`boundary_role=promax_review_boundary_not_atomic_v8_j_tuple`。它必须绑定 `preferred_option_id`、方案 actor/ref 与 authorization/ref，但不能冒充 v8 完整原子 J 元组或现实授权；未知引用使用显式 unresolved 记录。
- `procedure_states` 必须完整登记 O1—O4；ProMax 分析输出中 O4 固定为 `not_started`。
- `least_harm` 与 `proportionality` 分别绑定 `NSP-LEAST-HARM` 和 `NSP-PROPORTIONALITY`，比较全部方案（含 `no_action`），使用根级同一评价维度，记录充分理由、证据、独立复核人、时间与状态；复核人不得等于决策主体。
- `declared_low_information_house_policy_eligibility` 是有依据的显式声明，不是从不透明哈希自动推断出的事实。house policy 要求 `case_specific_facts_present=false` 且 `choice_changing_retrieval_evidence_present=false`。
- `ranking_support` 在 house policy 下必须为空；在 evidence-bound 分支下必须精确覆盖“每个具体 option × 每个评价维度”的笛卡尔积，每格均有非空理由和本轮检索证据引用。

## 排序闭包

- `ranking` 必须是所有 `option_id` 的完整排列，不漏项、不重复。
- `option_kind_ranking` 必须按 `ranking` 逐项投影 `option_kind`。
- `option_record_hashes` 必须用闭合 `{option_id, record_sha256}` 记录逐项覆盖全部方案；`record_sha256` 对包含 run-local `option_id` 的完整十九字段规范 JSON 求 SHA-256，用于本轮防篡改。
- `option_semantic_ranking` 必须按 `ranking` 逐项对删除 `option_id` 后的十八字段规范 JSON 求 SHA-256，用于跨运行比较同语义方案；它不受 run-local ID 差异污染。两种散列都是根级校验投影，不是 option 的第二十个字段。
- 当材料与检索证据足以进行个案比较时，使用 `ranking_policy=evidence_bound_case_comparison`；`ranking_evidence_refs` 必须恰好等于全部 `ranking_support` 单元证据引用的并集，并全部解析到本轮真实检索记录。
- `PROMAX-LOW-INFORMATION-RANKING`：当只有低信息命题、尚无足以改变选择的个案证据时，可以使用 `ranking_policy=promax_low_information_house_policy_not_v8`、`ranking_evidence_refs=[]`。此分支必须恰好生成六个方案、每类一个，类别顺序固定为 `probe_action > active_action > maintain_status_quo > delayed_action > exit_or_transfer > no_action`。
- 上述固定顺序是 ProMax 明示的低信息运行偏好，不是 v8 概念、定理或自动结论，也不得冒充 NSP、最小伤害或比例性原则的个案推导。材料充分后必须允许证据改变排序。
- `preferred_option_id=ranking[0]`，`second_option_id=ranking[1]`，二者不同。
- `no_action_option_id` 必须唯一指向恰好一条 `option_kind=no_action` 的方案。
- `switch_conditions` 至少一项明确写出 `second_option_id` 与触发切换的证据、预测路径或早期信号。
- `inaction_consequences` 非空，说明时间、机会、保护、外部性或路径锁定成本；不行动不是零成本基线。
- 根 `authorization_status` 只能是 `conditional_recommendation_only`、`not_authorized` 或 `authorization_unknown`；分析不得自我授予现实行动权限。
- 采用 house policy 时，dossier 与 essay 都必须逐字披露 `ranking_policy=promax_low_information_house_policy_not_v8`、`PROMAX-HOUSE-POLICY-NOT-V8`、`ranking_evidence_refs=[]`，并明确它不是 v8 概念、规范前提或 v8 自动结论。

写盘后执行 `validate_recommendation_semantics()`。P7 的 `option_ranking_after` 必须与本 ranking 完全相同；P10 essay 必须按首次出现顺序表达完整 ranking，并逐项携带十九字段记录的全部实质语义。
