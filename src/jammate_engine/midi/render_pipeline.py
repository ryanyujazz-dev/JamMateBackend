from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

from jammate_engine.realization.note_event_builder import NoteEvent, PedalEvent
from .midi_writer import write_midi


TIMING_CONTRACT_VERSION = "v2_0_43"
PEDAL_REALIZER_VERSION = "v2_3_9"


@dataclass(frozen=True)
class HumanizationPolicy:
    """Deterministic timing/velocity humanization policy.

    Humanization is intentionally renderer-side and disabled by default. Style
    pattern libraries still write musical grid positions; this policy may only
    apply tiny performed-time/velocity offsets after realization has already
    produced concrete NoteEvents.
    """

    enabled: bool = False
    max_offset_beats: float = 0.0
    velocity_jitter: int = 0
    seed: int = 0
    affect_tracks: tuple[str, ...] = field(default_factory=tuple)
    humanize_literal: bool = False
    profile_name: str = "none"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "HumanizationPolicy":
        data = data or {}
        tracks = data.get("affect_tracks", ())
        if isinstance(tracks, str):
            tracks = (tracks,)
        return cls(
            enabled=bool(data.get("enabled", False)),
            max_offset_beats=max(0.0, float(data.get("max_offset_beats", 0.0))),
            velocity_jitter=max(0, int(data.get("velocity_jitter", 0))),
            seed=int(data.get("seed", 0)),
            affect_tracks=tuple(str(track) for track in tracks),
            humanize_literal=bool(data.get("humanize_literal", False)),
            profile_name=str(data.get("profile_name", "none")),
        )

    def applies_to(self, event: NoteEvent) -> bool:
        if not self.enabled:
            return False
        if not self.humanize_literal and str(event.timing_intent or "auto") == "literal":
            return False
        if self.affect_tracks and event.track not in self.affect_tracks:
            return False
        return self.max_offset_beats > 0.0 or self.velocity_jitter > 0

    def offsets_for_event(self, event: NoteEvent) -> tuple[float, int]:
        if not self.applies_to(event):
            return 0.0, 0
        key = f"{self.seed}|{event.track}|{event.channel}|{event.note}|{event.start_beat:.6f}|{event.timing_intent}"
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        timing_unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        velocity_unit = int.from_bytes(digest[8:16], "big") / float(2**64 - 1)
        timing_offset = (timing_unit * 2.0 - 1.0) * self.max_offset_beats
        if self.velocity_jitter <= 0:
            velocity_delta = 0
        else:
            velocity_delta = round((velocity_unit * 2.0 - 1.0) * self.velocity_jitter)
        return timing_offset, int(velocity_delta)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_offset_beats": self.max_offset_beats,
            "velocity_jitter": self.velocity_jitter,
            "seed": self.seed,
            "affect_tracks": list(self.affect_tracks),
            "humanize_literal": self.humanize_literal,
            "profile_name": self.profile_name,
        }


