from __future__ import annotations

import ast
from io import StringIO
from pathlib import Path

from jammate_agent.cli.terminal_chat import run_interactive_chat
from jammate_agent.core.llm_provider import (
    LLM_CONFIG_FILE_ENV_VAR,
    LLMProviderConfig,
    load_llm_config_file,
    write_llm_config_file,
)

ROOT = Path(__file__).resolve().parents[1]


def test_llm_config_file_can_enable_terminal_provider_without_shell_exports(tmp_path: Path) -> None:
    config_path = tmp_path / "agent.env"
    write_llm_config_file(
        config_path,
        {
            "JAMMATE_LLM_PROVIDER": "openai_compatible",
            "JAMMATE_LLM_MODEL": "test-model",
            "JAMMATE_LLM_API_KEY": "fake-test-secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
            "JAMMATE_LLM_BASE_URL": "https://example.test/v1",
        },
    )

    config = LLMProviderConfig.from_env({LLM_CONFIG_FILE_ENV_VAR: str(config_path)})
    assert config.terminal_chat_available is True
    assert config.provider_name == "openai_compatible"
    assert config.model == "test-model"
    assert config.api_key_configured is True
    assert config.config_file_path == str(config_path)
    assert config.to_dict()["api_key_configured"] is True
    assert "fake-test-secret" not in str(config.to_dict())


def test_explicit_environment_overrides_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "agent.env"
    write_llm_config_file(
        config_path,
        {
            "JAMMATE_LLM_PROVIDER": "openai_compatible",
            "JAMMATE_LLM_MODEL": "file-model",
            "JAMMATE_LLM_API_KEY": "fake-file-secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
        },
    )
    config = LLMProviderConfig.from_env(
        {
            LLM_CONFIG_FILE_ENV_VAR: str(config_path),
            "JAMMATE_LLM_MODEL": "env-model",
            "JAMMATE_LLM_API_KEY": "fake-env-secret",
        }
    )
    assert config.model == "env-model"
    assert config.api_key_value == "fake-env-secret"
    assert "fake-env-secret" not in str(config.to_dict())


def test_setup_command_writes_local_config_without_echoing_secret(tmp_path: Path) -> None:
    config_path = tmp_path / "agent.env"
    out = StringIO()
    code = run_interactive_chat(
        [
            "setup",
            "--config-file",
            str(config_path),
            "--provider",
            "openai_compatible",
            "--model",
            "wizard-model",
            "--api-key",
            "fake-wizard-secret",
            "--base-url",
            "https://example.test/v1",
            "--yes",
        ],
        stdout=out,
    )
    text = out.getvalue()
    assert code == 0
    assert config_path.exists()
    assert "LLMConfigSetup> saved" in text
    assert "wizard-model" in text
    assert "api_key_configured: True" in text
    assert "fake-wizard-secret" not in text
    values = load_llm_config_file(config_path)
    assert values["JAMMATE_LLM_MODEL"] == "wizard-model"
    assert values["JAMMATE_LLM_API_KEY"] == "fake-wizard-secret"


def test_doctor_reads_config_and_masks_secret(tmp_path: Path) -> None:
    config_path = tmp_path / "agent.env"
    write_llm_config_file(
        config_path,
        {
            "JAMMATE_LLM_PROVIDER": "openai_compatible",
            "JAMMATE_LLM_MODEL": "doctor-model",
            "JAMMATE_LLM_API_KEY": "fake-doctor-secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
        },
    )
    out = StringIO()
    code = run_interactive_chat(["doctor", "--config-file", str(config_path)], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "LLMConfigDoctor>" in text
    assert "status: ready" in text
    assert "doctor-model" in text
    assert "api_key_configured: True" in text
    assert "fake-doctor-secret" not in text
    assert "tool_execution_enabled: False" in text


def test_unconfigured_chat_prints_setup_hint(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(LLM_CONFIG_FILE_ENV_VAR, str(tmp_path / "missing.env"))
    monkeypatch.delenv("JAMMATE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("JAMMATE_LLM_API_KEY", raising=False)
    out = StringIO()
    code = run_interactive_chat(["--once", "hello"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "Provider status:" in text
    assert "LLM setup hint:" in text
    assert "jammate-agent-chat setup" in text
    assert "JamMate[guarded]> LLM_PROVIDER_DISABLED" in text


def test_config_path_command_prints_default_path() -> None:
    out = StringIO()
    code = run_interactive_chat(["config-path"], stdout=out)
    assert code == 0
    assert "Default user LLM config path:" in out.getvalue()
    assert "JAMMATE_AGENT_LLM_CONFIG_FILE" in out.getvalue()


def test_help_mentions_setup_and_doctor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(LLM_CONFIG_FILE_ENV_VAR, str(tmp_path / "missing.env"))
    out = StringIO()
    code = run_interactive_chat(["--once", "/help"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "setup        # shell subcommand" in text
    assert "doctor       # shell subcommand" in text
    assert "Use `jammate-agent-chat setup` once" in text


def test_llm_config_wizard_stays_agent_only_and_no_provider_sdk_imports() -> None:
    for rel in [
        "src/jammate_agent/cli/terminal_chat.py",
        "src/jammate_agent/core/llm_provider.py",
    ]:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
        assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
