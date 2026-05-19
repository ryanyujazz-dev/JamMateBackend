## v2_6_31 Ballad SPREAD Lower/Upper Gap Audit Rule

The piano audit must expose grouped-SPREAD lower/upper gap behavior without reselecting notes.

Audit comfort band:

```text
2 <= lower/upper group gap <= 7 semitones
```

Required observational fields:

```text
lower_upper_gap_audit_version
lower_upper_group_gap_by_grouping
lower_upper_group_gap_by_density
lower_upper_group_gap_by_recipe
lower_upper_group_gap_too_tight_events_by_grouping
lower_upper_group_gap_too_wide_events_by_grouping
```

This audit is a voicing observability layer only. It must not change Pattern, Anticipation, Expression, Gesture, MIDI, or the current Ballad density lane.

## Voicing Rule Update: v2_6_28 Ballad SPREAD Top Voice / Register Micro Calibration

## v2_6_30 Jazz Ballad SPREAD voicing calibration

Jazz Ballad SPREAD now treats `1+4` as a low-frequency 5-note upper4 color lane. It is not a default comping body and must not leak through zero-weight compatible-neighbor routing. The main Ballad SPREAD body remains `2+3` for 5-note and `2+4` for 6-note, with `3+3` as a low-frequency 6-note thickness lane.

Current Misty / 3-chorus audit target: roughly 120 5-note events and 76 6-note events, with `1+4` around 4-10 events, 4-note SPREAD at 0, 7-note at 0 for the default seed, no unnotated maj7#11, and top register capped at or below 74.

Lower foundation groups should stay compact: lower group spans should remain within one octave, low-register density remains guarded, and audit must expose lower note range, lower span, recipe counts, and low-register events before further tuning.

---


`v2_6_28_engine_ballad_spread_top_voice_and_register_micro_calibration` adds a narrow selector-side micro bias for Jazz Ballad grouped SPREAD candidates.

The purpose is not to change the voicing system or density lane. The purpose is to avoid opening or isolated no-previous-state SPREAD choices that jump directly to the highest legal top register before top-line continuity has a previous voicing to compare against.

Current Ballad SPREAD ordinary runtime remains:

```text
2+3  stable 5-note body
2+4  fuller 6-note support
3+3  fuller 6-note support / lift
```

Still disabled by default:

```text
1+4  explicit upper4 color / isolation only
1+3  retired 4-note SPREAD
2+2  retired 4-note SPREAD
```

Guardrails after this pass:

```text
5-note:6-note remains near 6:4
4-note SPREAD remains 0
1+4 ordinary runtime remains 0
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
Misty max top note is capped at 74 for the reference seed
```

Recommended next task:

```text
v2_6_29_engine_ballad_spread_lower_foundation_register_micro_calibration
```

## v2_6_26 Voicing realization surface boundary note

`harmonic_realizer.py` is now explicitly treated as a thin realization surface. It may iterate active piano `PatternEvent`s, reset the request orchestrator cache at the start of a realization pass, delegate voicing plan requests, call `GestureRealizer`, own the returned `NoteEvent` list, and attach a surface-version marker to piano audit rows.

It must not construct degree sources, route content families, decide color permission, project closed/open/spread voicings, score/select voicing candidates directly, build `VoicingRequest` directly, own region voicing cache logic, build piano audit payloads directly, write MIDI, or apply expression.

Current realization owner map:

```text
harmonic_realizer.py                         # thin realization surface
realizer_voicing_request_orchestration.py    # VoicingRequest + region cache + resolver call
voicing_policy_context_adapter.py            # PatternEvent metadata -> event-scoped VoicingPolicy metadata
realizer_note_audit.py                       # piano audit rows / note debug / partial reattack trims
gesture_realizer.py                          # selected VoicingPlan -> NoteEvent projection
```

Guardrails remain unchanged:

```text
5-note:6-note ~= 6:4 for Ballad/SPREAD
4-note SPREAD default remains retired
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

Recommended next task:

```text
v2_6_27_engine_ballad_spread_listening_calibration_pass
```

## v2_6_25 Voicing realization boundary note

The request/cache owner is now `src/jammate_engine/realization/realizer_voicing_request_orchestration.py`.

Rule:

```text
HarmonicRealizer does not build VoicingRequest directly.
HarmonicRealizer does not own region voicing cache logic directly.
HarmonicRealizer does not call policy_with_event_voicing_context directly.
```

The current cache contract remains:

```text
one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices
```

Explicit fresh revoicing is allowed only through event or gesture metadata:

```text
force_fresh_voicing
revoice_within_region
```

This is a behavior-preserving boundary cleanup. It does not change Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, or shared docs.

---

## v2_6_24 Voicing realization boundary note

The harmonic realization boundary now separates voicing request orchestration from note/audit/debug payload construction:

```text
harmonic_realizer.py        # VoicingRequest / resolver / gesture realizer orchestration
realizer_note_audit.py      # piano audit rows, note debug payloads, partial reattack NoteEvent trims
```

`realizer_note_audit.py` is not a voicing source, color, projection, selector, expression, or MIDI owner. It may only consume already-selected PatternEvent / Expression / VoicingPlan / NoteEvent data.

## v2_6_23 Harmonic realizer policy/context adapter cleanup

- No musical rule, density, pattern, expression, MIDI, or API behavior changed in this pass.
- `voicing_policy_context_adapter.py` now owns only event-scoped policy/context metadata translation for voicing requests.
- `harmonic_realizer.py` should not directly own harmonic-context, texture-scope, Ballad SPREAD grouping-mix, or SPREAD expansion-ratio helper logic.
- The adapter does not construct degree sources, does not decide color permission, does not project closed/open/spread voicings, and does not score or select candidates.
- Jazz Ballad guardrails remain: 4-note SPREAD disabled, 5-note:6-note ~= 6:4, and maj7#11 remains off by default unless explicit/written/intent-enabled.

## v2_6_22 Voicing cleanup — retired SPREAD pilot logic

- Retired Jazz Ballad SPREAD pilot / dry-run / safe-dry-run / runtime-guard logic has been deleted from the active voicing surface.
- Current Ballad SPREAD generation uses grouped SPREAD runtime candidate pools directly: event-level grouping-mix policy chooses compatible SPREAD contracts, projection core creates notes-only candidates, runtime adapter maps legal projection candidates to `VoicingCandidate`, and selector performs groupwise voice-leading.
- This pass does not change Pattern, Anticipation, Expression, Gesture, Pedal, Timing, MIDI, Agent, API, or HarmonyOS behavior.
- Default Misty Ballad audit remains: 4-note SPREAD disabled, 5-note / 6-note near 6:4, maj7#11 absent unless explicit/written/intent-enabled.


## v2_6_15 Voicing/SPREAD runtime-boundary rule

SPREAD runtime gate and adapter are now separate voicing owners:

```text
spread_runtime_gate.py      # whether notes-only SPREAD projection may be queried
spread_runtime_adapter.py   # explicit SpreadProjectionCandidate -> VoicingCandidate field mapping
spread.py                   # compatibility facade; should not regain runtime gate/adapter implementation body
```

The gate does not imply adapter conversion. The adapter does not imply candidate-generator wiring. Neither layer may choose patterns, anticipation, expression, pedal, gesture, or MIDI behavior.

Ballad/SPREAD density calibration remains: 5-note and 6-note should stay near 6:4 in the Misty three-chorus audit, with 4-note SPREAD default disabled and maj7#11 absent unless explicitly requested or written in the chart.

# v2_3_9 Pedal / Expression Rule Update
Pedal is an expression-layer contract. Patterns expose facts such as tail availability, density, anticipation eligibility, and harmonic rhythm; Expression chooses `none/light/sustain/lush`; MIDI realizer only materializes approved CC64 with re-pedal offset. Bossa/Swing stay dry by default; Ballad may use balanced pedal with chord-change re-pedal.
# Generation Rules Summary V2 — Compact
Current version: `v2_6_8`.
Generation Rule Documentation Principle: every code-level generation rule change must update this file. 生成规则 includes style vocabulary, role/domain generation, anticipation, expression, voicing choice, BassFoundation, percussion, and MIDI timing interpretation.



## v2_6_8 Engine Voicing SPREAD Register Guard Split

- No runtime music-generation behavior changed in this pass.
- `spread_register_guards.py` now owns SPREAD register/gap/span legality: `SpreadProjectionRegisterPolicy`, lower/upper register windows, rooted bass anchor guard, low-register density guard, group gap guard, and overall span guard.
- `spread.py` remains the public compatibility surface and re-exports the register guard API; existing imports from `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition` continue to work.
- The register guard owner remains notes-only and voicing-only. It does not own Pattern, Anticipation, Expression, Gesture, MIDI writer, velocity, duration, or pedal decisions.
- v2_6_5 frozen behavior signatures for representative SPREAD candidates are preserved.

## v2_6_7 Engine Voicing SPREAD Upper Source Split

- No runtime music-generation behavior changed in this pass.
- `spread_upper_sources.py` now owns SPREAD upper source refs, options, adapter result dataclasses, source-oriented adapter policy, upper-structure source gate helpers, upper-source metadata extraction, and DROP2/DROP3-only upper 4-note method normalization.
- `spread.py` remains the public compatibility surface and re-exports the upper-source API.
- The upper source owner remains notes-only and source-oriented; it does not own lower placement, register legality, voice-leading, expression, gesture, or MIDI writer behavior.
- v2_6_5 frozen behavior signatures for representative SPREAD candidates are preserved.


## v2_6_4 Voicing taxonomy and boundary hardening

- No runtime music-generation behavior changed in this pass.
- Added the formal voicing taxonomy and boundary document: `docs/ENGINE_VOICING_TAXONOMY_AND_BOUNDARY_HARDENING_V2_6_4.md`.
- Voicing axes are now documented as: ContentFamily, RootSupportPolicy/BassRelation, Density/FunctionalGrouping, Disposition/ProjectionMethod, ColorPolicy/AlteredDominantPolicy, RegisterGuard, and Selector/VoiceLeading.
- Boundary baseline: only Voicing selects concrete vertical pitch content, density, grouping, disposition, register, and voice-leading. Pattern remains pitchless, Anticipation rewrites only pitchless events, Expression owns duration/velocity/articulation/touch/pedal intent, Gesture projects an already selected VoicingPlan, and MIDI writer only serializes resolved events.
- Style pattern files must not import concrete voicing selection internals or bind content families/dispositions. Style `voicing_policy.py` files may bias VoicingPolicy only.

## v2_6_3 MIDI output pipeline boundary audit

- No runtime music-generation behavior changed in this pass.
- Added the formal input/output boundary document for the current MIDI output chain: `docs/ENGINE_MIDI_OUTPUT_PIPELINE_BOUNDARY_AUDIT_V2_6_3.md`.
- Boundary baseline: PatternEvent remains pitchless; Anticipation rewrites only the pitchless timeline; Expression owns duration/velocity/articulation/touch/pedal intent; Voicing owns concrete vertical pitch content/density/disposition/voice-leading; Gesture projection maps already-selected voicing notes into NoteEvent objects; Timing owns swing/humanization performed placement; Pedal CC64 realization materializes expression pedal intent; MIDI writer only serializes resolved note/controller events.

## v2_5_9 V1 instrument-rule deep audit mapping

This documentation-only pass does not alter runtime generation. It establishes the formal rule that V1 is a musical-behavior reference only. Future style improvements must map V1 facts into V2 owners:

- Jazz Ballad piano: phrase intent + gesture + expression + voicing intent, not V1 phrase-engine migration.
- Jazz Ballad bass: anchor-path policy first; ornaments second; no walking by default.
- Jazz Ballad drums: semantic brush policy dimensions first; no generic fixed brush loop.
- Medium Swing piano: conversation/statement-answer and 4& rarity; no mechanical offbeat habit.
- Medium Swing bass: three-beat skeleton + beat-4 connector + rare scene-gated classic fill branch.
- Bossa piano: core batida identity anchor, Class A/B ratio, anticipation separated from rhythm cells.
- Bossa bass/percussion: root-fifth two-feel and shaker/cross-stick/kick groove identity.

Focused doc: `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.

