# Agent Context Persistence Executor No-op Skeleton v2_8_9

`v2_8_9_agent_context_persistence_executor_noop_skeleton` 在 v2_8_8 的 `ContextPersistenceConfirmationBoundary` 之后新增一个 future persistence executor 的 no-op 骨架。

本版目标不是写数据库，而是把真实写入前必须存在的 executor 边界先固定下来：

```text
PracticePlanPersistenceCandidate / RoutineHistoryPersistenceCandidate
→ ContextPersistenceConfirmationBoundary
→ ContextPersistenceExecutorNoop
→ no-op execution report
```

## 新增 API

```http
GET  /agent/context/persistence-executor-noop/spec
POST /agent/context/persistence-executor-noop/preview
```

## 新增 CLI

```text
/context-persistence-executor-noop [json_payload]
```

## Executor 检查项

```text
confirmed candidate required
userDecision must be approved
confirmationStatus must be user_approved_future_executor_required
candidate kind must be PracticePlan or RoutineHistory persistence candidate
idempotency key must exist or be derived
trace link must be supported
storage contract boundary must be checked
```

## 本版严格不做

```text
不写数据库
不写鸿蒙本地
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
不生成练习结束后的推荐卡片
```

即使 executor 状态为：

```text
noop_executor_ready
```

也只表示：

```text
如果未来真实 persistence executor 存在，这个确认记录理论上可进入真实写入阶段。
```

当前仍然：

```text
write_attempted = false
storage_written = false
backend_database_written = false
local_device_written = false
future_real_executor_implemented = false
```

## 终端示例

```text
/context-persistence-executor-noop {"candidateKind":"practice_plan","userDecision":"approved","practicePlan":{"title":"Medium Swing Comping Plan","planBlocks":[{"title":"Guide-tone warmup","style":"medium_swing","tempo":96,"durationMinutes":10}]}}
```

## 设计判断

这一层不能和真实存储实现混在一起。它只是把未来执行器必须遵守的条件先外显出来，防止后续直接把 candidate preview 或 confirmation record 当成数据库写入入口。

未来真实 executor 至少还需要：

```text
backend storage schema
storage adapter
idempotent upsert semantics
confirmed-candidate recheck
trace link persistence
safe retry policy
```
