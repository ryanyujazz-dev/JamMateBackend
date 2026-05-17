from __future__ import annotations

from ..selection.candidate import VoicingCandidate
from jammate_engine.core.harmony.chord_parser import parse_chord
from ..policy import VoicingPolicy, altered_dominant_source_weight_bias


SOURCE_BALANCE_CONTRACT_VERSION = "v2_1_43"
ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION = "v2_2_88"


def source_balance_key(candidate: VoicingCandidate) -> str:
    """Return the functional source key used by style-level source balance.

    The key is intentionally functional-role based.  Concrete accidentals such
    as b3/b5/b9/#11 are resolved by core harmony before candidate generation;
    source balance only talks in roles such as root_third_fifth_root or
    third_seventh_ninth.
    """

    if int(candidate.density or 0) == 3:
        return _three_note_source_balance_key(candidate)
    if int(candidate.density or 0) == 4:
        return _four_note_source_balance_key(candidate)
    return ""


def source_gate_mode(candidate: VoicingCandidate) -> str:
    """Return the source-balance gate bucket for a candidate.

    3-note and 4-note closed source work share the same four conceptual gates:
    chord_symbol_only, harmonic_expansion, explicit_chart_color, and
    explicit_chart_color_plus_harmonic_expansion.  The exact metadata markers
    differ by density, so this adapter keeps scorer.py small and auditable.
    """

    notes = _validity_notes(candidate)
    has_explicit = any(
        marker in notes
        for marker in (
            "explicit_chord_symbol_color_used",
            "explicit_chord_symbol_sixth_used",
            "explicit_chord_symbol_suspension_used",
        )
    ) or any(marker.startswith("three_note_source_component_explicit_") for marker in notes)
    has_expansion = any(
        marker in notes
        for marker in (
            "harmonic_expansion_color_used",
            "rootless_ab_harmonic_expansion_enabled",
        )
    ) or any(marker.startswith("triad_harmonic_expansion_") for marker in notes)

    if "four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" in notes:
        return "explicit_chart_color_plus_harmonic_expansion"
    if has_explicit and has_expansion:
        return "explicit_chart_color_plus_harmonic_expansion"
    if "four_note_color_gate_open_explicit_chord_symbol_color" in notes or has_explicit:
        return "explicit_chart_color"
    if "four_note_color_gate_open_harmonic_expansion" in notes or has_expansion:
        return "harmonic_expansion"
    if "four_note_color_gate_closed" in notes or any(note.startswith("basic_4note_conservative") for note in notes):
        return "chord_symbol_only"
    if int(candidate.density or 0) in {3, 4}:
        return "chord_symbol_only"
    return "unspecified"


def score_source_balance(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Apply style-level source weights to functional 3-note/4-note sources."""

    if int(candidate.density or 0) not in {3, 4}:
        return 0.0
    global_weights = dict(getattr(policy, "source_family_weights", None) or {})
    by_gate = dict(getattr(policy, "source_family_weights_by_gate", None) or {})
    gate_mode = source_gate_mode(candidate)
    gate_weights = dict(by_gate.get(gate_mode, {}) or {})
    style_score = _score_from_weight_map(candidate, global_weights) + _score_from_weight_map(candidate, gate_weights)
    return style_score + score_altered_dominant_intensity_balance(candidate, policy)


def score_altered_dominant_intensity_balance(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Return v2_2_88 altered-dominant source bias for a selected source.

    This function deliberately reads existing source metadata instead of adding
    a new source family. It lets the global altered-dominant policy convert
    ``light / medium / high / full`` into a selector score for rooted color,
    rootless A/B, or Upper Structure candidates.
    """

    source_kind = altered_dominant_source_kind(candidate)
    if not source_kind:
        return 0.0
    symbol = str(dict(candidate.metadata or {}).get("symbol") or "")
    if not symbol:
        return 0.0
    try:
        chord = parse_chord(symbol)
    except Exception:
        return 0.0
    return altered_dominant_source_weight_bias(policy, chord, source_kind)


def altered_dominant_source_kind(candidate: VoicingCandidate) -> str:
    """Return the altered-source family represented by candidate metadata."""

    metadata = dict(candidate.metadata or {})
    notes = set(_validity_notes(candidate))
    notes.update(str(item) for item in metadata.get("source_metadata", []) or [])
    notes.update(str(item) for item in metadata.get("upper_source_metadata", []) or [])
    if "rooted_color_4note_altered_dominant_rooted_source" in notes:
        return "rooted_color"
    if "rootless_ab_altered_dominant_rootless_source" in notes or "rootless_ab_content_type_altered_dominant_rootless" in notes:
        return "rootless_ab"
    if "upper_structure_source_family" in notes and "upper_structure_profile_kind_altered" in notes:
        return "upper_structure"
    return ""


def _score_from_weight_map(candidate: VoicingCandidate, weights: dict[str, float]) -> float:
    if not weights:
        return 0.0
    key = source_balance_key(candidate)
    content_family = getattr(candidate.content_family, "value", str(candidate.content_family or ""))
    metadata = dict(candidate.metadata or {})
    candidates = [
        key,
        key.replace("root_", "", 1) if key.startswith("root_") else key,
        str(metadata.get("rootless_ab_content_type") or ""),
        str(metadata.get("rooted_color_4note_source_family") or ""),
        str(metadata.get("basic_4note_source_family") or ""),
        str(metadata.get("triad_4note_source_family") or ""),
        content_family,
    ]
    for item in candidates:
        if item in weights:
            return float(weights[item])
    return 0.0


def _three_note_source_balance_key(candidate: VoicingCandidate) -> str:
    notes = _validity_notes(candidate)
    marker = next((note for note in notes if note.startswith("three_note_functional_source_type_")), "")
    if marker:
        return marker.removeprefix("three_note_functional_source_type_")
    marker = next((note for note in notes if note.startswith("three_note_source_role_order_")), "")
    if marker:
        return marker.removeprefix("three_note_source_role_order_")
    return ""


def _four_note_source_balance_key(candidate: VoicingCandidate) -> str:
    metadata = dict(candidate.metadata or {})
    key = str(
        metadata.get("triad_4note_functional_content_type")
        or metadata.get("triad_4note_content_type")
        or metadata.get("rootless_ab_functional_source_type")
        or metadata.get("rootless_ab_content_type")
        or metadata.get("rooted_color_4note_functional_content_type")
        or metadata.get("rooted_color_4note_source_family")
        or metadata.get("basic_4note_functional_content_type")
        or metadata.get("basic_4note_source_family")
        or ""
    )
    for prefix in (
        "triad_4note_functional_content_type_",
        "rootless_ab_functional_source_type_",
        "rooted_color_4note_functional_content_type_",
        "basic_4note_functional_content_type_",
    ):
        key = key.removeprefix(prefix)
    return key


def _validity_notes(candidate: VoicingCandidate) -> tuple[str, ...]:
    metadata = dict(candidate.metadata or {})
    recipe = dict(metadata.get("content_recipe") or {})
    return tuple(str(note) for note in recipe.get("validity_notes", []) or [])
