# Agent Terminal Chat Product Smoke Polish v2_8_22

## Goal

`v2_8_22_agent_terminal_chat_product_smoke_polish`收口真实终端对话测试体验，重点覆盖：

```text
provider setup / doctor
ordinary Chinese today-practice turn
persisted-context terminal memory
JSON fallback / partial-default behavior
guarded validation error hint
no-side-effect guard visibility
```

这一版不做新的推荐逻辑，不调用 Engine，不实现真实数据库写入。

## New surfaces

```text
GET  /agent/context/today-practice-guidance/terminal-product-smoke/spec
POST /agent/context/today-practice-guidance/terminal-product-smoke/preview
CLI  /terminal-product-smoke [json_payload]
```

## What the smoke pack checks

```text
1. setup / doctor / config-path entrypoints are reachable.
2. Provider status clearly says whether terminal chat is ready or still guarded.
3. Ordinary Chinese input such as “今天该练什么？” routes into the guarded TodayPracticeGuidance chain.
4. Loaded persisted-context memory is injected into the next today-practice guidance turn.
5. JSON-only / plain-text fallback / partial JSON default behavior is documented for manual provider testing.
6. Blocked guidance now prints an actionable terminal hint instead of only internal fields.
```

## Terminal flow

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat doctor
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status
```

Inside terminal chat:

```text
/terminal-product-smoke
/persisted-context-load { ...profile / practicePlan / routineHistoryRecords... }
今天该练什么？
```

## Boundaries

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row.
No LLM call by smoke preview.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
```

The smoke preview may report that the manually typed ordinary Chinese prompt will call the configured LLM provider, but the `/terminal-product-smoke` command and API preview themselves do not call the provider.

## Next recommended task

```text
v2_8_23_agent_v2_8_phase_cleanup_regression_handoff
```
