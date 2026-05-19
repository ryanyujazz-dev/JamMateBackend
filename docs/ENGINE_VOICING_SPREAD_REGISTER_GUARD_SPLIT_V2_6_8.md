# ENGINE VOICING SPREAD REGISTER GUARD SPLIT V2.6.8

**Task:** `v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split`  
**Track:** Engine / voicing-only  
**Change type:** behavior-preserving split  
**Primary owner:** `src/jammate_engine/core/voicing/disposition/spread_register_guards.py`

---

## 1. Purpose

This pass continues the SPREAD cleanup sequence started in `v2_6_5` and implemented incrementally in `v2_6_6` / `v2_6_7`.

The goal is to move SPREAD register legality into its own owner without changing listening behavior, source weights, style policy, harmonic expansion policy, altered-dominant policy, expression, pedal, MIDI timing, or pattern behavior.

SPREAD remains a **voicing disposition/projection** family. This pass only extracts the guard logic that decides whether an already chosen lower+upper SPREAD placement is legal in register.

---

## 2. New Owner

```text
src/jammate_engine/core/voicing/disposition/spread_register_guards.py
```

This file owns:

```text
SpreadProjectionRegisterPolicy
basic_spread_register_policy
spread_register_policy_for_contract
lower_group_register_window
basic_spread_projection_legality
low_register_density_guard_passed
root_bass_note_from_lower
rooted_bass_anchor_passed
root_anchor_tail_span_guard_enabled
root_anchor_tail_span_guard_passed
upper_structure_root_shell_tail_gate_passed
spread_register_guard_debug
```

The owner is deliberately notes-only and voicing-only. It does not own pattern, does not own anticipation, does not own expression, does not own pedal, does not own gesture realization, does not own MIDI, and does not own style pattern selection.

---

## 3. Public API Compatibility Rule

`spread.py` remains the public compatibility surface for historic imports.

These imports must continue to work:

```python
from jammate_engine.core.voicing.disposition.spread import SpreadProjectionRegisterPolicy
from jammate_engine.core.voicing.disposition.spread import basic_spread_register_policy
from jammate_engine.core.voicing.disposition.spread import spread_register_guard_debug
```

Package-level imports must also continue to work:

```python
from jammate_engine.core.voicing.disposition import SpreadProjectionRegisterPolicy
from jammate_engine.core.voicing.disposition import basic_spread_register_policy
from jammate_engine.core.voicing.disposition import spread_register_guard_debug
```

---

## 4. Boundary Rules

`spread_register_guards.py` may decide only these things:

```text
lower register window
upper register window
rooted bass anchor window
whole-voicing register window
group gap min/max
overall span max
low-register density guard
upper-structure lower gate
root-anchor high-tail span guard
```

It must not decide:

```text
which rhythm/pattern event exists
whether anticipation happens
which expression/duration/velocity/pedal is used
which source family is preferred
which style should use SPREAD
which MIDI notes are emitted into the writer
whether a candidate should be selected by voice-leading weight
```

Selection remains in the selector / voice-leading layer. Source/content remains in content planning and upper/lower source owners. SPREAD register guard only says whether a placed lower+upper candidate is legal.

---

## 5. Behavior-Preserving Requirements

This pass must preserve the `v2_6_5` frozen SPREAD candidate signatures for:

```text
Cmaj7
G7b9
Bm7b5
```

The following must remain unchanged:

```text
candidate count per SPREAD contract
first legal candidate notes
first legal candidate degrees
upper projection method
density
group gap
notes_only / no_expression_or_pedal metadata
```

---

## 6. Why This Split Matters

Before this pass, `spread.py` still owned register policy, lower/upper guard windows, rooted bass anchor legality, low-register density guard, and whole-span guard. That made it hard to tell whether a later SPREAD issue came from:

```text
lower group recipe
upper source adapter
register legality
projection construction
voice-leading scoring
runtime pilot entry
```

After this pass, register legality has a dedicated owner, which makes future SPREAD cleanup safer.

---

## 7. Non-goals

This pass does not:

```text
change Ballad SPREAD listening behavior
change source weights
change style voicing policy
change harmonic expansion policy
change altered dominant policy
change expression/pedal/velocity/duration
change MIDI writer behavior
create a new style-specific spread rule
retune register ranges
```

---

## 8. Recommended Next Step

Continue voicing-only cleanup with:

```text
v2_6_9_engine_voicing_spread_projection_core_behavior_preserving_split
```

That pass should extract the remaining core lower+upper projection orchestration from `spread.py`, while preserving the same frozen behavior signatures.
