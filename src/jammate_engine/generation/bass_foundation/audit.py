from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from jammate_engine.midi.render_pipeline import performed_beat


@dataclass(frozen=True)
class BassFoundationAudit:
    """Human-readable audit model for BassFoundation generation decisions.

    The audit formatter intentionally consumes the runtime debug dictionary
    instead of re-planning bass. This keeps audit reporting observational: it
    summarizes what the generator actually decided for the current seed/song.
    """

    summary: dict[str, Any]
    segment_rows: list[dict[str, Any]]
    warnings: list[str]


def build_bass_foundation_audit(debug: Mapping[str, Any]) -> BassFoundationAudit:
    """Build a compact BassFoundation musicality audit from GenerationResult.debug."""

    plan = dict(debug.get("bass_foundation_plan") or {})
    segments = list(plan.get("segments") or [])
    timing_policy = dict(debug.get("timing_policy") or {})

    zone_counter: Counter[str] = Counter()
    lane_counter: Counter[str] = Counter()
    connector_counter: Counter[str] = Counter()
    candidate_counter: Counter[str] = Counter()
    chord_counter: Counter[str] = Counter()
    root_echo_count = 0
    root_echo_bad_same = 0
    root_echo_bad_timing = 0
    classic_fill_count = 0
    repeated_root_segments = 0
    repeated_root_violations = 0
    seventh_family_segments = 0
    seventh_lower_lane_segments = 0
    seventh_by_zone: Counter[str] = Counter()
    seventh_by_lane: Counter[str] = Counter()
    target_continuity_total = 0
    target_continuity_matches = 0
    target_continuity_mismatches = 0
    span_violations = 0
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    for index, segment in enumerate(segments, start=1):
        row = _segment_row(index, segment, timing_policy)
        rows.append(row)
        zone_counter.update([row["zone"]])
        lane_counter.update([row["lane"]])
        connector_counter.update([row["connector"]])
        candidate_counter.update([row["candidate"]])
        if row["chord"]:
            chord_counter.update([row["chord"]])
        root_echo_count += int(row["root_echo_count"])
        root_echo_bad_same += int(row["root_echo_bad_same"])
        root_echo_bad_timing += int(row["root_echo_bad_timing"])
        classic_fill_count += 1 if row["classic_fill"] else 0
        repeated_root_segments += 1 if row["repeated_root_start"] else 0
        repeated_root_violations += 1 if row["repeated_root_violation"] else 0
        if row["seventh_family"]:
            seventh_family_segments += 1
            seventh_by_zone.update([row["zone"]])
            seventh_by_lane.update([row["lane"]])
            if row["lane"] == "lower":
                seventh_lower_lane_segments += 1
        if row["previous_target_nextR_note"] is not None:
            target_continuity_total += 1
            if row["target_continuity_match"]:
                target_continuity_matches += 1
            else:
                target_continuity_mismatches += 1
                warnings.append(f"Region {row['region_id']} did not inherit previous target_nextR_note")
        if row["repeated_root_violation"]:
            warnings.append(f"Region {row['region_id']} has R-R start that is not the exact same root note")
        if row["max_span"] > row["span_limit"]:
            span_violations += 1
            warnings.append(
                f"Region {row['region_id']} span {row['max_span']} exceeds limit {row['span_limit']}"
            )
        if row["root_echo_bad_same"]:
            warnings.append(f"Region {row['region_id']} has root echo not equal to region-root note")
        if row["root_echo_bad_timing"]:
            warnings.append(f"Region {row['region_id']} has root echo not rendered as swing upbeat")

    summary = {
        "title": debug.get("title"),
        "style": debug.get("style", "medium_swing"),
        "regions": debug.get("regions"),
        "segments": len(segments),
        "note_events_by_track": debug.get("note_events_by_track", {}),
        "zones": dict(zone_counter),
        "lanes": dict(lane_counter),
        "connectors": dict(connector_counter),
        "top_candidates": candidate_counter.most_common(12),
        "top_chords": chord_counter.most_common(12),
        "root_echo_count": root_echo_count,
        "root_echo_bad_same": root_echo_bad_same,
        "root_echo_bad_timing": root_echo_bad_timing,
        "classic_fill_count": classic_fill_count,
        "repeated_root_segments": repeated_root_segments,
        "repeated_root_violations": repeated_root_violations,
        "seventh_family_segments": seventh_family_segments,
        "seventh_lower_lane_segments": seventh_lower_lane_segments,
        "seventh_lower_lane_ratio": round(seventh_lower_lane_segments / seventh_family_segments, 3) if seventh_family_segments else 0.0,
        "seventh_by_zone": dict(seventh_by_zone),
        "seventh_by_lane": dict(seventh_by_lane),
        "target_continuity_total": target_continuity_total,
        "target_continuity_matches": target_continuity_matches,
        "target_continuity_mismatches": target_continuity_mismatches,
        "span_violations": span_violations,
        "timing_policy": timing_policy,
        "policy": plan.get("policy", {}),
    }
    return BassFoundationAudit(summary=summary, segment_rows=rows, warnings=warnings)


