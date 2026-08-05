# /crossframe-ultra

This explicit command is allowed only for the fixed CrossFrame Ultra v8.2 reference runtime. Its accepted names are exactly `crossframe-ultra`, `CrossFrame Ultra`, `$crossframe-ultra`, and `/crossframe-ultra`.

Read the canonical controller at `skills/crossframe-ultra/SKILL.md`, then execute it without copying or replacing its protocol. Pass the user's request unchanged:

`$ARGUMENTS`

An exact Ultra-only request starts Ultra directly. If the request also names another runtime, run each requested runtime independently only when it explicitly asks for a comparison; without that comparison, 暂停确认 which runtime the user wants before starting.

Use only the v8.2 authority, fixed runtime commands, fixed production/test roots, and official article path defined by the canonical controller. If any required capability, root, source, stage, or validation gate fails, report the Ultra state and stop；不得回退、不得静默降级，也不得用另一 runtime 或聊天短答替代。
