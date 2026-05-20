#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
RUN_ID="${JAMMATE_PRACTICE_COACH_LLM_ACTION_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_practice_coach_llm_action_smoke_${RUN_ID}"
KEEP_TMP="${JAMMATE_PRACTICE_COACH_LLM_ACTION_SMOKE_KEEP_TMP:-false}"

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping Practice Coach LLM action smoke temp dir: ${TMP_DIR}"
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
    elif expected_raw.startswith("int>="):
        threshold = int(expected_raw.split(">=", 1)[1])
        if not isinstance(value, int) or value < threshold:
            raise SystemExit(f"expected {path} >= {threshold}, got {value!r}")
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

prepare_payloads() {
  python - <<'PY' "${RUN_ID}" "${TMP_DIR}"
from __future__ import annotations

import json
import sys
from pathlib import Path

run_id = sys.argv[1]
tmp_dir = Path(sys.argv[2])
smoke_dir = Path.cwd()

product_names = [
    "product_practice_coach_message_today_request.json",
    "product_practice_coach_profile_form_submit_request.json",
]
smoke_names = [
    "smoke_llm_action_ask_clarifying_request.json",
    "smoke_llm_action_request_profile_sheet_request.json",
    "smoke_llm_action_plan_proposal_request.json",
    "smoke_llm_action_routine_card_ready_request.json",
]
for name in product_names + smoke_names:
    source = smoke_dir / name
    if not source.exists():
        raise SystemExit(f"missing fixture {source}; run this script from frontend_fixtures/harmonyos/smoke")

forbidden_product = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write", "llmActionDecisionResult", "providerResult"}
forbidden_internal = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write"}

def walk_no_keys(value, forbidden, *, path="$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in forbidden:
                raise SystemExit(f"forbidden field {path}.{key} found")
            walk_no_keys(nested, forbidden, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk_no_keys(item, forbidden, path=f"{path}[{index}]")

# Product fixtures are the real frontend contract. They must not include backend internals or injected LLM results.
for name in product_names:
    obj = json.loads((smoke_dir / name).read_text(encoding="utf-8"))
    walk_no_keys(obj, forbidden_product)
    obj["sessionId"] = f"practice-coach-product-{run_id}"
    target = tmp_dir / name
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Smoke fixtures intentionally inject LLM action JSON so backend/device smoke can validate every responseType without live provider setup.
for name in smoke_names:
    obj = json.loads((smoke_dir / name).read_text(encoding="utf-8"))
    walk_no_keys(obj, forbidden_internal)
    if "llmActionDecisionResult" not in obj:
        raise SystemExit(f"smoke fixture {name} must include llmActionDecisionResult to simulate the LLM boundary")
    if name in {"smoke_llm_action_plan_proposal_request.json", "smoke_llm_action_routine_card_ready_request.json"}:
        obj["sessionId"] = f"practice-coach-smoke-plan-{run_id}"
    else:
        obj["sessionId"] = f"practice-coach-smoke-{name.replace('.json', '')}-{run_id}"
    target = tmp_dir / name
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

ROUTE="/agent/harmonyos/practice-coach-session/message/execute"
prepare_payloads

echo "== JamMate Practice Coach LLM action smoke against ${BASE_URL} =="
echo "Product fixtures omit LLM injection. smoke_llm_action_* fixtures use llmActionDecisionResult only to simulate the LLM provider boundary."

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

echo "2) Product-shaped request without injected LLM action"
PRODUCT_RESPONSE="${TMP_DIR}/product_today_response.json"
post_json "${ROUTE}" "${TMP_DIR}/product_practice_coach_message_today_request.json" "${PRODUCT_RESPONSE}"
assert_json_paths "${PRODUCT_RESPONSE}" \
  "ok=true" \
  "data.responseType=oneof:ask_clarifying_question|chat_message|request_profile_sheet|practice_plan_proposal|cannot_proceed" \
  "data.content=nonempty" \
  "data.conversationStatePersisted=true" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false" \
  "safety.writesHarmonyOSLocalState=false"

echo "3) LLM action: ask_clarifying_question"
ASK_RESPONSE="${TMP_DIR}/ask_clarifying_response.json"
post_json "${ROUTE}" "${TMP_DIR}/smoke_llm_action_ask_clarifying_request.json" "${ASK_RESPONSE}"
assert_json_paths "${ASK_RESPONSE}" \
  "ok=true" \
  "debug.decisionMode=llm_action_decision" \
  "debug.llmActionDecisionSource=injected_provider_result" \
  "debug.deterministicFallbackUsed=false" \
  "data.responseType=ask_clarifying_question" \
  "data.content=nonempty" \
  "data.conversationStatePersisted=true" \
  "data.routineStartEnabled=false" \
  "safety.startsRoutine=false" \
  "safety.createsMidiAsset=false"

echo "4) LLM action: request_profile_sheet"
SHEET_RESPONSE="${TMP_DIR}/request_profile_sheet_response.json"
post_json "${ROUTE}" "${TMP_DIR}/smoke_llm_action_request_profile_sheet_request.json" "${SHEET_RESPONSE}"
assert_json_paths "${SHEET_RESPONSE}" \
  "ok=true" \
  "debug.decisionMode=llm_action_decision" \
  "debug.llmActionDecisionSource=injected_provider_result" \
  "data.responseType=request_profile_sheet" \
  "data.profileSheetIntentReady=true" \
  "data.sheetIntent.sheetType=practice_profile_setup" \
  "safety.frontendMayOpenNativeSheet=true" \
  "safety.frontendOwnsNativeSheetRendering=true" \
  "safety.startsRoutine=false"

echo "5) Product profile form submission"
PROFILE_RESPONSE="${TMP_DIR}/profile_form_submit_response.json"
post_json "${ROUTE}" "${TMP_DIR}/product_practice_coach_profile_form_submit_request.json" "${PROFILE_RESPONSE}"
assert_json_paths "${PROFILE_RESPONSE}" \
  "ok=true" \
  "data.responseType=chat_message" \
  "data.stateAfter.collected_fields.practice_profile.primary_instrument=piano" \
  "data.conversationStatePersisted=true" \
  "safety.writesHarmonyOSLocalState=false" \
  "safety.startsRoutine=false"

echo "6) LLM action: practice_plan_proposal"
PLAN_RESPONSE="${TMP_DIR}/plan_proposal_response.json"
post_json "${ROUTE}" "${TMP_DIR}/smoke_llm_action_plan_proposal_request.json" "${PLAN_RESPONSE}"
assert_json_paths "${PLAN_RESPONSE}" \
  "ok=true" \
  "debug.decisionMode=llm_action_decision" \
  "debug.llmActionDecisionSource=injected_provider_result" \
  "data.responseType=practice_plan_proposal" \
  "data.planProposalReady=true" \
  "data.planProposal.confirmationStatus=awaiting_user_confirmation" \
  "data.stateAfter.awaiting_confirmation=true" \
  "data.routineCardPayload=null" \
  "data.routineStartEnabled=false" \
  "safety.startsRoutine=false" \
  "safety.createsMidiAsset=false"

echo "7) LLM action: routine_card_ready from persisted draft plan"
CARD_RESPONSE="${TMP_DIR}/routine_card_ready_response.json"
post_json "${ROUTE}" "${TMP_DIR}/smoke_llm_action_routine_card_ready_request.json" "${CARD_RESPONSE}"
assert_json_paths "${CARD_RESPONSE}" \
  "ok=true" \
  "debug.decisionMode=llm_action_decision" \
  "debug.llmActionDecisionSource=injected_provider_result" \
  "data.responseType=routine_card_ready" \
  "data.routineCardReady=true" \
  "data.routineCardPayload.title=今日 Bossa Comping 稳定性练习" \
  "data.routineCardPayload.backendStartsRoutine=false" \
  "data.routineCardPayload.requiresUserTapToStart=true" \
  "data.routineStartEnabled=true" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false" \
  "safety.writesHarmonyOSLocalState=false"

echo "PASS: Practice Coach LLM action fixture smoke completed."
