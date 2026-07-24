# Continuation index 生成合同

产物：`promax-continuation-index.md`
生成阶段：`P10`
控制输入：当前 manifest 与由确定性流程生成的 `promax-continuation-ledger.json`

该索引是面向用户的分段交付导航，不替代 continuation ledger，也不自行计算父散列。顶层标题使用 `# ProMax v8 续写索引`。

## 必须包含

1. 当前 run ID、run status、parent manifest SHA-256 和索引生成时间。
2. 已交付的 P10 工件顺序、相对路径、章节范围与当前 SHA-256。
3. 对 ledger 中每条 continuation，逐项写 `continuation_id`、`sequence`、`status`、`resume_from_phase`、父工件路径、`pending_artifact_paths`、`reason`。
4. 明确续写只能从 `P10` 恢复，且必须重新校验当前 manifest 和父工件字节。
5. 给出下一段从哪个 SECTION ID、claim、concept 或案例开始，避免重复已交付文本或用摘要替代。
6. 没有 active continuation 时，明确写“当前交付已闭合”，并说明未来发生截断必须新建绑定当前 manifest 的记录。

## 一致性规则

- continuation IDs 从 `CONT-*` 记录读取，sequence 必须从 1 连续递增。
- pending paths 不能已经是 current artifact，且全局大小写折叠后仍唯一。
- parent artifact 必须是 manifest 中当前、由 `P10` 生成的工件。
- `pending` 或 `in_progress` 中最后一条记录是 final chat 的 `continuation_entry`；没有 active record 时该值为 `null`。
- manifest 或任何父工件变化后，旧索引与 ledger 一起失效，必须重新绑定。

索引用连续中文说明恢复边界；不写未执行的进度，不宣称容量耗尽等于分析完成。
