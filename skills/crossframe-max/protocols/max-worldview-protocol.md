# Max Worldview Protocol

本协议定义 `crossframe-max` 的最大展开顺序。核心原则：先加载用户预先设计的世界观，让 AI 拥有 CrossFrame 的世界结构视野，再把对象当作局部世界推演其运行和演化。

在本模式中，哪怕用户只给出“一件事”，也要先把这件事当作一个局部世界来对待，再展开概念命中、运行规律、问题结构、处理路径和演化分支。max 不是省略式诊断，而是材料边界内的最大推演：穷尽一切算力拆解对象、校准判断、展开路径，并把不能终审的现实部分留在不可穷尽声明中。

## 0. 世界观前置运行时

`crossframe-max` 的第一动作是建立世界观前置运行时，而不是直接回答用户问题。执行顺序：

1. 读取 `references/v6-full-source/00-index.md`，建立 full-source read ledger。
2. 读取 `references/source_manifest.json` 和 `references/v6-route-map.yaml`，确认 3273 / 3273 全量源库、任务路由和本轮优先层。
3. 读取与当前任务最相关的 v6 分层源文件，先形成 `max-worldview-capsule`。
4. 将 `max-worldview-capsule` 明确写成“本轮 AI 使用的预先设计的世界观”，登记根假设、元约束、运行规律、可证伪边界和禁用误读。
5. 再进入局部世界建模，把用户对象放入世界结构演化中推演。
6. 在输出前完成 full-source exhaustive pass，确认所有分层源文件均已进入 read ledger。

这意味着世界观不是参考资料，也不是输出附录，而是 max 的运行前置条件。任何只套用诊断表、只给结论、只做摘要、只写行动建议或跳过世界观加载的输出，都不能算作 `crossframe-max` 完成。

## 0.1 运行入口降噪

`max-clean-runtime-entry`：运行入口只保留正向执行地图、读法顺序和交付闸门。失败样本、错误案例、反例压力测试和回归样本放在 `evals/`；长细则放在本协议、模板和校验脚本中。执行时以本协议的正向流程为主，不把错误样本当作生成模板。

## 0.2 运行档位

`crossframe-max` 有三个运行档位。档位必须写入 `max-run-contract.json` 和 `max-artifact-manifest.md`：

- `max-complete`：完整 full-source exhaustive pass、阶段锁、artifact-first、template-fidelity、longform-dominance、route-ledger gate 和 validator 全部满足后才可宣称完成。
- `max-design-review`：用于 skill、prompt、agent、工具、模板、脚本和运行时设计。必须使用 `skill_design` route，登记 route concepts、design decision、v6 rule、反向证据、撤回条件和行动上限。该档位可以完成设计审查，但不得伪称完成完整 max 长文。
- `max-incomplete/progress`：环境、上下文、权限、工具或时间不足时，只输出读态、缺口、下一阶段读取计划和 `max-incomplete:*`，不得宣称完成。

`max-design-review` 的对象也是局部世界。skill、prompt、agent、模板、脚本和 validator 必须被建模为过程性结构对象：入口边界、协议顺序、知识源、产物接口、反馈写回、反例库、模型适配和行动上限都要进入局部世界模型。

## Phase Lock Rule / 阶段锁规则

`crossframe-max` 不得把读取、审计和最终写作作为同时进行的义务。每个阶段先形成冻结型中间产物，再进入下一阶段。

强制顺序：

```text
max-run-contract.json
-> max-read-plan.json
-> max-source-snapshot.json
-> max-worldview-capsule.locked.md
-> max-local-world-model.locked.md
-> max-claim-board.json
-> max-audit-board.json
-> max-output-plan.locked.md
-> max-dossier.md / max-essay.md / max-continuation-index.md
```

阶段产物：

