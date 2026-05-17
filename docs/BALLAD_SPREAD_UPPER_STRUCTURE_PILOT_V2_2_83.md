# Ballad SPREAD Upper Structure Pilot v2_2_83

## Scope

`v2_2_83` adds a conservative Upper Structure pilot for Ballad SPREAD dry-run/audit demos. It does not enable ordinary Jazz Ballad runtime and does not create a parallel voicing projection system.

## Architecture boundary

Upper Structure is a `core/voicing/sources` content family. It only declares upper pitch content and metadata.

Projection and placement must reuse existing core voicing abilities:

- 3-note upper structures reuse 3-note closed parent, inversion, register, and candidate selection.
- 4-note upper structures reuse 4-note closed parent, inversion, DROP2/DROP3 projection, register, and candidate selection.
- SPREAD upper 4-note still excludes DROP2&4.

## Lower group gate

When the Upper Structure pilot is enabled, lower groups are limited to two identities:

- `shell`: guide-tone lower support.
- `root_plus_shell`: rooted support plus guide-tone identity.

`root+3+7` is treated as a compact root+shell option for higher root-anchor tail zones where a lower `root+7+upper3` shape would become muddy.

## Low-register density guard

The pilot adds a whole-voicing guard:

```text
low_register_density_threshold = E2 / MIDI 40
max_notes_below_threshold = 1
```

If more than one note appears below the threshold, the candidate is rejected. This guard is intended to prevent thick rooted/shell material from becoming muddy in the low register.

## Pilot behavior

The demo exports two Misty Jazz Ballad versions:

- no-upper-structure reference: expanded SPREAD mix with Upper Structure disabled.
- upper-structure pilot: expanded SPREAD mix with Upper Structure enabled, lower gate active, and low-register density guard active.

The pilot remains explicit override behavior only.

## Audit targets

The audit must report:

- `upper_structure_events`
- `upper_structure_density`
- `upper_structure_sources`
- `upper_structure_lower_modes`
- `low_register_density_guard_enabled_events`
- `low_register_density_guard_violations`
- `fallback_non_spread_events`
- `source_integrity_rejected_events`
- `drop2_and_4_events`
- `whole_register_violations`
- top-voice and group-gap distributions

## Next tuning direction

After listening, tune Upper Structure frequency and scene gating before any runtime gate. The pilot may be richer than a final default; default Ballad comping should use Upper Structure sparingly unless the user or LLM requests richer harmony.
