# ProMax 正文技法路由

本表把九种体裁的读者任务映射到小型技法组合。路由只决定 P9 到 P10 的表达选择，不新增论证材料，也不改变上游锁定结果。

## 单次选择规则

- 每个 `genre_id` 只有一条主路由，主路由恰有 3 张 `core` 卡。
- `selected_techniques` 先按本表顺序记录 3 张 core，再记录 0–2 张 auxiliary；顺序也是契约的一部分。
- `auxiliary_candidates` 是候选池，不是一次性装载清单。
- 单次 P9 选择必须使用该路由的 3 张 core；auxiliary 只能选 0–2 张。
- core 与 auxiliary 合计不得超过 5 张。若候选卡解决不了当前读者问题，宁可不用辅助卡，也不为凑数套技法。
- 同一段原则上只安排一个主动作；多个技法发生冲突时，以表达更朴素、证据关系更清楚者为准。
- 所有选择只影响表达，不改变 P8 锁定的事实、命题、证据、判断与授权。

## 路由：reply-main

- genre_id：`reply`
- core：`direct-emotion`、`winding-path`、`less-is-more`
- auxiliary_candidates：`analogical-reasoning`、`retreat-to-advance`、`scene-emotion`、`feint-attack`、`hide-before-reveal`、`sparse-outline`
- 选择提示：回应先确认对方真正关心的现实关系，再给当前判断；若分歧来自概念误解选类比，若来自证据边界选退界，若需要降低对抗感选曲径。

## 路由：public-commentary-main

- genre_id：`public-commentary`
- core：`event-association`、`layered-argument`、`positive-negative-contrast`
- auxiliary_candidates：`ancient-modern-global`、`language-momentum`、`guest-host-contrast`、`point-surface`、`praise-blame-interlace`、`finishing-touch`
- 选择提示：公共评论必须把热点放回机制与成本分配；辅助卡只在需要时间纵深、主次换位或短促收束时加入。

## 路由：concept-explanation-main

- genre_id：`concept-explanation`
- core：`analogical-reasoning`、`split-wood-reasoning`、`virtual-to-real`
- auxiliary_candidates：`double-bridge`、`form-by-object`、`object-reason`、`one-word-spine`、`symbolic-meaning`、`personified-object`
- 选择提示：先沿对象真实纹理拆开概念，再以有限类比降低门槛，最后落到可观察关系；拟物或象征必须随即还原真实行动者。

## 路由：organization-review-main

- genre_id：`organization-review`
- core：`vertical-narration`、`fixed-point-changing-scenes`、`moving-viewpoint`
- auxiliary_candidates：`clouds-moon`、`life-from-dead`、`motion-for-stillness`、`praise-blame-interlace`、`form-by-object`
- 选择提示：组织复盘优先追踪决定的纵向传递，并从不同角色查看信息与成本；辅助卡用于显出低可见机制或区分忙碌与进展。

## 路由：case-analysis-main

- genre_id：`case-analysis`
- core：`narration-commentary`、`fine-carving`、`point-surface`
- auxiliary_candidates：`coincidence-structure`、`point-spirit`、`scene-emotion`、`suspense`、`guest-host-contrast`
- 选择提示：案例先保持事件可复原，再在高区分度节点评论，最后用总体材料校准代表性；悬置答案不得隐瞒决定性事实。

## 路由：debate-refutation-main

- genre_id：`debate-refutation`
- core：`feint-attack`、`positive-negative-contrast`、`release-to-capture`
- auxiliary_candidates：`raise-high-drop-heavy`、`retreat-to-advance`、`same-different`、`one-stone-many-birds`、`remove-foundation`
- 选择提示：反驳先给对方最强版本，再检验承重前提；能撤回的过宽主张应主动撤回，不用语势或讥讽替代证据。

## 路由：reading-synthesis-main

- genre_id：`reading-synthesis`
- core：`thread-beads`、`one-word-spine`、`narration-commentary`
- auxiliary_candidates：`final-reveal`、`meaning-beyond-words`、`stars-moon`、`stream-consciousness`、`symbolic-meaning`
- 选择提示：综合写作以一个问题串材料，以稳定关键词维持纵线；言外义、象征与认识过程都要保留解释级别，不能伪装成原材料明说。

## 路由：trend-deduction-main

- genre_id：`trend-deduction`
- core：`small-water-waves`、`multi-edge-extension`、`ancient-modern-global`
- auxiliary_candidates：`coincidence-structure`、`event-association`、`motion-for-stillness`、`surprise-victory`、`fixed-point-changing-scenes`
- 选择提示：趋势推演从微小信号写清传播路径，同时展开竞争关系边；辅助卡用于区分巧合、重复、活动量和真正结构变化。

## 路由：neutral-analysis-main

- genre_id：`neutral-analysis`
- core：`layered-argument`、`same-different`、`one-stone-many-birds`
- auxiliary_candidates：`release-to-capture`、`point-surface`、`less-is-more`、`multi-edge-extension`、`virtual-to-real`
- 选择提示：中性分析不是无判断，而是把事实、机制、规范和行动分层，并让同一标准约束各候选解释；结论应随证据收窄。

## P9 记录要求

P9 对每个实际选用技法记录 `genre_id`、`technique_id`、目标段落和要解决的读者问题。未选中的候选卡不进入正文动作。若技法与事实准确性、反方完整性、撤回条件或行动边界冲突，删除技法而不是修改锁定内容。
