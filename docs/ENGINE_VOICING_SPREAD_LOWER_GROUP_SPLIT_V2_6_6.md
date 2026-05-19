# Engine Voicing SPREAD Lower Group Split V2.6.6

**Task:** `v2_6_6_engine_voicing_spread_lower_group_recipes_behavior_preserving_split`  
**Track:** `feature/engine-deepening`  
**Change type:** behavior-preserving split; no listening-behavior retune, no source-weight changes, no style-policy change, no MIDI/API/Agent/shared-version change.

This pass starts the SPREAD cleanup planned in V2.6.5 by extracting the lower/foundation group recipe inventory and placement logic out of `core/voicing/disposition/spread.py` while preserving public import compatibility.

---

## 1. Boundary Rule

SPREAD remains a voicing disposition/projection family. This pass only moved lower-group material that already belonged to SPREAD voicing projection:

```text
lower recipe ids
lower recipe dataclasses
lower recipe inventory
chord-quality-aware lower recipe instantiation
lower register placement / octave-span guard
lower inventory debug payload
```

The new owner must not perform work owned by other layers:

```text
Pattern       -> rhythm/event layout only
Anticipation  -> pitchless cross-region movement only
Expression    -> duration / velocity / articulation / pedal intent only
Gesture       -> projection of an already selected VoicingPlan only
MIDI writer   -> serialization only, not voicing repair
```

Forbidden in this task:

```text
no source-weight changes
no listening-behavior retune
no harmonic-expansion or altered-dominant policy changes
no pattern / anticipation / expression / gesture / MIDI ownership drift
no Ballad runtime pilot behavior change
no Agent/shared docs/version/API/frontend changes
```

---

## 2. Files Added

```text
src/jammate_engine/core/voicing/disposition/spread_contracts.py
src/jammate_engine/core/voicing/disposition/spread_lower_groups.py
```

`spread_contracts.py` owns small shared SPREAD contract enums/constants needed before a full package conversion:

```text
SPREAD_RECIPE_CONTRACT_VERSION
SpreadGrouping
SpreadUpperSourceKind
SpreadReuseStatus
```

`spread_lower_groups.py` owns the extracted lower/foundation group logic:

```text
LOWER_GROUP_INVENTORY_VERSION
LowerGroupRecipeId
LowerGroupDegreeSpec
LowerGroupRecipeInventoryItem
LowerGroupRecipeInstance
LowerGroupPlacement
lower_group_recipe_inventory
lower_group_recipe_by_id
instantiate_lower_group_recipe
place_lower_group_recipe
lower_group_inventory_debug
```

`spread.py` remains the public compatibility surface and re-exports these symbols, so existing imports still work:

```python
from jammate_engine.core.voicing.disposition.spread import LowerGroupRecipeId
from jammate_engine.core.voicing.disposition.spread import place_lower_group_recipe
from jammate_engine.core.voicing.disposition import lower_group_recipe_inventory
```

---

## 3. Behavior Preservation Contract

The V2.6.5 behavior signatures remain the guardrail for this pass:

```text
lower recipe inventory ids stay unchanged
Cmaj7 / G7b9 / Bm7b5 project_basic_spread_candidates signatures stay unchanged
notes_only / no_expression_or_pedal metadata stays unchanged
SPREAD public imports stay compatible
```

The split reduces direct responsibility inside `spread.py` without changing the generated candidate notes, degree order, projection method, group gap, or legal candidate counts for the frozen representative chords.

---

## 4. Current State After This Pass

Before:

```text
spread.py ≈ 6580 lines
```

After:

```text
spread.py              ≈ 6044 lines
spread_lower_groups.py ≈ 533 lines
spread_contracts.py    ≈ 42 lines
```

This is intentionally not a full `spread/` package conversion yet. The project currently keeps `spread.py` as the import-compatible module and extracts lower groups into a sibling owner file. A later pass may convert to a package only after behavior-signature tests cover all public exports.

---

## 5. What Still Belongs to Later Passes

Not moved in V2.6.6:

```text
upper source adapter logic
register/gap/span/root-anchor guards
basic projection orchestration
groupwise voice-leading
runtime gate / selector facade
candidate-pool adapter
Ballad runtime pilot / isolation controls
```

Recommended next task:

```text
v2_6_7_engine_voicing_spread_upper_projection_adapter_behavior_preserving_split
```

Goal: extract SPREAD upper-source adapter / reusable source-reference logic while keeping content planning, color permission, closed/open projection reuse, and candidate signatures unchanged.
