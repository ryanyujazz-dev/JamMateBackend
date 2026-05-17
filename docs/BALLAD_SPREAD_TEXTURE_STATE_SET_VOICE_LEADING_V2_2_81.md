# Ballad SPREAD Texture-State + Set-Based Voice Leading — v2_2_81

Current package:

```text
v2_2_81 — Ballad SPREAD Texture-State + Set-Based Voice Leading
```

## Purpose

This pass corrects the v2_2_80 gap-tightening direction. The previous workaround raised the `1+4` lower root to close large lower/upper gaps. That was rejected because it treated a candidate-selection problem as a register-target problem.

The new direction is:

```text
Keep lower foundation musically natural.
Generate enough upper DROP2 / DROP3 placement candidates.
Combine lower × upper into full candidates.
Use group-aware / set-based voice-leading and whole-voicing scoring to choose the best candidate.
```

## Scope

This is still a default-off Ballad SPREAD dry-run / audit feature. It does not enable the grouping mix in the ordinary Jazz Ballad runtime.

It only affects explicit Ballad SPREAD grouping mix demos / audits using the dry-run override metadata.

## Active grouping set

`1+3` remains removed from the active Ballad SPREAD mix.

Active contracts:

```text
1+4
2+3
2+4
3+3
3+4
```

`3+4` remains climax-oriented and low-frequency.

## Texture-state grouping plan

The mix no longer treats every event as a free independent grouping lottery. It first narrows each event to a compatible texture family, then samples within that family.

Implemented texture families:

```text
root_plus_upper4_phrase:
  1+4 / 2+4

lift_2plus4_3plus3_phrase:
  2+4 / 3+3

ending_climax_phrase:
  2+4 / 3+3 / 3+4
```

This keeps adjacent events inside compatible lower/upper densities and prevents arbitrary jumps such as `1+4 → 3+4 → 2+3` at every chord event.

## Set-based voice-leading

Upper voice-leading now supports unequal note counts.

Old wrong model:

```text
prev_upper[0] -> curr_upper[0]
prev_upper[1] -> curr_upper[1]
prev_upper[2] -> curr_upper[2]
```

New model:

```text
previous upper pitch set
↓
current upper pitch set
↓
partial assignment with:
  common-tone reward
  nearest matched movement
  inserted color voice penalty
  released color voice penalty
```

This means a 3-note upper moving to a 4-note upper can be understood as:

```text
common tones stay
one color tone is inserted
```

not as all voices being index-shifted.

## 1+4 gap fix

The `1+4` lower root is no longer lifted to solve gaps.

Instead:

```text
1+4 lower root remains a natural foundation.
upper 4-note DROP2 / DROP3 candidates are allowed to occupy lower valid placements.
full-candidate selection chooses the voicing with better group gap, top continuity, and set-based voice-leading.
```

The resulting audit shows:

```text
max_group_gap_semitones = 12
large_group_gap_gt12_events = 0
```

## 3+4 invariants preserved

```text
whole register = A1–G5
upper = rootless color-only
DROP2 / DROP3 only
DROP2&4 = 0
source integrity preserved
```

## Audit summary

Reference demo:

```text
total events = 150
1+3 = 0
1+4 = 27
2+4 = 91
3+3 = 29
3+4 = 3
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
whole_register_violations = 0
max_group_gap_semitones = 12
large_group_gap_gt12_events = 0
set_based_voice_leading_events = 131
unequal_upper_assignment_events = 42
```

Expanded 60% demo:

```text
total events = 150
actual_color_upper_events = 90
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
whole_register_violations = 0
max_group_gap_semitones = 12
large_group_gap_gt12_events = 0
set_based_voice_leading_events = 138
unequal_upper_assignment_events = 48
```

## Verification

```text
compileall: OK
pytest: 676 passed
harness: HARNESS OK
```

## Recommended next step

Listen to the v2_2_81 reference and expanded-60% demos. If the texture transitions and previously large-gap measures feel natural, proceed to:

```text
v2_2_82 — Ballad SPREAD Grouping Mix Listening Tuning
```

That next step should tune family weights and scene boundaries, not rewrite the voicing architecture again.
