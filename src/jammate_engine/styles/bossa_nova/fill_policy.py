from __future__ import annotations

from typing import Any

BOSSA_NOVA_LIGHT_MARKER_FILL_POLICY_VERSION = "v2_6_106"


def get_light_marker_fill_policy() -> dict[str, Any]:
    """Return the Bossa light-marker policy contract.

    Bossa fills stay in the existing percussion candidate as sparse rim-click
    markers.  The policy deliberately does not introduce tom/crash/roll fills,
    a parallel selector, bar-first templates, or MIDI numeric values in the
    pattern layer.
    """

    return {
        "active": True,
        "version": BOSSA_NOVA_LIGHT_MARKER_FILL_POLICY_VERSION,
        "scope": "sparse phrase-end / turnaround / ending cross-stick markers inside the existing percussion candidate",
        "no_parallel_selector": True,
        "no_bar_first_restore": True,
        "no_tom_crash_roll_fill": True,
        "no_swing_or_rock_fill": True,
        "pattern_layer_numeric_values": False,
        "allowed_marker_kinds": ("phrase_end_micro", "turnaround_light", "ending_soft"),
        "recommended_next_task": "v2_6_107_engine_bossa_nova_drum_baseline_checkpoint_or_listening_refinement",
    }


def _bool_attr(obj: Any, name: str) -> bool:
    try:
        return bool(getattr(obj, name))
    except Exception:
        return False


def classify_light_marker_context(context: dict[str, Any], arc: dict[str, Any], *, duration_beats: float) -> dict[str, Any]:
    """Classify whether the current region should receive a sparse marker.

    The decision is ChordRegion-first: full regions may receive very sparse
    markers; split/short regions do not add marker fills because their harmonic
    clarity already needs restraint.
    """

    policy = get_light_marker_fill_policy()
    region = context.get("region")
    phase = str(arc.get("phase") or "")
    band = str(arc.get("full_band_arc_band") or "")
    runtime_intent = str(arc.get("runtime_intent") or "")
    phrase_index_raw = context.get("region_source_bar_index", context.get("region_performance_bar_index", context.get("bar_index", 0)))
    if region is not None:
        phrase_index_raw = getattr(region, "source_bar_index", phrase_index_raw)
    try:
        phrase_index = int(phrase_index_raw or 0) % 8
    except (TypeError, ValueError):
        phrase_index = 0

    is_section_end = _bool_attr(region, "is_last_bar_of_section")
    is_phrase_tail = phrase_index == 7 or is_section_end
    # The repeat-count arc is chorus-level, so a final-release chorus must not
    # mark every bar as an ending.  Only the actual terminal ChordRegion of the
    # final chorus gets the ending marker.
    total_choruses = int(getattr(region, "total_choruses", 1) or 1) if region is not None else 1
    chorus_index = int(getattr(region, "chorus_index", 0) or 0) if region is not None else 0
    is_final = _bool_attr(region, "is_last_bar_of_chorus") and chorus_index >= max(0, total_choruses - 1)
    is_lift = (band == "gentle_lift" or "lift" in phase or runtime_intent == "gentle_transition_lift") and is_phrase_tail

    if is_final:
        return {
            **policy,
            "marker_kind": "ending_soft",
            "enabled": True,
            "reason": "final_or_release_region_soft_marker",
        }
    if duration_beats <= 2.25:
        return {
            **policy,
            "marker_kind": "none",
            "enabled": False,
            "reason": "split_or_short_region_marker_suppressed",
        }
    if is_lift:
        return {
            **policy,
            "marker_kind": "turnaround_light",
            "enabled": True,
            "reason": "gentle_lift_turnaround_light_marker",
        }
    if is_phrase_tail:
        return {
            **policy,
            "marker_kind": "phrase_end_micro",
            "enabled": True,
            "reason": "phrase_tail_micro_marker",
        }
    return {
        **policy,
        "marker_kind": "none",
        "enabled": False,
        "reason": "ordinary_region_no_marker",
    }