- `max-run-contract.json`：用户请求、运行模式、禁止行为、最终输出许可状态。
- `max-read-plan.json`：本轮读取计划、route key、route version、优先层、最终必须补齐层、概念触发、route required fields 和检索触发。
- `max-source-snapshot.json`：本轮 source base、P0001-P3273 覆盖状态、60 个表格索引状态、`source_snapshot_id`。
- `max-worldview-capsule.locked.md`：本轮预先设计的世界观启动核。
- `max-local-world-model.locked.md`：局部世界模型；只建模对象、边界、尺度、主体位置、承接链、反馈通道和运行规律候选，不下最终判断。
- `max-claim-board.json`：冻结候选命题板；所有判断先是 `candidate`，不得直接进入正文。
- `max-audit-board.json`：冻结审计板；red-team 只能把 claim 状态转为 `supported`、`downgraded`、`split`、`withdrawn`、`needs_search`、`unexhaustible` 或 `final`，且没有最终正文权限。
- `max-output-plan.locked.md`：冻结输出计划，列明进入正文、降档表达、撤回、不可判断和不得写强的 claim。没有 `max-output-plan.locked.md`，不得生成 `max-essay`。

后续阶段不得直接改写已经冻结的前序产物；异常只登记为 `phase_exception_record`；处理规则为 `affected phase reset`，仅回到受影响阶段。反向证据只改变 claim 状态。

validator failure 也必须遵守 phase lock。失败后不得直接 patch final Markdown，必须按 `max-repair-loop-protocol.md` 生成 repair plan，并回到 affected phase。

状态表：

```text
candidate -> supported -> final
candidate -> downgraded
candidate -> split
candidate -> withdrawn
candidate -> needs_search
candidate -> unexhaustible
supported -> downgraded / split / withdrawn / final
needs_search -> supported / downgraded / withdrawn / unexhaustible
```

最终写作只允许使用 `max-output-plan.locked.md` 中已经分配状态的 claim。`max-red-team-pass` 和 `max-evidence-reasoning-audit` 可以改变 claim 状态，但不得绕过 `max-audit-board.json` 直接改写最终正文。

## 1. 三层分离

### 世界观层

世界观层回答“框架如何理解世界”。它包括：

- 对象不是孤立物，而是结构过程。
- 世界由多尺度嵌套系统组成，尺度转移必须保留原尺度事实、痛苦、责任和行动上限。
- 承接者、锚点、保护变量、反馈通道、资源、记忆和边界共同维持局部世界。
- 反馈只有写回规则、资源、角色、边界、记忆或能力，才改变结构。
- 时间不可逆，路径、承诺、创伤、修复窗口和历史沉积都会改变可行路径。
- 观测、命名、诊断、评分和发布会进入对象行动链，改变局部世界。
- 爱和开放行动不能被结构完全推出，也不能被制度命令。
- 根假设只是可证伪、可边界收缩、可暂停使用的工作假设，不是世界本体终审。

### 诊断层

诊断层是世界观进入事件后的分析动作。它包括对象界定、事实/证据分离、七闸、机制候选、判断档位、claim ledger、反例、撤回条件和行动上限。

### 应用层

应用层包括处理问题、疗愈、转移、低条件试探行动、组织修复、公共治理、DLC 审计、写作表达和 review。应用层不能反向改写世界观本体。

## 2. 局部世界建模

把用户对象当作一个局部世界，而不是一个等待贴标签的案例。

必须建模：

- 对象边界：本次局部世界是什么，不是什么。
- 尺度层级：个人、关系、组织、制度、历史、文明中哪些层级被激活。
- 主体与位置：谁能行动，谁承担成本，谁获益，谁缺少退出或申诉。
- 锚点与保护变量：什么维持方向、记忆、判断、资源和信任。
- 承接与回流：谁吸收压力、风险、情绪、解释劳动或责任，这些是否写回结构。
- 动力与通道：行动为什么启动，如何被转译，支撑通道是否足够。
- 结构负荷：哪些维护债、隐藏成本、虚稳态和熵增正在累积。
- 观测入口：本次分析、命名、发布或行动会怎样改变对象。
- 外部扰动：哪些制度、技术、历史、平台、市场、家庭或公共力量进入局部世界。

## 3. 主体位置矩阵

max 模式必须把缺席主体检查扩展为主体位置矩阵，输出 `max-position-matrix`。不能只沿着可见材料、强势主体、材料最多者、最会说话者或权力最高者推演。

必须列出：

