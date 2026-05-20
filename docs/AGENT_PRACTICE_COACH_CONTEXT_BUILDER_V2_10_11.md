# AGENT_PRACTICE_COACH_CONTEXT_BUILDER_V2_10_11

## 目标

v2_10_11 将 `今日练什么` 从一次性 guidance preview 继续推进到 **Practice Coach Session** 的上下文工程地基：先不执行真实 LLM 对话，不生成 Routine 卡片，而是把用户消息、用户画像、active plan、最近练习历史与当前会话状态组织成可审计、可缓存、可复用的 LLM messages preview。

新增接口：

```text
POST /agent/harmonyos/practice-coach-session/context-builder-preview
```

该接口接受与 HarmonyOS 黑盒 Agent 请求一致的产品字段，例如：

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

它可读取后端 SQLite context，但 **不会调用大模型**，也不会启动 Routine、调用 Engine、生成 MIDI、播放音频或写入 HarmonyOS 本地状态。

## 上下文分层

Practice Coach Session 的上下文 block 顺序固定为：

```text
stable_product_contract
stable_action_contract
user_profile_summary
active_practice_plan_summary
recent_practice_memory_summary
practice_coach_session_state
current_user_turn
```

缓存友好原则：

```text
越稳定越靠前
越动态越靠后
system/product contract 不掺 sessionId/traceId/deviceId
用户画像、计划、历史以 canonical JSON 投影
当前会话状态和当前用户消息放在末尾
```

每个 block 都有 digest，用于判断本轮请求中到底哪一块变化导致 cache miss：

```text
blockDigests.stable_product_contract
blockDigests.stable_action_contract
blockDigests.user_profile_summary
blockDigests.active_practice_plan_summary
blockDigests.recent_practice_memory_summary
blockDigests.practice_coach_session_state
blockDigests.current_user_turn
```

其中：

```text
stable_product_contract + stable_action_contract = stable prefix
current_user_turn = 每轮必变
practice_coach_session_state = 对话连续性状态，高频变化但靠后
```

## 返回结构重点

主要查看：

```text
data.llmRequestPreview
```

关键字段：

```text
messages                         # provider-compatible system/user messages
chatCompletionsMessagesIfCalled  # 当前版本等同 messages，均为 system/user roles
contextBlocks                    # 分层上下文 block + digest + payload
blockDigests                     # 每个 block 的 digest
debugMetadata.stable_prefix_digest
debugMetadata.context_packet_digest
debugMetadata.current_turn_digest
cacheDesign                      # 缓存设计说明
sourceProjection                 # SQLite/直接字段的投影来源摘要
```

## 最近练习历史投影

v2_10_11 修正了 v2_10_10 的一个上下文缺口：Routine completion record 中的 `items` 和 `notes` 不再丢失，而是以摘要形式进入：

```text
recent_practice_memory_summary.recent_sessions[].item_summaries
recent_practice_memory_summary.recent_sessions[].user_note_summary
```

但仍然不会把 raw `items` / raw `notes` 整坨塞进 prompt。这样既能让 LLM 知道用户上次具体练了什么，也控制 token 与缓存稳定性。

## 安全边界

该 preview 接口只做上下文工程审计：

```text
llm_called = false
network_call_executed = false
startsRoutine = false
callsEngineAdapter = false
callsAccompanimentGenerate = false
createsMidiAsset = false
startsPlayback = false
writesHarmonyOSLocalState = false
```

Provider prompt cache 只被视为成本优化，不作为连续性保证。真正保证长期连续性的是后端保存的 context projection：user profile、active plan、recent practice memory、practice coach session state。

## 下一步建议

```text
v2_10_12_agent_practice_coach_conversation_state_store
```

目标：在 v2_10_11 的上下文 builder 基础上，保存并恢复 Practice Coach Session 的对话状态，使用户在 Agent 追问后继续说“20分钟，想练bossa”时，后端知道这是在回答上一轮缺失字段，而不是孤立消息。
