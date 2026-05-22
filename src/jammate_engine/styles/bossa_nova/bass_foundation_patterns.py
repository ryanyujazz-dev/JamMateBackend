from __future__ import annotations

from typing import Any

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec
from jammate_engine.styles.bossa_nova import arrangement_policy


BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION = "v2_6_96"
BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION = "v2_6_98"
BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_99"
BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION = "v2_6_105"
BOSSA_BASS_PICKUP_AND_NEXT_ROOT_ANTICIPATION_VERSION = "v2_6_108"
BOSSA_BASS_ARTICULATION_AND_REGISTER_POLICY_VERSION = "v2_6_109"


def _duration_family(duration: float) -> str:
    if duration <= 1.25:
        return "very_short_region"
    if duration <= 2.25:
        return "split_region"
    return "root_fifth_region"


def _arc_refinement(context: dict[str, Any]) -> dict[str, Any]:
    return arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(
        context.get("bossa_nova_arrangement_arc_intent")
    )


def _base_metadata(context: dict[str, Any], *, family: str, pattern_function: str) -> dict[str, Any]:
    arc = _arc_refinement(context)
    return {
        "style_id": "bossa_nova",
        "pattern_domain": "bass_foundation",
        "pattern_library_id": "bossa_nova.bass_foundation",
        "pattern_library_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bossa_bass_and_drums_identity_audit_active": True,
        "bossa_bass_and_drums_identity_audit_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bass_identity": "root_fifth_support_not_walking",
        "bass_region_duration_family": family,
        "pattern_function": pattern_function,
        "chord_region_first": True,
        "bar_first": False,
        "walking_bass": False,
        "swing_walking_vocabulary": False,
        "voicing_boundary": "pitchless_degree_tokens_only",
        "expression_boundary": "semantic_length_and_dynamic_profiles_only",
        "region_duration_beats_at_selection": float(context.get("region_duration_beats", 4.0)),
        "bossa_full_band_arrangement_arc_listening_refinement_active": bool(arc.get("active")),
        "bossa_full_band_arrangement_arc_listening_refinement_version": BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "bossa_full_band_arrangement_arc_phase": arc.get("phase"),
        "bossa_full_band_arrangement_arc_runtime_intent": arc.get("runtime_intent"),
        "bossa_full_band_arrangement_arc_band": arc.get("full_band_arc_band"),
        "bossa_full_band_arrangement_arc_boundary": arc.get("boundary"),
        "bossa_style_baseline_phase_completion_checkpoint": True,
        "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_style_baseline_phase_completion_checkpoint_boundary": "style_identity_metadata_only_no_pattern_or_realizer_change",
        "bossa_bass_pickup_and_next_root_anticipation_active": True,
        "bossa_bass_pickup_and_next_root_anticipation_version": BOSSA_BASS_PICKUP_AND_NEXT_ROOT_ANTICIPATION_VERSION,
        "bossa_bass_pickup_and_next_root_anticipation_scope": "in-place Bossa bass rhythm refinement: root/fifth support plus occasional 2& fifth pickup and controlled 4& next-root anticipation",
        "bossa_bass_pickup_and_next_root_anticipation_no_parallel_selector": True,
        "bossa_bass_pickup_and_next_root_anticipation_no_walking_bass": True,
        "bossa_bass_pickup_and_next_root_anticipation_no_piano_voicing_api_agent_change": True,
        "bossa_bass_pickup_and_next_root_anticipation_boundary": "bass pattern semantic degree/length/dynamic profiles only; no concrete MIDI pitch/velocity/duration",
        "bossa_bass_articulation_and_register_policy_active": True,
        "bossa_bass_articulation_and_register_policy_version": BOSSA_BASS_ARTICULATION_AND_REGISTER_POLICY_VERSION,
        "bossa_bass_articulation_and_register_policy_no_parallel_selector": True,
        "bossa_bass_articulation_and_register_policy_no_new_bass_engine": True,
        "bossa_bass_articulation_and_register_policy_no_walking_bass": True,
        "bossa_bass_articulation_and_register_policy_scope": "in-place Bossa bass semantic articulation/register refinement; no new candidates beyond the v2_6_108 root/fifth/pickup/next-root set",
        "bossa_bass_articulation_and_register_policy_boundary": "pattern metadata declares semantic length/dynamic/register profile IDs only; BassFoundationRealizer maps them to concrete duration/register",
    }


