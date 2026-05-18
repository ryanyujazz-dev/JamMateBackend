# v2_4_4 Agent Terminal Chat CLI Foundation

## Goal

Add a terminal-first LLM chat entry point for backend debugging while preserving the existing Agent/API/tool-loop safety boundaries.

This delivery stays on `feature/agent-workflow` and does not deepen accompaniment-engine generation, voicing, pattern, expression, pedal, or listening logic.

## Entry point

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat
```

Installed-package console script:

```bash
jammate-agent-chat
```

One-shot smoke:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --once "解释一下 altered dominant"
```

## Provider configuration

The CLI uses the existing provider boundary and is disabled by default. To allow a real provider call, all gates must be explicit:

```bash
export JAMMATE_LLM_PROVIDER=openai_compatible
export JAMMATE_LLM_MODEL="<your-model>"
export JAMMATE_LLM_API_KEY="<your-api-key>"
export JAMMATE_LLM_ENABLE_NETWORK_CALLS=true
# Optional, default: https://api.openai.com/v1
export JAMMATE_LLM_BASE_URL="https://api.openai.com/v1"
# Optional, default: /chat/completions
export JAMMATE_LLM_CHAT_COMPLETIONS_PATH="/chat/completions"
```

Do not commit `.env` files or local secrets into the project package.

## Boundary rules

- The terminal CLI may call a configured OpenAI-compatible chat-completions provider.
- The API runloop preview remains preview-only and does not call an LLM.
- Tool descriptors may be included in context, but terminal chat does not execute tools.
- `autonomous_tool_execution_enabled=false` remains a hard guard.
- Engine access remains adapter/API-boundary only.

## Why this belongs in a CLI package

The feature is not an API route and not an engine capability. It is a developer/operator surface for testing JamMate Agent context packets and provider calls from a terminal. A small `jammate_agent.cli` package is therefore the stable owner.
