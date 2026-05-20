# v2_6_64 — Medium Swing Piano V1 Idiom Delta Audit Checkpoint

Behavior-preserving V1→V2 Medium Swing piano idiom delta audit. This checkpoint studies V1 vocabulary/expression/history ideas and maps them to the existing V2 ChordRegion-first pattern architecture without changing runtime selection logic.

## V1 reference signals

- Pattern templates / events: `70` / `182`
- Role counts: `{'base': 24, 'fill': 8, 'variation': 8, 'major_251': 7, 'two_five': 7, 'minor_251': 6, 'ii_setup': 4, 'two_chord_bar': 4, 'ending': 2}`
- Category counts: `{'stable': 30, 'offbeat': 15, 'variation': 7, 'push': 7, 'gentle_fill': 6, 'busy_fill': 3, 'ending': 2}`
- Expression touch ranges: `{'soft_hold': {'velocity': [48, 59], 'duration_ticks': [84, 140], 'usage': 'main support, beat-1/3 anchors, cadence release'}, 'light_stab': {'velocity': [48, 65], 'duration_ticks': [62, 88], 'usage': 'Charleston answer and light offbeat response'}, 'accent_stab': {'velocity': [60, 70], 'duration_ticks': [58, 72], 'usage': 'push, 4& pickup, dominant approach, busy fill'}, 'backbeat_hold': {'velocity': [51, 64], 'duration_ticks': [76, 108], 'usage': '2&/3& support, longer than stab'}, 'final_hold': {'velocity': [44, 45], 'duration_ticks': [220, 240], 'usage': 'ending final sustain'}}`

## V1 → V2 translation matrix

### base stable/offbeat vocabulary

- V1 signal: `base=24, stable=30, offbeat=15`
- V2 translation: `4-beat ChordRegion stable/offbeat pitchless cells`
- Status: `covered`
- Next action: Keep calibrated by v2_6_58/v2_6_59 history ratios; do not add more generic cells before context subset policy.

### two_chord_bar split vocabulary

- V1 signal: `two_chord_bar=4`
- V2 translation: `2-beat / 1-beat ChordRegion vocabulary; no bar-first route`
- Status: `covered_as_region_first_translation`
- Next action: Keep name and route region-first; do not restore two_chord_bar as a selector key.

### major_251 / minor_251 / two_five / ii_setup priority

- V1 signal: `major_251=7, minor_251=6, two_five=7, ii_setup=4`
- V2 translation: `ChordRegion functional context candidate subset, not bar-level pattern templates`
- Status: `partial_multiplier_only`
- Next action: v2_6_65 should add context-specific candidate subset priority before generic fallback.

### fill / variation vocabulary

- V1 signal: `fill=8, variation=8, gentle_fill=6, busy_fill=3`
- V2 translation: `Phrase-role/context-gated candidate subset with active/busy guard, not gesture or voicing`
- Status: `partial_low_level_active_only`
- Next action: Defer until after progression subset; extend history scorer with active/fill/busy memory before enabling more fills.

### ending vocabulary

- V1 signal: `ending=2 with final_hold`
- V2 translation: `ending/last-region candidate subset + final_hold semantic hint`
- Status: `partial_expression_hint_only`
- Next action: Add ending subset later, after expression calibration; do not write MIDI durations in pattern.

### 4& rare lift policy

- V1 signal: `has_4& downweighted; no_4and/delayed/tail rewarded`
- V2 translation: `region-local tail-push risk + region-first anticipation compatibility`
- Status: `covered_but_needs_v1_ratio_audit`
- Next action: v2_6_66 should reinforce no-4& / delayed-tail idioms using region-local tail slots.

### history guard

- V1 signal: `exact/rhythm/active/fill/push/offbeat/busy/two-phrase penalties`
- V2 translation: `CompingHistoryScorer over ChordRegion-local pattern history`
- Status: `partial_no_busy_fill_phrase_memory_yet`
- Next action: v2_6_67 should add active/fill/busy/multi-region phrase memory, not bar-first two-bar phrase logic.

### touch/expression numeric calibration

- V1 signal: `touch ranges for soft_hold/light_stab/accent_stab/backbeat_hold/final_hold`
- V2 translation: `ExpressionPolicy ranges; pattern carries semantic_expression_hint only`
- Status: `partial_handoff_done_calibration_pending`
- Next action: v2_6_68 should calibrate ExpressionPolicy from V1 ranges while preserving hold_until_next_touch semantics.

