# Agent Context Persistence Confirmation Boundary v2_8_8

## 目的

`v2_8_8_agent_context_persistence_confirmation_boundary` 为 Agent 线新增统一的上下文持久化确认边界。

它把已经存在的 candidate-only persistence payload：

- `PracticePlanPersistenceCandidate` (`v2_8_6`)
- `RoutineHistoryPersistenceCandidate` (`v2_8_7`)

统一包进一个用户可审阅、可确认、可拒绝、可关闭的 confirmation record。

## 核心原则

这一版仍然不是数据库实现，也不是同步实现。

```text
candidate preview
→ user review / edit
→ confirmation record
→ future persistence executor
```

`v2_8_8` 只做到第三步的记录边界，第四步还未实现。

## API

```http
GET  /agent/context/persistence-confirmation/spec
POST /agent/context/persistence-confirmation/preview
```

## Terminal CLI

```text
/context-persistence-confirmation {json_payload}
```

示例：

```json
{
  "candidateKind": "practice_plan",
  "userDecision": "approved",
  "practicePlan": {
    "title": "Medium Swing Comping Plan",
    "planBlocks": [
      {"title": "Guide-tone warmup", "style": "medium_swing", "tempo": 96, "durationMinutes": 10}
    ]
  }
}
```

RoutineHistory 示例：

```json
{
  "candidateKind": "routine_history",
  "decision": "confirm",
  "routineHistoryRecords": [
    {"sessionId": "session_001", "title": "Blue Bossa comping", "actualSeconds": 1260, "completed": true}
  ]
}
```

## 输出对象

核心输出包括：

```text
ContextPersistenceConfirmationBoundaryPayload
confirmation_envelope
future_executor_boundary
validation
guard_summary
```

其中 `confirmation_envelope` 只表示用户确认意图：

```text
pending_user_review
user_approved_future_executor_required
user_rejected_no_write
dismissed_no_write
not_confirmable
```

即使 `userDecision=approved`，也不会写库。

## 明确不做

```text
不写数据库
不写鸿蒙本地
不实现 sync job
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
不生成练习结束后的推荐卡片
```

## 未来下一步

推荐下一步：

```text
v2_8_9_agent_context_persistence_executor_noop_skeleton
```

也就是设计一个 future persistence executor 的 no-op skeleton，用来明确真实写入前需要哪些 idempotency、trace、storage contract、user confirmation 检查，但仍可以先不真正写数据库。
