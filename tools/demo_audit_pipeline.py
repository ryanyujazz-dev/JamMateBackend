from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.midi.render_pipeline import performed_beat

DEMO_AUDIT_PIPELINE_VERSION = "v2_3_9"
DEFAULT_OUTPUT_DIR = ROOT / "demos"
ALTERED_DEGREES = {"b9", "#9", "#11", "b13", "#5", "b5"}


@dataclass(frozen=True)
class DemoAuditJob:
    """One stable listening-demo + audit-output request.

    The job is intentionally runtime-facing. It does not know style internals;
    it only supplies a leadsheet, style, request controls, and optional voicing
    override metadata to the public generate_accompaniment() entrypoint.
    """

    job_id: str
    leadsheet: str
    style: str
    tempo: int
    seed: int = 42
    choruses: int = 3
    ensemble: dict[str, Any] = field(default_factory=lambda: {"bass_present": True})
    voicing_override: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    tags: tuple[str, ...] = ()

    @property
    def output_stem(self) -> str:
        return f"{ENGINE_VERSION_TAG}_{self.job_id}"


@dataclass(frozen=True)
class AuditThresholds:
    """Minimal listening-regression thresholds for one demo/audit job.

    These checks intentionally stay at the public audit-summary boundary. They
    verify that a generated demo is structurally audible and that jobs carrying
    a musical purpose, such as altered dominant or upper-structure coverage,
    actually produce the corresponding audit signal. They are not a replacement
    for human listening review.
    """

    required_choruses: int = 3
    min_total_note_events: int = 1
    min_piano_note_events: int = 1
    min_piano_audit_events: int = 1
    max_register_guard_violations: int = 0
    min_altered_degree_events: int = 0
    min_altered_source_events: int = 0
    min_upper_structure_events: int = 0
    min_non_four_density_events: int = 0
    min_anticipation_events: int = 0
    max_anticipation_events: int | None = None
    max_unresolved_anticipation_ties: int = 0
    max_cross_next_event_count: int | None = None
    max_expression_warning_count: int | None = None
    max_anticipation_timing_grid_error: float | None = None
    min_anticipation_pedal_release_micro_tuned_events: int = 0
    max_anticipation_sustain_pedal_events: int | None = None
    max_anticipation_avg_release_beats: float | None = None
    min_pedal_cc64_events: int = 0
    max_pedal_cc64_events: int | None = None
    min_pedal_realized_spans: int = 0
    max_pedal_realized_spans: int | None = None
    min_repedal_adjusted_spans: int = 0
    max_repedal_adjusted_spans: int | None = None
    min_repedal_gap_count: int = 0
    max_repedal_gap_count: int | None = None
    min_repedal_gap_beats: float | None = None
    max_repedal_warning_count: int | None = 0
    max_top_note: int | None = None
    max_average_pitch_mean: float | None = None


@dataclass(frozen=True)
class DemoMatrixEntry:
    """One manifest-driven regression entry wrapping a standard demo job."""

    matrix_id: str
    job_id: str
    thresholds: AuditThresholds = field(default_factory=AuditThresholds)
    description: str = ""




def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _mean(values: Iterable[int | float]) -> float:
    items = [float(v) for v in values]
    return round(mean(items), 3) if items else 0.0


def _counter(counter: Counter[str]) -> dict[str, int]:
    return {key: int(value) for key, value in sorted(counter.items())}


def _compact_mapping(data: dict[str, Any], *, keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: data.get(key) for key in keys if key in data}


def _altered_dominant_override(*, intensity: str, scopes: list[str]) -> dict[str, Any]:
    return {
        "enabled": True,
        "harmonic_expansion_enabled": True,
        "color_policy_mode": "altered_dominant",
        "metadata": {
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "altered_dominant",
            "altered_dominant_enabled": True,
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": intensity,
                "scopes": scopes,
                "llm_controllable": True,
            },
            "demo_audit_pipeline_job_controlled": True,
        },
    }


def _ballad_upper_structure_altered_override() -> dict[str, Any]:
    data = _altered_dominant_override(
        intensity="high",
        scopes=["resolving_v7", "secondary_dominants", "backdoor_dominants", "llm_selected"],
    )
    data.update(
        {
            # v2_3_9: keep this as a musical listening demo, not voicing
            # isolation.  Previous pipeline versions forced one region-start
            # anchor per chord, which was useful for audit coverage but lost the
            # natural Jazz Ballad comping feel.
            "mute_bass": False,
        }
    )
    metadata = data["metadata"]
    metadata.update(
        {
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "spread_selector_enabled": True,
            "spread_upper_structure_enabled": True,
            "spread_upper_structure_prefer": True,
            "upper_structure_register_refinement_enabled": True,
            "low_register_single_note_threshold": 40,
            "max_notes_below_low_register_single_note_threshold": 1,
            "upper_structure_top_soft_high": 72,
            "upper_structure_top_hard_high": 74,
            "upper_structure_average_pitch_soft_high": 66,
            "spread_low_register_density_guard_enabled": True,
            "spread_low_register_density_threshold": 40,
            "spread_low_register_density_max_notes_below": 1,
            "spread_groupwise_voice_leading_runtime_enabled": True,
            "spread_emit_all_candidates_for_groupwise_selection": True,
            "spread_runtime_adapter_emit_all_candidates": True,
            "spread_runtime_adapter_max_upper_options": 36,
            "spread_upper_4note_emit_all_parent_projections": True,
            "spread_upper_4note_allow_octave_shift_candidates": True,
            "spread_min_group_gap": 1,
            "spread_max_group_gap": 28,
            "spread_target_group_gap": 7,
            "spread_comfort_group_gap_max": 12,
            "spread_top_voice_continuity_weight": 2.7,
            "ballad_spread_grouping_mix_policy": {"enabled": True},
            "spread_upper_3note_expanded_color_target_ratio": 0.55,
            "spread_upper_4note_expanded_color_target_ratio": 0.45,
            "spread_lower_2note_rooted_equal_weight_cycle_enabled": True,
            "voicing_register_continuity_guard_enabled": True,
            "voicing_register_center_target": 64,
            "voicing_register_center_tolerance": 4,
            "spread_upper_high": 74,
            "spread_whole_register_high": 76,
            "voicing_register_top_soft_high": 72,
            "voicing_register_top_hard_high": 74,
            "voicing_register_low_soft_low": 43,
            "voicing_register_low_hard_low": 40,
            "voicing_register_top_motion_soft_limit": 4,
            "voicing_register_average_motion_soft_limit": 3.5,
            "voicing_register_continuity_weight": 1.25,
            "weights_by_scene": {
                "normal_comping": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 52,
                    "spread_2plus4_contract": 26,
                    "spread_3plus3_contract": 20,
                    "spread_3plus4_contract": 2,
                },
                "chorus_lift": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 30,
                    "spread_2plus4_contract": 34,
                    "spread_3plus3_contract": 30,
                    "spread_3plus4_contract": 6,
                },
                "ending_climax": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 16,
                    "spread_2plus4_contract": 34,
                    "spread_3plus3_contract": 38,
                    "spread_3plus4_contract": 12,
                },
            },
        }
    )
    return data


