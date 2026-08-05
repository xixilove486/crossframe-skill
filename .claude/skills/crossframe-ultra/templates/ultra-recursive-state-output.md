# Ultra 递归状态输出

本模板用于 U7 的单个 sealed recursive state。每个 node 保存本阶完整状态或声明边界的子图，不能只继承 parent 的一句结论。

| node | path | parent run / path / node | order | state 边界 |
|---|---|---|---:|---|
| 待填 | 待填 | 待填 | 待填 | full state 或 bounded subgraph |

## 继承与变化

分别列出继承的事实、证据、unknown、loss 与 residual，再记录本阶事件、mechanism、state diff 和观察 signal。

## channel 与证据身份

每项变化必须指出真实 channel；没有通道不得更新。模拟 state 继续保持 simulated 身份，递归深度不得提高其证据等级。
