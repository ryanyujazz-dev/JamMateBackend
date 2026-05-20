# v2_6_74 — Engine Medium Swing Standard-Tune Fill Frequency Checkpoint

## Scope

This milestone is a behavior-preserving listening/audit checkpoint for the Medium Swing piano comping line after:

- `v2_6_71` optional fill/variation vocabulary activation
- `v2_6_72` listening refinement after user review
- `v2_6_73` phrase-end fill context precision

It measures optional fill/variation frequency on 3-chorus standard-tune demos and confirms that the optional vocabulary remains low-intrusion and history-guarded.

## What changed

- Added arrangement metadata:
  - `piano_comping_standard_tune_fill_frequency_checkpoint=True`
  - `piano_comping_standard_tune_fill_frequency_checkpoint_version=v2_6_74`
- Added selected-candidate metadata:
  - `standard_tune_fill_frequency_checkpoint_version=v2_6_74`
  - `standard_tune_fill_frequency_checkpoint_scope=audit_only_no_behavior_change`
- Added an audit/demo script:
  - `examples/scripts/generate_medium_swing_standard_tune_fill_frequency_checkpoint.py`
- Added a focused test:
  - `tests/test_v2_6_74_engine_medium_swing_standard_tune_fill_frequency_checkpoint.py`

## What did not change

- No new optional fill/variation candidates.
- No candidate weight changes.
- No parallel fill selector.
- No phrase engine.
- No bar-first / `two_chord_bar` logic.
- No voicing changes.
- No expression numeric changes.
- No API / Agent / HarmonyOS changes.

## Acceptance intent

The checkpoint should verify:

- optional selected ratio stays low across standard-tune 3-chorus demos;
- active / fill / busy / tail-push continuity remains guarded;
- optional transition fill does not become a generic harmonic-transition habit;
- all pattern candidates remain pitchless and free of final velocity/duration/pedal or voicing fields;
- 3-chorus MIDI demos remain safe for listening review.

## Recommended next task

`v2_6_75_engine_medium_swing_optional_fill_density_macro_gate_only_if_frequency_rises`

Only implement a macro density gate if broader listening reveals optional fill/variation frequency rising above the current low-intrusion range.
