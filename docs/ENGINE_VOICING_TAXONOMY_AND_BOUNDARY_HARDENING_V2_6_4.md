# Engine Voicing Taxonomy and Boundary Hardening V2.6.4

**Task:** `v2_6_4_engine_voicing_taxonomy_doc_and_boundary_hardening`  
**Track:** `feature/engine-deepening`  
**Change type:** documentation + light boundary tests; no voicing retune and no listening-behavior change.

This document records the current V2 voicing taxonomy as implemented in the engine and hardens the boundary rule that no other layer may do voicing's work. It is intentionally Engine-owned and must not be used to change shared API, Agent workflow, HarmonyOS fixtures, or project version metadata.

---

## 1. Non-Negotiable Boundary

Voicing is the only layer that selects concrete vertical pitch content for harmonic instruments.

```text
Pattern       = horizontal pitchless rhythm / event placement / role / gesture request
Anticipation  = pitchless cross-region event rewrite
Expression    = duration / release / velocity / articulation / touch / pedal intent
Voicing       = concrete vertical pitch content / density / grouping / disposition / register / voice-leading
Gesture       = projection of an already selected VoicingPlan into one or more attacks
Realization   = NoteEvent / PedalEvent / MIDI materialization
```

Forbidden boundary breaks:

```text
pattern chooses MIDI notes
pattern chooses rootless_A / rooted_color / shell / spread / drop2
anticipation suppresses or creates notes based on voicing content
expression selects chord tones, source families, voicing textures, or disposition
style comping pattern binds voicing source/disposition instead of only declaring pitchless event facts
non-voicing core modules import voicing selection internals to make musical pitch decisions
voicing imports style, pattern, expression, realization, or MIDI modules
MIDI writer repairs bad voicing after the fact
```

Allowed cross-layer contacts:

```text
style voicing_policy.py returns a VoicingPolicy
HarmonicRealizer builds VoicingRequest and consumes VoicingPlan
GestureRealizer projects an already selected VoicingPlan
piano_audit observes voicing metadata without reselecting
voicing may depend on harmony/chord parsing and generic ensemble context
```

---

## 2. Current Runtime Voicing Chain

```text
VoicingPolicy
↓
VoicingRequest
↓
VoicingResolver
↓
content_planner / canonical source / color permission
↓
content placement and source rotation metadata
↓
disposition projection: closed / open / spread
↓
register variants and register guard
↓
VoicingCandidate[]
↓
scorer / Selector / Voice-leading state
↓
VoicingPlan
↓
GestureRealizer / NoteEvent projection
```

The concrete pitch boundary is `VoicingPlan`. Downstream modules may read `VoicingPlan.notes`, `projection_map`, `groups`, `content_family`, `density`, `functional_grouping`, and metadata, but they must not reselect pitch content.

---

## 3. Taxonomy Axis A — ContentFamily

`ContentFamily` answers: **which musical pitch roles are selected before disposition?** It does not decide register, hand split, timing, articulation, or MIDI serialization.

Current families:

```text
major_triad
minor_triad
diminished_triad
augmented_triad
sus2_triad
sus4_triad
power_chord_5th
seventh_chord_basic
guide_tone
shell
shell_plus_5
shell_plus_color
rootless_A
rootless_B
rooted_color
```

Practical groups:

| Group | Families | Responsibility |
| --- | --- | --- |
| Basic triad system | `major_triad`, `minor_triad`, `diminished_triad`, `augmented_triad`, `sus2_triad`, `sus4_triad`, `power_chord_5th` | Chord-symbol-faithful no-seventh voicing and future pop/folk/rock support. |
| Conservative seventh | `seventh_chord_basic` | Preserve the full chord-symbol seventh identity, typically root/third/fifth/seventh rotations. |
| Shell / guide | `guide_tone`, `shell`, `shell_plus_5`, `shell_plus_color` | Compact definition of chord quality; half-diminished and diminished must preserve their defining tones rather than arbitrary color. |
| Jazz rootless | `rootless_A`, `rootless_B` | A/B-oriented 4-note jazz color families such as `3-5-7-9`, `7-9-3-5`, and `3-13-7-9`, gated by color policy. |
| Rooted color | `rooted_color` | Root-included color/extension families such as `R-3-7-9`; important for Ballad, no-bass contexts, and explicit chart color. |

Boundary rule: `ContentFamily` is a voicing-source decision. Style pattern cells may not request a specific `ContentFamily`; style voicing policies may bias or allow families.

---

## 4. Taxonomy Axis B — RootSupportPolicy and BassRelation

`RootSupportPolicy` answers: **how much root/foundation support should the harmonic voicing carry?**

Current values:

```text
rootless_preferred
rootless_allowed
root_optional
root_preferred
root_required
bass_root_required
```

This axis is where ensemble context enters voicing. With bass present, piano may prefer or allow rootless voicings. Without bass, piano should normally move toward root/foundation support unless a user or higher-level intent explicitly requests rootless piano.

`BassRelation` describes the lowest-note relation after candidate construction:

```text
root_position
first_inversion
second_inversion
third_inversion
rootless_lowest_3rd
rootless_lowest_7th
bass_omitted
```

Boundary rule: ensemble context may influence `RootSupportPolicy`; pattern and expression must not compensate for missing root support by inserting voicing notes.

---

## 5. Taxonomy Axis C — Density and FunctionalGrouping

Density is not only a note count. It also carries an abstract grouping shape for lower/upper or foundation/projection organization without naming physical left/right hand in the core module.

Current `FunctionalGrouping` values:

