# v2_6_106 — Engine Bossa Nova Light Marker Fill Policy

## Scope
Add sparse Bossa rim-click markers inside the existing percussion candidate for phrase-end, turnaround/gentle-lift, and terminal ending contexts. This is not a tom/crash/roll fill system and does not create a parallel selector, bar-first template path, piano/bass/voicing change, API, Agent, or HarmonyOS change.

## Static audit
- Policy active/version: True / v2_6_106
- Fill policy version: v2_6_106
- Allowed marker kinds: ['phrase_end_micro', 'turnaround_light', 'ending_soft']
- Phrase marker slots: ['micro_4and']
- Lift marker slots: ['turnaround_4and']
- Ending short marker slots: ['ending_short_region_4and']
- Forbidden numeric pattern keys: []

## Runtime audits
### Blue Bossa 3x
- note_events_by_track: {'piano': 404, 'bass': 96, 'drums': 593}
- marker event count: 8
- marker kind counts: {'phrase_end_micro': 4, 'turnaround_light': 2, 'ending_soft': 2}
- marker slot counts: {'micro_4and': 4, 'turnaround_4and': 2, 'ending_short_region_4and': 2}
- marker velocity min/max: 32 / 41
- tom/crash/roll marker events: 0
- swing/rock marker events: 0
- MIDI: `demos/v2_6_106_blue_bossa_3x_bossa_nova_light_marker_fill_policy_demo.mid`

### Blue Bossa 5x
- note_events_by_track: {'piano': 664, 'bass': 160, 'drums': 989}
- marker event count: 12
- marker kind counts: {'phrase_end_micro': 8, 'turnaround_light': 2, 'ending_soft': 2}
- marker slot counts: {'micro_4and': 8, 'turnaround_4and': 2, 'ending_short_region_4and': 2}
- marker velocity min/max: 32 / 40
- tom/crash/roll marker events: 0
- swing/rock marker events: 0
- MIDI: `demos/v2_6_106_blue_bossa_5x_bossa_nova_light_marker_fill_policy_demo.mid`

## Acceptance
{
  "passed": true,
  "checks": {
    "policy_declares_light_marker_fill": true,
    "fill_policy_version_matches": true,
    "no_parallel_or_bar_first": true,
    "no_tom_crash_roll_or_swing_rock": true,
    "static_marker_slots_present": true,
    "markers_use_cross_stick_only": true,
    "no_pattern_numeric_values": true,
    "runtime_blue_bossa_light_markers_pass": true
  }
}
