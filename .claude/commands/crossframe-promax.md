# /crossframe-promax

`PROMAX-NAMED-ONLY`：只有 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax`、`/crossframe-promax` 四种明确名称具有触发权。

`PROMAX-PRIORITY-OVER-MAX`：若输入同时点名 ProMax 与 Max，本命令选择 ProMax 并完成冲突记录；进入 skill 后不再复判。

`PROMAX-NO-FALLBACK-TO-MAX`：进入后始终执行 ProMax 独立 v8 artifact workflow；材料、能力或验证缺口只影响 ProMax 自身状态。

本命令被调用就表示宿主已经完成 ProMax 选择；不要再次检查 `$ARGUMENTS` 是否含技能名。读取唯一 canonical 入口 `skills/crossframe-promax/SKILL.md`，把下列问题正文直接传给生产 `init -> prepare -> materialize -> checker` 流程。不要启动 suite 的模式/角色/文章选择器，不要串接 sibling workflow。

User input:

`$ARGUMENTS`
