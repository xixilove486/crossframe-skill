# Ultra 新鲜验证报告输出

本模板用于 U12 fresh-context validator report。checker 只读经过规范化的运行或 staging，向 stdout 返回 canonical bytes；持有 lease 的父进程负责保存原始报告。

## manifest 绑定

记录 attempt、manifest sha256、validator set sha256、验证时间和 fresh context 标记。任何散列错位都必须失败关闭。

| validator | artifact | passed status | error code |
|---|---|---|---|
| 待填 | 待填 | pass / fail / blocked | 待填 |

## overall status

只有所有必需 validator 均 passed，overall status 才能为 pass。error 必须使用稳定错误代码并绑定受影响 artifact；不得用自然语言成功宣言替代检查结果。

pre-publish 与 post-publish 分别产生独立 attempt。checker 不获取 lease、不写 current 报告，也不修改 manifest 或 delivery。
