# v2_6_124 — Engine Bossa Nova SPREAD 1+4 5-note Correction

## Correction

- Removed the wrong OPEN/generic_open 5-note direction.
- Bossa ordinary body remains 4-note OPEN drop-family.
- Low-frequency 5-note color now requests existing grouped-SPREAD `spread_1plus4_contract` event-scoped.
- `generic_open` remains fallback/rescue only.

## Static audit

- open methods: `['drop2', 'drop3', 'drop2_and_4']`
- has open density gate: `False`
- has selector tail lane: `False`
- core_short velocity: `48`

## Runtime audit

- density/method counts: `{'d4:open:drop2:d4__unGrouped__rootless_A__rootless_allowed': 57, 'd4:open:drop2:d4__unGrouped__rootless_B__rootless_allowed': 16, 'd4:open:drop3:d4__unGrouped__rootless_A__rootless_allowed': 9, 'd4:open:drop3:d4__unGrouped__rootless_B__rootless_allowed': 4, 'd5:spread:None:spread_1plus4_contract': 4, 'd4:open:drop2_and_4:d4__unGrouped__rootless_A__rootless_allowed': 5}`
- spread 5-note selected: `4`
- open 5-note selected: `0`
- generic_open selected: `0`
- core batida front velocities: `[48, 48, 48, 48]`

## Acceptance

- passed: `True`
- checks: `{'no_open_density_gate_or_tail_lane': True, 'generic_open_not_in_bossa_normal_pool': True, 'ordinary_pool_has_no_open_5note_or_generic': True, 'event_scoped_spread_probe_uses_1plus4_5note': True, 'runtime_has_low_frequency_spread_5note': True, 'runtime_has_no_open_5note_or_generic_open': True, 'core_batida_front_velocity_48_retained': True}`

## Demos

- Blue Bossa runtime: `demos/v2_6_124_blue_bossa_bossa_nova_spread_5note_correction_demo.mid`
- SPREAD 5-note audition: `demos/v2_6_124_bossa_nova_spread_5note_candidate_audition_demo.mid`
- Core batida velocity focus: `demos/v2_6_124_bossa_nova_core_batida_velocity_48_focus_demo.mid`
