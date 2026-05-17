from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Mapping

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent

from .expression_plan import EventExpression, ExpressionPlan


EXPRESSION_AUDIT_CONTRACT_VERSION = "v2_0_45"

SHORT_ARTICULATIONS = {"short", "staccato", "accent"}
SUSTAIN_ARTICULATIONS = {"sustain", "legato"}


@dataclass(frozen=True)
class ExpressionFoundationAudit:
    """Observational expression/sustain/duration audit.

    This audit is an infrastructure contract.  It consumes already-planned
    pitchless events and the already-resolved ExpressionPlan; it does not
    change pattern, voicing, realization, MIDI notes, or style weights.
    """

    summary: dict[str, Any]
    event_rows: list[dict[str, Any]]
    warnings: list[str]


def build_expression_foundation_audit(
    events: list[PatternEvent],
    expression_plan: ExpressionPlan,
    *,
    style_id: str | None = None,
    track_filter: str | None = "piano",
) -> ExpressionFoundationAudit:
    active_events = [event for event in events if event.status == "active"]
    if track_filter is not None:
        active_events = [event for event in active_events if event.track == track_filter]
    active_events = sorted(active_events, key=lambda event: (event.track, event.onset_beat, event.region_id, event.event_id))

    next_by_event_id = _next_same_track_starts(active_events)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing_expression_count = 0

    for event in active_events:
        expression = expression_plan.events.get(event.event_id)
        if expression is None:
            missing_expression_count += 1
            warnings.append(f"Event {event.event_id} is active but has no resolved expression")
            rows.append(_missing_expression_row(event, next_by_event_id.get(event.event_id), style_id=style_id))
            continue
        row = _event_expression_row(event, expression, next_by_event_id.get(event.event_id), style_id=style_id)
        rows.append(row)
        warnings.extend(_warnings_for_row(row))

    summary = _summary(rows, warnings, missing_expression_count=missing_expression_count, style_id=style_id, track_filter=track_filter)
    return ExpressionFoundationAudit(summary=summary, event_rows=rows, warnings=warnings)


def format_expression_foundation_audit_report(audit: ExpressionFoundationAudit, *, max_events: int | None = None) -> str:
    summary = audit.summary
    rows = audit.event_rows if max_events is None else audit.event_rows[:max_events]
    lines: list[str] = []
    lines.append("# Expression / Sustain / Duration Foundation Audit")
    lines.append("")
    lines.append(f"- Contract version: `{summary.get('contract_version')}`")
    lines.append(f"- Style: `{summary.get('style_id')}`")
    lines.append(f"- Track filter: `{summary.get('track_filter')}`")
    lines.append(f"- Events audited: `{summary.get('events')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key in (
        "profiles",
        "articulations",
        "pedal_modes",
        "touches",
        "avg_duration_beats",
        "avg_release_beats",
        "avg_velocity",
        "short_event_count",
        "sustain_event_count",
        "short_overlap_count",
        "cross_region_count",
        "cross_next_event_count",
        "sustain_chop_risk_count",
        "missing_expression_count",
        "flag_counts",
    ):
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if audit.warnings:
        for warning in audit.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Event Trace")
    lines.append("")
    lines.append("| # | Event | Chord | Beat | Pattern | Hint | Profile | Articulation | Dur | Gap | RegionLeft | Pedal | Vel | Flags |")
    lines.append("|---:|---|---|---:|---|---|---|---|---:|---:|---:|---|---:|---|")
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| {index} | `{event}` | `{chord}` | {beat:.3f} | `{pattern}` | `{hint}` | `{profile}` | `{articulation}` | {duration:.3f} | {gap} | {region_left} | `{pedal}` | {velocity} | `{flags}` |".format(
                index=index,
                event=row.get("event_id", ""),
                chord=row.get("chord_symbol", ""),
                beat=float(row.get("onset_beat") or 0.0),
                pattern=row.get("pattern_id") or "unknown",
                hint=row.get("expression_hint") or "",
                profile=row.get("profile_name") or "missing",
                articulation=row.get("articulation") or "missing",
                duration=float(row.get("duration_beats") or 0.0),
                gap=_fmt_float(row.get("gap_to_next_same_track")),
                region_left=_fmt_float(row.get("region_remaining_beats")),
                pedal=row.get("pedal") or "missing",
                velocity=int(row.get("velocity") or 0),
                flags=",".join(row.get("flags") or []),
            )
        )
    if max_events is not None and len(audit.event_rows) > max_events:
        lines.append("")
        lines.append(f"Report truncated to first {max_events} events out of {len(audit.event_rows)}.")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- This report is observational. It does not change durations, velocity, pedal, voicing, pattern, or MIDI output.")
    lines.append("- `Gap` is the distance to the next active event on the same track. It helps identify short notes that overlap the next chord or sustained notes that are chopped unexpectedly.")
    lines.append("- `RegionLeft` is the remaining length in the current harmonic region, derived from pattern event metadata. Crossing the region is a diagnostic signal, not an automatic error.")
    lines.append("- This audit is intended to close infrastructure before formal per-style musicality tuning begins.")
    lines.append("")
    return "\n".join(lines)


