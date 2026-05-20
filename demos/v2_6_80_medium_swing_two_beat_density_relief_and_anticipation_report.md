# v2_6_80 — Medium Swing 2-Beat Region Density Relief + Anticipation Audit

Relax Medium Swing piano in dense 2-beat ChordRegions and audit the generic region-first anticipation path on both All The Things You Are and Autumn Leaves. This stays in the style-owned candidate weighting layer and does not change core voicing internals, expression numeric values, rhythm vocabulary, API, Agent, or HarmonyOS.

Acceptance Passed: **True**

## Aggregate

```json
{
  "piano_active_pattern_events": 382,
  "piano_two_beat_active_events": 158,
  "two_beat_multi_touch_events": 4,
  "two_beat_start_anchor_events": 142,
  "two_beat_multi_touch_ratio": 0.0253,
  "two_beat_anchor_ratio": 0.8987,
  "active_anticipation_count": 19,
  "two_beat_previous_tail_anticipation_count": 14,
  "low_register_dense_events": 0,
  "voice_leading_warning_events": 0
}
```

## Outputs

### All the Things You Are

- MIDI: `demos/v2_6_80_all_the_things_you_are_medium_swing_two_beat_density_relief_and_anticipation_demo.mid`
- Piano active pattern events: 192
- 2-beat active events: 24
- 2-beat start anchors: 21
- 2-beat multi-touch events: 0
- Active anticipations: 5
- 2-beat previous-tail anticipations: 1
- Invalid region-first anticipations: 0

### Autumn Leaves

- MIDI: `demos/v2_6_80_autumn_leaves_medium_swing_two_beat_density_relief_and_anticipation_demo.mid`
- Piano active pattern events: 190
- 2-beat active events: 134
- 2-beat start anchors: 121
- 2-beat multi-touch events: 4
- Active anticipations: 14
- 2-beat previous-tail anticipations: 13
- Invalid region-first anticipations: 0

## Acceptance

- ✅ v2_6_80 two-beat relief policy declared
- ✅ no bar-first/two-chord-bar candidates
- ✅ All The Things generated and audited
- ✅ Autumn Leaves generated and audited
- ✅ Autumn Leaves two-beat comping relieved below v2_6_79 density
- ✅ Autumn Leaves multi-touch two-beat events are rare
- ✅ Autumn Leaves simple two-beat anchors dominate
- ✅ All The Things two-beat density also stays relaxed
- ✅ generic anticipation active on both tunes
- ✅ 2-beat previous-region anticipation observed
- ✅ no invalid region-first anticipation rows
- ✅ low-register clarity preserved
- ✅ voice-leading remains calm
