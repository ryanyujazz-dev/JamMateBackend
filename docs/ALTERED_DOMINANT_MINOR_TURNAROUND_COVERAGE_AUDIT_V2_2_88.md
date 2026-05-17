# v2_2_88 — Minor V→i / Turnaround Altered Coverage Audit

## Goal

This pass verifies that the existing altered-dominant policy chain covers minor-key and turnaround realities without creating a new progression recognizer or moving style logic into core voicing.

The target cases are:

- home-minor `Bm7b5 → E7 → Am` / `Bm7b5 → E7 → Am6`: the E7 is a resolving V7 when the home key is A minor;
- local-minor `Bm7b5 → E7 → Am` inside C major: the E7 is a secondary/local minor dominant, not the global resolving V7 of C;
- turnaround `Cmaj7 → A7 → Dm7 → G7 → Cmaj7`: A7 is a secondary dominant and G7 is the resolving V7;
- explicit altered symbols such as `E7b9`: chart fidelity remains authorized, while audit metadata preserves the inferred motion scope underneath the explicit-symbol gate.

## Architecture decision

No new altered-dominant subsystem is introduced.

The pass keeps the existing chain:

```text
ChordRegion metadata
→ HarmonicContext / FunctionalMotion
→ resolve_altered_dominant_policy()
→ rooted_color / rootless A-B / Upper Structure source planning
→ candidate scoring / audit notes
```

The only policy-contract refinement is that `AlteredDominantPolicyDecision` now exposes `inferred_functional_scope` in addition to `functional_scope`.

This matters because explicit chart alterations have to keep `functional_scope=explicit_chord_symbol_altered` for chart-fidelity reasons, but audit still needs to know whether the underlying motion was `resolving_v7`, `secondary_dominant`, `backdoor_dominant`, etc.

## Expected classifications

| Context | Home key | Current dominant | Next chord | Expected audit classification |
|---|---:|---|---|---|
| `Bm7b5 → E7 → Am6` | A minor | E7 | Am6 | `resolving_v7` |
| `Bm7b5 → E7 → Am7` | C | E7 | Am7 | `secondary_dominant` |
| `Cmaj7 → A7 → Dm7` | C | A7 | Dm7 | `secondary_dominant` |
| `Dm7 → G7 → Cmaj7` | C | G7 | Cmaj7 | `resolving_v7` |
| `Bm7b5 → E7b9 → Am6` | A minor | E7b9 | Am6 | `functional_scope=explicit_chord_symbol_altered`, `inferred_functional_scope=resolving_v7` |

## Source coverage

For authorized minor resolving V7, all existing altered source families remain eligible through the same gate:

- `rooted_color`
- `rootless_ab`
- `upper_structure`

The new audit notes include:

- `altered_dominant_functional_scope_*`
- `altered_dominant_inferred_functional_scope_*`
- `altered_dominant_authorization_reason_*`
- `altered_dominant_intensity_*`

## Demo / audit output

v2_2_88 should output both:

1. a standard-tune Blue Bossa three-chorus demo for real minor ii–V–i listening context;
2. a compact minor/turnaround coverage fixture for deterministic policy matrix and audit verification.

## Validation commands

```bash
python -m compileall src
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
```

## Next recommended task

`v2_2_89 — Upper Structure / Voicing Guard Listening Refinement`: use the v2_2_88 coverage confidence to return to listening quality, especially upper-register sharpness and low-register density guard behavior.
