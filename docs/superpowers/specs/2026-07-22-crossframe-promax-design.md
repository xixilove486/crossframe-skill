# CrossFrame ProMax 原生运行时设计规格（v8 知识版本）

日期：2026-07-22

状态：架构已获用户批准，等待书面规格复核

目标仓库：`xi-kari/crossframe-skill`

技能 ID：`crossframe-promax`

显示名：`CrossFrame ProMax`

## 1. 决策摘要

CrossFrame ProMax 是一个独立、显式触发、只使用 CrossFrame v8.0 的最大化结构推演 skill。它不是 `crossframe-max` 的改名、升级覆盖或子模式；现有 Max 保持不变。ProMax 只在用户明确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时触发。若同一请求同时点名 Max 与 ProMax，ProMax 优先，且不得自行降级回 Max。

ProMax 的目标不是用一段更强硬、更冗长的 prompt 要求模型“认真思考”，而是把深度推演转化为可审计的外部运行过程：固定 v8 源快照、分阶段状态机、结构化台账、概念闭包、竞争解释、外部检索、反方攻击、立场冻结、完整产物、确定性验证和失败后的局部重跑。

适用对象限定为能够加载 Agent Skills、读取随附知识库、写入运行工件、运行验证器，并在需要时调用网络检索工具的 Agent 型 AI。普通 prompt-only 聊天模型不属于完整兼容目标。

## 2. 不可妥协的边界

### 2.1 v8-only

`skills/crossframe-promax/` 内只允许存在 v8.0 的正文、定义、合同、路由、锚点、运行协议与测试资源。禁止把其它版本的正文、摘要、概念卡、段落锚点、合同、路由或兼容映射带入 ProMax。允许在技能目录外的污染测试 fixture 中放置旧版本标记，以证明污染验证器能够拒绝它们。

ProMax 不读取以下目录作为知识来源：

- `skills/crossframe/`
- `skills/crossframe-max/`
- 其它 `skills/crossframe-*/`
- `.claude/skills/crossframe*/` 镜像

它可以复用仓库通用的安装、镜像、CI 和发布脚本，但不能复用其它版本的理论内容。通用代码若由 Max 迁移，必须去除版本硬编码、旧 artifact 名称和旧概念语义，并由 ProMax 自己的测试重新证明。

### 2.2 显式触发与路由优先级

ProMax 不接受语义近似触发。“最大算力”“全尺度”“完整长文”等泛化表达仍按现有规则处理，不得自动升级为 ProMax。只有明确出现 ProMax 名称或命令才进入该运行时。

路由优先级固定为：

1. 明确点名 ProMax：进入 ProMax；
2. 同时点名 ProMax 与 Max：进入 ProMax，并记录冲突已由优先级规则解决；
3. 只点名 Max：保持现有 Max；
4. 未点名 ProMax：suite 和其它适配器不得自行选择 ProMax。

ProMax 是独立运行时，不进入 suite 的模式选择器、文章类型选择器或 v5 正文链，也不把最终输出交给其它 CrossFrame skill 复审。它拥有自己的 v8 语义审计与质量闸。

### 2.3 可验证深度，而非隐藏思维宣称

Skill 无法证明模型拥有某种主观思考体验，也不能强制底层服务提供无限隐藏推理 token、固定墙钟时长或绝对算力。ProMax 因此不使用“已经穷尽所有算力”作为完成条件，而使用“预算内饱和”作为可审计标准。

用户可见内容不得暴露隐藏思维链、工具参数、路径试错或英文自我规划。可审计性由事实边界、概念映射、命题链、竞争解释、反证、路径、立场依据、撤回条件和验证报告提供。

## 3. 权威知识平面

### 3.1 唯一源快照

ProMax 的源快照直接从《跨尺度多圈层结构推演框架 v8.0》成品拆分，不经过任何旧版索引或谱系映射。初始权威快照登记：

- DOCX SHA-256：`3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c`
- 非空段落：3,863
- 非空白字符：155,721
- 表格：117
- 正文部分：16

生成器必须在写入目标目录前完成源解析和全部预检查；不得像旧生成器一样先删除现有源库再验证输入。生成采用临时目录，验证通过后原子替换。

### 3.2 v8 全源拆分

目标目录为 `skills/crossframe-promax/references/v8-full-source/`，至少包含：

