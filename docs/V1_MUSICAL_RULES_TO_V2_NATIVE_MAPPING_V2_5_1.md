# v2_5_1 V1 Musical Rules Absorption and V2-Native Mapping

This document is a **no-runtime-change** planning/audit pass for `feature/engine-deepening`.
It studies the V1 source as a musical-rule reference only. It does **not** authorize code migration from V1, new Agent/LLM behavior, or a parallel V1-style runtime.

Current package version: `v2_5_1`.

---

## Scope

### In scope

- Read V1 source for musical behavior, especially style-level instrument rules.
- Extract reusable musical facts from V1.
- Re-express those facts using the V2 architecture and naming discipline.
- Decide which existing V2 owner should carry each future implementation.
- Plan the next engine-only development steps.

### Out of scope

- No V1 code migration.
- No direct copying of V1 file structure, pattern IDs, realizer logic, or runtime mirrors.
- No Agent/LLM workflow development.
- No new audible generation behavior in this pass.
- No new MIDI demos required because runtime behavior is unchanged.

---

## Required V2 architectural reading

V2 remains the source of truth:

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Gesture       = projection / movement / partial reattack / roll semantics
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Style packages may request policy and semantic intent. They must not choose concrete MIDI notes, final velocities, pedal CC, or voicing layouts directly.

---

## V1 source areas reviewed

The useful V1 references were concentrated in these source owners:

```text
styles/jazz_ballad/piano_phrase_engine.py
styles/jazz_ballad/idiomatic_phrases.py
styles/jazz_ballad/piano_rendering.py
styles/jazz_ballad/harmonic_movement.py
styles/jazz_ballad/piano_patterns.py
styles/jazz_ballad/bass_phrase_engine.py
styles/jazz_ballad/bass_patterns.py
styles/jazz_ballad/drum_brush_engine.py
styles/jazz_ballad/expression_policy.py
styles/jazz_ballad/voicing_policy.py

styles/medium_swing/piano_patterns.py
styles/medium_swing/piano_pattern_policy.py
styles/medium_swing/comping_feel_policy.py
styles/medium_swing/bass_classic_fills.py
styles/medium_swing/expression_policy.py

generators/bass/walking/skeletons.py
generators/bass/walking/connector.py
generators/bass/walking/line_builder.py
generators/bass/walking/bass_target_graph.py

styles/bossa_nova/piano_patterns.py
styles/bossa_nova/piano_pattern_policy.py
styles/bossa_nova/anticipation_policy.py
styles/bossa_nova/expression_policy.py
styles/bossa_nova/bass_patterns.py
styles/bossa_nova/drum_patterns.py
```

V1's important contribution is its **musical behavior**, not its implementation boundary.

---

## Core finding

V1 sounds better mainly because many style “patterns” are not simple rhythm cells. They are phrase/gesture templates that already encode:

```text
harmonic context
phrase function
cadence state
response density
held foundation vs reattack scope
inner/top/color movement
pedal refresh behavior
bass path role
brush breath / time anchor
```

V2 currently has the cleaner architecture, but some style vocabularies are still too thin. The next V2 work should therefore add **V2-native phrase / gesture / expression / bass-path semantics**, not more low-level onset cells.

---

## Translation rule: V1 behavior to V2 owners

| V1 musical behavior | Do not copy | V2-native owner / expression |
|---|---|---|
| Ballad phrase intent such as warm pad, breath answer, cadence release | V1 phrase engine class/runtime path | `styles/jazz_ballad/arrangement_policy.py` + `comping_patterns.py` metadata + `gesture_policy.py` |
| Inner voice movement / inner dyad answer | Pattern IDs with direct note/slot assumptions | `core/gestures/voice_motion_gesture.py` + `styles/jazz_ballad/gesture_policy.py` request |
| Held foundation with partial reattack | V1 `slots_to_notes` slicing | Gesture projection refs: `foundation_group`, `color_group`, `inner`, `top`, `projection_group` |
| Pedal refresh / re-pedal at chord change | Pattern or MIDI repair hacks | `core/expression/pedal.py` and style expression policy |
| Warm/open/thick Ballad sound | V1 `warm5`, `rootless5`, `shell4` texture names in pattern | V2 voicing intent: density, texture state, disposition preference, color permission |
| 251 color idioms | Direct V1 notes or hardcoded altered tones | Phrase metadata + V2 `HarmonicExpansionPolicy` / future altered gate |
| Ballad bass two-feel path | Static root-only pattern | `generation/bass_foundation` style policy / future Ballad anchor-path logic |
| Swing walking feel | V1 line builder import | Existing V2 BassFoundation owner with ThreeBeatSkeleton + Beat4Connector rules |
| Bossa batida identity | Whole V1 piano policy | Existing Bossa style pattern/expression/anticipation owners |

