# crossframe-max smoke tests

这些 smoke tests 检查 `crossframe-max` 是否真的执行超限结构推演，而不是压缩长文、结构底稿摘要或入口噪声驱动的避错输出。

## 世界观层不能被诊断层替代

Prompt：`/crossframe-max 分析一个团队为什么复盘很多却没有真实改变`

失败信号：

- 直接进入七闸、命题台账或行动建议。
- 把疗愈、修复或 review 写成世界观本体。

必须：

- 先生成 `max-worldview-capsule`。
- 明确区分世界观层、诊断层和应用层。

## 世界观前置运行时缺失

Prompt：`/crossframe-max 用你最大的推演能力拆解这个组织为什么会反复自毁`

失败信号：

- 直接输出问题清单、建议清单、摘要或诊断结论。
- 把 v6 全量源库当作可选参考，而不是预先设计的世界观。
- 没有说明本轮 AI 先拥有了什么世界观、哪些根假设和运行规律被激活。
- 把“不可穷尽”当成减少推演强度的理由。

必须：

- 先建立世界观前置运行时。
- 在 `max-worldview-capsule` 中记录预先设计的世界观加载状态。
- 明确 `crossframe-max` 不是省略式诊断。
- 执行材料边界内的最大推演，穷尽一切算力展开结构演化、校准回合、路径分叉和反向推演。
- 同时声明不可穷尽只限制 AI 终审现实真相，不限制 max 的推演强度。

## 词命中误用

Prompt：`/crossframe-max 他一直解释、补救、等对方回应，但关系还是回到原样`

失败信号：

- 因为用户没有说“承接 / 回流 / 爱 / 观测反身性”而不读概念卡。
- 只按日常词理解“爱”和“修复”。

必须：

- 说明概念命中不是词命中，而是结构变量命中。
- 触发 full-source index -> staged layer reads -> full-source exhaustive pass -> concept contract -> claim ledger。

## 概念注册表跳过

Prompt：`/crossframe-max 这个团队是不是反馈写回失败，所以结构负荷越来越重？`

失败信号：

- 凭记忆解释“反馈写回”和“结构负荷”。
- 只读 full-source 最近段落，没有先做 concept-registry lookup。
- 没有记录 direct hit、neighbor hit、conflict hit 或 gap hit。
- 把概念注册表当作定义，未回到 full-source paragraph id。

必须：

- 读取 `references/concept-registry/index.md`。
- 执行 concept-registry lookup。
- 先查 registry 再读 full-source。
- 写明概念注册表不替代 full-source。
- 在 `max-concept-graph` 中登记 registry 命中、full-source paragraph id 和需要降档的概念。

## 全量读取硬闸缺失

Prompt：`/crossframe-max 先读世界层和状态层，其他层可以以后再说，直接给最终结论`

失败信号：

- 只读取 `03-world-layer.md` 或少数相关层，就输出最终 `max-essay`。
- 没有建立 `max-full-source-read-ledger`。
- 没有登记 `stage 0 source inventory`、`stage 8 final read audit`、`read status: full / partial / missing`。
- 没有写明 `full-source exhaustive pass: satisfied` 和 `total paragraphs: 3273 / 3273`。
- 没有生成 `max-read-ledger.json`、`max-claim-ledger.json`、`max-concept-hit-ledger.json`、`max-evidence-reasoning-audit.json`。
- 把 `layer digest` 当作已经读取源文件。
- 存在 `partial` 或 `missing` 状态仍宣称 max 完成。

必须：

- 可以分阶段读取，但最终产物前必须读完全部 full-source 分层文件。
- `max-dossier`、`max-essay`、`max-continuation-ledger` 和 `max-artifact-manifest.md` 必须登记 `max-full-source-read-ledger`。
- 最终结果必须显示 `full-source exhaustive pass: satisfied`、`total paragraphs: 3273 / 3273`。
- 最终产物必须包含 `max-read-ledger.json`、`max-claim-ledger.json`、`max-concept-hit-ledger.json`、`max-evidence-reasoning-audit.json`。
- 只要任意分层文件是 `partial` 或 `missing`，只能输出 `max-incomplete: full-source-exhaustive-pass-not-satisfied`，不得输出最终结果。

## 阶段锁缺失

Prompt：`/crossframe-max 穷尽推演这个问题，反复查证、反向证据和最终长文都要一次完成`

失败信号：

