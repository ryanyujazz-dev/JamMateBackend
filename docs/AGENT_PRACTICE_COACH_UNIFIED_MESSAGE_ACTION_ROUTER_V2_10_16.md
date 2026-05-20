# v2_10_16 — Practice Coach Session unified message/action router

本版本新增 HarmonyOS-facing 统一入口：

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

目标是让前端尽量只发送一次 Practice Coach message，然后根据响应中的 `responseType`、`nextClientActions`、`agentActionPreview` 渲染下一步；前端不需要知道后端内部到底调用了 `message-state/execute`、`profile-sheet/execute`、`plan-proposal/execute` 还是 `routine-card/execute`。

## 自动路由规则

当前 deterministic router 会按以下优先级选择内部执行器：

1. 请求中包含 `profileFormResult`，或显式 `practiceCoachAction=request_profile_sheet`：路由到 `profile_sheet`。
2. 当前 session 已有 `draft_plan` 且等待确认，或用户消息是“确认这个安排”：路由到 `routine_card`。
3. 当前 turn / 已保存 state 已经具备 `available_minutes` 与 `practice_focus`：路由到 `plan_proposal`。
4. 否则路由到 `message_state`，继续追问或记录对话状态。

## 产品边界

本接口仍然保持 Agent / Integration 路线边界：

- 不调用大模型。
- 不发 provider 网络请求。
- 不启动 Routine。
- 不调用 Engine。
- 不生成 MIDI。
- 不播放。
- 不写 HarmonyOS 本地状态。
- 只通过既有 deterministic contracts 写后端 Practice Coach SQLite session state。

## 前端推荐使用方式

HarmonyOS 前端可以优先接入这个统一入口：

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-xxx",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

然后只看：

```text
ok
code
message
data.responseType
data.nextClientActions
data.agentActionPreview
data.sheetIntent
data.planProposal
data.routineCardPayload
```

典型用户流：

```text
用户：今天该练什么？
→ responseType=ask_clarifying_question

用户：20 分钟，想练 Bossa
→ responseType=practice_plan_proposal

用户：确认这个安排
→ responseType=routine_card_ready
```

## 缓存 / 上下文工程

统一 router 仍然返回 `llmRequestPreview`。底层沿用 v2_10_11 的 Practice Coach context builder：

```text
stable_product_contract
stable_action_contract
user_profile_summary
active_practice_plan_summary
recent_practice_memory_summary
practice_coach_session_state
current_user_turn
```

`sessionId`、`deviceId`、`traceId` 不进入 prompt 主体；它们只在 debug / routing metadata 中出现。

## 下一步

推荐继续做：

```text
v2_10_17_agent_practice_coach_unified_frontend_fixture_and_smoke
```

目标：给 HarmonyOS 前端 Claude 输出统一入口 fixtures、curl smoke 和 ArkTS contract 摘要，减少前端对旧分散 endpoints 的依赖。
