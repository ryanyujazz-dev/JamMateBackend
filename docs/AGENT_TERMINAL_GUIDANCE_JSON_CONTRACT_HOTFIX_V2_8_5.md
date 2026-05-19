# Agent Terminal Guidance JSON Contract Hotfix v2_8_5

## Goal

Make the terminal chat path usable when a configured LLM answers `今天该练什么` with ordinary prose or partial JSON instead of a strict `TodayPracticeGuidanceOutput` object.

This is a terminal/provider compatibility hotfix only. It does not implement storage, does not start Routine, does not call `/accompaniment/generate`, does not execute tools, and does not touch Engine generation.

## Problem Fixed

Some OpenAI-compatible models successfully respond to the prompt but do not return the exact structured JSON required by the strict guidance validator. In v2_8_4 this produced:

```text
Guidance output was blocked by validation.
action_card_is_valid: False
routine_candidate_count: 0
```

That meant the LLM was connected, but terminal UX still looked broken.

## Changes

### 1. Stronger JSON-only prompt

The today-practice prompt now explicitly says:

```text
Return JSON only, with no Markdown, no code fence, and no prose outside the JSON object.
```

It also includes the minimal valid shape inline:

```json
{
  "guidance_mode": "fallback_without_plan",
  "summary": "...",
  "recommended_focus": "...",
  "recommended_blocks": [],
  "routine_candidates": [],
  "user_confirmation_required": true,
  "next_client_actions": ["show_guidance"]
}
```

### 2. Plain-text provider fallback

If the provider call succeeds but returns plain text rather than JSON, terminal guidance now safely coerces it into display-only guidance:

```json
{
  "guidance_mode": "fallback_without_plan",
  "summary": "<provider text>",
  "recommended_focus": "今日练习安排",
  "recommended_blocks": [],
  "routine_candidates": [],
  "user_confirmation_required": true,
  "next_client_actions": ["show_guidance"]
}
```

This keeps terminal testing usable while preserving the safety boundary.

### 3. Partial JSON safe defaults

If the model returns partial JSON, for example only a summary, the provider boundary fills safe defaults:

```text
guidance_mode = fallback_without_plan
recommended_focus = 今日练习安排
user_confirmation_required = true
next_client_actions = [show_guidance]
```

### 4. Safety unchanged

The fallback never enables:

```text
Routine start
Tool execution
Engine adapter call
/accompaniment/generate
MIDI asset creation
Playback start
```

## Tests

New test file:

```text
tests/test_v2_8_5_agent_terminal_guidance_json_contract_hotfix.py
```

Covers:

```text
1. Prompt demands JSON-only output.
2. Plain-text provider response is coerced into valid display-only guidance.
3. Ordinary terminal turn no longer prints validation-blocked message when provider returns plain text.
4. Partial JSON receives safe defaults.
```

## Validation Commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_8_5_agent_terminal_guidance_json_contract_hotfix.py \
  tests/test_v2_8_4_agent_terminal_llm_provider_compatibility_hotfix.py \
  tests/test_v2_8_3_agent_today_practice_guidance_profile_aware_e2e.py \
  tests/test_v2_8_2_agent_practice_context_storage_boundary_contract.py \
  tests/test_v2_8_1_agent_user_profile_context_intake.py \
  tests/test_v2_8_0_agent_context_and_guidance_skeleton_cleanup.py \
  tests/test_v2_7_9_agent_today_practice_guidance_terminal_chat_e2e.py \
  tests/test_v2_7_8_agent_today_practice_guidance_action_card.py \
  tests/test_v2_7_7_agent_today_practice_guidance_provider_boundary_e2e.py \
  tests/test_v2_7_6_agent_today_practice_guidance_output_validation.py \
  tests/test_v2_7_5_agent_user_capability_map_and_intent_taxonomy.py \
  tests/test_v2_7_4_agent_today_practice_guidance_prompt_contract.py \
  tests/test_v2_7_3_agent_context_engineering_skeleton_foundation.py
```

## Next Recommended Task

Continue the original Agent route:

```text
v2_8_6_agent_practice_plan_persistence_candidate_contract
```

Design save/update `PracticePlan` candidate actions with preview + confirmation + no-op boundary first. Do not implement full database writes yet.
