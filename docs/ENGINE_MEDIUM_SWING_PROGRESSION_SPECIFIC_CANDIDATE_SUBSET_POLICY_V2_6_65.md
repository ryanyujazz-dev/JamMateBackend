# v2_6_65 — Engine Medium Swing Progression-Specific Candidate Subset Policy

## Scope

This milestone translates the useful V1 Medium Swing piano `major_251` / `minor_251` / `two_five` / `ii_setup` candidate-priority idea into the V2 ChordRegion-first architecture.

It does **not** restore V1 bar-first templates, `two_chord_bar` routing, pattern-level voicing texture expansion, final MIDI velocity/duration/pedal values, gesture logic, Agent/API/HarmonyOS changes, or a parallel selector.

## Runtime placement

The existing Medium Swing piano selection path remains:

```text
ChordRegion-length candidate pool
→ repeat/category guard
→ v2_6_65 progression-specific preferred subset policy
→ v2_6_60 harmonic-function multiplier
→ v2_6_59 history scorer
→ weighted sampling
→ v2_6_62 CoverageGuard
→ Anticipation / Expression / Voicing
```

The new policy is a preferred-subset reweight inside the existing candidate pool. It never creates a separate pattern source.

## V1 → V2 translation

| V1 idiom | V2 translation |
|---|---|
| `major_251` / `minor_251` V→I templates | dominant-resolution ChordRegion preferred subset |
| `two_five` / `ii_setup` templates | predominant-to-dominant ChordRegion preferred subset |
| `two_chord_bar` templates | already translated as 2-beat / 1-beat ChordRegion vocabulary |
| shell2/shell4/rootless4 texture expansion | rejected from pattern layer; remains voicing policy |

## Audit metadata

Selected piano events may now carry:

```text
progression_specific_subset_policy_version = v2_6_65
progression_specific_subset_policy_applied
progression_specific_context_label
progression_specific_subset_key
progression_specific_subset_status
progression_specific_subset_multiplier
progression_specific_subset_reasons
```

## Acceptance

- Pattern candidates remain pitchless and region-local.
- No pattern or pattern event contains final velocity/duration/pedal values.
- No bar-first `two_chord_bar` / `split_bar` route is restored.
- Existing harmonic-function multiplier, history scorer, coverage guard, expression handoff, and voicing system remain active.
- Standard-tune demos remain top-register and voice-leading safe.

## Recommended next task

`v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement`
