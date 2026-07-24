# Essay 生成合同

产物：`promax-essay.md`
生成阶段：`P10`
冻结输入：全部当前 P0–P9 工件与其它 P10 语义工件

Essay 是完整、连续、可读、有明确立场的中文解释，不是 dossier 摘要、字段台账或 marker 集合。篇幅只作为异常信号；语义闭包由下列段落关系和跨工件一致性证明。

## 建议章节顺序

1. `# ProMax v8 完整推演`
2. `## 问题、对象与事实边界`
3. `## 明确判断与竞争解释`
4. `## v8 概念逐项解释`
5. `## 机制、路径与前瞻条件`
6. `## 真实检索、案例与反例`
7. `## 最强反方、修正与撤回`
8. `## 方案排序与行动边界`，仅在建议被请求时出现
9. `## 结论、未知项与续跑`

## 四类连续语义段落

各类别必须至少有一个独立自然段，不能用字段行、项目键值或 ID 清单代替。

### 判断段

同一自然段必须逐字携带 position 的 `position`、`judgment_strength`、全部 `primary_reasons` 和完整 `runner_up_explanation`，并用因为、因此、但、若等关系词解释领先机制为何胜过次优机制。中心 claim statement 必须直接表达。

### 概念段

每个 applied concept 至少一个连续自然段，同时出现 registry 的 `authoritative_name_zh`、完整 `definition`、disposition 的完整 `rationale`，并用因果、对比、条件或限制关系说明当前作用。正文还要解释全部必要邻接关系、误用边界、类似结构和失效条件；概念名或 ID 出现不等于完成解释。

### 反方与撤回段

同一自然段必须逐字携带全部 `strongest_counterevidence`、全部 `why_not_adopted` 和全部 `withdrawal_conditions`，并用对比或条件关系解释为何目前不采纳、什么证据出现时必须撤回或降级。另写 red-team 对对象、尺度、人格、圈层、阶段、简单基线、路径故事化、概率和授权的实际修正。

### 建议段

仅当建议被请求时，同一自然段必须出现 `preferred_option_id`、`second_option_id`、全部 `switch_conditions`、全部 `inaction_consequences` 和根 `authorization_status`，并明确写“首选 OPTION-*”“次选 OPTION-*”以及切换因果。

## 建议完整性

当 recommendation required 时：

- 所有 option IDs 在 essay 中的首次出现顺序必须与完整 `ranking` 相同。
- 每个 option 都逐字携带 `description`、全部 `benefits`、`costs`、`risks`、`stop_conditions`、`rollback` 和自身 `authorization_status`。
- 全部 `evaluation_dimensions` 必须出现并用于比较，不只是列名。
- 明确区分条件化推荐与现实授权，不能因“最优”而自我授予执行权。

当 recommendation 未请求时，essay 不得出现 `OPTION-*`、首选、推荐方案或其它自行生成的建议。

## Claim、路径与案例闭包

- 全部 plan claim statements 必须出现在 essay 或 dossier；中心 claim、竞争机制与修订循环在 essay 中完整解释。
- 每个实质路径分叉解释 trigger、early signal、reverse signal、stop condition 和 outcome writeback。
- 每个主要机制说明至少两个 typed similar cases 和一个 typed failure case；真实案例、用户材料、条件情景、结构类比必须显式区分。
- 外部案例说明来源能证明与不能证明什么；案例不能压过 v8 定义或偷渡授权。

## 禁止的替代写法

- 不把 `key: value`、散列、概念 ID、OPTION 行或 validation marker 堆积当作段落。
- 不用“问题复杂”“各有道理”“还需更多材料”结束；材料不足时给条件分支、当前排序、最有区分力的补证和低后悔观察。
- 不披露私密推理过程、工具试错、英文自我规划或角色自由聊天记忆。
- 不声称穷尽开放世界；只说明验证过的源、概念、检索和攻击闭包。

写完后同时执行长文语义验证、manifest 字节绑定与 continuation lineage 校验；任何 locked field 改变都必须回到其生成阶段重新封存。
