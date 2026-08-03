# Ultra 工件索引输出

本模板用于 delivery/工件索引.md 的人类可读投影。权威 artifact manifest 由 runtime 生成并验证；索引不得手工声明未进入 manifest 的官方工件。

| artifact | sha256 | schema | phase | media type | path |
|---|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

## 依赖与完整性

path 必须是相对运行目录的规范路径，sha256 必须由已发布字节重算。每个 phase 工件应能追溯到对应 phase event 和 frozen upstream DAG。

## 读者导航

将主文章、完整推演档案、验证报告和结构化工件分组说明用途。绝对运行路径只作为导航投影，不进入 manifest 的相对 path 字段。