## v2_5_8 Jazz Ballad default swing-8 and anticipation timing

- Jazz Ballad timing policy now defaults to `feel=swing`; written `.5` upbeats remain logical pattern-grid positions but render at the triplet/swing `2/3` point by default.
- Ballad anticipation keeps the pitchless logical `4&` placement (`target_offset_beats=-0.5`) but sets `timing_intent=swing_upbeat`, `timing_grid=swing_triplet_upbeat`, `performed_lead_in_beats=1/3`, and `expected_upbeat_fraction=2/3`.
- Pattern still must not write literal `0.666...`; Timing owns performed placement, Anticipation owns pitchless movement, and Expression consumes the performed lead-in for tied anticipated duration.
- This supersedes the v2_5_6 temporary scoped `1&` patch: Ballad swing-8 is now the default feel, not a one-pattern exception.
- Focused doc: `docs/JAZZ_BALLAD_DEFAULT_SWING8_ANTICIPATION_TIMING_PATCH_V2_5_8.md`.

## v2_5_7 Jazz Ballad 1& sustain continuity

- Ballad pattern candidates still write logical `0.5` for written `1&`; event metadata may request `timing_intent=swing_upbeat` so rendering performs it at `2/3`.
- Expression duration clamping now respects this declared timing intent when measuring the next same-track gap, so a beat-1 anchor sustains into the performed swing `1&` instead of releasing at the logical `0.5` grid point.
- `soft_whisper` is sustained/light, not short/staccato. Ballad near-downbeat touch should connect, not sound clipped.
- Ownership remains V2-native: Pattern stores grid and timing intent; Timing owns performed placement; Expression owns duration/articulation; MIDI does not repair the gap after the fact.
- Focused doc: `docs/JAZZ_BALLAD_1AND_SUSTAIN_CONTINUITY_BUGFIX_V2_5_7.md`.

## v2_5_3 Jazz Ballad phrase-intent foundation

- Jazz Ballad piano comping now exposes phrase-intent metadata inside the existing style-owned pattern library: `phrase_family`, `phrase_function`, `phrase_slot`, `context_gate`, and `gesture_intent`.
- Initial phrase families are `warm_pad`, `breath_answer`, `two_chord_soft_marks`, and context-gated `major_251_stable_cadence`. The prior v2_5_0 retouch cells remain available only as `temporary_low_level_fallback`.
- `breath_answer` and `major_251_stable_cadence` may request approved pitchless `inner_movement` gestures. These requests do not select notes, source degrees, voicing texture, duration, velocity, pedal, or MIDI repair behavior.
- `major_251_stable_cadence` is gated by the existing `core/harmony/harmonic_context.py` classifier for a conservative current-dominant `major_ii_v_i` window such as `Dm7 -> G7 -> Cmaj7`; no new progression recognizer was added.
- Default deterministic no-rng Ballad comping still selects the warm-pad anchor. Inner movement realization is available from `v2_5_4`; `v2_5_5` adds a narrow two-beat soft-mark timing correction.
- Focused doc: `docs/JAZZ_BALLAD_PHRASE_INTENT_FOUNDATION_V2_5_3.md`.

## v2_5_2 Jazz Ballad gesture contract foundation

- Jazz Ballad `gesture_policy.py` now explicitly allows only three gesture kinds for the style contract: `simultaneous_onset`, `inner_movement`, and `rolled_onset`. `arpeggiated_onset` / broken-chord behavior is still not opened for Ballad by default.
- `inner_movement` is a pitchless GestureRequest carrying abstract motion/projection intent such as `motion_shape`, `target_voice_class`, `attack_scope`, `held_voice_policy`, and `rearticulation_scope`. It must not contain MIDI notes, final duration/velocity/pedal, or voicing texture/source decisions.
- `rolled_onset` is opened only as a projection gesture over an already-selected voicing. It may specify abstract projection refs and offset shape, but it must not choose cadence color, voicing texture, or concrete notes.
- Default Jazz Ballad comping/runtime selection is intentionally unchanged in this pass; v2_5_0 retouch cells remain temporary fallback until phrase-intent and partial-reattack realization are implemented.
- Focused doc: `docs/JAZZ_BALLAD_GESTURE_CONTRACT_FOUNDATION_V2_5_2.md`.

## v2_5_1 V1 musical-rule absorption / V2-native mapping

- No runtime generation behavior changes in this pass. The purpose is to prevent the next music pass from becoming V1 code migration or more low-level onset-cell accumulation.
- V1 may be studied as a musical-rule source only. Useful rules must be translated into V2 owners: Pattern = pitchless timing/roles; Gesture = inner movement, rolled onset, partial reattack, fill/ornament projection; Expression = duration/velocity/touch/pedal; Voicing = concrete vertical notes and projection map; MIDI = materialization only.
- Jazz Ballad direction changes from adding more `soft_retouch`-style cells to phrase/gesture semantics: warm pad, breath answer, two-chord soft marks, major 251 stable cadence, held foundation + inner/color movement, and later gated 251 color families.
- Inner movement is explicitly a Gesture concern, not an ordinary pattern or voicing hack. Future Ballad pattern candidates may request `GestureKind.INNER_MOVEMENT` or `ROLLED_ONSET` through pitchless metadata, but must not choose MIDI notes, final expression, or voicing texture.
- Ballad bass should evolve toward restrained anchor paths: beat-1 foundation/root, beat-3 fifth/third/seventh/root/hold, rare beat-4 setup and rarer 4& approach. It must not become generic walking.
- Medium Swing should recover phrase feel through statement/answer, call-response, tail, Charleston/reverse-Charleston, and dominant-resolution semantics while keeping 4& push rare.
- Bossa should preserve identity anchors: core batida `1, 2, 3&`, Class A dominance, independent anticipation, distance-aware articulation, and root-fifth bass behavior.
- Focused doc: `docs/V1_MUSICAL_RULES_TO_V2_NATIVE_MAPPING_V2_5_1.md`.

## v2_5_0 Jazz Ballad comping motion update

- Jazz Ballad piano no longer uses only a single full-bar downbeat sustain candidate. The highest-weight anchor remains `ballad_piano_soft_downbeat_sustain`, but the style library now also exposes pitchless light-retouch candidates for downbeat + beat 3, downbeat + beat 3&, and downbeat + beat 1&.
- Two-beat chord regions use local Ballad candidates only: a soft anchor or downbeat + beat-2 retouch inside the region. This prevents multi-chord bars from inheriting four-beat retouch events that would cross the harmonic boundary.
- All Ballad comping candidates remain pitchless style vocabulary. Core voicing still owns note choice, and core expression still owns duration, velocity, articulation, release, and pedal realization.
- New Ballad expression intents are `soft_retouch`, `soft_answer`, and `soft_whisper`. They are intentionally lighter than `soft_sustain`, and the expression resolver may still clamp duration before the next same-track event.
- This pass does not change Agent/LLM workflow behavior.

