# v2_2_84 — Ballad SPREAD Upper Structure Harmonic Expansion / Altered Dominant Policy Gate

## Purpose

v2_2_84 turns the v2_2_83 Upper Structure pilot into a policy-gated source family. Upper Structure remains part of `core/voicing/sources`; it does not create a parallel voicing or projection system.

The key architectural correction is that Upper Structure entry metadata no longer silently enables harmonic expansion. It only opens the Upper Structure candidate doorway. Actual source authorization is decided by two semantic controls:

```text
harmonic_expansion_enabled
altered_dominant_policy / altered_dominant_enabled
```

## Stable architecture rules

```text
Upper Structure = source / content family
SPREAD = lower/upper grouping, register, spacing, candidate combination
CLOSED/OPEN projection = existing closed/inversion/DROP projection resources
Selection = full-candidate guard + top-voice / set-based voice-leading scorer
```

Upper Structure projection reuse remains mandatory:

```text
3-note Upper Structure:
  reuse existing 3-note closed parent + inversion placement

4-note Upper Structure:
  reuse existing 4-note closed parent + inversion + DROP2 / DROP3
  SPREAD upper 4-note still forbids DROP2&4
```

Lower group gate for Upper Structure remains restricted:

```text
allowed lower modes:
  shell
  root_plus_shell
```

Low-register density guard remains active:

```text
below E2 / MIDI40:
  max 1 note
```

## Policy semantics

### 1. No expansion, no altered

```text
harmonic_expansion_enabled = false
altered_dominant_enabled = false
```

Behavior:

```text
Do not introduce Upper Structure for plain chord symbols.
Only chord-symbol material is legal.
```

### 2. Expansion only

```text
harmonic_expansion_enabled = true
altered_dominant_enabled = false
```

Behavior:

```text
Allow safe Upper Structure at low / controlled frequency.
Dominant Upper Structures use safe color sources, not altered sources.
```

Example safe dominant source:

```text
US II major / lydian dominant color:
  9 #11 13
```

### 3. Expansion + altered dominant

```text
harmonic_expansion_enabled = true
altered_dominant_enabled = true
```

Behavior:

```text
Dominant Upper Structures are authorized to use the altered source pool.
Selected dominant Upper Structure sources should be altered, while non-dominant maj7 contexts may still use safe major-color sources.
```

### 4. Altered enabled without expansion

```text
harmonic_expansion_enabled = false
altered_dominant_enabled = true
```

Behavior:

```text
Do not allow altered Upper Structure for plain dominant chord symbols.
Explicit altered chord symbols such as G7alt, G7b9, G7#9, G7b13 remain legal chart material.
```

## Implementation notes

New/updated policy surface:

```text
AlteredDominantIntensity
AlteredDominantScope
AlteredDominantPolicyDecision
resolve_altered_dominant_policy(policy, chord)
```

Upper Structure source metadata now includes:

```text
upper_structure_policy_gate_v2_2_84
upper_structure_profile_kind_safe / altered
upper_structure_harmonic_expansion_enabled_true / false
upper_structure_altered_dominant_enabled_true / false
upper_structure_altered_dominant_authorized_true / false
```

The source resolver currently honors the altered-dominant policy gate by dominant chord quality and explicit altered chord symbols. The `scope` field is prepared for future harmonic-context integration, where the engine can narrow altered behavior to functional dominants, selected regions, or LLM-selected spans.

## Demo / audit summary

All demos use Misty / Jazz Ballad / SPREAD dry-run, 3 choruses. Default Jazz Ballad runtime remains unchanged.

### No expansion / no altered

```text
events = 150
upper_structure_events = 0
dominant_events = 48
dominant_upper_structure_events = 0
actual_color_upper_events = 1
source_integrity_rejected_events = 0
fallback_non_spread_events = 0
DROP2&4 = 0
whole_register_violations = 0
max_group_gap_semitones = 7
max_top_voice_abs_motion_semitones = 9
```

### Expansion only

```text
events = 150
upper_structure_events = 23
upper_structure_profile_kind = safe: 23
upper_structure_quality_gates = dominant_safe: 13, maj7_safe: 10
dominant_events = 48
dominant_upper_structure_events = 13
dominant_upper_structure_altered_events = 0
dominant_upper_structure_altered_ratio = 0.0
actual_color_upper_events = 90
source_integrity_rejected_events = 0
fallback_non_spread_events = 0
DROP2&4 = 0
whole_register_violations = 0
max_group_gap_semitones = 7
max_top_voice_abs_motion_semitones = 7
```

### Expansion + altered dominant

```text
events = 150
upper_structure_events = 22
upper_structure_profile_kind = altered: 11, safe: 11
upper_structure_quality_gates = dominant_altered: 11, maj7_safe: 11
dominant_events = 48
dominant_upper_structure_events = 11
dominant_upper_structure_altered_events = 11
dominant_upper_structure_altered_ratio = 1.0
actual_color_upper_events = 90
source_integrity_rejected_events = 0
fallback_non_spread_events = 0
DROP2&4 = 0
whole_register_violations = 0
max_group_gap_semitones = 7
max_top_voice_abs_motion_semitones = 7
```

## Next recommended task

If the user approves the three semantic colors, the next task should be:

```text
v2_2_85 — Altered Dominant Functional Scope / LLM Semantic Control Tuning
```

This should integrate harmonic-context/function information so `scope=functional_dominants` can distinguish resolving V7, secondary dominants, static/blues dominants, backdoor dominants, and user/LLM-selected altered spans.
