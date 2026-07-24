# Artifact manifest 生成合同

产物：`promax-artifact-manifest.json`
生成阶段：`P10`
Schema：`promax-artifact-manifest.schema.json`
生成权：确定性运行时

禁止模型手算散列或直接编写该文件。先对安全、稳定、非链接的实际文件运行 `inventory_artifacts()`，再把结果与当前 run contract、phase chain head、五个 role records 传给 `build_artifact_manifest()`。

## 根字段

生成器写入且闭合：`schema_id`、`schema_version`、`run_id`、`run_nonce`、`request_sha256`、`source_snapshot_sha256`、`run_contract_sha256`、`mode`、`orchestration_mode`、`role_records`、`phase_chain_head_sha256`、`artifacts`、`generated_at`、`manifest_sha256`。

`schema_id` 固定为 `crossframe.promax.v8.artifact-manifest`，`schema_version=1`。`run_contract_sha256` 由当前规范 JSON 计算；`manifest_sha256` 由除自身外的完整 body 计算。

## Artifact inventory

每条 artifact 只含 `path`、`sha256`、`media_type`、`generating_phase`、`input_artifact_sha256s`、`status`。路径使用规范相对 POSIX 拼写，media type 由后缀派生，status 只能是 `current`、`invalidated`、`superseded`。

当前分析 inventory 必须精确登记：

- `promax-source-snapshot.json`
- `promax-read-events.jsonl`
- `promax-worldview-capsule.locked.md`
- `promax-local-world-model.locked.json`
- `promax-concept-disposition-ledger.json`
- `promax-claim-path-graph.json`
- `promax-retrieval-ledger.json`
- `promax-red-team-report.json`
- `promax-position.locked.json`
- `promax-recommendation.locked.json`
- `promax-output-plan.locked.json`
- `promax-dossier.md`
- `promax-concept-atlas.md`
- `promax-case-and-countercase.md`
- `promax-essay.md`
- `promax-continuation-index.md`

Run contract、manifest 自身、continuation ledger、phase events、validator report、repair plan 和 final chat 不得作为 current inventory 输入。

## 五角色记录

`role_records` 必须按 run contract 顺序精确登记五个角色。每条只含 `role_id`、`sequence`、`execution_mode`、`exchange_protocol`、`input_artifacts`、`observed_input_artifacts`、`output_artifacts`、`status`；exchange protocol 固定为 `structured-artifacts-only`，status 只能是 `completed`、`blocked`、`invalidated`。

完成角色必须实际观察已声明输入；输出不能与自身输入相同，也不能读取同序或未来角色输出。五个角色的输出生成阶段依次为 `P4`、`P6`、`P7`、`P8`、`P10`，每个输出的 input lineage 必须等于该角色 observed input hashes。

生成后立即过 schema、角色隔离、文件字节、closed inventory 与自散列校验。任何 current 字节变化都要求重新 inventory 和生成新 manifest。
