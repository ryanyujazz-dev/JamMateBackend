# V1 Instrument Rules Deep Audit and V2-Native Mapping — v2_5_9

Status: documentation-only engine-planning pass.  
Baseline: `v2_5_8_ballad_default_swing8_anticipation_timing_patch`.  
Rejected baseline: the prior experimental `v2_5_9_jazz_ballad_brush_drums_foundation` is not carried forward because it added a generic Ballad brush layer before completing V1 instrument-rule absorption.

This document records a deeper audit of V1 source rules by style and instrument, then maps those musical facts into the existing V2 architecture. It is intentionally not a migration plan for V1 code. V1 is a reference for musical behavior only.

---

## 1. Non-negotiable V2 interpretation

V2 must keep the current responsibility split:

```text
Pattern       = pitchless horizontal event layout and phrase slots
Anticipation  = pitchless barline/region movement
Gesture       = musical projection behavior such as inner movement, roll, partial reattack, fill
Expression    = duration, release, velocity, articulation, pedal intent, re-pedal offset
Voicing       = vertical pitch content, density, disposition, functional groups, voice leading
Realization   = MIDI note/CC materialization from already-resolved semantics
```

Therefore:

- V1 phrase IDs and source names are allowed only as audit references, not implementation names that force old structure into V2.
- `inner movement` belongs to V2 `core/gestures` and style `gesture_policy.py`, not to ordinary comping pattern cells.
- V1 `LOW/HIGH/INNER/INNER_DYAD` slot logic should become V2 functional projection groups such as `foundation_group`, `support_group`, `projection_group`, `color_group`, `motion_group`, `top_voice`, not sorted-note slicing.
- V1 `rootless4/rootless5/warm5/shell4` texture names must not be copied into pattern selection. They translate only into V2 `voicing_intent`, `target_density`, `content_policy`, and `disposition_policy` hints.
- V1 late MIDI repairs and mirror runtimes must not be reproduced. Presence, phrase slots, anticipation, expression, and gesture intent must be correct before MIDI realization.

---

## 2. Jazz Ballad — V1 musical rules worth absorbing

### 2.1 Piano

V1 source areas audited:

```text
styles/jazz_ballad/piano_phrase_engine.py
styles/jazz_ballad/idiomatic_phrases.py
styles/jazz_ballad/piano_rendering.py
styles/jazz_ballad/piano_realizer.py
generators/piano/pipeline/ballad_inner_movement_planner.py
```

Observed V1 musical behavior:

1. Ballad piano is planned as phrase breathing, not as isolated one-bar rhythm cells.
2. Default space means `light/anchored harmonic presence`, not empty bars.
3. The core Ballad gesture is `held foundation + inner/color motion`, not repeated full-voicing strikes.
4. 251 vocabulary is context-gated and phrase-family based: stable cadence, warm guide cluster, sus group, dominant color glide, altered cluster, diminished group, tonic afterglow, open cadence roll, inner chromatic/triplet highlights.
5. V1's Ballad phrase layer chooses middle-layer musical jobs: gesture, coverage policy, pedal policy, top voice intent, voicing moment, touch intent, response density, harmonic movement, movement register.
6. Delayed entry should still feel anchored and sustained. It must not become a short isolated tap.
7. Cadence release can be rolled/open, but only at phrase/section/release contexts.
8. Strong colors such as 13/#11, altered clusters, and diminished groups are expressive-budget events, not default bar-level noise.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| phrase breathing | `styles/jazz_ballad/comping_patterns.py` + `arrangement_policy.py` | phrase-family metadata and phrase-slot selection only |
| held foundation + inner motion | `styles/jazz_ballad/gesture_policy.py`, `core/gestures`, realization projection map | `GestureKind.INNER_MOVEMENT`, `motion_group` / `color_group`; no sorted `INNER_DYAD` legacy slots |
| cadence roll | `core/gestures` + style gesture policy | `GestureKind.ROLLED_ONSET` gated by phrase role |
| 251 family choice | `core/harmony/harmonic_context.py` + style phrase candidates | `major_251_*` / `minor_251_*` phrase intent; no V1 code migration |
| 13/#11, altered, dim colors | `core/voicing` harmonic expansion + future altered policy gate | phrase supplies `color_intent`; voicing decides legal source |
| soft entry and response | `core/expression` + style expression policy | sustained/light touch; avoid short staccato for Ballad response unless explicitly requested |
| pedal breathing | `core/expression` / pedal policy | clear-on-change, light re-pedal, connected release; no MIDI-after repair |