## BassFoundation
- Package owner: `generation/bass_foundation` with `generator.py`, `audit.py`, `policy.py`, `rules.py`.
- Each chord region line is guarded by `max_region_span=12` / `max_region_span`.
- Beat-4 continuity uses `target_nextR_note`; lane types include `scale_near_nextR`, `approach_nextR`, and `dominant_connection`.
- ThreeBeatSkeleton table preserves old-engine weights: `"scale_near_nextR": 40.0`, `"approach_nextR": 40.0`, `"dominant_connection": 10.0` = `40 : 40 : 10`.
- R-R-starting skeletons / `R-R-*` include `C03_R_R_Fifth`, `C05_R_R_Third`, `C11_R_R_Seventh`, and repeated-root metadata: `repeated_root_exact`, `repeated_root_notes`, `repeated_root_violations`.
- Lane instance selection keeps `"lane_instance_selection": "legacy_random"` / `legacy random` where documented.
- Preflight filters illegal skeletons before weighted choice: `candidate_preflight`, `old_engine_legal_skeleton_pool`.
- Root echo policy uses `root_echo_probability`, `root_echo_compact_probability_multiplier`, conservative root echo density, exact same current-root note, logical grid, and `timing_intent`.
- Classic fill `CF_TWO_BAR_TONIC_01` is scene-triggered by `bass_foundation_fill_scene` / `classic_fill_scene`, guarded by `classic_fill_enabled` and `classic_fill_min_gap_regions`.
## Style/domain rules
- Patterns are pitchless; MIDI notes are never emitted by style files.
- Swing timing is interpreted in render pipeline; style patterns use logical `.5` upbeats.
- Anticipation moves next beat-1 only when previous tail slots allow it.
- Expression owns sustain/short/staccato/velocity/pedal, after anticipation.
## Voicing generation rules
- Chord-symbol-only mode must not invent unstated color. Explicit chart colors are honored. Harmonic expansion can add richer colors when enabled.
- 3-note and 4-note closed verification: `root-third-fifth`, per-source nearest, no-seventh symbols use real triad/add/sus sources, `1351`, `3513`, `5135`, `F3 / MIDI 53`.
- Rootless A/B and source families are governed by `VOICING_SYSTEM_V2_DESIGN.md`.
## SPREAD voicing notes planning
SPREAD notes are core voicing rules, not pattern or expression rules. Current plan: lower/upper grouped projection, 1-note lower root only, 2-note lower `root+7/root+3/root+5/3+7`, 3-note lower `root+5+upper_root/root+3+7/root+7+upper3/root+5+upper3`, 5-note `1+4` and `2+3`, and separated lower/upper voice-leading. Existing source/orientation/color/drop resources may be reused, but final placed closed/open voicings must not be copied as SPREAD placements.
## Compact shipped-contract alias index
This index preserves stable contract names for regression tests while avoiding old rolling task prose. Tokens: 生成规则梳理总结; Medium Swing / BassFoundation; ThreeBeatSkeleton; Five-zone register model; Seventh Bias Audit; Target Continuity Audit; 代码落位; 规则包组织方式; Pattern rules; Voicing rules; Expression rules; Timing rules; Current known; Style rule baseline docs and formal tuning entry point through `v2_0_46`; v2_0_46 Style Rule Baseline Docs + Tuning Entry Point; STYLE_RULE_BASELINE_V2.md; STYLE_TUNING_ENTRY_POINT_V2.md; Medium Swing Piano baseline; Bossa Piano baseline; Jazz Ballad Piano baseline; v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1; piano musical audit; expression audit; v2_1_4 rooted foundation component; root; foundation component; rooted foundation component; standalone; 2-note standalone voicings; Do **not** treat `root + 3 / 10` as an independent 2-note tuning class; Rooted dyad component pool, not standalone review targets; foundation/support component for 4/5/6-note recipes; v2_1_5; shell_plus_5; shell_plus_1or5; 3rd + 7th + 5th; 3 + 7 + 5; not a triad; v2_1_6; specified color; shell_plus_specified_color; v2_1_7; expanded shell color; harmonic expansion; v2_1_8; superseded; v2_1_9; _color_minor_second_direction_adjustment; move color toward the other shell; v2_1_10; rootless_ab_safe; chord_symbol_has_explicit_color; rootless_ab_explicit_chord_symbol_color_used; rootless_ab_harmonic_expansion_enabled; rootless_ab_content_type_halfdim_with_9; v2_1_11; HarmonicExpansionPolicy; VoicingColorPolicy; harmonic_expansion_enabled; color_policy_mode; chord_symbol_only; explicit_chord_symbol_color; v2_1_12; rootless A/B orientation; canonical source; canonical_closed_position_source; rootless_A; rootless_B; rootless_ab_inversion_weight; 3579; 7935; with_5; with_13; v2_1_13; minor 13 modal gate; Locrian; Half-diminished is not a separate rootless source; v2_1_15; canonical inversions; v2_1_16; Voicing Source Module Boundary Cleanup; source_balance.py; No new subfolder; Minimal File Split Principle; v2_1_17; rootless_ab_average_pitch_target_low; rootless_ab_average_pitch_target_high; v2_1_18; halfdim Locrian rootless A/B; v2_1_19; basic_4note_root_third_fifth_seventh; root-third-fifth-seventh; v2_1_20; altered_dominant_rootless; rooted/rootless altered color families; v2_1_21; harmonic expansion cleanup; v2_1_22; functional source degree naming; v2_1_23; basic_4note_source_family; basic_4note_source_role_order; v2_1_24; four_note_color_gate; v2_1_27; four_note_allowed_color_set_contract_v2_1_27; chart_color_fidelity; explicit_chart_color; explicit_chart_color_plus_harmonic_expansion; v2_1_37; Do not generalize v2_1_37 immediately; v2_1_40; 3-note closed listening verification; root-third-fifth; per-source nearest; no-seventh symbols use real triad/add/sus sources; v2_1_42; 4-Note Triad-Aware Closed Source Sync; 1351; 3513; 5135; sus2, density=4, closed; closed register floor down by a major third; F3 / MIDI 53; v2_1_43; source_balance.py; Current audit version: `v2_2_10`; Source-of-truth matrix; Documentation update policy; Canonical reading path; No new docs subfolder is needed; v2_1_44; Current plan version: `v2_2_5`; closed legality filter; per-source nearest-motion realization; 1351 / 3513 / 5135; v2_2_0; v2_2_1 — Disposition Projection Entry Pass; v2_2_5; v2_2_8; OPEN method candidate pool rule; v2_2_8 Progression / Phrase-level Voicing Method Lock Contract; VoicingMethodLockSpec; auto_method_lock_scope_enabled; open_projection_method_pool; active_open_projection_method; method_lock_follow_metadata_from_seed_candidate; v2_2_10; method_lock_rescue_runtime_enabled; v2_2_12; harmonic_context_adapter; metadata_harmonic_context_adapter; harmonic_context_backed_method_lock_scope_adapter_v2_2_14; v2_2_14; method_lock_seed_then_follow_runtime_wiring_v2_2_14; method_lock_rescue_planning_v2_2_14; method_lock_filtered_all_candidates; v2_2_20; v2_2_21; VoicingTextureIntent; VoicingTextureState; VoicingTexturePlan; VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> DispositionGenerator -> VoiceLeadingScorer; derive_voicing_texture_intent; derive_voicing_texture_state; voicing_texture_state_engine_resolved_contract_v2_2_21; default listening behavior unchanged; the next engineering target should be selected by the user.
## v2_2_38 Medium Swing texture contrast rule
Medium Swing now attaches section/chorus texture intent metadata before voicing resolution. A normal A section remains `baseline_open_swing`; a bridge exposes `bridge_open_contrast` with slightly wider semantic `width`; the final chorus exposes `final_chorus_open_lift` with slightly higher semantic energy/density. This is debug/contract planning only: OPEN family filtering, OPEN method weights, MethodLock, and nearest-motion rescue remain the active runtime behavior.
## Additional compact compatibility aliases
generation/bass_foundation/; Do not add more core infrastructure; No BassFoundation retune; 3-note; 5-note; 6-note; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; m7 + 13; m7b5; m11b5; b3 + b7 + b5; shell_plus_expanded_color; supersedes; replaces; directed minor-second; directed m2; runtime_filtering_enabled=True; HarmonicContext-backed Method Lock Scope Adapter; Seed-Then-Follow; Method Lock Rescue; Method Lock Rescue Runtime; OpenProjectionMethod.DROP2; ii-V; V-I; ii-V-I; progression_phrase_voicing_method_lock_planning_only; locked_method; open_projection_method; boundary_test_source; DROP2 Audit Fixture; open_drop2_parent_closed_degrees; docs/ARCHITECTURE_V2.md; docs/PIPELINE_V2.md; docs/SYSTEM_CONTRACTS_V2.md; docs/API_CONTRACT_V2.md; docs/GENERATION_RULES_SUMMARY_V2.md; docs/STYLE_RULE_BASELINE_V2.md; docs/STYLE_TUNING_ENTRY_POINT_V2.md; docs/DEVELOPMENT_TASK_PLAN_V2.md; docs/DEVELOPMENT_HARNESS_V2.md; docs/NEW_FILE_PLACEMENT_GUIDE_V2.md; docs/FUTURE_IDEAS_BACKLOG_V2.md; docs/VOICING_MODULE_FILE_AUDIT_V2.md; docs/PROJECT_DOCUMENTATION_AUDIT_V2.md; docs/CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md; docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md; generate_closed_34note_baseline_smoke_listening.py; generate_3note_closed_listening_verification_demos.py; generate_4note_source_weight_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos; closed_34note_baseline_smoke_summary; 4-note triad-aware closed listening; closed register downshift; closed legality; avg_closed_4note_source_collapse_distance; closed_3note_closed_legality_then_nearest_motion; closed_3note_per_source_minimum_motion; closed_4note_per_source_minimum_motion; closed_4note_minimum_motion_events; closed_voicing_lowest_note_floor; min_closed_voicing_lowest_note; max_closed_voicing_span; max_density; min_density; preferred_density.

## v2_6_7 update — SPREAD upper source adapter split
- SPREAD upper source/orientation adaptation is now owned by `core/voicing/disposition/spread_upper_sources.py`.
- The adapter remains notes-only and source-oriented: it reuses core content-planner/color/upper-structure source resources and DROP2/DROP3 method names, but it must not reuse final CLOSED/OPEN placements as SPREAD placements.
- Public compatibility remains through `core.voicing.disposition.spread` and `core.voicing.disposition`.
- This is behavior-preserving: no source weights, style policies, pattern, expression, gesture, realization, pedal, MIDI, API, Agent, or shared version files changed.