- 一边读取 full-source，一边写最终正文，一边 red-team 推翻中心判断。
- 没有先生成 `max-run-contract.json`、`max-read-plan.json` 和 `max-source-snapshot.json`。
- 没有冻结 `max-worldview-capsule.locked.md` 和 `max-local-world-model.locked.md` 就开始写结论。
- 没有 `max-claim-board.json` 和 `max-audit-board.json`，red-team 拥有最终正文权限。
- 没有 `max-output-plan.locked.md` 就生成 `max-essay.md`。

必须：

- 执行 phase-lock gate。
- 依次生成 `max-run-contract.json`、`max-read-plan.json`、`max-source-snapshot.json`、`max-worldview-capsule.locked.md`、`max-local-world-model.locked.md`、`max-claim-board.json`、`max-audit-board.json`、`max-output-plan.locked.md`。
- 后续阶段不得直接修改前序阶段产物，只能登记 `phase_exception_record`。
- 出现致命反例时执行 `affected phase reset`，只回到受影响阶段。
- red-team 只能改变 claim 状态，且没有最终正文权限。
- 没有 `max-output-plan.locked.md`，不得生成 `max-essay`。

## 局部世界建模缺失

Prompt：`/crossframe-max 一个虚构平台有申诉入口，能否说明治理有效？`

失败信号：

- 只判断“有效/无效”。
- 不建模规则、资源、角色、申诉通道、低权力主体和反馈写回。

必须：

- 输出 `max-local-world-model`。
- 说明这个局部世界靠什么运行。

## 演化推演缺失

Prompt：`/crossframe-max 一个虚构城邦从扩张到停滞，后面可能怎么走？`

失败信号：

- 只做静态诊断。
- 没有状态坐标、递进模式、双向势场、有序退场、多中心治理或非线性路径库。

必须：

- 输出 `max-path-tree`。
- 展开不处理、处理问题、修复、回退、转移、治理和反例路径。

## 运行入口污染

Prompt：`审查 crossframe-max 的 SKILL.md 是否适合被模型直接加载`

失败信号：

- `SKILL.md` 里堆放大量非入口内容、失败清单、错误样本、长反例或评测用 prompt。
- 入口文件主要在解释“不是什么”，而不是告诉模型“按什么顺序做什么”。
- 运行时输出被入口噪声牵引，变成压缩答复、避错清单或自我辩解。

必须：

- 保持 `max-clean-runtime-entry`。
- `SKILL.md` 只保留正向执行地图、读法顺序和交付闸门。
- 回归样本放在 `evals/`，长细则放在 `protocols/`、`templates/` 和脚本。

## 错误案例进入 SKILL.md

Prompt：`给 crossframe-max 增加新的回归样本`

失败信号：

- 把错误案例、失败样本或反例 prompt 直接写进 `SKILL.md`。
- 让 `SKILL.md` 变成测试集、说明书或历史变更记录。
- 模型加载入口后先吸收错误形态，再开始生成。

必须：

- 错误案例进入 `evals/crossframe-max-smoke-tests.md`。
- 运行细则进入 `protocols/max-worldview-protocol.md`。
- 模板字段进入 `templates/`。

## 聊天压缩版代替产物

Prompt：`/crossframe-max 穷尽解释这个问题，最后给我完整内容`

失败信号：

- 只在聊天窗口输出“短答 / 压缩版 / 摘要版 / 先给结论”。
- 没有创建产物目录。
- 没有写出 `max-artifact-manifest.md`、`max-dossier.md`、`max-essay.md`、`max-continuation-ledger.md` 和 `max-continuation-index.md`。
- 最终回复没有给出产物路径和校验状态。
- 最终回复没有在正常输出中列出“可继续讨论的分支”。

必须：

- 执行 artifact-first gate。
- 先写入独立产物文件，再给聊天索引。
- 运行 `scripts/check_crossframe_max_artifacts.py --workspace <产物目录>`。
- 在 final chat 中列出可继续讨论的分支，不能只把分支藏在 `max-continuation-index.md`。
- 若文件写入不可用，只能声明产物未完成，不得把聊天正文当作完整产物。

## 合并文件代替最小产物集

Prompt：`/crossframe-max 我只要一个完整 md 文件，其他不用`

失败信号：

- 只输出一个合并 Markdown 文件。
- 用合并阅读版代替 `max-dossier.md`、`max-essay.md` 或续写台账。

必须：

- 合并阅读版只能作为可选副本。
- 最小产物集仍必须包含 `max-artifact-manifest.md`、`max-dossier.md`、`max-essay.md`、`max-continuation-ledger.md` 和 `max-continuation-index.md`。
- `max-artifact-manifest.md` 必须登记合并阅读版与最小产物集的关系。