What not to absorb:

- V1 direct `voicing_arc` names as implementation selectors.
- V1 phrase engine as a new runtime subsystem.
- V1 idiom IDs as direct pattern IDs that choose pitches.
- Late MIDI presence repair.

### 2.2 Bass

V1 source areas audited:

```text
styles/jazz_ballad/bass_phrase_engine.py
styles/jazz_ballad/bass_patterns.py
styles/jazz_ballad/bass_realizer.py
```

Observed V1 musical behavior:

1. Ballad bass is `anchor path first, ornament second`.
2. Beat 1 is usually a root/foundation anchor.
3. Beat 3 is a secondary target: fifth, third, seventh, root, or hold, chosen according to phrase role and root-root streak guard.
4. Split bars stay restrained; they outline changes without forcing root-root mechanical repetition.
5. Cadence setup may add beat 4 or 4& approaches, but these are phrase-function ornaments with consecutive-use guards.
6. Beat 2 can be a safer broken-two-feel color than frequent 2&.
7. 2& is rare and mostly split-bar/gentle-lift specific.
8. Ballad bass is not walking bass by default.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| anchor path | `styles/jazz_ballad/bass_foundation_patterns.py` or adjacent bass foundation policy | `BassAnchorPathIntent` style vocabulary: beat1 target + beat3 target |
| phrase-role weighting | `styles/jazz_ballad/arrangement_policy.py` + bass foundation owner | phrase role influences target weights; no generic rhythm-first cell |
| root-root streak guard | bass foundation selector | scoring/guard before pitch realization |
| cadence setup ornaments | bass foundation + future fill/ornament policy | beat4 setup / 4& approach only when resolving and spaced |
| split-bar restraint | bass foundation owner | root touch per short region; avoid forcing beat3 if chord changes make it unclear |

Recommended V2 implementation shape:

```text
JazzBalladBassAnchorPathPolicy
  -> choose phrase_role
  -> choose beat1 target_function
  -> choose beat3 target_function
  -> optionally attach restrained ornament intent
  -> Bass pitch resolver realizes target functions later
```

This should be the next audible Ballad improvement after this audit pass.

### 2.3 Drums / Brush

V1 source areas audited:

```text
styles/jazz_ballad/drum_brush_engine.py
styles/jazz_ballad/drum_patterns.py
styles/jazz_ballad/drum_realizer.py
```

Observed V1 musical behavior:

1. Brush is a semantic texture layer, not a fixed GM drum-loop pattern.
2. Brush planning chooses four independent dimensions:
   - texture: `circular_sparse`, `circular_standard`, `half_bar_breath_sweep`, `release_sweep`
   - time anchor: `none`, `4_only`, `2_4_soft`
   - kick policy: `none`, `beat1_only`, `one_three`, `all_four_feather`
   - phrase breath: `none`, `brush_drag_to_4`, `soft_swish_4and`, `section_breath`, `final_release`
3. The policy depends on role tags, phrase/section endings, `energy`, and sparse/active context.
4. Feather kick is very soft and supportive; it is not a rock kick layer.
5. Phrase breath appears at phrase/section boundaries or interactive response contexts, not every bar.
6. Velocities are low, and density labels remain `very_low`, `low`, or `low_mid`.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| brush texture dimension | `styles/jazz_ballad/percussion_patterns.py` | semantic brush policy candidate, not hard-coded single loop |
| time anchor dimension | percussion style policy | 2/4 soft hat or 4-only selected by arrangement context |
| feather kick dimension | percussion style policy + realizer semantic map | very soft kick/foundation shadow |
| phrase breath | `fill_policy.py` or percussion phrase marker metadata | only phrase/section/ending contexts |
| kit abstraction | core percussion realizer profile map | semantic names with GM fallback; no V1 render profile migration |

