# JamMate Development Task Plan V2

Current baseline: `v2_4_7`.

`v2_4_7_agent_terminal_trace_export` adds explicit `--trace-dir` JSON export for terminal chat and `/tool-preview` on `feature/agent-workflow`. It reuses TraceLogger, JsonTraceStore, ContextBuilder, provider boundary, descriptor-only tool registry, and the validation-only tool invocation preview contract; it does not dispatch workflows, routes, adapters, or engine code. Runtime music generation behavior is unchanged from `v2_3_17`; HarmonyOS direct `/accompaniment/generate` contract from `v2_4_1` remains intact.

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
v2_4_8_agent_trace_api_contract_hardening
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