```text
2
3
1+3
2+2
1+4
2+3
2+4
3+3
3+4
```

Current group roles:

```text
anchor
foundation
support
projection
color
motion
extension
```

Canonical reading:

| Density shape | Functional meaning |
| --- | --- |
| `2` | Minimal support/projection dyad. |
| `3` | Compact triad/shell/projection block. |
| `1+3` | One anchor/foundation note plus a three-note projection block. |
| `2+2` | Two-note support plus two-note color/projection block. |
| `1+4` | One foundation anchor plus an upper four-note projection block. |
| `2+3` | Two-note support/foundation plus upper three-note projection. |
| `2+4` | Two-note support/foundation plus upper four-note projection. |
| `3+3` | Three-note foundation plus three-note projection. |
| `3+4` | Three-note foundation plus four-note projection. |

Boundary rule: grouping belongs to voicing. Piano realization may later map groups to hands/registers, but core voicing must keep the abstract role names.

---

## 6. Taxonomy Axis D — Disposition and ProjectionMethod

Disposition answers: **how are selected pitch roles arranged in space?** It is distinct from content. `rootless_A` is not a disposition; `drop2` is not a content family.

Legacy-compatible public dispositions:

```text
closed
open
spread
two_hand_spread
left_root_right_chord
left_root_right_rootless
open_root_10th
```

Normalized projection families:

```text
closed
open
spread
```

Closed methods:

```text
compact
```

Open methods:

```text
generic_open
drop2
drop3
drop2_and_4
```

Spread methods:

```text
lower_upper_grouped
foundation_projection
root_anchored
root_10th_projection
```

Boundary rule: projection methods are voicing-owned. Style policies may specify allowed/preferred dispositions or method weights; style pattern cells must not request `drop2`, `drop3`, `spread`, or any projection method.

---

## 7. Taxonomy Axis E — ColorPolicy and Altered Dominant Policy

Color policy answers: **may the voicing add color tones not explicitly written in the chord symbol?**

Current color policy modes:

```text
chord_symbol_only
style_safe_extensions
altered_dominant
rich_reharm_color
```

Rules:

```text
chord_symbol_only       = use only chord tones and explicitly written tensions/alterations
style_safe_extensions   = allow style-safe added color such as 9/13 when authorized
altered_dominant        = allow altered dominant source families according to intensity/scope
rich_reharm_color       = reserved for richer reharm color policy
```

Altered dominant is not the same thing as ordinary harmonic expansion. It has its own intensity and scope:

```text
Intensity: off / light / medium / high / full
Scope: functional_dominants / resolving_v7 / secondary_dominants / static_blues_dominants / backdoor_dominants / all_dominants / llm_selected
```

Boundary rule: chart-symbol fidelity and seventh-chord identity are mandatory. A seventh chord expanded with color must preserve the original seventh-chord identity, especially the third and seventh.

---

## 8. Taxonomy Axis F — Register, Guard, Selector, and Voice-leading

Register and selection answer: **which legal candidate should actually be used?**

Owned by voicing:

```text
register_low / register_high
right_hand_low / right_hand_high
top_voice_low / top_voice_high
comfort_register_low / comfort_register_high
max_voicing_span
max_top_voice_leap
low-register single-note guard
source balance score
register guard score
voice-leading distance
top-voice continuity
method/texture stickiness
weighted selection
```

The selector may use prior voicing state to preserve continuity. It may not ask pattern or expression to repair a poor candidate.

Boundary rule: voice-leading is a voicing-selection responsibility. MIDI writer and gesture realization must not repair voice-leading after notes have been chosen.

---

## 9. Style Policy Summary

Style voicing policies are allowed to bias taxonomy axes. They are not allowed to generate notes.

| Style | Current voicing identity |
| --- | --- |
| Medium Swing | Mostly `open` / DROP-family, rootless jazz color, 4-note-centered, section/method texture stickiness. |
| Bossa Nova | Mostly `closed` / compact, clean rootless/guide-tone options, light color, tighter span. |
| Jazz Ballad | Mostly `spread`, `rooted_color`, 5-note-ish warmth, safe expansion on by default, stronger continuity/register guard. |

---

## 10. Known Structural Debt for the Next Voicing-Only Stage

This document does not fix these debts; it defines the boundary for fixing them safely.

```text
1. spread.py still owns too many concerns: lower recipes, upper projection, register gates, pilot gates, adapter/audit surfaces.
2. content_planner.py still combines many source-family gates, color permissions, and edge-case rules.
3. HarmonicRealizer still contains event-scoped voicing policy adaptation that could move into a voicing runtime policy-context adapter later.
```

Recommended voicing-only cleanup sequence:

```text
v2_6_5_engine_voicing_spread_boundary_split_plan
v2_6_6_engine_voicing_spread_lower_group_recipes_behavior_preserving_split
v2_6_7_engine_voicing_spread_upper_projection_adapter_behavior_preserving_split
v2_6_8_engine_voicing_runtime_policy_context_adapter_extraction
```

Each step should include behavior-signature tests and should avoid changing style weights or musical defaults unless explicitly requested.

---

## 11. Development Guardrail

When adding or modifying voicing behavior, first identify the axis being changed:

```text
ContentFamily?
RootSupportPolicy?
Density / FunctionalGrouping?
Disposition / ProjectionMethod?
ColorPolicy / AlteredDominantPolicy?
RegisterGuard?
Selector / VoiceLeading?
StylePolicy bias only?
```

If a proposed change cannot be assigned to one of those axes, it probably belongs to pattern, expression, gesture, realization, or a new clearly named voicing sub-boundary that must be documented before implementation.
