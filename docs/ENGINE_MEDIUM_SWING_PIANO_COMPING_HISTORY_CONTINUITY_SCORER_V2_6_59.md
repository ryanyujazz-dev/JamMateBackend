# v2_6_59 — Engine Medium Swing Piano Comping History Continuity Scorer

## Scope

This is an Engine / Medium Swing piano pattern pass. It continues the existing `styles/medium_swing/comping_patterns.py` region-length pattern line and does **not** introduce a parallel selector, shadow pattern source, voicing rule, expression parameter, gesture, API change, Agent change, or HarmonyOS fixture change.

## Design intent

`v2_6_56` established ChordRegion-first pitchless piano rhythm vocabulary. `v2_6_57` activated region-length-aware candidate lookup. `v2_6_58` calibrated stable/offbeat/active/tail-push weights.

`v2_6_59` adds a lightweight history continuity scorer on top of the same candidate pool:

```text
ChordRegion duration
→ existing region-length candidate pool
→ existing repeat/category guards
→ v2_6_59 history reweighting
→ normal weighted sampling
```

The scorer is intentionally small. It does not create new patterns and does not decide voicing, expression realization, or anticipation.

## Scorer behavior

The scorer tracks a short recent piano-comping history window and applies multipliers to candidates:

- exact repeat: strong penalty
- repeated non-stable rhythm family: penalty
- repeated stable family: mild penalty
- consecutive offbeat: penalty
- recent offbeat cluster: penalty
- recent active: strong penalty
- recent tail-push: very strong penalty
- stable reset after active/tail-push: small bonus
- stable reset after offbeat: small bonus

The selected events carry audit metadata:

```text
history_continuity_scorer_version = v2_6_59
history_continuity_scorer_applied
history_continuity_multiplier
history_continuity_reasons
history_continuity_class
history_continuity_previous_class
history_continuity_previous_candidate
```

## Current demo/audit checkpoint

Generated standard-tune demos:

- All The Things You Are / Medium Swing / 3 choruses
- Autumn Leaves / Medium Swing / 3 choruses

Key acceptance:

- history metadata applied to all piano events
- no exact consecutive piano pattern repeats at region level
- no consecutive active region-level choices
- no consecutive tail-push region-level choices
- top register remains calm (`top_note_ge_75_events = 0`)
- OPEN/DROP voice-leading warnings remain zero

## Boundary notes

The scorer does not replace region-length candidate lookup. It only reweights candidates that already came from the existing style-owned pattern source.

Pattern events remain pitchless and carry only semantic expression hints; final velocity, duration, release, pedal, voicing content, DROP method, and AB/rotation are still owned by their downstream layers.

## Recommended next task

`v2_6_60_engine_medium_swing_harmonic_function_aware_piano_comping_policy`

The next step should add harmonic-function-aware weighting on top of the existing ChordRegion-first vocabulary, for example tonic-resolution regions favoring stable anchors, dominant regions allowing slightly more answer/tail behavior, and phrase-release regions reducing active/busy cells.
