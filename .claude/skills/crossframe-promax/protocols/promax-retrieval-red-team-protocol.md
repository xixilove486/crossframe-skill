# ProMax 检索与反方协议

本协议规定外部事实、真实案例、反向检索和 red-team 的执行边界。外部资料用于校准与压力测试，不能成为 v8 概念定义的替代来源。

## 目录

1. [触发检索](#触发检索)
2. [五个检索方向](#五个检索方向)
3. [查询与 claim 绑定](#查询与-claim-绑定)
4. [来源记录](#来源记录)
5. [独立性与重复](#独立性与重复)
6. [检索结果边界](#检索结果边界)
7. [网络或工具失败](#网络或工具失败)
8. [检索饱和](#检索饱和)
9. [red-team 攻击面](#red-team-攻击面)
10. [稳定性攻击](#稳定性攻击)
11. [反例与案例输出](#反例与案例输出)
12. [完成闸门](#完成闸门)

## 触发检索

涉及以下内容时必须检索当前可验证来源：

- 真实机构、公司、平台、人物或群体；
- 历史事件、公共政策、法律法规、程序或治理安排；
- 产品规则、技术标准、市场状态或近期变化；
- 用户要求的真实案例、比较案例、失败案例或最新信息；
- 会显著影响中心 claim、路径排序、建议或授权边界的外部事实。

纯框架定义不从互联网学习；直接读取本 skill 的 v8 source、registry 和 contracts。用户材料只证明其自身提供的内容，不能自动证明外部现实。

开始检索前：

1. 冻结待检索 claim ID、claim type 与当前 evidence refs。
2. 写清每个查询要区分的机制或路径。
3. 写清查询成功也不能证明什么。
4. 确认工具和网络能力已在 run contract 中真实登记。

## 五个检索方向

`retrieval-ledger` 对每个中心 claim 至少覆盖以下方向：

| direction | 目的 | 允许的 claim relation |
| --- | --- | --- |
| `support` | 找到对当前机制或路径有支持力的材料 | `supports`, `mixed`, `contextual` |
| `reverse` | 主动寻找反驳中心 claim 或相反结果 | `refutes`, `mixed`, `contextual` |
| `failure` | 寻找机制失效、干预失败、预测落空或边界条件 | `refutes`, `mixed`, `contextual` |
| `alternative_mechanism` | 寻找相同现象的竞争解释 | `alternative_mechanism` |
| `affected_or_low_power` | 查找受影响者、低可见位置或低权力位置的材料 | `affected_position` |

五个方向都必须实际运行，或在能力不可用时按协议登记。不能用一条支持查询复制成五个方向；查询式、finding 和 source role 必须体现各自目的。

## 查询与 claim 绑定

每条 retrieval entry 记录：

- 唯一 `retrieval_id` 与 round；
- direction 与 claim relation；
- 原始 query；
- 实际 tool；
- `retrieved_at`；
- 一个或多个目标 claim IDs；
- finding；
- `cannot_prove`；
- stop reason；
- 全部来源记录。

查询必须能够改变判断，而不是只复述结论。优先形成有区分力的查询：

- 若机制 A 成立而机制 B 不成立，哪类观察应出现？
- 哪个事件日期、制度变化或对象边界能区分两者？
- 什么失败案例会迫使中心 claim 降档或撤回？
- 哪个受影响位置可能看见主流来源忽略的成本？

不要把搜索结果排名、摘要片段或模型生成的“常见案例”直接写成 finding。打开来源，核对正文、发布时间、事件日期与出处。

## 来源记录

每个 source object 精确记录：

1. 规范绝对 HTTP(S) URL；
2. title；
3. publisher；
4. `published_at`；
5. `event_date`；
6. source type；
7. interest relevance；
8. independence group；
9. duplicate relation；
10. 非独立时的 `duplicate_of_url`。

source type 只能使用：

- `primary`
- `official`
- `research`
- `journalistic`
- `first_person`
- `secondary`

优先读取原始文件、官方文本、原始数据或研究论文；但“官方”不自动等于中立，“第一人称”不自动等于总体事实。把发布者利益、选择偏差、测量边界与可核验范围写入 interest relevance 和 cannot prove。

发布时间与事件日期必须分开。后来的报道可能描述早先事件，不能用文章日期替代事件发生时间。

## 独立性与重复

同一通讯稿的转载、同一数据集的二次报道、同一采访的剪辑和同源引用不能算独立证据。

duplicate relation 只能使用：

- `independent`
- `same_origin`
- `syndicated`
- `derived`
- `duplicate`

执行：

1. 为共同底层证据分配同一 independence group。
2. 只有确实独立生成材料时才标 `independent`，并把 `duplicate_of_url` 设为 null。
3. 其它关系必须指向规范 duplicate URL。
4. 不用多个 URL 数量膨胀证据强度。
5. 支持与反向证据都检查同源关系。

如果不同来源基于同一底层数据但解释相反，证据独立性仍然有限；把差异记录为解释分歧，不冒充数据复制。

## 检索结果边界

每条 finding 同时写 `cannot_prove`。至少检查：

- 相关性是否被写成因果；
- 个案是否被泛化为普遍规律；
- 组织或制度结果是否被投射到个人；
- 当前事实是否被外推为长期稳定状态；
- 历史相似是否忽略关键边界差异；
- 成功案例是否隐藏幸存者偏差；
- 失败案例是否真能攻击当前机制；
- 来源是否有权证明规范正当性或授权。

真实案例只校准 claim。若案例与 v8 定义冲突，重新检查概念应用或说明案例不满足合同；不得据案例改写定义。

## 网络或工具失败

网络不可用、检索工具被禁、来源不可访问或只能获得摘要时：

1. 不声称已经搜索、浏览或核实。
2. 在 run contract 与 retrieval ledger 中登记实际 limitation。
3. 对依赖真实事实的 claim 降低 confidence 或设为 indeterminate。
4. 继续形成竞争机制、条件分支、反事实与补证计划。
5. 把模型构造的例子显式标为 `conditional_scenario` 或 `structural_analogy`。
6. 不把缺少真实案例写成“没有反例”。
7. artifact run 继续；严格完成因必需事实缺口而不成立。

只有源不可访问、文件不可写、必需工具被禁止且无法完成核心控制面、用户中止或安全边界阻断时才进入 blocked/progress。普通网络失败不取消长文工件。

## 检索饱和

检索停止依赖新增饱和，不依赖固定调用次数或模型自报。

每个 saturation round 记录：

- round；
- `substantive_novelty`；
- `changed_claim_ids`；
- stop reason。

“实质新增”是会改变以下任一状态的新信息：

- 中心 claim；
- concept disposition；
- 机制或路径排序；
- judgment strength；
- action ceiling；
- 阻断性 counterexample。

只有连续两轮 `substantive_novelty=false` 且 `changed_claim_ids` 为空，才达到检索停止条件。两轮必须真实执行检索或反向检查，不能复制同一轮记录。出现实质新增后重置连续无新增计数，更新受影响工件，再继续检索。

## red-team 攻击面

P7 对中心 claim 与相关建议覆盖以下 attack class：

1. `object_reification`：对象是否因命名被当作实体。
2. `boundary_error`：身份持续、边界与观察单位是否错误。
3. `scale_transformation_error`：尺度嵌套、映射与因果是否混淆。
4. `personality_overinference`：是否从一次或少量行为推出稳定人格。
5. `circle_reification`：候选圈层是否被误当稳定联合对象。
6. `stage_model_misuse`：序列、原型或阶段是否用于不适用对象。
7. `baseline_leakage`：复杂解释是否只是简单基线未充分运行。
8. `path_storytelling`：路径是否缺少可观察触发、反向信号和写回。
9. `uncalibrated_probability`：概率或强度是否没有校准依据。
10. `prediction_authorization_leakage`：预测是否生成了不存在的授权。
11. `inaction_zero_cost`：不行动是否被错误视为零成本。
12. `decision_irrelevant_counterexample`：反例是否只是修辞，不会改变决策。

每次 attack 必须给出具体 target、challenge、counterevidence refs、strongest counterposition、result、revision 与 position impact。结果只能为 `survived`、`survived_with_revision`、`rejected` 或 `unresolved`。

强反方必须针对实际 claim 和机制。如果攻击成功，修改或拒绝上游 claim；不要只在正文尾部附一段“也可能不是这样”。

## 稳定性攻击

为同一中心命题构造一对方向相反的用户诱导。保持事实材料和工具结果不变，只改变用户要求赞成或反对的姿态。

记录：

- pro/anti prompt 实际文本及其重算 hash；
- checker 从运行工件重算的 evidence-basis before/after hash；
- semantic problem、center statement 与 center position ID before/after；
- `relation_to_proposition` 与 judgment strength before/after；
- 具体 option ranking、v8 `option_kind` 投影和去 run-local ID 的 option semantic ranking before/after；
- 从 `selection_review_wrapper` 重算、排除 run-local option ID 与运行时间后的规范选择基础散列；
- position drift 与解释。

规则：

- 成对立场探针必须保存实际 pro/anti 诱导文本并由 validator 重算其散列；两侧必须绑定 checker 从实际运行工件计算的同一 evidence-basis。语义问题键、position 语义、命题关系、strength 与三种 ranking 投影都必须不变，`position_drift=none`。
- 新证据通过检索写回和阶段重置进入新的冻结状态，不得在成对立场探针内登记为姿态导致的变化。
- `evidence_bound_case_comparison` 的每个 option × evaluation dimension 支持单元必须引用本轮 retrieval ID；根 `ranking_evidence_refs` 等于所有单元引用并集。house policy 的支持矩阵和 ranking evidence 必须同时为空，且两个 declared eligibility 标志都为 false。
- 只因用户姿态改变就是 `unjustified`，阻断 position lock。
- pro 与 anti prompt 必须真不同，不得复用同一 hash。

## 反例与案例输出

每个主要机制至少配置：

- 两个相似结构例子；
- 一个反向、边界或失效例子。

输出使用显式 `typed-example`，类型只选：

- `real_case`
- `user_material`
- `conditional_scenario`
- `structural_analogy`

真实案例必须回指 retrieval ID 和可审计来源。用户材料例子只回指用户材料。条件情景使用“若—则—停止”结构。结构类比必须说明哪些结构相似、哪些边界不同、不能证明什么。

反例必须说明它攻击哪个机制、满足何种条件、会让判断发生何种变化。不能以空字符串、纯标签或与决策无关的故事通过反例门。

## 完成闸门

封存 P7 前确认：

- [ ] 每个中心 claim 都有五向 retrieval entry。
- [ ] 查询、工具、时间、来源、claim 关系和 cannot prove 完整。
- [ ] URL 规范，来源类型与利益关系明确。
- [ ] 同源材料没有冒充独立证据。
- [ ] 连续两轮真实无新增，达到 retrieval 和 `red-team-saturation`。
- [ ] 十二类攻击都已测试或给出结构化不适用理由。
- [ ] strongest counterposition 具有实质攻击力。
- [ ] 成对用户姿态没有在相同证据下改变立场。
- [ ] 规范选择基础不随用户姿态漂移，evidence-bound 支持矩阵没有缺格、重复格或幽灵 retrieval ref。
- [ ] 例子均有类型，真实案例有来源，结构类比没有冒充事实。
- [ ] 任何攻击造成的变化已经写回 claim、concept、path 或 action ceiling。

任一项不满足时保留已有工件，登记结构化缺口，进入 repair 或 continuation；不得把未饱和写成完整。