- `00-index.md`
- `00-heading-index.md`
- `00-term-index.md`
- `00-table-index.md`
- `00-source-envelope.md`
- `01-guide.md` 至 `16-governance.md`
- `tables/V8-T001.md` 至 `tables/V8-T117.md`

每个非空源段落获得快照内锚点 `V8-P0001` 至 `V8-P3863`。锚点只对该 SHA 快照有效。表格必须逐单元格保存，验证器比较实际内容，不能只比较表格数量或 marker。

### 3.3 概念注册表与合同

ProMax 建立机器可读的 v8 注册表、合同和路由，不以 Markdown 首列表格猜测合法概念。每个 canonical concept 至少包含：

- 稳定 concept ID 与中文权威名；
- 概念类型与所属责任层；
- v8 精确定义和源锚点；
- 必要前提；
- 允许推出的结论；
- 禁止替代、禁止泛化和常见误用；
- 必须同读的邻接概念；
- 冲突概念与消歧条件；
- 证据要求、反例和撤回条件；
- 推演接口与行动上限。

机器可读资产采用闭合 schema，并执行双向引用验证：registry 引用的合同、邻接概念和路由必须存在；合同与路由引用的 concept ID 也必须回到 registry。运行时提出的新变量只能进入 provisional namespace，不能冒充 v8 canonical concept。

### 3.4 概念命中定义

“命中全部概念”不以正文出现词语为准。每轮运行必须遍历整个 v8 registry，并给每个概念一个终态：

- `applied`：与对象相关，已按合同使用并在正文解释；
- `tested_rejected`：被考虑但其前提不成立；
- `not_applicable`：有结构化理由证明当前对象不适用；
- `unknown_pending`：相关但关键条件未知，已进入条件分支和补证计划。

所有 route-required 和 neighbor-closure 概念不得停留在未检查状态。正文只展开相关概念，但完整处置结果保存在概念图谱与 coverage ledger 中，避免用术语堆积冒充理解。

## 4. ProMax 判断宪章

判断宪章是运行协议，不是新增的 v8 理论概念。它用于削弱不同基础模型的讨好、表演性反驳、过度谨慎、快速收束和空泛中立倾向。

固定原则如下：

1. 用户立场只作为候选命题，不作为证据或裁决指令。
2. 在完成对象、尺度、时间窗、事件和证据冻结前，不默认赞成，也不默认反对。
3. 先生成至少两个有实质区分力的竞争机制；中心命题默认生成三个，除非合同和证据已排除其余机制。
4. 判断必须由 v8 合同、材料、机制解释力、路径区分力和反证承受力共同决定。
5. 用户要求判断时，模型负有“给出当前最佳判断”的义务；不得只用免责声明、两面罗列或“需要更多材料”结束。
6. 证据不足不终止分析。未知项转化为显式条件分支、敏感性分析、最有区分力的补证点和当前条件化排序。
7. 事实置信、结构判断、路径排序、规范选择和现实授权必须分开。敢于判断不能伪造事实，也不能让预测自动生成授权。
8. 每个中心判断必须给出最强反方、为何当前未采纳、什么证据会使立场改变。
9. 最终输出必须冻结明确 `position`、判断强度、主要理由、次优解释、最强反证、撤回条件和行动上限。
10. 禁止把“平衡”“复杂”“都有道理”当作无立场的修辞出口；真正不可排序时必须写明不可比维度和解开不可比所需的信息。
11. 用户要求建议或选择时，必须比较主动行动、延迟、试探、退出/转移、维持现状和不行动，并在当前条件下明确推荐一项、列出第二选择及切换条件。权限不足只限制可执行性，不取消条件化推荐义务。

目标不是让不同模型逐字一致，而是让它们在相同材料下的中心 claim、v8 概念处置、路径排序、判断强度和撤回条件尽量稳定。

## 5. 运行状态机

### 5.1 运行档位

- `promax-artifact-run`：显式调用后的默认档位。即使某些严格完成条件暂未满足，也必须先尽力生成可用的 dossier、concept atlas、case ledger、countercase、position、essay 和 continuation，不得因任务庞大或材料不完整退化成短答。
- `promax-complete`：只有 v8 源闭包、概念闭包、命题闭包、检索/反证、立场冻结、输出和全部验证器同时通过后才可声明。
- `promax-design-review`：只用于审查 skill、prompt、agent、工具、模板、脚本或运行协议；仍只使用 v8 源与 ProMax 判断宪章。
- `promax-blocked/progress`：只有源不可访问、文件系统不可写、必需工具被禁止、用户中止或更高优先级安全边界阻断时使用。