## v2_2_56 update — Ballad SPREAD 1+3 Pilot + Demo
- SPREAD `1+3` is an explicit listening/audit candidate: lower/foundation group = root only; upper/projection group = existing 3-note content source/oriented upper stack.
- The combined 1+3 voicing must preserve seventh-chord identity under the global v2_2_54 source-integrity gate; seventh chords cannot become triad/add shapes that drop the defining 3/7.
- This is not a default Ballad retune; future lower+upper groupings continue one at a time with standard-tune demo review.
## v2_2_55 update — Ballad SPREAD 1+4 Upper DROP2/DROP3 Only Audit
- `SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION = "v2_2_55"`: SPREAD upper 4-note blocks explicitly reuse only OPEN DROP2 / DROP3 projection resources. OPEN DROP2&4 remains available for OPEN-family listening and style policies, but it is intentionally excluded from SPREAD upper 4-note blocks because SPREAD already owns a lower+upper grouping and gap/span guard.
- The restriction is enforced at the SPREAD adapter boundary: even if a future config accidentally passes DROP2&4 into an upper 4-note reference, SPREAD filters it back to DROP2/DROP3 and emits metadata `spread_upper_4note_drop2_and_4_allowed=false`.
- Listening/audit demo: `v2_2_55_misty_jazz_ballad_spread_1plus4_upper_drop2_drop3_only_audit_demo.mid`; audit summary: `v2_2_55_misty_jazz_ballad_spread_1plus4_upper_drop2_drop3_only_audit_summary.json`.
- Next lower+upper grouping work should proceed one grouping or a small coherent group at a time, each with a standard-tune listening demo for user review before mixing into broader Ballad SPREAD defaults.
## v2_2_54 update — Global Seventh-Chord Expansion Source Integrity Gate
- `GLOBAL_SEVENTH_CHORD_EXPANSION_SOURCE_INTEGRITY_GATE_VERSION = "v2_2_54"`: global voicing source gate for CLOSED/OPEN/SPREAD/future grouped voicings. Seventh-chord expansions preserve 3+7 identity (and half-dim/dim keep b5); triad/add paths may keep `1-3-5-9`, but seventh chords use sources such as `1-3-7-9`, `1-3-7-13`, `3-5-7-9`, `3-13-7-9`. Demo: `v2_2_54_misty_jazz_ballad_global_source_integrity_demo.mid`.
## Final compact compatibility aliases
A-B-A; B-A-B; Dorian; modal; 3-5-7-9; 7-9-3-5; 5-7-9-3; 9-3-5-7; Content Recipe; ContentRecipe; Register Center; register center; b9; b13; 1357; 1-3-5-7; color_permission.py; four_note_sources.py; SEVENTH_BASIC altered-dominant compatibility path has been removed; 4-Note Source Weight Implementation / Listening Prep Pass; 4-Note Source Weight Listening Verification Pass; 3-note functional closed; no partial fallback; 2-note Guide-Tone Shell; Rule Change Documentation Sync Standard; 不能只改代码、不改规则文档; root/1; root / 1; shell+1/root; 1251; 2512; 5125; docs/VOICING_SYSTEM_V2_DESIGN.md; docs/VOICING_MODULE_CORE_LOGIC_V2.md; docs/VOICING_TUNING_WORKFLOW_V2.md; Voicing Source Module Boundary Cleanup; _four_note_color_permission_notes; from .color_permission import; from .four_note_sources import; source_family_weights; mode-aware gate buckets; four_note_source_balance_gate_modes; four_note_source_balance_keys; source_family; source_type; source weight; altered dominant; compatibility path; root_third_fifth_seventh; root_third_fifth_sixth; root_fourth_fifth_seventh; root_third_fifth_ninth; root_third_ninth; root_third_seventh_altered_color; root-third-fifth-sixth; root-third-seventh-altered-color; rooted_color_4note; rooted_color_4note_source_family; rooted_color_4note_functional_content_type_; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; rootless_ab_inversion_index; rootless_ab_inversion_prior_score; rootless_ab_degree_order; basic_4note_legacy_source_family_alias; basic_4note_altered_dominant_compatibility_source; basic_4note_dim7_source_family; basic_4note_1357; 4_note_basic_1357; hard binding concept; not a new progression recognizer; OpenProjectionMethod.DROP3; OpenProjectionMethod.DROP2_AND_4; same DispositionFamily + ProjectionMethod; method lock rescue; same-family fallback; generic open fallback; closed compact fallback; nearest motion; source-order compact stack; parent-closed; parent_closed; closed_parent_placement_callback.
Compact consistency index (historical shipped contract aliases, not active roadmap): ABA; BAB; 8:2; 52-74; 60-74; 3-b7-X-Y; Harmonic expansion does not replace the chord; functional degree source; 4-Note Source Gating Audit; Mode-Aware Source Weight; Unified Color Permission + Chart Fidelity; Eleventh / #11 / Explicit Extension Source Completion; Color Source Gating Regression; four_mode_aware; v2_1_37; v2_1_40; v2_1_43; B3-F4; Rule Change Documentation Sync Standard; 规则变化就必须同步文档; 1451; 1351; 1251; core/harmony/harmonic_context.py; OpenProjectionMethod.GENERIC_OPEN; planning-only.
Compact contract token index B (historical shipped docs preserved as aliases, not active roadmap): rootless_ab_register_center_score; generated demo artifacts are not packaged; third-fifth-seventh-ninth; source_family_weights_by_gate; AllowedColorSet; root-third-seventh-eleventh; alt palette; G9 / G7#9 / G7b13 / Bm11b5; Top-k nearest realizations; common-tone; 3-note closed; 4-note closed; 3513; 5135; Progression / phrase-level voicing method lock.
Compact contract token index C: Gesture-driven revoicing; 2_note_guide_tone_shell; per-source nearest.
Compact contract token index D: Do not generalize v2_1_37 immediately; All the Things You Are.
Compact harness contract index: classic_fill_min_gap_regions; classic fill; logical grid; same current-root note; timing_intent; BassFoundation Musicality Audit; Region Decision Trace; target-to-target; target_nextR_note; Seventh lower-lane; Target Continuity Audit; Pattern rules; Voicing rules; Expression rules; Timing rules; generate_closed_34note_baseline_smoke_listening.py; CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; legacy Disposition; resolver migration is not part of v2_2_x; project_source_to_disposition(); DispositionProjectionResult; v2_2_2 — Closed Projection Migration / No Behavior Change; src/jammate_engine/core/voicing/disposition/closed.py; place_compact_closed_seed_layout; strict_closed_register_variants; closed_projection_migrated; v2_2_3 — Legacy Disposition Cleanup Pass; src/jammate_engine/core/voicing/disposition/open.py; src/jammate_engine/core/voicing/disposition/spread.py; src/jammate_engine/core/voicing/disposition/placement_utils.py; disposition/facade.py is now only a placement facade; v2_2_4 — Open Projection Skeleton / DROP2 4-note Only; v2_2_5 update — DROP2 Parent-Closed Projection Correction Pass; place_drop2_projection_from_closed_parent; open_drop2_parent_closed_notes; not from a direct source-order compact stack; v2_2_7 update — OPEN Method Candidate Pool / DROP3-DROP2&4 Skeleton Pass; open_projection_method_pool; DROP3; DROP2_AND_4.
Compact package organization token: BassFoundation 规则包; generation/bass_foundation/.
## v2_2_28 Medium Swing voicing rule
Medium Swing harmonic comping uses OPEN family continuity by default. CLOSED is no longer left in the normal Medium Swing candidate family pool for per-chord random selection; if a future rescue needs CLOSED, it must be explicit/audited.
## v2_2_38 Medium Swing voicing texture rule
Medium Swing consumes section-scoped `VoicingTextureState`: the style still filters to OPEN family, but the state now has a concrete section scope id derived from chord-region metadata. This prepares bridge/chorus texture contrast without changing Bossa or Ballad voicing behavior.
## v2_2_38 SPREAD lower group rules
SPREAD lower/foundation inventory is implemented but not runtime-enabled. Recipe set: 1-note `root`; 2-note `root+7 / root+3 / root+5 / 3+7`; 3-note `root+5+upper_root / root+3+7 / root+7+upper3 / root+5+upper3`. Placement must obey span guards and emit metadata including recipe id, roles, degrees, register low/high, span, and notes-only/runtime-disabled flags.
## v2_2_40 SPREAD upper source rules
The Upper Source Adapter is not a style runtime rule. It prepares source_oriented_not_placed upper material for future SPREAD projection by reusing `content_planner`, existing source/orientation metadata, shared color permission, and DROP2/DROP3 projection-resource refs. It remains notes-only, runtime-disabled, and does not reuse final placed closed/open candidates.
## v2_2_40 — Basic SPREAD Projection
Basic SPREAD Projection adds a notes-only projection skeleton in the existing `core/voicing/disposition/spread.py` module. It combines the v2_2_38 lower inventory + upper source adapter from v2_2_39 into placed lower/upper candidates while keeping `runtime_enabled=false`.
Required public contract tokens: `BASIC_SPREAD_PROJECTION_VERSION`, `SpreadProjectionRegisterPolicy`, `SpreadProjectionCandidate`, `SpreadProjectionResult`, `project_basic_spread_contract`, `project_basic_spread_candidates`, and `basic_spread_projection_debug`.
The layer owns `group_gap_guard`, `span_guard`, lower/upper register metadata, and candidate legality metadata. It remains notes-only, does not touch expression or pedal, and does not reuse final placed closed/open voicing results. `1+4` is still interpreted as lower root foundation plus an upper DROP2/DROP3-derived projection block.
## v2_2_41 — Group-wise Voice-Leading Scorer
Group-wise Voice-Leading Scorer adds notes-only SPREAD continuity scoring in the existing `core/voicing/disposition/spread.py` owner. It introduces `GROUPWISE_SPREAD_VOICE_LEADING_VERSION = "v2_2_41"`, `SpreadGroupwiseVoiceLeadingWeights`, `SpreadGroupwiseVoiceLeadingScore`, `score_spread_groupwise_voice_leading`, `rank_spread_candidates_by_groupwise_voice_leading`, `select_spread_candidate_by_groupwise_voice_leading`, and `spread_groupwise_voice_leading_path_debug`.
The scorer works only on `SpreadProjectionCandidate` objects produced by Basic SPREAD Projection. It does not change `project_basic_spread_candidates()` ordering, does not create a runtime `VoicingCandidate`, does not enable SPREAD in Medium Swing/Bossa/Ballad, and remains `runtime_enabled=false`, notes-only, with no expression or pedal behavior.
Scoring is explicitly group-wise rather than total-motion-only. The component metadata includes `lower_group_motion`, `upper_group_motion`, `top_voice_motion`, `group_gap_change`, `span_penalty`, `register_penalty`, `weighted_penalty`, and `continuity_score`. This preserves the SPREAD model as lower/foundation group + upper/projection group and prepares for later Ballad SPREAD pilot work without violating Pattern / Voicing / Expression separation.
## v2_2_43 — SPREAD Candidate Selector Contract / Runtime Gate Skeleton
SPREAD Candidate Selector Contract / Runtime Gate Skeleton adds a safety-gated selector surface in the existing `core/voicing/disposition/spread.py` owner. It introduces `SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"`, `SpreadRuntimeGateDecision`, `SpreadCandidateSelectorRequest`, `SpreadCandidateSelectorResult`, `spread_runtime_gate_from_policy`, `select_spread_candidate_with_runtime_gate`, and `spread_candidate_selector_contract_debug`.
The gate is closed by default. To open it, policy metadata must explicitly request the SPREAD selector gate, for example `spread_selector_enabled=true` / `spread_runtime_gate_enabled=true`, and the resolved texture family must request `spread` through `primary_family`, `allowed_families`, or `VoicingTextureState`. Even when open, the result remains a notes-only `SpreadProjectionCandidate`: `candidate_conversion_allowed=false`, `style_runtime_wiring_enabled=false`, `runtime_enabled=false`, and no expression or pedal behavior is introduced. This is a selector contract / runtime gate skeleton only; it does not retune Ballad, Bossa, or Medium Swing runtime behavior.
## v2_2_43 — SPREAD Runtime Pilot Planning / Ballad Entry Contract
SPREAD Runtime Pilot Planning / Ballad Entry Contract adds a guarded Jazz Ballad pilot entry contract in the existing `core/voicing/disposition/spread.py` owner. It introduces `BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION = "v2_2_43"`, `BalladSpreadEntryScene`, `BalladSpreadRuntimeEntryContract`, `BalladSpreadRuntimeEntryDecision`, `BalladSpreadRuntimePilotResult`, `ballad_spread_runtime_entry_contract`, `resolve_ballad_spread_runtime_entry`, `select_ballad_spread_pilot_candidate`, and `ballad_spread_runtime_entry_debug`.
The contract is planning/debug only: Jazz Ballad must explicitly set `ballad_spread_runtime_pilot.enabled=true` and still pass the existing SPREAD selector gate before notes-only pilot selection can return a `SpreadProjectionCandidate`. It keeps `style_runtime_wiring_enabled=false`, `candidate_conversion_allowed=false`, `runtime_enabled=false`, `notes-only`, and `no_expression_or_pedal=true`; Medium Swing and Bossa remain unaffected. Ballad pilot grouping is limited to `1+4`, `2+3`, `2+4`, and `3+3`, with `3+4` / 7-note thick ending left for a later explicit ending/climax pass.
## v2_2_44 update — Ballad SPREAD Runtime Pilot Wiring Plan + Safe Dry Run
`core/voicing/disposition/spread.py` now exposes `BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION`, `BalladSpreadRuntimePilotWiringPlan`, `BalladSpreadRuntimeDryRunChordTrace`, `BalladSpreadRuntimeSafeDryRunResult`, `ballad_spread_runtime_pilot_wiring_plan`, `run_ballad_spread_runtime_safe_dry_run`, and `ballad_spread_runtime_safe_dry_run_debug`. This pass validates the safe chain `entry_contract_to_selector_gate_to_notes_only_candidate_to_future_conversion_boundary` for an explicitly enabled Ballad SPREAD pilot. The result remains a notes-only `SpreadProjectionCandidate`; `candidate_conversion_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false`. It is safe dry run only, with no expression/pedal changes and no default Ballad runtime retune. Medium Swing and Bossa remain unaffected.
## v2_2_45 update — Ballad SPREAD Runtime Conversion Boundary Audit
- Added `SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION` in the existing `core.voicing.disposition.spread` owner.
- Added `SpreadRuntimeConversionBoundaryStatus`, `SpreadRuntimeConversionFieldAudit`, `SpreadRuntimeConversionBoundaryAudit`, and `BalladSpreadRuntimeConversionBoundaryAuditResult`.
- Added `spread_runtime_conversion_boundary_audit`, `audit_ballad_spread_runtime_conversion_boundaries`, `spread_runtime_conversion_boundary_debug`, and `ballad_spread_runtime_conversion_boundary_debug`.
- This stage audits the future `SpreadProjectionCandidate_to_VoicingCandidate_boundary_audit_only` path and explicitly does not create a runtime `VoicingCandidate`.
- The audit records mappable fields such as notes/degrees, adapter-required fields such as `content_family/root_support/bass_relation/interval_structure`, and the v2_2_46 `runtime_functional_grouping_value_exists` alignment for `1+4` before any SPREAD runtime conversion.
- `candidate_conversion_allowed=false`, `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false`; no expression/pedal/touch behavior is changed.
- Medium Swing and Bossa remain unaffected. This is boundary audit only, not Ballad runtime retune.
## v2_2_46 update — FunctionalGrouping 1+4 Contract Alignment
Tokens: `FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION`, `FunctionalGrouping.ONE_PLUS_FOUR`, `SpreadFunctionalGroupingContractAlignment`, `align_spread_functional_grouping_contract`, `functional_grouping_1plus4_contract_alignment_debug`, `runtime_functional_grouping_value_exists`, `foundation_group`, `projection_group`, `candidate_conversion_allowed=false`, `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, `runtime_enabled=false`; Medium Swing and Bossa remain unaffected.
Meaning: SPREAD `1+4` is now aligned with the core abstract grouping taxonomy as lower/foundation root plus upper/projection 4-note block. The projection map can partition a five-note candidate as `foundation_group=[0]` and `projection_group=[1,2,3,4]`. This is contract alignment only: it does not convert `SpreadProjectionCandidate` into `VoicingCandidate`, does not wire candidate_generator, and does not touch expression or pedal.
## v2_2_47 update — SPREAD Runtime Adapter Skeleton
- Added `SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION = "v2_2_47"` in the existing `core/voicing/disposition/spread.py` module; no new parallel voicing system or new file split was introduced.
- New contract/debug surfaces: `SpreadRuntimeAdapterStatus`, `SpreadRuntimeAdapterFieldMapping`, `SpreadRuntimeAdapterResult`, `BalladSpreadRuntimeAdapterSkeletonResult`, `spread_projection_candidate_to_voicing_candidate_adapter`, `run_ballad_spread_runtime_adapter_skeleton`, `spread_runtime_adapter_skeleton_debug`, and `ballad_spread_runtime_adapter_skeleton_debug`.
- The adapter maps a legal `SpreadProjectionCandidate` to a `VoicingCandidate` only when explicitly requested for dry-run/debug verification; default behavior remains blocked.
- Field mapping preserves notes, degrees, `FunctionalGrouping.ONE_PLUS_FOUR`, foundation/projection group roles, projection map metadata, register/span/gap guards, and SPREAD source metadata.
- `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false` remain hard boundaries; this is adapter skeleton only, not Ballad runtime retune.
- Jazz Ballad metadata now declares `SpreadProjectionCandidate_to_VoicingCandidate_adapter_skeleton_only`; Medium Swing and Bossa remain unaffected.
## v2_2_48 update — Ballad SPREAD Runtime Pilot Candidate Pool Integration
- Added `BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION = "v2_2_48"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New contract/debug surfaces: `BalladSpreadRuntimeCandidatePoolStatus`, `BalladSpreadRuntimeCandidatePoolPlan`, `BalladSpreadRuntimeCandidatePoolResult`, `ballad_spread_runtime_candidate_pool_plan`, `build_ballad_spread_runtime_pilot_candidate_pool`, and `ballad_spread_runtime_candidate_pool_debug`.
- The candidate pool is closed by default: `candidate_pool_enabled=false`, `adapter_conversion_allowed=false`, `candidate_pool_merge_allowed=false`, and `candidate_generator_wiring_allowed=false` in the default Jazz Ballad policy metadata.
- When explicitly enabled for `jazz_ballad`, the pilot may prepend adapted SPREAD `VoicingCandidate` skeletons to the runtime candidate pool while preserving the existing non-SPREAD pool as fallback: `fallback_to_existing_pool=true` and `default_style_runtime_unchanged=true`.
- The integration is still a controlled pilot candidate source: no expression/pedal/touch behavior is changed, no Ballad default retune is enabled, and Medium Swing and Bossa remain unaffected.
## v2_2_49 update — Ballad SPREAD Pilot Selection Weight + Fallback Audit
- Added `BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New audit/debug surfaces: `BalladSpreadPilotSelectionAuditStatus`, `BalladSpreadPilotSelectionWeightPlan`, `BalladSpreadPilotSelectionWeightFallbackAuditResult`, `ballad_spread_pilot_selection_weight_plan`, `audit_ballad_spread_pilot_selection_weight_and_fallback`, and `ballad_spread_pilot_selection_weight_fallback_audit_debug`.
- The audit checks explicit Ballad pilot pool safety before any real selection: `fallback_required=true`, `candidate_order_is_selection_priority=false`, `selector_scoring_still_authoritative=true`, and `candidate_selection_not_performed=true`.
- Explicit SPREAD pilot candidates remain secondary pilot candidates rather than a default replacement for the existing non-SPREAD pool. The fallback pool must be retained, SPREAD raw-score margin and candidate share are audited, and dominance risk is reported instead of silently retuning selection.
- This pass remains audit-only: `style_runtime_default_enabled=false`, `default_style_runtime_unchanged=true`, `runtime_enabled=false`, no expression/pedal/touch retune, and Medium Swing and Bossa remain unaffected.
### v2_2_50 — Ballad SPREAD Pilot Runtime Enablement Guard + First Listening Isolation
- Adds `BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION = "v2_2_50"` in the existing SPREAD disposition module.
- Adds `BalladSpreadPilotRuntimeEnablementGuardStatus`, `BalladSpreadPilotRuntimeEnablementGuardPlan`, and `BalladSpreadPilotRuntimeEnablementGuardResult`.
- Adds `ballad_spread_pilot_runtime_enablement_guard_plan`, `guard_ballad_spread_pilot_runtime_enablement`, and `ballad_spread_pilot_runtime_enablement_guard_debug`.
- Candidate generation now requires the v2_2_50 guard before consuming explicit Ballad SPREAD pilot candidates: `runtime_guard_enabled=false` and `listening_isolation_enabled=false` are the default style-policy values.
- First listening isolation is generated by `examples/scripts/generate_ballad_spread_first_listening_isolation_demo.py` and writes `v2_2_50_misty_jazz_ballad_spread_first_listening_isolation_demo.mid`.
- The pilot remains `first_listening_isolation_only=true`: fallback is retained, expression/pedal are not changed, and Medium Swing and Bossa remain unaffected.
### v2_2_51 — Expression Region Duration Clamp for Ballad SPREAD Listening Clarity
- Adds `EXPRESSION_REGION_DURATION_CLAMP_VERSION = "v2_2_51"` in the existing core expression resolver.
- Concrete expression durations are clamped to the remaining length of their own harmonic/chord region when region metadata is available. Pattern remains pitchless; style expression profiles still describe desired touch/sustain.
- This directly addresses Ballad SPREAD first-listening clarity: warm sustain can no longer spill over dense two-chord bars and blur into the next chord region.
- The expression audit exposes clamp metadata and does not treat intentionally region-clamped Ballad soft sustain as a soft-sustain error.
- No SPREAD voicing retune, no pedal retune, no new voicing system, and no Medium Swing/Bossa behavior change by policy.
- Listening demo: `v2_2_51_misty_jazz_ballad_spread_region_clamped_listening_demo.mid`.
## v2_2_52 update — Ballad SPREAD 1+4 True Isolation Fix
- Adds `BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION = "v2_2_52"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new file split was introduced.
- Adds explicit listening-isolation metadata: `ballad_spread_1plus4_true_isolation.enabled=true`, `required_recipe_id="spread_1plus4_contract"`, and `fallback_only_when_missing=true`.
- In first-listening isolation mode, candidate generation now filters the guarded pool to the matching SPREAD pilot candidate when available, so the selector cannot choose the normal 4-note fallback pool during a requested 1+4 isolation demo.
- Fallback remains available only when the requested SPREAD contract cannot be built at all; Medium Swing and Bossa remain blocked by the existing Ballad style gate.
- This pass does not change expression, pedal, pattern, or default Jazz Ballad runtime policy. It only fixes the isolation demo contract so `1+4 = lower root + upper 4-note block` can actually be heard as a 5-note piano voicing.
- Listening demo: `v2_2_52_misty_jazz_ballad_spread_1plus4_true_isolation_demo.mid`.
## v2_2_53 update — SPREAD 1+4 Upper Compact Closed Parent Alignment
- Adds `SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION = "v2_2_53"`.
- Adds `compact_closed_parent_candidates_for_projection()` to existing `core/voicing/disposition/closed.py` as a shared compact parent construction boundary.
- SPREAD 1+4 upper 4-note blocks now use compact closed parent candidates before delegating to OPEN-owned DROP2/DROP3 projection resources.
- This prevents extension/alteration offsets such as 9/b9 from being treated as wide oriented-stack parents before drop projection.
- No new parallel voicing system; no Ballad expression/pedal/pattern retune; no Medium Swing/Bossa runtime change.
- Listening demo: `v2_2_53_misty_jazz_ballad_spread_1plus4_compact_parent_alignment_demo.mid`.
## v2_2_58 update — Ballad SPREAD 2+3 listening rule
`spread_2plus3_contract` is now available for explicit Ballad SPREAD listening isolation. The lower/foundation group uses existing 2-note lower recipes such as `root+7`, `root+3`, `root+5`, and `3+7`; the upper/projection group reuses existing 3-note upper content. Every future SPREAD grouping audit should be reviewed in two forms: unexpanded and expansion-enabled. Expansion-enabled demos currently target approximately 60% actual expanded upper color while preserving seventh-chord identity.
- v2_2_58: `spread_2plus3_contract` lower fix: rooted `root+3/root+5/root+7` equal family, rootless `3+7` separate mode, lower A0-E2/top≥G1, upper shell+1 excluded, dual demos remain required.
## v2_2_60 update — Ballad SPREAD 2+3 Closed Upper Groupwise Voice-Leading Fix
- For `spread_2plus3_contract`, upper 3-note placement must be a compact closed upper group, not source-order spread. The upper group lowest note floor is F3.
- Lower 2-note rooted foundation for this pilot is E2-E3. `root+3`, `root+5`, and `root+7` are equal-weight rooted candidates; rootless `3+7` is a separate mode.
- Runtime listening isolation may emit multiple legal SPREAD candidates so the final selector can collapse by lower/upper groupwise nearest motion. This is gated and must not change default style runtime.
- `shell+1/root` remains excluded from SPREAD upper 3-note pools, and the v2_2_54 source-integrity baseline still applies.
- v2_2_60 register correction: `spread_2plus3_contract` upper 3-note closed stack must have lowest upper note >= F3; lower 2-note rooted foundation is constrained to E2-E3.