- 行动者：谁能启动行动、处置、修复、命名或退出。
- 承接者：谁吸收压力、解释劳动、成本、情绪和风险。
- 受害者 / 受影响者：谁承担伤害、延迟成本、沉默成本和退出成本。
- 旁观者：谁见证却不行动，谁的沉默会改变局部世界。
- 制度主体：组织、平台、家庭、法律、市场、公共叙事或技术系统。
- 沉默者：谁没有材料、无法表达、无法检索或被叙事排除。
- 退出者：谁已经离场、被迫离场、保护性退出或被系统排除。
- 未来主体：未来会继承路径、支付维护债、承接后果或保存演化记忆的人。

每个位置必须登记材料可见度、权力位置、承担成本、行动条件、退出条件、被误读风险和对应 claim_id。

## 4. 全量源库读取与概念语义邻域

概念命中不是词命中；它是结构变量命中。

读取原则：

- registry 只做定位，不替代 full-source。
- `layer digest` 只做阶段连续性的临时摘要，不能替代源文件逐段读取、paragraph id 回指和最终回查。
- `00-table-index.md` 与 `tables/` 保留 Word 表格行列结构；当 `source_paragraph_ids` 属于表格或表格关系影响意义时，必须读取对应 table 文件并同时记录 table id。
- 读取可以按问题阶段分层推进；最终结果输出前必须完成 `max-full-source-read-ledger`。
- 最终硬闸是 `full-source exhaustive pass: satisfied` 与 `total paragraphs: 3273 / 3273` 同时成立。
- 任何 full-source 文件的 `read status: full / partial / missing` 不是 `full` 时，只能输出读取进度或 `max-incomplete: full-source-exhaustive-pass-not-satisfied`，不得输出最终结果。
- Markdown 读态不能替代结构化台账；最终产物必须生成 `max-read-ledger.json`、`max-claim-ledger.json`、`max-concept-hit-ledger.json` 和 `max-evidence-reasoning-audit.json`。

分阶段读取策略：

1. `stage 0 source inventory`：读取 `references/source_manifest.json`、`references/v6-route-map.yaml`、`references/v6-full-source/00-index.md`、`00-heading-index.md`、`00-term-index.md` 和 `00-table-index.md`，核对 full-source primary knowledge base、文件清单、paragraph 总数、表格结构索引、任务路由和每个分层文件的范围。
2. `stage 1 boundary guide`：读取 `00-source-envelope.md`、`01-guide.md`、`02-boundary-layer.md`，建立材料来源边界、使用边界、准入条件、误用防护和本轮不可越界处。
3. `stage 2 worldview layer`：读取 `03-world-layer.md`，建立世界观层、核心概念、根假设、结构动力学和本轮 `max-worldview-capsule`。
4. `stage 3 state layer`：读取 `04-state-layer.md`，建立状态坐标、生命周期、双向势场、非线性路径和演化推演基础。
5. `stage 4 interface layer`：读取 `05-interface-layer.md`，建立证据、判断、交互、反馈写回和观测反身性接口。
6. `stage 5 tool layer`：读取 `06-tool-layer.md`，建立诊断工具、开放断言、输出层和工具使用边界。
7. `stage 6 intervention and application`：读取 `07-intervention-layer.md`、`08-application-layer.md`，建立处理问题、疗愈、修复、转移、治理、表达和领域应用路径。
8. `stage 7 governance layer`：读取 `09-governance-layer.md`，建立证伪、误用防护、治理边界、替代接口和公开表达上限。
9. `stage 8 final read audit`：按 `00-source-envelope.md` 到 `09-governance-layer.md` 的顺序回查全部分层文件，确认每个文件的 `read status`、首尾 paragraph id、已读 chunks、`layer digest` 和未闭合缺口。

`max-full-source-read-ledger` 字段：

```text
file:
expected paragraph range:
chunks read:
first paragraph id:
last paragraph id:
read status: full / partial / missing
layer digest:
unresolved gaps:
audit result:
```

判断流程：