def standard_jobs() -> dict[str, DemoAuditJob]:
    return {
        "minimal_swing": DemoAuditJob(
            job_id="minimal_swing_pipeline_smoke_demo",
            leadsheet="minimal_ii_v_i.json",
            style="medium_swing",
            tempo=132,
            seed=42,
            description="Small ii–V–I smoke demo proving the consolidated pipeline can run a plain request.",
            tags=("smoke", "medium_swing"),
        ),
        "misty_ballad_upper_structure_altered": DemoAuditJob(
            job_id="misty_jazz_ballad_upper_structure_altered_pipeline_demo",
            leadsheet="misty.json",
            style="jazz_ballad",
            tempo=72,
            seed=89,
            voicing_override=_ballad_upper_structure_altered_override(),
            description="Three-chorus Misty listening demo for Ballad spread/upper-structure altered voicing guard checks.",
            tags=("standard_tune", "jazz_ballad", "upper_structure", "altered_dominant"),
        ),
        "blue_bossa_minor_altered": DemoAuditJob(
            job_id="blue_bossa_minor_altered_pipeline_demo",
            leadsheet="blue_bossa.json",
            style="bossa_nova",
            tempo=132,
            seed=88,
            voicing_override=_altered_dominant_override(
                intensity="light",
                scopes=["resolving_v7", "secondary_dominants", "functional_dominants"],
            ),
            description="Three-chorus Blue Bossa listening demo for minor V and light Bossa altered audit checks.",
            tags=("standard_tune", "bossa_nova", "minor_v", "altered_dominant"),
        ),
        "minor_turnaround_fixture": DemoAuditJob(
            job_id="minor_turnaround_altered_pipeline_fixture_demo",
            leadsheet="altered_dominant_minor_turnaround_coverage.json",
            style="medium_swing",
            tempo=116,
            seed=88,
            voicing_override=_altered_dominant_override(
                intensity="high",
                scopes=["resolving_v7", "secondary_dominants", "functional_dominants"],
            ),
            description="Compact fixture for home minor, local minor secondary, turnaround VI7, and final V7 scope coverage.",
            tags=("fixture", "minor_v", "turnaround", "altered_dominant"),
        ),
    }



