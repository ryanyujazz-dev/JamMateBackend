from __future__ import annotations

from jammate_engine.core.gestures.gesture import simultaneous_onset
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion

from .beat1_movability import Beat1Movability
from .pattern_candidate import PatternCandidate, event_spec
from .pattern_plan import PatternPlan
from .tail_policy import TailPolicy


REGION_START_ANCHOR_PATTERN_ID = "global_voicing_override_region_start_anchor"


def plan_region_start_anchor_only(
    region: HarmonicRegion,
    *,
    style_name: str,
    expression_hint: str = "sustain",
) -> PatternPlan:
    """Return one pitchless piano event at the start of a harmonic region.

    This is a global voicing-isolation helper, not a style pattern vocabulary.
    It is used only when a runtime request explicitly freezes rhythm so the
    selected voicing family can be auditioned chord-by-chord across any style.
    """

    region_shape = "two_beat_region" if float(region.duration_beats) <= 2.0 else "four_beat_region"
    candidate = PatternCandidate(
        name=REGION_START_ANCHOR_PATTERN_ID,
        weight=1.0,
        category="voicing_override_anchor_only",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=simultaneous_onset(metadata={"voicing_override": True}),
                expression_hint=expression_hint,
                metadata={
                    "density": "voicing_isolation",
                    "cell": "region_start_only",
                    "function": "voicing_override_anchor",
                    "region_shape": region_shape,
                    "style_context": style_name,
                    "voicing_override": True,
                    "normal_style_default": False,
                },
            ),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
        beat1_movability=Beat1Movability(movable=False, reason="voicing_override_keeps_all_events_on_region_start"),
        metadata={
            "voicing_override": True,
            "pattern_mode": "region_start_anchor_only",
            "style_context": style_name,
            "purpose": "freeze_pattern_choice_to_region_start_for_global_voicing_audit",
        },
        tags=("piano", "voicing_override", "region_start", "comping"),
    )
    return candidate.instantiate(region)

def replace_piano_with_region_start_anchor(
    plan: PatternPlan,
    region: HarmonicRegion,
    *,
    style_name: str,
    expression_hint: str = "sustain",
) -> PatternPlan:
    """Replace only piano pattern events with a region-start anchor.

    This keeps the rest of the style arrangement intact: bass, drums, and any
    other non-piano pattern events remain exactly as the style generated them.
    It is the correct global voicing-audit behavior because voicing isolation
    should freeze only piano rhythm while auditioning vertical note choices.
    """

    anchor_plan = plan_region_start_anchor_only(
        region,
        style_name=style_name,
        expression_hint=expression_hint,
    )
    non_piano_events = [event for event in plan.events if event.track != "piano"]
    return PatternPlan(
        events=non_piano_events + anchor_plan.events,
        tail_policy=anchor_plan.tail_policy,
        beat1_movability=anchor_plan.beat1_movability,
        selected_candidate=anchor_plan.selected_candidate,
        metadata={
            **dict(plan.metadata or {}),
            **dict(anchor_plan.metadata or {}),
            "piano_pattern_override": "region_start_anchor_only",
            "non_piano_events_preserved": len(non_piano_events),
        },
    )