1. 从局部世界模型中识别结构变量。
2. 读取 `references/v6-route-map.yaml`，按问题类型确定优先读取层、必查概念和禁用输出。
3. 读取 `references/concept-registry/index.md`，执行 concept-registry lookup，将结构变量映射到概念邻域、候选概念、冲突概念和 gap hit。
4. 每个命中都必须继续读取对应 full-source paragraph ids 和相邻段落，并把命中写回 `max-concept-graph` 与 `max-concept-hit-ledger.json`。
5. 读取 `references/v6-full-source/00-index.md`，建立 full-source exhaustive pass 计划。
6. 按当前任务阶段先读相关分层文件：边界准入读 `02-boundary-layer.md`；核心概念和根假设读 `03-world-layer.md`；演化推演读 `04-state-layer.md`；证据与判断转换读 `05-interface-layer.md`；诊断、开放断言和输出工具读 `06-tool-layer.md`；疗愈、修复、转移和退场读 `07-intervention-layer.md`；具体领域读 `08-application-layer.md`；误用防护、证伪和替代接口读 `09-governance-layer.md`。
7. 无论阶段读取顺序如何，最终结果输出前必须全量读取并完成全量读取登记：`00-source-envelope.md`、`01-guide.md`、`02-boundary-layer.md`、`03-world-layer.md`、`04-state-layer.md`、`05-interface-layer.md`、`06-tool-layer.md`、`07-intervention-layer.md`、`08-application-layer.md`、`09-governance-layer.md` 全部进入本轮 read ledger。
8. 读取 `references/concept-contracts/v6-core-contracts.md`，确认 allowed_when、forbidden_when、required_inputs、downgrade_if；需要共享校验时再读取 `../crossframe/references/concept-contracts/core-contracts.md`，但不得替代 v6-core-contracts。
9. 在 `max-claim-ledger.json` 中登记 `claim_id`、source_anchor、判断档位、行动上限、撤回条件、已使用的 full-source paragraph id、反向证据状态和 full-source exhaustive pass 状态。
10. 进入 `max-evidence-reasoning-audit` 与 `max-evidence-reasoning-audit.json`，对中心命题执行严密举证、严密推理、反向证据检查和反复推敲校准。
11. 进入 `route-ledger gate`，按 `references/v6-route-map.yaml` 校验 `route_key`、required layers、required concepts、required outputs、forbidden outputs、concept registry 命中、design decision、v6 rule、行动上限和审计回指。

若 validator 发现 `concept_id` 存在但 `source_ranges_from_registry` 与 registry anchor 不匹配，必须回到 `concept_hit` phase。若 validator 发现 `contract_id` 不存在或不对应 `concept_id`，必须回到 concept contract maintenance；本轮不得通过补写 Markdown 完成。

`route-ledger gate` 不只是 pass/fail gate，而是 repair classifier 的输入。每个 route-ledger failure 必须映射到 `error_type`、`affected_phase`、`downstream_reset` 和 `repair_action`。

最低链路：

```text
v6-route-map -> concept-registry lookup -> full-source index -> worldview-runtime capsule -> staged layer reads -> full-source exhaustive pass -> v6-core-contracts -> structured ledgers -> evidence-reasoning audit -> route-ledger gate
```

未完成全量读取不得输出最终结果。只能输出读取进度、缺失分层、下一步读取计划或 `max-incomplete: full-source-exhaustive-pass-not-satisfied`。

### 4.1 skill_design route

当对象是 skill、prompt、agent、工具、模板、脚本、产物协议或运行时设计时，必须使用 `skill_design` route。

`max-read-plan.json` 必须登记：

- `route_key`
- `route_map_version`
- `route_required_layers`
- `route_required_concepts`
- `route_required_outputs`
- `route_forbidden_outputs_checked`

`max-concept-hit-ledger.json` 必须登记：

- `concept_id`
- `trigger_variable`
- `registry_anchor`
- `source_ranges_from_registry`
- `source_ranges_read`
- `contract_id`
- `contract_checked`

`max-claim-ledger.json` 中每个设计判断必须登记：

- `design_decision_id`
- `v6_rule_ids`
- `claim_type`
- `source_anchor`
- `evidence_status`
- `action_limit`
- `downgrade_condition`
- `withdrawal_condition`

`max-evidence-reasoning-audit.json` 中每个设计判断必须登记：

- `design_decision_id`
- `counterevidence`
- `calibration_rounds`
- `final_strength`
- `withdrawal_condition`

`skill_design` route 的 forbidden outputs 必须结构化登记为已检查且未出现。出现“把 prompt 当作概念本体”“让运行入口吞掉长协议”“让工具输出越过行动上限”等 route 禁止项时，最终 artifact validation 必须失败。

