# CrossFrame Suite Smoke Tests

## 1. 普通洞察文章

Prompt：写一篇“解释劳动为什么会耗竭”的文章。

期望：

- 工作流包含 `crossframe -> crossframe-essay -> crossframe-review`。
- 如果识别为关系困惑，可按需加入亲密关系协议，但不强行加入 `crossframe-public`。
- 必须先有结构洞察底稿。
- 输出档位必须是 `full-visible-v5-longform`。
- 底稿完整可见，正文默认完整长文，不得只有短答或项目符号。
- 正文声口默认是现代编辑底色，不能只输出诊断提纲或概念说明。
- 最后过 `crossframe-review` 时，不得只输出质量闸或评审报告；最终仍必须可见 `结构洞察底稿` 和 `文章正文`。

## 2. 公共评论

Prompt：写一篇“平台申诉为什么可能只是表面治理”的公共评论。

期望：

- 工作流包含 `crossframe -> crossframe-public -> crossframe-essay -> crossframe-review`。
- 必须查源或声明需要查源。
- 不能让检索材料接管文章命题。
- 正文用评论体，亲切但能严厉批评表演性治理。
- 正文不能被公共证据台账压缩成报告摘要；仍要有文章推进和余味。

## 2.1 哲学概念长文回归

Prompt：生命的第一因是什么？

期望：

- 工作流包含 `crossframe -> crossframe-essay -> crossframe-review`。
- 输出档位是 `full-visible-v5-longform`。
- 不查源，除非用户要求科学材料。
- 底稿完整可见：科学层、结构层、意义层；机制候选至少两个；边界清楚。
- 正文有标题、铺陈、生命/边界/反馈/回应的递进、概念上升和余味结尾。
- 不机械退出为“不可诊断”，也不压缩成“如果只要一句话”的短答。

## 3. 组织修复

Prompt：给这个项目失败写组织修复备忘录，再转成一篇给内部看的文章。

期望：

- 工作流包含 `crossframe -> crossframe-org -> crossframe-essay -> crossframe-review`。
- 先输出组织备忘录所需结构，再成文。
- 检查责任链、授权链、反馈写回。

## 4. 答读者问

Prompt：像编辑回信一样回答“是不是我太敏感”。

期望：

- 工作流包含 `crossframe -> crossframe-dialogue -> crossframe-essay -> crossframe-review`。
- 默认进入 `full-visible-v5-longform`，先短答接住问题，再扩成完整文章。
- 不把修复责任压回提问者。

## 4.1 显式短答关闭文章

Prompt：像编辑回信一样回答“是不是我太敏感”，只要三句话短答，不要文章。

期望：

- 因用户明确说“只要三句话短答，不要文章”，工作流才允许包含 `crossframe -> crossframe-dialogue -> crossframe-review(lite)`。
- 不追加 `crossframe-essay`。
- 输出档位标明“显式短答，关闭文章层”。

## 5. 读书后成文

Prompt：读这篇文章，写与 CrossFrame 的关联与不同，并扩成一篇思想文章。

期望：

- 工作流包含 `crossframe -> crossframe-notebook -> crossframe-essay -> crossframe-review`。
- 先比较关联、不同、可吸收处和冲突处，再成文。
- 不伪造引用。

## 6. 辩论后成文

Prompt：先检验“所有制度问题都是反馈问题”这个命题，再写一篇文章。

期望：

- 工作流包含 `crossframe -> crossframe-debate -> crossframe-essay -> crossframe-review`。
- 必须列隐藏前提、最强反驳和撤回条件。
- 文章不能把命题写成绝对真理。

## 7. 只评审

Prompt：评审这段 CrossFrame 输出是否合格。

期望：

- 工作流包含 `crossframe-review -> crossframe-essay -> crossframe-review(lite)`。
- 先输出评审对象、事实边界、失败点和修复建议，再默认形成文章式综合。
- 若用户说“只要评审，不要文章”，才停在 `crossframe-review`。

## 7.1 只评审关闭文章

Prompt：只评审这段 CrossFrame 输出是否合格，不要生成文章。

期望：

- 工作流为 `crossframe-review`。
- 不追加 `crossframe-essay`。
- 输出档位标明“原始评审，关闭文章层”。

## 8. 过度触发失败

Prompt：写一篇普通关系文章。

失败表现：

- 同时读取全部 sibling skill。
- 把案例库、公共制度、组织修复、读书笔记全部列入必读。

期望：

- 只读取必要链路。
- 在“不读取”中说明至少两个未触发 skill。

## 9. 模式/角色选择器压缩失败

Prompt：`/crossframe-suite` 后只输入主题，没有给 `2+1` 或任何模式/角色触发词。

失败表现：

- 只写“请选择模式/角色”或“请回复数字”。
- 直接采用默认 `2+1` 开始分析。
- 在开头同时询问文章类型。

期望：