def _next_same_track_starts(events: list[PatternEvent]) -> dict[str, float | None]:
    grouped: dict[str, list[PatternEvent]] = {}
    for event in events:
        grouped.setdefault(event.track, []).append(event)
    result: dict[str, float | None] = {}
    for track_events in grouped.values():
        ordered = sorted(track_events, key=lambda event: (event.onset_beat, event.region_id, event.event_id))
        for index, event in enumerate(ordered):
            next_start = None
            for later in ordered[index + 1 :]:
                if later.onset_beat > event.onset_beat + 1e-6:
                    next_start = float(later.onset_beat)
                    break
            result[event.event_id] = next_start
    return result


def _missing_expression_row(event: PatternEvent, next_same_track_start: float | None, *, style_id: str | None) -> dict[str, Any]:
    region_remaining = _region_remaining(event)
    return {
        "contract_version": EXPRESSION_AUDIT_CONTRACT_VERSION,
        "style_id": style_id,
        "event_id": event.event_id,
        "track": event.track,
        "region_id": event.region_id,
        "chord_symbol": event.chord_symbol,
        "onset_beat": event.onset_beat,
        "local_beat": event.local_beat,
        "pattern_id": event.pattern_id,
        "expression_hint": event.expression_hint,
        "profile_name": None,
        "articulation": None,
        "duration_beats": None,
        "release_beats": None,
        "velocity": None,
        "pedal": None,
        "touch": None,
        "accent": None,
        "gap_to_next_same_track": None if next_same_track_start is None else max(0.0, next_same_track_start - float(event.onset_beat)),
        "region_remaining_beats": region_remaining,
        "crosses_next_same_track_event": False,
        "crosses_region_end": False,
        "flags": ["missing_expression"],
    }


def _event_expression_row(
    event: PatternEvent,
    expression: EventExpression,
    next_same_track_start: float | None,
    *,
    style_id: str | None,
) -> dict[str, Any]:
    duration = float(expression.duration_beats)
    onset = float(event.onset_beat)
    gap = None if next_same_track_start is None else max(0.0, float(next_same_track_start) - onset)
    region_remaining = _region_remaining(event)
    articulation = str(expression.articulation or "").lower()
    pedal = str(expression.pedal or "").lower()
    flags: list[str] = []

    if duration <= 0:
        flags.append("non_positive_duration")
    if not 1 <= int(expression.velocity) <= 127:
        flags.append("velocity_out_of_midi_range")
    if gap is not None and duration > gap + 0.05:
        flags.append("crosses_next_same_track_event")
    if region_remaining is not None and duration > region_remaining + 0.05:
        flags.append("crosses_region_end")
    if articulation in SHORT_ARTICULATIONS and gap is not None and duration > gap - 0.03:
        flags.append("short_overlaps_next_event")
    if articulation in SHORT_ARTICULATIONS and duration > 0.75:
        flags.append("short_duration_long")
    if articulation in SUSTAIN_ARTICULATIONS and gap is not None and gap >= 1.25 and duration < min(gap, 2.0) * 0.55 and pedal == "none":
        flags.append("sustain_chop_risk")
    if expression.profile_name == "core_short" and duration > 0.6:
        flags.append("bossa_core_short_too_long")
    if expression.profile_name == "core_sustain" and duration < 1.0:
        flags.append("bossa_core_sustain_too_short")
    anticipated_tie = bool(expression.metadata.get("duration_anticipation_tie_applied", False))
    region_clamped = bool(expression.metadata.get("duration_region_clamp_applied", False))
    if anticipated_tie:
        flags = [flag for flag in flags if flag not in {"crosses_region_end", "short_duration_long", "bossa_core_short_too_long"}]
    if expression.profile_name == "soft_sustain" and duration < 2.5 and not region_clamped and not anticipated_tie:
        flags.append("ballad_soft_sustain_too_short")

    return {
        "contract_version": EXPRESSION_AUDIT_CONTRACT_VERSION,
        "style_id": style_id,
        "event_id": event.event_id,
        "track": event.track,
        "region_id": event.region_id,
        "chord_symbol": event.chord_symbol,
        "onset_beat": onset,
        "local_beat": event.local_beat,
        "pattern_id": event.pattern_id,
        "expression_hint": event.expression_hint,
        "profile_name": expression.profile_name,
        "articulation": articulation,
        "duration_beats": duration,
        "release_beats": float(expression.release_beats),
        "velocity": int(expression.velocity),
        "pedal": pedal,
        "touch": str(expression.touch or "").lower(),
        "accent": float(expression.accent),
        "metadata": dict(expression.metadata),
        "gap_to_next_same_track": gap,
        "region_remaining_beats": region_remaining,
        "crosses_next_same_track_event": "crosses_next_same_track_event" in flags,
        "crosses_region_end": "crosses_region_end" in flags,
        "flags": flags,
    }