@dataclass(frozen=True)
class TimingPolicy:
    """Style-owned timing policy consumed by the renderer timing stage."""

    feel: str = "straight"
    swing_ratio: float = 2.0 / 3.0
    half_beat_grid: float = 0.5
    humanization: HumanizationPolicy = field(default_factory=HumanizationPolicy)
    contract_version: str = TIMING_CONTRACT_VERSION
    boundary: str = "timing_policy_only_no_pattern_voicing_expression_content"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | "TimingPolicy" | None) -> "TimingPolicy":
        if isinstance(data, TimingPolicy):
            return data
        data = data or {}
        humanization_data = data.get("humanization") or {
            "enabled": data.get("humanize_enabled", False),
            "max_offset_beats": data.get("humanize_max_offset_beats", 0.0),
            "velocity_jitter": data.get("humanize_velocity_jitter", 0),
            "seed": data.get("humanize_seed", 0),
            "affect_tracks": data.get("humanize_tracks", ()),
        }
        return cls(
            feel=str(data.get("feel", "straight")),
            swing_ratio=float(data.get("swing_ratio", 2.0 / 3.0)),
            half_beat_grid=float(data.get("half_beat_grid", 0.5)),
            humanization=HumanizationPolicy.from_mapping(humanization_data),
            contract_version=str(data.get("version", data.get("contract_version", TIMING_CONTRACT_VERSION))),
            boundary=str(data.get("boundary", "timing_policy_only_no_pattern_voicing_expression_content")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "version": self.contract_version,
            "feel": self.feel,
            "swing_ratio": self.swing_ratio,
            "half_beat_grid": self.half_beat_grid,
            "humanization": self.humanization.to_debug_dict(),
            "boundary": self.boundary,
            "metadata": dict(self.metadata),
        }


DEFAULT_TIMING_POLICY = TimingPolicy()


def describe_timing_policy(timing_policy: Mapping[str, Any] | TimingPolicy | None = None) -> dict[str, Any]:
    return TimingPolicy.from_mapping(timing_policy).to_debug_dict()


def render_midi(
    note_events: list[NoteEvent],
    output_path: Path,
    tempo_bpm: int,
    timing_policy: Mapping[str, Any] | TimingPolicy | None = None,
) -> Path:
    path, _debug = render_midi_with_audit(note_events, output_path, tempo_bpm=tempo_bpm, timing_policy=timing_policy)
    return path


def render_midi_with_audit(
    note_events: list[NoteEvent],
    output_path: Path,
    tempo_bpm: int,
    timing_policy: Mapping[str, Any] | TimingPolicy | None = None,
) -> tuple[Path, dict[str, Any]]:
    policy = TimingPolicy.from_mapping(timing_policy)
    performed_events = apply_timing_policy(note_events, policy)
    pedal_events, pedal_audit = realize_pedal_events(performed_events, policy)
    path = write_midi(performed_events, output_path, tempo_bpm=tempo_bpm, pedal_events=pedal_events)
    return path, {
        "midi_render_version": PEDAL_REALIZER_VERSION,
        "timing_policy": policy.to_debug_dict(),
        "pedal_realization": pedal_audit,
    }


def realize_pedal_events(
    note_events: list[NoteEvent],
    timing_policy: Mapping[str, Any] | TimingPolicy | None = None,
) -> tuple[list[PedalEvent], dict[str, Any]]:
    """Convert already-resolved expression pedal intent into MIDI CC64 spans.

    v2_3_9 keeps the expression/pedal boundary from v2_3_7 but adds a
    Ballad-specific re-pedal offset.  Pianists do not usually hold one pedal
    span mechanically through a harmony change: the pedal comes up just before
    the next chord and goes back down just after the new attack.  That lift / 
    re-press belongs at the MIDI realization boundary because it is a performed
    controller detail, not a pattern, voicing, or expression-selection decision.
    """

    policy = TimingPolicy.from_mapping(timing_policy)
    style_id = str((policy.metadata or {}).get("style") or "").strip().lower()
    allowed_modes = _allowed_pedal_modes_for_style(style_id)
    mode_values = {"light": 64, "sustain": 96}
    eligible_tracks = {"piano"}
    repedal_policy = _repedal_policy_for_style(style_id)

    intent_counts: dict[str, int] = defaultdict(int)
    realized_counts: dict[str, int] = defaultdict(int)
    suppressed_counts: dict[str, int] = defaultdict(int)
    grouped: dict[tuple[str, int, str, str, float], list[NoteEvent]] = defaultdict(list)
    for event in note_events:
        mode = str(getattr(event, "pedal", "none") or "none").strip().lower()
        intent_counts[mode] += 1
        if event.track not in eligible_tracks or mode == "none":
            if mode != "none":
                suppressed_counts[f"{mode}:ineligible_track_or_mode"] += 1
            continue
        if mode not in allowed_modes:
            suppressed_counts[f"{mode}:style_boundary"] += 1
            continue
        event_key = str(event.expression_event_id or event.voicing_event_id or f"{event.track}:{event.start_beat:.6f}:{event.duration_beats:.6f}")
        grouped[(event.track, int(event.channel), event_key, mode, round(float(event.start_beat), 6))].append(event)

    raw_spans: list[dict[str, Any]] = []
    for (track, channel, event_key, mode, _start_key), notes in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][4], item[0][2])):
        start = min(float(note.start_beat) for note in notes)
        end = max(float(note.start_beat) + float(note.duration_beats) for note in notes)
        if end <= start:
            continue
        raw_spans.append(
            {
                "track": track,
                "channel": channel,
                "expression_event_id": event_key,
                "mode": mode,
                "raw_start_beat": start,
                "raw_end_beat": end,
                "note_count": len(notes),
            }
        )

    realized_spans = _apply_repedal_offsets(raw_spans, repedal_policy)
    pedal_events: list[PedalEvent] = []
    spans_sample: list[dict[str, Any]] = []
    repedal_gap_count = 0
    repedal_adjusted_count = 0
    repedal_gap_durations: list[float] = []
    repedal_warnings: list[str] = []
    for span in realized_spans:
        mode = str(span["mode"])
        value = mode_values.get(mode, 96)
        on_beat = float(span["cc64_on_beat"])
        off_beat = float(span["cc64_off_beat"])
        if off_beat <= on_beat:
            repedal_warnings.append(f"skipped_non_positive_pedal_span:{span['expression_event_id']}")
            continue
        pedal_events.append(PedalEvent(track=str(span["track"]), channel=int(span["channel"]), value=value, beat=on_beat, timing_intent="literal"))
        pedal_events.append(PedalEvent(track=str(span["track"]), channel=int(span["channel"]), value=0, beat=off_beat, timing_intent="literal"))
        realized_counts[mode] += 1
        if bool(span.get("repedal_gap_before_next")):
            repedal_gap_count += 1
            repedal_gap_durations.append(float(span.get("repedal_gap_beats") or 0.0))
        if bool(span.get("repedal_adjusted")):
            repedal_adjusted_count += 1
        if len(spans_sample) < 48:
            spans_sample.append(_round_span_for_audit(span, cc64_on_value=value))

    audit = {
        "pedal_realizer_version": PEDAL_REALIZER_VERSION,
        "repedal_policy_version": REPEDAL_POLICY_VERSION,
        "style": style_id or "unknown",
        "enabled": True,
        "boundary": "expression_pedal_intent_to_midi_cc64_with_style_repedal_offset_only_no_pattern_voicing_decision",
        "eligible_tracks": sorted(eligible_tracks),
        "allowed_modes": sorted(allowed_modes),
        "repedal_policy": dict(repedal_policy),
        "intent_note_counts_by_mode": dict(sorted(intent_counts.items())),
        "realized_span_counts_by_mode": dict(sorted(realized_counts.items())),
        "suppressed_note_counts_by_reason": dict(sorted(suppressed_counts.items())),
        "cc64_event_count": len(pedal_events),
        "cc64_on_count": sum(1 for event in pedal_events if int(event.value) >= 64),
        "cc64_off_count": sum(1 for event in pedal_events if int(event.value) < 64),
        "repedal_offset_enabled": bool(repedal_policy.get("enabled")),
        "repedal_adjusted_span_count": repedal_adjusted_count,
        "repedal_gap_count": repedal_gap_count,
        "repedal_gap_beats_min": round(min(repedal_gap_durations), 6) if repedal_gap_durations else 0.0,
        "repedal_gap_beats_max": round(max(repedal_gap_durations), 6) if repedal_gap_durations else 0.0,
        "repedal_gap_beats_avg": round(sum(repedal_gap_durations) / len(repedal_gap_durations), 6) if repedal_gap_durations else 0.0,
        "repedal_warning_count": len(repedal_warnings),
        "repedal_warnings_sample": repedal_warnings[:12],
        "spans_sample": spans_sample,
    }
    return pedal_events, audit


