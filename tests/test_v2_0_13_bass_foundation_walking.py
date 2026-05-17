from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.engine import JamMateEngine
from jammate_engine.generation.bass_foundation import BassFoundationGenerator, BassFoundationPolicy
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.realization.bass_degree_resolver import resolve_bass_degree_token
from jammate_engine.runtime.generation_request import GenerationRequest
from jammate_engine.styles.medium_swing.bass_foundation_patterns import get_bass_foundation_policy, get_pattern_candidates


ROOT = Path(__file__).resolve().parents[1]


def test_bass_foundation_library_uses_nextR_not_literal_four() -> None:
    # In BassFoundation vocabulary, legacy "4" means nextR.
    resolution = resolve_bass_degree_token(chord_symbol="Dm7", token="4", next_chord_symbol="G7")
    assert resolution.degree == "nextR"
    assert resolution.pitch_class == 7


def test_bass_foundation_generator_stays_in_upright_register() -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(leadsheet)), choruses=1)
    plan = BassFoundationGenerator().generate(
        regions=timeline.regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(get_bass_foundation_policy()),
        rng=__import__("random").Random(208),
    )
    notes = [int(event.metadata["resolved_midi_note"]) for event in plan.events]
    assert notes
    assert min(notes) >= 26
    assert max(notes) <= 48
    assert len(plan.events) >= len(timeline.regions) * 2


def test_two_beat_regions_do_not_emit_past_region_duration() -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(leadsheet)), choruses=1)
    plan = BassFoundationGenerator().generate(
        regions=timeline.regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(get_bass_foundation_policy()),
        rng=__import__("random").Random(208),
    )
    duration_by_region = {region.region_id: region.duration_beats for region in timeline.regions}
    compact_events = [event for event in plan.events if duration_by_region[event.region_id] <= 2.0]
    assert compact_events
    assert all(float(event.local_beat) < duration_by_region[event.region_id] for event in compact_events)


def test_runtime_debug_reports_bass_foundation_plan(tmp_path: Path) -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json").read_text())
    output = tmp_path / "bass_foundation.mid"
    _, debug = JamMateEngine().generate(
        GenerationRequest(leadsheet=leadsheet, style="medium_swing", choruses=1, seed=208, output_path=str(output)),
        output,
    )
    assert output.exists()
    assert debug["bass_foundation_plan"]["enabled"] is True
    assert debug["note_events_by_track"].get("bass", 0) > 0
