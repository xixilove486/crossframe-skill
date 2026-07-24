# 快速开始

## 1. 安装到 Codex

在仓库根目录运行：

Windows PowerShell：

```powershell
.\scripts\install-codex.ps1
```

macOS / Linux：

```bash
bash scripts/install-codex.sh
```

它会安装 16 个 `crossframe-*` skills 到 `$HOME/.codex/skills`。

## 2. Claude Code

Claude Code 项目内使用：

```text
/crossframe-suite 分析这个团队为什么复盘很多但没有真实修复
/crossframe-max 把这件事当作一个局部世界，做全尺度结构推演并写完整解释
/crossframe-promax 用 v8 框架穷尽分析这个判断，主动搜索反例并给出明确立场
/crossframe-essay 写一篇关于平台治理的中文评论文章
/crossframe-inquiry 基于刚才的文章继续追问反证和迁移条件
```

需要迁移到别的项目时，复制：

```text
.claude/skills/crossframe*
.claude/commands/crossframe*.md
CLAUDE.md
skills/crossframe*
```

## 3. 其他 AI 工具

不支持 skill 文件夹的工具，可以先读取对应薄入口：

```text
AGENTS.md
CLAUDE.md
GEMINI.md
llms.txt
docs/ADAPTERS.md
```

效果最好的是完整保留 `skills/crossframe*` 目录，因为真实规则、协议、模板和检查表都在 skill 主体里。

CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。

## 4. 本地验证

公开仓库日常验证不需要本机私有 DOCX：

```bash
python scripts/check_crossframe_skill_integrity.py --repo .
python scripts/check_source_continuity.py --materials-only --repo .
python -m json.tool skills/crossframe/schemas/claim-ledger.schema.json
python -m pip install jsonschema
python scripts/validate_claim_ledger_schema_fixtures.py --repo .
python scripts/validate_v5_dlc_quantification_schema_fixtures.py --repo .
python scripts/check_v5_dlc_casebook_trials.py --repo .
python scripts/check_v5_dlc_publication_bundle.py --repo .
python scripts/check_crossframe_max_v6_full_source.py --repo .
python scripts/check_crossframe_max_v6_registry_anchors.py --repo .
python scripts/validate_crossframe_max_route_ledger_fixtures.py
python -m json.tool skills/crossframe-max/schemas/max-validator-report.schema.json
python -m json.tool skills/crossframe-max/schemas/max-repair-plan.schema.json
python scripts/validate_crossframe_max_repair_fixtures.py
python scripts/sync_skill_mirrors.py --check
bash -n scripts/install-codex.sh
python -m py_compile scripts/*.py
git diff --check
```

`check_v5_dlc_casebook_trials.py` 只检查 v5 DLC 案例库试跑是否保留降档、分歧、反例和反误用边界；它不是发布证明，也不是现实正确性证明。

生成 v5 DLC 发布 bundle：

```powershell
python scripts\build_v5_dlc_publication_bundle.py --repo .
```

生成 v5 DLC DOCX 发布稿：

```powershell
python scripts\build_v5_dlc_docx.py --repo .
```

`check_v5_dlc_publication_bundle.py` 会生成 ignored `outputs/` bundle 并核对 manifest、章节、来源引用和反误用语言；通过只说明发布源稿结构可审计，不说明现实判断正确。

如果你持有原始 v5.0 DOCX，可以运行完整源一致性检查：

```powershell
python scripts\check_source_continuity.py --version v5 --source-docx <path-to-v5-docx> --repo .
```

## 5. Max 校验失败怎么办

validator failed 后不要直接重写完整回答。运行：

```bash
python scripts/build_crossframe_max_repair_plan.py --workspace <artifact-dir> --write-report --write-repair-plan
```

它会生成：

- `max-validator-report.json`
- `max-repair-plan.json`

根据 repair plan，只重建受影响阶段及其下游；修复前把 failed contract 重置为 `not_run`，修改分析产物后重写 manifest。strict-only 缺口使用 `mark_artifact_incomplete`，证据不足时降档或撤回。只有 fresh passed complete report 可以宣称 `max-complete`。
