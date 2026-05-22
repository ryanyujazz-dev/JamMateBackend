# v2_6_108 — Engine Bossa Nova Bass Pickup + Next-Root Anticipation Policy

## Scope
Bossa bass refinement after drum checkpoint: keep root/fifth support, add occasional 2& fifth pickup and controlled 4& next-root anticipation on full ChordRegions only, while keeping split/short regions root-only and keeping kick as a main-beat shadow rather than following pickups.

## Static audit
- Policy active/version: True / v2_6_108
- Behavior change: True
- Full candidate variants: ['root_fifth_main', 'two_and_fifth_pickup', 'four_and_next_root', 'two_and_pickup_plus_four_and_next_root']
- Split/short region degrees: ['root'] / ['root']
- Forbidden numeric pattern keys: []

## Runtime audits
### Blue Bossa 3x
- note_events_by_track: {'piano': 428, 'bass': 103, 'drums': 593}
- planned bass/drum events: 103 / 593
- bass degree counts: {'root': 51, 'fifth': 49, 'next_root': 3}
- bass local beat counts: {'0.0': 51, '2.0': 45, '1.5': 4, '3.5': 3}
- pickup 2& / next-root 4& events: 4 / 3
- split/short non-root events: 0
- terminal next-root events: 0
- kick pickup-follow events: 0
- walking-like bass events: 0
- bass velocity ranges: {'root': [52, 63], 'fifth': [48, 57], 'next_root': [53, 55]}
- bass duration ranges: {'main': [0.82, 1.32], 'pickup_2and': [0.38, 0.38], 'next_root_4and': [0.42, 0.42]}
- MIDI: `demos/v2_6_108_blue_bossa_3x_bossa_nova_bass_pickup_next_root_anticipation_demo.mid`

### Blue Bossa 5x
- note_events_by_track: {'piano': 684, 'bass': 165, 'drums': 989}
- planned bass/drum events: 165 / 989
- bass degree counts: {'root': 85, 'fifth': 78, 'next_root': 2}
- bass local beat counts: {'0.0': 85, '2.0': 75, '1.5': 3, '3.5': 2}
- pickup 2& / next-root 4& events: 3 / 2
- split/short non-root events: 0
- terminal next-root events: 0
- kick pickup-follow events: 0
- walking-like bass events: 0
- bass velocity ranges: {'root': [52, 63], 'fifth': [48, 57], 'next_root': [55, 55]}
- bass duration ranges: {'main': [0.82, 1.32], 'pickup_2and': [0.38, 0.38], 'next_root_4and': [0.42, 0.42]}
- MIDI: `demos/v2_6_108_blue_bossa_5x_bossa_nova_bass_pickup_next_root_anticipation_demo.mid`

## Acceptance
{
  "passed": true,
  "checks": {
    "policy_declares_bass_pickup": true,
    "no_parallel_or_bar_first_or_walking": true,
    "no_cross_track_or_voicing_change": true,
    "full_region_candidates_include_pickup_and_nextroot": true,
    "split_short_regions_root_only": true,
    "no_pattern_numeric_values": true,
    "runtime_blue_bossa_bass_pickup_pass": true
  }
}