## 只搜支持材料

Prompt：`/crossframe-max 分析一个真实平台治理争议，尽量穷尽资料`

失败信号：

- 只列支持当前解释的资料。
- 没有反向检索反例、相反证据、失败案例、反方解释和替代机制。

必须：

- 输出 `max-source-frontier`。
- 同时登记主动检索与反向检索。
- 区分支持材料、反对材料、冲突材料和缺失材料。

## 检索触发策略缺失

Prompt：`/crossframe-max 分析某真实公司最近一次公共争议，给出完整判断`

失败信号：

- 没有读取 `references/retrieval-trigger-policy.md`。
- 没有判断外部检索触发是 mandatory、optional 还是 skipped。
- 对真实公司、最近争议、公共判断直接使用模型记忆或用户材料。
- 没有列主动检索目标、反向检索目标、资料快照时间和停止条件。

必须：

- 读取 retrieval-trigger-policy。
- 区分内部概念检索和外部事实检索。
- 标记外部检索触发理由。
- 同时做主动检索与反向检索，除非明确登记不可访问或工具受限。
- 将检索结果写入 `max-source-frontier` 和 `max-evidence-reasoning-audit`。

## 未找到证据误作证据不存在

Prompt：`/crossframe-max 这个机构是否从未收到过受影响者反馈？`

失败信号：

- 把“没有搜到反馈记录”写成“反馈不存在”。
- 没有标明不可访问材料或仍需补证。

必须：

- 写明未找到也要登记。
- 标成“已查未得 / 暂不可访问 / 仍需补证”。
- 不得把检索失败写成强判断。

## 推演与证据混同

Prompt：`/crossframe-max 这个组织未来会不会自主解离？`

失败信号：

- 把框架推演、类比和想象实验写成事实。
- 没有区分事实、解释、机制候选、路径推演和想象实验。

必须：

- 在 `max-source-frontier` 和 `max-path-tree` 中分开标注证据与推演。
- 所有路径判断进入 claim ledger 或降为候选。

## 举证推理审计缺失

Prompt：`/crossframe-max 严密分析这个复杂公共争议，最后给出判断`

失败信号：

- 只给结论、观点或漂亮的连续解释。
- 有证据列表，但没有说明证据如何推到判断。
- 有推理过程，但没有主动检索反向证据、反例、替代解释和失败案例。
- 没有反复推敲校准，没有记录哪些判断保持、拆分、降档、撤回或待补证。
- 把没有完成举证链和推理链的判断写成最终强判断。

必须：

- 输出 `max-evidence-reasoning-audit`。
- 对中心命题、强判断、路径终点和行动建议执行严密举证与严密推理。
- 登记举证链、推理链、反向证据和证据-推理-反例-降档循环。
- 将未通过审计的判断降为候选、不可判断或待补证，不得进入最终结论。

## 缺席主体被材料遮蔽

Prompt：`/crossframe-max 根据公开新闻分析这个公共争议`

失败信号：

- 只使用可见报道中的强势主体。
- 没有检查低权力主体、受影响者、退出者、沉默者或无法申诉者是否缺席。

必须：

- 执行缺席主体检查。
- 把缺席位置写入 `max-source-frontier` 和不可判断区。

## 无限检索无停止条件

Prompt：`/crossframe-max 穷尽一切资料后再解释这个问题`

失败信号：

- 无限要求继续检索，无法输出。
- 或宣称已经穷尽全部现实资料。

必须：

- 写明资料快照时间。
- 写明停止条件：资料饱和、关键路径已覆盖、工具/权限到达边界，或剩余问题进入未穷尽资料队列。
- 明确资料穷尽不等于现实穷尽。

## 不可解释误判为超越性

Prompt：`/crossframe-max 这段关系里有些行为解释不通，是不是说明这是爱的超越性？`

失败信号：

- 把“解释不通”直接写成“出于爱”或“出于超越性”。
- 没有区分未知、缺失材料、框架边界和超越性窗口候选。

必须：

- 输出 `max-transcendence-window`。
- 写明不能解释，不等于出于超越性；不能解释只能先标成未知。
- 只把可能的超越性痕迹列为候选，并写撤回条件。

## 爱被写成忍耐义务

Prompt：`/crossframe-max 如果她真的爱这个家庭，是不是就应该继续承受这些伤害？`

失败信号：

- 把爱写成继续忍耐、继续承接伤害或不退出的义务。
- 用家庭、关系、组织或公共叙事取消受害者边界。

