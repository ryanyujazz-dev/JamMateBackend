# Engine Track Changelog

Current baseline: `v2_6_1`.

This file records engine-track changes to reduce conflicts in the global `docs/CHANGELOG.md`.

---

## v2_5_9 — V1 Instrument Rules Deep Audit and V2-Native Mapping

- Documentation-only engine planning pass based on `v2_5_8`; no generation code changed.
- Explicitly discarded the experimental Ballad brush-drums shortcut as an abandoned trial, not an official baseline.
- Added deep V1 instrument-rule audit and V2-native mapping for Jazz Ballad, Medium Swing, and Bossa Nova piano/bass/drums.
- Reaffirmed no V1 code migration, no V1 phrase-engine/runtime mirror, no pattern-to-texture binding, and no MIDI repair paths.

## v2_5_8 — Jazz Ballad Default Swing-8 Anticipation Timing Patch

- Jazz Ballad timing profile defaults to swing-8 feel.
- Anticipation uses logical `.5` but performs as swing/triplet upbeat.

## v2_5_7 — Jazz Ballad 1& Sustain Continuity Bugfix

- Expression duration clamp respects performed swing-upbeat timing for Ballad `beat 1 -> 1&` continuity.

## v2_5_4 — Held Foundation Partial Reattack Realization

- `INNER_MOVEMENT` projects only requested inner/color voices.
- Foundation/common tones remain held through partial reattack.
