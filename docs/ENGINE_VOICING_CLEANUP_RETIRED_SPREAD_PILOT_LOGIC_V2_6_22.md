# v2_6_22 Engine Voicing Cleanup — Retired SPREAD Pilot Logic Removal

## Scope

This is a voicing-only cleanup pass. It deletes retired Jazz Ballad SPREAD pilot / dry-run / safe-dry-run / selection-audit logic that was superseded by the current grouped SPREAD runtime candidate pool.

No Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, HarmonyOS fixture, VERSION, README, or shared integration document was changed.

## Removed / retired

Deleted from the public SPREAD facade/runtime path:

- `BalladSpreadRuntimeEntryContract` and entry-contract resolver/debug helpers
- `run_ballad_spread_runtime_safe_dry_run` and dry-run wiring helpers
- `spread_runtime_conversion_boundary_audit` and boundary-audit-only helpers
- `run_ballad_spread_runtime_adapter_skeleton` wrapper helpers
- `build_ballad_spread_runtime_pilot_candidate_pool`
- `guard_ballad_spread_pilot_runtime_enablement`
- pilot selection/fallback audit helpers
- old v2_2 pilot tests that asserted the deleted workflow

## Kept / current runtime path

The active runtime path is now:

```text
Ballad grouping-mix event metadata
  -> candidate_generator grouped SPREAD runtime candidate pool
  -> spread_projection_core.project_basic_spread_candidates
  -> spread_runtime_adapter.spread_projection_candidate_to_voicing_candidate_adapter
  -> selector groupwise voice-leading collapse
```

`spread.py` remains a compatibility facade for current SPREAD contracts/projection helpers, but it no longer owns the retired pilot/dry-run/guard workflow.

## Density / color guardrails

The cleanup preserves the current Ballad SPREAD listening constraints:

- 4-note SPREAD default remains retired.
- 5-note / 6-note Misty audit remains near 6:4.
- maj7#11 default safe-extension gate remains closed.
- SPREAD candidate generation remains notes-only and voicing-only.

## Boundary rule

`spread_runtime_adapter.py` owns `SpreadProjectionCandidate -> VoicingCandidate` field mapping. Candidate generator may request grouped SPREAD runtime candidates, but it must not construct source inventory, decide color permission, project registers, apply expression, or write MIDI.