### texture expansion shell2/shell4/rootless4

- V1 signal: `V1 expands rhythm templates into texture candidates`
- V2 translation: `Reject pattern-level texture expansion; keep voicing policy independent`
- Status: `rejected_for_v2_pattern_layer`
- Next action: Keep shell2/rootless/drop2/drop3 in voicing policy only.

## V2 static pattern audit

- Candidate count total/active: `39` / `37`
- Active by region length: `{'one_beat_region': 2, 'two_beat_region': 6, 'three_beat_region': 1, 'four_beat_region': 28}`
- Active by weight class: `{'stable': 19, 'offbeat': 12, 'active': 2, 'tail_push': 4}`
- Active semantic hints: `{'light_stab': 23, 'soft_hold': 18, 'backbeat_hold': 15, 'accent_hold': 6, 'accent_stab': 4}`
- Tail-push active candidate count/weight: `4` / `0.042`
- No-4& delayed/tail candidate count: `11`
- Forbidden expression candidates: `0`
- Bar-first two_chord_bar candidates: `0`

## Runtime standard-tune audit

### All the Things You Are

- MIDI: `demos/v2_6_64_all_the_things_you_are_medium_swing_piano_v1_idiom_delta_audit_demo.mid`
- Piano events: `205`
- Region length counts: `{'four_beat_region': 175, 'two_beat_region': 30}`
- Harmonic context counts: `{'section_start': 22, 'predominant_to_dominant': 40, 'dominant_resolution': 50, 'tonic_resolution': 50, 'generic': 15, 'section_end': 16, 'tonic_prolongation': 6, 'ending': 6}`
- Weight class counts: `{'offbeat': 41, 'stable': 155, 'active': 9}`
- Semantic hint counts: `{'backbeat_hold': 51, 'light_stab': 66, 'accent_hold': 22, 'soft_hold': 66}`
- Tail-push / active-or-tail-push / no-4& delayed-tail events: `0` / `9` / `67`
- History penalty / bonus events: `15` / `51`
- Harmonic policy / hold-until-next-touch events: `205` / `139`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

### Autumn Leaves

- MIDI: `demos/v2_6_64_autumn_leaves_medium_swing_piano_v1_idiom_delta_audit_demo.mid`
- Piano events: `234`
- Region length counts: `{'two_beat_region': 179, 'four_beat_region': 55}`
- Harmonic context counts: `{'section_start': 35, 'tonic_resolution': 57, 'generic': 35, 'predominant_to_dominant': 41, 'dominant_resolution': 46, 'section_end': 15, 'ending': 5}`
- Weight class counts: `{'stable': 175, 'offbeat': 59}`
- Semantic hint counts: `{'soft_hold': 96, 'backbeat_hold': 43, 'light_stab': 87, 'accent_hold': 8}`
- Tail-push / active-or-tail-push / no-4& delayed-tail events: `0` / `0` / `47`
- History penalty / bonus events: `1` / `37`
- Harmonic policy / hold-until-next-touch events: `234` / `147`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Acceptance

Passed: `True`

- `static: no pattern candidate writes final expression values`: `True`
- `static: no bar-first/two-chord-bar markers remain in V2 candidates`: `True`
- `static: V2 has active 1/2/4-beat region candidates`: `True`
- `static: V2 keeps V1-derived expression semantic hints`: `True`
- `static: V1 progression vocabulary is explicitly marked partial, not falsely accepted`: `True`
- `static: V1 texture expansion is explicitly rejected from V2 pattern layer`: `True`
- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: harmonic policy remains active`: `True`
- `all_the_things_you_are: history scorer remains active`: `True`
- `all_the_things_you_are: no pattern events contain concrete expression values`: `True`
- `all_the_things_you_are: no bar-first two_chord_bar runtime events`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: harmonic policy remains active`: `True`
- `autumn_leaves: history scorer remains active`: `True`
- `autumn_leaves: no pattern events contain concrete expression values`: `True`
- `autumn_leaves: no bar-first two_chord_bar runtime events`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`

## Recommended next tasks

- `v2_6_65_engine_medium_swing_progression_specific_candidate_subset_policy`
- `v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement`
- `v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer`
- `v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration`
- `v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint`
