# v2_6_109 — Engine Bossa Nova Bass Articulation + Register Policy

Engine tag: `v2_10_28`

## Scope

Bossa bass articulation/register refinement after v2_6_108: keep the same root/fifth/pickup/next-root candidate set, calibrate semantic length profiles for close pickups, and use existing BassFoundationRealizer register projection metadata for smooth fifths/root-repeat fallback.

## Acceptance

Passed: `True`

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_109_blue_bossa_3x_bossa_nova_bass_articulation_register_policy_demo.mid`
- Notes piano/bass/drums: `412` / `103` / `593`
- Bass articulation coverage: `103/103`
- Bass degree counts: `{'root': 51, 'fifth': 50, 'next_root': 2}`
- Duration ranges by role: `{'light_2and_pickup_short': [0.36, 0.36], 'light_4and_next_root_short': [0.36, 0.36], 'main_fifth_support': [1.08, 1.18], 'main_root_support': [1.08, 1.32], 'short_region_root_clear': [1.12, 1.12]}`
- Register policy counts: `{'root_stable_floor': 51, 'pickup_fifth_nearest_continuity': 5, 'main_fifth_nearest_with_root_repeat_fallback': 45, 'next_root_light_nearest_continuity': 2}`
- Note ranges by degree: `{'fifth': [32, 43], 'next_root': [32, 38], 'root': [38, 48]}`
- Max consecutive bass leap: `12`
- split/short non-root: `0`; terminal next-root: `0`; walking-like: `0`; kick pickup-follow: `0`

### Blue Bossa 5x

- MIDI: `demos/v2_6_109_blue_bossa_5x_bossa_nova_bass_articulation_register_policy_demo.mid`
- Notes piano/bass/drums: `688` / `172` / `989`
- Bass articulation coverage: `172/172`
- Bass degree counts: `{'root': 85, 'fifth': 79, 'next_root': 8}`
- Duration ranges by role: `{'light_2and_pickup_short': [0.36, 0.36], 'light_4and_next_root_short': [0.36, 0.36], 'main_fifth_support': [1.08, 1.18], 'main_root_support': [1.08, 1.32], 'short_region_root_clear': [1.12, 1.12]}`
- Register policy counts: `{'root_stable_floor': 85, 'main_fifth_nearest_with_root_repeat_fallback': 75, 'pickup_fifth_nearest_continuity': 4, 'next_root_light_nearest_continuity': 8}`
- Note ranges by degree: `{'fifth': [32, 43], 'next_root': [26, 41], 'root': [38, 48]}`
- Max consecutive bass leap: `12`
- split/short non-root: `0`; terminal next-root: `0`; walking-like: `0`; kick pickup-follow: `0`

## Recommendation

v2_6_110_engine_bossa_nova_bass_listening_refinement_or_checkpoint