---

## Jazz Ballad rules to absorb

### Ballad piano grammar

V1's Ballad piano is phrase-first. The V2 version should eventually describe phrase families such as:

```text
warm_pad
breath_answer
two_chord_soft_marks
inner_voice_breath
inner_resolution
middle_motion_line
delayed_soft_entry
rolled_cadence_release
major_251_stable_cadence
major_251_warm_guide_cluster
major_251_sus_group_resolution
major_251_dominant_color_glide
major_251_dominant_dim_resolution
major_251_alt_cluster_release
minor_251_dark_resolution
tonic_6dim_afterglow
```

These names are **musical-intent names**, not final V2 runtime IDs. Implementation should start with the safest three or four families only.

### Ballad piano must not be “more cells”

The V2 `v2_5_0` light-retouch candidates are a low-level fallback, not the long-term direction. Future Ballad work should avoid simply adding cells like `1_2and`, `1_3and`, or `1_1and` unless they carry real phrase function and a gesture contract.

### Held foundation + inner movement

The key V1 musical fact is:

```text
full harmonic presence establishes the chord;
common/foundation voices can continue;
only inner/color/top material may move or be lightly re-articulated;
pedal may refresh without making every event a full re-strike.
```

In V2 this must become gesture/expression/voicing cooperation:

```text
PatternEvent
  gesture = GestureKind.INNER_MOVEMENT or ROLLED_ONSET
  metadata.phrase_family = ...
  metadata.attack_scope = inner / color_group / top / projection_group

Expression
  touch = gentle / breath / release
  duration = sustain-aware
  pedal = light_refresh / clear_on_change / connected

Voicing
  chooses actual notes and projection map

Realization
  projects the gesture onto selected voicing voices/groups
```

### Ballad color and altered material

V1 contains strong 251 idioms: dominant 13/#11 glide, altered cluster release, diminished group resolution, tonic 6-dim afterglow, drop-like cadence roll, and minor 251 dark resolution.

V2 must gate them:

```text
chord_symbol_only: use only chart-expressed tones/colors
harmonic_expansion_enabled: allow tasteful added color
altered_enabled / altered_intent: allow altered dominant material
cadence/release context: allow low-frequency color group movement
```

Do not hardcode V1 color notes in style patterns.

### Ballad bass anchor path

V1 Ballad bass suggests a restrained two-feel path:

```text
beat 1: root/foundation anchor
beat 3: fifth / third / seventh / root / hold
beat 4: occasional setup
4&: rare approach, only when phrase/cadence allows
2&: very rare color/answer
```

V2 should express this through the BassFoundation owner rather than a separate Ballad walking engine. The goal is **anchor path**, not walking.

### Ballad brush / drums

V1 brush behavior is phrase-breath aware. V2 should eventually distinguish:

```text
brush time anchor
brush breath
phrase-end release
cadence lift
soft final decay
```

This is lower priority than Ballad piano gesture and bass anchor path.

---

## Medium Swing rules to absorb

### Piano comping feel

V1 Medium Swing piano is phrase-feel heavy. Useful musical families:

```text
two_bar_statement_answer
call_response
hold_answer
backbeat_tail
soft_tail
delayed_answer
charleston
reverse_charleston
dominant_resolution
resolution_breath
```

V2 should not turn these into an uncontrolled pattern soup. They should be selected by phrase/region context, with 4& push kept rare and shell2 remaining a user/LLM-requestable simple texture, not a default sound.

### Bass walking feel

V1's useful Swing bass facts align with V2's existing BassFoundation direction:

```text
ThreeBeatSkeleton
Beat4Connector
target-to-target continuity
register zone / lane guard
root echo DI as independent ornament
rare classic fill as scene branch
```

Future Swing work should deepen existing `generation/bass_foundation` logic instead of importing V1 walking modules.

