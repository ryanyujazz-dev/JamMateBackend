# v2_4_12 — Agent Terminal LLM Config Wizard

## Goal

`v2_4_12_agent_terminal_llm_config_wizard` improves terminal LLM chat setup without changing Agent tool execution or accompaniment engine behavior.

The previous developer flow required manual shell exports before terminal chat could call a provider. This version keeps environment variables as the highest-precedence mechanism, but adds a local config-file setup and doctor flow so a developer can run terminal chat with less friction.

## Scope

In scope:

- `jammate-agent-chat setup`
- `jammate-agent-chat doctor`
- `jammate-agent-chat config-path`
- `--config-file <path>` support for terminal chat
- automatic config-file loading from repo-local `.jammate_agent.env` or user-level `~/.jammate/agent_config.env`
- API-key masking in status, trace, and setup/doctor output

Out of scope:

- autonomous tool execution
- deterministic workflow dispatch from LLM text
- engine adapter calls from terminal chat
- provider SDK dependencies
- HarmonyOS settings UI
- accompaniment generation changes

## Precedence

LLM config is resolved in this order:

```text
1. explicit environment variables
2. JAMMATE_AGENT_LLM_CONFIG_FILE=<path>
3. repo-local .jammate_agent.env
4. ~/.jammate/agent_config.env
5. disabled / guarded mode
```

Explicit environment variables still override values loaded from a config file.

## Commands

Create a local config:

```bash
jammate-agent-chat setup
```

Non-interactive setup:

```bash
jammate-agent-chat setup \
  --config-file ~/.jammate/agent_config.env \
  --provider openai_compatible \
  --model "your-model" \
  --api-key "your-api-key" \
  --base-url "https://api.openai.com/v1" \
  --yes
```

Inspect config:

```bash
jammate-agent-chat doctor
```

Use a specific config file:

```bash
jammate-agent-chat --config-file ~/.jammate/agent_config.env
```

Print the default config path:

```bash
jammate-agent-chat config-path
```

## Secret Policy

- API key values are never printed in `setup` output.
- API key values are never printed in `doctor` output.
- API key values are not included in `LLMProviderConfig.to_dict()`.
- API key values are not written into Agent trace payloads.
- `.jammate_agent.env`, `.jammate_agent.env.*`, and `agent_config.env` are ignored by git/package cleanup.

## Runtime Guard

Even with a valid provider config:

```text
terminal chat may call the configured LLM provider
terminal chat may preview JSON tool-call candidates
tool execution remains disabled
adapter / engine calls remain disabled
API runloop preview remains provider-call disabled
```

`v2_4_12` is still an Agent workflow debugging milestone, not an autonomous execution milestone.