REPEDAL_POLICY_VERSION = "v2_3_9"


def _repedal_policy_for_style(style_id: str) -> dict[str, Any]:
    """Return controller-level re-pedal behavior for a style.

    Only Jazz Ballad gets a re-pedal offset by default.  Dry styles suppress
    CC64 before this point, so their policy is intentionally disabled.
    """

    style = str(style_id or "").strip().lower()
    if style == "jazz_ballad":
        return {
            "enabled": True,
            "on_after_attack_beats": 0.02,
            "lift_before_next_onset_beats": 0.035,
            "minimum_gap_beats": 0.02,
            "minimum_span_beats": 0.05,
            "reason": "ballad_repedal_after_new_chord_attack_and_lift_before_next_harmony",
        }
    return {
        "enabled": False,
        "on_after_attack_beats": 0.0,
        "lift_before_next_onset_beats": 0.0,
        "minimum_gap_beats": 0.0,
        "minimum_span_beats": 0.0,
        "reason": "dry_or_unknown_style_no_cc64_repedal_offset",
    }


def _apply_repedal_offsets(raw_spans: list[dict[str, Any]], repedal_policy: Mapping[str, Any]) -> list[dict[str, Any]]:
    enabled = bool(repedal_policy.get("enabled"))
    on_after = max(0.0, float(repedal_policy.get("on_after_attack_beats") or 0.0)) if enabled else 0.0
    lift_before = max(0.0, float(repedal_policy.get("lift_before_next_onset_beats") or 0.0)) if enabled else 0.0
    minimum_span = max(0.0, float(repedal_policy.get("minimum_span_beats") or 0.0)) if enabled else 0.0
    minimum_gap = max(0.0, float(repedal_policy.get("minimum_gap_beats") or 0.0)) if enabled else 0.0
    realized: list[dict[str, Any]] = []
    spans_by_channel: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for span in raw_spans:
        spans_by_channel[(str(span["track"]), int(span["channel"]))].append(span)

    for (_track, _channel), spans in sorted(spans_by_channel.items(), key=lambda item: item[0]):
        ordered = sorted(spans, key=lambda span: (float(span["raw_start_beat"]), str(span["expression_event_id"])))
        for index, span in enumerate(ordered):
            start = float(span["raw_start_beat"])
            end = float(span["raw_end_beat"])
            next_start = float(ordered[index + 1]["raw_start_beat"]) if index + 1 < len(ordered) else None
            on = start + on_after
            off = end
            repedal_gap = 0.0
            repedal_gap_before_next = False
            if enabled and next_start is not None and next_start > start:
                target_off = min(end, next_start - lift_before)
                # Keep the span audible and preserve at least a small pedal gap
                # before the next pedal-down if there is enough room.
                min_off = on + minimum_span
                if target_off < min_off:
                    target_off = min(end, min_off)
                if target_off < end:
                    off = target_off
                next_on = next_start + on_after
                repedal_gap = max(0.0, next_on - off)
                if repedal_gap < minimum_gap and next_on > minimum_gap:
                    earlier_off = max(on + minimum_span, next_on - minimum_gap)
                    if earlier_off <= end:
                        off = earlier_off
                        repedal_gap = max(0.0, next_on - off)
                repedal_gap_before_next = repedal_gap >= max(1e-9, minimum_gap)
            # A final safety clamp for pathological very short spans.
            if off <= on:
                on = start
                off = end
            out = dict(span)
            out.update(
                {
                    "cc64_on_beat": on,
                    "cc64_off_beat": off,
                    "repedal_adjusted": bool(enabled and (abs(on - start) > 1e-9 or abs(off - end) > 1e-9)),
                    "repedal_on_after_attack_beats": on_after,
                    "repedal_lift_before_next_onset_beats": lift_before,
                    "repedal_next_raw_start_beat": next_start,
                    "repedal_gap_before_next": repedal_gap_before_next,
                    "repedal_gap_beats": repedal_gap,
                }
            )
            realized.append(out)
    return sorted(realized, key=lambda span: (int(span["channel"]), float(span["cc64_on_beat"]), str(span["expression_event_id"])))


