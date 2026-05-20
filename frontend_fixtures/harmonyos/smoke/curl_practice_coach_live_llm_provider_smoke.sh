#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
RUN_ID="${JAMMATE_PRACTICE_COACH_LIVE_LLM_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_practice_coach_live_llm_smoke_${RUN_ID}"
KEEP_TMP="${JAMMATE_PRACTICE_COACH_LIVE_LLM_SMOKE_KEEP_TMP:-false}"

if [[ "${JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE:-}" != "1" ]]; then
  cat >&2 <<'MSG'
This smoke performs a real Practice Coach LLM provider execution through the running FastAPI server.
Set JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1 to opt in.

Server-side env must already be configured before starting uvicorn, for example:
  export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_live_llm.sqlite3
  export JAMMATE_LLM_PROVIDER=openai_compatible
  export JAMMATE_LLM_MODEL=<model>
  export JAMMATE_LLM_API_KEY=<key>
  export JAMMATE_LLM_ENABLE_NETWORK_CALLS=true
  export JAMMATE_LLM_BASE_URL=<openai-compatible-base-url>
  PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000

The HarmonyOS/product request fixture must not include llmActionDecisionResult, providerResult, dbPath, or internal write gates.
MSG
  exit 2
fi

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping Practice Coach live LLM smoke temp dir: ${TMP_DIR}"
  fi
}
trap cleanup EXIT

assert_json_paths() {
  local file="$1"
  shift
  python - <<'PYASSERT' "${file}" "$@"
from __future__ import annotations

import json
import sys
from pathlib import Path

file_path = Path(sys.argv[1])
obj = json.loads(file_path.read_text(encoding="utf-8"))

for assertion in sys.argv[2:]:
    path, expected_raw = assertion.split("=", 1)
    value = obj
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise SystemExit(f"missing JSON path {path!r} in {file_path}")
        value = value[part]
    if expected_raw == "true":
        expected = True
    elif expected_raw == "false":
        expected = False
    elif expected_raw == "null":
        expected = None
    elif expected_raw == "nonempty":
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"expected {path} to be a non-empty string, got {value!r}")
        continue
    elif expected_raw.startswith("oneof:"):
        allowed = set(expected_raw.split(":", 1)[1].split("|"))
        if str(value) not in allowed:
            raise SystemExit(f"expected {path} in {sorted(allowed)!r}, got {value!r}")
        continue
    else:
        expected = expected_raw
    if value != expected:
        raise SystemExit(f"expected {path}={expected!r}, got {value!r}")
PYASSERT
}

post_json() {
  local route="$1"
  local payload="$2"
  local response_file="$3"
  local status
  status=$(curl -sS -o "${response_file}" -w "%{http_code}" -X POST "${BASE_URL}${route}" \
    -H "Content-Type: application/json" \
    -d @"${payload}")
  if [[ "${status}" != "200" ]]; then
    echo "HTTP ${status} from ${route}" >&2
    python -m json.tool "${response_file}" || cat "${response_file}" >&2
    exit 1
  fi
}

prepare_payload() {
  python - <<'PY' "${RUN_ID}" "${TMP_DIR}"
from __future__ import annotations

import json
import sys
from pathlib import Path

run_id = sys.argv[1]
tmp_dir = Path(sys.argv[2])
smoke_dir = Path.cwd()
source = smoke_dir / "product_practice_coach_live_llm_message_request.json"
if not source.exists():
    raise SystemExit(f"missing fixture {source}; run this script from frontend_fixtures/harmonyos/smoke")
obj = json.loads(source.read_text(encoding="utf-8"))
forbidden = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write", "llmActionDecisionResult", "providerResult", "llmDecision"}

def walk(value, path="$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in forbidden:
                raise SystemExit(f"forbidden product field {path}.{key} found")
            walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{path}[{index}]")

walk(obj)
obj["sessionId"] = f"practice-coach-live-llm-{run_id}"
target = tmp_dir / source.name
target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

ROUTE="/agent/harmonyos/practice-coach-session/message/execute"
prepare_payload

echo "== JamMate Practice Coach real LLM provider guarded smoke against ${BASE_URL} =="
echo "This uses a production-shaped request: no llmActionDecisionResult, no providerResult, no dbPath, no internal write gate."

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

echo "2) POST Practice Coach unified message with live provider enabled server-side"
RESPONSE="${TMP_DIR}/live_provider_response.json"
post_json "${ROUTE}" "${TMP_DIR}/product_practice_coach_live_llm_message_request.json" "${RESPONSE}"
assert_json_paths "${RESPONSE}" \
  "ok=true" \
  "debug.realLlmProviderGuardedSmokeVersion=v2_10_20" \
  "debug.llmCalled=true" \
  "debug.networkCallExecuted=true" \
  "debug.llmActionDecisionSource=live_provider" \
  "debug.deterministicFallbackUsed=false" \
  "debug.llmActionDecisionValidation.ok=true" \
  "data.responseType=oneof:ask_clarifying_question|chat_message|request_profile_sheet|practice_plan_proposal|practice_plan_revision|routine_card_ready|cannot_proceed" \
  "data.content=nonempty" \
  "data.conversationStatePersisted=true" \
  "safety.llmCalled=true" \
  "safety.networkCallExecuted=true" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false" \
  "safety.writesHarmonyOSLocalState=false"

echo "PASS: Practice Coach real LLM provider guarded smoke completed."