- 完整渲染 4 个输出模式和 6 个角色选项。
- 明确默认推荐是 `2+1`，但必须等用户回复“默认/直接开始/随便/都行/不用选”才采用。
- 开头不展示文章类型；文章类型必须晚于结构洞察底稿。

## 10. 胶囊与文章类型全链路

Prompt：用户先回复 `2+1`，再要求写一篇公共评论，但未指定文章类型。

期望：

- suite 不生成 `v5-read-state-capsule`，只传 `selection_state`、`workflow_state`、`voice_mode` 和文章层状态。
- `crossframe` 生成 `v5-read-state-capsule`，包含 source modules、入口包、必须同读闭包、相邻候选和下游读取策略。
- 成文前执行源锚点完整性检查。
- 成文前必须生成或复用 `claim ledger`，并在结构洞察底稿中显示命题台账摘要。
- 文章正文必须能把中心命题、机制句、高风险概念句、行动建议和点睛句回指到 `claim_id`。
- review 必须抽取至少 1 条命题台账候选，检查是否无 `claim_id` 或强于台账。
- 结构洞察底稿之后完整展示 9 项文章类型选择器，带推荐项和推荐理由。
- review 只做质量闸摘要，不吞掉 `结构洞察底稿` 和 `文章正文`。

## 11. 批量压测控制器口径

Prompt：控制器批量调用 9 个 suite 任务，已显式指定 `2+1` 和文章类型，只做文件级流程完整性汇总。

期望：

- 每篇结果记录 `selection_state: controller-specified`，文章类型来源为控制器显式指定，不再写“待选择”。
- 控制器汇总必须拆分 `structural_pass`、`substantive_pass`、`publish_boundary`。
- 只做标题、底稿、正文、胶囊、来源台账、技法和质量闸存在性检查时，只能标 `structural_pass=true`。
- 不得写“全部通过/可发布”，除非已完成反向否决最小块、来源台账字段校验、技法落地证据和正文抽句回指。

失败表现：

- 把文件级 smoke check 写成总通过。
- 高责任公共事件、事故、法律政策或 AI 合规样稿只有单一来源族仍给 A 档发布结论。
- 技法只列名字、胶囊只写“闭包已读完”，但控制器仍判实质合格。

## 12. 完成态后续输入接管

Prompt：用户先显式调用 `/crossframe-suite`，选择 `2+1`，完成结构分析、文章正文和 `crossframe-review`。下一轮用户只说“继续”或“那我呢？”。

期望：

- 完整链路交付后记录 `post_completion_inquiry_armed=true`。
- 下一轮用户的实质后续输入默认进入 `crossframe-inquiry`，不要求用户再次说“继续追问”。
- 不重新默认进入 `crossframe-essay`，不再生成一篇新文章。
- `crossframe-inquiry` 必须复用上一轮 claim ledger、机制候选、概念契约、source ledger、结构洞察底稿、文章正文和 review warning。
- 只有用户明确说“新任务 / 换主题 / 退出追问 / 不接着上文”时，才解除完成态接管。

## 12.1 完成态纯致谢/纯确认不追问

Prompt：用户先显式调用 `/crossframe-suite`，选择 `2+1`，完成结构分析、文章正文和 `crossframe-review`。下一轮用户只说“谢谢，先这样”。

期望：

- 不自动展开 `crossframe-inquiry`。
- 不生成新的 3-5 个追问问题。
- 对纯致谢、确认收到、结束语或无内容回应，只轻量收束或结束本轮。
- 若用户随后再次提出与上一轮相关的问题，再重新触发 `crossframe-inquiry`。

## 13. crossframe-max 让路

Prompt：`/crossframe-suite` 后用户说“改用 crossframe-max，把这件事当作局部世界做全尺度推演，不设字数限制”。

期望：

- 不渲染 `2+1` 模式/角色选择器。
- 不进入普通文章类型选择器。
- 直接转交 `crossframe-max -> crossframe-review`。
- 明确 `crossframe-max` 是独立模式，不是 suite 的体积档位。

## 14. CrossFrame ProMax 精确优先

责任标记：`PROMAX-NAMED-ONLY`、`PROMAX-PRIORITY-OVER-MAX`、`PROMAX-NO-FALLBACK-TO-MAX`、`PROMAX-GENERIC-MAX-STAYS-MAX`。

Prompt A：同时使用 `crossframe-max` 和 `CrossFrame ProMax`，失败时改用 Max。

期望：

- 直接读取 `skills/crossframe-promax/SKILL.md`，不启动 suite 选择器，不串接 review。
- ProMax 优先；Max 只作为已解决的冲突名称记录。
- 验证失败仍留在 ProMax 状态。

Prompt B：请用最大算力完整解释，但未说四种 ProMax 名称。

期望：维持既有 Max 路由，不升级为 ProMax。

Prompt C：分别使用 `ProMax`、`crossframe pro max`、`crossframe-promaxx`、`crossframe-pro`。

期望：四个近似名称均不命中 ProMax。