def _round_span_for_audit(span: Mapping[str, Any], *, cc64_on_value: int) -> dict[str, Any]:
    rounded: dict[str, Any] = {
        "track": span.get("track"),
        "channel": span.get("channel"),
        "expression_event_id": span.get("expression_event_id"),
        "mode": span.get("mode"),
        "cc64_on_value": cc64_on_value,
        "raw_start_beat": round(float(span.get("raw_start_beat") or 0.0), 6),
        "raw_end_beat": round(float(span.get("raw_end_beat") or 0.0), 6),
        "cc64_on_beat": round(float(span.get("cc64_on_beat") or 0.0), 6),
        "cc64_off_beat": round(float(span.get("cc64_off_beat") or 0.0), 6),
        "duration_beats": round(float(span.get("cc64_off_beat") or 0.0) - float(span.get("cc64_on_beat") or 0.0), 6),
        "note_count": int(span.get("note_count") or 0),
        "repedal_adjusted": bool(span.get("repedal_adjusted")),
        "repedal_gap_before_next": bool(span.get("repedal_gap_before_next")),
        "repedal_gap_beats": round(float(span.get("repedal_gap_beats") or 0.0), 6),
    }
    if span.get("repedal_next_raw_start_beat") is not None:
        rounded["repedal_next_raw_start_beat"] = round(float(span.get("repedal_next_raw_start_beat") or 0.0), 6)
    return rounded

