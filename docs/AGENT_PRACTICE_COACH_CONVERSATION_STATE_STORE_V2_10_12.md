# AGENT_PRACTICE_COACH_CONVERSATION_STATE_STORE_V2_10_12

## 目标

`v2_10_12` 把 Practice Coach Session 从“能预览上下文工程”推进到“能保存和恢复对话状态”。

新的 HarmonyOS-facing 路由：

```text
POST /agent/harmonyos/practice-coach-session/message-state/execute
```

它解决的真实用户问题是：

```text
第一轮：用户点“今日练什么”
Agent：我还需要知道你今天有多少时间、想练什么方向。
第二轮：用户说“20 分钟，想练 Bossa”
后端能知道第二句话是在回答上一轮缺失字段，而不是孤立消息。
```

## 边界

这个版本只做 Conversation State Store，不做完整 Practice Coach LLM 执行。

严格边界：

```text
会写后端 SQLite 的 Practice Coach session state
不会调用大模型
不会发 provider 网络请求
不启动 Routine
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
不生成最终练习安排卡片
```

## 请求体

前端仍然只传产品字段：

```json
{
  "userId": "local-dev-user",
  "sessionId": "coach-session-1",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

前端不传：

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal gate
LLM messages
```

后端继续通过 `JAMMATE_AGENT_CONTEXT_DB_PATH` 或安全 local-dev 默认路径选择 SQLite。

## 响应重点

```text
data.conversationStatePersisted
data.stateFoundBeforeTurn
data.stateBefore
data.stateAfter
data.extractedFieldsFromCurrentTurn
data.agentActionPreview
data.llmRequestPreview
```

`agentActionPreview` 是确定性的状态机预览，不是 LLM 输出。

第一轮可能返回：

```json
{
  "responseType": "ask_clarifying_question",
  "missingFields": ["available_minutes", "practice_focus"],
  "nextClientActions": ["show_chat_message", "show_suggested_replies"]
}
```

第二轮用户补齐后可能返回：

```json
{
  "responseType": "chat_message",
  "collectedFields": {
    "available_minutes": 20,
    "practice_focus": "bossa"
  },
  "missingFields": [],
  "nextClientActions": ["build_practice_plan_proposal_next"]
}
```

## SQLite 表

本版本新增 Practice Coach 专用状态表：

```text
practice_coach_session_states
practice_coach_session_turns
```

它们与既有 `context_persistence_records` 共用同一个后端 SQLite DB 文件，但职责不同：

```text
context_persistence_records：长期练习上下文/完成记录/计划/画像
practice_coach_session_states：当前 Practice Coach 对话状态
practice_coach_session_turns：当前 Practice Coach 会话 turn 审计
```

## 上下文工程关系

状态写入后，路由会同步返回 `llmRequestPreview`，使用 v2_10_11 的 cache-friendly context builder。

新增进入 `practice_coach_session_state` block 的内容包括：

```text
collected_fields
pending_missing_fields
pending_question
last_agent_action
turn_count
```

但 `sessionId` / `deviceId` 仍不进入 LLM prompt 主体，避免破坏缓存前缀。

## 下一步

推荐下一步：

```text
v2_10_13_agent_practice_coach_plan_proposal_contract
```

目标是在 `available_minutes` 与 `practice_focus` 等必要信息齐备后，生成结构化 `practice_plan_proposal`，让用户确认或调整。确认之前仍不生成 Routine card，不启动 Routine。
