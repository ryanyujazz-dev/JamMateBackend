# Agent Today Practice Guidance Persisted Context Recovery E2E v2_8_17

## 目标

把 v2_8_15 dev fixture read-back 与 v2_8_16 snapshot context intake 恢复出来的用户画像、长期练习计划、RoutineHistory 上下文，接入现有 v2_8_3 profile-aware today-practice guidance 链路。

```text
fixture/read-back snapshot
→ snapshot context intake
→ ContextBuilder-ready profile / active plan / routine history sections
→ profile-aware today-practice guidance
→ display-only ActionCard / Routine candidate
```

## 非目标

本版本不做真实存储、不启动练习、不调用伴奏引擎。

```text
不写数据库
不写 HarmonyOS 本地
不创建 SQLite connection/table/row
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
不生成练习结束后的推荐卡片
```

## API

```http
GET  /agent/context/today-practice-guidance/persisted-context-recovery/spec
POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview
```

## CLI

```text
/today-practice-guidance-persisted-context-recovery {json_payload}
```

## 设计原则

- persisted context 只作为下一次用户主动询问“今天该练什么”的上下文。
- 用户画像是 soft context，不是硬编码推荐规则引擎。
- 输出仍然只是建议与候选 Routine；是否展示、编辑、加入队列或开始练习由客户端和后续 confirmation flow 决定。
- 本链路可以使用 `providerResult` fixture 做 E2E 验证；真实 LLM 调用仍由显式 provider boundary 控制。

## 下一步建议

`v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls`

建议开始做终端侧的 persisted context 临时加载/清除/查看命令，让开发者不用每次都手动贴完整 snapshot payload。