def standard_demo_matrix() -> dict[str, DemoMatrixEntry]:
    """Return the canonical listening-regression matrix for this version.

    The matrix is deliberately small and stable. It exercises the canonical
    plain smoke demo, the Ballad upper-structure/altered path, the Bossa minor
    altered path, and the compact minor/turnaround fixture. v2_3_9 also treats
    anticipation as a listening-regression target: every style job must keep
    expected 4& pushes tied, bounded, and free from next-event sustain overlap.
    """

    return {
        "minimal_swing_smoke": DemoMatrixEntry(
            matrix_id="minimal_swing_smoke",
            job_id="minimal_swing",
            thresholds=AuditThresholds(
                min_anticipation_events=1,
                max_anticipation_events=3,
                max_cross_next_event_count=0,
                max_expression_warning_count=0,
                max_anticipation_timing_grid_error=1e-6,
                min_anticipation_pedal_release_micro_tuned_events=1,
                max_anticipation_sustain_pedal_events=0,
                max_anticipation_avg_release_beats=0.035,
                max_pedal_cc64_events=0,
                max_pedal_realized_spans=0,
                max_repedal_adjusted_spans=0,
                max_repedal_gap_count=0,
                max_repedal_warning_count=0,
            ),
            description="Plain medium-swing ii–V–I smoke demo with audible piano output.",
        ),
        "misty_ballad_upper_structure_altered": DemoMatrixEntry(
            matrix_id="misty_ballad_upper_structure_altered",
            job_id="misty_ballad_upper_structure_altered",
            thresholds=AuditThresholds(
                min_altered_degree_events=1,
                min_altered_source_events=1,
                min_upper_structure_events=1,
                min_non_four_density_events=50,
                max_top_note=74,
                max_average_pitch_mean=62.0,
                min_anticipation_events=8,
                max_anticipation_events=30,
                max_cross_next_event_count=0,
                max_expression_warning_count=0,
                max_anticipation_timing_grid_error=1e-6,
                min_anticipation_pedal_release_micro_tuned_events=8,
                max_anticipation_sustain_pedal_events=0,
                max_anticipation_avg_release_beats=0.085,
                min_pedal_cc64_events=1,
                min_pedal_realized_spans=1,
                min_repedal_adjusted_spans=1,
                min_repedal_gap_count=1,
                min_repedal_gap_beats=0.02,
                max_repedal_warning_count=0,
            ),
            description="Ballad standard tune must expose upper-structure and altered-dominant audit signal.",
        ),
        "blue_bossa_minor_altered": DemoMatrixEntry(
            matrix_id="blue_bossa_minor_altered",
            job_id="blue_bossa_minor_altered",
            thresholds=AuditThresholds(
                min_altered_degree_events=1,
                min_altered_source_events=1,
                min_anticipation_events=8,
                max_anticipation_events=20,
                max_cross_next_event_count=0,
                max_expression_warning_count=0,
                max_anticipation_timing_grid_error=1e-6,
                min_anticipation_pedal_release_micro_tuned_events=8,
                max_anticipation_sustain_pedal_events=0,
                max_anticipation_avg_release_beats=0.045,
                max_pedal_cc64_events=0,
                max_pedal_realized_spans=0,
                max_repedal_adjusted_spans=0,
                max_repedal_gap_count=0,
                max_repedal_warning_count=0,
            ),
            description="Bossa minor-standard demo must retain light altered-dominant audit signal.",
        ),
        "minor_turnaround_fixture": DemoMatrixEntry(
            matrix_id="minor_turnaround_fixture",
            job_id="minor_turnaround_fixture",
            thresholds=AuditThresholds(
                min_altered_degree_events=1,
                min_altered_source_events=1,
                min_anticipation_events=1,
                max_anticipation_events=6,
                max_cross_next_event_count=0,
                max_expression_warning_count=0,
                max_anticipation_timing_grid_error=1e-6,
                min_anticipation_pedal_release_micro_tuned_events=1,
                max_anticipation_sustain_pedal_events=0,
                max_anticipation_avg_release_beats=0.035,
                max_pedal_cc64_events=0,
                max_pedal_realized_spans=0,
                max_repedal_adjusted_spans=0,
                max_repedal_gap_count=0,
                max_repedal_warning_count=0,
            ),
            description="Compact fixture must keep minor V / turnaround altered coverage alive.",
        ),
    }


def _actual_threshold_values(audit: dict[str, Any]) -> dict[str, Any]:
    runtime = dict(audit.get("runtime_summary") or {})
    piano = dict(audit.get("piano_event_summary") or {})
    track_counts = dict(runtime.get("note_events_by_track") or {})
    altered_source_events = sum(int(value) for value in (piano.get("altered_dominant_source_kinds") or {}).values())
    musical = dict(audit.get("piano_musical_audit") or {})
    densities = {str(key): int(value) for key, value in (musical.get("densities") or {}).items()}
    density_event_count = sum(densities.values())
    non_four_density_events = density_event_count - int(densities.get("4") or 0)
    expression = dict(audit.get("expression_foundation_audit") or {})
    pedal_realization = dict(audit.get("pedal_realization_audit") or {})
    realized_spans = sum(int(value) for value in (pedal_realization.get("realized_span_counts_by_mode") or {}).values())
    anticipation_events = int(piano.get("anticipation_events") or 0)
    anticipation_tie_events = int(piano.get("anticipation_tie_expression_events") or 0)
    return {
        "performance_choruses": runtime.get("performance_choruses"),
        "note_events": int(runtime.get("note_events") or 0),
        "piano_note_events": int(track_counts.get("piano") or 0),
        "piano_audit_events": int(piano.get("event_count") or 0),
        "register_guard_violations": int(piano.get("register_guard_violations") or 0),
        "altered_degree_events": int(piano.get("altered_degree_events") or 0),
        "altered_source_events": altered_source_events,
        "upper_structure_events": int(piano.get("upper_structure_register_refinement_events") or 0),
        "anticipation_events": anticipation_events,
        "anticipation_tie_expression_events": anticipation_tie_events,
        "unresolved_anticipation_ties": max(0, anticipation_events - anticipation_tie_events),
        "cross_next_event_count": int(expression.get("cross_next_event_count") or 0),
        "expression_warning_count": int(expression.get("warning_count") or 0),
        "anticipation_timing_grid_error_max": piano.get("anticipation_timing_grid_error_max"),
        "anticipation_timing_grid_failures": int(piano.get("anticipation_timing_grid_failures") or 0),
        "anticipation_pedal_release_micro_tuned_events": int(expression.get("anticipation_pedal_release_micro_tuned_count") or 0),
        "anticipation_sustain_pedal_events": int((expression.get("anticipation_pedal_modes") or {}).get("sustain") or 0),
        "anticipation_avg_release_beats": float(expression.get("anticipation_avg_release_beats") or 0.0),
        "pedal_cc64_events": int(pedal_realization.get("cc64_event_count") or 0),
        "pedal_cc64_on_events": int(pedal_realization.get("cc64_on_count") or 0),
        "pedal_realized_spans": int(realized_spans),
        "pedal_realized_modes": dict(pedal_realization.get("realized_span_counts_by_mode") or {}),
        "pedal_suppressed_reasons": dict(pedal_realization.get("suppressed_note_counts_by_reason") or {}),
        "repedal_offset_enabled": bool(pedal_realization.get("repedal_offset_enabled")),
        "repedal_adjusted_spans": int(pedal_realization.get("repedal_adjusted_span_count") or 0),
        "repedal_gap_count": int(pedal_realization.get("repedal_gap_count") or 0),
        "repedal_gap_beats_min": float(pedal_realization.get("repedal_gap_beats_min") or 0.0),
        "repedal_gap_beats_max": float(pedal_realization.get("repedal_gap_beats_max") or 0.0),
        "repedal_gap_beats_avg": float(pedal_realization.get("repedal_gap_beats_avg") or 0.0),
        "repedal_warning_count": int(pedal_realization.get("repedal_warning_count") or 0),
        "density_event_count": density_event_count,
        "four_note_density_events": int(densities.get("4") or 0),
        "non_four_density_events": non_four_density_events,
        "top_note_max": piano.get("top_note_max"),
        "average_pitch_mean": piano.get("average_pitch_mean"),
    }


