# v2_6_16 Engine Voicing — Content Planner Boundary Split Plan

## Scope

`v2_6_16_engine_voicing_content_planner_boundary_split_plan` is a voicing-only audit and planning pass.

It is intentionally behavior-preserving relative to `v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup`:

```text
Do not change Pattern / Anticipation / Expression / Gesture / MIDI
Do not change API / Agent / HarmonyOS fixtures
Do not change Ballad 5-note:6-note target ratio
Do not re-enable 4-note 1+3 / 2+2 SPREAD defaults
Do not allow default maj7#11 safe extension
Do not split content_planner.py destructively in this pass
```

This pass answers one question:

```text
Before splitting core voicing content planning, which responsibilities must have stable owners?
```

## Current audit result

The current content source area is already partly separated:

```text
src/jammate_engine/core/voicing/sources/content_planner.py
src/jammate_engine/core/voicing/sources/color_permission.py
src/jammate_engine/core/voicing/sources/source_balance.py
src/jammate_engine/core/voicing/sources/upper_structure.py
src/jammate_engine/core/voicing/sources/four_note_sources.py
src/jammate_engine/core/voicing/sources/chord_tone_resolver.py
src/jammate_engine/core/voicing/sources/canonical_source.py
src/jammate_engine/core/voicing/sources/source_audit.py
```

But `content_planner.py` is still a broad orchestration file. It currently owns several different concern groups:

```text
1. public content planning API
   - VoicingContentRecipe
   - choose_content_families
   - plan_content_recipes
   - choose_degrees compatibility helper

2. chord-quality normalization
   - triad family normalization
   - root-support family filtering
   - seventh-chord identity preservation
   - half-diminished / diminished quality handling

3. source inventory assembly
   - shell+5 / shell+1-or-5 options
   - shell+color options
   - seventh-basic 1-3-5-7 options
   - rooted-color 4-note options
   - rootless A/B options
   - triad 4-note doubled-rotation options

4. global color admission glue
   - asks color_permission.py whether colors are allowed
   - applies style-safe extension / chord-symbol-only behavior
   - applies Ballad maj7 9/13 preference and #11 gate

5. altered dominant and explicit-symbol routing glue
   - altered dominant palette admission
   - explicit color fidelity
   - rootless/rooted color source variants

6. compatibility helpers
   - trim_content_degrees
   - choose_degrees
   - validity/debug note assembly
```

This is workable today, but future upper-structure, altered-dominant, density-aware content, and style/LLM semantic controls will make it hard to maintain if all concern groups remain in one file.

## Boundary model for the next split

The next actual code split should preserve public behavior while separating owners as follows.

### 1. Public planner facade

Candidate file:

```text
src/jammate_engine/core/voicing/sources/content_planner.py
```

Future role:

```text
public API / compatibility facade
orchestration only
no large source-family implementation blocks
```

Keep public imports stable:

```text
VoicingContentRecipe
choose_content_families
plan_content_recipes
choose_degrees
trim_content_degrees
source_preserves_seventh_chord_identity
seventh_chord_source_integrity_notes
```

### 2. Content family normalization owner

Candidate file:

```text
src/jammate_engine/core/voicing/sources/content_family_router.py
```

Responsibilities:

```text
choose valid ContentFamily list for a parsed chord and VoicingPolicy
normalize triad labels against chord quality
apply root-support policy before source inventory
prevent fake rootless voicing for no-seventh chords
keep seventh-chord identity requirements visible
```

Must not own:

```text
specific rootless A/B source rotations
specific altered-dominant palette contents
register / disposition / projection
style pattern or expression policy
```

### 3. Source inventory owner

Candidate file:

```text
src/jammate_engine/core/voicing/sources/content_source_inventory.py
```

Responsibilities:

```text
family -> degree source options
shell+5 / shell+color / seventh-basic / rooted-color / rootless A/B / triad-4note inventory
source-level validity notes
explicit-symbol color fidelity hooks
seventh-chord identity source gate hooks
```

