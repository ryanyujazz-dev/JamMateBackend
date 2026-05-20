# v2_6_60 — Engine Medium Swing Harmonic-Function-Aware Piano Comping Policy

## Scope

`v2_6_60` continues the Medium Swing piano pattern track after the region-length vocabulary, candidate lookup, weight calibration, and history scorer milestones:

```text
v2_6_56 region-length vocabulary baseline
v2_6_57 region-length candidate lookup
v2_6_58 weight calibration
v2_6_59 history continuity scorer
v2_6_60 harmonic-function-aware comping policy
```

This is not a new pattern source and not a bar-first/two-chord-bar route. The policy reweights the existing ChordRegion-local candidate pool before normal weighted sampling.

## Runtime order

```text
ChordRegion duration
→ existing region-length candidate pool
→ repeat/category guard
→ v2_6_60 harmonic-function multiplier
→ v2_6_59 history scorer multiplier
→ weighted sampling
```

## Harmonic labels

The policy reuses the shared harmony classifier, plus ChordRegion section/ending flags:

```text
section_start
section_end
ending
predominant_to_dominant
dominant_resolution
tonic_resolution
tonic_prolongation
turnaround_like
generic
```

## Weighting intent

- `section_start`, `tonic_resolution`, and `ending` give stable start-anchor cells a small bonus.
- `dominant_resolution` gives answer/tail cells a small bonus but keeps tail-push controlled.
- `predominant_to_dominant` keeps stable support primary and allows only light answer bonus.
- `section_end` supports tail/anchor cells and controls active/tail-push.
- 1-beat and 2-beat regions retain an offbeat boost ceiling so dense harmonic rhythm remains anchor-led.

## Boundaries

The policy does not:

```text
choose voicing
choose AB / rotation / DROP method
write MIDI pitches
write final duration / velocity / pedal
change anticipation
insert gestures
introduce a parallel selector
restore bar-first two-chord-bar logic
```

Selected piano events expose audit metadata:

```text
harmonic_function_comping_policy_version = v2_6_60
harmonic_function_context_label
harmonic_function_multiplier
harmonic_function_reasons
harmonic_function_previous_to_current_type
harmonic_function_current_to_next_type
harmonic_function_window_type
harmonic_function_tags
```

## Validation summary

Focused tests and demo audit confirm:

- the policy metadata is declared in Medium Swing arrangement policy;
- dominant resolutions can favor answer/tail cells without forcing tail-push;
- tonic resolution and section-start contexts favor stable anchors;
- selected piano events carry both v2_6_60 harmonic metadata and v2_6_59 history metadata;
- pattern events remain pitchless and free of final expression or voicing values.

Recommended next task:

```text
v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint
```
