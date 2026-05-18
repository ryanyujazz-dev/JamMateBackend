from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

LLM_PROVIDER_BOUNDARY_VERSION = "v2_4_13"
LLM_CONFIG_FILE_VERSION = "v2_4_13"
LOCAL_LLM_CONFIG_FILENAME = ".jammate_agent.env"
USER_LLM_CONFIG_RELATIVE_PATH = (".jammate", "agent_config.env")
LLM_CONFIG_FILE_ENV_VAR = "JAMMATE_AGENT_LLM_CONFIG_FILE"

_TRUTHY = {"1", "true", "yes", "on"}
_SUPPORTED_CHAT_PROVIDERS = {"openai", "openai_compatible"}


def default_llm_config_paths(cwd: str | Path | None = None, home: str | Path | None = None) -> list[Path]:
    """Return config locations in precedence order after explicit environment variables.

    The repo-local file is useful for a checked-out developer workspace; the
    user config file is better for long-lived terminal usage across project
    directories. Neither path should be committed or packaged with secrets.
    """

    base = Path(cwd) if cwd is not None else Path.cwd()
    home_base = Path(home) if home is not None else Path.home()
    return [
        base / LOCAL_LLM_CONFIG_FILENAME,
        home_base.joinpath(*USER_LLM_CONFIG_RELATIVE_PATH),
    ]


def default_user_llm_config_path(home: str | Path | None = None) -> Path:
    home_base = Path(home) if home is not None else Path.home()
    return home_base.joinpath(*USER_LLM_CONFIG_RELATIVE_PATH)