---

## Bossa Nova rules to absorb

V1 reinforces the Bossa rules already designed in V2 discussions:

```text
core_batida = 1, 2, 3&
first two hits short/detached, third hit sustained
core_batida anchors pickup/opening/phrase return/after fill
Class A beat-1-start cells dominate
Class B 1&-start cells are rare
anticipation is independent from pattern selection
no anticipation if current 4& is occupied
articulation follows event distance, not pattern name alone
bass uses root-fifth / two-bar alternation, not walking
multi-chord bars need harmonic clarity over rhythmic flourish
```

V2 should preserve Bossa's identity anchor and avoid making it phrase-heavy in the Ballad/Swing sense.

---

## Explicitly forbidden V1 inheritance

Do not implement any of the following in V2:

```text
copy V1 source files or classes
copy V1 runtime paths
recreate V1 mature-runtime/mirror-runtime double path
place voicing texture names inside pattern candidates
place concrete MIDI notes/velocity/duration/pedal in GestureRequest
repair harmonic presence after MIDI rendering instead of planning it upstream
use sorted-note slot slicing as the main inner-movement system
make Bossa/Swing/Ballad import each other's runtime helpers directly
```

V2 names should use the project's current taxonomy:

```text
simultaneous_onset
rolled_onset
inner_movement
foundation_group
support_group
projection_group
color_group
VoicingTextureIntent
VoicingTextureState
HarmonicExpansionPolicy
BassFoundation
PatternEvent
GestureRequest
EventExpression
```

---

## Development plan after this audit

### v2_5_2 — Jazz Ballad Gesture Contract Foundation

Goal: enable Ballad to request V2-native gestures without changing voicing selection logic.

- Extend existing `styles/jazz_ballad/gesture_policy.py`; do not create a new subsystem first.
- Allow `inner_movement` and `rolled_onset` as style-approved gesture kinds.
- Keep requests pitchless and expressionless.
- Add tests proving forbidden concrete gesture metadata is still rejected.
- Do not yet add complex 251 color idioms.

### v2_5_3 — Jazz Ballad Phrase Intent Foundation

Goal: move away from low-level retouch cells toward phrase-aware pattern metadata.

Start with only:

```text
warm_pad
breath_answer
two_chord_soft_marks
major_251_stable_cadence
```

Each candidate should emit pitchless events with phrase metadata and optional gesture requests. It must not choose notes or voicing textures directly.

### v2_5_4 — Held Foundation / Partial Reattack Realization

Goal: make Ballad inner motion sound like held foundation plus light movement, not repeated full voicing.

- Use existing projection-map concepts.
- Prefer group refs over sorted-note slicing.
- Expression owns duration/release/pedal refresh.
- Voicing remains the only note selector.

### v2_5_5 — Ballad Bass Anchor Path

Goal: upgrade Jazz Ballad bass from static root-only support to restrained anchor path.

- Implement in or adjacent to existing `generation/bass_foundation` owners after reuse audit.
- Bias beat 1 root/foundation.
- Bias beat 3 to fifth/third/seventh/root/hold based on cadence and register.
- Keep beat 4 / 4& rare and phrase-aware.
- Do not walking-bass-ify Ballad.

### v2_5_6 — Ballad 251 Color Families, Gated

Goal: add a small set of idiomatic 251 families only after gesture and partial reattack are stable.

Start with:

```text
major_251_warm_guide_cluster
major_251_sus_group_resolution
major_251_dominant_color_glide
minor_251_dark_resolution
```

Altered, diminished, triplet, and 6-dim afterglow should remain later gated additions.

### v2_5_7 — Medium Swing Piano Phrase Feel Restoration

Goal: recover statement/answer comping feel without increasing random offbeat clutter.

### v2_5_8 — Bossa Identity / Anticipation / Articulation Review

Goal: protect Bossa identity and anticipation correctness after Ballad/Swing phrase work.

---

## Immediate recommendation

Next engineering task:

```text
v2_5_2_jazz_ballad_gesture_contract_foundation
```

Do **not** continue expanding `soft_retouch`, `soft_answer`, or `soft_whisper` as the main Ballad path. Treat `v2_5_0` Ballad retouch cells as temporary fallback while V2-native phrase/gesture semantics are built.
