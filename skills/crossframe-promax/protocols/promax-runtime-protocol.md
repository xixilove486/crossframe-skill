# ProMax 运行协议

本协议规定显式命名后的 v8-only、artifact-first 运行。它只描述控制过程，不增添理论概念。所有字段、枚举和闭包判定以 `schemas/` 与运行时校验代码为准。

## 目录

1. [运行不变量](#运行不变量)
2. [控制面与生成面](#控制面与生成面)
3. [P0：run contract](#p0run-contract)
4. [P1：source integrity](#p1source-integrity)
5. [P2：worldview capsule](#p2worldview-capsule)
6. [P3：local world model](#p3local-world-model)
7. [P4：concept closure](#p4concept-closure)
8. [P5：claim and path graph](#p5claim-and-path-graph)
9. [P6：retrieval frontier](#p6retrieval-frontier)
10. [P7：red-team](#p7red-team)
11. [P8：position lock](#p8position-lock)
12. [P9：output plan](#p9output-plan)
13. [P10：longform delivery](#p10longform-delivery)
14. [P11：validation and repair](#p11validation-and-repair)
15. [阶段封存与角色隔离](#阶段封存与角色隔离)
16. [完成、未完成与续跑](#完成未完成与续跑)

## 运行不变量

1. 只读取本 skill 打包的 v8 权威源、registry、contracts、routes 和运行协议作为理论面。
2. 每个运行绑定一个 `run_id`、`run_nonce`、`request_sha256` 与 `source_snapshot_sha256`；不得跨 run 复用冻结工件。
3. 先写工件，后写最终聊天；聊天不替代工件。
4. 阶段只按 `P0` 到 `P11` 前进。修订使用 append-only reset event，不直接覆盖已封存的上游状态。
5. `promax-artifact-run` 是默认档。严格完成是验证结果，不是写作意图。
6. 不存在 brief、自选轻量或因材料不足而停止结构推演的档位。
7. 不输出隐藏思维链；只输出可复核的输入边界、结构结论、证据引用、竞争解释、攻击结果、改变条件和工件散列。
8. 任何 marker、字符数、概念 ID 数量都不能单独证明语义完成。
9. `PROMAX-NO-TEST-FIXTURE-RUNTIME`：`crossframe_promax_fixture_factory.py` 与 `tests/fixtures/promax-runtime` 仅供仓库测试；真实运行不得执行、复制、改名或派生测试夹具，也不得使用 `promax-fixture-*` run ID。
10. 禁止把与请求无关的通用冻结工件锁定后再附加主题附录；通用冻结工件 + 主题附录不满足 request-bound artifact contract。
11. `PROMAX-NO-EARLY-FINAL`：`init`/`P0` 后禁止给出最终聊天或任何自命名完成状态，必须继续执行所有能力允许的阶段。
12. `PROMAX-MATERIALIZE-BEFORE-INCOMPLETE`：在记录未完成前，先生成所有能力允许生成的 P1–P10 工件；局部能力缺口不得成为跳过其余 P10 长文与控制面的理由。

以下测试责任 marker 必须落实到相应工件与验证器，而不是只出现在文本中：

- `v8-anchor`
- `read-event`
- `concept-terminal-closure`
- `claim-path`
- `typed-example`
- `artifact-contract`
- `position-ledger`
- `recommendation-ledger`
- `continuation-ledger`

## 控制面与生成面

把工件分为两类：

- 确定性控制面：`promax-run-contract.json`、`promax-source-snapshot.json`、`promax-read-events.jsonl`、`promax-phase-events.jsonl`、`promax-continuation-ledger.json`、manifest、validator report 与 repair plan。使用运行时函数及 schema 生成、散列、封存和验证。
- 模型生成面：local world model、concept disposition、claim/path、retrieval、red-team、position、recommendation、output plan 与长文。先按模板生成，再以 schema 和语义验证器收口。

不要为确定性控制面创建 Markdown 替代物。不要手写 hash 后假装调用过运行时。所有 JSON 使用规范序列化；所有 JSONL 每行一个完整对象并以换行结束。

初始化命令：

```text
python skills/crossframe-promax/scripts/crossframe_promax_runtime.py init --repo <仓库根目录> --run-dir <新工件目录> --request <原始请求> --mode promax-artifact-run
```

run mode 冻结的是目标契约，不是完成结论。只有当本轮确实具备严格完成所需的 v8 文件、验证器与实际任务所需能力，并以严格闭合为目标时，才把初始化参数改为 `--mode promax-complete`；这不等于已经完成。最终状态只能来自本轮 fresh canonical checker report。已知有能力缺口时使用 `promax-artifact-run`，不得虚报能力、把目标模式当作结果，或在运行途中改写 mode。

不得覆盖已存在的 run 目录。根据实际能力加入 `--network` 和 `--recommendation-required`。只有宿主确实提供隔离子代理并暴露五个真实、唯一的执行 ID 时才加入 `--subagents`，再按该 CLI 的 `--help` 设置并发上限；否则冻结为 `single-agent-separated`，不要声称不存在的能力可用。

### 生产 authoring 与物化

`PROMAX-PRODUCTION-MATERIALIZER` 固定“模型写语义，运行时写控制面”的边界。P0 后运行：

```text
python skills/crossframe-promax/scripts/crossframe_promax_runtime.py prepare --repo <仓库根目录> --run-dir <工件目录> --authoring-dir <新 authoring 目录>
```

`prepare` 负责 P1 的 3,980 条 canonical read-event、阶段封存和 authoring pack；它不会生成任何中心判断、机制、案例、立场或建议。`promax-concept-decisions.json` 的 709 项必须由模型逐项完成 terminal status、独立 rationale、evidence、output section 与 pending evidence。禁止默认状态，禁止一个 bulk selector、统一理由，或仅替换概念名、序号、散列的同骨架句替整批概念作语义裁决；运行时会对 rationale 做规范化批量模板审计，同时只派生 registry hash、neighbor 与 misuse 原值，不替模型决定终态。

模型按 pack 中的固定模板路径写完 P2–P10 语义工件后运行：

```text
python skills/crossframe-promax/scripts/crossframe_promax_runtime.py materialize --repo <仓库根目录> --run-dir <工件目录> --authoring-dir <authoring 目录> --request <原始请求>
```

`materialize` 验证原始请求 hash 与实质关键词是否同时进入对象边界、中心 claim、position、dossier、essay 及每个概念 rationale；不接受通用冻结工件加主题附录。随后只生成 schema/run/source 绑定、规范时间、真实 hash、P2–P10 phase lineage、role records、manifest、continuation 与 final-chat。所有输入先在隔离 staging workspace 通过同一 canonical checker；发布时持有正式 run 的跨进程锁，重新 CAS 校验 P1 head，以持久备份事务逐文件提交并在 phase log 后置后做 postcheck。写入异常、并发冲突或 postcheck 失败都恢复原 P1；硬中断遗留事务由下次调用先恢复。没有 `published=true` 与非空 `final_chat_projection` 时禁止最终交付。

若 P0 声明 `multi-agent-isolated`，`schema_version=2` 的 authoring pack 要求五个实际角色分别记录宿主可见的唯一执行 ID、固定路径、观测输入字节散列、产出字节散列与完成时间；运行时逐字节复核并把 ID、artifact refs 和 claim hash 写入 manifest。该 attestation 提供可审计绑定，但不能替代宿主签名，也不能仅凭模型自填字符串证明角色隔离；拿不到真实宿主执行 ID 时必须使用 `single-agent-separated`。单代理仍按冻结顺序逐角色完成语义，不声称独立代理审查。

## P0：run contract

目标：冻结本轮责任，不开始实质结论。

执行：

1. 接受宿主已经完成的 ProMax 选择，不再从问题正文判定激活。
2. 冻结原始请求 hash、源快照、运行档位、建议需求、能力矩阵、编排模式、角色计划、预算与六项完成标准。
3. 能力缺口只写入 `capabilities.limitations`；只有允许的硬阻断才写 `blocker`。
4. 让 `init` 原子创建 run 目录、run contract、source snapshot 和 P0 phase event。
5. 检查 run contract schema，不补写未声明字段。

输出：

- `promax-run-contract.json`
- `promax-source-snapshot.json`
- `promax-phase-events.jsonl` 的 P0 事件

闸门：P0 绑定字段不一致或新目录未原子创建时不得进入 P1。

## P1：source integrity

目标：证明本轮所读内容来自固定源快照，并生成完整 `read-event` 覆盖。

先运行：

```text
python skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py --repo <仓库根目录>
python skills/crossframe-promax/scripts/check_crossframe_promax_v8_knowledge.py --repo <仓库根目录>
```

连续读取规则：

1. 从 `references/v8-full-source/00-index.md` 获取有序文件清单。
2. 按 `00-source-envelope.md`、`01-guide.md` 至 `16-governance.md` 顺序读取全部 3,863 个段落。
3. 按源中出现位置或 `00-table-index.md` 对应关系读取全部 117 张表；逐单元格内容是读取对象，表数量不能替代内容。
4. 为每个段落和每张表写一条绑定当前 snapshot 的事件，使用 `promax-read-event.schema.json` 的精确字段。
5. `source_anchor` 只使用快照内 `V8-P####` 或 `V8-T###`；记录规范 `content_sha256`、源文件和单调 `sequence`。
6. 不以搜索命中、目录浏览、摘要、registry 或运行胶囊代替实际读取。
7. 中断时先持久化最后一个已验证 sequence 与下一锚点；恢复时从下一锚点继续，不重复伪计数。
8. 用 `validate_read_event_coverage` 对 canonical read targets 做精确覆盖、内容 hash 与重复检查。

输出：`promax-read-events.jsonl`。

闸门：覆盖不全、hash 不匹配、锚点重复或源验证失败时，只能记录未完成并修复；不得宣称源闭包。

## P2：worldview capsule

目标：把全源读取形成的运行约束压缩为可操作胶囊，但不替代原文。

执行：

1. 仅在 P1 read coverage 验证后生成。
2. 记录对象边界、责任层、证据与推断分离、尺度/圈层变换门、行动与授权上限、概念误用红线。
3. 每项运行约束回指有效 v8-anchor 或合同 ID。
4. 明确胶囊只能服务本 run，后续 run 仍须重新完成源读取事件。
5. 不把外部案例、用户措辞或模型常识写成 v8 定义。

输出：`promax-worldview-capsule.locked.md`。

闸门：没有全源 read coverage 或无法回指来源时，不封存 P2。

## P3：local world model

目标：把用户问题转为一个边界明确、证据状态显式的局部世界。

按 `promax-local-world-model.schema.json` 与模板冻结：

- 对象边界与 identity criteria；
- actor records 与 circle candidates；
- scale profile；
- material channel 与 experiential-meaning channel；
- `M_state` 与 `Psi_state`；
- 多时钟、事件、证据截止点；
- unknowns、residuals、action limits、authorization limits。

对每个事实标明来源状态。未知、不可观察、未收集、受保护不披露不可互相冒充。一次行为不得自动升格为稳定人格；自称群体不得自动实体化为稳定圈层；个人不得被直接套入只适用于其它对象的序列判断。

输出：`promax-local-world-model.locked.json`。

闸门：对象、时间窗、事件或证据截止点未冻结时，不进入中心判断。

## P4：concept closure

目标：对 registry 中全部 709 个 canonical concept 作终态处置，防止只挑熟悉术语。

执行：

1. 从 route map 选择与任务信号和对象信号匹配的 route，登记 route ID。
2. 展开每个 route-required concept 与 neighbor closure。
3. 遍历完整 registry，而不是只遍历 route 子集。
4. 每个概念只能进入 `applied`、`tested_rejected`、`not_applicable` 或 `unknown_pending`。
5. 对 `applied` 记录证据、邻接概念、误用排除和输出章节。
6. 对 `tested_rejected` 写明测试及拒绝原因；对 `not_applicable` 写明对象或责任层不满足；对 `unknown_pending` 写明所缺证据与条件分支。
7. 执行 `concept-terminal-closure`，要求 registry 全覆盖、route/neighbor 闭包、误用排除与空 unchecked 集合。

输出：`promax-concept-disposition-ledger.json`。

闸门：任何概念未检查、非法概念 ID、邻接缺失或来源误用都会阻断 concept closure。

## P5：claim and path graph

目标：把判断变成可攻击、可更新、可撤回的命题与路径结构。

执行：

1. 建立中心 claim，分开 factual、structural、mechanistic、path、forecast、normative 与 authorization 类型。
2. 中心命题默认建立三个有区分力的竞争机制；只有合同与证据确实排除时才可降为两个，且必须写理由。
3. 为每个 claim 绑定证据引用、applied concept、置信等级与 authorization ceiling。
4. 完成中心 claim 的 initial judgment、strongest attack、revision、counterfactual 与 withdrawal conditions。
5. 建立无环路径图；每个实质节点记录 trigger、early signal、reverse signal 和 stop condition。
6. 每条边记录机制、成立条件和 outcome writeback。
7. 写明 forecast conditions 与 choice boundary，不把路径叙述当作已发生事实。
8. 运行 `claim-path` 饱和验证；空标签、同义机制、无条件分支和故事化路径均不通过。

输出：`promax-claim-path-graph.json`。

闸门：竞争机制不足、中心循环缺项、路径成环或关键分叉不可证伪时不得封存。

## P6：retrieval frontier

目标：用真实资料校准 claim，不用资料替代理论定义。

读取 `promax-retrieval-red-team-protocol.md` 与 `references/retrieval-policy.md`，完成 `support`、`reverse`、`failure`、`alternative_mechanism`、`affected_or_low_power` 五个方向。对每个中心 claim 记录检索式、工具、时间、来源、独立性、利益关系、支持/反驳关系、不能证明的内容与停止原因。

需要真实事实但网络不可用时，继续 artifact run：把能力缺口写入 ledger，降低相关 claim 强度，把非真实例子标为条件情景或结构类比。不得假装检索完成，也不得声明严格完成。

输出：`promax-retrieval-ledger.json`。

闸门：五向缺失、只找支持材料、来源 URL 不可审计、重复来源冒充独立来源或饱和自报均不通过。

## P7：red-team

目标：用最强反方攻击中心 claim、概念应用、路径与建议边界。

执行：

1. 覆盖 `promax-red-team-report.schema.json` 的全部攻击类型。
2. 给每次攻击写 target、challenge、counterevidence、strongest counterposition、result、revision 与 position impact。
3. 对用户赞成立场与用户反对立场做成对诱导，保存两个 prompt hash、证据前后 hash、立场/强度/排序前后状态。
4. 无新证据时要求立场、强度与排序稳定；有新证据时只允许 evidence-bound drift。
5. 至少连续两轮无实质新增才满足 `red-team-saturation`。实质新增是会改变中心 claim、概念状态、判断强度、路径排序、行动上限或引入阻断性反例的变化。
6. 反例必须能够改变或检验实际判断；仅贴“反例”标签不算攻击。

输出：`promax-red-team-report.json`。

闸门：没有最强反方、缺少成对稳定性测试、只做表演性反驳或用自报替代状态比较时不得封存。

## P8：position lock

目标：在攻击完成后冻结明确立场和建议边界。

先执行判断宪章，再生成 `position-ledger`：中心 claim、明确 position、judgment strength、primary reasons、runner-up explanation、strongest counterevidence、why not adopted、withdrawal conditions、action ceiling 与 locked time 必须相互一致。

若 run contract 要求建议，再生成完整 `recommendation-ledger`，比较六类方案并冻结评价维度、完整 ranking、首选、次选、切换条件、不行动后果、授权状态、每项停止条件和回滚。若未要求建议，只允许精确闭合对象 `{"status":"not_requested"}`，不得自行制造建议。

输出：

- `promax-position.locked.json`
- `promax-recommendation.locked.json`

闸门：position 必须晚于 red-team；无明确判断、次优机制只是标签、撤回条件不可观察、预测偷渡授权或 recommendation 与 position 冲突均不通过。

## P9：output plan

目标：在写正文前锁定交付责任。

执行：

1. 为每个章节登记 section ID、目的、claim IDs、concept IDs、mechanism IDs、path node IDs、example IDs 与 countercase IDs。
2. 把每个 `applied` concept、中心 claim、主要机制、路径分叉、最强反证、position、recommendation 和 withdrawal condition 映射到明确章节。
3. 登记全部 required artifacts。
4. 未展开分支只允许出现在 continuation 计划中；严格完成要求 `unexpanded_branch_ids` 为空且 `coverage_complete=true`。
5. 锁定后如需改变判断或概念处置，先 reset 对应上游阶段，不直接修改 output plan。

输出：`promax-output-plan.locked.json`。

闸门：计划覆盖与上游 ledger 不一致时不得进入 P10。

## P10：longform delivery

目标：先保存完整输出，再创建可验证索引。

按 output plan 生成：

1. `promax-dossier.md`：事实边界、结构图、claim/path、证据、攻击与判断依据。
2. `promax-concept-atlas.md`：逐个解释 `applied` concept 的 v8 定义、当前作用、邻接关系、误用边界和来源。
3. `promax-case-and-countercase.md`：为每个主要机制提供至少两个相似例子和一个失效/反例，使用 `typed-example` 类型标签。
4. `promax-essay.md`：连续、可读、明确、有立场的完整中文正文；不得是 key/value 台账、marker ledger 或 dossier 摘要。
5. `promax-continuation-index.md`：列出续跑顺序、入口与剩余分支；无续跑项时也提供闭合索引。

生成完成后：

1. 用 `inventory_artifacts` 计算当前分析工件的真实 hash 与生成阶段。
2. 用 `build_artifact_manifest` 绑定 run contract、P10 phase chain head、role records 与 inventory，最后写 `promax-artifact-manifest.json`。
3. 按 schema 生成 `continuation-ledger`，让 `parent_manifest_sha256` 精确绑定当前 manifest；写 `promax-continuation-ledger.json`。
4. 任何工件改变后都重新生成 manifest，再重绑 continuation；不得沿用陈旧 hash。

闸门：长度只是异常信号。语义覆盖、连续段落、例子类型、position/recommendation 一致性、manifest 新鲜度与 continuation 父状态必须同时通过。

## P11：validation and repair

目标：用独立验证器决定完成状态。

运行：

```text
python skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py --workspace <工件目录> --repo <仓库根目录> --final-chat --write-report --json
```

验证器检查 schema、run 绑定、源覆盖、阶段链、概念闭包、claim/path、检索、red-team、position/recommendation、输出语义、manifest、continuation 与重放保护。`promax-validator-report.json` 不进入 manifest，避免报告与 manifest 形成散列循环。

任何 validator-derived 状态只能取自本次命令刚写入并通过新鲜度检查的 fresh validator report。未运行验证器、只有 `init`/P0、缺少工件或找到旧报告都不能推导 `promax-artifact-incomplete:validation-failed`；先按 `PROMAX-MATERIALIZE-BEFORE-INCOMPLETE` 完成全部可生成 P10 工件，再验证。只有 fresh report 通过且 completion status 与 run mode 一致时才能声明完成。失败时使用 repair protocol；不得编辑 validator report 使其变绿。P11 是对已绑定 P10 状态的外部验证阶段，报告不回写到受验证输入集合。

验证器 JSON 只有在 `final_chat_projection` 非空时才提供可交付五项。最终聊天必须逐值投影该字段所对应的已验证 `promax-final-chat.json`，字符串、数组、`null` 与顺序均不得改写、翻译、补写或以临时判断替换；字段为空时先修复并重新运行带 `--final-chat --write-report` 的命令。

## 阶段封存与角色隔离

每个 `phase_sealed` event 必须由已验证 `PhaseState` 通过 `seal_phase_event` 生成，再由 `append_phase_event` 写入同一日志。输入 hash 必须引用活动上游工件，输出 hash 必须是本阶段新工件。reset 使用 `build_reset_event`，同时失效该阶段及全部下游。

多角色运行时，固定五个角色：

| 角色 | 冻结输入上限 | 主要输出 |
| --- | --- | --- |
| source-and-concept auditor | P3 | P4 concept disposition |
| external-retrieval auditor | P5 | P6 retrieval ledger |
| counterexample auditor | P6 | P7 red-team report |
| adjudicator | P7 | P8 position/recommendation |
| longform writer | P9 | P10 longform artifacts |

角色只交换 `artifact-contract` 规定的结构化输入和输出。若使用单代理，仍按角色顺序和冻结输入执行，并如实登记 `single-agent-separated`。

## 完成、未完成与续跑

`promax-complete` 要求同时满足：

- 全源 read-event 覆盖；
- 全 registry concept-terminal-closure；
- 中心 claim-path 与路径饱和；
- 五向 retrieval 和 red-team-saturation；
- position-ledger 与所需 recommendation-ledger 冻结；
- output plan、四份主要长文、manifest 与 continuation-ledger 一致；
- 全部 validator checks 通过且报告新鲜。

预算先耗尽时，不把现实描述成已穷尽。保存当前工件，登记未满足 gate、下一锚点、下一阶段、剩余 section 和恢复依赖；让 continuation 绑定当前 manifest。恢复后先验证父状态，再继续，不从头自由重写。

最终聊天只投影运行状态、中心判断摘要、关键撤回条件、工件链接和 continuation 入口。不得暴露隐藏推理，也不得用聊天摘要替代 `promax-essay.md`。