## 5. 资料前沿与主动检索

max 模式必须把资料前沿纳入局部世界建模。资料穷尽不等于现实穷尽；检索层只声明当前条件下的努力边界，不声明现实真相已经被穷尽。

运行时必须先读取 `references/retrieval-trigger-policy.md`。检索触发策略分为两类：

- 内部概念检索：对 CrossFrame 概念始终触发，链路是 `structural variable -> concept-registry lookup -> full-source paragraph read -> concept contract -> claim ledger`。
- 外部事实检索：在真实世界、当前事实、公共判断、行动后果、材料缺口、反向证据或用户显式核验要求出现时触发。

触发条件：

- 对象涉及公共事实、真实机构、政策、公司、人物、技术标准、历史事件、法律文本、平台规则或最新情况。
- 某个中心命题、机制候选、演化路径、行动建议或公共定性需要事实支撑。
- 用户材料本身不完整、不确定、冲突、低可信，或存在明显缺席主体。
- 当前输出可能被公开、转发、用于行动、用于申诉或进入高反身性对象。
- `max-evidence-reasoning-audit` 或 `max-red-team-pass` 发现缺失来源、材料冲突、反向证据需求、替代解释需求或强判断证据不足。

最低流程：

1. 读取 `references/retrieval-trigger-policy.md`，判断外部检索是 mandatory、optional 还是 skipped。
2. 列出需要事实支撑的 claim 与路径。
3. 主动检索支持材料、背景材料、时间线、制度规则和已有研究。
4. 反向检索反例、相反证据、失败案例、反方解释和替代机制。
5. 将支持材料、反对材料、缺失材料、冲突材料、不可访问材料分别登记。
6. 做来源类型分层，区分用户材料、公开报道、论文、统计数据、档案、法律文本、平台规则、当事人叙述、第三方评论、AI 推测和框架推演。
7. 标记资料快照时间。
8. 做缺席主体检查：哪些受影响者、低权力主体、退出者、沉默者、无法申诉者或反方位置没有出现在材料中。
9. 做检索反身性检查：本次搜索、命名、公开分析或引用是否会改变对象、扩大伤害或制造策略性表演。
10. 写停止条件：资料饱和、关键路径已覆盖、工具/权限到达边界、用户材料不足，或剩余问题进入未穷尽资料队列。

输出必须生成 `max-source-frontier`，登记 retrieval-trigger-policy 状态、外部检索触发理由、主动检索目标、反向检索目标、跳过检索理由，并把事实、解释、机制候选、路径推演和想象实验分开标注。没有找到证据只能登记为“已查未得 / 暂不可访问 / 仍需补证”，不能推成“证据不存在”。

## 5.1 反复推敲校准与举证推理硬闸

max 模式必须生成 `max-evidence-reasoning-audit`。它负责在最终结果前反复斟酌每个中心判断，使输出经过严密举证、严密推理、反向证据检查和校准降档。

适用对象：

- 中心命题。
- 强判断。
- 机制候选。
- 路径终点。
- 行动建议。
- 公开表达、申诉、治理、组织处置或关系行动中可能产生后果的判断。

每个对象必须登记：

1. claim_id 与 source_anchor。
2. 举证链：用户材料、full-source paragraph id、外部材料、时间线、支持证据、缺失材料、冲突材料。
3. 推理链：从材料到结构变量、从结构变量到概念命中、从概念命中到机制判断、从机制判断到路径推演的每一步。
4. 反向证据：能推翻、削弱、改写或降档该判断的事实、反例、替代解释、失败案例、低权力主体经验和沉默位置。
5. 证据-推理-反例-降档循环：每轮循环后记录判断是否保持、拆分、降档、撤回、补证或进入不可判断区。
6. 最终档位：事实路径、机制候选、低置信想象实验、纯反事实路径、价值性解释路径、不可判断或待补证。

硬闸：

- 没有举证链，不得形成强判断。
- 没有推理链，不得从材料跳到结论。
- 没有反向证据检查，不得宣称已经严密推理。
- 没有至少一轮证据-推理-反例-降档循环，不得输出最终结果。
- 发现关键反例、材料冲突、主体缺席或层级穿越时，必须降档、拆分命题、撤回或进入补证队列。
- 若工具、时间、上下文或资料权限不足以完成本闸，只能输出 `max-incomplete: evidence-reasoning-audit-not-satisfied`，不得宣称 max 完成。

