from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import PRACTICE_COACH_REAL_LLM_PROVIDER_GUARDED_SMOKE_VERSION

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"


class _RecordingChatHandler(BaseHTTPRequestHandler):
    requests: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.__class__.requests.append(
            {
                "path": self.path,
                "authorization_present": bool(self.headers.get("Authorization")),
                "payload": payload,
            }
        )
        action = {
            "responseType": "request_profile_sheet",
            "message": "为了给你安排更准确的练习，我需要先了解你的基础信息。",
            "missingFields": ["practice_profile.primary_instrument", "practice_profile.skill_level"],
            "nextClientActions": ["open_profile_sheet", "submit_profile_form_result"],
        }
        body = {
            "choices": [{"message": {"content": json.dumps(action, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 321, "completion_tokens": 48, "total_tokens": 369},
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        return


def _start_stub_provider() -> tuple[HTTPServer, str]:
    _RecordingChatHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), _RecordingChatHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((SMOKE_DIR / name).read_text(encoding="utf-8"))


def _assert_no_key_recursive(value: Any, forbidden: set[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert key not in forbidden, f"forbidden field {path}.{key} found"
            _assert_no_key_recursive(nested, forbidden, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_key_recursive(item, forbidden, f"{path}[{index}]")


def test_live_provider_product_fixture_does_not_contain_injected_llm_action_or_backend_fields() -> None:
    payload = _load_json("product_practice_coach_live_llm_message_request.json")
    forbidden = {
        "dbPath",
        "sqliteDbPath",
        "sqlite_db_path",
        "clientConfirmedRecordWrite",
        "client_confirmed_record_write",
        "llmActionDecisionResult",
        "providerResult",
        "llmDecision",
    }
    _assert_no_key_recursive(payload, forbidden)
    assert payload["userId"]
    assert payload["sessionId"]
    assert payload["deviceId"]
    assert payload["userMessage"] == "今天该练什么？"


def test_unified_message_execute_can_call_openai_compatible_provider_under_explicit_env_guards(tmp_path: Path, monkeypatch) -> None:
    server, base_url = _start_stub_provider()
    try:
        monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_real_llm_provider.sqlite3"))
        monkeypatch.setenv("JAMMATE_LLM_PROVIDER", "openai_compatible")
        monkeypatch.setenv("JAMMATE_LLM_MODEL", "local-practice-coach-stub")
        monkeypatch.setenv("JAMMATE_LLM_API_KEY", "test-key-not-secret")
        monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "true")
        monkeypatch.setenv("JAMMATE_LLM_BASE_URL", base_url)
        monkeypatch.setenv("JAMMATE_LLM_CHAT_COMPLETIONS_PATH", "/chat/completions")
        monkeypatch.setenv("JAMMATE_LLM_MAX_OUTPUT_TOKENS", "300")
        monkeypatch.setenv("JAMMATE_LLM_REQUEST_TIMEOUT_SECONDS", "5")

        client = TestClient(app)
        payload = _load_json("product_practice_coach_live_llm_message_request.json")
        payload["sessionId"] = "v2-10-20-live-provider-stub"
        response = client.post(ROUTE, json=payload)
        assert response.status_code == 200
        body = response.json()
    finally:
        server.shutdown()
        server.server_close()

    assert body["ok"] is True
    assert body["data"]["responseType"] == "request_profile_sheet"
    assert body["data"]["profileSheetIntentReady"] is True
    assert body["data"]["sheetIntent"]["sheetType"] == "practice_profile_setup"
    assert body["debug"]["realLlmProviderGuardedSmokeVersion"] == PRACTICE_COACH_REAL_LLM_PROVIDER_GUARDED_SMOKE_VERSION
    assert body["debug"]["decisionMode"] == "llm_action_decision"
    assert body["debug"]["llmActionDecisionSource"] == "live_provider"
    assert body["debug"]["deterministicFallbackUsed"] is False
    assert body["debug"]["llmActionDecisionValidation"]["ok"] is True
    assert body["debug"]["llmProviderStatus"]["provider_class"] == "OpenAICompatibleChatProvider"
    assert body["debug"]["llmProviderStatus"]["llm_calls_enabled"] is True
    assert body["debug"]["llmProviderResult"]["ok"] is True
    assert body["debug"]["llmCalled"] is True
    assert body["debug"]["networkCallExecuted"] is True
    assert body["safety"]["llmCalled"] is True
    assert body["safety"]["networkCallExecuted"] is True
    assert body["safety"]["startsRoutine"] is False
    assert body["safety"]["callsEngineAdapter"] is False
    assert body["safety"]["createsMidiAsset"] is False
    assert body["safety"]["startsPlayback"] is False
    assert body["safety"]["writesHarmonyOSLocalState"] is False

    assert len(_RecordingChatHandler.requests) == 1
    provider_request = _RecordingChatHandler.requests[0]
    assert provider_request["path"] == "/chat/completions"
    assert provider_request["authorization_present"] is True
    network_payload = provider_request["payload"]
    assert network_payload["model"] == "local-practice-coach-stub"
    assert network_payload["max_tokens"] == 300
    assert [message["role"] for message in network_payload["messages"]] == ["system", "user", "user"]
    joined = "\n".join(message["content"] for message in network_payload["messages"])
    assert "STABLE_PRODUCT_CONTRACT_JSON" in joined
    assert "PRACTICE_CONTEXT_PACKET_JSON" in joined
    assert "CURRENT_USER_MESSAGE_JSON" in joined
    assert "v2-10-20-live-provider-stub" not in joined


def test_live_provider_curl_smoke_is_opt_in_and_documents_server_side_llm_env() -> None:
    script = SMOKE_DIR / "curl_practice_coach_live_llm_provider_smoke.sh"
    readme = SMOKE_DIR / "README.md"
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_REAL_LLM_PROVIDER_EXECUTION_GUARDED_SMOKE_V2_10_20.md"
    api_doc = ROOT / "docs" / "API_CONTRACT_V2.md"

    assert script.exists()
    script_text = script.read_text(encoding="utf-8")
    assert "JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE" in script_text
    assert "product_practice_coach_live_llm_message_request.json" in script_text
    assert "llmActionDecisionResult" in script_text
    assert "debug.llmActionDecisionSource=live_provider" in script_text
    assert "debug.networkCallExecuted=true" in script_text
    assert "safety.startsRoutine=false" in script_text
    assert "safety.callsEngineAdapter=false" in script_text

    for path in (readme, dev_doc, api_doc):
        text = path.read_text(encoding="utf-8")
        assert "v2_10_20" in text
        assert "real LLM provider" in text or "真实 LLM provider" in text
        assert "JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE" in text
        assert "llmActionDecisionResult" in text
        assert "practice-coach-session/message/execute" in text


def test_smoke_pack_lists_v2_10_20_live_provider_smoke() -> None:
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))
    assert pack["version"] == "v2_10_20"
    section = pack["practice_coach_real_llm_provider_guarded_smoke"]
    assert section["endpoint"] == "POST /agent/harmonyos/practice-coach-session/message/execute"
    assert section["script"] == "curl_practice_coach_live_llm_provider_smoke.sh"
    assert section["fixture"] == "product_practice_coach_live_llm_message_request.json"
    assert section["opt_in_env"] == "JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1"
    assert section["product_request_forbidden_fields"]["llmActionDecisionResult"] is True
    assert section["safety_expectations"]["startsRoutine"] is False
    assert section["safety_expectations"]["callsEngineAdapter"] is False
    assert section["safety_expectations"]["createsMidiAsset"] is False