## v2_2_72 update — Ballad SPREAD 2+3 Whole Register C2-A4

- `spread_2plus3_contract` listening isolation now uses rooted bass anchor policy: in rooted lower mode, the root must be the lowest note and must sit inside the root-bass anchor window.
- Lower `root+3`, `root+5`, and `root+7` remain equal inventory candidates; rootless `3+7` remains a separate lower foundation mode and is not mixed into rooted demos.
- The previous mechanical lower E2-E3 / upper F3 floor design is replaced by whole-voicing register/span/gap guard plus groupwise voice-leading and whole-voicing scoring.
- Upper 3-note remains closed stack and continues to exclude `shell+1/root` from the SPREAD upper 3-note pool.
- Dual listening workflow remains mandatory for this grouping: unexpanded demo plus expanded demo targeting about 60% actual expansion.


## v2_2_72 update — Ballad SPREAD 2+4 Pilot Dual Demo

- `spread_2plus4_contract` is explicit listening-isolation only; default Ballad runtime remains unchanged unless requested by metadata.
- Lower 2-note foundation reuses the approved 2+3 rooted bass-anchor logic: root is the lowest note in C2-C3, `root+3/root+5/root+7` are the equal-weight rooted family, and rootless `3+7` stays a separate mode.
- Upper 4-note group reuses the approved 1+4 upper logic: CLOSED compact parent + OPEN DROP2/DROP3 projection; DROP2&4 is not allowed in SPREAD upper 4-note.
- The 2+4 pilot uses whole-register C2-G5 plus gap/span guard, groupwise voice-leading, and whole-voicing scoring.
- Dual-demo workflow remains required: unexpanded and expansion-enabled standard-tune demos; expansion-enabled target is about 60% actual color and must preserve v2_2_54 seventh-chord source integrity.

