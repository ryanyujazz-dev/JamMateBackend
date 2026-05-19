# Engine Voicing SPREAD Groupwise Voice-Leading Split — v2_6_12

## Scope

This is a voicing-only, behavior-preserving split.

The goal is to give SPREAD groupwise voice-leading / ranking / continuity a clear owner without changing musical output, density mix, source weights, safe-extension color policy, expression, pedal, gesture timing, pattern selection, MIDI writing, Agent behavior, API contract, or shared project metadata.

## New owner

```text
src/jammate_engine/core/voicing/disposition/spread_voice_leading.py
```

The new owner contains:

```text
SpreadGroupwiseVoiceLeadingWeights
SpreadGroupwiseVoiceLeadingScore
compute_groupwise_motion_score
score_spread_groupwise_voice_leading
rank_spread_candidates_by_group_motion
rank_spread_candidates_by_groupwise_voice_leading
select_spread_candidate_by_groupwise_voice_leading
lower_group_motion_distance
upper_group_motion_distance
top_voice_continuity_distance
spread_voice_leading_debug
spread_groupwise_voice_leading_path_debug
```

`spread.py` remains the public compatibility facade and still re-exports the existing v2_2_41 public API names.

## Boundary rule

SPREAD voice-leading is notes-only:

```text
Input:  SpreadProjectionCandidate / previous SpreadProjectionCandidate
Output: SpreadGroupwiseVoiceLeadingScore / ranked candidate list
```

It may score:

```text
lower/foundation group motion
upper/projection group motion
top voice continuity
group gap stability
overall span penalty
register penalty
legality penalty
```

It must not decide:

```text
Pattern
Anticipation
Expression
Pedal
Gesture
MIDI
Agent behavior
API behavior
```

## Behavior preserved

This split preserves the v2_6_10 Ballad SPREAD density reset:

```text
4-note SPREAD 1+3 / 2+2 are not default Jazz Ballad runtime paths
5-note 2+3 remains the normal Ballad SPREAD body
6-note 2+4 / 3+3 remain fuller support / lift paths
7-note 3+4 remains low-frequency ending / climax texture
```

It also preserves the v2_6_11 Ballad safe-extension color gate:

```text
plain maj7 -> prefer 9 / 13
unnotated maj7#11 -> not default warm Ballad safe extension
written maj7#11 or explicit harmonic-color intent -> #11 allowed
```

## Validation

New regression test:

```text
tests/test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split.py
```

It verifies:

```text
spread_voice_leading.py is the implementation owner
spread.py no longer directly defines the groupwise scoring/ranking classes/functions
public import compatibility remains intact
Cmaj7 / G7b9 / Bm7b5 spread_2plus3 signatures remain stable
groupwise scoring remains notes-only and componentized
```
