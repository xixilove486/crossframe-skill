---
name: crossframe-max
description: "Use when the user explicitly invokes crossframe-max, /crossframe-max, $crossframe-max, maximum CrossFrame mode, exhaustive structural projection, full-scale world-model interpretation, no word-limit complete explanation, or v6 meta-runtime design review for skills, prompts, agents, tools, templates, scripts, and runtime protocols. explicit-only."
disable-model-invocation: true
---

# CrossFrame Max

`crossframe-max` 是 CrossFrame v6 世界观前置的 meta-runtime。它不是超长回答模板，也不是省略式诊断模板；它先让 AI 拥有用户预先设计的世界观，再把对象当作局部世界建模，在材料、工具、上下文和行动边界内完成最大推演、校准回合、举证推理、反向证据、产物交付和续写索引。

## max-clean-runtime-entry

运行入口保持正向、精简：`SKILL.md` 只放触发边界、运行档位、必读顺序、交付闸门和校验命令。失败样本和反例压力测试放在 `evals/`；长细则放在 `protocols/`、`templates/` 和脚本。

## 触发边界

这是 explicit-only skill。只有用户明确要求 `crossframe-max`、最大尺度、穷尽推演、完整解释、无限制长文、全尺度世界观解释，或明确要求用 v6 meta-runtime 审查 skill、prompt、agent、工具、模板、脚本、运行协议时使用。

## 运行档位

- `max-complete`：完整 full-source exhaustive pass、阶段锁、artifact-first、template-fidelity、longform-dominance 和 validator 全部满足后才可宣称完成。
- `max-design-review`：用于 skill、prompt、agent、工具、模板、脚本和运行时设计。必须使用 `skill_design` route，登记 `route_key`、route concepts、design decision、v6 rule、反向证据、撤回条件和行动上限；不得伪称完整 max 长文完成。
- `max-incomplete/progress`：上下文、权限、工具或时间不足时，只输出读态、缺口、下一步读取计划和 `max-incomplete:*`，不得宣称完成。

## 世界观层先行

第一动作是建立 `max-worldview-capsule`。先加载 v6 全量分层源库作为本轮预先设计的世界观，再进入局部世界建模、概念命中、证据审计、路径推演和正文生成。

执行时必须把对象当作一个局部世界来对待：

- 先做局部世界建模，再做判断。
- 先识别运行规律，再定位问题。
- 先查 registry 再读 full-source。
- 先完成举证链、推理链、反向证据和证据-推理-反例-降档循环，再进入最终表达。
- 先保留撤回条件、行动上限和不可穷尽声明，再写完整长文或设计审查结论。

## 必读顺序

1. `protocols/max-worldview-protocol.md`
2. `protocols/max-repair-loop-protocol.md`
3. `references/source_manifest.json`
4. `references/v6-route-map.yaml`
5. `references/concept-registry/index.md`
6. `references/concept-contracts/v6-core-contracts.md`
7. `references/concept-contracts/v6-contract-map.json`
8. `references/retrieval-trigger-policy.md`
9. `references/v6-full-source/00-index.md`
10. `references/v6-full-source/00-heading-index.md`
11. `references/v6-full-source/00-term-index.md`
12. `references/v6-full-source/00-table-index.md`
13. route 指定的 v6 full-source 分层文件与 `tables/`
14. `templates/` 中本轮产物对应 contract
15. `scripts/` 中对应 validator

任务路由以 `references/v6-route-map.yaml` 为准。route map 只决定阶段读取顺序，不能降低最终 full-source exhaustive pass 要求。概念注册表只做定位、别名、邻域和触发，不替代 full-source。

## 阶段锁

完整运行必须依次冻结：

- `max-run-contract.json`
- `max-read-plan.json`
- `max-source-snapshot.json`
- `max-worldview-capsule.locked.md`
- `max-local-world-model.locked.md`
- `max-claim-board.json`
- `max-audit-board.json`
- `max-output-plan.locked.md`

没有 `max-output-plan.locked.md`，不得生成 `max-essay.md`。后续阶段不得直接改写前序冻结产物；异常登记为 `phase_exception_record`，并按 `affected phase reset` 回到受影响阶段。

## 校验失败后的 repair loop

validator failure 不等于整轮重写。必须先生成 `max-validator-report.json`，再生成 `max-repair-plan.json`。

