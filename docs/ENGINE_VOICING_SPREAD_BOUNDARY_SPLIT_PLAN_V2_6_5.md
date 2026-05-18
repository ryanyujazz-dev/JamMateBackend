# Engine Voicing SPREAD Boundary Split Plan V2.6.5

**Task:** `v2_6_5_engine_voicing_spread_boundary_split_plan`  
**Track:** `feature/engine-deepening`  
**Change type:** documentation + pre-split behavior-signature tests; no voicing retune and no listening-behavior change.

This document plans a behavior-preserving cleanup of `src/jammate_engine/core/voicing/disposition/spread.py`. It does not implement the split yet. The goal is to make SPREAD voicing safe to develop without allowing other layers to perform voicing work or allowing SPREAD to become a parallel voicing system.

---

## 1. Non-Negotiable Boundary

SPREAD is a voicing **disposition/projection** family. It owns lower/upper functional grouping, register/gap/span legality, and groupwise voice-leading for already selected pitch-role material.

SPREAD must not own:

```text
pattern rhythm selection
anticipation decisions
expression duration / velocity / pedal intent
MIDI note serialization
style-level pattern vocabulary
new chord parser / scale resolver
parallel content-planner source system
final repair of bad notes after realization
```

Allowed SPREAD dependencies:

```text
core.harmony material/chord parsing
core.voicing content planner resources
core.voicing color permission / harmonic-expansion gates
core.voicing closed/open projection resources for upper groups
core.voicing policy metadata needed to select spread contracts and guards
```

Forbidden future shortcuts:

```text
SPREAD invents its own rootless/color source family instead of reusing content planner
SPREAD writes expression/pedal metadata beyond notes-only audit facts
SPREAD reaches into style pattern files
SPREAD becomes Ballad-only and stops being a reusable disposition family
Pattern or expression modules import spread internals to make note choices
MIDI writer fixes SPREAD register mistakes after the fact
```

---

## 2. Current `spread.py` Responsibility Inventory

Current size:

```text
src/jammate_engine/core/voicing/disposition/spread.py ≈ 6580 lines
```

The file currently contains all of these responsibilities in one module:

| Responsibility | Current representative symbols | Owner after split |
| --- | --- | --- |
| Public contracts / dataclasses / enums | `SpreadGrouping`, `SpreadUpperSourceKind`, `LowerGroupRecipeId`, `SpreadRecipeContract`, `SpreadProjectionCandidate`, `SpreadProjectionResult`, `SpreadRuntimeGateDecision` | `spread/contracts.py` |
| Lower group inventory and placement | `lower_group_recipe_inventory`, `instantiate_lower_group_recipe`, `place_lower_group_recipe`, `_resolve_lower_group_degree_spec`, `_place_lower_group_offsets` | `spread/lower_groups.py` |
| Upper source reuse / adapter | `spread_upper_source_refs`, `adapt_spread_upper_source`, `adapt_spread_upper_sources_for_contracts`, `_plan_upper_source_content_recipes`, `_place_upper_source_for_spread`, `_place_closed_upper_stack_candidates` | `spread/upper_sources.py` |
| Register, gap, span, root-anchor guards | `SpreadProjectionRegisterPolicy`, `basic_spread_register_policy`, `_spread_register_policy_for_contract`, `_lower_group_register_window`, `_rooted_bass_anchor_passed`, `_basic_spread_projection_legality`, `_low_register_density_guard_passed` | `spread/register_guards.py` |
| Basic SPREAD projection | `project_basic_spread_contract`, `project_basic_spread_candidates`, `place_lower_upper_grouped_projection`, `place_foundation_projection`, `place_root_10th_projection`, `_dedupe_spread_projection_candidates` | `spread/projection.py` |
| Groupwise voice-leading | `SpreadGroupwiseVoiceLeadingWeights`, `score_spread_groupwise_voice_leading`, `rank_spread_candidates_by_groupwise_voice_leading`, `select_spread_candidate_by_groupwise_voice_leading` | `spread/voice_leading.py` |
| Runtime gate and selector facade | `spread_runtime_gate_from_policy`, `select_spread_candidate_with_runtime_gate`, `spread_candidate_selector_contract_debug` | `spread/runtime_gate.py` |
| Candidate-pool adapter to normal `VoicingCandidate` | `spread_projection_candidate_to_voicing_candidate_adapter`, `run_ballad_spread_runtime_adapter_skeleton`, conversion-boundary audit helpers | `spread/runtime_adapter.py` |
| Ballad runtime pilot / isolation controls | `BalladSpreadRuntimeEntryContract`, `resolve_ballad_spread_runtime_entry`, `build_ballad_spread_runtime_pilot_candidate_pool`, `guard_ballad_spread_pilot_runtime_enablement`, Ballad grouping mix helpers | `spread/ballad_runtime.py` |
| Debug/audit wrappers | `basic_spread_projection_debug`, `spread_recipe_contract_debug`, `lower_group_inventory_debug`, Ballad dry-run/debug helpers | stay near owner or `spread/audit.py` only if it reduces coupling |

