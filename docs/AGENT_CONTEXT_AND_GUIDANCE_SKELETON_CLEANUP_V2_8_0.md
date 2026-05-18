# AGENT_CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_V2_8_0

## 目标

`v2_8_0_agent_context_and_guidance_skeleton_cleanup` 是 Agent 线的上下文 / guidance 骨架收口版本。

本版本不扩张新的用户能力，也不新增真实执行动作。它只把 `v2_7_3` 到 `v2_7_9` 已建立的 “今天该练什么” 上下文链路整理成一个统一可查询的骨架状态：

```text
Active PracticePlan / RoutineHistory / today constraints
→ assembled_practice_context
→ TodayPracticeGuidance prompt contract
→ user capability map / intent taxonomy
→ output validation
→ provider-boundary E2E
→ display-only ActionCard
→ terminal chat E2E surface
```

## 新增契约

```text
ContextAndGuidanceSkeletonCleanupPayload
build_context_and_guidance_skeleton_cleanup_payload(...)
build_context_and_guidance_skeleton_cleanup_summary(...)
context_and_guidance_skeleton_cleanup_contract()
```

## 新增 API

```http
GET /agent/context/guidance-skeleton-cleanup
```

## 新增 CLI

```text
/context-guidance-skeleton [json_payload]
```

## 收口内容

本版本集中暴露：

```text
stage_registry
canonical_routes
terminal_commands
normalized_guard_flags
cleanup_findings
next_recommended_task
```

其中 `stage_registry` 按顺序列出：

```text
1. context_engineering_skeleton
2. today_practice_guidance_prompt_contract
3. user_capability_map_and_intent_taxonomy
4. today_practice_guidance_output_validation
5. today_practice_guidance_provider_boundary_e2e
6. today_practice_guidance_action_card
7. today_practice_guidance_terminal_chat_e2e
```

## 边界

本版本继续保持：

```text
不创建 Routine 结束后的自动推荐卡片
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 engine adapter
不生成 MIDI asset
不启动 playback
不假设鸿蒙前端 UI 流程
不改 Engine 音乐生成
不改共享文档
不改 HarmonyOS fixture
```

## 后续建议

`v2_8_0` 之后可以进入更具体的上下文来源和用户功能，例如：

```text
v2_8_1_agent_user_profile_context_intake
```

或先做：

```text
v2_8_1_agent_today_practice_guidance_persistence_boundary
```

二者都应继续遵守：先定义上下文 / 契约，再做受控执行。
