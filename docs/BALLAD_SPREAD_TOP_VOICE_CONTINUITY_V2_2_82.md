# Ballad SPREAD Top-Voice Continuity Scoring — v2_2_82

## Version

```text
v2_2_82 — Ballad SPREAD Top-Voice Continuity Scoring
```

## Purpose

This pass optimizes the Ballad SPREAD grouping mix after the v2_2_81 texture-state + set-based voice-leading work.

The key musical correction is: **the highest sounding voice is a stable audible anchor even when lower/upper note counts change.** Therefore the SPREAD selector should directly compare the previous voicing top note and the current full-candidate top note, and prefer the closer soprano line.

## What changed

```text
1. Added SPREAD top-voice continuity profile:
   previous_top_voice
   current_top_voice
   top_voice_motion
   top_voice_abs_motion
   label: close / acceptable / moderate / large / extreme
   cost

2. Added top-voice continuity cost into SPREAD groupwise candidate collapse.

3. Opened compatible texture-family candidate pools for the dry-run mix:
   root_plus_upper4_phrase:
     spread_1plus4_contract
     spread_2plus4_contract

   lift_2plus4_3plus3_phrase:
     spread_2plus4_contract
     spread_3plus3_contract

   ending_climax_phrase:
     spread_2plus4_contract
     spread_3plus3_contract
     spread_3plus4_contract

4. Candidate selection no longer hard-selects one grouping before voicing.
   The policy still defines the texture family and scene, but compatible contracts
   can enter the same candidate pool and the final full-candidate scorer decides.

5. Audit now reports:
   top_voice_continuity_events
   top_voice_continuity_labels
   top_voice_profile_avg_abs_motion_semitones
   top_voice_profile_max_abs_motion_semitones
   large_top_jump_gt7_events
   extreme_top_jump_gt12_events
   top_voice_profile_motion_distribution
```

## Boundary

This remains an explicit Ballad SPREAD dry-run / listening pilot. It does not enable the ordinary Jazz Ballad runtime by default.

```text
style_runtime_default_enabled = false
candidate_conversion_allowed_only_in_explicit_demo_override = true
default_ballad_runtime_unchanged = true
```

## Important retained rules

```text
1+3 remains removed from active Ballad SPREAD mix.
3+4 remains sparse / climax-oriented.
3+4 remains A1–G5.
3+4 upper remains rootless color-only.
SPREAD upper 4-note still uses DROP2 / DROP3 only.
DROP2&4 remains excluded from SPREAD upper 4-note.
Source integrity gate remains preserved.
```

## Demo audit summary

Reference demo:

```text
events = 150
selected_groupings:
  1+4 = 14
  2+4 = 69
  3+3 = 65
  3+4 = 2
avg_top_voice_abs_motion = 1.752 semitones
max_top_voice_abs_motion = 7 semitones
large_top_jump_gt7_events = 0
extreme_top_jump_gt12_events = 0
max_group_gap = 12
large_group_gap_gt12_events = 0
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
whole_register_violations = 0
```

Expanded 60% demo:

```text
events = 150
selected_groupings:
  1+4 = 13
  2+4 = 55
  3+3 = 80
  3+4 = 2
actual_color_upper_events = 90
avg_top_voice_abs_motion = 1.503 semitones
max_top_voice_abs_motion = 7 semitones
large_top_jump_gt7_events = 0
extreme_top_jump_gt12_events = 0
max_group_gap = 12
large_group_gap_gt12_events = 0
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
whole_register_violations = 0
```

## Why this is better than register patching

The rejected v2_2_80 approach solved some gaps by raising the 1+4 lower root. That was not architecturally ideal because it moved the foundation instead of letting the full candidate selector choose a better upper placement.

v2_2_82 solves the problem at the selection level:

```text
texture family
↓
compatible SPREAD contracts
↓
all legal lower × upper candidates
↓
set-based voice-leading for unequal note counts
↓
top-voice continuity scoring
↓
whole-candidate final selection
```

This keeps the lower/foundation group natural while giving the audible soprano line strong continuity.

## Recommended next step

Listen to the v2_2_82 reference and expanded-60% demos. If the highest voice feels stable and the texture density is acceptable, the next task should be:

```text
v2_2_83 — Ballad SPREAD Grouping Mix Listening Tuning
```

That step should tune texture-family weights and scene boundaries, not rebuild the voicing architecture again.
