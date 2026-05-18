# ENGINE VOICING SPREAD PROJECTION CORE SPLIT V2.6.9

**Task:** `v2_6_9_engine_voicing_spread_projection_core_behavior_preserving_split`  
**Track:** Engine / voicing-only  
**Change type:** behavior-preserving split  
**Primary owner:** `src/jammate_engine/core/voicing/disposition/spread_projection_core.py`

---

## 1. Purpose

This pass continues the SPREAD cleanup sequence after `v2_6_6` lower group extraction, `v2_6_7` upper source extraction, and `v2_6_8` register guard extraction.

The goal is to move the remaining basic lower+upper SPREAD projection orchestration into its own owner without changing listening behavior, source weights, style policy, harmonic expansion policy, altered-dominant policy, expression, pedal, MIDI timing, or pattern behavior.

SPREAD remains a **voicing disposition/projection** family. This pass only owns notes-only lower+upper projection construction.

---

## 2. New Owner

```text
src/jammate_engine/core/voicing/disposition/spread_projection_core.py
```

This file owns:

```text
SPREAD_PROJECTION_CORE_SPLIT_VERSION
project_basic_spread_contract
project_basic_spread_candidates
basic_spread_projection_debug
```

The owner orchestrates these already-separated voicing components:

```text
lower group recipes and placement     -> spread_lower_groups.py
upper source adapter                  -> spread_upper_sources.py
register / gap / span guard           -> spread_register_guards.py
SPREAD recipe contracts               -> spread.py compatibility surface for now
```

It returns notes-only `SpreadProjectionResult` / `SpreadProjectionCandidate` objects and must not convert them into runtime `VoicingCandidate` unless a separate runtime adapter explicitly asks for that.

---

## 3. Public API Compatibility Rule

`spread.py` remains the public compatibility surface for historic imports, but the implementation owner is now `spread_projection_core.py`.

These imports must continue to work:

```python
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_contract
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_candidates
from jammate_engine.core.voicing.disposition.spread import basic_spread_projection_debug
```

Package-level imports must also continue to work:

```python
from jammate_engine.core.voicing.disposition import project_basic_spread_contract
from jammate_engine.core.voicing.disposition import project_basic_spread_candidates
from jammate_engine.core.voicing.disposition import basic_spread_projection_debug
```

Those functions should report their implementation module as:

```text
jammate_engine.core.voicing.disposition.spread_projection_core
```

---

## 4. Boundary Rules

`spread_projection_core.py` may decide only these things:

```text
which SPREAD contract is projected
which lower recipe ids are attempted for that contract
which upper source options are tried for that contract
how lower and upper placed material are combined into a notes-only candidate
whether register/gap/span legality allows the candidate
how duplicate lower+upper candidate signatures are compacted
```

It does not own pattern, does not own expression, and does not own MIDI.

It must not decide:

```text
which rhythm/pattern event exists
whether anticipation happens
which expression/duration/velocity/pedal is used
which style should choose SPREAD over closed/open
which source family is globally preferred
which runtime candidate should win by voice-leading
which MIDI notes are written by the MIDI writer
```

Selection remains in selector / voice-leading. Source/content remains in content planning and lower/upper source owners. Register legality remains in `spread_register_guards.py`. The projection core only composes lower+upper notes-only candidates.

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

## 6. Demo Requirement

This pass also produces a listening demo to confirm that the split did not break the full MIDI output chain:

```text
demos/v2_6_9_misty_jazz_ballad_voicing_spread_projection_core_demo.mid
```

The demo is generated through the normal runtime path from the V2 Misty leadsheet with Jazz Ballad style and three choruses. It is not a separate hand-authored MIDI file.

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
create a new style-specific SPREAD rule
retune register ranges
convert notes-only SPREAD candidates into default runtime winners
```

---

## 8. Recommended Next Step

Continue voicing-only cleanup with:

```text
v2_6_10_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split
```

That pass should extract SPREAD groupwise voice-leading scoring/ranking from `spread.py`, while preserving the same frozen behavior signatures and listening demo path.
