# Voicing Module Architecture Cleanup — v2_2_77

## Scope

This pass is a structural cleanup before `Ballad SPREAD Grouping Mix Policy Draft + Audit`.
It does not introduce a grouping mix policy, does not change pattern generation, and does not change expression behavior.

The goal is to make the voicing chain easier to read and maintain by removing old flat-module clutter and grouping the remaining files by runtime responsibility.

## Current voicing chain

```text
Style VoicingPolicy / override metadata
↓
runtime/ request + texture state + resolver
↓
sources/ content source planning + chord-tone/color permission + source audits
↓
taxonomy/ density recipe + abstract projection map
↓
disposition/ closed/open/spread projection + method lock/weights
↓
selection/ candidate generation + register guard + scoring + voice leading selector
↓
runtime/ VoicingPlan output
```

## Directory ownership after cleanup

```text
src/jammate_engine/core/voicing/
├── __init__.py                 # public export surface only
├── policy.py                   # shared voicing policy enums/dataclass
├── sources/                    # what notes are eligible
│   ├── canonical_source.py
│   ├── chord_tone_resolver.py
│   ├── color_permission.py
│   ├── content_planner.py
│   ├── four_note_sources.py
│   ├── source_audit.py
│   └── source_balance.py
├── taxonomy/                   # density/grouping taxonomy
│   ├── projection_map.py
│   └── recipes.py
├── disposition/                # how selected source material is laid out
│   ├── closed.py
│   ├── open.py
│   ├── spread.py
│   ├── facade.py
│   ├── placement_utils.py
│   ├── projection.py
│   ├── method_lock.py
│   ├── method_weights.py
│   └── models.py
├── selection/                  # candidate pool, scoring, selection
│   ├── candidate.py
│   ├── candidate_generator.py
│   ├── constraints.py
│   ├── scorer.py
│   ├── selector.py
│   └── voice_leading.py
└── runtime/                    # request/state/resolver/output plan
    ├── override.py
    ├── plan.py
    ├── request.py
    ├── state.py
    ├── texture_plan.py
    └── voicing_resolver.py
```

## Removed / merged files

Removed from the flat `core/voicing` layer:

```text
candidate.py              → selection/candidate.py
candidate_generator.py    → selection/candidate_generator.py
selector.py               → selection/selector.py
scorer.py                 → selection/scorer.py
constraints.py            → selection/constraints.py
voice_leading.py          → selection/voice_leading.py

canonical_source.py       → sources/canonical_source.py
chord_tone_resolver.py    → sources/chord_tone_resolver.py
color_permission.py       → sources/color_permission.py
content_planner.py        → sources/content_planner.py
four_note_sources.py      → sources/four_note_sources.py
source_balance.py         → sources/source_balance.py
source_audit.py           → sources/source_audit.py

projection_map.py         → taxonomy/projection_map.py
recipes.py                → taxonomy/recipes.py

request.py                → runtime/request.py
plan.py                   → runtime/plan.py
state.py                  → runtime/state.py
voicing_resolver.py       → runtime/voicing_resolver.py
override.py               → runtime/override.py
texture_plan.py           → runtime/texture_plan.py

disposition_planner.py    → disposition/facade.py
voice_motion.py           → deleted; unused top-level placeholder
```

No old flat-module compatibility shims were kept. Internal imports, tests, docs, and harness checks now point to the categorized paths.

## Intentionally preserved behavior

- v2_2_54 seventh-chord source integrity gate remains intact.
- SPREAD upper 4-note still excludes DROP2&4.
- 3+4 remains an isolation/listening texture only; no default Ballad runtime mix policy was added.
- 3+4 still uses A1–G5 whole-register guard, color-only rootless upper 4-note for seventh-family chords, and high-root lower compression where required.

## Why `disposition/spread.py` was not split in this pass

`spread.py` is still the largest file, but it now lives under the correct owner: `disposition/`.
It contains active 1+3 / 1+4 / 2+3 / 2+4 / 3+3 / 3+4 isolation logic plus runtime gate/audit helpers.
Splitting it before the grouping mix policy would risk scattering a still-evolving SPREAD contract across too many files.

Recommended follow-up after mix policy stabilizes:

```text
spread/contracts.py       # grouping contracts and lower/upper inventory
spread/projection.py      # lower+upper candidate projection
spread/selection.py       # groupwise voice-leading / whole voicing scoring
spread/runtime_gate.py    # Ballad isolation/runtime gate
spread/audit.py           # listening/audit debug payloads
```

That split should happen only after `Ballad SPREAD Grouping Mix Policy` confirms the final contract surface.

## Validation

```text
compileall: OK
pytest: 666 passed
harness: HARNESS OK
```

Regression listening demo generated:

```text
demos/v2_2_77_voicing_cleanup_misty_spread_3plus4_reference_demo.mid
demos/v2_2_77_voicing_cleanup_misty_spread_3plus4_expanded_flag_demo.mid
```
