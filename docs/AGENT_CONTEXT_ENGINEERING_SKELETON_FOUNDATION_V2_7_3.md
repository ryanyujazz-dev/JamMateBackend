# AGENT_CONTEXT_ENGINEERING_SKELETON_FOUNDATION_V2_7_3

## 版本

```text
v2_7_3_agent_context_engineering_skeleton_foundation
```

## 目标

本版本用于收口 JamMate Agent 的“练习上下文工程基本骨架”。

它不是新的推荐功能，也不是 Routine 结束页卡片，而是把未来用户主动询问：

```text
今天该练什么？
```

所需要的基础上下文结构搭起来。

## 本版本新增三层上下文边界

```text
Active PracticePlan Context Intake
Routine History Context Intake
Practice Context Assembly Policy
Today Practice Context E2E Preview
```

其中 Routine History Context Intake 已在 v2_7_2 建立，本版本把它和 active PracticePlan 组合起来。

## 1. Active PracticePlan Context Intake

新增：

```text
ActivePracticePlanContextIntakePayload
build_active_practice_plan_context_intake_payload(...)
build_active_practice_plan_context_intake_summary(...)
active_practice_plan_context_intake_contract()
```

API：

```http
GET  /agent/context/active-practice-plan/spec
POST /agent/context/active-practice-plan/intake
```

CLI：

```text
/active-practice-plan-context [json_payload]
```

作用：

```text
active PracticePlan
→ normalized active_plan_context_items
→ active_practice_plan_context section
```

不做：

```text
不生成推荐
不启动 Routine
不调用 /accompaniment/generate
不生成 MIDI
不调用 engine adapter
```

## 2. Practice Context Assembly Policy

新增：

```text
PracticeContextAssemblyPolicyPayload
build_practice_context_assembly_policy_payload(...)
build_practice_context_assembly_policy_summary(...)
practice_context_assembly_policy_contract()
```

API：

```http
GET  /agent/context/practice-assembly/spec
POST /agent/context/practice-assembly/build
```

CLI：

```text
/practice-context-assembly [json_payload]
```

作用：

```text
active_practice_plan_context
+ routine_history_context
+ today_constraints
→ assembled_practice_context
```

它只生成 LLM / deterministic planner 未来可使用的决策输入，不直接输出“今天练什么”的答案。

## 3. Today Practice Context E2E Preview

新增：

```text
build_today_practice_context_e2e_payload(...)
build_today_practice_context_e2e_summary(...)
today_practice_context_e2e_contract()
```

API：

```http
GET  /agent/context/today-practice/spec
POST /agent/context/today-practice/preview
```

CLI：

```text
/today-practice-context [json_payload]
```

作用：

```text
用户主动问“今天该练什么？”时
→ 预组装 active plan + recent Routine history + available minutes
→ 输出 context-only decision inputs
```

本版本仍然不调用 LLM，也不创建推荐结果。

## 4. ContextBuilder 集成

`ContextBuilder` 现在可以接收：

```text
active_practice_plan / activePracticePlan / practice_plan / practicePlan
routine_history_records / routineHistoryRecords
active_practice_plan_context
routine_history_context
assembled_practice_context
```

并注入：

```text
learner_context.active_practice_plan_context
learner_context.routine_history_context
learner_context.assembled_practice_context
```

新增 task profile：

```text
today_practice_guidance
```

该 profile 是未来 LLM 回答“今天该练什么”的上下文入口。

## 5. 重要边界

本版本明确不做：

```text
不创建 Routine 结束后的 Agent 推荐卡片
不调用 LLM
不输出最终练习建议
不启动 Routine
不调用 /accompaniment/generate
不调用 engine adapter
不生成 MIDI asset
不假设鸿蒙前端 UI 流程
```

Routine 结束页仍由鸿蒙客户端自己处理：

```text
本次练习内容
练习时长
完成状态
已记录
```

Agent 只在下次用户主动发起对话时使用上下文。

## 6. 为什么这算上下文工程基本骨架

因为现在已经有：

```text
当前长期练习计划 → active_practice_plan_context
最近 Routine 记录 → routine_history_context
计划 + 历史 + 今天可用时间 → assembled_practice_context
用户问今天练什么 → today_practice_context preview
```

后续真正让 LLM 输出建议时，不需要重新设计数据入口，只需要在这个 context skeleton 上接入：

```text
LLM Prompt Policy
Recommendation Output Contract
Routine Candidate Follow-up
```

## 7. 验收命令

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src python -m pytest -q tests/test_v2_7_3_agent_context_engineering_skeleton_foundation.py
```
