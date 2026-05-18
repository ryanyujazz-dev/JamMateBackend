# v2_6_27 Engine Voicing — Ballad SPREAD Listening Calibration Pass

## Scope

This is a voicing-only listening calibration pass after the v2_6_22–v2_6_26 cleanup sequence. It does not change Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixtures, VERSION, README, or shared integration docs.

The goal is not to add a new voicing feature. The goal is to keep the current Ballad SPREAD body musical after the realization surface cleanup: stable 5-note body, controlled 6-note lift, no default 4-note SPREAD relapse, and no unnotated maj7#11 in warm Ballad color.

## Calibration decision

v2_6_26 audit was structurally stable:

```text
5-note:6-note ~= 61:39
4-note SPREAD = 0
maj7#11 = 0
max top note = 77, only low-frequency
```

The only default-runtime density lane that still read like a special effect was `1+4`. It is a valid SPREAD contract and remains available for explicit upper4-color or listening-isolation work, but it should not be part of ordinary Jazz Ballad comping by default.

v2_6_27 therefore changes ordinary Ballad grouped-SPREAD runtime to:

```text
ordinary runtime groupings:
  2+3  stable 5-note body
  2+4  fuller 6-note support
  3+3  fuller 6-note support / lift

not ordinary default:
  1+4  upper4 color lane / explicit special usage only
```

## Code boundaries

Changed owners:

```text
styles/jazz_ballad/voicing_policy.py
  updates style metadata and grouping weights only

core/voicing/disposition/spread.py
  filters zero-weight compatible contracts out of the runtime compatible pool

realization/voicing_policy_context_adapter.py
  keeps deterministic extra 6-note support sparse enough after removing 1+4 from default runtime
```

Still forbidden:

```text
no source construction in style policy
no color permission change
no projection rewrite
no selector rewrite
no Pattern / Anticipation / Expression / Gesture / MIDI changes
```

## Runtime guardrails

Expected Misty / Jazz Ballad / 3 choruses audit:

```text
5-note:6-note remains near 6:4
4-note SPREAD remains 0
7-note SPREAD remains 0 or low-frequency
1+4 ordinary runtime events = 0
2+3 remains the only 5-note ordinary body
2+4 / 3+3 provide the 6-note support
maj7#11 remains 0 by default
```

## Why zero-weight compatible filtering was needed

Before this pass, a zero or low weight could remove a contract from the weighted event decision, but the phrase-level compatible candidate pool could still admit that contract as a neighboring option for voice-leading. That was useful during pilot phases, but it made `1+4` continue appearing after it had been demoted from ordinary default runtime.

v2_6_27 makes the boundary explicit:

```text
weight > 0  -> may enter ordinary compatible candidate pool
weight = 0  -> still valid contract, but not ordinary runtime neighbor
```

This keeps source/projection capability intact while preventing default comping from drifting into upper4-color special effects.

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_27_engine_ballad_spread_listening_calibration.py \
  tests/test_v2_6_26_engine_voicing_realization_surface_final_cleanup.py \
  tests/test_v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit.py \
  tests/test_v2_6_24_engine_voicing_realizer_note_audit_cleanup.py \
  tests/test_v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup.py \
  tests/test_v2_6_22_engine_voicing_cleanup_retired_spread_pilot_logic.py
```

## Recommended next task

```text
v2_6_28_engine_ballad_spread_top_voice_and_register_micro_calibration
```

After the 1+4 default lane is controlled, the next listening pass can inspect top-voice shape and register behavior directly instead of mixing register decisions with density-lane cleanup.
