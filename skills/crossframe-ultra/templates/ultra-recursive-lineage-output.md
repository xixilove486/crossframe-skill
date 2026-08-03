# Ultra 递归谱系输出

本模板用于 U7 冻结 lineage。每个节点引用一个已验证的 recursive-state 工件，并保留 node、path、parent 与 artifact sha256 的一一对应。

## lineage 节点

| node | parent node | order | recursive state sha256 |
|---|---|---:|---|
| 待填 | 待填 | 待填 | 待填 |

## 分支、合并与剪枝

主路径、最强竞争路径、混合路径和 residual 路径分别列出。合并必须记录多 parent 分支；剪枝必须保留理由和残差。

## order-2 与 order-3

order-2 写出一阶状态如何改变行动集、资源、反馈和下一事件条件；order-3 写出制度化、lock-in、reversal 或跨圈层外溢。合法早停时说明停止理由和未展开方向。