This inventory is intentionally based on real current symbols so later split work can be reviewed mechanically.

---

## 3. Target Shape

The final path should preserve the existing import path:

```text
jammate_engine.core.voicing.disposition.spread
```

Recommended future package shape:

```text
src/jammate_engine/core/voicing/disposition/spread/
├── __init__.py              # public re-export compatibility surface
├── contracts.py             # dataclasses/enums/contracts only
├── lower_groups.py          # lower/foundation recipe inventory and placement
├── upper_sources.py         # content-planner/open-projection reuse adapters
├── register_guards.py       # register/gap/span/root-anchor legality
├── projection.py            # project_basic_spread_contract/candidates orchestration
├── voice_leading.py         # groupwise spread voice-leading scoring/selecting
├── runtime_gate.py          # generic spread runtime gate/select facade
├── runtime_adapter.py       # SpreadProjectionCandidate -> VoicingCandidate adapter
└── ballad_runtime.py        # Ballad pilot/isolation/candidate-pool policy only
```

Do not create all files in one pass unless a behavior-signature test proves unchanged output after each extraction. Prefer one extraction per version.

---

## 4. Public API Compatibility Rule

The following public imports must continue to work after the split:

```python
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_candidates
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_contract
from jammate_engine.core.voicing.disposition.spread import spread_recipe_contract_skeleton
from jammate_engine.core.voicing.disposition.spread import lower_group_recipe_inventory
from jammate_engine.core.voicing.disposition.spread import build_ballad_spread_runtime_pilot_candidate_pool
from jammate_engine.core.voicing.disposition import project_basic_spread_candidates
from jammate_engine.core.voicing import project_basic_spread_candidates
```

The split should therefore convert `spread.py` into a `spread/` package with `__init__.py` re-exporting the same public symbols, or otherwise preserve exactly the same public import contract.

---

## 5. Behavior-Signature Gates Before Any Split

Before moving implementation code, preserve these signatures with tests:

### 5.1 Contract skeleton signature

```text
spread_1plus3_contract → 1+3, density 4
spread_2plus2_contract → 2+2, density 4
spread_1plus4_contract → 1+4, density 5
spread_2plus3_contract → 2+3, density 5
spread_2plus4_contract → 2+4, density 6
spread_3plus3_contract → 3+3, density 6
spread_3plus4_contract → 3+4, density 7
```

### 5.2 Lower inventory signature

```text
lower_1note_root
lower_2note_root_7
lower_2note_root_3
lower_2note_root_5
lower_2note_3_7
lower_3note_root_5_upper_root
lower_3note_root_3_7
lower_3note_root_7_upper3
lower_3note_root_5_upper3
```

### 5.3 Projection behavior signature

Representative chords must keep their `project_basic_spread_candidates` contract ids, legal candidate counts, first legal notes/degrees/projection methods, and notes-only metadata stable.

Current representative chords:

```text
Cmaj7
Cmaj9
Dm7
G7b9
Bm7b5
```

The current first-legal-candidate signatures are captured in `tests/test_v2_6_5_engine_voicing_spread_boundary_split_plan.py`. Any future split must pass that test before being considered behavior-preserving.

