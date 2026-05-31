# v2_6_105 — Engine Bossa Nova Kick/Bass Lock and Low-frequency Shadow Refinement

## Scope
Refine the existing Bossa low-frequency drum/bass layer in place. Bass remains root/fifth support, and kick remains a low-velocity shadow locked to the same root/fifth beats. Split/short ChordRegions stay root-only; no four-on-floor, rock backbeat, swing ride, piano, voicing, API, Agent, or HarmonyOS change.

## Static audit
- Policy active/version: True / v2_6_105
- Full-region kick slots: ['root_on_1_locked_shadow', 'fifth_on_3_locked_shadow']
- Split kick slots: ['root_on_1_locked_shadow']
- Short kick slots: ['root_on_1_locked_shadow']
- Kick low-frequency role: ['shadow_not_driver']
- Forbidden numeric pattern keys: []

## Runtime audits
### Blue Bossa 3x
- note_events_by_track: {'piano': 440, 'bass': 96, 'drums': 585}
- kick lock coverage: 1.0
- kick root/fifth events: 51 / 45
- kick velocity min/max: 20 / 39
- bass velocity min/max: 48 / 63
- split/short fifth kick events: 0
- four-on-floor / rock driver events: 0 / 0
- bass walking-like events: 0
- MIDI: `demos/v2_6_105_blue_bossa_3x_bossa_nova_kick_bass_lock_low_frequency_shadow_demo.mid`

### Blue Bossa 5x
- note_events_by_track: {'piano': 680, 'bass': 160, 'drums': 977}
- kick lock coverage: 1.0
- kick root/fifth events: 85 / 75
- kick velocity min/max: 20 / 39
- bass velocity min/max: 48 / 63
- split/short fifth kick events: 0
- four-on-floor / rock driver events: 0 / 0
- bass walking-like events: 0
- MIDI: `demos/v2_6_105_blue_bossa_5x_bossa_nova_kick_bass_lock_low_frequency_shadow_demo.mid`

## Acceptance
{
  "passed": true,
  "checks": {
    "policy_declares_kick_bass_lock": true,
    "no_parallel_or_bar_first": true,
    "full_region_kick_locks_to_root_and_fifth": true,
    "split_and_short_regions_root_only": true,
    "kick_shadow_not_driver": true,
    "no_pattern_numeric_values": true,
    "runtime_blue_bossa_kick_bass_lock_passes": true
  }
}
