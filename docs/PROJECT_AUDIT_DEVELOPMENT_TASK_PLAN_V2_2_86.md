# v2_2_88 — Project Audit / Documentation Plan Sync

## Scope

This is a documentation, harness, and roadmap synchronization pass. Runtime generation logic is unchanged. It does **not** change runtime generation logic, voicing selection behavior, altered dominant authorization behavior, expression, pattern planning, MIDI rendering, or style defaults.

The goal is to make the repository entry points match the true v2_2_85 code state before starting the next musical tuning pass.

## Audit result

### Verified current implementation

- Package/runtime version is advanced to `v2_2_88`.
- v2_2_85 altered dominant functional scope implementation is present and stable.
- `resolve_altered_dominant_policy()` is the single gate for unnotated altered dominant color.
- Rooted color, rootless A/B, and Upper Structure all consume the same altered dominant policy decision.
- LLM-selected altered dominant region metadata already supports region, section, phrase, chord symbol, chorus index, performance bar, written bar, and source bar selection.
- `AlteredDominantIntensity` exists as policy metadata, but it is not yet calibrated into final source-selection probability or style-specific source weights.
- SPREAD Upper Structure remains a source-family / grouped-voicing pilot path; it does not introduce a parallel projection system.
- The project still follows the V2 boundary: style pattern libraries are pitchless and style-owned; voicing, expression, harmony, timeline, and realization remain core/domain layers.

### Documentation gaps fixed in this pass

- Updated project version surfaces: `VERSION`, `pyproject.toml`, `src/jammate_engine/api/version.py`, `README.md`, and `agent.md`.
- Recorded the canonical validation command as `PYTHONPATH=src python -m pytest -q`, because this source-layout package is not always installed in ad-hoc local runs.
- Added this audit / development task plan as the current roadmap entry.
- Marked the next work as actual musical tuning rather than more infrastructure expansion.

## Canonical validation commands

Run from repository root:

```bash
python -m compileall src
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
```

For docs-only passes, a current standard-tune demo should still be exported when practical, but the delivery must explicitly say runtime generation logic is unchanged.

## Current architecture assessment

### Healthy areas

- The altered dominant policy gate is correctly located in `core/voicing/policy.py`, not duplicated in each source family.
- Functional harmonic context is reused from `core/harmony/harmonic_context.py`; no new progression recognizer was introduced.
- Voicing source families remain separated from disposition/projection methods.
- SPREAD lower/upper grouping is still expressed in core voicing/disposition concepts instead of hardcoded piano LH/RH language.
- Test coverage is broad enough that version/document sync mistakes are caught quickly.

### Main open risks

- `AlteredDominantIntensity` is currently a permission label more than a true probability/weight control.
- Altered source families can be authorized correctly but still need calibrated final selection weights by style, scope, and texture family.
- Upper Structure can make the top register feel sharper than the rest of the Ballad texture if the next pass does not constrain source choice, upper-density, and register target together.
- Demo/audit scripts are useful but still scattered; they need a small standardized comparison workflow before v2_3_x.

## Next development path

### v2_2_88 — Altered Dominant Intensity / Source Weight Calibration

Goal: turn altered intensity from metadata into actual source probability and style-weight behavior.

Tasks:

- Map `light / medium / high / full` to source-family weights.
- Separate weights for rooted color, rootless A/B, and Upper Structure altered sources.
- Add scope-aware defaults: resolving V7 can be stronger than secondary; backdoor can be color-safe; static/blues dominant should stay restrained unless explicitly requested.
- Add style defaults:
  - Medium Swing: moderate altered on functional cadences.
  - Jazz Ballad: warmer, more selective altered; avoid constant bright top tension.
  - Bossa Nova: conservative altered unless chart/LLM explicitly asks.
- Output Misty / Blue Bossa / Medium Swing standard demos plus audit JSON.

### v2_2_88 — LLM Semantic Control Granularity

Goal: make LLM semantic overrides practical without breaking local music policy.

Tasks:

- Support local overrides for intensity, scope, source-family preference, and target bars/regions.
- Keep default functional policy active when no LLM override is present.
- Add audit fields showing whether altered came from chart symbol, functional policy, or LLM-selected region.

### v2_2_89 — Minor V→i / Turnaround Functional Audit

Goal: verify altered behavior in minor cadence and turnaround situations.

Tasks:

- Audit V7→i, iiø7→V7→i, I–VI–ii–V, and dominant chain cases.
- Ensure minor V altered color does not get confused with generic static dominant behavior.
- Add targeted fixtures before broad style retuning.

### v2_2_90 — Upper Structure Register / Sharpness Guard

Goal: reduce尖锐感 without deleting Upper Structure as a color option.

Tasks:

- Add or tune upper-register ceiling/target penalties for Upper Structure sources.
- Consider policy for highest-note density and repeated bright altered tensions.
- Preserve the existing low-register density guard: below a low threshold, allow at most one note unless the user explicitly asks for thick low texture.

### v2_3_3 — Demo / Audit Comparison Pipeline

Goal: standardize generated listening checks.

Tasks:

- One command or small script for selected standard-tune demo + audit export.
- Support unexpanded / expanded / altered-intensity comparison sets.
- Keep all demos three choruses unless a test fixture needs a shorter loop.

## Acceptance criteria for v2_2_88

- Runtime generation logic is unchanged.
- `VERSION`, API version, pyproject version, README, agent harness, and docs roadmap agree on `v2_2_88`.
- Full compile and pytest pass with `PYTHONPATH=src`.
- A baseline standard-tune demo is exported under `demos/` with a `v2_2_88` filename when practical.
- Next recommended task is `v2_2_88 — Altered Dominant Intensity / Source Weight Calibration`.
