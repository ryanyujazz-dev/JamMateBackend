# Engine Track Development Task Plan V2

Current baseline: `v2_6_1`.

This file is the rolling plan for `feature/engine-deepening`. It owns accompaniment generation, style rules, voicing/expression/gesture behavior, MIDI realization, and listening demos.

---

## Ownership

Allowed owner paths:

```text
src/jammate_engine/core/
src/jammate_engine/styles/
src/jammate_engine/generation/
src/jammate_engine/performance/
src/jammate_engine/harmony/
src/jammate_engine/midi/
src/jammate_engine/realization/
examples/scripts/generate_standard_tune_v2_examples_demos.py
```

Do not modify Agent workflow code in an Engine task.

---

## Current Engine Baseline

Official engine music baseline preserved in the integrated package:

```text
v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping
```

Important retained engine facts:

- Jazz Ballad defaults to swing-8 feel.
- Ballad anticipation keeps logical `.5` but performs on the swing/triplet upbeat.
- Ballad `beat 1 -> 1&` continuity respects performed swing-upbeat timing.
- Jazz Ballad `inner_movement` is a V2 `GestureRequest`, not a pattern hack.
- Held foundation + partial reattack remains a realization/gesture/expression boundary behavior.
- V1 is only a musical-rule reference; no V1 code migration or runtime mirror.

---

## Recommended Next Engine Task

```text
v2_6_2_engine_jazz_ballad_bass_anchor_path_policy
```

Goal: implement a restrained two-feel Ballad bass anchor path based on the V1 musical-rule audit, but with V2 ownership boundaries.

Expected scope:

- beat 1 root/foundation anchor;
- beat 3 fifth / third / seventh / root / hold selection;
- root-root streak penalty;
- cadence setup bias;
- split-bar restrained behavior;
- low-frequency beat 4 setup only when context asks for it.

Forbidden scope:

- no walking-bass conversion;
- no Agent/LLM changes;
- no V1 code migration;
- no pattern-to-voicing-texture binding;
- no MIDI repair after the fact.

---

## Near-Term Engine Queue

1. `v2_6_2_engine_jazz_ballad_bass_anchor_path_policy`
2. `v2_6_3_engine_jazz_ballad_phrase_color_families_gated`
3. `v2_6_4_engine_jazz_ballad_drums_brush_policy_from_v1_rules`
4. `v2_6_5_engine_medium_swing_piano_phrase_feel_restoration`
5. `v2_6_6_engine_bossa_identity_anticipation_articulation_review`

Each task should produce either a focused audit summary or a three-chorus standard-tune listening demo when music output changes.
