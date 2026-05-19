# AGENT_TOOL_EXECUTION_CONFIRMATION_GATE_V2_6_2

## 版本目标

`v2_6_2_agent_tool_execution_confirmation_gate` 只建立 Agent 工具执行前确认门：

```text
Tool Invocation Preview
→ Tool Execution Confirmation Envelope
→ 用户 /confirm 或 /reject
→ Trace 记录确认结果
```

本版本明确不是 Tool Executor，不是 deterministic workflow dispatcher，也不调用 engine。

## 已落位能力

- `ToolExecutionConfirmationEnvelope`
- `ToolExecutionConfirmationPolicy`
- `ToolExecutionConfirmationResult`
- `build_confirmation_envelope(...)`
- `confirm_tool_invocation(...)`
- `tool_execution_confirmation_contract()`
- terminal chat `/pending`
- terminal chat `/confirm`
- terminal chat `/reject`
- confirmation trace summary
- `GET /agent/tools/confirmation/spec`
- `POST /agent/tools/confirmation/preview`

## 硬边界

```text
不执行工具
不 dispatch deterministic workflow
不调用 engine adapter
不调用 /accompaniment/generate
不修改 pattern / voicing / expression / pedal
不修改 demos/*.mid
不改共享文档
```

## 行为规则

1. 只有 preview 通过的 tool proposal 才能进入 pending confirmation。
2. unknown tool / not allowed tool 会得到 `not_confirmable` envelope。
3. 用户 `/confirm` 后只记录 `user_approved=true`，仍然 `would_execute=false`。
4. 用户 `/reject` 后只记录 `user_approved=false`，仍然 `would_execute=false`。
5. 所有 confirmation payload 都保持：

```text
would_execute_after_confirmation=false
execution_still_disabled=true
requires_executor_boundary=true
```

## Trace 事件

新增 trace step：

```text
terminal_tool_confirmation_envelope_created
terminal_tool_confirmation_user_approved
terminal_tool_confirmation_user_rejected
terminal_tool_execution_confirmation_summary_recorded
```

final response summary 新增：

```text
tool_execution_confirmation_contract_version
tool_execution_confirmation_summary
```

## API Contract

```http
GET /agent/tools/confirmation/spec
POST /agent/tools/confirmation/preview
```

`POST /agent/tools/confirmation/preview` 复用 tool invocation preview request shape，并返回：

```json
{
  "ok": true,
  "confirmation_contract_version": "v2_6_2",
  "preview": {},
  "confirmation": {
    "confirmation_status": "pending",
    "requires_user_confirmation": true,
    "user_approved": false,
    "would_execute_after_confirmation": false,
    "execution_still_disabled": true
  },
  "context_packet_summary": {}
}
```

## 下一步

推荐下一步进入：

```text
v2_6_3_agent_tool_executor_boundary
```

目标只定义 executor boundary / dry-run / no-op execution，不应直接进入真实 engine 调用。
