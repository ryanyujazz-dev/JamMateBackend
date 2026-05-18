# JamMate Development Task Plan V2

Current baseline: `v2_4_11`.

`v2_4_11_agent_terminal_tool_call_candidate_extraction` adds JSON-only candidate extraction from successful terminal LLM replies on top of the existing terminal chat, `/tool-preview`, trace export, read-only trace viewer, and context controls. It reuses `core/tool_invocation.py` and the existing preview contract; extracted candidates are previewed against the current ContextPacket allow-list and never execute tools, dispatch workflows, call adapters, call API routes, or call engine code. Runtime music generation behavior is unchanged from `v2_3_17`; HarmonyOS direct `/accompaniment/generate` contract from `v2_4_1` remains intact.

---

## Immediate Branch Split

### Agent branch

```text
feature/agent-workflow
```

Scope:

- JamMate Agent workflow
- Practice Agent
- LLM context engineering
- bounded tool loop
- HarmonyOS API / contracts / fixtures
- trace/debug inspection

Suggested next task:

```text
v2_4_12_agent_tool_call_preview_trace_contract
```

### Engine branch

```text
feature/engine-deepening
```

Scope:

- JamMatePyEngine music generation
- voicing
- pattern selection
- expression / touch / dynamics / pedal
- style tuning
- listening demos

Suggested next task:

```text
v2_5_0_engine_deepening_audit_and_next_music_pass
```

---

## Merge Strategy

Recommended order:

```text
1. Merge Agent branch into main first.
2. Sync main into Engine branch.
3. Merge Engine branch into main.
```

Reason: API/Agent/HarmonyOS contracts should stabilize before engine deepening is merged back into the integrated baseline.

---

## Delivery Rule

Every future engineering delivery must perform cleanup before packaging:

- remove caches/temp files
- keep README as project overview, not changelog
- keep docs aligned with behavior changes
- run compileall and targeted tests when possible
- preserve relevant small MIDI demos for listening validation
