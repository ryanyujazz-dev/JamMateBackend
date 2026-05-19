# Agent TodayPracticeGuidance Profile-Aware E2E v2_8_3

## Purpose

`v2_8_3_agent_today_practice_guidance_profile_aware_e2e` connects the durable `UserPracticeProfileContext` introduced in v2_8_1 into the existing guarded today-practice guidance chain.

The user-facing scenario is:

```text
用户问：今天该练什么？
→ active PracticePlan context
→ recent RoutineHistory context
→ UserPracticeProfileContext
→ assembled_practice_context
→ TodayPracticeGuidance prompt/provider boundary
→ output validation
→ display-only ActionCard / editable Routine candidates
```

This version does not turn the profile into a rule engine. The profile is soft personalization context only.

## New Surfaces

```text
GET  /agent/context/today-practice-guidance/profile-aware/spec
POST /agent/context/today-practice-guidance/profile-aware/e2e-preview
/today-practice-guidance-profile-aware [json_payload]
```

## New Core Contract

```text
TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION = v2_8_3
TodayPracticeGuidanceProfileAwareE2EPayload
build_today_practice_guidance_profile_aware_e2e_payload
build_today_practice_guidance_profile_aware_e2e_summary
today_practice_guidance_profile_aware_e2e_contract
```

## Profile Context Used

The profile-aware bridge can use:

```text
current_goal
preferred_styles
focus_areas
skill_focus
comfortable_tempo_ranges
avoid
practice_mode_preference
summary_for_llm
```

The bridge also exposes:

```text
profile_context_available
profile_summary
preferred_styles
focus_areas
comfortable_tempo_ranges
profile_is_soft_context_not_rule_engine
recommendation_must_still_consider_active_plan
recommendation_must_still_consider_routine_history
candidate_only_no_execution
```

## Prompt Contract Extension

The existing TodayPracticeGuidance prompt contract now includes a profile-aware policy block:

```text
prompt_policy.profile_aware_policy
```

It tells the future provider that profile context should influence:

```text
- goal alignment
- preferred style
- comfort tempo range
- avoid list
- practice-mode preference
```

But it must not:

```text
- override the active plan by itself
- ignore recent Routine history
- force a tempo by itself
- start Routine
- call /accompaniment/generate
```

The output schema accepts an optional field:

```text
profile_considerations
```

This is a short user-facing note explaining how the user profile affected the candidate suggestion.

## Alignment Preview

The profile-aware payload includes a soft preview:

```text
profile_alignment_preview
```

It reports:

```text
candidate_item_count
preferred_style_match_count
tempo_range_match_count
warnings
alignment_is_soft_warning_only
does_not_block_valid_guidance
```

Tempo/style mismatches are warnings only. They do not block otherwise safe guidance.

## Guards

This contract preserves all Agent safety and boundary rules:

```text
llm call default: disabled
tool execution: disabled
Routine start: disabled
/accompaniment/generate: disabled
engine adapter call: disabled
MIDI asset creation: disabled
playback start: disabled
storage write: disabled
frontend flow assumption: false
client decides presentation: true
```

## Boundaries

Agent line only:

```text
src/jammate_agent/
src/jammate_api/routes/agent_routes.py
Agent tests
Agent docs
```

Not changed:

```text
Engine pattern / voicing / expression / pedal / MIDI generation
demos/*.mid
README.md
agent.md
VERSION
pyproject.toml
shared architecture/API/changelog docs
HarmonyOS fixtures
```

## Test Coverage

`tests/test_v2_8_3_agent_today_practice_guidance_profile_aware_e2e.py` covers:

```text
1. contract is candidate-only
2. prompt policy includes UserPracticeProfileContext as soft context
3. profile-aware E2E payload bridges profile → action card safely
4. ContextBuilder and manifests advertise v2_8_3
5. API routes are side-effect-free
6. terminal command works and preserves guards
```

## Next Recommended Task

```text
v2_8_4_agent_practice_plan_persistence_candidate_contract
```

Recommended scope:

```text
Design save/update PracticePlan as a candidate action with preview + confirmation.
Do not implement full database writes yet unless explicitly requested.
Do not call Engine or start Routine.
```