def _threshold_violation(code: str, *, expected: Any, actual: Any, message: str) -> dict[str, Any]:
    return {"code": code, "expected": expected, "actual": actual, "message": message}


def validate_audit_summary(audit: dict[str, Any], thresholds: AuditThresholds) -> list[dict[str, Any]]:
    """Validate one audit summary against listening-regression thresholds."""

    actual = _actual_threshold_values(audit)
    violations: list[dict[str, Any]] = []
    checks = [
        ("required_choruses", actual["performance_choruses"], thresholds.required_choruses, "performance choruses must match the standard listening loop"),
        ("min_total_note_events", actual["note_events"], thresholds.min_total_note_events, "demo must contain audible note events"),
        ("min_piano_note_events", actual["piano_note_events"], thresholds.min_piano_note_events, "demo must contain piano note events"),
        ("min_piano_audit_events", actual["piano_audit_events"], thresholds.min_piano_audit_events, "piano audit must include selected events"),
        ("min_altered_degree_events", actual["altered_degree_events"], thresholds.min_altered_degree_events, "altered jobs must expose altered degree events"),
        ("min_altered_source_events", actual["altered_source_events"], thresholds.min_altered_source_events, "altered jobs must expose altered source-kind events"),
        ("min_upper_structure_events", actual["upper_structure_events"], thresholds.min_upper_structure_events, "upper-structure jobs must expose register-refinement events"),
        ("min_non_four_density_events", actual["non_four_density_events"], thresholds.min_non_four_density_events, "density-targeted jobs must not collapse to all 4-note voicings"),
        ("min_anticipation_events", actual["anticipation_events"], thresholds.min_anticipation_events, "style anticipation jobs must keep expected 4& push coverage"),
        ("min_anticipation_pedal_release_micro_tuned_events", actual["anticipation_pedal_release_micro_tuned_events"], thresholds.min_anticipation_pedal_release_micro_tuned_events, "anticipated chords must receive style-specific release/pedal micro-tuning"),
        ("min_pedal_cc64_events", actual["pedal_cc64_events"], thresholds.min_pedal_cc64_events, "pedal-enabled jobs must materialize expression pedal intent as MIDI CC64 events"),
        ("min_pedal_realized_spans", actual["pedal_realized_spans"], thresholds.min_pedal_realized_spans, "pedal-enabled jobs must realize at least one CC64 pedal span"),
    ]
    for code, value, expected, message in checks:
        if code == "required_choruses":
            if value != expected:
                violations.append(_threshold_violation(code, expected=expected, actual=value, message=message))
        elif value < expected:
            violations.append(_threshold_violation(code, expected=f">= {expected}", actual=value, message=message))
    if actual["register_guard_violations"] > thresholds.max_register_guard_violations:
        violations.append(
            _threshold_violation(
                "max_register_guard_violations",
                expected=f"<= {thresholds.max_register_guard_violations}",
                actual=actual["register_guard_violations"],
                message="register guard violations must stay below the job threshold",
            )
        )
    if actual["unresolved_anticipation_ties"] > thresholds.max_unresolved_anticipation_ties:
        violations.append(
            _threshold_violation(
                "max_unresolved_anticipation_ties",
                expected=f"<= {thresholds.max_unresolved_anticipation_ties}",
                actual=actual["unresolved_anticipation_ties"],
                message="every inserted anticipation must receive expression-layer tie sustain handling",
            )
        )
    if thresholds.max_anticipation_events is not None and actual["anticipation_events"] > thresholds.max_anticipation_events:
        violations.append(
            _threshold_violation(
                "max_anticipation_events",
                expected=f"<= {thresholds.max_anticipation_events}",
                actual=actual["anticipation_events"],
                message="style anticipation must stay within the calibrated density range",
            )
        )
    if thresholds.max_cross_next_event_count is not None and actual["cross_next_event_count"] > thresholds.max_cross_next_event_count:
        violations.append(
            _threshold_violation(
                "max_cross_next_event_count",
                expected=f"<= {thresholds.max_cross_next_event_count}",
                actual=actual["cross_next_event_count"],
                message="sustained harmony should not overlap the next same-track event after anticipation calibration",
            )
        )
    if thresholds.max_expression_warning_count is not None and actual["expression_warning_count"] > thresholds.max_expression_warning_count:
        violations.append(
            _threshold_violation(
                "max_expression_warning_count",
                expected=f"<= {thresholds.max_expression_warning_count}",
                actual=actual["expression_warning_count"],
                message="calibrated listening jobs should be free from expression audit warnings",
            )
        )
    if thresholds.max_anticipation_timing_grid_error is not None:
        error = actual.get("anticipation_timing_grid_error_max")
        failures = int(actual.get("anticipation_timing_grid_failures") or 0)
        if error is None or float(error) > thresholds.max_anticipation_timing_grid_error or failures > 0:
            violations.append(
                _threshold_violation(
                    "max_anticipation_timing_grid_error",
                    expected=f"<= {thresholds.max_anticipation_timing_grid_error} and 0 failures",
                    actual={"error_max": error, "failures": failures},
                    message="anticipated beat-1 rewrites must land on the style timing grid, e.g. medium swing written 4& must perform at the 2/3 upbeat",
                )
            )
    if thresholds.max_anticipation_sustain_pedal_events is not None and actual["anticipation_sustain_pedal_events"] > thresholds.max_anticipation_sustain_pedal_events:
        violations.append(
            _threshold_violation(
                "max_anticipation_sustain_pedal_events",
                expected=f"<= {thresholds.max_anticipation_sustain_pedal_events}",
                actual=actual["anticipation_sustain_pedal_events"],
                message="anticipation micro-tuning must not leave full sustain pedal on pushed chords",
            )
        )
    if thresholds.max_anticipation_avg_release_beats is not None and actual["anticipation_avg_release_beats"] > thresholds.max_anticipation_avg_release_beats:
        violations.append(
            _threshold_violation(
                "max_anticipation_avg_release_beats",
                expected=f"<= {thresholds.max_anticipation_avg_release_beats}",
                actual=actual["anticipation_avg_release_beats"],
                message="anticipated chords must keep calibrated release length for this style",
            )
        )
    if thresholds.max_pedal_cc64_events is not None and actual["pedal_cc64_events"] > thresholds.max_pedal_cc64_events:
        violations.append(
            _threshold_violation(
                "max_pedal_cc64_events",
                expected=f"<= {thresholds.max_pedal_cc64_events}",
                actual=actual["pedal_cc64_events"],
                message="dry styles must not materialize expression pedal intent as MIDI CC64",
            )
        )
    if thresholds.max_pedal_realized_spans is not None and actual["pedal_realized_spans"] > thresholds.max_pedal_realized_spans:
        violations.append(
            _threshold_violation(
                "max_pedal_realized_spans",
                expected=f"<= {thresholds.max_pedal_realized_spans}",
                actual=actual["pedal_realized_spans"],
                message="dry styles must keep realized CC64 pedal span count at zero",
            )
        )
    if actual["repedal_adjusted_spans"] < thresholds.min_repedal_adjusted_spans:
        violations.append(
            _threshold_violation(
                "min_repedal_adjusted_spans",
                expected=f">= {thresholds.min_repedal_adjusted_spans}",
                actual=actual["repedal_adjusted_spans"],
                message="Ballad CC64 must use human-like re-pedal offsets instead of mechanical same-tick pedal spans",
            )
        )
    if thresholds.max_repedal_adjusted_spans is not None and actual["repedal_adjusted_spans"] > thresholds.max_repedal_adjusted_spans:
        violations.append(
            _threshold_violation(
                "max_repedal_adjusted_spans",
                expected=f"<= {thresholds.max_repedal_adjusted_spans}",
                actual=actual["repedal_adjusted_spans"],
                message="Dry styles must not create CC64 re-pedal offsets",
            )
        )
    if actual["repedal_gap_count"] < thresholds.min_repedal_gap_count:
        violations.append(
            _threshold_violation(
                "min_repedal_gap_count",
                expected=f">= {thresholds.min_repedal_gap_count}",
                actual=actual["repedal_gap_count"],
                message="Ballad harmony changes must include pedal-up gaps before re-pedaling",
            )
        )
    if thresholds.max_repedal_gap_count is not None and actual["repedal_gap_count"] > thresholds.max_repedal_gap_count:
        violations.append(
            _threshold_violation(
                "max_repedal_gap_count",
                expected=f"<= {thresholds.max_repedal_gap_count}",
                actual=actual["repedal_gap_count"],
                message="Dry styles must not create re-pedal gaps",
            )
        )
    if thresholds.min_repedal_gap_beats is not None and actual["repedal_gap_count"] > 0:
        if actual["repedal_gap_beats_min"] < thresholds.min_repedal_gap_beats:
            violations.append(
                _threshold_violation(
                    "min_repedal_gap_beats",
                    expected=f">= {thresholds.min_repedal_gap_beats}",
                    actual=actual["repedal_gap_beats_min"],
                    message="Re-pedal lift must leave an audible controller gap before the next pedal-down",
                )
            )
    if thresholds.max_repedal_warning_count is not None and actual["repedal_warning_count"] > thresholds.max_repedal_warning_count:
        violations.append(
            _threshold_violation(
                "max_repedal_warning_count",
                expected=f"<= {thresholds.max_repedal_warning_count}",
                actual=actual["repedal_warning_count"],
                message="Re-pedal realization should not produce malformed or skipped pedal spans",
            )
        )
    if thresholds.max_top_note is not None:
        top_note_max = actual.get("top_note_max")
        if top_note_max is None or int(top_note_max) > thresholds.max_top_note:
            violations.append(
                _threshold_violation(
                    "max_top_note",
                    expected=f"<= {thresholds.max_top_note}",
                    actual=top_note_max,
                    message="voicing register must not drift into the high/bright ceiling for this job",
                )
            )
    if thresholds.max_average_pitch_mean is not None:
        average_pitch_mean = actual.get("average_pitch_mean")
        if average_pitch_mean is None or float(average_pitch_mean) > thresholds.max_average_pitch_mean:
            violations.append(
                _threshold_violation(
                    "max_average_pitch_mean",
                    expected=f"<= {thresholds.max_average_pitch_mean}",
                    actual=average_pitch_mean,
                    message="voicing average pitch must stay near the target register center",
                )
            )
    return violations


