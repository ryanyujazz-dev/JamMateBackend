# AGENT User Capability Map and Intent Taxonomy v2_7_5

## Scope

This Agent-track document defines what a JamMate user can ask the LLM/Agent to do inside the Routine workflow, which outputs are candidate-only, which actions require confirmation, and which actions are forbidden for LLM autonomy.

This version is a contract and planning surface only.

```text
No LLM call
No tool execution
No Routine start
No /accompaniment/generate call
No engine adapter call
No MIDI asset creation
No playback start
```

## New surfaces

```http
GET  /agent/capabilities/user-intents/spec
POST /agent/capabilities/user-intents/preview
```

```text
/user-capability-map [json_payload]
```

## User capability layers

```text
pure_coach_qa
→ direct explanation / coaching answer, no side effect

context_guidance
→ user-initiated today-practice or history-review guidance, no automatic post-session card

candidate_generation
→ PracticePlanCandidate / RoutineConfigCandidate / RoutineCandidate / PlaybackPrepareCandidate

confirmation_required_actions
→ save/update/start/generate style actions, must go through preview + confirmation + executor/dispatcher/trace

forbidden_direct_actions
→ direct playback, direct /accompaniment/generate, engine internals, pattern/voicing/expression/pedal mutation
```

## Intent taxonomy

Current taxonomy includes:

```text
today_practice_guidance
practice_plan_generation
routine_config_prepare
playback_prepare_guarded
difficulty_adjustment
practice_explanation
routine_history_review
```

The taxonomy is intentionally UI-flow neutral. HarmonyOS decides whether a candidate becomes a Setup page, Bottom Sheet, queue item, template, or another presentation.

## Routine boundary

Routine completion remains client-owned.

```text
Routine结束页：鸿蒙客户端显示本次练了什么、练了多久、已记录。
Agent不自动生成练习结束推荐卡片。
```

Agent uses Routine history later, on the next user-initiated LLM turn such as:

```text
今天该练什么？
```

At that point, ContextBuilder may combine:

```text
active_practice_plan_context
routine_history_context
available_minutes
user profile / goals when available
```

## Side-effect policy

```text
none
→ direct answer or candidate/context preview allowed

low
→ saved user-facing state; requires explicit preview and confirmation before real execution

high
→ MIDI asset generation, playback, Routine start, backend generation calls; requires strict confirmation and dedicated executor boundary

engine_internal
→ forbidden for LLM autonomy; Engine-track development only
```

## Non-goals

```text
Do not call LLMs in this contract.
Do not validate final LLM output yet.
Do not start Routine.
Do not call /accompaniment/generate.
Do not generate MIDI.
Do not modify Engine music-generation rules.
Do not assume HarmonyOS frontend flow.
```

## Next recommended step

```text
v2_7_6_agent_today_practice_guidance_output_validation
```

After the capability map is explicit, the next step can validate future `TodayPracticeGuidanceOutput` responses against this taxonomy and side-effect policy.
