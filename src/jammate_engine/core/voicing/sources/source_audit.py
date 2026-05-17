from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..selection.candidate_generator import generate_candidates
from ..policy import ContentFamily, VoicingPolicy

FOUR_NOTE_SOURCE_BALANCE_AUDIT_VERSION = "v2_1_37"


@dataclass(frozen=True)
class FourNoteSourceAuditRow:
    """Observational row for one symbol/policy candidate-pool audit.

    This module is deliberately read-only.  It does not select voicings and does
    not modify source weights.  It exists so 4-note source balance work can be
    based on visible candidate-pool data rather than guesses.
    """

    symbol: str
    policy_label: str
    content_family: str
    source_family: str
    functional_source_type: str
    legacy_alias: str
    gate_reason: str
    degree_order: tuple[str, ...]
    degree_role_order: str
    candidate_count: int
    source_balance_weight: float
    source_balance_gate_mode: str
    chart_color_fidelity: str
    allowed_color_set: str
    root_included: bool
    harmonic_expansion_enabled: bool
    color_policy_mode: str

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "policy_label": self.policy_label,
            "content_family": self.content_family,
            "source_family": self.source_family,
            "functional_source_type": self.functional_source_type,
            "legacy_alias": self.legacy_alias,
            "gate_reason": self.gate_reason,
            "degree_order": list(self.degree_order),
            "degree_role_order": self.degree_role_order,
            "candidate_count": self.candidate_count,
            "source_balance_weight": self.source_balance_weight,
            "source_balance_gate_mode": self.source_balance_gate_mode,
            "chart_color_fidelity": self.chart_color_fidelity,
            "allowed_color_set": self.allowed_color_set,
            "root_included": self.root_included,
            "harmonic_expansion_enabled": self.harmonic_expansion_enabled,
            "color_policy_mode": self.color_policy_mode,
        }


@dataclass(frozen=True)
class FourNoteSourceBalanceAudit:
    contract_version: str
    rows: tuple[FourNoteSourceAuditRow, ...]
    summary: dict[str, Any]

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "summary": dict(self.summary),
            "rows": [row.to_debug_dict() for row in self.rows],
        }