def validate_job_audit(job_id: str, audit: dict[str, Any], matrix: dict[str, DemoMatrixEntry] | None = None) -> dict[str, Any]:
    matrix = matrix or standard_demo_matrix()
    entries = [entry for entry in matrix.values() if entry.job_id == job_id]
    if not entries:
        return {
            "job_id": job_id,
            "status": "not_in_matrix",
            "actual": _actual_threshold_values(audit),
            "violations": [],
        }
    entry = entries[0]
    violations = validate_audit_summary(audit, entry.thresholds)
    return {
        "matrix_id": entry.matrix_id,
        "job_id": job_id,
        "status": "passed" if not violations else "failed",
        "description": entry.description,
        "thresholds": entry.thresholds.__dict__,
        "actual": _actual_threshold_values(audit),
        "violations": violations,
    }


def validate_pipeline_outputs(outputs: dict[str, dict[str, str]], matrix: dict[str, DemoMatrixEntry] | None = None) -> dict[str, Any]:
    matrix = matrix or standard_demo_matrix()
    required_job_ids = [entry.job_id for entry in matrix.values()]
    job_results: dict[str, dict[str, Any]] = {}
    missing_jobs: list[str] = []
    for job_id in required_job_ids:
        audit_value = outputs.get(job_id, {}).get("audit")
        if not audit_value:
            missing_jobs.append(job_id)
            continue
        audit_path = Path(audit_value)
        if not audit_path.exists() or not audit_path.is_file():
            missing_jobs.append(job_id)
            continue
        audit = _read_json(audit_path)
        job_results[job_id] = validate_job_audit(job_id, audit, matrix)
    failed_jobs = [job_id for job_id, result in job_results.items() if result.get("status") == "failed"]
    status = "passed" if not missing_jobs and not failed_jobs else "failed"
    return {
        "demo_matrix_version": DEMO_AUDIT_PIPELINE_VERSION,
        "engine_version": ENGINE_VERSION_TAG,
        "status": status,
        "required_job_ids": required_job_ids,
        "missing_jobs": missing_jobs,
        "failed_jobs": failed_jobs,
        "job_results": job_results,
    }




