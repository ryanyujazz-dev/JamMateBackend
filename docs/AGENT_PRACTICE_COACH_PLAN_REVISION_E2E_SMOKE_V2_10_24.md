# v2_10_24 — Practice Coach Plan Revision E2E Smoke

## Purpose

This milestone turns the v2_10_23 plan-revision routing hotfix into a repeatable HarmonyOS/front-end smoke sequence. It validates the user-facing flow reported by the frontend team without requiring the frontend to create a new session or carry plan rewrite semantics.

The unified product endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

## Covered one-session flow

```text
1. 今天该练什么？
   -> ask_clarifying_question

2. 中级，今天可以练30分钟，目标是提升伴奏稳定性，喜欢 bossa 和 swing。
   -> practice_plan_proposal, 30 min, bossa, awaiting_confirmation=true

3. 我想调整为20分钟
   -> practice_plan_revision, 20 min, revisionReason=adjust_duration

4. 我想多安排基本功和节拍器稳定性练习
   -> practice_plan_revision, fundamentals, revisionReason=adjust_focus

5. 我想换成曲目练习
   -> practice_plan_revision, tune_practice, revisionReason=change_tune

6. 确认这个安排
   -> routine_card_ready, 20 min, tune_practice
```

This explicitly prevents the prior failure mode where a pending draft plan caused the backend to stop at:

```text
existing_draft_plan_waiting_for_confirmation
```

for clear revision requests.

## New smoke assets

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_plan_revision_e2e_sequence.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_plan_revision_e2e_smoke.sh
tests/test_v2_10_24_agent_practice_coach_plan_revision_e2e_smoke.py
```

## Run

Start FastAPI:

```bash
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_revision_e2e.sqlite3
export JAMMATE_LLM_ENABLE_NETWORK_CALLS=false
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

Then run:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_practice_coach_plan_revision_e2e_smoke.sh http://127.0.0.1:8000
```

For a phone/HarmonyOS device, use:

```text
http://<Mac LAN IP>:8000
```

not `127.0.0.1`.

## Product contract boundary

The E2E sequence fixture is product-shaped. It must not include:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
providerResult
llmActionDecisionResult
apiKey
internal write gate
```

Those remain backend/test concerns only.

## Safety boundary

The smoke requires every step to preserve:

```text
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
```

Even `routine_card_ready` only means the frontend may display a Routine card and wait for the user to tap Start. The backend does not start practice automatically.

## Frontend validation guidance

The frontend should now re-run the original reported sequence in the same session and verify:

```text
- Step 3/4/5 produce practice_plan_revision, not a generic waiting-for-confirmation message.
- The displayed plan card updates after every revision.
- Confirming after the last revision creates a Routine card from the latest draft.
- No frontend workaround such as new-session creation or client-side plan rewriting is needed.
```
