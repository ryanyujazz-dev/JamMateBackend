# v2_6_57 — Engine Medium Swing Piano Region-Length Candidate Lookup Policy

## Scope

This milestone continues the Medium Swing piano pattern track in the existing style-owned source:

```text
src/jammate_engine/styles/medium_swing/comping_patterns.py
```

It does **not** create a parallel pattern source, a bar-first selector, or a `two_chord_bar` path.  The v2_6_56 vocabulary baseline remains the library version; v2_6_57 adds a candidate-lookup / activation policy on top of that vocabulary.

No Agent, API, HarmonyOS, MIDI writer, voicing selector, anticipation runtime, or final expression-parameter logic is changed.

## Core contract

```text
ChordRegion.duration_beats
  -> region_length_family
  -> region-local candidate family
  -> weighted sampling
```

Supported current families:

```text
one_beat_region
two_beat_region
four_beat_region
```

Future-safe placeholders remain for:

```text
three_beat_region
five_beat_region
long_region
```

## What changed

- Added `CANDIDATE_LOOKUP_POLICY_VERSION = "v2_6_57"`.
- Added candidate metadata:
  - `candidate_lookup_policy_version`
  - `candidate_lookup_policy=region_length_aware`
  - `candidate_lookup_key`
  - `candidate_lookup_contract`
- Conservatively activated a subset of v2_6_56 zero-weight vocabulary with low positive weights inside its matching region-length family.
- Kept `PATTERN_LIBRARY_VERSION = "v2_6_56"` so vocabulary identity and the v2_6_56 boundary tests remain stable.
- Updated arrangement policy metadata with `piano_region_length_candidate_lookup_policy_version = "v2_6_57"`.
- Updated older exact-count voicing tests to assert invariant behavior rather than frozen event counts, because piano pattern activation can legitimately increase same-region reattack counts while the reuse/cache invariants remain true.

## Activation posture

This is not the full weight-calibration step.  New region-length vocabulary is intentionally conservative:

```text
4-beat region:
  1,3 / 1,2&,4 / 1&,3 / 2&,4 / delayed answer are low positive weight
  rare 4& push variants remain extremely low

2-beat region:
  start,local2 / start,local1& / local1& are low positive weight

1-beat region:
  start remains dominant
  local& is very low positive weight
  rest_if_covered remains zero-weight until coverage policy explicitly supports it
```

## Demo / audit checkpoints

All The Things You Are / Medium Swing / 3 choruses:

```text
pattern_candidate_count: 120
region_length_candidate_counts: {four_beat_region: 96, two_beat_region: 24}
active_region_length_lookup_candidate_count: 8
tail_push_or_4and_candidates: 0
same_chord_reattack_events: 60
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0
```

Autumn Leaves / Medium Swing / 3 choruses:

```text
pattern_candidate_count: 162
region_length_candidate_counts: {two_beat_region: 132, four_beat_region: 30}
active_region_length_lookup_candidate_count: 4
tail_push_or_4and_candidates: 0
same_chord_reattack_events: 66
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0
```

## Acceptance

- Existing Medium Swing piano source remains the only normal comping source.
- 1/2/4-beat regions route to their own region-local candidate families.
- No `two_chord_bar` naming/tags/categories return in the normal piano comping source.
- Pattern events remain pitchless and carry semantic expression hints, not final velocity/duration/pedal values.
- Safe-extension/top-register guardrails remain calm: no top-note >= 75 events and no voice-leading warnings in the two standard-tune demos.

## Recommended next task

```text
v2_6_58_engine_medium_swing_piano_region_length_weight_calibration
```

Tune the newly activated vocabulary ratios more musically: stable remains the subject, offbeat/conversation stays controlled, and 4& push remains rare.