def _region_remaining(event: PatternEvent) -> float | None:
    duration = event.metadata.get("region_duration_beats")
    if duration is None:
        return None
    local = float(event.local_beat or 0.0)
    return max(0.0, float(duration) - local)


def _warnings_for_row(row: Mapping[str, Any]) -> list[str]:
    warnings: list[str] = []
    event_id = row.get("event_id")
    chord = row.get("chord_symbol")
    for flag in row.get("flags") or []:
        if flag == "crosses_next_same_track_event":
            warnings.append(f"Event {event_id} ({chord}) duration crosses the next same-track event")
        elif flag == "crosses_region_end":
            warnings.append(f"Event {event_id} ({chord}) duration crosses the harmonic region end")
        elif flag == "short_overlaps_next_event":
            warnings.append(f"Event {event_id} ({chord}) is short/accented but overlaps the next same-track event")
        elif flag == "sustain_chop_risk":
            warnings.append(f"Event {event_id} ({chord}) is sustain/legato but may be chopped before the next event")
        elif flag.endswith("too_long") or flag.endswith("too_short") or flag in {"non_positive_duration", "velocity_out_of_midi_range"}:
            warnings.append(f"Event {event_id} ({chord}) expression diagnostic flag: {flag}")
    return warnings


def _summary(
    rows: list[dict[str, Any]],
    warnings: list[str],
    *,
    missing_expression_count: int,
    style_id: str | None,
    track_filter: str | None,
) -> dict[str, Any]:
    profiles = Counter(row.get("profile_name") or "missing" for row in rows)
    articulations = Counter(row.get("articulation") or "missing" for row in rows)
    pedals = Counter(row.get("pedal") or "missing" for row in rows)
    touches = Counter(row.get("touch") or "missing" for row in rows)
    flags = Counter(flag for row in rows for flag in row.get("flags") or [])
    durations = [float(row["duration_beats"]) for row in rows if row.get("duration_beats") is not None]
    releases = [float(row["release_beats"]) for row in rows if row.get("release_beats") is not None]
    velocities = [int(row["velocity"]) for row in rows if row.get("velocity") is not None]
    anticipated_rows = [
        row
        for row in rows
        if (row.get("metadata") or {}).get("duration_anticipation_tie_applied")
    ]
    anticipation_micro_tuned_rows = [
        row
        for row in anticipated_rows
        if (row.get("metadata") or {}).get("anticipation_pedal_release_micro_tuning_applied")
    ]
    anticipation_duration_micro_tuned_rows = [
        row
        for row in anticipated_rows
        if (row.get("metadata") or {}).get("duration_anticipation_micro_tuning_applied")
    ]
    anticipated_pedals = Counter(str(row.get("pedal") or "missing") for row in anticipated_rows)
    anticipated_releases = [float(row["release_beats"]) for row in anticipated_rows if row.get("release_beats") is not None]
    return {
        "contract_version": EXPRESSION_AUDIT_CONTRACT_VERSION,
        "style_id": style_id or "unknown",
        "track_filter": track_filter or "all",
        "events": len(rows),
        "profiles": dict(profiles),
        "articulations": dict(articulations),
        "pedal_modes": dict(pedals),
        "touches": dict(touches),
        "avg_duration_beats": round(mean(durations), 3) if durations else 0.0,
        "avg_release_beats": round(mean(releases), 3) if releases else 0.0,
        "avg_velocity": round(mean(velocities), 3) if velocities else 0.0,
        "short_event_count": sum(articulations[k] for k in SHORT_ARTICULATIONS),
        "sustain_event_count": sum(articulations[k] for k in SUSTAIN_ARTICULATIONS),
        "short_overlap_count": flags.get("short_overlaps_next_event", 0),
        "cross_region_count": flags.get("crosses_region_end", 0),
        "cross_next_event_count": flags.get("crosses_next_same_track_event", 0),
        "sustain_chop_risk_count": flags.get("sustain_chop_risk", 0),
        "missing_expression_count": missing_expression_count,
        "warning_count": len(warnings),
        "anticipation_tie_event_count": len(anticipated_rows),
        "anticipation_pedal_release_micro_tuned_count": len(anticipation_micro_tuned_rows),
        "anticipation_duration_micro_tuned_count": len(anticipation_duration_micro_tuned_rows),
        "anticipation_pedal_modes": dict(anticipated_pedals),
        "anticipation_avg_release_beats": round(mean(anticipated_releases), 3) if anticipated_releases else 0.0,
        "flag_counts": dict(flags),
    }


def _fmt_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.3f}"
