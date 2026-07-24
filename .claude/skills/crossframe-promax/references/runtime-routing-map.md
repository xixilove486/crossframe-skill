# ProMax 运行与工件路由图

本图只说明 v8 运行时的阶段、工件依赖和生成权限，不提供新的理论定义。激活权由上游显式路由器决定；进入运行后，以 `schemas/`、`scripts/promax_runtime/` 和当前冻结工件为准。

## 阶段路由

| 阶段 | 必须完成的责任 | 当前工件 |
| --- | --- | --- |
| `P0` | 冻结请求、能力、档位、角色计划和源绑定 | `promax-run-contract.json`、`promax-source-snapshot.json`、初始 `promax-phase-events.jsonl` |
| `P1` | 校验源与知识图，并登记逐项读取 | `promax-read-events.jsonl` |
| `P2` | 完成全源连续读取并形成运行胶囊 | `promax-worldview-capsule.locked.md` |
| `P3` | 冻结对象、行动者、圈层候选、尺度、双通道、时钟、事件和未知项 | `promax-local-world-model.locked.json` |
| `P4` | 给全 registry 概念终态并完成 route/neighbor closure | `promax-concept-disposition-ledger.json` |
| `P5` | 建立中心 claim、竞争机制、路径 DAG、前瞻条件与选择边界 | `promax-claim-path-graph.json` |
| `P6` | 完成五向检索和连续两轮无实质新增的饱和记录 | `promax-retrieval-ledger.json` |
| `P7` | 完成十二类攻击、最强反方和成对立场稳定性检查 | `promax-red-team-report.json` |
| `P8` | 在攻击后冻结立场、行动上限和建议分支 | `promax-position.locked.json`、`promax-recommendation.locked.json` |
| `P9` | 把全部 applied 概念、claims、案例、反例和判断映射到交付章节 | `promax-output-plan.locked.json` |
| `P10` | 生成完整交付，清点当前字节并绑定续跑 | 四份长文、`promax-continuation-index.md`、manifest、continuation ledger |
| `P11` | 运行完整验证集；失败时建立最早受影响阶段的局部修复 | validator report；失败时另有 repair plan |

## 生成权限

以下控制平面必须由确定性运行函数产生，不得用散文或模型自报替代：

- `promax-run-contract.json`
- `promax-source-snapshot.json`
- `promax-read-events.jsonl`
- `promax-phase-events.jsonl`
- `promax-continuation-ledger.json`

以下结果同样必须由运行时计算散列和闭合字段：

- `promax-artifact-manifest.json`：使用 `inventory_artifacts()` 与 `build_artifact_manifest()`。
- `promax-validator-report.json`：使用工件检查器或 `build_validator_report()`。
- `promax-repair-plan.json`：使用 `build_repair_plan()` 或对应 CLI。

模型负责构造 local world、概念处置、claim/path、检索、red-team、position、recommendation、output plan 以及 Markdown 长文的语义内容。写盘前先读同名模板；写盘后必须通过 schema 与跨工件语义校验。

## 固定依赖

1. 宿主完成 ProMax 选择后，直接对全新 run 目录执行 `init`；运行时不重新判定激活。
2. 每一阶段只读取 run contract 允许的冻结输入；角色交换协议固定为 `structured-artifacts-only`。
3. `P4` 的 applied 概念集合必须与 `P9` 的 concept IDs 双向相等。
4. `P5` 的全部 claim IDs 必须与 `P9` 双向相等；案例 ID、反例 ID 和判断 ID 也必须闭合。
5. `P8` position 必须晚于 `P7`，recommendation 必须晚于 position，并绑定 position 的规范 JSON 散列。
6. `P10` manifest 只登记当前分析工件；run contract、manifest 自身、continuation ledger、phase events、validator report、repair plan 和 final chat 不进入其 current inventory。
7. continuation 必须绑定当前 manifest 和一个当前 `P10` 父工件；待交付路径不得已是 current artifact。
8. 任一上游工件改变后，旧 manifest、旧 validator report 和其下游冻结工件立即失效。

## 可执行入口

```text
python skills/crossframe-promax/scripts/crossframe_promax_runtime.py init --repo <仓库根目录> --run-dir <新工件目录> --request <原始请求> --mode promax-artifact-run
python skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py --workspace <工件目录> --repo <仓库根目录> --write-report --json
```

建议需求、网络和隔离子代理能力只通过 `init` 的真实参数冻结。不得在后续工件中把不可用能力改写为已执行。

## 重置路由

验证错误必须保留 `error_type`、`artifact`、`affected_phase`、`downstream_reset`、`repair_action`。以最早 `affected_phase` 为 `reset_from_phase`，追加 reset event，重建该阶段及其后代，重新生成 manifest，把 validation 置为 `not_run`，再运行完整验证集。不得覆盖历史事件、只改报告或只补关键词。