def _allowed_pedal_modes_for_style(style_id: str) -> set[str]:
    style = str(style_id or "").strip().lower()
    if style == "jazz_ballad":
        return {"light", "sustain"}
    if style in {"bossa_nova", "medium_swing", "medium_swing_voicing_tuning"}:
        return set()
    return {"sustain"}


def apply_timing_policy(
    note_events: list[NoteEvent],
    timing_policy: Mapping[str, Any] | TimingPolicy | None = None,
) -> list[NoteEvent]:
    """Convert logical beat-grid events into performed beat positions.

    Pattern/generation stages write musical grid locations: e.g. ``0.5`` means
    the written upbeat ``1&``.  The timing stage may then apply style grid
    interpretation, such as swing upbeats, and optional deterministic
    humanization. Timing never decides pattern choice, pitch content, voicing,
    expression duration, or pedal behavior.

    Timing intents:
    - ``auto``: use the style timing policy. In swing styles, half-beat grid
      slots are interpreted as swing upbeats.
    - ``swing_upbeat``: force swing interpretation for a half-beat slot.
    - ``straight_even``: keep the written ``.5`` exactly even, even in swing.
    - ``literal``: do not transform this event's start beat. Humanization is
      also skipped unless ``humanize_literal`` is explicitly enabled.
    """

    policy = TimingPolicy.from_mapping(timing_policy)
    out: list[NoteEvent] = []
    for event in note_events:
        performed_start = performed_beat(event.start_beat, event.timing_intent, policy)
        grid_offset = performed_start - float(event.start_beat)
        human_offset, velocity_delta = policy.humanization.offsets_for_event(event)
        final_start = max(0.0, performed_start + human_offset)
        final_velocity = max(1, min(127, int(event.velocity) + velocity_delta))
        timing_debug = {
            "policy_version": policy.contract_version,
            "feel": policy.feel,
            "timing_intent": event.timing_intent,
            "logical_start_beat": float(event.start_beat),
            "grid_offset_beats": grid_offset,
            "humanization_offset_beats": human_offset,
            "velocity_delta": velocity_delta,
            "humanization_profile": policy.humanization.profile_name,
        }
        out.append(
            replace(
                event,
                start_beat=final_start,
                velocity=final_velocity,
                logical_start_beat=float(event.start_beat),
                timing_grid_offset_beats=grid_offset,
                humanization_offset_beats=human_offset,
                timing_policy_version=policy.contract_version,
                timing_profile=policy.feel,
                timing_debug=timing_debug,
            )
        )
    return out


def performed_beat(
    logical_beat: float,
    timing_intent: str = "auto",
    timing_policy: Mapping[str, Any] | TimingPolicy | None = None,
) -> float:
    policy = TimingPolicy.from_mapping(timing_policy)
    intent = str(timing_intent or "auto")
    if intent in {"straight_even", "literal"}:
        return float(logical_beat)
    if intent == "swing_upbeat" or (intent == "auto" and policy.feel == "swing"):
        return _swing_half_beat(logical_beat, policy.swing_ratio, policy.half_beat_grid)
    return float(logical_beat)


def _swing_half_beat(logical_beat: float, swing_ratio: float, half_beat_grid: float = 0.5) -> float:
    beat = float(logical_beat)
    whole = int(beat)
    frac = beat - whole
    # Only written eighth upbeats are swung. A real triplet, grace offset,
    # rolled-chord offset, or explicitly straight event should remain literal.
    if abs(frac - half_beat_grid) < 1e-6:
        return whole + swing_ratio
    return beat