---

## 6. Minimal Split Order

### v2_6_6 — Lower group extraction

Move only:

```text
LowerGroupRecipeId
LowerGroupDegreeSpec
LowerGroupRecipeInventoryItem
LowerGroupRecipeInstance
LowerGroupPlacement
lower_group_recipe_inventory
lower_group_recipe_by_id
instantiate_lower_group_recipe
place_lower_group_recipe
_resolve_lower_group_degree_spec
_place_lower_group_offsets
```

Do not move projection, Ballad runtime pilot, or adapter logic in this pass.

### v2_6_7 — Upper source adapter extraction

Move only:

```text
UpperSourceRef
SpreadUpperSourceOption
SpreadUpperSourceAdapterResult
spread_upper_source_refs
spread_upper_source_ref_by_id
adapt_spread_upper_source
adapt_spread_upper_sources_for_contracts
_plan_upper_source_content_recipes
_spread_upper_adapter_policy
_place_upper_source_for_spread
_place_closed_upper_stack_candidates
```

Keep upper source reuse dependent on `content_planner` and open/drop projection resources. Do not create a parallel upper-source family system.

### v2_6_8 — Register guard extraction

Move:

```text
SpreadProjectionRegisterPolicy
basic_spread_register_policy
_spread_register_policy_for_contract
_lower_group_register_window
_basic_spread_projection_legality
_rooted_bass_anchor_passed
_low_register_density_guard_passed
```

No weight, register value, or root-anchor target changes.

### v2_6_9 — Projection orchestration extraction

Move:

```text
project_basic_spread_contract
project_basic_spread_candidates
place_lower_upper_grouped_projection
place_foundation_projection
place_root_10th_projection
_dedupe_spread_projection_candidates
```

This is the pass where `spread.py` should become a compatibility re-export or `spread/` package initializer.

### v2_6_10 — Ballad runtime pilot isolation cleanup

Move Ballad-only entry/gate/candidate-pool helpers out of the generic SPREAD projection path:

```text
BalladSpreadRuntimeEntryContract
resolve_ballad_spread_runtime_entry
build_ballad_spread_runtime_pilot_candidate_pool
ballad grouping mix helpers
runtime enablement guard
selection/fallback audit helpers
safe dry-run helpers
```

Ballad-specific pilot logic must remain a policy/gate over generic SPREAD candidates, not a separate voicing engine.

---

## 7. What Must Not Change During Split

```text
source weights
style voicing policies
harmonic expansion policy
altered dominant policy
rootless/rooted color source behavior
lower group recipe availability
upper 4-note DROP2/DROP3-only rule inside SPREAD
SPREAD 3+4 lower recipe gate
Ballad spread pilot enablement guards
MIDI output timing/pedal/realization behavior
```

If any of these need to change, that is a listening-behavior task, not a projection cleanup task.

---

## 8. Validation Command Set

Minimum validation after each SPREAD split pass:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_5_engine_voicing_spread_boundary_split_plan.py \
  tests/test_v2_6_4_engine_voicing_taxonomy_boundary_hardening.py \
  tests/test_v2_6_2_engine_voicing_projection_cleanup.py
```

Recommended additional SPREAD regression group, excluding legacy version-only assertions where needed:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_2_40_basic_spread_projection.py \
  tests/test_v2_2_46_functional_grouping_1plus4_alignment.py \
  tests/test_v2_2_47_spread_runtime_adapter_skeleton.py \
  tests/test_v2_2_48_ballad_spread_runtime_candidate_pool.py \
  tests/test_v2_2_50_ballad_spread_runtime_enablement_guard.py \
  -k 'not version'
```

---

## 9. Continuation Instruction

Continue the voicing-only phase with `v2_6_6_engine_voicing_spread_lower_group_recipes_behavior_preserving_split`. Move only lower group inventory/placement from `spread.py` into a dedicated lower-group owner, preserve all public imports, pass the v2_6_5 behavior-signature tests, and do not change style policy, source weights, expression, pattern, realization, MIDI, Agent, or shared version files.
