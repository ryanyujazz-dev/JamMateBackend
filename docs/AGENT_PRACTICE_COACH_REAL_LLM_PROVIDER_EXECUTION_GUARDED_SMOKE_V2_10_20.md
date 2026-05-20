# v2_10_20 — Practice Coach Real LLM Provider Execution Guarded Smoke

## Summary

`v2_10_20` real LLM provider smoke adds an opt-in guarded smoke path for the unified Practice Coach endpoint to execute a real OpenAI-compatible LLM provider call using a production-shaped HarmonyOS request.

The endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

The production request fixture intentionally does **not** contain:

```text
llmActionDecisionResult
providerResult
dbPath / sqliteDbPath
clientConfirmedRecordWrite / internal write gate
```

The LLM provider is configured only on the FastAPI server side through environment variables. HarmonyOS still sends only product fields such as `userId`, `sessionId`, `deviceId`, and `userMessage`.

## New smoke assets

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_live_llm_message_request.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_live_llm_provider_smoke.sh
tests/test_v2_10_20_agent_practice_coach_real_llm_provider_execution_guarded_smoke.py
```

## Server-side setup

Before starting FastAPI, configure the provider on the server:

```bash
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_live_llm.sqlite3
export JAMMATE_LLM_PROVIDER=openai_compatible
export JAMMATE_LLM_MODEL=<model>
export JAMMATE_LLM_API_KEY=<key>
export JAMMATE_LLM_ENABLE_NETWORK_CALLS=true
export JAMMATE_LLM_BASE_URL=<openai-compatible-base-url>

PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

For default OpenAI API usage, `JAMMATE_LLM_PROVIDER=openai`, `JAMMATE_LLM_MODEL`, `JAMMATE_LLM_API_KEY`, and `JAMMATE_LLM_ENABLE_NETWORK_CALLS=true` are the key fields; `JAMMATE_LLM_BASE_URL` can stay default if appropriate.

## Run the guarded smoke

The smoke is opt-in:

```bash
cd frontend_fixtures/harmonyos/smoke
JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1 \
  bash curl_practice_coach_live_llm_provider_smoke.sh http://127.0.0.1:8000
```

For phone-to-Mac device smoke:

```bash
JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1 \
  bash curl_practice_coach_live_llm_provider_smoke.sh http://<MAC_LAN_IP>:8000
```

The script asserts:

```text
debug.llmCalled = true
debug.networkCallExecuted = true
debug.llmActionDecisionSource = live_provider
debug.deterministicFallbackUsed = false
debug.llmActionDecisionValidation.ok = true
```

and safety remains:

```text
startsRoutine = false
callsEngineAdapter = false
createsMidiAsset = false
startsPlayback = false
writesHarmonyOSLocalState = false
```

## Local automated test strategy

The v2_10_20 unit test starts a local OpenAI-compatible stub server and points the backend provider config to it. This validates the actual provider path, HTTP payload shape, provider role normalization, JSON parsing, schema validation, and Practice Coach state persistence without depending on an external API key.

The test also confirms the provider network payload is cache-friendly:

```text
roles: system, user, user
stable product contract present
practice context packet present
current user message present
sessionId excluded from prompt text
```

## Boundary

This is still a Practice Coach Agent / Integration task. It does not modify Engine accompaniment generation, style logic, voicing, MIDI generation, playback, or HarmonyOS local persistence behavior.