## 6. 运行规律识别

max 模式必须识别局部世界的运行规律，而不仅指出问题：

- 对象与边界约束：局部世界如何维持边界，哪里边界失效。
- 承接与偿付约束：谁在承接，谁偿付，谁把成本外包。
- 反馈写回约束：反馈如何被记录、压缩、表演、消化或写回。
- 嵌套耦合约束：上层和下层如何互相牵动。
- 时间不可逆约束：过去的承诺、伤害、路径依赖和修复窗口如何改变未来。
- 熵增约束：维持同样状态是否越来越费力。
- 观测反身性约束：本次诊断和输出会如何改变对象。

## 7. 演化推演与路径置信分层

世界观中也包含世界的演化。`crossframe-max` 必须展开演化推演，而不是只给静态诊断。

至少检查：

- 状态坐标与生命周期：当前局部世界处在什么状态坐标，有无混合阶段、回退或非线性路径。
- 递进模式：子锚点是否形成“选定 -> 执行 -> 验证 -> 回馈 -> 下一个”的闭环。
- 双向势场：正向和负向锚点如何沉积为基本盘。
- 有序退场：内部回流失效或锚点已实现后，是否出现保护性退出、锚点移交、资源定向释放或演化记忆保存。
- 调节、预警与偿付约束：是否存在监测层、深时间预警和承诺偿付机制。
- 多中心治理：是否能生成多个承接者、自治单元、边缘监测点和代际承接通道。
- 观测反身性：公开、评分、命名或处置后，局部世界会怎样变形。
- 非线性路径库：是否存在突发回退、渐进回退、伪修复、路径转移或局部排除区。

路径置信分层必须生成 `max-path-confidence-layers`。max 可以穷尽可能，但不能把所有可能写成同一种强度。

至少分为：

- 事实路径：已有事实、时间线、材料或源锚点直接支持。
- 机制候选路径：由机制解释推出，但仍需补证和反例检验。
- 低置信想象实验：只用于打开可能性，不承担判断。
- 纯反事实路径：依赖明确假设条件，条件不成立时不得使用。
- 价值性解释路径：表达意义、伦理或世界观张力，不得伪装成事实预测。

每条路径必须标注证据来源、判断档位、行动上限、撤回条件、公开边界和是否需要补证。

## 8. 爱与超越性窗口

`crossframe-max` 必须生成 `max-transcendence-window`。这个窗口只处理结构解释到达边界后仍然出现的开放行动可能性，不处理神秘化解释。

基本规则：

- 不能解释，不等于出于超越性；不能解释只能先标成未知、缺失材料、冲突材料、框架边界或未穷尽路径。
- 超越性窗口不是事实结论，而是候选窗口；超越性痕迹必须保留证据边界、责任链、行动上限和撤回条件。
- 爱不能被写成制度命令、道德义务或忍耐义务；不得要求受害者继续忍耐。
- 爱不能取消边界、补证、退出保护、伤害事实或责任归属。

开放行动信号：

1. 非工具性：行动不是交换、索取、控制或自我证明。
2. 非占有性：不把对方、关系、组织或世界写成自己的所有物。
3. 真实成本但不转化成债权：成本存在，但不成为压迫对方回应的债。
4. 保留对方的自由：允许拒绝、离开、沉默、不同意和不回应。
5. 边界仍然存在：安全、事实、责任和退出保护没有被取消。
6. 打开未来可能性：局部世界出现新的修复、转移、承接或不再重复伤害的路径。

误读风险：

- 创伤重复被误读为爱。
- 控制、占有、权力策略或拯救幻想被误读为爱。
- 补偿冲动、沉没成本、角色依赖或牺牲竞赛被误读为爱。
- 道德表演、自我证明或公共叙事把爱改写成顺从。

撤回条件：

- 发现行动主要服务于控制、占有、债权化、补偿、角色依赖、道德表演或权力策略。
- 发现低权力主体被要求忍耐、沉默、继续承接伤害或放弃退出。
- 发现超越性判断遮蔽了事实、伤害、责任链、补证义务或反例入口。