Must continue using:

```text
color_permission.py for permission decisions
four_note_sources.py for canonical rotations / orientation helpers
chord_tone_resolver.py and harmony material for quality-correct degree spelling
upper_structure.py only as a source provider, not as a projection system
```

Must not own:

```text
weighted candidate selection
register placement
DROP/SPREAD projection
MIDI / expression / pedal behavior
```

### 4. Color permission owner

Existing file remains:

```text
src/jammate_engine/core/voicing/sources/color_permission.py
```

Responsibilities:

```text
ColorPermissionContext
chord-symbol-only vs style-safe-extension admission notes
explicit color fidelity
altered-dominant palette admission helper data
source_color_degrees
```

It should stay a permission/gate layer, not a source inventory or selector.

### 5. Source balance owner

Existing file remains:

```text
src/jammate_engine/core/voicing/sources/source_balance.py
```

Responsibilities:

```text
candidate source-family balance scores
altered-dominant intensity balance scores
rootless/rooted/basic/upper-structure source balance keys
```

It should stay scoring-only. It must not decide which source degrees exist.

### 6. Upper-structure owner

Existing file remains:

```text
src/jammate_engine/core/voicing/sources/upper_structure.py
```

Responsibilities:

```text
upper-structure source families
source-only degree recipes
harmonic-expansion / altered-dominant authorization for upper structures
explicit source debug metadata
```

It must continue to reuse existing closed/inversion/DROP projection capabilities. Upper Structure must not reimplement disposition projection.

## Non-negotiable behavior guardrails

The next split must preserve these current results:

```text
Ballad grouped SPREAD still targets about 5-note:6-note = 6:4
4-note SPREAD 1+3 / 2+2 remain retired from default Ballad runtime
7-note remains rare ending/climax thickness
plain Ballad maj7 prefers 9 / 13 and does not auto-generate unnotated #11
explicit maj7#11 chord symbols remain faithful
half-diminished shell+color uses chord-core b3+b7+b5 logic
seventh chords with expansion preserve original chord identity, especially 3 and 7
Upper Structure remains source-only and projection-reusing
```

## Recommended next code pass

```text
v2_6_17_engine_voicing_content_family_router_behavior_preserving_split
```

Suggested implementation order:

```text
1. Add content_family_router.py.
2. Move only family-choice / normalization helpers first.
3. Re-export through content_planner.py.
4. Freeze representative plan_content_recipes signatures before and after:
   - C
   - Cmaj7
   - Cmaj9
   - Cmaj7#11
   - Dm7
   - G7
   - G7b9
   - G7alt
   - Bm7b5
   - Bdim7
5. Do not move source inventory in the same pass.
6. Run Misty three-chorus audit to verify density/color behavior unchanged.
```

Rationale:

```text
Family routing is the safest first split because it is upstream of source inventory but small enough to verify.
Moving source inventory, altered-dominant variants, and explicit-color routing in the same pass would create too much behavior risk.
```

## Future split queue after v2_6_17

```text
v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split
v2_6_19_engine_voicing_content_planner_facade_cleanup
v2_6_20_engine_voicing_upper_structure_runtime_usage_gate_review
v2_6_21_engine_ballad_spread_listening_calibration_pass
```

`v2_6_21` is the earliest recommended point for another listening retune. Until then, keep structure and behavior changes separate.

## Validation added in this pass

Added:

```text
tests/test_v2_6_16_engine_voicing_content_planner_boundary_split_plan.py
```

Assertions:

```text
1. content planner boundary document exists
2. current owners are explicit and importable
3. content_planner.py has not drifted into Pattern / Expression / MIDI / Agent ownership
4. color_permission.py remains the color gate owner
5. source_balance.py remains source scoring owner
6. upper_structure.py remains source-only and projection-reusing
7. Misty three-chorus audit still preserves v2_6_14/v2_6_15 density/color guardrails
```