What the previous experimental brush pass missed:

- It added generic brush hits before modeling V1's policy dimensions.
- It did not connect brush density to phrase role, energy, or section/ending context.
- It treated brush primarily as audible time-fill instead of a breathing texture policy.

Correct future Ballad drum task should be named around `percussion_policy` or `brush_semantic_policy`, not merely `brush_drums_foundation`.

---

## 3. Medium Swing — V1 musical rules worth absorbing

### 3.1 Piano

V1 source areas audited:

```text
styles/medium_swing/piano_patterns.py
styles/medium_swing/piano_pattern_policy.py
styles/medium_swing/comping_feel_policy.py
generators/piano/pipeline/medium_swing_comping_feel_planner.py
```

Observed V1 musical behavior:

1. Medium Swing piano is conversational comping, not constant pad.
2. Important families include:
   - single hold / split hold
   - Charleston / reverse Charleston
   - delayed hold / delayed answer
   - two-bar statement-answer
   - backbeat tail / soft tail
   - dominant resolution / two-five support
   - phrase release / resolution breath
3. Two-bar statement-answer is central. Swing piano should not be independent random one-bar choices every bar.
4. 4& push exists but must be rare; it must not become a repeated 4&→1 habit.
5. Offbeat comping is classified into semantic feel roles: time anchor, offbeat response, answer lift, forward push, cadence color support, phrase release, support space.
6. Shell2/simple shell capability is a user/LLM-controllable option but not a default style sound.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| conversation/statement-answer | `styles/medium_swing/comping_patterns.py` + style history policy | phrase-pair metadata / history-aware selection |
| 4& rarity | anticipation/style comping guard | low budget, consecutive-use guard, phrase-boundary only |
| comping feel roles | `styles/medium_swing/expression_policy.py` or adjacent comping feel policy | semantic touch/duration/accent hints consumed by expression |
| dominant/two-five support | harmonic context + style phrase candidate | event role and color intent only; voicing owns pitch |
| shell2 minority | `voicing_policy.py` / voicing intent | option preserved but default weight low |

### 3.2 Bass

V1 source areas audited:

```text
generators/bass/walking/skeletons.py
generators/bass/walking/connector.py
generators/bass/walking/line_builder.py
generators/bass/walking/bass_target_graph.py
styles/medium_swing/bass_classic_fills.py
```

Observed V1 musical behavior:

1. Medium Swing bass is a walking system built from target-root anchors, first-three-beat skeletons, and beat-4 connectors.
2. Register/lane/zone guards prevent random octave jumps and unnatural line direction.
3. Beat 4 is primarily a connector to the next root, not a random chord tone.
4. DI/root-echo ornaments are optional rhythmic ornaments, not pitch-vocabulary skeletons.
5. Classic fills are a high-level branch: first detect a scene, then generate a complete idiomatic candidate; otherwise fall back to the generic walking engine.
6. The two-bar tonic fill is a complete phrase: root, low-third upbeat sustain, 4-#4-5 motion, upbeat 5, return 4-3, connect to next root.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| three-beat skeleton + beat4 connector | `styles/medium_swing/bass_foundation_patterns.py` and generation bass owner | keep split between skeleton and connector |
| register/lane guard | bass pitch resolver / scorer | range-contour score; avoid large jumps |
| DI/root echo | gesture/ornament policy | separate rhythmic ornament, not pitch pattern core |
| classic fill branch | `styles/medium_swing/fill_policy.py` + bass foundation | scene-gated complete candidate, rare |

### 3.3 Drums

V1 source areas audited:

```text
styles/medium_swing/drum_patterns.py
styles/medium_swing/drum_realizer.py
generators/drums/phrase_policy.py
```

Observed V1 musical behavior:

1. Ride pattern is the time identity: spang-a-lang variants and sparse quarters.
2. Hi-hat 2/4 and feather kick are foundational time anchors.
3. Snare/ride fills occur at phrase/section/ending boundaries, not as constant bar-level chatter.
4. Ending fills are stronger; phrase fills remain tiny.
5. The drummer stabilizes time while piano and bass converse.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| ride identity | `styles/medium_swing/percussion_patterns.py` | semantic ride vocabulary with swing timing |
| hat/kick anchor | percussion style policy + expression | low-velocity time anchor |
| phrase/section fills | `fill_policy.py` or percussion role metadata | boundary-only, energy-gated |
| density balancing | arrangement/percussion policy | less comping when piano/bass are active |

---

## 4. Bossa Nova — V1 musical rules worth absorbing

### 4.1 Piano

V1 source areas audited:

```text
styles/bossa_nova/piano_patterns.py
styles/bossa_nova/piano_pattern_policy.py
styles/bossa_nova/anticipation_policy.py
styles/bossa_nova/expression_policy.py
```

Observed V1 musical behavior:

1. Core identity anchor is exactly `1, 2, 3&`, with short-short-sustain articulation.
2. The first two opening bars strongly prefer core batida when harmonic rhythm allows it.
3. Ordinary Bossa cells are separated into Class A and Class B:
   - Class A starts on beat 1 and dominates.
   - Class B starts on 1& and is rare color.
4. Class A examples: `1`, `1 + 2&`, `1 + 3&`, rare `1 + 4&`, lower-weight `1 + 3`, and ordinary `1 + 2 + 3&`.
5. Class B examples: `1&`, `1& + 3` as strongest B color, lower `1& + 3&`, very rare `1& + 4`, `1& + 4&`, `1& + 3 + 4&`.
6. Core batida is an identity reset, not a mechanical every-bar loop.
7. Anticipation is separate from rhythm-cell choice. Native 4& cells and barline anticipation must not collide.
8. Harmonic-rhythm clarity overrides groove identity: two-chord and multi-chord bars need segment-aware light marks.
9. Distance-aware articulation matters: close gaps usually short; larger gaps usually sustain; last-event behavior should resolve against next real event.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| core batida identity | `styles/bossa_nova/comping_patterns.py` + style policy | one canonical `core_batida`, elevated at starts/resets |
| Class A/B ratio | style comping selection policy | explicit class metadata and history guard |
| anticipation separation | `styles/bossa_nova/anticipation_policy.py` + core anticipation | no native 4& conflict; independent eligibility |
| harmonic clarity | harmonic rhythm analyzer + style candidate filter | two-chord/multi-chord handlers override ordinary cells |
| distance articulation | core expression + bossa expression policy | final-event distance resolver, not fixed pattern duration only |

What not to absorb:

- V1 texture weights in rhythm templates; V2 voicing policy should own texture/density.
- Fixed two-bar phrase templates. V1 itself already removed fixed length-2 Bossa phrase templates; V2 should maintain that.

### 4.2 Bass

V1 source areas audited:

```text
styles/bossa_nova/bass_patterns.py
styles/bossa_nova/bass_realizer.py
```

Observed V1 musical behavior:

1. Bossa bass is root/fifth two-feel, not walking.
2. Long regions get root on 1 and fifth on 3.
3. Two-bar A/B alternation creates light phrase contour.
4. Split/short regions state root only for clarity.
5. Next-root anticipation at 4& is low-probability and phrase/section/transition boosted, but disabled for endings.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| root/fifth two-feel | `styles/bossa_nova/bass_foundation_patterns.py` | root/fifth A/B cells |
| split-bar clarity | bass foundation policy | root-only short-region support |
| next-root anticipation | bossa anticipation/bass owner | low-probability, eligibility-gated, no walking conversion |

### 4.3 Drums / Percussion

V1 source areas audited:

```text
styles/bossa_nova/drum_patterns.py
styles/bossa_nova/drum_realizer.py
```

Observed V1 musical behavior:

1. Shaker/hat eighth contour supplies air, not rock hi-hat weight.
2. Cross-stick is a two-bar A/B vocabulary:
   - A: 1, 2&, 4
   - B: 2, 3&
3. Kick is a soft low-frequency shadow on 1 and 3, with optional 2&/4& shadows.
4. Micro markers and turnaround/ending markers stay idiomatic: rim/cross-stick and shaker lifts, no generic tom/snare fills.
5. Percussion should stabilize groove identity while staying out of the piano anticipation lane.

V2-native mapping:

| V1 musical fact | V2 owner | V2-native expression |
|---|---|---|
| shaker air contour | `styles/bossa_nova/percussion_patterns.py` | light semantic shaker/hat layer |
| cross-stick A/B | percussion style policy | phrase-local two-bar alternation |
| soft kick shadow | percussion style policy | low-velocity support layer |
| idiomatic micro markers | fill/percussion boundary | phrase/turnaround/ending only |

---

## 5. Cross-style V2 development principles extracted from V1

1. The style layer should own musical vocabulary and selection policy, but never concrete final pitches.
2. Advanced music behavior should usually enter as phrase/gesture/expression/bass-path/percussion-policy semantics, not as more low-level rhythm cells.
3. Bass and drums are not generic MIDI layers; each style has a different instrument grammar:
   - Ballad bass = restrained anchor path.
   - Swing bass = walking skeleton + connector + rare fills.
   - Bossa bass = root/fifth two-feel.
   - Ballad drums = brush texture policy.
   - Swing drums = ride/hat/kick time identity with boundary fills.
   - Bossa percussion = shaker/cross-stick/kick groove identity.
4. Harmonic context must be reused from `core/harmony/harmonic_context.py` or existing timeline/arrangement metadata before adding new recognizers.
5. A style-specific policy may request gestures, density, color intent, or projection groups, but core voicing remains responsible for notes.
6. Every audible style change must include a standard-tune listening demo, but documentation-only audit passes do not need to generate new MIDI.

---

## 6. Corrected engine roadmap after v2_5_9

The previous `v2_5_9_jazz_ballad_brush_drums_foundation` should be treated as an abandoned trial. The formal engine roadmap should be:

```text
v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping — this pass, docs only
v2_5_10_jazz_ballad_bass_anchor_path_policy — next audible pass
v2_5_11_jazz_ballad_brush_semantic_policy — after bass, not before; based on V1 brush dimensions
v2_5_12_jazz_ballad_251_color_families_gated — gated phrase/color families
v2_5_13_medium_swing_piano_phrase_feel_restoration — statement/answer and 4& rarity
v2_5_14_medium_swing_bass_classic_fill_branch_review — scene-gated, not main skeleton
v2_5_15_bossa_identity_anticipation_articulation_review — core batida, A/B ratio, anticipation separation
v2_5_16_bossa_percussion_groove_identity_review — shaker/cross-stick/kick layers
```

### v2_5_10 immediate task definition

Do not add drums yet. Implement the Ballad bass anchor-path policy first because the trio foundation must be correct before brush density is judged.

Minimum requirements:

```text
- reuse existing jazz_ballad/bass_foundation_patterns.py if possible
- no new V1-style bass phrase engine unless existing owner cannot carry the policy
- beat 1 target mostly root
- beat 3 target fifth/third/seventh/root/hold with root-root streak guard
- split-bar restrained behavior
- beat 2 very rare setup; 2& rarer
- beat 4 / 4& only as resolving cadence/setup ornament
- no walking by default
- no V1 code migration
```

---

## 7. Checklist for future implementation reviews

Before each style/instrument optimization, answer:

1. Which V1 musical rule is being absorbed?
2. Is it truly a musical behavior, or just an old implementation artifact?
3. Which V2 module owns it?
4. Does it respect Pattern / Gesture / Expression / Voicing separation?
5. Does it avoid concrete pitch or texture binding in pattern vocabulary?
6. Does it reuse existing core/style owners before adding files?
7. Is there a focused standard-tune demo for listening if generation changes?
8. Is there a negative test or audit guard preventing V1 code-shape regression?