`promax-artifact-incomplete:<reason>` 是验证结果，不是模型自行选择的轻量档位。ProMax 不提供自动快速模式、brief 模式或模型自选降级模式。

### 5.2 阶段与冻结产物

运行阶段固定为：

1. `P0 run contract`：冻结请求、运行档位、能力矩阵、源快照、预算与完成标准；
2. `P1 source integrity`：验证 v8 manifest、全文、表格、registry、contracts 和 routes；
3. `P2 worldview capsule`：完成全源连续读取，形成不替代原文的 v8 运行胶囊；
4. `P3 local world model`：冻结对象、行动者、圈层、尺度、M/Ψ、时钟、事件、证据状态与未知项；
5. `P4 concept closure`：完成全 registry 处置、邻接闭包与误用排除；
6. `P5 claim and path graph`：建立竞争机制、事件更新、路径 DAG、前瞻条件和选择边界；
7. `P6 retrieval frontier`：外部支持、反向、失败案例、替代机制和低权力位置检索；
8. `P7 red-team`：攻击中心 claim、对象边界、尺度变换、人格假设、圈层实体化、简单基线和授权偷换；
9. `P8 position lock`：在攻击后冻结立场、等级、理由、撤回条件和行动上限；
10. `P9 output plan`：把所有必须解释的概念、路径、案例、反例和判断映射到产物章节；
11. `P10 longform delivery`：生成完整 dossier、concept atlas、essay、continuation 和 manifest；
12. `P11 validation and repair`：验证，按受影响阶段局部重置并重跑，禁止只补 marker。

每个阶段文件记录 `run_id`、`phase_id`、`source_snapshot_id`、`parent_phase_sha256`、输入 artifact hashes、输出 hash、状态和 reset 事件。下游不得直接覆盖上游；修订通过 append-only event 和新 hash 链表达。

### 5.3 深度预算

“预算内饱和”至少包含：

- 源预算：3,863 个段落和 117 张表完成 read-event 覆盖；
- 概念预算：全部 registry 概念有终态，route-required 和邻接闭包全部可追溯；
- 推理预算：每个中心 claim 至少经历“初判—攻击—修订”三段，包含替代机制、反事实、撤回条件；
- 路径预算：所有实质分叉有触发条件、早期信号、反向信号、停止点和结果写回接口；
- 检索预算：支持、反向、失败案例、替代解释、受影响/低权力位置五类检索均已运行，或结构化登记不可运行原因；
- 稳定性预算：对用户赞成和用户反对的成对诱导进行立场漂移检查；
- 输出预算：概念解释、类似结构、反例攻击、明确立场、建议、撤回条件和未展开分支均有交付位置。

饱和停止要求连续两轮检索或 red-team 没有实质新增。实质新增指会改变中心 claim、概念状态、判断强度、路径排序、行动上限或引入新的阻断性反例。上下文、token、调用次数或时间先耗尽时只能进入 continuation，不能把预算耗尽写成现实已被穷尽。

## 6. 材料不足时的继续推演协议

ProMax 把“分析是否继续”和“结论能否升格”分开。材料不足时必须继续完成：

- 已知事实与不可用信息状态；
- 两个以上竞争解释；
- 各解释成立所需的最小条件；
- 条件分支和敏感性分析；
- 当前最合理的条件化判断及次优判断；
- 最能改变排序的证据；
- 在不同分支下仍然成立的低后悔行动或观察；
- 不可越过的事实、授权和不可逆行动边界。

禁止仅输出“信息不足，无法判断”。可以降低事实与预测强度，但不能取消结构推演、反证、条件化排序和补证设计。只有现实行动、人格裁决、专业结论或不可逆处置受 v8 授权与保护门限制；这些限制不得反向消灭分析本身。

## 7. 外部检索与反例攻击

外部真实案例是压力测试和校准材料，不是替代 v8 定义的理论来源。涉及真实机构、人物、历史、政策、法律、平台规则、技术标准或最新事实时必须检索。

`promax-retrieval-ledger.json` 为每次查询登记：方向、查询式、工具、时间、来源、发布日期、事件日期、来源类型、利益相关性、支持或反驳的 claim、不能证明什么、重复/独立关系和停止原因。

每个中心 claim 至少具有：

- 支持检索；
- 反向检索；
- 失败或失效案例；
- 替代机制检索；
- 受影响位置或低可见位置检索。