def format_bass_foundation_audit_report(debug: Mapping[str, Any], *, max_segments: int | None = None) -> str:
    """Format BassFoundation debug as a markdown audit report."""

    audit = build_bass_foundation_audit(debug)
    summary = audit.summary
    policy = dict(summary.get("policy") or {})
    timing_policy = dict(summary.get("timing_policy") or {})
    rows = audit.segment_rows if max_segments is None else audit.segment_rows[:max_segments]

    lines: list[str] = []
    lines.append("# BassFoundation Musicality Audit")
    lines.append("")
    lines.append(f"- Title: `{summary.get('title')}`")
    lines.append(f"- Segments audited: `{summary.get('segments')}`")
    lines.append(f"- Note events by track: `{summary.get('note_events_by_track')}`")
    lines.append(f"- Timing policy: `{timing_policy}`")
    lines.append(f"- Register: `{policy.get('register_low')}-{policy.get('register_high')}`")
    lines.append(f"- Max region span: `{policy.get('max_region_span')}` semitones")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Zones: `{summary.get('zones')}`")
    lines.append(f"- Lanes: `{summary.get('lanes')}`")
    lines.append(f"- Connectors: `{summary.get('connectors')}`")
    lines.append(f"- Root echo count: `{summary.get('root_echo_count')}`")
    lines.append(f"- Root echo same-root violations: `{summary.get('root_echo_bad_same')}`")
    lines.append(f"- Root echo swing-timing violations: `{summary.get('root_echo_bad_timing')}`")
    lines.append(f"- Classic fills: `{summary.get('classic_fill_count')}`")
    lines.append(f"- Repeated-root starts: `{summary.get('repeated_root_segments')}`")
    lines.append(f"- Repeated-root exact-note violations: `{summary.get('repeated_root_violations')}`")
    lines.append(f"- Seventh-family segments: `{summary.get('seventh_family_segments')}`")
    lines.append(f"- Seventh-family lower-lane ratio: `{summary.get('seventh_lower_lane_ratio')}`")
    lines.append(f"- Target-continuity matches/mismatches: `{summary.get('target_continuity_matches')}` / `{summary.get('target_continuity_mismatches')}`")
    lines.append(f"- Span violations: `{summary.get('span_violations')}`")
    lines.append("")
    lines.append("## Seventh Bias Audit")
    lines.append("")
    lines.append(f"- Seventh-family segments: `{summary.get('seventh_family_segments')}`")
    lines.append(f"- Lower-lane ratio: `{summary.get('seventh_lower_lane_ratio')}`")
    lines.append(f"- By zone: `{summary.get('seventh_by_zone')}`")
    lines.append(f"- By lane: `{summary.get('seventh_by_lane')}`")
    lines.append("")
    lines.append("## Target Continuity Audit")
    lines.append("")
    lines.append(f"- Regions with previous target note: `{summary.get('target_continuity_total')}`")
    lines.append(f"- Matches: `{summary.get('target_continuity_matches')}`")
    lines.append(f"- Mismatches: `{summary.get('target_continuity_mismatches')}`")
    lines.append("")
    lines.append("## Top Candidates")
    lines.append("")
    for candidate, count in summary.get("top_candidates") or []:
        lines.append(f"- `{candidate}`: {count}")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if audit.warnings:
        for warning in audit.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Region Decision Trace")
    lines.append("")
    lines.append(
        "| # | Region | Chord | Candidate | Notes | Span | Zone | Lane | Connector | Seventh | Start | Target | Root Echo | Fill | Performed Timing |"
    )
    lines.append(
        "|---:|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|"
    )
    for row in rows:
        lines.append(
            "| {index} | `{region_id}` | `{chord}` | `{candidate}` | `{notes}` | {max_span} | `{zone}` | `{lane}` | `{connector}` | {seventh} | `{start}` | `{target}` | {root_echo} | {fill} | {performed} |".format(
                index=row["index"],
                region_id=row["region_id"],
                chord=row["chord"],
                candidate=row["candidate"],
                notes=" ".join(str(note) for note in row["notes"]),
                max_span=row["max_span"],
                zone=row["zone"],
                lane=row["lane"],
                connector=row["connector"],
                seventh="yes" if row["seventh_family"] else "",
                start=f"{row['start_note']}:{row['start_note_source']}",
                target=f"prev={row['previous_target_nextR_note']} next={row['target_nextR_note']}",
                root_echo=_format_echo_cell(row),
                fill="yes" if row["classic_fill"] else "",
                performed=_format_performed_cell(row),
            )
        )
    if max_segments is not None and len(audit.segment_rows) > max_segments:
        lines.append("")
        lines.append(f"Report truncated to first {max_segments} segments out of {len(audit.segment_rows)}.")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- `Notes` are resolved MIDI notes after BassFoundation planning, before MIDI channel/program rendering.")
    lines.append("- `Span` is the lowest-to-highest BassFoundation note span inside that chord region; it should stay within the one-octave guard.")
    lines.append("- `Performed Timing` shows logical `.5` grid values converted by the style timing policy; Medium Swing renders `.5` as swung upbeat.")
    lines.append("- Root echo should reuse the exact same current-root note as the chord-region downbeat.")
    lines.append("- R-R-starting skeletons must repeat the exact same root MIDI note, never an octave-displaced root.")
    lines.append("- `Start` shows whether the region inherited the previous segment's `target_nextR_note`; this keeps old-engine target-to-target continuity.")
    lines.append("- `Seventh` marks R-Seventh / Seventh-containing skeletons used to audit the old-engine lower-lane bias.")
    lines.append("")
    return "\n".join(lines)


