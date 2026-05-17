from __future__ import annotations

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.policy import ContentFamily, Disposition, VoicingPolicy
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.core.voicing.sources.source_balance import SOURCE_BALANCE_CONTRACT_VERSION, source_balance_key, source_gate_mode
from jammate_engine.styles.registry import get_style


def test_v2_1_43_source_balance_module_handles_3note_functional_sources() -> None:
    policy = VoicingPolicy(
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR, ContentFamily.SHELL_PLUS_5),
        preferred_content=ContentFamily.SHELL_PLUS_COLOR,
        preferred_density=3,
        min_density=3,
        max_density=3,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        source_family_weights_by_gate={
            "explicit_chart_color": {"third_seventh_ninth": 0.25},
            "chord_symbol_only": {"third_seventh_fifth": 0.11},
        },
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
            "closed_3note_per_source_minimum_motion": True,
        },
    )
    candidates = generate_candidates("Cmaj9", policy)
    selected = next(candidate for candidate in candidates if source_balance_key(candidate) == "third_seventh_ninth")

    assert SOURCE_BALANCE_CONTRACT_VERSION == "v2_1_43"
    assert source_gate_mode(selected) == "explicit_chart_color"
    breakdown = score_candidate(selected, policy)
    assert breakdown.details["three_note_source_balance_key"] == "third_seventh_ninth"
    assert breakdown.details["three_note_source_balance_score"] == 0.25


def test_v2_1_43_source_balance_module_handles_4note_doubled_triad_sources() -> None:
    policy = VoicingPolicy(
        allowed_content=(ContentFamily.MAJOR_TRIAD,),
        preferred_content=ContentFamily.MAJOR_TRIAD,
        preferred_density=4,
        min_density=4,
        max_density=4,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        source_family_weights_by_gate={"chord_symbol_only": {"root_third_fifth_root": 0.17}},
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
        },
    )
    candidates = generate_candidates("C", policy)
    selected = next(candidate for candidate in candidates if source_balance_key(candidate) == "root_third_fifth_root")

    assert selected.density == 4
    assert source_gate_mode(selected) == "chord_symbol_only"
    breakdown = score_candidate(selected, policy)
    assert breakdown.details["four_note_source_balance_key"] == "root_third_fifth_root"
    assert breakdown.details["source_balance_score"] == 0.17


def test_v2_1_43_style_weight_maps_cover_closed_3_and_4_note_sources() -> None:
    medium = get_style("medium_swing").voicing_policy
    bossa = get_style("bossa_nova").voicing_policy
    ballad = get_style("jazz_ballad").voicing_policy

    assert medium.source_family_weights_by_gate["harmonic_expansion"]["third_seventh_ninth"] > medium.source_family_weights_by_gate["harmonic_expansion"]["third_seventh_root"]
    assert bossa.source_family_weights_by_gate["chord_symbol_only"]["root_second_fifth_root"] > bossa.source_family_weights_by_gate["chord_symbol_only"]["fifth_root_second_fifth"]
    assert ballad.source_family_weights_by_gate["explicit_chart_color"]["root_third_ninth"] > ballad.source_family_weights_by_gate["explicit_chart_color"]["third_seventh_root"]


def test_v2_1_43_no_new_voicing_subfolder_needed() -> None:
    import pathlib

    voicing_dir = pathlib.Path(__file__).resolve().parents[1] / "src" / "jammate_engine" / "core" / "voicing"
    assert (voicing_dir / "sources" / "source_balance.py").exists()
    assert not (voicing_dir / "source_families").exists()