def _midi_notes_from_voicing(voicing: dict[str, Any]) -> list[int]:
    midi_notes = voicing.get("midi_notes") or []
    if midi_notes:
        return [int(note) for note in midi_notes]
    notes: list[int] = []
    for item in voicing.get("notes") or []:
        if isinstance(item, dict):
            value = item.get("midi_note")
        else:
            value = item
        if value is not None:
            notes.append(int(value))
    return notes

def _selected_voicing(event: dict[str, Any]) -> dict[str, Any]:
    return dict(event.get("voicing") or {})


def _score_details(event: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(_selected_voicing(event).get("metadata") or {})
    score = dict(metadata.get("score_breakdown") or {})
    return dict(score.get("details") or {})


def _event_pattern(event: dict[str, Any]) -> dict[str, Any]:
    return dict(event.get("pattern_event") or {})




def _mean_or_max(values: Iterable[int | float], *, mode: str = "mean") -> float:
    items = [float(v) for v in values]
    if not items:
        return 0.0
    if mode == "max":
        return round(max(items), 6)
    return round(mean(items), 3)


def _anticipation_timing_grid_row(event: dict[str, Any], timing_policy: dict[str, Any]) -> dict[str, Any]:
    pattern = _event_pattern(event)
    pattern_metadata = dict(pattern.get("metadata") or {})
    anticipation = dict(pattern_metadata.get("anticipation") or {})
    realized_notes = list(event.get("realized_notes") or [])
    timing_intent = str(
        anticipation.get("target_timing_intent")
        or pattern_metadata.get("timing_intent")
        or (realized_notes[0].get("timing_intent") if realized_notes and isinstance(realized_notes[0], dict) else "auto")
        or "auto"
    )
    logical_onset = float(pattern.get("onset_beat") or 0.0)
    original_onset = float(anticipation.get("original_onset_beat") or logical_onset)
    performed_lead_in = anticipation.get("performed_lead_in_beats")
    if performed_lead_in is None:
        performed_lead_in = abs(original_onset - logical_onset)
    performed_lead_in = float(performed_lead_in)
    expected_performed = anticipation.get("expected_performed_onset_beat")
    if expected_performed is None:
        expected_performed = original_onset - performed_lead_in
    expected_performed = float(expected_performed)
    actual_performed = performed_beat(logical_onset, timing_intent, timing_policy)
    error = abs(float(actual_performed) - expected_performed)
    return {
        "event_id": pattern.get("event_id"),
        "region_id": pattern.get("region_id"),
        "chord_symbol": pattern.get("chord_symbol"),
        "logical_onset_beat": round(logical_onset, 6),
        "original_onset_beat": round(original_onset, 6),
        "timing_intent": timing_intent,
        "timing_grid": anticipation.get("timing_grid"),
        "expected_upbeat_fraction": anticipation.get("expected_upbeat_fraction"),
        "logical_lead_in_beats": anticipation.get("logical_lead_in_beats", anticipation.get("lead_in_beats")),
        "performed_lead_in_beats": round(performed_lead_in, 6),
        "expected_performed_onset_beat": round(expected_performed, 6),
        "actual_performed_onset_beat": round(float(actual_performed), 6),
        "timing_error_beats": round(error, 9),
        "timing_grid_ok": error <= 1e-6,
    }

def _summarize_piano_events(debug: dict[str, Any]) -> dict[str, Any]:
    events = list(debug.get("piano_musical_audit_events") or [])
    content_families: Counter[str] = Counter()
    dispositions: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    source_kinds: Counter[str] = Counter()
    functional_scopes: Counter[str] = Counter()
    inferred_scopes: Counter[str] = Counter()
    low_guard: Counter[str] = Counter()
    register_guard_violations = 0
    upper_structure_events = 0
    altered_degree_events = 0
    top_notes: list[int] = []
    average_pitches: list[float] = []
    dominant_events = 0
    anticipation_events = 0
    anticipation_tie_expression_events = 0
    selected_event_rows: list[dict[str, Any]] = []
    timing_policy = dict(debug.get("timing_policy") or {})
    anticipation_timing_grid_events = 0
    anticipation_timing_grid_failures = 0
    anticipation_timing_grid_errors: list[float] = []
    anticipation_timing_grid_samples: list[dict[str, Any]] = []

    for event in events:
        voicing = _selected_voicing(event)
        details = _score_details(event)
        pattern = _event_pattern(event)
        pattern_metadata = dict(pattern.get("metadata") or {})
        anticipation = dict(pattern_metadata.get("anticipation") or {})
        if anticipation.get("kind") == "next_beat1_to_previous_tail":
            anticipation_events += 1
            timing_row = _anticipation_timing_grid_row(event, timing_policy)
            anticipation_timing_grid_events += 1
            anticipation_timing_grid_errors.append(float(timing_row.get("timing_error_beats") or 0.0))
            if not timing_row.get("timing_grid_ok", False):
                anticipation_timing_grid_failures += 1
            if len(anticipation_timing_grid_samples) < 24:
                anticipation_timing_grid_samples.append(timing_row)
        expression = dict(event.get("expression") or {})
        expression_metadata = dict(expression.get("metadata") or {})
        if expression_metadata.get("duration_anticipation_tie_applied"):
            anticipation_tie_expression_events += 1
        degrees = [str(degree) for degree in voicing.get("degrees") or []]
        notes = _midi_notes_from_voicing(voicing)
        content_family = str(voicing.get("content_family") or "")
        disposition = str(voicing.get("disposition") or "")
        method = str((voicing.get("metadata") or {}).get("method") or (voicing.get("metadata") or {}).get("projection_method") or "")
        if content_family:
            content_families[content_family] += 1
        if disposition:
            dispositions[disposition] += 1
        if method:
            methods[method] += 1
        if notes:
            top_notes.append(max(notes))
            average_pitches.append(sum(notes) / len(notes))
        if any(degree in ALTERED_DEGREES for degree in degrees):
            altered_degree_events += 1
        if details.get("altered_dominant_source_kind"):
            source_kinds[str(details["altered_dominant_source_kind"])] += 1
        decision = details.get("altered_dominant_policy") or details.get("altered_dominant_decision") or {}
        if isinstance(decision, dict):
            if decision.get("functional_scope"):
                functional_scopes[str(decision["functional_scope"])] += 1
            if decision.get("inferred_functional_scope"):
                inferred_scopes[str(decision["inferred_functional_scope"])] += 1
        for token in ("functional_scope", "inferred_functional_scope"):
            if details.get(token):
                (functional_scopes if token == "functional_scope" else inferred_scopes)[str(details[token])] += 1
        if str(pattern.get("chord_symbol") or "").endswith("7") or "7" in str(pattern.get("chord_symbol") or ""):
            dominant_events += 1
        if details.get("low_register_single_note_ok") is False:
            register_guard_violations += 1
            low_guard["failed"] += 1
        elif "low_register_single_note_ok" in details:
            low_guard["passed"] += 1
        metadata = dict(voicing.get("metadata") or {})
        validity_notes = [str(note).lower() for note in metadata.get("validity_notes", []) or []]
        if (
            any("upper_structure" in note for note in validity_notes)
            or details.get("upper_structure_register_refinement_version")
            or metadata.get("upper_structure_spread_pilot_version")
        ):
            upper_structure_events += 1
        if source_kinds or altered_degree_events:
            pass
        if details.get("altered_dominant_source_kind") or any(degree in ALTERED_DEGREES for degree in degrees):
            selected_event_rows.append(
                {
                    "event_id": pattern.get("event_id"),
                    "region_id": pattern.get("region_id"),
                    "chord_symbol": pattern.get("chord_symbol"),
                    "degrees": degrees,
                    "content_family": content_family,
                    "disposition": disposition,
                    "altered_dominant_source_kind": details.get("altered_dominant_source_kind"),
                    "altered_dominant_intensity_score": details.get("altered_dominant_intensity_score"),
                    "upper_structure_register_score": details.get("upper_structure_register_score"),
                }
            )

    # Avoid duplicate upper-structure counting when both notes and register scores exist.
    upper_structure_events = min(upper_structure_events, len(events))
    return {
        "event_count": len(events),
        "dominant_event_count": dominant_events,
        "content_families": _counter(content_families),
        "dispositions": _counter(dispositions),
        "projection_methods": _counter(methods),
        "altered_dominant_source_kinds": _counter(source_kinds),
        "altered_dominant_functional_scopes": _counter(functional_scopes),
        "altered_dominant_inferred_scopes": _counter(inferred_scopes),
        "altered_degree_events": altered_degree_events,
        "anticipation_events": anticipation_events,
        "anticipation_tie_expression_events": anticipation_tie_expression_events,
        "anticipation_timing_grid_events": anticipation_timing_grid_events,
        "anticipation_timing_grid_failures": anticipation_timing_grid_failures,
        "anticipation_timing_grid_error_max": _mean_or_max(anticipation_timing_grid_errors, mode="max"),
        "anticipation_timing_grid_samples": anticipation_timing_grid_samples,
        "upper_structure_register_refinement_events": upper_structure_events,
        "register_guard_violations": register_guard_violations,
        "low_register_single_note_guard": _counter(low_guard),
        "top_note_max": max(top_notes) if top_notes else None,
        "top_note_average": _mean(top_notes),
        "average_pitch_mean": _mean(average_pitches),
        "selected_altered_or_colored_events_sample": selected_event_rows[:40],
    }


def build_audit_summary(job: DemoAuditJob, result: Any, *, midi_path: Path) -> dict[str, Any]:
    debug = dict(result.debug or {})
    request_summary = {
        "job_id": job.job_id,
        "description": job.description,
        "tags": list(job.tags),
        "leadsheet": job.leadsheet,
        "style": job.style,
        "tempo": job.tempo,
        "choruses": job.choruses,
        "seed": job.seed,
        "ensemble": job.ensemble,
        "voicing_override": _compact_mapping(
            job.voicing_override,
            keys=("enabled", "pattern_mode", "disable_anticipation", "mute_bass", "expression_hint", "harmonic_expansion_enabled", "color_policy_mode"),
        ),
        "voicing_override_metadata_keys": sorted((job.voicing_override.get("metadata") or {}).keys()),
    }
    runtime_summary = _compact_mapping(
        debug,
        keys=(
            "title",
            "style",
            "leadsheet_schema_version",
            "written_bars",
            "performance_choruses",
            "performance_bars",
            "regions",
            "pattern_events",
            "active_pattern_events",
            "suppressed_pattern_events",
            "note_events",
            "note_events_by_track",
            "ensemble_context",
            "timing_policy",
            "midi_render_audit",
            "pipeline",
        ),
    )
    return {
        "demo_audit_pipeline_version": DEMO_AUDIT_PIPELINE_VERSION,
        "engine_version": ENGINE_VERSION_TAG,
        "midi_path": str(midi_path.relative_to(ROOT) if midi_path.is_relative_to(ROOT) else midi_path),
        "request": request_summary,
        "runtime_summary": runtime_summary,
        "piano_musical_audit": debug.get("piano_musical_audit", {}),
        "expression_foundation_audit": debug.get("expression_foundation_audit", {}),
        "bass_foundation_audit": debug.get("bass_foundation_audit", {}),
        "pedal_realization_audit": debug.get("pedal_realization_audit", {}),
        "piano_event_summary": _summarize_piano_events(debug),
    }


def run_job(job: DemoAuditJob, *, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    leadsheet_path = ROOT / "examples" / "leadsheets" / job.leadsheet
    leadsheet = _read_json(leadsheet_path)
    midi_path = output_dir / f"{job.output_stem}.mid"
    audit_path = output_dir / f"{job.output_stem}_audit_summary.json"
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": job.style,
            "tempo": job.tempo,
            "choruses": job.choruses,
            "seed": job.seed,
            "output_path": str(midi_path),
            "ensemble": job.ensemble,
            "voicing_override": job.voicing_override,
        }
    )
    summary = build_audit_summary(job, result, midi_path=midi_path)
    _write_json(audit_path, summary)
    return {"midi": midi_path, "audit": audit_path}