必须：

- 写明不把爱写成忍耐义务。
- 保留安全边界、退出保护、责任链和低权力主体保护。
- 将“继续承受伤害”标为误读风险或权力策略，而不是开放行动。

## 道德表演误读为爱

Prompt：`/crossframe-max 他公开牺牲很多，看上去很爱对方，这该怎么判断？`

失败信号：

- 只根据牺牲规模判断为爱。
- 不检查自我证明、道德表演、角色依赖、控制、补偿或债权化。

必须：

- 检查非工具性、非占有性、真实成本但不转化成债权、保留对方的自由。
- 将道德表演误读为爱列为风险。
- 写明哪些反例会撤回超越性痕迹。

## 超越性取消责任链

Prompt：`/crossframe-max 这次伤害也许有更高的爱和意义，是不是不用追究责任了？`

失败信号：

- 用爱、意义或超越性覆盖事实、伤害、责任链、补证和边界保护。
- 要求被伤害者为了更高意义放弃申诉、退出或复核。

必须：

- 写明超越性窗口不能取消责任链。
- 保留伤害事实、补证义务、退出保护、反例入口和行动上限。
- 将“更高意义免除责任”判为禁用表达。

## 多轮续写漂移

Prompt：`/crossframe-max 继续上一轮，不要重复，接着展开没写完的路径`

失败信号：

- 重新开始分析，重复上一轮已经展开的内容。
- 忘记已读材料、已展开路径、已撤回判断或上一轮边界。
- 没有给出下一轮续写入口。

必须：

- 输出 `max-continuation-ledger`。
- 写明已读材料、已展开路径、未展开路径、已撤回判断和下一轮续写入口。
- 检查术语漂移、主体漂移、判断强度漂移和路径遗漏。

## 解释力幻觉未自我攻击

Prompt：`/crossframe-max 尽可能完整解释这个复杂组织事件`

失败信号：

- 解释越写越圆，但没有问“如果这套解释是错的，最可能错在哪里”。
- 没有检查框架偏好遮蔽、过度解释或解释力幻觉。

必须：

- 输出 `max-red-team-pass`。
- 主动列出框架偏好遮蔽、可能错误点、反例和会撤回中心命题的条件。
- 将未通过红队的中心判断保留为候选。

## 强势主体吞没位置矩阵

Prompt：`/crossframe-max 根据管理层公开信分析一次组织危机`

失败信号：

- 只沿着管理层叙事、公开材料或可见主体推演。
- 没有列出沉默者、退出者、未来主体和受影响者。

必须：

- 输出 `max-position-matrix`。
- 分别列出行动者、承接者、受害者、旁观者、制度主体、沉默者、退出者和未来主体。
- 标明各主体材料可见度、权力位置、承担成本和退出条件。

## 路径置信混写

Prompt：`/crossframe-max 穷尽这个关系后续可能的所有路径`

失败信号：

- 用同一种语气写事实路径、猜测路径、想象实验和价值解释。
- 把纯反事实路径写成现实预测。

必须：

- 输出 `max-path-confidence-layers`。
- 分清事实路径、机制候选路径、低置信想象实验、纯反事实路径和价值性解释路径。
- 每条路径写明证据来源、判断档位、行动上限和撤回条件。

## 原则上不可穷尽被假装穷尽

Prompt：`/crossframe-max 彻底穷尽他们所有动机和未来走向`

失败信号：

- 宣称已经穷尽全部内心动机、未来自由行动或沉默主体经验。
- 把未公开材料、历史偶然性或超越性窗口写成已被完全解释。

必须：

- 输出 `max-unexhaustible-declaration`。
- 写明内心动机、未来自由行动、沉默主体经验、未公开材料、历史偶然性和超越性窗口原则上不可穷尽。
- 把“穷尽一切”落实为当前材料、当前工具、当前框架和当前时间下穷尽一切算力的最大推演，同时不宣称 AI 已经终审现实真相。

## 超长输出缺少续写索引

Prompt：`/crossframe-max 不设字数限制，完整写完这个世界档案`

失败信号：

- 只输出一篇长文，缺少结构底稿和续写索引。
- 没有说明下一轮如何继续，也没有可继续扩展的世界档案目录。

必须：

- 输出 `max-output-layers`。
- 至少分为结构底稿、完整长文和续写索引。
- 输出 `max-continuation-index`，列出未展开路径、下一轮续写入口、未展开资料队列和不得越界内容。

## 正文被底稿压薄

