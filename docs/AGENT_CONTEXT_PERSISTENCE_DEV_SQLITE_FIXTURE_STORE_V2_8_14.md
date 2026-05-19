# AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_V2_8_14

## 1. 版本目标

`v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in` 在 v2_8_13 dry-run writer shape 之后，新增一个 **dev-only 显式 opt-in fixture store**。

这一层允许在所有 gate 通过后，向开发用 JSONL fixture 文件追加一条已脱敏、可回放的上下文持久化记录，用于本地调试 persistence 链路。

它仍然不是正式数据库实现。

## 2. 新增入口

```text
GET  /agent/context/persistence-dev-sqlite-fixture-store/spec
POST /agent/context/persistence-dev-sqlite-fixture-store/preview
CLI  /context-persistence-dev-sqlite-fixture-store [json_payload]
```

## 3. 显式 opt-in gate

必须同时满足：

```text
fixtureStoreWriteEnabled=true
executeFixtureStore=true
userDecision=approved
confirmationStatus=user_approved_future_executor_required
environment in dev/local_dev/test/fixture
fixtureStorePath is relative or tmp/dev path
traceId present
idempotencyKey present or derived
storageBoundaryCheckPassed=true
redactionCheckPassed=true
schemaPreviewAccepted=true
```

任何 gate 失败都会返回 `fixture_store_blocked`，不会写 fixture 文件。

## 4. 允许写入什么

只允许写入本地开发 fixture JSONL 文件中的一条 redacted context persistence record。

记录内容包括：

```text
record_contract_version
fixture_store_id
written_at_utc
environment
user_id
candidate_kind
candidate_id
confirmation_id
trace_id
idempotency_key
entities
planned_rows
storage_boundary
source
```

## 5. 不允许做什么

即使 fixture store 成功，也仍然不做：

```text
不创建 SQLite connection
不创建 SQLite tables
不写 SQLite rows
不写 backend database
不写 HarmonyOS local state
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
不生成练习结束后的推荐卡片
```

## 6. 终端示例

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status
```

```text
/context-persistence-dev-sqlite-fixture-store {"fixtureStoreWriteEnabled":true,"executeFixtureStore":true,"fixtureStorePath":"./.jammate/dev_agent_fixture_store.jsonl","userDecision":"approved","confirmationStatus":"user_approved_future_executor_required","environment":"dev","traceId":"trace_fixture_store"}
```

预期输出：

```text
ContextPersistenceDevSqliteFixtureStore>
  version: v2_8_14
  validation_status: fixture_store_ready
  accepted: True
  fixture_store_write_executed: True
  sqlite_connection_created: false
  backend_database_written: false
```

## 7. 架构边界

这一版属于 Agent 线 context persistence dev fixture 工具链，不属于 Engine 线。

未修改：

```text
Engine 音乐生成
pattern / voicing / expression / pedal
demos/*.mid
README.md
agent.md
VERSION
pyproject.toml
共享 ARCHITECTURE / API_CONTRACT / 主 CHANGELOG
HarmonyOS fixture
```

## 8. 下一步建议

```text
v2_8_15_agent_context_persistence_dev_fixture_readback_and_replay_preview
```

下一步可以围绕 fixture store 追加后的 read-back / replay preview 做验证，但仍建议保持 dev-only，不进入正式数据库实现。
