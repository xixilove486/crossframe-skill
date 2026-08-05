# Ultra 有界修复计划输出

本模板用于 U12 validation 失败后的 bounded local repair plan。repair 只能从最早受影响阶段开始，并保留仍可由散列证明的上游工件。

## failed attempt

记录 failed report sha256、attempt number 和稳定 error code；不得用调用方声明代替失败报告。

| artifact | affected phase | repair action | downstream reset | retryable |
|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 |

## reset 边界

reset from phase 必须等于所有失败项中最早的受影响阶段；downstream reset 只覆盖依赖 DAG 中真正受影响的阶段，不做全量重跑。

## bounded 执行

列出 preserved artifact hashes、manifest 是否重建、是否重新验证和本次 bounded repair 的停止条件。达到重试或资源边界时进入 needs_attention，不得冒充 complete。