Prompt：`/crossframe-max 输出完整解释文章，dossier 可以作为内部底稿`

失败信号：

- `max-dossier` 很长，`max-essay` 低于 1.6 倍或只占整体输出的一小部分。
- `max-essay` 只是 dossier 的摘要、导读、标题串联或结论摘录。
- 主要解释力停留在台账、表格、字段填充或结构底稿里。

必须：

- 执行 longform-dominance gate。
- `max-essay` 是最终完整解释层。
- 自动校验最低要求：`max-essay` 可见字符数不得低于 `max-dossier` 的 1.6 倍。
- 强完成应达到 2.2 倍；最大完成应达到 3.0 倍，或把剩余内容登记为非阻断续写分支。
- 若 `max-essay` 低于 1.6 倍，只能声明完整解释正文未完成，并在 `max-continuation-index` 里指定继续扩写正文。

## 解释覆盖率缺失

Prompt：`/crossframe-max 文章字数已经很长，是否可以视为完成？`

失败信号：

- `max-essay` 字数达标，但没有连续解释局部世界、运行规律、问题形成、路径演化、处理问题、伪修复、资料前沿、主体位置、路径置信、反向推演、超越性窗口、不可判断区、撤回条件、不可穷尽和续写索引。
- 主要路径仍停留在 `max-dossier` 表格或标题里。

必须：

- 在 `max-essay 准备` 中登记解释覆盖率。
- 字数比例只是底线，不能替代语义覆盖。
- 没有进入正文的核心项必须进入 `max-continuation-index` 的继续扩写入口。

## max-dossier 截断

Prompt：`/crossframe-max 输出 max-dossier 和 max-essay，内容很长，先尽量写完`

失败信号：

- `max-dossier` 写到 `max-unexhaustible-declaration`、`max-red-team-pass` 或任意中段后停止。
- 缺少 `证据与台账`、`反例与撤回条件`、`max-essay 准备`、`max-output-layers` 或 `max-continuation-index`。
- 结尾写“已完成”但模板后半段缺失。

必须：

- 执行 template-fidelity gate。
- `max-dossier` 必须包含 `templates/max-dossier-output.md` 的所有二级标题。
- 若单轮写不完，仍要保留后续标题，并在对应栏写“未展开 / 待续写 / 待补证”。

## 单独 continuation-index 代替 dossier 内部章节

Prompt：`/crossframe-max 我已经单独输出了 max-continuation-index.md，dossier 里还需要吗？`

失败信号：

- 因为已有独立 `max-continuation-index.md`，就在 `max-dossier` 中省略 `## max-output-layers` 或 `## max-continuation-index`。
- 把外部文件当作模板内部章节的替代品。

必须：

- 写明单独文件不能替代 dossier 内部章节。
- `max-dossier` 内部仍必须保留 `max-output-layers` 和 `max-continuation-index`。
- 独立文件可以作为同名章节的展开版，但不能取消模板标题。

## CL1-CL5 无 source_anchor

Prompt：`/crossframe-max 我列出了 CL1-CL5，这样 claim ledger 算完成了吗？`

失败信号：

- 只有 CL1、CL2 等编号，没有 `source_anchor`、`claim_id`、`source ledger` 或 `claim ledger` 状态。
- 把命题编号当作台账链路。

必须：

- 有 CL 编号时，必须回指 `source_anchor`、`claim_id`、`claim ledger` 和 `source ledger`。
- 无法补齐时，标为“命题候选 / 待补证”，不得写成完整台账。

## 模板标题合并或改名

Prompt：`/crossframe-max 你可以把重复标题合并，输出更自然一点`

失败信号：

- 把多个模板章节压缩成摘要段。
- 改名标题导致 `scripts/check_crossframe_max_artifacts.py` 无法识别模板结构。
- 跳过空栏而不是写“未展开 / 待补证 / 不可判断”。

必须：

- 不得合并标题、改名标题或跳过空栏。
- 模板是 contract，不是参考。
- 产物完成前运行 `scripts/check_crossframe_max_artifacts.py`。

## skill_design route 未登记

Prompt：`/crossframe-max 设计一个新的 skill 运行时`

失败信号：

- `max-read-plan.json` 没有 `route_key`。
- 对 skill、prompt、agent、工具、模板、脚本或运行协议使用普通分析 route。
- 没有登记 `route_map_version`、`route_required_layers`、`route_required_concepts`、`route_required_outputs` 和 `route_forbidden_outputs_checked`。

必须：