def _event(
    *,
    beat: float,
    degree: str,
    role: str,
    length_profile: str,
    dynamic_profile: str,
    family: str,
    tag: str,
    arc: dict[str, Any] | None = None,
    pickup_role: str = "main_support",
    anticipation_role: str = "none",
) -> Any:
    arc = dict(arc or {})
    return event_spec(
        track="bass",
        beat=beat,
        role="bass_note",
        metadata={
            "degree": degree,
            "bossa_bass_role": role,
            "bossa_bass_tag": tag,
            "bass_identity": "root_fifth_support_not_walking",
            "bass_region_duration_family": family,
            "length_profile": length_profile,
            "dynamic_profile": dynamic_profile,
            "register_low": 26,
            "register_high": 48,
            "timing_intent": "straight_even",
            "walking_bass": False,
            "bossa_bass_and_drums_identity_audit_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
            "bossa_full_band_arrangement_arc_listening_refinement_active": bool(arc.get("active")),
            "bossa_full_band_arrangement_arc_listening_refinement_version": BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
            "bossa_full_band_arrangement_arc_phase": arc.get("phase"),
            "bossa_full_band_arrangement_arc_runtime_intent": arc.get("runtime_intent"),
            "bossa_full_band_arrangement_arc_band": arc.get("full_band_arc_band"),
            "bossa_full_band_arrangement_arc_boundary": arc.get("boundary"),
            "bossa_style_baseline_phase_completion_checkpoint": True,
            "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
            "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
            "bossa_style_baseline_phase_completion_checkpoint_boundary": "bass_event_metadata_only_no_pattern_or_realizer_change",
            "bossa_kick_bass_lock_and_low_frequency_shadow_active": True,
            "bossa_kick_bass_lock_and_low_frequency_shadow_version": BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
            "bass_kick_lock_counterpart_degree": "root" if degree == "root" else "fifth" if degree == "fifth" else None,
            "bass_kick_lock_expected_kick_slot": "root_on_1_locked_shadow" if degree == "root" else "fifth_on_3_locked_shadow" if degree == "fifth" else None,
            "bass_low_frequency_role": "foundation_that_kick_shadows",
            "bass_kick_lock_boundary": "bass metadata only; kick remains drums-side semantic shadow",
            "bossa_bass_pickup_and_next_root_anticipation_active": True,
            "bossa_bass_pickup_and_next_root_anticipation_version": BOSSA_BASS_PICKUP_AND_NEXT_ROOT_ANTICIPATION_VERSION,
            "bossa_bass_pickup_role": pickup_role,
            "bossa_bass_next_root_anticipation_role": anticipation_role,
            "bossa_bass_pickup_and_next_root_anticipation_no_walking_bass": True,
            "bossa_bass_pickup_and_next_root_anticipation_kick_policy": "kick_shadows_main_root_fifth_only_not_pickups",
            "bossa_bass_pickup_and_next_root_anticipation_boundary": "semantic degree/length/dynamic profile metadata only",
            "bossa_bass_articulation_and_register_policy_active": True,
            "bossa_bass_articulation_and_register_policy_version": BOSSA_BASS_ARTICULATION_AND_REGISTER_POLICY_VERSION,
            "bossa_bass_articulation_role": _articulation_role_for(degree=degree, role=role, pickup_role=pickup_role, anticipation_role=anticipation_role),
            "bossa_bass_register_policy": _register_policy_for(degree=degree, role=role, pickup_role=pickup_role),
            "bossa_bass_register_policy_no_new_resolver": True,
            "bossa_bass_register_policy_boundary": "existing BassFoundationRealizer register projection only",
        },
    )


def _articulation_role_for(*, degree: str, role: str, pickup_role: str, anticipation_role: str) -> str:
    if pickup_role == "two_and_fifth_pickup" or role == "bossa_fifth_pickup":
        return "light_2and_pickup_short"
    if anticipation_role == "controlled_next_root_4and" or degree == "next_root":
        return "light_4and_next_root_short"
    if role == "bossa_fifth" and pickup_role == "main_support":
        return "main_fifth_support"
    if role in {"bossa_split_root", "bossa_short_root"}:
        return "short_region_root_clear"
    if role == "bossa_root":
        return "main_root_support"
    return "bossa_bass_support"


