from __future__ import annotations

import random
from pathlib import Path

from jammate_engine.core.anticipation.anticipation_resolver import AnticipationResolver
from jammate_engine.core.anticipation import AnticipationPolicy
from jammate_engine.core.pattern_runtime.anchor_override import replace_piano_with_region_start_anchor
from jammate_engine.core.voicing.runtime.override import (
    build_voicing_override_policy,
    isolation_disables_anticipation,
    isolation_expression_hint,
    isolation_mutes_bass,
    voicing_isolation_enabled,
    voicing_override_debug,
)
from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.expression.expression_resolver import ExpressionResolver
from jammate_engine.core.expression.audit import build_expression_foundation_audit
from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.generation.bass_foundation import build_bass_foundation_audit
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.generation.bass_foundation import BassFoundationGenerator, BassFoundationPolicy
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.midi.render_pipeline import describe_timing_policy, render_midi_with_audit
from jammate_engine.realization.bass_foundation_realizer import BassFoundationRealizer
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.realization.harmonic_realizer import HarmonicRealizer
from jammate_engine.realization.piano_lh_bass_foundation_realizer import PianoLHBassFoundationRealizer
from jammate_engine.runtime.generation_request import GenerationRequest
from jammate_engine.styles.registry import get_style


class JamMateEngine:
    def generate(self, request: GenerationRequest, output_path: Path) -> tuple[Path, dict]:
        rng = random.Random(request.seed)
        ensemble_context = EnsembleContext.from_dict(request.ensemble)
        leadsheet = normalize_leadsheet(parse_leadsheet(request.leadsheet))
        timeline = expand_form_to_regions(leadsheet, request.choruses)
        style = get_style(request.style)
        effective_voicing_policy = build_voicing_override_policy(
            style.voicing_policy,
            request.voicing_override,
            style_name=request.style,
        )

        pattern_events = []
        region_plans = {}
        style_pattern_history: dict[str, str] = {}
        use_voicing_isolation = voicing_isolation_enabled(request.voicing_override)
        for region in timeline.regions:
            plan = style.plan_region(
                region,
                context={
                    "tempo": request.tempo,
                    "ensemble": ensemble_context.to_dict(),
                    "ensemble_context": ensemble_context,
                    "rng": rng,
                    "style_pattern_history": style_pattern_history,
                },
            )
            if use_voicing_isolation:
                plan = replace_piano_with_region_start_anchor(
                    plan,
                    region,
                    style_name=request.style,
                    expression_hint=isolation_expression_hint(request.voicing_override),
                )
            region_plans[region.region_id] = plan
            pattern_events.extend(plan.events)

        bass_foundation_plan = None
        allow_bass_foundation = not isolation_mutes_bass(request.voicing_override)
        if allow_bass_foundation and style.bass_foundation_source is not None and style.bass_foundation_policy.get("enabled", False):
            bass_foundation_plan = BassFoundationGenerator().generate(
                regions=timeline.regions,
                pattern_source=style.bass_foundation_source,
                policy=BassFoundationPolicy.from_dict(style.bass_foundation_policy),
                rng=rng,
                context={"tempo": request.tempo, "ensemble": ensemble_context.to_dict(), "ensemble_context": ensemble_context},
            )
            pattern_events = [event for event in pattern_events if event.track != "bass"] + bass_foundation_plan.events

        # Anticipation is now an active pitchless timeline rewrite stage.
        # It runs after pattern planning and before expression/voicing.
        anticipation_policy = (
            AnticipationPolicy(enabled=False, debug_name="voicing_override_isolation_anticipation_disabled")
            if isolation_disables_anticipation(request.voicing_override)
            else style.anticipation_policy
        )
        pattern_events = AnticipationResolver().resolve(
            pattern_events,
            anticipation_policy,
            rng,
            regions=timeline.regions,
            region_plans=region_plans,
        )

        expression_plan = ExpressionResolver().resolve(pattern_events, style.expression_policy, timing_policy=style.timing_policy)
        expression_audit = build_expression_foundation_audit(pattern_events, expression_plan, style_id=request.style)

        # Harmonic realization now routes through the core gesture projection
        # boundary before NoteEvent creation.
        harmonic_realizer = HarmonicRealizer(rng=rng)
        harmonic_notes = harmonic_realizer.realize(pattern_events, expression_plan, effective_voicing_policy, ensemble_context)
        bass_notes = BassFoundationRealizer().realize(pattern_events) if ensemble_context.bass_present else []
        piano_lh_bass_notes = PianoLHBassFoundationRealizer().realize(pattern_events, ensemble_context)
        drum_notes = PercussionRealizer().realize(pattern_events)
        note_events = harmonic_notes + bass_notes + piano_lh_bass_notes + drum_notes

        midi_path, midi_render_debug = render_midi_with_audit(note_events, output_path, tempo_bpm=request.tempo, timing_policy=style.timing_policy)
        debug = {
            "title": leadsheet.title,
            "style": request.style,
            "leadsheet_schema_version": leadsheet.schema_version,
            "written_bars": len(leadsheet.bars),
            "performance_choruses": request.choruses,
            "performance_bars": timeline.performance_bars,
            "regions": len(timeline.regions),
            "pattern_events": len(pattern_events),
            "active_pattern_events": sum(1 for event in pattern_events if event.status == "active"),
            "suppressed_pattern_events": sum(1 for event in pattern_events if event.status == "suppressed"),
            "note_events": len(note_events),
            "note_events_by_track": _count_by_track(note_events),
            "ensemble_context": ensemble_context.to_dict(),
            "effective_voicing_policy": effective_voicing_policy.to_debug_dict(),
            "voicing_override": voicing_override_debug(request.voicing_override, effective_voicing_policy),
            "bass_foundation_plan": bass_foundation_plan.metadata if bass_foundation_plan else None,
            "piano_musical_audit_events": list(harmonic_realizer.last_piano_audit_events),
            "expression_foundation_audit_events": list(expression_audit.event_rows),
            "expression_foundation_audit": dict(expression_audit.summary),
            "timing_policy": describe_timing_policy(style.timing_policy),
            "midi_render_audit": dict(midi_render_debug),
            "pedal_realization_audit": dict((midi_render_debug or {}).get("pedal_realization") or {}),
            "pipeline": [
                "leadsheet",
                "form_expansion",
                "style_pattern_planning",
                "bass_foundation_target_to_target_generation",
                "bass_foundation_root_echo_ornament",
                "pitchless_gesture_requests",
                "anticipation_pitchless_timeline_rewrite",
                "expression_policy_resolution",
                "expression_sustain_duration_foundation_audit",
                "voicing_resolution",
                "gesture_projection",
                "realization",
                "timing_policy_resolution",
                "humanization_policy_application",
                "piano_musical_debug_audit",
                "pedal_intent_to_midi_cc64_boundary",
                "midi_rendering",
            ],
        }
        if bass_foundation_plan is not None:
            debug["bass_foundation_audit"] = build_bass_foundation_audit(debug).summary
        debug["piano_musical_audit"] = build_piano_musical_audit(debug).summary
        return midi_path, debug


def _count_by_track(note_events) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in note_events:
        counts[event.track] = counts.get(event.track, 0) + 1
    return counts
