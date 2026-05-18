# Agent Track Changelog

Current baseline: `v2_6_5_agent_first_controlled_tool_execution_e2e`.

This file records Agent-track changes to reduce conflicts in the global `docs/CHANGELOG.md`.

---

## v2_6_5 — Agent First Controlled Tool Execution E2E

- Added first guarded controlled workflow execution path.
- Enabled only `agent_practice_plan` / `PracticePlanner.build_plan` for real controlled execution.
- Added `ControlledWorkflowExecutionPolicy` and `ControlledWorkflowExecutionResult` shapes.
- Added terminal `/execute-controlled` command after preview, confirmation, executor dry-run, and workflow descriptor resolution.
- Added Agent controlled execution spec/API route.
- Controlled execution remains low-risk: no route call, no engine adapter call, no accompaniment generation, and no MIDI asset creation.

## v2_6_4 — Agent Deterministic Workflow Dispatcher

- Added descriptor-only deterministic workflow dispatcher boundary.
- Added `ToolWorkflowDispatcherPolicy`, `DeterministicWorkflowDescriptor`, and `ToolWorkflowDispatchResult` shapes.
- Added terminal `/dispatch-dry-run` command after ToolExecutor dry-run.
- Added Agent workflow dispatcher spec/dry-run API routes.
- Dispatch remains descriptor-only: no workflow invocation, no route call, no engine adapter call, no MIDI asset creation.

## v2_6_3 — Agent Tool Executor Boundary

- Added dry-run/no-op ToolExecutor boundary contracts.
- Added `ToolExecutionPolicy`, `ToolExecutionRequest`, and `ToolExecutionResult` shapes.
- Added terminal `/execute-dry-run` command after explicit confirmation.
- Added Agent executor spec/dry-run API routes.
- Execution remains no-op: no deterministic workflow dispatch, no route call, no engine adapter call, no MIDI asset creation.

## v2_6_2 — Agent Tool Execution Confirmation Gate

- Added a preview-after confirmation envelope for Agent tool proposals.
- Added terminal chat `/pending`, `/confirm`, and `/reject` commands.
- Added trace summaries for confirmation envelope creation and user approve/reject decisions.
- Added Agent confirmation spec/preview API routes.
- Execution remains disabled: no ToolExecutor, no workflow dispatch, no engine adapter call.

## v2_4_13 — Agent Tool Call Preview Trace Contract

- Preserved as the current Agent baseline inside the integrated package.
- Tool-call preview remains validation-only and non-autonomous.
- Preview trace contract remains available for inspection and HarmonyOS integration.

## v2_4_12 — Agent Terminal LLM Config Wizard

- Added bounded provider-configuration guidance for terminal chat.

## v2_4_11 — Agent Terminal Tool-Call Candidate Extraction

- Added JSON candidate extraction for tool-call preview.

## v2_4_9 — Agent Trace Viewer CLI

- Added read-only trace inspection surface.