def build_four_note_source_balance_audit(
    symbols: Iterable[str],
    policies: Mapping[str, VoicingPolicy],
) -> FourNoteSourceBalanceAudit:
    """Summarize 4-note source candidates by symbol and policy.

    v2_1_26 applies source-level balance decisions after exposing what actually enters the
    candidate pool under chord-symbol-only, explicit-chart-color, and harmonic
    expansion contexts.  It counts candidates after gating and candidate
    generation, but before and during weighted selection.
    """

    rows: list[FourNoteSourceAuditRow] = []
    for policy_label, policy in policies.items():
        for symbol in symbols:
            grouped: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(lambda: {"count": 0})
            for candidate in generate_candidates(symbol, policy):
                if int(candidate.density or 0) != 4:
                    continue
                metadata = dict(candidate.metadata or {})
                source_family = _candidate_source_family(metadata)
                functional_source_type = _candidate_functional_source_type(metadata, source_family)
                legacy_alias = _candidate_legacy_alias(metadata)
                gate_reason = _candidate_gate_reason(metadata)
                degree_order = tuple(str(degree) for degree in candidate.degrees)
                degree_role_order = _candidate_degree_role_order(metadata)
                source_balance_gate_mode = _candidate_source_balance_gate_mode(metadata)
                source_balance_weight = _candidate_source_balance_weight(
                    policy=policy,
                    source_family=source_family,
                    functional_source_type=functional_source_type,
                    content_family=candidate.content_family.value if candidate.content_family else "unknown",
                    legacy_alias=legacy_alias,
                    gate_mode=source_balance_gate_mode,
                )
                chart_color_fidelity = _candidate_chart_color_fidelity(metadata)
                allowed_color_set = _candidate_allowed_color_set(metadata)
                key = (
                    symbol,
                    policy_label,
                    candidate.content_family.value if candidate.content_family else "unknown",
                    source_family,
                    functional_source_type,
                    legacy_alias,
                    gate_reason,
                    degree_order,
                    degree_role_order,
                    float(source_balance_weight),
                    str(source_balance_gate_mode),
                    str(chart_color_fidelity),
                    str(allowed_color_set),
                    bool(candidate.root_included),
                    bool(policy.harmonic_expansion_enabled),
                    getattr(policy.color_policy_mode, "value", str(policy.color_policy_mode)),
                )
                grouped[key]["count"] += 1
            for key, payload in grouped.items():
                (
                    row_symbol,
                    row_policy_label,
                    content_family,
                    source_family,
                    functional_source_type,
                    legacy_alias,
                    gate_reason,
                    degree_order,
                    degree_role_order,
                    source_balance_weight,
                    source_balance_gate_mode,
                    chart_color_fidelity,
                    allowed_color_set,
                    root_included,
                    harmonic_expansion_enabled,
                    color_policy_mode,
                ) = key
                rows.append(
                    FourNoteSourceAuditRow(
                        symbol=str(row_symbol),
                        policy_label=str(row_policy_label),
                        content_family=str(content_family),
                        source_family=str(source_family),
                        functional_source_type=str(functional_source_type),
                        legacy_alias=str(legacy_alias),
                        gate_reason=str(gate_reason),
                        degree_order=tuple(str(degree) for degree in degree_order),
                        degree_role_order=str(degree_role_order),
                        candidate_count=int(payload["count"]),
                        source_balance_weight=float(source_balance_weight),
                        source_balance_gate_mode=str(source_balance_gate_mode),
                        chart_color_fidelity=str(chart_color_fidelity),
                        allowed_color_set=str(allowed_color_set),
                        root_included=bool(root_included),
                        harmonic_expansion_enabled=bool(harmonic_expansion_enabled),
                        color_policy_mode=str(color_policy_mode),
                    )
                )

    rows.sort(key=lambda row: (row.policy_label, row.symbol, row.content_family, row.source_family, row.degree_order))
    summary = _summarize_rows(rows)
    return FourNoteSourceBalanceAudit(
        contract_version=FOUR_NOTE_SOURCE_BALANCE_AUDIT_VERSION,
        rows=tuple(rows),
        summary=summary,
    )


def format_four_note_source_balance_audit_report(audit: FourNoteSourceBalanceAudit) -> str:
    """Return a compact Markdown report for source-balance preparation."""

    summary = audit.summary
    lines: list[str] = []
    lines.append("# 4-Note Source Balance Decision Audit")
    lines.append("")
    lines.append(f"- Contract version: `{audit.contract_version}`")
    lines.append(f"- Rows: `{len(audit.rows)}`")
    lines.append(f"- Total 4-note candidates: `{summary.get('total_candidates')}`")
    lines.append(f"- Policies: `{summary.get('policies')}`")
    lines.append(f"- Symbols: `{summary.get('symbols')}`")
    lines.append("")
    lines.append("## Counters")
    lines.append("")
    lines.append(f"- Content families: `{summary.get('content_families')}`")
    lines.append(f"- Source families: `{summary.get('source_families')}`")
    lines.append(f"- Functional source types: `{summary.get('functional_source_types')}`")
    lines.append(f"- Gate reasons: `{summary.get('gate_reasons')}`")
    lines.append(f"- Root included: `{summary.get('root_included')}`")
    lines.append(f"- Source balance weights: `{summary.get('source_balance_weights')}`")
    lines.append(f"- Source balance gate modes: `{summary.get('source_balance_gate_modes')}`")
    lines.append(f"- Chart color fidelity: `{summary.get('chart_color_fidelity')}`")
    lines.append("")
    lines.append("## Rows")
    lines.append("")
    lines.append("| Policy | Symbol | Family | Source family | Functional source | Alias | Gate | Balance mode | Fidelity | Allowed colors | Degrees | Role order | Root | Balance | Count |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---:|")
    for row in audit.rows:
        lines.append(
            "| `{policy}` | `{symbol}` | `{family}` | `{source}` | `{functional}` | `{alias}` | `{gate}` | `{mode}` | `{fidelity}` | `{allowed}` | `{degrees}` | `{roles}` | `{root}` | {balance:.2f} | {count} |".format(
                policy=row.policy_label,
                symbol=row.symbol,
                family=row.content_family,
                source=row.source_family,
                functional=row.functional_source_type,
                alias=row.legacy_alias,
                gate=row.gate_reason,
                mode=row.source_balance_gate_mode,
                fidelity=row.chart_color_fidelity,
                allowed=row.allowed_color_set,
                degrees=" ".join(row.degree_order),
                roles=row.degree_role_order,
                root="yes" if row.root_included else "no",
                balance=float(row.source_balance_weight),
                count=row.candidate_count,
            )
        )
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- This report is observational for candidate counts before weighted selection, and also shows the v2_1_36 four-mode-aware style-level source-balance and chart-color-fidelity scores that will be applied during weighted selection; read it as before and during weighted selection.")
    lines.append("- Functional source names such as `root_third_fifth_seventh` or `third_fifth_seventh_ninth` are source-role contracts; Harmony resolves concrete accidentals.")
    lines.append("- Gate remains separate from balance: a source must first be legal under chord-symbol-only, explicit chart color, or harmonic expansion before any balance weight applies.")
    return "\n".join(lines)