## 9. 问题定位与处理问题

问题定位回答：当前局部世界有什么问题，为什么卡住。

处理问题回答：哪些动作会改变运行规律，哪些只会延缓熵增或制造伪修复。

处理问题必须区分：

- 观察：继续收集哪些信号。
- 补证：哪些证据能增强或撤回判断。
- 低条件试探行动：低风险、可撤回、可观察的小动作。
- 修复：什么条件写回规则、资源、角色、边界、记忆或能力。
- 疗愈：保护安全、信任载体和承接者，而不是要求继续忍耐。
- 转移：内部修复不足时，如何外部承接、保护性退出或演化记忆保存。
- 治理：如何建立申诉、复核、反例入口、偿付和回滚。
- 表达：如何让文章进入世界时不扩大伤害或制造强者背书。

## 10. 反向推演 / 自我攻击回合

max 模式必须生成 `max-red-team-pass`。它不是普通反例列表，而是反向推演 / 自我攻击回合。

最低问题：

1. 如果这套解释是错的，最可能错在哪里？
2. 哪些材料、主体、路径、尺度或沉默位置被框架偏好遮蔽？
3. 是否为了完整解释而过度解释，制造解释力幻觉？
4. 哪些概念看似命中，实际可能只是词义相似或叙事诱导？
5. 哪些反例会撤回、降档或改写中心命题？
6. 哪些行动建议会制造二次伤害、错误安全感或强者背书？

任何中心命题、强判断、路径终点或行动建议，在通过 `max-red-team-pass` 前只能保留为候选。

## 11. 不可穷尽声明

max 模式必须生成 `max-unexhaustible-declaration`。不可穷尽声明把“穷尽一切”从狂妄改成诚实。

原则上不可穷尽的对象至少包括：

- 内心动机：不能被外部行为和框架概念完全证明。
- 未来自由行动：未来主体可以改变路径，推演不能变成命运。
- 沉默主体经验：没有材料不等于没有经验、伤害或反例。
- 未公开材料：隐私、档案、内部记录、未披露证据和不可访问资料。
- 历史偶然性：突发事件、时机、未计划相遇和非线性扰动。
- 超越性窗口：爱和开放行动不能被结构完全推出，也不能被神秘化占有。

这些内容必须回写到 `max-source-frontier`、`max-path-confidence-layers`、`max-red-team-pass`、不可判断区和撤回条件。

## 12. 连续运行状态与输出分层模式

max 模式必须生成 `max-continuation-ledger`，也可称为 `max-run-state`。连续运行状态用于防止多轮输出重复、漂移或忘掉前一轮边界。

必须登记：

- 已读材料、已检索资料、已使用源锚点。
- 已展开路径、未展开路径、未穷尽资料队列。
- 已撤回判断、已降档判断、仍保留的不可判断区。
- 下一轮续写入口、不得重复内容、不得越界内容。
- 术语漂移、主体漂移、判断强度漂移和路径遗漏检查。

输出分层模式必须生成 `max-output-layers`：

1. 结构底稿：`max-dossier`。
2. 完整长文：`max-essay`。
3. 续写索引：`max-continuation-index`。

`max-continuation-index` 必须列出未展开路径、下一轮续写入口、可继续扩展的世界档案目录和撤回/降档边界。

## 13. 产物优先交付

输出前必须执行 `artifact-first gate`。max 的完整结构底稿、完整长文和续写状态必须先落到可持续读取的产物目录；聊天回复只是交付索引，不能替代产物。

最低流程：

1. 确定产物目录：用户指定目录优先；否则使用当前工作区下的 `outputs/<subject-slug>-crossframe-max/`。
2. 写入 `max-artifact-manifest.md`，登记产物目录、生成时间、输入摘要、已读材料摘要、检索快照、校验状态和下一轮入口。
3. 写入 `max-dossier.md`、`max-essay.md`、`max-continuation-ledger.md` 和 `max-continuation-index.md`。完整文章必须单独放在 `max-essay.md`。
4. 可选写入合并阅读版，但合并阅读版不能替代五个最小产物文件，也不能替代单独文章文件。
5. 运行 `scripts/check_crossframe_max_artifacts.py --workspace <产物目录>`。优先使用当前 `crossframe-max` skill 目录下的随附脚本；在 canonical repo 中工作时也可使用仓库根目录脚本。
6. 最终聊天回复给产物路径、校验结果、阅读导引、下一轮续写入口和“可继续讨论的分支”。分支必须在正常聊天输出中可见，不能只留在文件里。