## v2_2_72 update — Ballad SPREAD 3+3 Pilot Dual Demo
- `spread_3plus3_contract` is now available for explicit Ballad listening isolation.
- Lower group: rooted 3-note foundation inventory (`root+5+upper_root`, `root+3+7`, `root+7+upper3`, `root+5+upper3`) with root as the lowest note.
- Register policy: root bass anchor `C2-C3`; full voicing guard `C2-G5`; no separate hard LH/RH register split.
- Upper group: 3-note closed stack, shell+1/root excluded, same upper source policy as approved `2+3`.
- Expanded demo target is approximately 60%; unexpanded and expanded demos must both be generated for review.

## v2_2_72 update — Ballad SPREAD 3+3 Lower Recipe / Register Fix
- `spread_3plus3_contract` lower rooted foundation keeps `root+3+7` and removes `root+5+7`; `root+5+7` is not part of the 3-note lower spread pool.
- Remaining lower 3-note recipes are `root+5+upper_root`, `root+3+7`, `root+7+upper3`, and `root+5+upper3`.
- 3-note lower spread span guard is 16 semitones, while root remains the lowest bass anchor in C2-C3.
- Upper 3-note remains closed stack and forbids shell+1/root. Dual Misty demos remain unexpanded plus expansion-enabled at about 60%.

## v2_2_72 update — Ballad SPREAD 2+3 / 2+4 / 3+3 Register Raised M3 Dual Demos

- Preserve approved rooted SPREAD grouping logic for `2+3`, `2+4`, and `3+3`.
- Keep root as lowest bass anchor in C2-C3. Do not mechanically move the root anchor window to E2-E3; for Eb-rooted material this would force an octave jump rather than a musical major-third register lift.
- Raise the upper/whole listening register target by a major third:
  - `2+3`: whole register ceiling A4 -> C#5.
  - `2+4` / `3+3`: whole register ceiling G5 -> B5.
- Continue dual-demo workflow: unexpanded plus expansion-enabled around 60%.
- Keep v2_2_54 source integrity baseline and all approved SPREAD guards intact.


## v2_2_72 update — Ballad SPREAD Lower Foundation Quality Gate

- SPREAD lower foundation is now chord-quality aware instead of a homogeneous random pool.
- Lower 2-note: `root+5` is treated as triad/root-fifth foundation material; seventh-family chords prefer `root+3` / `root+7`, while triad-family chords can use `root+3` / `root+5`.
- Lower 3-note: seventh-or-above chords prefer `root+3+7` / `root+7+upper3`; triad-family chords prefer `root+5+upper_root` / `root+5+upper3`.
- Existing root anchor E2-E3, root-lowest guard, high-tail span guard, P5 lower-to-upper gap guard, and unexpanded/expanded 60% demo workflow remain intact.

## v2_2_72 update — Ballad SPREAD 3+4 Pilot Dual Demo

- Added explicit Ballad SPREAD `3+4` listening isolation as a thick texture candidate.
- `3+4` reuses the approved `3+3` lower 3-note rooted foundation logic and the approved `2+4` / `1+4` upper 4-note DROP2/DROP3 logic.
- SPREAD upper 4-note still excludes DROP2&4; for `3+4`, upper 4-note projection now can emit all legal parent projections so overlap/gap guards and groupwise voice-leading can choose a non-overlapping version.
- Register / guard baseline remains: root anchor `E2–E3`, root must be the lowest note, high-tail lower span guard, lower-top to upper-bottom gap `<= P5`, no upper/lower MIDI-note overlap, and full voicing within the Ballad SPREAD whole register.
- Dual demo workflow remains required: unexpanded and harmonic-expansion-on versions; expanded demo target remains about 60%.

## v2_2_72 update — Ballad SPREAD 3+4 Lower Recipe Gate
- `3+4` lower 3-note is no longer the full `3+3` lower pool. Seventh-or-above chords use `root+7+upper3` only; triad-family chords use `root+5+upper3` only.
- The root-anchor high-tail span guard is disabled only for `spread_3plus4_contract`; other SPREAD groupings keep the guard.
- Upper 4-note remains DROP2 / DROP3 only, with optional octave-shift candidate emission so thick lower groups can satisfy the P5 gap and no-overlap guards.
- Dual Misty demos: `v2_2_72_misty_jazz_ballad_spread_3plus4_lower_recipe_gate_unexpanded_demo.mid` and `v2_2_72_misty_jazz_ballad_spread_3plus4_lower_recipe_gate_expanded_60pct_demo.mid`.