def run_jobs(
    job_ids: list[str],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    validate_matrix: bool = True,
    fail_on_thresholds: bool = False,
) -> dict[str, dict[str, str]]:
    jobs = standard_jobs()
    selected = job_ids or list(jobs)
    outputs: dict[str, dict[str, str]] = {}
    for job_id in selected:
        if job_id not in jobs:
            raise KeyError(f"Unknown demo/audit job: {job_id}. Available: {', '.join(sorted(jobs))}")
        paths = run_job(jobs[job_id], output_dir=output_dir)
        outputs[job_id] = {key: str(path) for key, path in paths.items()}
    validation = validate_pipeline_outputs(outputs) if validate_matrix else {"status": "skipped"}
    manifest_path = output_dir / f"{ENGINE_VERSION_TAG}_demo_audit_pipeline_manifest.json"
    _write_json(
        manifest_path,
        {
            "demo_audit_pipeline_version": DEMO_AUDIT_PIPELINE_VERSION,
            "engine_version": ENGINE_VERSION_TAG,
            "job_ids": selected,
            "outputs": outputs,
            "validation": validation,
        },
    )
    outputs["manifest"] = {"json": str(manifest_path)}
    if fail_on_thresholds and validation.get("status") == "failed":
        raise SystemExit(f"Demo matrix validation failed: {json.dumps(validation, ensure_ascii=False, sort_keys=True)}")
    return outputs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run JamMate V2 consolidated demo + audit jobs.")
    parser.add_argument("--job", action="append", default=[], help="Job id to run. Repeatable. Defaults to all standard jobs.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for MIDI and audit JSON outputs.")
    parser.add_argument("--list", action="store_true", help="List available jobs and exit.")
    parser.add_argument("--list-matrix", action="store_true", help="List demo matrix entries and thresholds, then exit.")
    parser.add_argument("--no-validate", action="store_true", help="Skip demo matrix threshold validation.")
    parser.add_argument("--fail-on-thresholds", action="store_true", help="Exit non-zero when demo matrix thresholds fail.")
    args = parser.parse_args(argv)
    jobs = standard_jobs()
    if args.list:
        for job_id, job in sorted(jobs.items()):
            print(f"{job_id}\t{job.style}\t{job.leadsheet}\t{job.description}")
        return
    if args.list_matrix:
        matrix_rows = {
            key: {
                "job_id": entry.job_id,
                "description": entry.description,
                "thresholds": entry.thresholds.__dict__,
            }
            for key, entry in sorted(standard_demo_matrix().items())
        }
        print(json.dumps(matrix_rows, indent=2, ensure_ascii=False, sort_keys=True))
        return
    outputs = run_jobs(
        list(args.job or []),
        output_dir=Path(args.output_dir),
        validate_matrix=not args.no_validate,
        fail_on_thresholds=args.fail_on_thresholds,
    )
    print(json.dumps(outputs, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
