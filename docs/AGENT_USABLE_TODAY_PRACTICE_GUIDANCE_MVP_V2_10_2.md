# AGENT_USABLE_TODAY_PRACTICE_GUIDANCE_MVP_V2_10_2

## Purpose

`v2_10_2_agent_usable_today_practice_guidance_mvp` moves the Agent track back from internal preview/guard packaging toward a user-facing MVP:

```text
User: 今天该练什么？
        ↓
Agent optionally auto-reads a configured SQLite context DB
        ↓
Agent recovers profile / active plan / routine history when available
        ↓
Agent returns display-only today-practice guidance or a clear no-context setup message
```

The goal is not another debug pack. The goal is to make the terminal developer build feel like a usable Agent entry point.

## New contract

```text
GET  /agent/context/usable-today-practice-guidance-mvp/spec
POST /agent/context/usable-today-practice-guidance-mvp/preview
CLI  /usable-today-practice-guidance [json_payload]
CLI  ordinary chat: 今天该练什么？
```

Terminal ordinary chat now supports an optional SQLite context DB path through:

```text
--context-db-path <path>
```

or:

```text
JAMMATE_AGENT_CONTEXT_DB_PATH=<path>
```

When either is configured, ordinary turns such as `今天该练什么？` route through the usable MVP surface first. The user does not need to manually run `/persisted-context-autoload-sqlite` before asking.

## Behavior

### With SQLite context configured and recoverable

```text
sqliteDbPath / JAMMATE_AGENT_CONTEXT_DB_PATH
        ↓
read-only SQLite context recovery
        ↓
profile + active plan + routine history recovered
        ↓
display-only today-practice guidance ActionCard preview
```

The surface internally supplies the existing v2_9 readback gates so the user-facing entry does not expose backend gate terminology.

### Fresh install or no context DB configured

The Agent returns an actionable no-context message instead of failing silently:

```text
现在还没有可恢复的练习上下文。可以先保存练习计划/练习记录，或配置 JAMMATE_AGENT_CONTEXT_DB_PATH 后再问：今天该练什么？
```

If a provider / `providerResult` is available, the surface can still fall back to the existing ordinary display-only today-practice guidance chain.

## Response fields

Important API/terminal fields:

```text
agent_usable_today_practice_guidance_mvp_version: v2_10_2
context_source: sqlite_backend | plain_fallback_after_sqlite_miss | none
sqlite_readback_attempted: bool
sqlite_context_recovered: bool
backend_database_read: bool
sqlite_rows_read: int
guidance_action_card_is_valid: bool
routine_candidate_count: int
terminal_response.content: string
```

## Boundaries

Allowed in this milestone:

```text
read an existing safe SQLite context DB when a DB path is explicitly configured
call the LLM provider only through the existing guarded provider boundary when requested/available
return display-only guidance data
```

Still outside this milestone:

```text
starting Routine
calling /accompaniment/generate
calling Engine adapters
creating MIDI
starting playback
writing HarmonyOS local state
creating post-session recommendation cards
performing schema migration
creating SQLite tables from the v2_10 metadata preview
```

The existing v2_9 store route remains responsible for explicit backend writes.

## Files changed

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_10_2_agent_usable_today_practice_guidance_mvp.py
docs/AGENT_USABLE_TODAY_PRACTICE_GUIDANCE_MVP_V2_10_2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

No Engine generation files, HarmonyOS fixture directory, shared root docs, `VERSION`, or `pyproject.toml` were changed.

## Regression

```text
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_10_2_agent_usable_today_practice_guidance_mvp.py
PYTHONPATH=src python -m pytest -q tests/test_v2_10_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py tests/test_v2_10_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py tests/test_v2_9_*.py tests/test_v2_10_*.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Recommended next Agent task

```text
v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp
```

Rationale: now that `今天该练什么？` can read persisted context naturally, the next usable loop should save practice-completion summaries into backend context through a product-facing endpoint, so future guidance is based on actual completed practice.
