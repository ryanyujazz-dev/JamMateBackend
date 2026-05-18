from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.core.voicing.runtime.request import VoicingRequest
from jammate_engine.realization.note_event_builder import NoteEvent, PedalEvent
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_MIDI_OUTPUT_PIPELINE_BOUNDARY_AUDIT_V2_6_3.md"


def _field_names(cls: type) -> set[str]:
    return {field.name for field in fields(cls)}


def _mini_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Boundary Mini",
        "key": "C",
        "tempo": 72,
        "default_time_signature": {"numerator": 4, "denominator": 4},
        "metadata": {"fixture_role": "v2_6_3_midi_pipeline_boundary_audit"},
        "sections": {
            "A": {
                "label": "A",
                "phrase": "A",
                "role": "normal",
                "bars": [
                    {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}]},
                    {"chords": [{"beat": 1.0, "symbol": "Dm7"}, {"beat": 3.0, "symbol": "G7"}]},
                ],
            }
        },
        "written_form": [{"section": "A"}],
    }


def test_v2_6_3_pipeline_boundary_doc_exists_and_names_runtime_contracts() -> None:
    text = DOC.read_text(encoding="utf-8")

    required_tokens = [
        "GenerationRequest",
        "ChordRegionTimeline",
        "PatternEvent",
        "Anticipation",
        "ExpressionPlan",
        "VoicingRequest",
        "VoicingPlan",
        "NoteEvent",
        "PedalEvent",
        "MIDI writer",
        "midi_base64",
    ]
    for token in required_tokens:
        assert token in text

    assert "Pattern events describe horizontal placement" in text
    assert "Expression decides duration, release, velocity" in text
    assert "Voicing selects concrete vertical pitch content" in text
    assert "MIDI writer serializes already-resolved" in text


def test_v2_6_3_boundary_objects_keep_cross_layer_fields_separated() -> None:
    pattern_fields = _field_names(PatternEvent)
    assert {"event_id", "track", "region_id", "chord_symbol", "onset_beat", "gesture", "expression_hint"} <= pattern_fields
    assert "note" not in pattern_fields
    assert "midi_note" not in pattern_fields
    assert "velocity" not in pattern_fields
    assert "duration_beats" not in pattern_fields
    assert "pedal" not in pattern_fields

    expression_fields = _field_names(EventExpression)
    assert {"duration_beats", "velocity", "articulation", "pedal", "touch", "release_beats"} <= expression_fields
    assert "note" not in expression_fields
    assert "midi_note" not in expression_fields
    assert "voicing_notes" not in expression_fields
    assert "channel" not in expression_fields

    request_fields = _field_names(VoicingRequest)
    assert {"event_id", "chord_symbol", "gesture", "expression_articulation", "ensemble_context", "policy"} <= request_fields
    assert "duration_beats" not in request_fields
    assert "velocity" not in request_fields
    assert "pedal" not in request_fields
    assert "note" not in request_fields
    assert "midi_note" not in request_fields

    note_fields = _field_names(NoteEvent)
    assert {"track", "channel", "note", "velocity", "start_beat", "duration_beats", "timing_intent"} <= note_fields
    assert {"voice_role", "projection_ref", "voicing_event_id", "expression_event_id", "pedal"} <= note_fields

    pedal_fields = _field_names(PedalEvent)
    assert {"track", "channel", "value", "beat", "timing_intent"} <= pedal_fields


def test_v2_6_3_voicing_plan_is_the_vertical_pitch_boundary() -> None:
    plan = VoicingPlan(
        event_id="event_1",
        chord_symbol="Cmaj7",
        notes=[
            VoicedNote(midi_note=60, degree="1", voice_role="root", group_id="lower"),
            VoicedNote(midi_note=64, degree="3", voice_role="third", group_id="upper"),
            VoicedNote(midi_note=67, degree="5", voice_role="fifth", group_id="upper"),
            VoicedNote(midi_note=71, degree="7", voice_role="seventh", group_id="upper"),
        ],
        projection_map={"simultaneous_onset": [0, 1, 2, 3]},
        groups={"lower": [0], "upper": [1, 2, 3]},
        content_family="basic_4note",
        disposition="closed",
        functional_grouping="1+3",
    )

    assert plan.midi_notes == [60, 64, 67, 71]
    assert plan.degrees == ["1", "3", "5", "7"]
    assert plan.density == 4
    debug = plan.to_debug_dict()
    assert debug["midi_notes"] == [60, 64, 67, 71]
    assert debug["projection_map"] == {"simultaneous_onset": [0, 1, 2, 3]}
    assert debug["groups"] == {"lower": [0], "upper": [1, 2, 3]}


def test_v2_6_3_engine_debug_preserves_macro_midi_output_pipeline_order(tmp_path: Path) -> None:
    result = generate_accompaniment(
        {
            "leadsheet": _mini_leadsheet(),
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 1,
            "seed": 263,
            "output_path": str(tmp_path / "v2_6_3_boundary_mini.mid"),
            "ensemble": {"bass_present": True},
        }
    )

    assert result.ok is True
    assert result.midi_path is not None
    assert Path(result.midi_path).exists()
    assert result.debug["written_bars"] == 2
    assert result.debug["regions"] == 3
    assert result.debug["pattern_events"] >= result.debug["active_pattern_events"] > 0
    assert result.debug["note_events"] > 0
    assert result.debug["note_events_by_track"].get("piano", 0) > 0
    assert result.debug["note_events_by_track"].get("bass", 0) > 0

    pipeline = result.debug["pipeline"]
    expected_order = [
        "leadsheet",
        "form_expansion",
        "style_pattern_planning",
        "anticipation_pitchless_timeline_rewrite",
        "expression_policy_resolution",
        "voicing_resolution",
        "gesture_projection",
        "realization",
        "timing_policy_resolution",
        "pedal_intent_to_midi_cc64_boundary",
        "midi_rendering",
    ]
    positions = [pipeline.index(stage) for stage in expected_order]
    assert positions == sorted(positions)

    assert result.debug["timing_policy"]["boundary"] == "timing_policy_only_no_pattern_voicing_expression_content"
    assert (
        result.debug["pedal_realization_audit"]["boundary"]
        == "expression_pedal_intent_to_midi_cc64_with_style_repedal_offset_only_no_pattern_voicing_decision"
    )
    assert result.debug["midi_render_audit"]["timing_policy"]["feel"] == "swing"