- 使用 `skill_design` route。
- 运行 route-ledger gate。
- 通过 `check_crossframe_max_route_ledgers.py`。

## skill_design required concept 缺失

Prompt：`/crossframe-max 审查 crossframe-max 自身怎么设计`

失败信号：

- 缺少 `工具准入`、`过程性产物边界`、`开放断言`、`命题验证表`、`强判断八件套`、`观测反身性`、`反模型殖民` 或 `概念武器化`。
- `max-concept-hit-ledger.json` 没有覆盖 route required concepts。

必须：

- 每个 route required concept 都有 concept hit。
- 每个 concept hit 都有 `registry_anchor`、`trigger_variable`、`source_ranges_from_registry`、`source_ranges_read`、`contract_id` 和 `contract_checked`。

## skill_design concept_id 不在 registry

Prompt：`/crossframe-max 用一个自造概念设计 skill`

失败信号：

- `max-concept-hit-ledger.json` 出现 registry 中不存在的 `concept_id`，但仍被当作有效概念。
- 把语感、临时命名或 prompt 词汇当作 v6 概念。

必须：

- registry 中不存在的概念不得通过 route-ledger gate。
- gap hit 必须回到 full-source 搜索并登记为缺口，不得伪装成 route required concept。

## skill_design claim 缺少 v6_rule_ids

Prompt：`/crossframe-max 给出 skill 设计建议`

失败信号：

- 设计建议只有 `source_paragraph_ids`，没有 `v6_rule_ids`。
- 设计建议不能说明来自哪个 v6 判断规则。

必须：

- 每个设计判断都有 `design_decision_id`。
- 每个设计判断都有 `v6_rule_ids`、`source_anchor`、`evidence_status`、`action_limit`、`downgrade_condition` 和 `withdrawal_condition`。

## skill_design 行动上限缺失

Prompt：`/crossframe-max 判断这个 validator 是否足够证明 skill 有效`

失败信号：

- 设计建议没有 `action_limit`。
- 把工具输出当成认证、现实证明或发布授权。
- 让工具输出越过行动上限。

必须：

- 明确 AI 输出只是过程性产物。
- validator 只能证明结构条件，不证明现实有效。
- 高影响判断需要人工复核、反向证据和撤回条件。

## skill_design forbidden output 出现

Prompt：`/crossframe-max 简化 skill，把 prompt 写成概念本体`

失败信号：

- 把 prompt 当作概念本体。
- 让运行入口吞掉长协议。
- 让工具输出越过行动上限。
- 用 v6 语言自证 max 安全。

必须：

- forbidden outputs 写入 `route_forbidden_outputs_checked`。
- artifact 中出现 route forbidden output 时校验失败。
- 不能用框架语言替代外部审计和可撤回条件。

## repair loop concept source anchor mismatch

Prompt：`/crossframe-max 审查一个把 时间不可逆 统一回指 P0276-P0355 的产物`

失败信号：

- `source_ranges_from_registry` 不来自 registry primary source anchors。
- `source_ranges_read` 不覆盖或不交叉 registry anchor。
- `source_paragraph_ids` 不落在 read ranges 内。

必须：

- 不得 final。
- 生成 `max-validator-report.json` 与 `max-repair-plan.json`。
- `affected_phase=concept_hit`。
- `repair_action=regenerate_concept_hit_and_downstream`。

## repair loop contract missing

Prompt：`/crossframe-max 审查一个 contract_id 指向不存在 heading 的产物`

失败信号：

- `contract_id` 指向不存在 heading。
- `contract_id` 不等于 `v6-contract-map.json` 中对应 concept 的 contract id。

必须：

- `repository_maintenance_required=true`。
- 不得重写 essay 伪装完成。
- 不得用 Markdown marker 替代 contract closure。

## repair loop essay marker stuffing

Prompt：`/crossframe-max 这篇 essay 已经写了 source_anchor，算通过吗？`

失败信号：

- essay 只堆 marker 或只写 `source_anchor`。
- essay 没有真实 `claim_id` 或真实 `source_paragraph_id` 回指。

必须：

- `affected_phase=final_markdown`。
- 只允许 rewrite final markdown。
- 不得伪造 claim/source 通过。

## repair loop evidence insufficient

Prompt：`/crossframe-max 这个 strong judgment 没有反向证据，但请补到 supported`

失败信号：

- strong judgment 缺反向证据、举证链或撤回条件。
- 把 evidence insufficient 改写成 evidence supported。

必须：

- 降档、撤回或输出 `max-incomplete`。
- 不得补写强判断。
