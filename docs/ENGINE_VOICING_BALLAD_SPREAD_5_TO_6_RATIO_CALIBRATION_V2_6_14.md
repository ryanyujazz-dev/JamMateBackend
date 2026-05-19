# Engine Voicing Ballad SPREAD 5-to-6 Ratio Calibration — v2_6_14

## Scope

`v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration` is a voicing-only listening calibration pass.

The user requested the Jazz Ballad/SPREAD density mix be adjusted so 5-note and 6-note voicings are approximately:

```text
5-note:6-note ~= 6:4
```

This pass continues the v2_6_10 density-system reset and v2_6_13 selected-contract bias mechanism.  It does not create a new density system and does not reopen retired 4-note SPREAD groupings.

This pass does not touch:

```text
Pattern
Anticipation
Expression
Pedal
Gesture
MIDI writer
Agent
API contract
HarmonyOS fixtures
shared VERSION / README / architecture docs
```

## Implementation

The adjustment remains owned by `core.voicing.disposition.spread_voice_leading` through the existing notes-only selected 6-note contract intent cost.

The metadata-controlled bias is raised from the v2_6_13 gentle lift value to:

```text
spread_grouping_mix_selected_6note_contract_bias = 5.0
```

Meaning:

```text
If grouping-mix policy selects spread_2plus4_contract or spread_3plus3_contract,
then the groupwise voice-leading collapse gives that selected 6-note candidate
enough preference to survive nearest-motion collapse more often.
```

The mechanism still allows a 5-note neighbor to win if the 6-note candidate is not musically/legalistically suitable.  It does not force notes after selection and does not rewrite MIDI.

## Expected runtime behavior

Reference Misty / Jazz Ballad / 3-chorus audit shape after this pass:

```text
piano_audit_events: 196
5-note: 118
6-note: 76
7-note: 2
4-note: 0

2+3: 118
2+4: 71
3+3: 5
3+4: 2

maj7 #11 events: 0
```

If ignoring the intentionally rare 7-note ending/climax color, the 5-note vs 6-note ratio is:

```text
118 : 76 ~= 60.8% : 39.2%
```

This is close to the requested 6:4 target while preserving 7-note as low-frequency and keeping 4-note retired.

## Guardrails

The following must remain true:

```text
4-note SPREAD 1+3 / 2+2 remain retired from default Ballad runtime
5-note remains the slightly larger body, not a minority
6-note becomes a real secondary body, not a rare accent only
7-note remains low-frequency
unnotated maj7#11 remains disabled by default
Pattern / Anticipation / Expression / Pedal / Gesture / MIDI do not choose voicing density
```

## Next recommended task

After this listening calibration, the next structural voicing-only cleanup can return to:

```text
v2_6_15_engine_voicing_spread_runtime_gate_and_adapter_cleanup
```

This should clean up SPREAD runtime gate / adapter ownership without further density retuning unless the listening result needs correction.