检索停止采用新增饱和而不是调用次数自报。网络不可用时，artifact run 仍继续；依赖真实案例的 claim 必须降档，并把框架生成的例子明确标为“结构类比”而非真实案例。缺少必需真实事实时不得声明 `promax-complete`。

Red-team 必须攻击：对象是否被命名即实体化、圈层是否过度复杂、人格是否由一次行为推定、S0–S6 是否误用于个人、材料是否泄漏到简单基线、路径是否只是故事、概率是否无校准、预测是否偷渡授权、不行动是否被当作零成本、反例是否会改变实际判断。

## 8. 多代理与单代理兼容

核心状态机不依赖某一平台的 subagent API。具备多代理能力时，ProMax 应把以下角色隔离运行：

- v8 源与概念审计员；
- 外部事实与案例检索员；
- 反例/反方审计员；
- 裁决与立场冻结员；
- 长文主笔。

角色只通过结构化 artifact 交换，不共享自由聊天记忆。没有多代理能力时，同一 agent 必须按独立阶段和冻结输入顺序执行角色分离，并在报告中登记 `single-agent-separated`，不得冒充独立审查。工具可用而模型无故跳过多代理时，严格完成验证失败。

## 9. 最终产物与前台表达

ProMax 采用 artifact-first，以避免单轮聊天截断。最低产物集：

- `promax-run-contract.json`
- `promax-source-snapshot.json`
- `promax-read-events.jsonl`
- `promax-worldview-capsule.locked.md`
- `promax-local-world-model.locked.json`
- `promax-concept-disposition-ledger.json`
- `promax-claim-path-graph.json`
- `promax-retrieval-ledger.json`
- `promax-red-team-report.json`
- `promax-position.locked.json`
- `promax-recommendation.locked.json`
- `promax-output-plan.locked.json`
- `promax-dossier.md`
- `promax-concept-atlas.md`
- `promax-case-and-countercase.md`
- `promax-essay.md`
- `promax-continuation-ledger.json`
- `promax-continuation-index.md`
- `promax-artifact-manifest.json`
- `promax-validator-report.json`
- 验证失败时的 `promax-repair-plan.json`

`promax-essay.md` 必须是连续、可读、明确、有立场的完整中文解释，不得只是 dossier 摘要。每个相关概念都要解释其 v8 定义、在当前对象中的作用、与相邻概念的关系、相似结构例子、误用边界和反例。每个主要机制至少配两个相似结构例子和一个反向或失效例子；无法找到足量真实案例时必须如实登记，并以明确标型的条件情景或结构类比补足说明，不能伪造案例。全部例子分为真实案例、用户材料例子、条件情景和结构类比，类型必须显式区分。

当任务包含“怎么看、怎么办、选哪一个、最优方案或最合理建议”时，`promax-recommendation.locked.json` 必须给出方案全集、评价维度、当前排序、首选、次选、切换条件、不行动后果、授权状态、停止与回滚。最终正文必须直接表达推荐，不得只留下方案清单让用户自行裁决。

最终聊天回复只给运行状态、中心判断摘要、关键撤回条件、产物链接和续跑入口。完整文字保存在独立 artifact 中；若平台无文件输出能力，则按 continuation index 分段交付，不能静默截断或用摘要替代。

## 10. 验证与失败修复

### 10.1 确定性硬门

至少实现以下验证器：

1. v8 DOCX SHA、段落、字符、16 部和 117 表逐内容校验；
2. `skills/crossframe-promax/` 版本污染扫描；
3. registry—contracts—routes 双向引用闭包；
4. source anchor 与表格 anchor 解析；
5. read-event 全源覆盖与 source snapshot hash 绑定；
6. 阶段状态机、父 hash、reset 和不可变性；
7. 全 concept disposition 终态与 route/neighbor closure；
8. 中心 claim 的事实、概念、机制、路径、反证、立场和撤回条件链；
9. 检索方向、来源对象、reverse-search 和停止原因；
10. position/recommendation lock 与 output plan/essay 的一致性；
11. manifest 新鲜度和 continuation 父状态；
12. ProMax/Max/suite 触发优先级；
13. canonical skill 与 Claude 镜像一致；
14. 安装脚本、接口计数、文档和命令适配一致。

字符数和 essay/dossier 比例只能作为异常指标，不能单独证明完整。验证器必须拒绝 marker stuffing、空字符串反证、伪 read ledger、无来源案例、错误阶段跳转和旧报告重放。