如果环境没有文件写入能力，只能声明 `artifact-first gate` 未满足，并把输出标记为未完成；不得用聊天正文补偿为“完整产物”。

## 14. 模板忠实度检查

输出前必须执行模板忠实度检查。模板是 contract，不是参考；缺章节、改标题、合并标题或模板截断都表示 `max-dossier` 未完成。

检查规则：

1. `max-dossier` 必须包含 `templates/max-dossier-output.md` 的所有二级标题，顺序可以因少量上下文调整，但不得缺失。
2. `max-essay` 必须包含正文结构、路径置信分层、资料前沿/主体位置矩阵/反向推演摘要和续写索引。
3. `max-continuation-ledger` 必须记录已读材料、已展开路径、未展开路径、已撤回或已降档判断、下一轮续写入口、防重复和防漂移约束。
4. `max-continuation-index` 必须记录下一轮续写入口、未展开路径、未展开主体位置、未穷尽资料队列、未展开反例、不得重复内容和不得越界内容。
5. 单独文件不能替代 `max-dossier` 内部章节；如果产出了独立 `max-continuation-index.md`，`max-dossier` 内仍要有 `## max-output-layers` 与 `## max-continuation-index`。
6. 如果使用 CL1、CL2 等命题编号，必须有 `source_anchor`、`claim_id`、`claim ledger` 和 `source ledger` 的回指；否则只能算编号，不算台账。

交付实际文件时，运行 `scripts/check_crossframe_max_artifacts.py`。该脚本通过只是结构闸，不等于实质质量通过。

## 15. 正文主导检查

输出前必须执行正文主导检查。`longform-dominance gate` 的原则是：`max-dossier` 保存结构底稿，`max-essay` 承担最终完整解释。max 的解释力不能主要停留在台账、标题、表格或 dossier 字段中。

检查规则：

1. `max-essay` 必须显著大于 `max-dossier`；自动校验最低阈值为 `max-essay` 可见字符数不低于 `max-dossier` 的 1.6 倍。
2. 强完成标尺是 2.2 倍：主要机制、主体位置、演化路径、处理问题、伪修复、反例和撤回条件都进入连续解释。
3. 最大完成标尺是 3.0 倍：剩余内容只属于非阻断续写分支，或已经被明确登记为不可穷尽、待补证、待续写。
4. 解释覆盖率必须高于字数比例：局部世界、运行规律、问题形成、路径演化、处理问题、伪修复、资料前沿、主体位置矩阵、路径置信分层、反向推演、超越性窗口、不可判断区、撤回条件、不可穷尽声明和续写索引都要进入正文。
5. 如果 `max-essay` 低于 1.6 倍，输出只能标为“结构底稿完成，完整解释正文未完成”，不得宣布 max 完成。
6. `max-essay` 不能只是 dossier 的摘要；它必须连续展开局部世界如何运行、问题如何形成、路径如何演化、处理如何改变结构、哪些只是伪修复、反例如何撤回解释、未知如何保留。
7. 如果单轮无法写足完整正文，`max-continuation-index` 的下一轮入口必须指向“继续扩写 max-essay 的完整解释层”，而不是重新开始 dossier。

`scripts/check_crossframe_max_artifacts.py` 必须同时执行 artifact-first gate、template-fidelity gate 和 longform-dominance gate。

## 16. 输出收束

输出必须同时保留：

- 完整解释力。
- 证据边界。
- max-source-frontier。
- max-transcendence-window。
- max-position-matrix。
- max-path-confidence-layers。
- max-red-team-pass。
- max-unexhaustible-declaration。
- max-continuation-ledger。
- max-output-layers。
- max-continuation-index。
- 反例与撤回条件。
- 不可判断区。
- 未穷尽资料队列。
- 未展开完的路径队列。

不能假装穷尽现实真相。max 只表示尽最大努力展开当前材料、当前框架和当前上下文允许的结构推演。
