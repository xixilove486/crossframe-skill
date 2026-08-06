# /crossframe-ultra

This explicit command is allowed only for the fixed CrossFrame Ultra v8.2 reference runtime. Its accepted names are exactly `crossframe-ultra`, `CrossFrame Ultra`, `$crossframe-ultra`, and `/crossframe-ultra`; 精确点名只限制激活。

Read the canonical controller at `skills/crossframe-ultra/SKILL.md`, then execute it without copying or replacing its protocol. Pass the user's request unchanged:

`$ARGUMENTS`

普通自然语言是合法输入并默认进入 `open-world`；不要强制改写成 closed-input JSON。按 canonical controller 调用 `prepare` / `materialize`：读取 runtime 的 `pending-action`，用真实宿主工具执行唯一获准的联网、读源或 subagent 动作，只写指定 result/authoring slot，再交回 runtime 验证。candidate 在 U3 admission 前不是证据。

`awaiting-host-action` 与 `awaiting-authoring` 是正常运行进度。不得手工编辑 control、checkpoint 或 lease，也不得用清文件推动状态。

An exact Ultra-only request starts Ultra directly. If the request also names another runtime, run each requested runtime independently only when it explicitly asks for a comparison; without that comparison, 暂停确认 which runtime the user wants before starting.

Use only the v8.2 authority, fixed runtime commands, fixed production/test roots, and official article path defined by the canonical controller. If any required capability, root, source, stage, or validation gate fails, report the Ultra state and stop；不得回退、不得静默降级，也不得用另一 runtime 或聊天短答替代。
