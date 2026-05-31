# v2_6_107 — Engine Bossa Nova Drum Baseline Checkpoint

## Scope
Bossa drum baseline checkpoint after shaker microdynamics, cross-stick phrase-local contour, kick/bass low-frequency shadow lock, and sparse light marker policy. Metadata/audit/demo only; no new drum behavior.

## Static audit
- Policy active/version: True / v2_6_107
- Behavior change: False
- Completed drum versions: ['v2_6_100', 'v2_6_101', 'v2_6_105', 'v2_6_106']
- Candidate event checkpoint coverage: 1.0
- Layers present: shaker=True, cross=True, kick=True, marker=True
- Forbidden numeric pattern keys: []

## Runtime audits
### Blue Bossa 3x
- note_events_by_track: {'piano': 416, 'bass': 96, 'drums': 593}
- planned drum events: 593
- checkpoint coverage: 1.0
- shaker / cross / kick / marker events: 384 / 113 / 96 / 8
- marker kind counts: {'phrase_end_micro': 4, 'turnaround_light': 2, 'ending_soft': 2}
- velocity ranges: {'cross_stick': [24, 52], 'kick': [20, 39], 'marker': [32, 41], 'shaker': [22, 42]}
- drum swing/rock events: 0
- tom/crash/roll marker events: 0
- MIDI: `demos/v2_6_107_blue_bossa_3x_bossa_nova_drum_baseline_checkpoint_demo.mid`

### Blue Bossa 5x
- note_events_by_track: {'piano': 668, 'bass': 160, 'drums': 989}
- planned drum events: 989
- checkpoint coverage: 1.0
- shaker / cross / kick / marker events: 640 / 189 / 160 / 12
- marker kind counts: {'phrase_end_micro': 8, 'turnaround_light': 2, 'ending_soft': 2}
- velocity ranges: {'cross_stick': [24, 52], 'kick': [20, 39], 'marker': [32, 40], 'shaker': [22, 42]}
- drum swing/rock events: 0
- tom/crash/roll marker events: 0
- MIDI: `demos/v2_6_107_blue_bossa_5x_bossa_nova_drum_baseline_checkpoint_demo.mid`

## Acceptance
{
  "passed": true,
  "checks": {
    "policy_declares_drum_checkpoint": true,
    "checkpoint_is_metadata_only": true,
    "no_parallel_or_bar_first": true,
    "no_new_vocabulary_or_cross_track_change": true,
    "candidate_events_stamped": true,
    "static_layers_present": true,
    "no_pattern_numeric_values": true,
    "runtime_blue_bossa_drum_checkpoint_pass": true
  }
}