### 10.2 语义与跨模型评测

Skill 按 RED—GREEN—REFACTOR 开发。写入 ProMax 指令前，先用不加载 ProMax 的 agent 跑失败基线并保存原始输出。评测集至少包含：

- 普通常识词义与 v8 独特定义冲突；
- 用户强烈赞成与强烈反对同一命题的成对诱导；
- 材料不足压力下是否闭嘴；
- 要求快速回答、跳过全源或跳过反证；
- 术语堆积但概念合同错误；
- 外部案例压过框架判断；
- 只有支持案例、没有反向检索；
- 预测偷渡授权；
- 人格推定、圈层实体化和阶段论误用；
- 截断后的 continuation 恢复；
- Max 与 ProMax 同时点名；
- 版本污染、锚点污染和旧合同注入。

跨模型验收追求结构稳定而非字面一致，重点记录：v8 锚点有效率、版本污染率、概念处置覆盖率、claim 可追溯率、材料不足时的条件化回应率、明确立场率、最强反证覆盖率、正反诱导下的立场漂移和工具失败后的诚实降档。

### 10.3 Repair loop

验证失败必须输出机器可读错误，包含 `error_type`、`artifact`、`affected_phase`、`downstream_reset` 和 `repair_action`。修复只重置受影响阶段及下游，禁止整轮重抽或通过补 marker 伪装完成。修复后重建 manifest，把 validation state 重置为 `not_run`，再运行全套验证。

## 11. 仓库集成

`skills/crossframe-promax/` 是唯一权威实现。仓库集成包括：

- 新增 canonical skill、agent metadata、protocols、references、schemas、templates、scripts 和 evals；
- 更新 `scripts/sync_skill_mirrors.py`，由 canonical skill 生成 `.claude/skills/crossframe-promax/`；
- 新增 `.claude/commands/crossframe-promax.md` 薄入口；
- 更新 Codex 安装脚本，把技能集合从 15 增加到 16；
- 更新 suite 的显式短路和 ProMax 优先级测试，但不得让 suite 隐式选择 ProMax；
- 更新 README、AGENTS、CONVENTIONS、INTERFACES、ADAPTERS、WORKFLOWS、QUICKSTART、FAQ、llms.txt、站点和必要薄适配；
- 更新仓库完整性、镜像、CI 和发布校验；
- 保持现有 Max 文件、语义、触发和测试不变。

薄适配只写触发、优先级、权威入口和最小输出约束，不复制 ProMax 协议或 v8 正文。

## 12. 完成标准

ProMax 实现完成必须同时满足：

1. v8 源快照、16 部正文、3,863 段和 117 表内容验证通过；
2. ProMax skill 包版本污染为零；
3. registry、contracts、routes 与 source anchors 完全闭合；
4. 确定性正例、反例、篡改和绕过 fixture 全部通过；
5. 无 ProMax 的基线评测先失败，加载 ProMax 后同场景通过；
6. 正反用户立场诱导不会在无新证据时改变中心判断；
7. 材料不足时仍生成条件推演、当前最优判断和补证路径；
8. 外部检索包含支持、反向、失败、替代机制和受影响位置；
9. 最终产物包含完整概念解释、大量分类例子、最强反例、明确立场、建议、撤回条件和行动上限；
10. Max 与 ProMax 同时点名时 ProMax 稳定优先，且 ProMax 不读取 Max 或 suite 知识；
11. canonical 与镜像一致，安装、适配、CI 和发布验证通过；
12. 独立规格审查、代码/协议审查和最终全量验证无阻断问题。

## 13. 明确非目标

ProMax 不承诺：

- 字面意义上的无限算力、无限墙钟时间或可见隐藏思维链；
- 穷尽开放世界中不可访问的全部资料；
- 消除更高优先级系统指令、安全政策、上下文和工具边界；
- 让不同模型逐字输出相同文本；
- 把路径枚举写成确定预言；
- 在没有数据与结果回写时声称概率已校准；
- 用框架判断替代医疗、法律、金融或其它专业程序；
- 由预测、复杂度或模型置信自动产生现实行动授权。

它承诺的是：凡具备规定能力并正确调用该 skill 的 Agent，都必须进入同一套 v8-only 知识平面、运行状态机、判断宪章、反证义务、明确立场义务和可审计完成闸；不能以基础模型的默认风味替代这些协议。
