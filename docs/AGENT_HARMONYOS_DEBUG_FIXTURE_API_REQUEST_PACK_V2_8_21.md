# v2_8_21 Agent HarmonyOS Debug Fixture API Request Pack

## 目标

`v2_8_21_agent_harmonyos_debug_fixture_api_request_pack` 把 v2_8_19 / v2_8_20 已经打通的 persisted-context guidance debug fixture 链路整理成鸿蒙前端可直接联调的 API request pack。

本版本只生成可复制的 endpoint / request body / response path / curl example / terminal command preview，不真正调用这些 route。

## 新增接口

```text
GET  /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview
CLI  /harmonyos-debug-fixture-api-request-pack [json_payload]
```

## Request Pack 包含的三步

```text
1. POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview
   从 profile / active plan / routine history 构建 HarmonyOS debug fixture。

2. POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview
   使用 fixture.agentRequestPreview.body 进入 persisted-context recovery guidance。

3. POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview
   验证 debug fixture 可以 roundtrip 回 Agent guidance preview。
```

## 终端测试

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status
```

```text
/harmonyos-debug-fixture-api-request-pack {
  "baseUrl": "http://127.0.0.1:8000",
  "userInput": "今天该练什么？",
  "availableMinutes": 25,
  "userPracticeProfile": {
    "currentGoal": "提高 jazz comping 稳定性",
    "preferredStyles": ["medium_swing", "bossa_nova"],
    "focusAreas": ["ii-V-I", "comping"],
    "comfortableTempoRanges": {
      "medium_swing": [90, 120],
      "bossa_nova": [100, 145]
    }
  },
  "practicePlan": {
    "title": "Persisted Medium Swing Comping Plan",
    "status": "active",
    "planBlocks": [
      {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}
    ]
  },
  "routineHistoryRecords": [
    {"sessionId": "session_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": true}
  ],
  "providerResult": {
    "content": {
      "guidance_mode": "continue_original_plan",
      "summary": "从已恢复的长期计划继续，今天优先练 Medium Swing ii-V-I comping。",
      "recommended_focus": "ii-V-I comping 稳定性",
      "recommended_blocks": [
        {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 guide-tone voice leading"}
      ],
      "routine_candidates": [
        {"routineName": "Persisted Medium Swing comping routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"}
      ],
      "user_confirmation_required": true,
      "next_client_actions": ["show_guidance", "present_routine_candidate"]
    }
  }
}
```

## 边界

本版本严格保持：

```text
不写数据库
不写 HarmonyOS 本地状态
不创建 SQLite connection/table/row
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
不生成练习结束后的推荐卡片
不改 frontend_fixtures/harmonyos
```

## 前端联调意义

前端可以用 request pack 中的三组 request body 做 debug screen 或 API smoke test：

```text
已恢复上下文
→ HarmonyOS debug fixture
→ Agent persisted-context recovery preview
→ display-only TodayPracticeGuidance ActionCard / Routine candidate
```

它不假设具体 UI 流程。HarmonyOS 仍然决定：

```text
展示卡片
展示候选 routine
进入设置页
进入 bottom sheet
只作为 debug 面板展示
```

## 下一步

推荐下一步：

```text
v2_8_22_agent_terminal_chat_product_smoke_polish
```

重点检查真实 LLM 终端对话体验、错误提示、provider 配置、普通中文输入和 persisted context memory 是否稳定。