def _summarize_rows(rows: list[FourNoteSourceAuditRow]) -> dict[str, Any]:
    content = Counter()
    source = Counter()
    functional = Counter()
    gates = Counter()
    root = Counter()
    balance = Counter()
    fidelity = Counter()
    gate_modes = Counter()
    policies = set()
    symbols = set()
    total = 0
    for row in rows:
        total += row.candidate_count
        content.update({row.content_family: row.candidate_count})
        source.update({row.source_family: row.candidate_count})
        functional.update({row.functional_source_type: row.candidate_count})
        gates.update({row.gate_reason: row.candidate_count})
        root.update({"root_included" if row.root_included else "rootless": row.candidate_count})
        balance.update({f"{row.source_balance_gate_mode}:{row.source_family}:{row.source_balance_weight:+.2f}": row.candidate_count})
        gate_modes.update({row.source_balance_gate_mode: row.candidate_count})
        fidelity.update({row.chart_color_fidelity: row.candidate_count})
        policies.add(row.policy_label)
        symbols.add(row.symbol)
    return {
        "total_candidates": total,
        "policies": sorted(policies),
        "symbols": sorted(symbols),
        "content_families": dict(content),
        "source_families": dict(source),
        "functional_source_types": dict(functional),
        "gate_reasons": dict(gates),
        "root_included": dict(root),
        "source_balance_weights": dict(balance),
        "source_balance_gate_modes": dict(gate_modes),
        "chart_color_fidelity": dict(fidelity),
    }


def _candidate_source_balance_gate_mode(metadata: Mapping[str, Any]) -> str:
    validity_notes = _candidate_validity_notes(metadata)
    if "four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" in validity_notes:
        return "explicit_chart_color_plus_harmonic_expansion"
    if "four_note_color_gate_open_explicit_chord_symbol_color" in validity_notes:
        return "explicit_chart_color"
    if "four_note_color_gate_open_harmonic_expansion" in validity_notes:
        return "harmonic_expansion"
    if "four_note_color_gate_closed" in validity_notes:
        return "chord_symbol_only"
    if any(note.startswith("basic_4note_conservative") for note in validity_notes):
        return "chord_symbol_only"
    return "unspecified"