def _register_policy_for(*, degree: str, role: str, pickup_role: str) -> str:
    if degree == "fifth" and (role == "bossa_fifth_pickup" or pickup_role == "two_and_fifth_pickup"):
        return "pickup_fifth_nearest_continuity"
    if degree == "fifth":
        return "main_fifth_nearest_with_root_repeat_fallback"
    if degree == "next_root":
        return "next_root_light_nearest_continuity"
    return "root_stable_floor"


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Bossa Nova bass foundation candidates.

    v2_6_96 overwrites the previous one-size root/fifth candidate in place.
    Bass remains ChordRegion-first and pitchless: full regions use root/fifth
    support, split/short regions state only the current root so the line does
    not spill a fifth into the next chord region. This is Bossa support, not
    Medium Swing walking vocabulary.
    """

    context = dict(context or {})
    duration = float(context.get("region_duration_beats", 4.0))
    family = _duration_family(duration)
    if family == "very_short_region":
        return (_short_region_root_touch(context, family=family),)
    if family == "split_region":
        return (_split_region_root_only(context, family=family),)
    return _full_region_candidates(context, family=family)


def _root_fifth_foundation(context: dict[str, Any], *, family: str) -> PatternCandidate:
    region = context.get("region")
    raw_bar = context.get("region_source_bar_index") or context.get("bar_index")
    if raw_bar is None and region is not None:
        raw_bar = getattr(region, "source_bar_index", None) or getattr(region, "bar_index", None)
    try:
        local_bar = int(raw_bar or 0)
    except (TypeError, ValueError):
        local_bar = 0
    answer = local_bar % 2 == 1
    arc = _arc_refinement(context)
    root_dynamic = str(arc.get("bass_root_dynamic_profile") or ("bossa_root_answer" if answer else "bossa_root"))
    fifth_dynamic = str(arc.get("bass_fifth_dynamic_profile") or ("bossa_fifth_answer" if answer else "bossa_fifth"))
    name = "bossa_bass_root_fifth_2bar_B_answer" if answer else "bossa_bass_root_fifth_2bar_A"
    category = "bossa_root_fifth_support_answer" if answer else "bossa_root_fifth_support"
    root_tag = "root_on_1_answer" if answer else "root_on_1"
    fifth_tag = "fifth_on_3_answer" if answer else "fifth_on_3"
    return _make_root_fifth_candidate(
        context,
        family=family,
        arc=arc,
        name=name,
        category=category,
        weight=1.0,
        root_tag=root_tag,
        fifth_tag=fifth_tag,
        root_dynamic=root_dynamic,
        fifth_dynamic=fifth_dynamic,
        include_2and_pickup=False,
        include_next_root=False,
        pattern_function="long_region_root_fifth_support",
        bass_pickup_variant="root_fifth_main",
    )


def _full_region_candidates(context: dict[str, Any], *, family: str) -> tuple[PatternCandidate, ...]:
    base = _root_fifth_foundation(context, family=family)
    if not _can_use_full_region_pickup_policy(context):
        return (base,)

    arc = _arc_refinement(context)
    phase = str(arc.get("phase") or "")
    band = str(arc.get("full_band_arc_band") or "warm_flow")
    is_release = band == "release" or "release" in phase
    is_breath = band == "breath" or "breath" in phase
    is_lift = band == "gentle_lift" or "lift" in phase or _is_phrase_or_section_transition(context)
    allow_next_root = _can_use_next_root_anticipation(context)

    candidates: list[PatternCandidate] = [base]
    pickup_weight = 0.16
    next_weight = 0.08
    combined_weight = 0.04
    if is_lift:
        pickup_weight = 0.28
        next_weight = 0.24
        combined_weight = 0.12
    elif is_breath:
        pickup_weight = 0.06
        next_weight = 0.02
        combined_weight = 0.0
    elif is_release:
        pickup_weight = 0.0
        next_weight = 0.0
        combined_weight = 0.0

    if pickup_weight > 0:
        candidates.append(_pickup_variant(context, family=family, arc=arc, weight=pickup_weight))
    if allow_next_root and next_weight > 0:
        candidates.append(_next_root_variant(context, family=family, arc=arc, weight=next_weight))
    if allow_next_root and combined_weight > 0:
        candidates.append(_pickup_and_next_root_variant(context, family=family, arc=arc, weight=combined_weight))
    return tuple(candidates)


def _make_root_fifth_candidate(
    context: dict[str, Any],
    *,
    family: str,
    arc: dict[str, Any],
    name: str,
    category: str,
    weight: float,
    root_tag: str,
    fifth_tag: str,
    root_dynamic: str,
    fifth_dynamic: str,
    include_2and_pickup: bool,
    include_next_root: bool,
    pattern_function: str,
    bass_pickup_variant: str,
) -> PatternCandidate:
    events: list[Any] = [
        _event(
            beat=0.0,
            degree="root",
            role="bossa_root",
            length_profile="bossa_root_with_pickup" if include_2and_pickup else "bossa_root",
            dynamic_profile=root_dynamic,
            family=family,
            tag=root_tag,
            arc=arc,
        )
    ]
    if include_2and_pickup:
        events.append(
            _event(
                beat=1.5,
                degree="fifth",
                role="bossa_fifth_pickup",
                length_profile="bossa_fifth_pickup_2and",
                dynamic_profile="bossa_fifth_pickup_lift" if "lift" in str(arc.get("full_band_arc_band") or "") else "bossa_fifth_pickup",
                family=family,
                tag="fifth_pickup_on_2and",
                arc=arc,
                pickup_role="two_and_fifth_pickup",
            )
        )
    events.append(
        _event(
            beat=2.0,
            degree="fifth",
            role="bossa_fifth",
            length_profile="bossa_fifth_before_next_root" if include_next_root else "bossa_fifth",
            dynamic_profile=fifth_dynamic,
            family=family,
            tag=fifth_tag,
            arc=arc,
        )
    )
    if include_next_root:
        events.append(
            _event(
                beat=3.5,
                degree="next_root",
                role="bossa_next_root_anticipation",
                length_profile="bossa_next_root_anticipation",
                dynamic_profile="bossa_next_root_lift" if "lift" in str(arc.get("full_band_arc_band") or "") else "bossa_next_root",
                family=family,
                tag="next_root_on_4and",
                arc=arc,
                pickup_role="four_and_next_root_anticipation",
                anticipation_role="controlled_next_root_4and",
            )
        )
    metadata = _base_metadata(context, family=family, pattern_function=pattern_function)
    metadata.update(
        {
            "bossa_bass_pickup_variant": bass_pickup_variant,
            "bossa_bass_has_2and_fifth_pickup": bool(include_2and_pickup),
            "bossa_bass_has_4and_next_root_anticipation": bool(include_next_root),
            "bossa_bass_pickup_and_next_root_anticipation_behavior_change": bool(include_2and_pickup or include_next_root),
            "bossa_bass_pickup_and_next_root_anticipation_kick_follows_pickups": False,
            "bossa_bass_pickup_and_next_root_anticipation_split_short_root_only": True,
        }
    )
    beats = tuple(float(event.local_beat) for event in events)
    return PatternCandidate(
        name=name,
        weight=float(weight),
        category=category,
        events=tuple(events),
        tail_policy=TailPolicy.from_local_beats(beats, can_receive_next_chord_anticipation=False),
        tags=("bossa", "bass", "root_fifth", "pickup_aware", "not_walking", "chord_region_first"),
        metadata=metadata,
    )


def _pickup_variant(context: dict[str, Any], *, family: str, arc: dict[str, Any], weight: float) -> PatternCandidate:
    return _make_root_fifth_candidate(
        context,
        family=family,
        arc=arc,
        name="bossa_bass_root_2and_fifth_pickup_3_fifth",
        category="bossa_root_fifth_with_2and_pickup",
        weight=weight,
        root_tag="root_on_1_shortened_for_2and_pickup",
        fifth_tag="fifth_on_3_after_pickup",
        root_dynamic=str(arc.get("bass_root_dynamic_profile") or "bossa_root"),
        fifth_dynamic=str(arc.get("bass_fifth_dynamic_profile") or "bossa_fifth"),
        include_2and_pickup=True,
        include_next_root=False,
        pattern_function="long_region_root_fifth_with_light_2and_pickup",
        bass_pickup_variant="two_and_fifth_pickup",
    )


def _next_root_variant(context: dict[str, Any], *, family: str, arc: dict[str, Any], weight: float) -> PatternCandidate:
    return _make_root_fifth_candidate(
        context,
        family=family,
        arc=arc,
        name="bossa_bass_root_fifth_4and_next_root",
        category="bossa_root_fifth_with_next_root_anticipation",
        weight=weight,
        root_tag="root_on_1",
        fifth_tag="fifth_on_3_released_for_next_root",
        root_dynamic=str(arc.get("bass_root_dynamic_profile") or "bossa_root"),
        fifth_dynamic=str(arc.get("bass_fifth_dynamic_profile") or "bossa_fifth"),
        include_2and_pickup=False,
        include_next_root=True,
        pattern_function="long_region_root_fifth_with_controlled_4and_next_root",
        bass_pickup_variant="four_and_next_root",
    )


def _pickup_and_next_root_variant(context: dict[str, Any], *, family: str, arc: dict[str, Any], weight: float) -> PatternCandidate:
    return _make_root_fifth_candidate(
        context,
        family=family,
        arc=arc,
        name="bossa_bass_root_2and_fifth_3_fifth_4and_next_root",
        category="bossa_root_fifth_with_2and_pickup_and_next_root",
        weight=weight,
        root_tag="root_on_1_shortened_for_2and_pickup",
        fifth_tag="fifth_on_3_released_for_next_root",
        root_dynamic=str(arc.get("bass_root_dynamic_profile") or "bossa_root_lift"),
        fifth_dynamic=str(arc.get("bass_fifth_dynamic_profile") or "bossa_fifth_lift"),
        include_2and_pickup=True,
        include_next_root=True,
        pattern_function="long_region_root_fifth_with_2and_pickup_and_controlled_4and_next_root",
        bass_pickup_variant="two_and_pickup_plus_four_and_next_root",
    )


def _can_use_full_region_pickup_policy(context: dict[str, Any]) -> bool:
    return float(context.get("region_duration_beats", 4.0)) >= 3.75


def _is_terminal_final_region(context: dict[str, Any]) -> bool:
    region = context.get("region")
    if region is None:
        return False
    try:
        return bool(region.is_last_bar_of_chorus and int(region.chorus_index) >= int(region.total_choruses) - 1)
    except Exception:
        return False


def _is_phrase_or_section_transition(context: dict[str, Any]) -> bool:
    region = context.get("region")
    if region is None:
        return False
    return bool(getattr(region, "is_last_bar_of_section", False) or getattr(region, "is_last_region_of_bar", False) and getattr(region, "is_last_bar_of_section", False))


def _can_use_next_root_anticipation(context: dict[str, Any]) -> bool:
    if not _can_use_full_region_pickup_policy(context):
        return False
    if _is_terminal_final_region(context):
        return False
    next_symbol = context.get("next_chord_symbol")
    if not next_symbol:
        return False
    current_symbol = str(context.get("chord_symbol") or "")
    if current_symbol and str(next_symbol) == current_symbol:
        return False
    arc = _arc_refinement(context)
    band = str(arc.get("full_band_arc_band") or "")
    phase = str(arc.get("phase") or "")
    if band in {"release", "breath"} or "release" in phase:
        return False
    return band == "gentle_lift" or "lift" in phase or _is_phrase_or_section_transition(context)

def _split_region_root_only(context: dict[str, Any], *, family: str) -> PatternCandidate:
    arc = _arc_refinement(context)
    return PatternCandidate(
        name="bossa_bass_split_region_root_only",
        weight=1.0,
        category="bossa_split_region_root_support",
        events=(
            _event(
                beat=0.0,
                degree="root",
                role="bossa_split_root",
                length_profile="bossa_split_root",
                dynamic_profile=str(arc.get("bass_split_root_dynamic_profile") or "bossa_split_root"),
                family=family,
                tag="split_region_root",
                arc=arc,
            ),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0,), can_receive_next_chord_anticipation=False),
        tags=("bossa", "bass", "split_region", "root_only", "not_walking", "chord_region_first"),
        metadata=_base_metadata(context, family=family, pattern_function="split_region_root_only_clarity"),
    )


def _short_region_root_touch(context: dict[str, Any], *, family: str) -> PatternCandidate:
    arc = _arc_refinement(context)
    return PatternCandidate(
        name="bossa_bass_short_region_root_touch",
        weight=1.0,
        category="bossa_short_region_root_touch",
        events=(
            _event(
                beat=0.0,
                degree="root",
                role="bossa_short_root",
                length_profile="bossa_short_root",
                dynamic_profile=str(arc.get("bass_short_root_dynamic_profile") or "bossa_short_root"),
                family=family,
                tag="short_region_root",
                arc=arc,
            ),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0,), can_receive_next_chord_anticipation=False),
        tags=("bossa", "bass", "short_region", "root_only", "not_walking", "chord_region_first"),
        metadata=_base_metadata(context, family=family, pattern_function="very_short_region_root_touch"),
    )