## v2_2_72 update — Ballad SPREAD 3+4 Root Anchor Lowered

- `3+4` keeps the approved lower recipe gate: seventh-or-above chords use `root+7+upper3`; triad-family chords use `root+5+upper3`.
- For `3+4` only, the root bass anchor register is lowered four semitones from `E2–E3` to `C2–C3` to reduce overall height.
- The `3+4` anchor-tail span guard remains disabled; the P5 lower-to-upper gap guard, no-overlap guard, root-lowest rule, DROP2/DROP3-only upper 4-note policy, and source-integrity gate remain active.
- Dual Misty demos are exported for unexpanded and expansion-enabled approximately 60% color versions.
## v2_2_73 update — Ballad SPREAD 3+4 Root Target Fine Tune

3+4 keeps the C2–C3 root window but lowers its root target to Eb2/MIDI 39; this preserves the v2_2_54 source-integrity gate, DROP2/DROP3-only upper 4-note rule, root-lowest rule, P5 gap cap, and overlap guard while reducing the thick lower group's C3-side bias.

## v2_2_82 — Ballad SPREAD Top-Voice Continuity Scoring

Ballad SPREAD dry-run mix now scores full-candidate top voice continuity. The previous voicing's highest note and current candidate's highest note are compared directly, with close motion preferred and large/excessive jumps penalized. Compatible texture-family contracts may enter the same candidate pool so the selector can choose the grouping/realization whose soprano line is closest, instead of hard-selecting one grouping before voicing. This remains explicit dry-run/audit behavior and does not enable ordinary Jazz Ballad runtime by default.


## v2_5_4 Jazz Ballad held-foundation partial reattack

- Ballad `INNER_MOVEMENT` is a gesture/realization behavior, not an ordinary pattern cell.
- The motion event projects only requested `inner`, `inner_n`, `color_group`, `projection_group`, or equivalent V2 projection refs.
- A later inner-motion gesture is not treated as a full harmonic interruption for expression duration clamp.
- Realization releases only voices re-struck by the motion event and lets foundation/common-tone voices hold.
- No concrete notes, voicing textures, final expression values, or V1 legacy slots may be stored in pattern metadata.


## v2_5_6 Jazz Ballad swing 1& timing intent correction

For Jazz Ballad piano `1&` soft-mark / retouch events, write the written upbeat as logical `0.5` and set event metadata `timing_intent=swing_upbeat`. Do not encode the performed location as `0.666...` in the pattern. The render timing policy is the owner of converting logical `.5` to the swing/triplet upbeat.

As of v2_5_8, this event-level `swing_upbeat` contract remains valid, but Jazz Ballad also defaults globally to swing-8 timing. Event-level tags remain useful for musical upbeats that must stay swung under future isolation/override profiles.

## v2_5_5 Jazz Ballad two-beat 1& correction

For two-beat Jazz Ballad regions, the soft-mark / light-retouch piano candidates should use local beats `0.0, 0.5`, i.e. beat 1 + beat 1&. Avoid the heavier `0.0, 1.0` beat 1 + beat 2 feel for this candidate.


## v2_5_10 Integration Note

Engine generation rules remain at the `v2_5_9` official engine-deepening baseline. The discarded experimental Ballad brush-drums shortcut is not part of this integrated baseline.


## v2_6_5 Engine Voicing SPREAD Boundary Split Plan

SPREAD remains a voicing disposition/projection family. It owns lower/upper functional grouping, register/gap/span/root-anchor legality, groupwise voice-leading, and adapter/gate logic for converting SPREAD candidates into ordinary voicing candidates. It does not own pattern rhythm, anticipation, expression, pedal, MIDI writing, or style pattern vocabulary.

Current `core/voicing/disposition/spread.py` responsibilities are now inventoried for future behavior-preserving extraction: contracts, lower group inventory and placement, upper source adapter, register guards, basic projection, groupwise voice-leading, runtime gate, runtime adapter, Ballad pilot/isolation, and debug/audit wrappers.

Before any SPREAD implementation split, preserve the v2_6_5 behavior signatures for: lower recipe ids, seven spread contract skeletons, and representative projection output for `Cmaj7`, `G7b9`, and `Bm7b5`. Future split work must keep public imports from `jammate_engine.core.voicing.disposition.spread`, `jammate_engine.core.voicing.disposition`, and `jammate_engine.core.voicing` compatible.

## v2_6_6 Engine Voicing SPREAD Lower Group Split

- No runtime music-generation behavior changed in this pass.
- `spread_lower_groups.py` now owns SPREAD lower/foundation recipe ids, recipe dataclasses, inventory, chord-quality-aware instantiation, lower placement, and lower inventory debug payloads.
- `spread_contracts.py` now owns small shared SPREAD contract constants/enums needed before a full package conversion.
- `spread.py` remains the public compatibility surface and re-exports the lower-group API; existing imports from `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition` continue to work.
- The lower group owner remains notes-only and does not own Pattern, Anticipation, Expression, Gesture, MIDI writer, velocity, duration, or pedal decisions.
- v2_6_5 frozen behavior signatures for lower recipe ids and representative SPREAD candidates are preserved.


## v2_6_9 Engine Voicing SPREAD Projection Core Split

- No music-generation rule changed in this pass.
- `spread_projection_core.py` now owns notes-only lower+upper SPREAD projection orchestration.
- Lower group recipes remain in `spread_lower_groups.py`; upper source adaptation remains in `spread_upper_sources.py`; register/gap/span legality remains in `spread_register_guards.py`.
- SPREAD projection core must not own Pattern, Anticipation, Expression, Gesture, Pedal, MIDI, style pattern vocabulary, or style-level voicing preference selection.
- Existing imports from `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition` must remain compatible.
- v2_6_5 frozen behavior signatures for representative SPREAD candidates remain preserved.

## Voicing Rule Update: v2_6_10 SPREAD Density Reset

Jazz Ballad SPREAD no longer treats 4-note `1+3` / `2+2` as normal runtime SPREAD. Those contracts are retired from default output because 4-note voicings belong to ordinary closed/open/rooted-color paths, while SPREAD should represent lower/upper functional grouping.

Active default SPREAD contracts:

```text
1+4  -> 5-note
2+3  -> 5-note, normal Ballad body
2+4  -> 6-note, fuller support/lift
3+3  -> 6-note, fuller support/lift/climax
3+4  -> 7-note, ending/climax only
```

Boundary rule: Pattern, Anticipation, Expression, Gesture, and MIDI do not choose voicing density, source, or disposition. The density/disposition gate belongs to `core.voicing.density_policy`; Ballad only declares grouped-spread preferences through its voicing policy metadata.

## Voicing Rule Update: v2_6_11 Ballad Safe Extension Color Gate

Jazz Ballad safe harmonic expansion now treats plain major-seventh chords as warm 9/13 targets by default. `#11` is no longer part of the ordinary unnotated maj7 safe-extension pool.

```text
Ebmaj7 + default Ballad expansion -> 9 / 13 priority, no automatic #11
Ebmaj7#11 written in chart -> #11 preserved faithfully
Ebmaj7 + harmonic_color_intent=lydian/bright/modern -> #11 may enter the source pool
```

This rule belongs to core voicing source/color permission. Pattern, Anticipation, Expression, Gesture, Pedal, and MIDI do not choose or suppress maj7#11.

## Voicing Rule Update: v2_6_12 SPREAD Groupwise Voice-Leading Owner

SPREAD groupwise voice-leading / ranking / continuity is now owned by `core.voicing.disposition.spread_voice_leading`.

The scorer remains notes-only and componentized:

```text
lower/foundation group motion
upper/projection group motion
top voice continuity
group gap stability
span penalty
register penalty
legality penalty
```

`spread.py` is the compatibility facade. It may re-export the existing public scorer names, but it should not regain the main groupwise scoring implementation.

This split does not change Jazz Ballad SPREAD density routing or color policy: v2_6_10 still keeps Ballad SPREAD centered on 5/6-note grouped voicings, and v2_6_11 still prevents unnotated maj7#11 from becoming default warm Ballad safe extension color.


## Voicing Rule Update: v2_6_13 Ballad Six-Note Ratio Lift

Jazz Ballad SPREAD remains centered on 5-note `2+3`, but selected 6-note grouping-mix contracts now receive a small notes-only intent bias during SPREAD groupwise voice-leading collapse:

```text
spread_grouping_mix_selected_6note_contract_bias = 0.20
```

Owner:

```text
core.voicing.disposition.spread_voice_leading
```

Effect in reference Misty / Jazz Ballad / 3-chorus audit:

```text
v2_6_12: 6-note = 8
v2_6_13: 6-note = 12
```

Guardrails remain unchanged:

```text
4-note SPREAD 1+3 / 2+2 remain retired from default Ballad runtime
5-note remains dominant
7-note remains rare
unnotated maj7#11 remains disabled by default
Pattern / Anticipation / Expression / Pedal / Gesture / MIDI do not choose voicing density
```

## Voicing Rule Update: v2_6_14 Ballad SPREAD 5-to-6 Ratio Calibration

Jazz Ballad SPREAD grouped voicing now targets approximately:

```text
5-note:6-note ~= 6:4
```

The adjustment is still notes-only and owned by:

```text
core.voicing.disposition.spread_voice_leading
```

Runtime lever:

```text
spread_grouping_mix_selected_6note_contract_bias = 5.0
```

Reference Misty / Jazz Ballad / 3-chorus audit:

```text
5-note: 118
6-note: 76
7-note: 2
4-note: 0
```

Guardrails remain unchanged:

```text
4-note SPREAD 1+3 / 2+2 remain retired from default Ballad runtime
7-note remains low-frequency
unnotated maj7#11 remains disabled by default
Pattern / Anticipation / Expression / Pedal / Gesture / MIDI do not choose voicing density
```

## Voicing Rule Update: v2_6_15 SPREAD Runtime Gate / Adapter Owners

SPREAD notes-only runtime enablement and candidate adapter mapping now have dedicated owners:

```text
core.voicing.disposition.spread_runtime_gate
core.voicing.disposition.spread_runtime_adapter
```