def _candidate_source_balance_weight(
    *,
    policy: VoicingPolicy,
    source_family: str,
    functional_source_type: str,
    content_family: str,
    legacy_alias: str,
    gate_mode: str,
) -> float:
    global_weights = dict(getattr(policy, "source_family_weights", None) or {})
    by_gate = dict(getattr(policy, "source_family_weights_by_gate", None) or {})
    gate_weights = dict(by_gate.get(gate_mode, {}) or {})
    return _weight_from_map(global_weights, source_family, functional_source_type, content_family, legacy_alias) + _weight_from_map(gate_weights, source_family, functional_source_type, content_family, legacy_alias)


def _weight_from_map(
    weights: Mapping[str, float],
    source_family: str,
    functional_source_type: str,
    content_family: str,
    legacy_alias: str,
) -> float:
    for key in (functional_source_type, source_family, legacy_alias, content_family):
        if key in weights:
            return float(weights[key])
    return 0.0



def _candidate_chart_color_fidelity(metadata: Mapping[str, Any]) -> str:
    validity_notes = _candidate_validity_notes(metadata)
    contains = "chart_color_fidelity_contains_explicit_color" in validity_notes
    omits = "chart_color_fidelity_omits_explicit_color" in validity_notes
    if contains and omits:
        return "contains_some_and_omits_some_explicit_chart_color"
    if contains:
        return "contains_explicit_chart_color"
    if omits:
        return "omits_explicit_chart_color"
    return "not_applicable"


def _candidate_allowed_color_set(metadata: Mapping[str, Any]) -> str:
    validity_notes = _candidate_validity_notes(metadata)
    for note in validity_notes:
        if note.startswith("four_note_allowed_color_set_") and note != "four_note_allowed_color_set_contract_v2_1_27":
            return note.removeprefix("four_note_allowed_color_set_")
    return "none"

def _candidate_source_family(metadata: Mapping[str, Any]) -> str:
    validity_notes = _candidate_validity_notes(metadata)
    if "rooted_color_4note_legacy_fallback" in validity_notes:
        return "rooted_color_legacy_fallback"
    return str(
        metadata.get("basic_4note_source_family")
        or metadata.get("rooted_color_4note_source_family")
        or metadata.get("rootless_ab_functional_source_type")
        or metadata.get("rootless_ab_content_type")
        or "unknown"
    )


def _candidate_functional_source_type(metadata: Mapping[str, Any], source_family: str) -> str:
    if source_family == "rooted_color_legacy_fallback":
        return "rooted_color_legacy_fallback"
    return str(
        metadata.get("basic_4note_functional_content_type")
        or metadata.get("rooted_color_4note_functional_content_type")
        or metadata.get("rootless_ab_functional_source_type")
        or source_family
    )


def _candidate_legacy_alias(metadata: Mapping[str, Any]) -> str:
    return str(
        metadata.get("basic_4note_legacy_source_family_alias")
        or metadata.get("rooted_color_4note_legacy_source_family_alias")
        or metadata.get("rootless_ab_content_type")
        or ""
    )


def _candidate_gate_reason(metadata: Mapping[str, Any]) -> str:
    validity_notes = _candidate_validity_notes(metadata)
    for prefix in (
        "four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion",
        "four_note_color_gate_open_explicit_chord_symbol_color",
        "four_note_color_gate_open_harmonic_expansion",
        "four_note_color_gate_closed",
    ):
        if prefix in validity_notes:
            return prefix
    if any(note.startswith("basic_4note_conservative") for note in validity_notes):
        return "basic_4note_conservative_chord_symbol_material"
    if "rooted_color_4note_legacy_fallback" in validity_notes:
        return "rooted_color_4note_legacy_fallback"
    return "unknown"


def _candidate_validity_notes(metadata: Mapping[str, Any]) -> list[str]:
    content_recipe = dict(metadata.get("content_recipe") or {})
    return [str(note) for note in content_recipe.get("validity_notes") or []]


def _candidate_degree_role_order(metadata: Mapping[str, Any]) -> str:
    return str(
        metadata.get("basic_4note_degree_role_order")
        or metadata.get("rooted_color_4note_degree_role_order")
        or metadata.get("rootless_ab_degree_role_order")
        or "unknown"
    )
