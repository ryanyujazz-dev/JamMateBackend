# Engine Voicing SPREAD Upper Source Split V2.6.7

**Task:** `v2_6_7_engine_voicing_spread_upper_projection_adapter_behavior_preserving_split`  
**Track:** `feature/engine-deepening`  
**Change type:** behavior-preserving split; no listening-behavior retune, no source-weight changes, no style-policy change, no MIDI/API/Agent/shared-version change.

This pass continues the SPREAD cleanup planned in V2.6.5 by extracting the upper source/orientation adapter out of `core/voicing/disposition/spread.py` while preserving public import compatibility and SPREAD candidate behavior.

---

## 1. Boundary Rule

SPREAD remains a voicing **disposition/projection** family. This pass only moved upper-source material that already belonged to SPREAD voicing projection:

```text
UpperSourceRef
SpreadUpperSourceOption
SpreadUpperSourceAdapterResult
upper source adapter policy
core content planner reuse
upper-structure source gateway
DROP2/DROP3-only upper 4-note projection method normalization
upper source debug metadata
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
src/jammate_engine/core/voicing/disposition/spread_upper_sources.py
```

`spread_upper_sources.py` owns the source-oriented upper adapter:

```text
UPPER_SOURCE_ADAPTER_VERSION
UpperSourceRef
SpreadUpperSourceOption
SpreadUpperSourceAdapterResult
adapt_spread_upper_source_from_ref
```

It also owns helper logic for:

```text
upper-structure enablement gates
upper-structure source identification
upper-structure lower-mode labels
core content-planner adapter policy
upper source projection-method normalization
DROP2/DROP3-only 4-note upper projection resource filtering
upper source functional source type / orientation metadata extraction
```

---

## 3. Public API Compatibility Rule

Existing public imports remain valid:

```python
from jammate_engine.core.voicing.disposition.spread import UpperSourceRef
from jammate_engine.core.voicing.disposition.spread import SpreadUpperSourceOption
from jammate_engine.core.voicing.disposition.spread import SpreadUpperSourceAdapterResult
from jammate_engine.core.voicing.disposition.spread import adapt_spread_upper_source
from jammate_engine.core.voicing.disposition.spread import spread_upper_source_adapter_debug
```

The package-level compatibility surface also remains valid:

```python
from jammate_engine.core.voicing.disposition import UpperSourceRef
from jammate_engine.core.voicing.disposition import adapt_spread_upper_source
```

`spread.py` is still the compatibility surface and contract aggregator. `spread_upper_sources.py` is the implementation owner for upper source adaptation.

---

## 4. Behavior Preservation Gates

The split is protected by tests that verify:

```text
public imports still point to the extracted owner objects
upper adapter result signatures remain unchanged for G7b9 and Cmaj7
SPREAD candidate behavior signatures remain unchanged for Cmaj7 / G7b9 / Bm7b5
spread_upper_sources.py does not import pattern / anticipation / expression / realization / MIDI / style modules
upper source adapter remains notes-only and source-oriented, not a final candidate generator
```

The upper adapter may reuse:

```text
core.voicing.sources.content_planner
core.voicing.sources.upper_structure
core voicing policy / color gates
OPEN-family DROP2 / DROP3 projection resource names for upper 4-note SPREAD blocks
```

It must not reuse:

```text
final CLOSED/OPEN VoicingCandidate placements
style pattern vocabulary
expression or pedal data
MIDI NoteEvent / PedalEvent
runtime repair paths
```

---

## 5. Current Split State After V2.6.7

Completed:

```text
spread_contracts.py      # shared SPREAD contract enums/constants
spread_lower_groups.py   # lower/foundation recipe inventory and placement
spread_upper_sources.py  # upper source/orientation adapter
```

Still inside `spread.py` and planned for later behavior-preserving passes:

```text
SpreadProjectionRegisterPolicy
SpreadProjectionCandidate / SpreadProjectionResult
basic_spread_register_policy
project_basic_spread_contract / project_basic_spread_candidates
score_spread_groupwise_voice_leading
select_spread_candidate_with_runtime_gate
spread_projection_candidate_to_voicing_candidate_adapter
Ballad spread runtime pilot / candidate pool
```

---

## 6. Recommended Next Step

```text
v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split
```

Next pass should extract only SPREAD register/gap/span guard policy and guard helpers. It should continue to preserve candidate signatures and avoid touching pattern, anticipation, expression, realization, MIDI, API, Agent, or shared version files.