`spread.py` remains a public compatibility facade. Runtime gate / adapter logic must not own style pattern vocabulary, anticipation, expression, pedal, MIDI writing, or API behavior. The adapter remains explicitly notes-only unless a later runtime wiring pass intentionally opens conversion.

The v2_6_14 Jazz Ballad SPREAD density calibration remains unchanged:

```text
5-note:6-note ~= 6:4
4-note SPREAD 1+3 / 2+2 remain retired from default Ballad runtime
7-note remains rare
unnotated maj7#11 remains off by default
```

## Voicing Rule Update: v2_6_16 Content Planner Boundary Split Plan

`core.voicing.sources.content_planner` remains the public content-planning API for now, but future code split work must separate concern groups before adding more source families.

Planned ownership model:

```text
content_planner.py             public API / compatibility facade / orchestration
content_family_router.py       chord-quality-valid ContentFamily routing
content_source_inventory.py    family -> degree source options
color_permission.py            color admission gates / explicit-symbol fidelity
source_balance.py              source-family scoring only
upper_structure.py             source-only upper-structure recipes
```

Non-negotiable guardrails for the next split:

```text
Content routing must not decide disposition/register/projection.
Source inventory must not score or select candidates.
Color permission must not invent source inventories.
Source balance must not create degree recipes.
Upper Structure must stay source-only and reuse closed/inversion/DROP projection.
Pattern / Anticipation / Expression / Gesture / MIDI must remain outside voicing source planning.
```

Recommended next code task:

```text
v2_6_17_engine_voicing_content_family_router_behavior_preserving_split
```

## Voicing Rule Update: v2_6_17 Content Family Router Owner

Content-family routing now has a dedicated source-boundary owner:

```text
core.voicing.sources.content_family_router
```

This module decides which `ContentFamily` values are chord-quality-valid for a given chord symbol and `VoicingPolicy`. It handles triad family normalization, root-support filtering, fake-rootless prevention for no-seventh chords, conservative seventh-basic filtering, and the existing 4-note color-family entry gate.

`content_planner.py` remains the public facade and source inventory orchestration surface. Source inventory still owns family-to-degree options until the next planned split.

Boundary guardrails:

```text
content_family_router does not create degree recipes
content_family_router does not score source balance
content_family_router does not choose register/disposition/projection
content_family_router does not touch Pattern / Anticipation / Expression / Gesture / MIDI
```

Reference Jazz Ballad voicing guardrails remain unchanged:

```text
5-note:6-note ~= 6:4
4-note SPREAD remains retired from default Ballad runtime
unnotated maj7#11 remains off by default
```

Recommended next task:

```text
v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split
```

## Voicing Rule Update: v2_6_18 Content Source Inventory Owner

Family-to-degree source inventory now has a dedicated source-boundary owner:

```text
core.voicing.sources.content_source_inventory
```

This module owns source construction for:

```text
shell+5 / shell+color
seventh-basic 4-note sources
rooted-color 4-note sources
rootless A/B sources
triad-aware 3-note and 4-note sources
altered-dominant source inventory
explicit-symbol color source inventory
seventh-chord source integrity notes
```

`content_planner.py` remains the public facade and recipe orchestration layer. It should call `content_family_router.py` for valid families and `content_source_inventory.py` for source options, then attach density metadata to form `VoicingContentRecipe` objects.

Boundary guardrails:

```text
content_source_inventory does not route ContentFamily values
content_source_inventory does not score source balance
content_source_inventory does not choose register/disposition/projection
content_source_inventory does not touch Pattern / Anticipation / Expression / Gesture / MIDI
```

Reference Jazz Ballad voicing guardrails remain unchanged:

```text
5-note:6-note ~= 6:4
4-note SPREAD remains retired from default Ballad runtime
unnotated maj7#11 remains off by default
```

Recommended next task:

```text
v2_6_19_engine_voicing_color_permission_adapter_cleanup
```
## Voicing Rule Update: v2_6_19 Color Permission Adapter Owner

`v2_6_19_engine_voicing_color_permission_adapter_cleanup` clarifies the color-permission boundary:

```text
color_permission.py           decides explicit / expanded color admission and audit notes
content_source_inventory.py   constructs voicing source degree options
content_family_router.py      routes legal ContentFamily choices
content_planner.py            remains the facade / recipe orchestration layer
```

`color_permission.py` now owns `explicit_symbol_color_degrees`, `rootless_ab_explicit_color_degrees`, `ordered_explicit_colors`, `expansion_color_candidates`, `major_seventh_safe_extension_preference`, and `build_voicing_color_permission_context`.

It does not construct voicing sources. Rooted-color, rootless A/B, altered-dominant, shell+color, triad-aware and seventh-basic source construction remains in `content_source_inventory.py`.

Guardrails remain unchanged:

```text
5-note:6-note ~= 6:4 for Ballad/SPREAD
4-note SPREAD default remains retired
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

## Voicing Rule Update: v2_6_20 Source Balance Boundary Owner

`v2_6_20_engine_voicing_source_balance_boundary_cleanup` clarifies the source-balance boundary:

```text
source_balance.py            source-family scoring / bias only
content_family_router.py     ContentFamily routing / chord-quality normalization
content_source_inventory.py  family -> degree source construction
color_permission.py          explicit / expanded color admission
upper_structure.py           source-only upper-structure recipes
```

`source_balance.py` may read existing candidate metadata and apply `source_family_weights`, `source_family_weights_by_gate`, and altered-dominant intensity bias. It does not construct sources, does not route ContentFamily, does not decide color permission, and does not choose disposition/projection/register.

`SourceBalanceProfile` is an inspectable scoring/debug profile only; it exposes the selected source key, gate mode, lookup keys, content family, and altered-dominant source kind.

Guardrails remain unchanged:

```text
5-note:6-note ~= 6:4 for Ballad/SPREAD
4-note SPREAD default remains retired
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

Recommended next task:

```text
v2_6_21_engine_voicing_upper_structure_boundary_audit
```

## Voicing Rule Update: v2_6_21 Upper Structure Boundary Owner

`v2_6_21_engine_voicing_upper_structure_boundary_audit` clarifies the Upper Structure boundary:

```text
upper_structure.py           source-only upper-structure degree recipes
content_family_router.py     ContentFamily routing / chord-quality normalization
content_source_inventory.py  family -> degree source construction
color_permission.py          explicit / expanded color admission
source_balance.py            source-family scoring / bias only
spread_*                     projection / register / runtime adapter / groupwise motion
selection/*                  candidate scoring / selector / voice-leading
```

`upper_structure.py` may publish 3-note and 4-note Upper Structure source recipes and source metadata. It does not project closed/open/spread voicings, does not choose register or octave placement, does not score/select candidates, does not rank voice-leading, does not adapt runtime SPREAD candidates, and does not write MIDI or touch expression.

Upper Structure remains a source family, not a projection system:

```text
3-note upper structures reuse existing closed / inversion placement
4-note upper structures reuse existing closed / inversion / DROP2 / DROP3 projection paths
```

Guardrails remain unchanged:

```text
5-note:6-note ~= 6:4 for Ballad/SPREAD
4-note SPREAD default remains retired
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

Recommended next task:

```text
v2_6_22_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup
```

## v2_6_27 Completed — Engine Ballad SPREAD Listening Calibration

Completed voicing-only listening calibration:

- kept Ballad SPREAD focused on ordinary runtime groupings `2+3`, `2+4`, and `3+3`;
- demoted `1+4` to an explicit upper4-color/listening-isolation lane instead of default comping body;
- filtered zero-weight compatible contracts out of the runtime candidate pool;
- kept the 5-note:6-note balance near 6:4 after removing 1+4 from ordinary runtime;
- preserved zero default 4-note SPREAD and zero default unnotated maj7#11.

Next recommended voicing-only task: `v2_6_28_engine_ballad_spread_top_voice_and_register_micro_calibration`.

## v2_6_29 Voicing Audit Rule — Drop Projection Counts

Piano audit now distinguishes top-level drop projection usage from SPREAD upper-group drop usage.

For ordinary OPEN voicings:

```text
scope = main_voicing
method = drop2 / drop3 / drop2_and_4
```

For grouped SPREAD voicings:

```text
scope = spread_upper_group
method = upper_projection_method when it is drop2 / drop3 / drop2_and_4
```

The audit must include upper group drop usage in 5-note / 6-note / 7-note SPREAD counts, because grouped SPREAD may have a whole-voicing disposition of `spread` while its upper group internally reuses DROP2 or DROP3 projection resources.

Current Misty Ballad v2_6_29 expected upper-group drop counts:

```text
spread_upper_projection_methods:
  closed_upper_stack: 120
  drop2: 12
  drop3: 64

spread_upper_drop_projection_methods_by_density:
  6:
    drop2: 12
    drop3: 64
```

These audit fields are observational only and must not influence runtime selection.

## v2_6_35 Ballad SPREAD Phrase-Scope Wide Gap Rule

For Jazz Ballad SPREAD, the two known `2+3 Fm7` wide-gap rows may use a narrow phrase-scope candidate availability rule:

```text
only spread_2plus3_contract
same-recipe only
use top-stable replacement candidate
realized gap target <= 7 semitones
advance VoicingState with original phrase anchor
no broad scorer
no density lane reopening
```

Expected Misty three-chorus guardrails:

```text
5-note:124 / 6-note:72
1+4:10
4-note:0 / 7-note:0
lower_upper_too_wide_events:0
top_note_max <= 74
```

## v2_6_40 Ballad SPREAD Phrase-State Anchor Policy Gate

`VoicingStateAdvanceAnchor` is a core voicing runtime helper, but production resolver consumption must be explicitly authorized by style policy.

Runtime rule:

```text
candidate has state_anchor_notes
AND policy.metadata.voicing_state_advance_anchor_policy_gate_enabled = true
AND candidate scope is allowed by policy.metadata.voicing_state_advance_anchor_allowed_scopes
```

Current allowed Jazz Ballad scope:

```text
ballad_spread_phrase_scope_wide_gap_candidate_availability
```

Default global behavior:

```text
disabled without explicit policy gate
```

This prevents the realized-notes/state-anchor separation from silently becoming a global voicing behavior. Future styles may opt in only with a clear policy gate, audit fields, and regression tests.
