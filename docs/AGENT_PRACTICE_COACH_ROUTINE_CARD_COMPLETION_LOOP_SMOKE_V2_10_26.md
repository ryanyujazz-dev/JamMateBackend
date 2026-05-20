# v2_10_26 — Practice Coach Routine Card → Completion → Next Guidance Loop Smoke

## 1. 目标

`v2_10_26` 验证 Practice Coach 的核心产品闭环：

```text
practice_plan_proposal / practice_plan_revision
→ 用户确认
→ routine_card_ready
→ 前端用户手动开始并完成练习
→ POST /agent/harmonyos/routine-completion-record/execute
→ 下一次 POST /agent/harmonyos/practice-coach-session/message/execute
→ Practice Coach context builder 读到 recent_practice_memory_summary
```

这一步是 Agent / Integration 路线 smoke，不改变 Engine 音乐生成逻辑。

## 2. 覆盖接口

```text
POST /agent/harmonyos/practice-coach-session/message/execute
POST /agent/harmonyos/routine-completion-record/execute
```

统一 Practice Coach 入口仍然由 `responseType` 驱动前端 UI：

```text
practice_plan_proposal
practice_plan_revision
routine_card_ready
```

Routine 完成记录仍然由真实练习结束事件显式提交，不由后端自动创建。

## 3. 新增 smoke 文件

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_routine_card_completion_loop_sequence.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_routine_card_completion_loop_smoke.sh
tests/test_v2_10_26_agent_practice_coach_routine_card_completion_loop_smoke.py
```

## 4. 产品序列

```text
1. 中级，今天可以练30分钟，目标是提升伴奏稳定性，喜欢 bossa 和 swing。
   -> practice_plan_proposal / 30 分钟 / bossa

2. 我想调整为20分钟
   -> practice_plan_revision / 20 分钟 / bossa

3. 确认这个安排
   -> routine_card_ready / routineCardPayload

4. 前端完成练习后提交 routineCompletionRecord
   -> completionRecordPersisted=true
   -> nextTodayGuidanceCanReadHistory=true

5. 用户下一次问：今天该练什么？
   -> llmRequestPreview.sourceProjection.sqliteRowsRead >= 1
   -> recent_practice_memory_summary.recent_sessions 包含刚完成的 routine
   -> item_summaries 和 user_note_summary 进入 LLM context projection
```

## 5. 关键验证点

完成记录写入后，下一次 Practice Coach 请求的 `llmRequestPreview.contextBlocks` 中应包含：

```text
contextBlocks[name=recent_practice_memory_summary].payload.recent_sessions[0].title
contextBlocks[name=recent_practice_memory_summary].payload.recent_sessions[0].item_summaries
contextBlocks[name=recent_practice_memory_summary].payload.recent_sessions[0].user_note_summary
```

这说明 Routine 完成记录不只是写入成功，而是已经进入下一次 LLM 上下文投影。

## 6. 安全边界

整个 smoke 保持：

```text
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
```

`routine_card_ready` 只表示前端可以展示 Routine 卡片；真正开始练习仍然必须由用户点击开始。练习结束后也不自动弹 Agent 推荐卡片，只记录完成；下一次用户主动问“今天该练什么？”时再进入 Practice Coach。

## 7. 运行方式

启动后端：

```bash
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_completion_loop.sqlite3
export JAMMATE_LLM_ENABLE_NETWORK_CALLS=false
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

运行 smoke：

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_practice_coach_routine_card_completion_loop_smoke.sh http://127.0.0.1:8000
```

真机联调时使用：

```text
http://<Mac局域网IP>:8000
```

不要使用手机端的 `127.0.0.1`。

## 8. 前端后续验证重点

前端需要在真实 UI 里验证：

```text
1. routine_card_ready 是否显示 Routine 卡片。
2. 用户点击开始后是否进入练习流程。
3. 用户完成练习 / 计时结束 / 点击完成时，是否调用 routine-completion-record/execute。
4. 完成页只显示本次练习已记录，不自动弹 Agent 推荐卡片。
5. 用户下一次主动点击“获取建议”时，Practice Coach 是否读到这次完成历史。
```

## 9. 下一步建议

`v2_10_27` 建议进入 HarmonyOS UI 接线反馈：

```text
Practice Coach 多轮对话 UI
routine_card_ready 卡片展示
RoutineFocusPage / RoutineSummaryPage 完成事件绑定
completion record 真机提交
下次 Practice Coach 读取历史的 UI 验证
```
