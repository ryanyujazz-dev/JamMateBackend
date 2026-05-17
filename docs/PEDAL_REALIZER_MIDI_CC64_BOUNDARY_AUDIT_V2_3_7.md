# v2_3_9 — Pedal Realizer / MIDI CC64 Boundary Audit

## Goal

v2_3_9 closes the boundary between core expression pedal intent and concrete MIDI CC64 output. The pass does not change pattern choice, anticipation timing, voicing, pitch content, or style rhythm. It only decides whether an already-resolved expression pedal mode should be materialized as MIDI controller 64.

Pipeline boundary:

```text
Pattern / anticipation
↓
ExpressionResolver: pedal intent = none / light / sustain
↓
Gesture + voicing realization: NoteEvent carries expression_event_id + pedal metadata
↓
MIDI render pipeline: style boundary decides whether CC64 is allowed
↓
midi_writer.py serializes explicit PedalEvent objects as controller 64
```

## Style boundary

- Jazz Ballad: `light` and `sustain` pedal intent may become CC64 spans.
- Bossa Nova: no CC64 by default, even if an expression profile carries light pedal metadata.
- Medium Swing: no CC64 by default; comping stays dry.
- Unknown/future styles: conservative default only allows `sustain` until a style policy explicitly says otherwise.

This keeps Bossa and Swing from becoming muddy while allowing Ballad to carry connected pedal intent into the actual MIDI file.

## Implementation notes

Files touched:

- `src/jammate_engine/realization/note_event_builder.py`
  - `NoteEvent` now carries `expression_event_id`, `pedal`, `release_beats`, and `pedal_debug` metadata.
- `src/jammate_engine/realization/gesture_realizer.py`
  - Copies `EventExpression.pedal` into realized `NoteEvent`s.
- `src/jammate_engine/midi/render_pipeline.py`
  - Adds `PEDAL_REALIZER_VERSION = v2_3_9`.
  - Adds `realize_pedal_events()` and `render_midi_with_audit()`.
  - Produces `pedal_realization` audit metadata.
- `src/jammate_engine/midi/midi_writer.py`
  - Adds optional `pedal_events` input.
  - Serializes explicit CC64 on/off messages only from pre-decided `PedalEvent`s.
  - Adds deterministic same-tick event priorities for note-off / pedal-off / pedal-on / note-on.
- `src/jammate_engine/core/engine.py`
  - Uses `render_midi_with_audit()` and exposes `pedal_realization_audit` in debug.
- `tools/demo_audit_pipeline.py`
  - Adds pedal realization metrics and matrix thresholds.

## Audit fields

`pedal_realization_audit` includes:

- `pedal_realizer_version`
- `style`
- `allowed_modes`
- `intent_note_counts_by_mode`
- `realized_span_counts_by_mode`
- `suppressed_note_counts_by_reason`
- `cc64_event_count`
- `cc64_on_count`
- `cc64_off_count`
- `spans_sample`

Demo matrix validates:

- Ballad must realize at least one CC64 pedal span.
- Bossa and Medium Swing must realize zero CC64 events by default.
- Anticipation timing-grid, tie, release, and overlap checks from v2_3_5/v2_3_6 remain active.

## Verification

```bash
python -m compileall src tools
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q tests/test_v2_3_9_pedal_realizer_midi_cc64_boundary.py
```

Full test split used in this delivery:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q $(ls tests/*.py | grep -v 'test_v2_3_' | tr '\n' ' ')
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q tests/test_v2_3_0_demo_audit_pipeline_consolidation.py tests/test_v2_3_3_anticipation_tie_sustain.py tests/test_v2_3_4_anticipation_listening_calibration.py tests/test_v2_3_5_anticipation_timing_grid_contract.py tests/test_v2_3_6_anticipation_pedal_release_micro_tuning.py tests/test_v2_3_9_pedal_realizer_midi_cc64_boundary.py tests/test_voicing_foundation.py
```

## Next recommended task

v2_3_9 should not expand pedal usage yet. Recommended next step:

**v2_3_9 — Ballad Pedal Listening Calibration / Re-pedal Policy**

Focus:

- Listen to whether Ballad CC64 sustain is too strong at chord changes.
- If needed, introduce a small re-pedal offset or phrase-level pedal density limit.
- Keep Bossa/Swing dry unless an explicit LLM/user intent requests otherwise.