def resolve_llm_config_env(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Merge optional local config with environment variables.

    Precedence is explicit env > explicit config file > repo-local config >
    user config. Raw API keys are kept inside the merged dict only; status
    payloads expose only configured/not-configured booleans.
    """

    source_env = dict(os.environ if env is None else env)
    config_values: dict[str, str] = {}
    config_path: Path | None = None
    explicit_path = (source_env.get(LLM_CONFIG_FILE_ENV_VAR) or "").strip()
    candidates = [Path(explicit_path)] if explicit_path else default_llm_config_paths()
    for candidate in candidates:
        if candidate.exists():
            config_path = candidate
            config_values = load_llm_config_file(candidate)
            break
    merged = dict(config_values)
    for key, value in source_env.items():
        if value is not None and str(value) != "":
            merged[key] = value
    return {
        "env": merged,
        "config_file_path": str(config_path) if config_path else None,
        "config_source": "env+config_file" if config_path else "env",
    }


def load_llm_config_file(path: str | Path) -> dict[str, str]:
    """Load a small .env-style LLM config file without third-party deps."""

    config_path = Path(path)
    values: dict[str, str] = {}
    if not config_path.exists():
        return values
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def write_llm_config_file(path: str | Path, values: dict[str, str]) -> Path:
    """Write a local .env-style provider config with restrictive permissions."""

    config_path = Path(path).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    ordered_keys = [
        "JAMMATE_LLM_PROVIDER",
        "JAMMATE_LLM_MODEL",
        "JAMMATE_LLM_API_KEY_ENV_VAR",
        "JAMMATE_LLM_API_KEY",
        "JAMMATE_LLM_ENABLE_NETWORK_CALLS",
        "JAMMATE_LLM_BASE_URL",
        "JAMMATE_LLM_CHAT_COMPLETIONS_PATH",
        "JAMMATE_LLM_MAX_OUTPUT_TOKENS",
        "JAMMATE_LLM_TEMPERATURE",
        "JAMMATE_LLM_REQUEST_TIMEOUT_SECONDS",
    ]
    lines = [
        "# JamMate Agent terminal LLM config",
        f"# config_file_version={LLM_CONFIG_FILE_VERSION}",
        "# Do not commit this file. It may contain secrets.",
    ]
    seen: set[str] = set()
    for key in ordered_keys:
        if key in values and values[key] not in {None, ""}:
            lines.append(f"{key}={_quote_env_value(str(values[key]))}")
            seen.add(key)
    for key in sorted(set(values) - seen):
        if values[key] not in {None, ""}:
            lines.append(f"{key}={_quote_env_value(str(values[key]))}")
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        config_path.chmod(0o600)
    except OSError:  # pragma: no cover - chmod may be unavailable on some FS.
        pass
    return config_path


def masked_llm_config(values: dict[str, str]) -> dict[str, Any]:
    """Return a display-safe config summary."""

    output: dict[str, Any] = {}
    for key, value in values.items():
        if "KEY" in key or "TOKEN" in key or "SECRET" in key:
            output[key] = "configured" if value else "missing"
        else:
            output[key] = value
    return output


def _quote_env_value(value: str) -> str:
    if value == "" or any(ch.isspace() for ch in value) or any(ch in value for ch in ['#', '"', "'"]):
        return json.dumps(value, ensure_ascii=False)
    return value


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration guard for optional LLM provider integration.

    The provider boundary remains provider-agnostic at the Agent runloop level.
    Network calls are only allowed when all explicit gates are present and a
    caller chooses an execution entry point such as the terminal chat CLI.
    The bounded Agent runloop still previews envelopes and never executes tools.
    """

    provider_name: str = "none"
    model: str | None = None
    api_key_env_var: str = "JAMMATE_LLM_API_KEY"
    api_key_configured: bool = False
    network_calls_enabled: bool = False
    base_url: str = "https://api.openai.com/v1"
    chat_completions_path: str = "/chat/completions"
    max_prompt_chars: int = 12000
    max_output_tokens: int = 1200
    temperature: float = 0.2
    request_timeout_seconds: int = 30
    config_file_path: str | None = None
    config_source: str = "env"
    api_key_value: str | None = field(default=None, repr=False, compare=False)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def provider_configured(self) -> bool:
        return self.provider_name not in {"", "none", "disabled"} and self.api_key_configured and self.network_calls_enabled

    @property
    def supported_provider(self) -> bool:
        return self.provider_name in _SUPPORTED_CHAT_PROVIDERS

    @property
    def terminal_chat_available(self) -> bool:
        return self.provider_configured and self.supported_provider and bool(self.model)

    @property
    def execution_mode(self) -> str:
        if self.terminal_chat_available:
            return "terminal_chat_enabled_runloop_preview_guarded"
        if self.provider_configured:
            return "provider_configured_but_unsupported_or_missing_model"
        return "disabled"

    @property
    def guard_reason(self) -> str:
        if self.provider_name in {"", "none", "disabled"}:
            return "JAMMATE_LLM_PROVIDER is not configured."
        if not self.api_key_configured:
            return f"API key env var {self.api_key_env_var} is not set."
        if not self.network_calls_enabled:
            return "JAMMATE_LLM_ENABLE_NETWORK_CALLS is not enabled."
        if self.provider_name not in _SUPPORTED_CHAT_PROVIDERS:
            return f"Unsupported provider {self.provider_name!r}; supported terminal chat providers: {sorted(_SUPPORTED_CHAT_PROVIDERS)}."
        if not self.model:
            return "JAMMATE_LLM_MODEL is not set."
        return "Terminal chat provider is configured; bounded Agent runloop remains preview-only and tool execution is disabled."

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "LLMProviderConfig":
        resolved = resolve_llm_config_env(env)
        source = resolved["env"]
        provider_name = (source.get("JAMMATE_LLM_PROVIDER") or "none").strip().lower()
        api_key_env_var = (source.get("JAMMATE_LLM_API_KEY_ENV_VAR") or "JAMMATE_LLM_API_KEY").strip()
        api_key_value = source.get(api_key_env_var)
        api_key_configured = bool(api_key_value)
        network_calls_enabled = (source.get("JAMMATE_LLM_ENABLE_NETWORK_CALLS") or "").strip().lower() in _TRUTHY
        return cls(
            provider_name=provider_name,
            model=(source.get("JAMMATE_LLM_MODEL") or None),
            api_key_env_var=api_key_env_var,
            api_key_configured=api_key_configured,
            network_calls_enabled=network_calls_enabled,
            base_url=(source.get("JAMMATE_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
            chat_completions_path=(source.get("JAMMATE_LLM_CHAT_COMPLETIONS_PATH") or "/chat/completions"),
            max_prompt_chars=_safe_int(source.get("JAMMATE_LLM_MAX_PROMPT_CHARS"), 12000),
            max_output_tokens=_safe_int(source.get("JAMMATE_LLM_MAX_OUTPUT_TOKENS"), 1200),
            temperature=_safe_float(source.get("JAMMATE_LLM_TEMPERATURE"), 0.2),
            request_timeout_seconds=_safe_int(source.get("JAMMATE_LLM_REQUEST_TIMEOUT_SECONDS"), 30),
            config_file_path=resolved.get("config_file_path"),
            config_source=resolved.get("config_source") or "env",
            api_key_value=api_key_value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_version": LLM_PROVIDER_BOUNDARY_VERSION,
            "provider_name": self.provider_name,
            "model": self.model,
            "api_key_env_var": self.api_key_env_var,
            "api_key_configured": self.api_key_configured,
            "config_file_path": self.config_file_path,
            "config_source": self.config_source,
            "config_file_version": LLM_CONFIG_FILE_VERSION,
            "network_calls_enabled": self.network_calls_enabled,
            "base_url": self.base_url,
            "chat_completions_path": self.chat_completions_path,
            "provider_configured": self.provider_configured,
            "supported_provider": self.supported_provider,
            "terminal_chat_available": self.terminal_chat_available,
            "execution_mode": self.execution_mode,
            "guard_reason": self.guard_reason,
            "max_prompt_chars": self.max_prompt_chars,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "request_timeout_seconds": self.request_timeout_seconds,
            "extra": dict(self.extra),
        }


@dataclass(frozen=True)
class LLMRequestEnvelope:
    """Provider-neutral request envelope assembled from a ContextPacket."""

    context_packet: dict[str, Any]
    allowed_tools: tuple[str, ...]
    output_contract: dict[str, Any]
    runtime_policy: dict[str, Any]
    messages: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_packet": self.context_packet,
            "allowed_tools": list(self.allowed_tools),
            "output_contract": self.output_contract,
            "runtime_policy": self.runtime_policy,
            "messages": [dict(message) for message in self.messages],
        }


@dataclass(frozen=True)
class LLMProviderResult:
    ok: bool
    content: str | None = None
    provider_name: str = "none"
    model: str | None = None
    error_code: str | None = None
    message: str | None = None
    raw_usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "content": self.content,
            "provider_name": self.provider_name,
            "model": self.model,
            "error_code": self.error_code,
            "message": self.message,
            "raw_usage": dict(self.raw_usage),
        }


class LLMProvider(Protocol):
    """Protocol future concrete providers must satisfy."""

    def status(self) -> dict[str, Any]:
        ...

    def generate(self, envelope: LLMRequestEnvelope) -> LLMProviderResult:
        ...


class DisabledLLMProvider:
    """Default provider boundary: never calls an LLM or network."""

    def __init__(self, config: LLMProviderConfig | None = None) -> None:
        self.config = config or LLMProviderConfig.from_env()

    def status(self) -> dict[str, Any]:
        status = self.config.to_dict()
        status["provider_class"] = self.__class__.__name__
        status["llm_calls_enabled"] = False
        status["terminal_chat_enabled"] = False
        status["autonomous_tool_execution_enabled"] = False
        return status

    def generate(self, envelope: LLMRequestEnvelope) -> LLMProviderResult:
        return LLMProviderResult(
            ok=False,
            provider_name=self.config.provider_name,
            model=self.config.model,
            error_code="LLM_PROVIDER_DISABLED",
            message="LLM provider is not available. Configure JAMMATE_LLM_PROVIDER, JAMMATE_LLM_MODEL, API key, and JAMMATE_LLM_ENABLE_NETWORK_CALLS for terminal chat.",
        )


class OpenAICompatibleChatProvider:
    """Small stdlib-only Chat Completions provider for terminal debugging.

    This class intentionally lives behind explicit env guards and is not used by
    the bounded runloop to execute tools. It posts a provider-neutral message
    envelope to an OpenAI-compatible `/chat/completions` endpoint.
    """

    def __init__(self, config: LLMProviderConfig | None = None) -> None:
        self.config = config or LLMProviderConfig.from_env()

    def status(self) -> dict[str, Any]:
        status = self.config.to_dict()
        status["provider_class"] = self.__class__.__name__
        status["llm_calls_enabled"] = self.config.terminal_chat_available
        status["terminal_chat_enabled"] = self.config.terminal_chat_available
        status["autonomous_tool_execution_enabled"] = False
        status["tool_execution_enabled"] = False
        return status

    def generate(self, envelope: LLMRequestEnvelope) -> LLMProviderResult:
        if not self.config.terminal_chat_available:
            return DisabledLLMProvider(self.config).generate(envelope)
        api_key = self.config.api_key_value or os.environ.get(self.config.api_key_env_var)
        if not api_key:
            return LLMProviderResult(
                ok=False,
                provider_name=self.config.provider_name,
                model=self.config.model,
                error_code="LLM_API_KEY_MISSING",
                message=f"API key env var {self.config.api_key_env_var} is not set.",
            )
        endpoint = self._endpoint()
        payload = {
            "model": self.config.model,
            "messages": _trim_messages_for_prompt(envelope.messages, self.config.max_prompt_chars),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return LLMProviderResult(
                ok=False,
                provider_name=self.config.provider_name,
                model=self.config.model,
                error_code="LLM_HTTP_ERROR",
                message=f"HTTP {exc.code}: {_compact_error_body(body)}",
            )
        except Exception as exc:  # pragma: no cover - exact network failures vary by machine.
            return LLMProviderResult(
                ok=False,
                provider_name=self.config.provider_name,
                model=self.config.model,
                error_code="LLM_REQUEST_FAILED",
                message=str(exc),
            )

        content = _extract_chat_content(response_payload)
        return LLMProviderResult(
            ok=bool(content),
            content=content,
            provider_name=self.config.provider_name,
            model=self.config.model,
            error_code=None if content else "LLM_EMPTY_RESPONSE",
            message=None if content else "Provider response did not contain choices[0].message.content.",
            raw_usage=dict(response_payload.get("usage") or {}),
        )

    def _endpoint(self) -> str:
        path = self.config.chat_completions_path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.config.base_url}{path}"


def build_llm_provider_from_env(env: dict[str, str] | None = None) -> LLMProvider:
    config = LLMProviderConfig.from_env(env)
    if config.terminal_chat_available:
        return OpenAICompatibleChatProvider(config)
    return DisabledLLMProvider(config)


def build_request_envelope(context_packet: Any, conversation_history: list[dict[str, str]] | None = None) -> LLMRequestEnvelope:
    """Build a provider-neutral envelope from a ContextPacket-like object."""

    data = context_packet.to_dict() if hasattr(context_packet, "to_dict") else dict(context_packet)
    runtime_policy = dict(data.get("runtime_policy") or {})
    allowed_tools = tuple(str(tool) for tool in data.get("allowed_tools") or [])
    output_contract = dict(data.get("output_contract") or {})
    user_text = str((data.get("user_request") or {}).get("text") or "")
    system_context = data.get("system_product_context") or {}
    tool_note = (
        "Tool descriptors may be shown for planning context only. "
        "Do not claim that tools were executed unless a deterministic route actually executed them."
    )
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are JamMate Agent. Follow the task-scoped context packet, allowed tools, output contract, and engine/Agent/API boundaries.",
        },
        {
            "role": "developer",
            "content": f"System product context: {system_context}\n{tool_note}",
        },
    ]
    if conversation_history:
        messages.extend(_sanitize_history(conversation_history))
    messages.append({"role": "user", "content": user_text})
    return LLMRequestEnvelope(
        context_packet=data,
        allowed_tools=allowed_tools,
        output_contract=output_contract,
        runtime_policy=runtime_policy,
        messages=tuple(messages),
    )


def _sanitize_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    clean: list[dict[str, str]] = []
    for message in history[-12:]:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            clean.append({"role": role, "content": content.strip()})
    return clean


def _trim_messages_for_prompt(messages: tuple[dict[str, str], ...], max_chars: int) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    remaining = max_chars
    for message in reversed(messages):
        content = message.get("content", "")
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = content[-remaining:]
        output.append({"role": message.get("role", "user"), "content": content})
        remaining -= len(content)
    return list(reversed(output))


def _extract_chat_content(payload: dict[str, Any]) -> str | None:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip() or None
    return None


def _compact_error_body(body: str) -> str:
    body = body.strip().replace("\n", " ")
    return body[:500]


def _safe_int(raw: str | None, default: int) -> int:
    try:
        return int(raw) if raw not in {None, ""} else default
    except ValueError:
        return default


def _safe_float(raw: str | None, default: float) -> float:
    try:
        return float(raw) if raw not in {None, ""} else default
    except ValueError:
        return default
