# v2_2_88 — Altered Dominant Intensity / Source Weight Calibration

## Goal

`v2_2_85` made altered dominant authorization functional: resolving V7, secondary dominant, static/blues dominant, backdoor dominant, explicit chord-symbol alteration, and LLM-selected altered dominant region control now pass through one shared policy gate.

`v2_2_88` keeps that gate intact and adds the missing selector layer: once a chord is legally authorized for altered material, `light / medium / high / full` now changes how strongly altered source families compete.

The calibrated source kinds are:

- `rooted_color`
- `rootless_ab`
- `upper_structure`

This remains source-weight tuning. It is not a new progression recognizer, not a new voicing projection system, and not a replacement for harmonic expansion or LLM semantic control.

## Runtime owner files

- `src/jammate_engine/core/voicing/policy.py`
  - Owns `ALTERED_DOMINANT_POLICY_VERSION = "v2_2_88"`.
  - Resolves `AlteredDominantPolicyDecision.source_weight_biases`.
  - Exposes `altered_dominant_source_weight_bias(policy, chord, source_kind)`.

- `src/jammate_engine/core/voicing/sources/source_balance.py`
  - Keeps the historical `SOURCE_BALANCE_CONTRACT_VERSION = "v2_1_43"`.
  - Adds `ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION = "v2_2_88"`.
  - Detects altered source family from existing candidate metadata.
  - Adds intensity bias into the existing source-balance score.

- `src/jammate_engine/core/voicing/selection/scorer.py`
  - Candidate score metadata now includes `altered_dominant_intensity_score` and `altered_dominant_source_kind`.

- `src/jammate_engine/core/voicing/sources/content_planner.py`
  - Rooted color and rootless A/B altered recipes now annotate the chosen intensity and source-weight bias.

- `src/jammate_engine/core/voicing/sources/upper_structure.py`
  - Upper Structure remains source-only and reuses existing projection resources.
  - Dominant Upper Structure source mix now depends on intensity.

## Default intensity curve

| Intensity | rooted_color | rootless_ab | upper_structure | Musical meaning |
|---|---:|---:|---:|---|
| `off` | 0.00 | 0.00 | 0.00 | no altered source bias |
| `light` | +0.04 | -0.08 | -0.12 | legal altered is possible but secondary |
| `medium` | +0.10 | +0.02 | +0.00 | rooted altered becomes audible; rootless/US remain occasional |
| `high` | +0.16 | +0.10 | +0.08 | normal jazz altered-dominant setting |
| `full` | +0.24 | +0.20 | +0.18 | strongly favors legal altered pools |

Explicit altered symbols such as `G7alt`, `G7b9`, `G7#9`, and `G7b13` are chart fidelity. They receive at least medium-level bias even when global intensity is light.

LLM-selected regions receive a small audible boost. Static/blues and backdoor altered color are slightly damped unless the chart explicitly asks for alteration or the LLM/policy overrides the source weights.

## Style defaults

Style policies may override the default curve with `metadata["altered_dominant_source_weight_biases_by_intensity"]`.

Current defaults:

- Medium Swing
  - Default altered intent: stronger jazz altered/rootless vocabulary.
  - Default profile leans toward `high`-style rooted/rootless/upper bias.

- Jazz Ballad
  - Default altered intent: warm rooted color with some upper structure color.
  - Rooted and upper color are favored more than Bossa; rootless remains available but less dominant than Medium Swing.

- Bossa Nova
  - Default altered intent: light and conservative.
  - `rootless_ab` and `upper_structure` altered sources are damped unless explicitly requested.

## Upper Structure behavior

Upper Structure source planning remains separate from projection:

- 3-note Upper Structure continues to reuse existing closed/inversion capability.
- 4-note Upper Structure continues to reuse existing closed/inversion/DROP2/DROP3 capability.
- v2_2_88 only changes the legal source mix:
  - `light`: safe source first, plus a small altered option.
  - `medium`: safe source plus a larger altered option set.
  - `high`: altered sources first, safe source retained.
  - `full`: altered sources only when authorized.

## Policy metadata examples

```python
metadata = {
    "harmonic_expansion_enabled": True,
    "color_policy_mode": "style_safe_extensions",
    "previous_chord_symbol": "Dm7",
    "next_chord_symbol": "Cmaj7",
    "home_key": "C",
    "altered_dominant_policy": {
        "enabled": True,
        "intensity": "high",
        "scopes": ["resolving_v7", "secondary_dominants"],
    },
}
```

Optional source-weight override:

```python
metadata = {
    "altered_dominant_source_weight_biases": {
        "rooted_color": 0.18,
        "rootless_ab": 0.06,
        "upper_structure": 0.12,
    },
}
```

Optional per-intensity override:

```python
metadata = {
    "altered_dominant_source_weight_biases_by_intensity": {
        "light": {"rooted_color": 0.02, "rootless_ab": -0.12, "upper_structure": -0.16},
        "high": {"rooted_color": 0.10, "rootless_ab": 0.02, "upper_structure": -0.02},
    },
}
```

## Validation commands

```bash
python -m compileall src
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
```

Targeted tests:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_2_88_altered_dominant_intensity_source_weight.py \
  tests/test_v2_2_85_altered_dominant_functional_scope.py \
  tests/test_v2_2_84_upper_structure_policy_gate.py \
  tests/test_v2_1_43_closed_source_weight_and_voicing_cleanup.py
```

## Demo / audit expectation

Every delivery should include a standard-tune listening demo. For this pass, use the existing Misty jazz ballad Upper Structure / altered dominant demo path and export three choruses plus audit JSON.

Audit should include:

- altered dominant functional scope
- intensity
- source family: `rooted_color`, `rootless_ab`, `upper_structure`
- source-weight bias values
- Upper Structure safe-vs-altered source mix

## Acceptance criteria

- `VERSION`, API version, pyproject, README, `agent.md`, and task docs agree on `v2_2_88`.
- All altered source families read one shared altered-dominant policy decision.
- `light / medium / high / full` affects selector/audit behavior, not just debug naming.
- Existing v2_2_85 functional-scope behavior remains stable.
- `PYTHONPATH=src python -m pytest -q` passes.

## Recommended next task

`v2_2_88 — Minor V→i / Turnaround Altered Coverage Audit`

Focus on minor cadences, turnaround dominants, and style-specific listening checks before expanding the altered system further.