def _segment_row(index: int, segment: Mapping[str, Any], timing_policy: Mapping[str, Any]) -> dict[str, Any]:
    notes = [int(note) for note in segment.get("notes", []) if isinstance(note, int) or str(note).lstrip("-").isdigit()]
    if not notes and segment.get("classic_fill_notes"):
        notes = [int(item["note"]) for item in segment.get("classic_fill_notes", []) if "note" in item]
    region_span_values = [int(value) for value in dict(segment.get("classic_fill_region_spans", {})).values()]
    # Classic fills may consume two chord regions. The hard guard is per chord
    # region, not across the whole multi-region phrase, so audit the maximum
    # per-region span when the generator provides it.
    span = max(region_span_values) if region_span_values else (max(notes) - min(notes) if notes else 0)
    span_limit = int(segment.get("max_region_span", 12) or 12)
    echoes = list(segment.get("root_echo_ornaments") or [])
    echo_bad_same = sum(1 for echo in echoes if not bool(echo.get("same_as_region_root", echo.get("root_echo_same_as_region_root", True))))
    echo_bad_timing = 0
    echo_performed: list[dict[str, Any]] = []
    for echo in echoes:
        logical = float(echo.get("local_beat", 0.0))
        performed = performed_beat(logical, "swing_upbeat", timing_policy)
        echo_performed.append({"logical": logical, "performed": performed, "note": echo.get("note")})
        if _is_half_beat(logical) and performed <= logical + 0.05:
            echo_bad_timing += 1
    classic_notes = list(segment.get("classic_fill_notes") or [])
    classic_performed = []
    for item in classic_notes:
        logical = float(item.get("local_beat", 0.0))
        if _is_half_beat(logical):
            classic_performed.append({"logical": logical, "performed": performed_beat(logical, "swing_upbeat", timing_policy), "note": item.get("note")})
    degrees = tuple(segment.get("skeleton_degrees", ()) or ())
    seventh_family = any(str(degree) == "Seventh" for degree in degrees[1:])
    return {
        "index": index,
        "region_id": str(segment.get("region_id", "")),
        "chord": str(segment.get("chord_symbol", "")),
        "candidate": str(segment.get("candidate", "")),
        "notes": notes,
        "max_span": span,
        "span_limit": span_limit,
        "zone": str(segment.get("zone", "unknown")),
        "lane": str(segment.get("selected_lane", "unknown")),
        "connector": str(segment.get("beat4_connector_kind", "")),
        "root_echo_count": len(echoes),
        "root_echo_bad_same": echo_bad_same,
        "root_echo_bad_timing": echo_bad_timing,
        "root_echo_performed": echo_performed,
        "classic_fill": bool(segment.get("classic_fill_triggered", False)),
        "classic_fill_scene": str(segment.get("classic_fill_scene", "")),
        "repeated_root_start": bool(segment.get("repeated_root_start", False)),
        "repeated_root_exact": bool(segment.get("repeated_root_exact", True)),
        "repeated_root_notes": tuple(segment.get("repeated_root_notes", ())),
        "repeated_root_violation": bool(segment.get("repeated_root_start", False)) and not bool(segment.get("repeated_root_exact", True)),
        "skeleton_degrees": degrees,
        "seventh_family": seventh_family,
        "start_note": segment.get("start_note"),
        "start_note_source": str(segment.get("start_note_source", "")),
        "previous_target_nextR_note": segment.get("previous_target_nextR_note"),
        "target_nextR_note": segment.get("target_nextR_note"),
        "target_continuity_match": bool(segment.get("target_continuity_match", False)),
        "classic_performed": classic_performed,
    }


def _format_echo_cell(row: Mapping[str, Any]) -> str:
    echoes = row.get("root_echo_performed") or []
    if not echoes:
        return ""
    return ", ".join(f"{item['note']}@{item['logical']:.1f}->{item['performed']:.3f}" for item in echoes)


def _format_performed_cell(row: Mapping[str, Any]) -> str:
    values = []
    for item in row.get("root_echo_performed") or []:
        values.append(f"echo {item['logical']:.1f}->{item['performed']:.3f}")
    for item in row.get("classic_performed") or []:
        values.append(f"fill {item['logical']:.1f}->{item['performed']:.3f}")
    return ", ".join(values)


def _is_half_beat(value: float) -> bool:
    return abs((float(value) % 1.0) - 0.5) < 1e-6
