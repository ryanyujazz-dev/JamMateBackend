# ENGINE_VOICING_SPREAD_DENSITY_SYSTEM_RESET_V2_6_10

## Scope

`v2_6_10_engine_voicing_spread_density_system_reset` is a voicing-only reset for Jazz Ballad SPREAD density routing.

This is not a scorer patch. The goal is to correct the macro taxonomy and runtime route that caused Jazz Ballad to keep producing 4-note SPREAD output even though the style policy preferred warmer, thicker Ballad voicing.

## Root Cause

The previous Jazz Ballad policy declared `preferred_density=5` and `preferred_disposition=SPREAD`, but the active runtime path still started from ordinary 4-note content sources and then applied legacy SPREAD projection. The newer grouped SPREAD contracts such as `spread_1plus4_contract`, `spread_2plus3_contract`, `spread_2plus4_contract`, and `spread_3plus3_contract` were mostly pilot/dry-run routes rather than the default Ballad voicing body.

So the problem was systemic:

```text
policy says Ballad wants spread / 5-ish
↓
active candidate route still emits 4-note source + legacy spread grouping
↓
selector chooses legal 4-note candidates
```

The fix therefore belongs in density/disposition routing and Ballad grouped-spread runtime policy, not in a small score bonus.

## Main Decision

4-note SPREAD 1+3 / 2+2 retired from the default SPREAD runtime.

The retired contracts remain available only as explicit compatibility/audit references:

```text
spread_1plus3_contract  # retired default runtime
spread_2plus2_contract  # retired default runtime
```

Active default SPREAD contracts are now:

```text
spread_1plus4_contract  # 5-note
spread_2plus3_contract  # 5-note, normal Ballad body
spread_2plus4_contract  # 6-note, fuller support/lift
spread_3plus3_contract  # 6-note, fuller support/lift/climax
spread_3plus4_contract  # 7-note, ending/climax only
```

## New Boundary Rule

`core.voicing.density_policy` now owns the density/disposition compatibility gate.

The key rule:

```text
Disposition.SPREAD + density 4 + grouping 1+3 / 2+2 = blocked by default
```

This rule does not block 4-note `closed` or `open` voicings. It only removes the old 4-note SPREAD path, because SPREAD should represent lower/upper functional grouping, not a stretched version of the ordinary 4-note candidate.

## Ballad Density Policy

Jazz Ballad now routes default grouped SPREAD as follows:

```text
normal_comping  → centered on spread_2plus3_contract
chorus_lift     → mix of spread_2plus3_contract and spread_2plus4_contract
ending_climax   → spread_2plus4_contract / spread_3plus3_contract, with low-frequency 3+4
```

This makes the normal Ballad sound use 5-note grouped SPREAD by default, while keeping 6/7-note voicings available for lift and endings.

## Layer Boundary

This reset is still voicing-only.

It does not let Pattern, Anticipation, Expression, Gesture, or MIDI choose voicing notes.

```text
Pattern       = pitchless rhythm/event layout
Anticipation  = pitchless cross-region timing rewrite
Expression    = duration / release / velocity / pedal intent
Voicing       = content / density / grouping / disposition / register / selection
Gesture       = projection of an existing VoicingPlan
MIDI          = serialization only
```

## Expected Runtime Result

For Misty / Jazz Ballad, the MIDI output should no longer be dominated by 4-note SPREAD.

Expected audit shape:

```text
no spread_1plus3_contract
no spread_2plus2_contract
no 1+3 or 2+2 SPREAD grouping
5-note 2+3 SPREAD is the normal Ballad body
6-note 2+4 / 3+3 remain available for fuller lift
```

## Validation

Primary validation:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_10_engine_voicing_spread_density_system_reset.py
```

The test verifies the taxonomy gate, active SPREAD skeleton, basic projection output, and a real Misty / Jazz Ballad runtime output.
