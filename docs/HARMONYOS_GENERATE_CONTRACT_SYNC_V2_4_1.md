# HarmonyOS Generate Contract Sync v2_4_1

## Scope

`v2_4_1_harmonyos_generate_contract_sync` is a `feature/agent-workflow` delivery. It does not deepen the accompaniment engine's musical generation logic.

This pass hardens the current HarmonyOS direct playback contract:

```text
POST /accompaniment/generate
```

## Contract decisions

- HarmonyOS direct accompaniment calls `POST /accompaniment/generate`.
- Legacy `/v1/generate-midi-base64` is not the current frontend path.
- The preferred chart input is inline `jammate_leadsheet_v2`.
- Inline leadsheets use `sections` + `written_form`.
- Old Harmony bridge `blocks` + `playback_form` is not the V2 direct-generation contract.
- `tune` remains an optional fallback hint, but backend route priority is `leadsheet` first, `tune` resolver second.
- API request fields continue to accept camelCase and snake_case.
- Backend responses remain canonical snake_case.
- HarmonyOS owns practice duration via local timer; backend returns a playable MIDI asset, not a 20/30/45-minute long render.

## Minimum successful response dependency

HarmonyOS playback only requires this minimum successful shape:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "...",
    "cache_key": "..."
  }
}
```

`asset.debug_summary` may be present for diagnostics and contract tests, but should not be required for basic playback.

## Implementation notes

- `/accompaniment/generate` now includes a leadsheet content signature in `cache_key` to avoid collisions between different user-custom charts sharing the same title/style/tempo.
- Default direct output paths also include the leadsheet signature.
- Invalid inline leadsheets return `ok=false`, `error_code="INVALID_LEADSHEET"`, and structured validation `issues` instead of leaking an internal error.
- Route-level `ensemble` and `voicing_override` dictionaries are normalized from camelCase to snake_case before passing into engine runtime.
- HarmonyOS smoke fixtures now include an inline `jammate_leadsheet_v2` request body while keeping `tune` as a fallback hint.

## Non-goals

- No voicing/pattern/expression/pedal behavior changes.
- No LLM provider connection.
- No autonomous Agent tool execution.
- No long-duration MIDI generation for practice timer lengths.