repair plan 必须登记 `error_id`、`error_type`、`severity`、`artifact`、`field`、`affected_phase`、`downstream_reset`、`repair_action`、`retry_count`、`final_output_allowed`。只允许重建 `affected_phase` 及其 downstream artifacts。

不得为了通过 validator 补 marker、伪造 `source_anchor`、伪造 `claim_id`、伪造 `source_paragraph_ids`，或把 evidence insufficient 写成 supported。若 repair plan 的 `final_output_allowed=false`，不得输出 final chat，只能执行受控重建、降档、撤回或输出 `max-incomplete/progress`。

## 必建模块

完整运行必须生成并互相回指：

- `max-worldview-capsule`
- `max-local-world-model`
- `max-concept-graph`
- `max-scale-map`
- `max-source-frontier`
- `max-position-matrix`
- `max-path-tree`
- `max-path-confidence-layers`
- `max-evidence-reasoning-audit`
- `max-red-team-pass`
- `max-transcendence-window`
- `max-unexhaustible-declaration`
- `max-output-layers`
- `max-continuation-ledger` / `max-run-state`
- `max-continuation-index`
- `max-dossier`
- `max-essay`

## 结构化台账

最终产物必须生成：

- `max-read-ledger.json`
- `max-claim-ledger.json`
- `max-concept-hit-ledger.json`
- `max-evidence-reasoning-audit.json`
- `max-validator-report.json`：每次 validator 运行后的机器可读报告；失败时必建，成功时可建。
- `max-repair-plan.json`：validator 失败后的修复计划；只在失败时必建。

`max-read-plan.json` 必须登记 `route_key`、`route_map_version`、`route_required_layers`、`route_required_concepts`、`route_required_outputs`、`route_forbidden_outputs_checked`。`skill_design` route 的设计判断必须登记 `design_decision_id`、`v6_rule_ids`、`action_limit`、`source_anchor`、`counterevidence`、`withdrawal_condition`。

Markdown 章节不能替代 JSON 台账。source paragraph id 必须存在于 v6 full-source；route concepts 必须来自 concept registry；强判断、设计建议和行动路径必须有反向证据、降档条件、撤回条件和行动上限。

通过 final validation 时，`max-repair-plan.json` 可以不存在；只要 validation failed，就必须存在，且 `final_output_allowed=false`。

## 资料前沿

涉及真实机构、公共事实、历史事件、法律政策、平台规则、技术标准、人物、公司或最新情况时，主动检索与反向检索并行。运行时读取 `references/retrieval-trigger-policy.md`，区分内部概念检索和外部事实检索。资料穷尽不等于现实穷尽，不能假装穷尽现实真相。

## 产物优先硬闸

完整输出先写入产物目录，再给聊天索引。最低产物：

- `max-artifact-manifest.md`
- `max-dossier.md`
- `max-essay.md`
- `max-continuation-ledger.md`
- `max-continuation-index.md`
- 全部阶段锁文件
- 全部结构化台账

文件必须分开交付；完整文章必须单独放在 `max-essay.md`。最终聊天回复承担交付索引和继续讨论入口功能，并列出可继续讨论的分支。

## 模板与校验

执行：

- `artifact-first gate`
- `template-fidelity gate`
- `longform-dominance gate`
- `route-ledger gate`

正文完整性按三档判断：

- 最低通过：`max-essay` 可见字符数至少达到 `max-dossier` 的 1.6 倍。
- 强完成：`max-essay` 至少达到 2.2 倍，并把主要路径写入连续解释。
- 最大完成：`max-essay` 至少达到 3.0 倍，或剩余内容只属于非阻断续写分支。

交付前运行：

```bash
python scripts/check_crossframe_max_artifacts.py --workspace <artifact-dir>
python scripts/build_crossframe_max_repair_plan.py --workspace <artifact-dir> --write-report --write-repair-plan
```

源库维护或发布前运行：

```bash
python scripts/check_crossframe_max_v6_full_source.py --repo <repo> --source-docx <v6-docx> --allow-source-path-mismatch
python scripts/check_crossframe_max_v6_registry_anchors.py --repo <repo>
python scripts/check_crossframe_max_route_ledgers.py --workspace <artifact-dir>
python scripts/validate_crossframe_max_route_ledger_fixtures.py
python scripts/validate_crossframe_max_repair_fixtures.py
```

未完成全量读取、route-ledger、举证推理、阶段锁或 artifact validation 时，只能输出 `max-incomplete:*`，不得宣称完成。
