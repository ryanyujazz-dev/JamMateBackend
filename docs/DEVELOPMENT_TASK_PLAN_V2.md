# JamMate Development Task Plan V2

Current baseline: `v2_6_1`.

This file is now the stable integration index. To reduce Agent/Engine merge conflicts, rolling task plans are split:

```text
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
```

Rules:

- Engine feature branches update only `DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`.
- Agent feature branches update only `DEVELOPMENT_TASK_PLAN_AGENT_V2.md`.
- This main file is updated only by integration tasks or explicit user request.
- Track ownership is defined in `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

## Current Recommended Next Tasks

```text
Engine: v2_6_2_engine_jazz_ballad_bass_anchor_path_policy
Agent: no required implementation before the next Engine pass
Integration: only when either track needs shared API/docs/version reconciliation
```

---


## v2_5_10 Agent / Engine Integration Merge

Current integrated baseline: `v2_5_10`. Agent workflow is merged through `v2_4_13_agent_tool_call_preview_trace_contract`; engine-deepening is merged through `v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping`. Resume engine work only after this package passes harness and smoke tests. Recommended next engine task: `v2_5_11_jazz_ballad_bass_anchor_path_policy`. Recommended Agent continuation should remain in Agent-owned modules and must not alter engine generation runtime.


Current baseline: `v2_5_9`.

`v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping` is a documentation-only engine planning baseline based on the audible `v2_5_8` Ballad swing-8 timing patch. It explicitly discards the earlier experimental Ballad brush-drums shortcut and records the required V1-to-V2 musical-rule mapping in `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.

---

## Immediate Branch Split

### Agent branch

```text
feature/agent-workflow
```

Scope:

- JamMate Agent workflow
- Practice Agent
- LLM context engineering
- bounded tool loop
- HarmonyOS API / contracts / fixtures
- trace/debug inspection

Suggested next task:

```text
v2_4_0_agent_llm_context_runtime_foundation
```

### Engine branch

```text
feature/engine-deepening
```

Scope:

- JamMatePyEngine music generation
- voicing
- pattern selection
- expression / touch / dynamics / pedal
- style tuning
- listening demos

Suggested next task:

```text
v2_5_10_jazz_ballad_bass_anchor_path_policy
```

---

## Engine Deepening Roadmap after v2_5_9

```text
v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping — completed, docs only
v2_5_10_jazz_ballad_bass_anchor_path_policy — next audible pass
v2_5_11_jazz_ballad_brush_semantic_policy — after bass, policy dimensions before hits
v2_5_12_jazz_ballad_251_color_families_gated — gated phrase/color families
v2_5_13_medium_swing_piano_phrase_feel_restoration — statement/answer and 4& rarity
v2_5_14_medium_swing_bass_classic_fill_branch_review — scene-gated classic fills
v2_5_15_bossa_identity_anticipation_articulation_review — core batida, A/B ratio, anticipation separation
v2_5_16_bossa_percussion_groove_identity_review — shaker/cross-stick/kick layers
```

Rule: V1 is a musical-rule reference only. Do not migrate V1 code, file structure, runtime mirrors, pattern-texture binding, or MIDI repair paths. Inner movement belongs to V2 gesture semantics, not ordinary pattern cells.

---

## v2_5_9 delivery result: V1 Instrument Rules Deep Audit and V2-Native Mapping

- Rebased official planning baseline on `v2_5_8`; the previous experimental Ballad brush-drums shortcut is not carried forward.
- Added `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.
- Audited V1 Jazz Ballad, Medium Swing, and Bossa Nova piano/bass/drums behavior.
- Mapped each absorbed musical rule to V2 owners: pattern, gesture, expression, voicing, bass foundation, percussion policy, fill policy, or harmony context.
- No generation code changed. No Agent/LLM logic changed.

Recommended next task:

```text
v2_5_10_jazz_ballad_bass_anchor_path_policy
```

---

## v2_5_2 delivery result: Jazz Ballad Gesture Contract Foundation

- Extended existing `styles/jazz_ballad/gesture_policy.py`; no new gesture subsystem was created.
- Opened only pitchless `inner_movement` and `rolled_onset` style-approved requests.
- Added helper constructors and validation that reject V1-style voicing texture metadata, concrete MIDI/pitch data, final duration/velocity/pedal data, and unknown legacy slot keys.
- Kept default Jazz Ballad runtime comping selection unchanged. The next pass should add phrase-intent candidates that may request these gestures without choosing notes or voicing textures.

## v2_5_3 delivery result: Jazz Ballad Phrase Intent Foundation

- Extended existing `styles/jazz_ballad/comping_patterns.py`; no V1-style phrase engine or new runtime path was created.
- Added phrase-intent metadata for `warm_pad`, `breath_answer`, `two_chord_soft_marks`, and context-gated `major_251_stable_cadence`.
- Phrase candidates may request approved pitchless gestures but still cannot choose notes, voicing textures, expression values, pedal, source degrees, or MIDI repair behavior.
- Reused `core/harmony/harmonic_context.py` for the conservative `major_ii_v_i` context gate instead of adding a new recognizer.
- Kept deterministic no-rng Ballad selection anchored on the warm pad until partial-reattack realization is implemented.

Recommended next task:

```text
v2_5_9_ballad_bass_anchor_path
```


## v2_5_4 delivery result: Held Foundation Partial Reattack Realization

- Updated Jazz Ballad inner-movement realization without migrating V1 code or adding a V1-style phrase engine.
- `INNER_MOVEMENT` now projects only the requested inner/color voice or group instead of appending all unselected voices.
- Expression next-event duration clamping ignores non-interrupting partial reattack gestures so warm anchors can hold through inner motion.
- Harmonic realization trims only the voices re-struck by the inner movement; foundation/common-tone notes remain sustained.
- Pattern, gesture, expression, voicing, and realization boundaries remain separate.

Recommended next task:

```text
v2_5_8_ballad_bass_anchor_path
```



## v2_5_8 delivery result: Jazz Ballad Default Swing-8 Anticipation Timing Patch

Corrected Jazz Ballad timing-feel ownership. The style timing profile now uses `feel=swing`, and Ballad anticipation now mirrors the swing-upbeat contract: logical `4&` remains at `.5` in the pitchless timeline, but the event carries `timing_intent=swing_upbeat`, `timing_grid=swing_triplet_upbeat`, and a performed lead-in of `1/3`. This does not move pattern events to literal `0.666...`, does not migrate V1 code, and does not change notes, voicing texture, expression values, pedal behavior, API behavior, or Agent/LLM logic. Recommended next task: `v2_5_9_ballad_bass_anchor_path`.

## v2_5_6 delivery result: Jazz Ballad Swing 1& Timing Patch

Corrected the previous Ballad `1&` patch so logical `0.5` is interpreted through the existing V2 swing-upbeat timing contract. The pattern layer still writes logical `.5`; the second `1&` touch now carries `timing_intent=swing_upbeat`, so render timing performs it at `2/3`. No notes, voicing texture, expression values, pedal behavior, gesture logic, API behavior, or Agent/LLM code changed. Recommended next task: `v2_5_7_ballad_bass_anchor_path`.

## v2_5_5 delivery result: Jazz Ballad Two-Beat 1& Pattern Patch

Corrected the Jazz Ballad two-beat piano soft-mark timing from local beat `1.0` to `0.5`, so the feel is beat 1 + beat 1& rather than beat 1 + beat 2. This did not change notes, voicing texture, expression values, pedal behavior, or Agent/LLM logic. Recommended next task: `v2_5_7_ballad_bass_anchor_path`.
