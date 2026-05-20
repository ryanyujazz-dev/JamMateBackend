#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
RUN_ID="${JAMMATE_AGENT_PRODUCT_CONTRACT_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_agent_black_box_product_contract_smoke_${RUN_ID}"
KEEP_TMP="${JAMMATE_AGENT_PRODUCT_CONTRACT_SMOKE_KEEP_TMP:-false}"

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping product-contract smoke temp dir: ${TMP_DIR}"
  fi
}
trap cleanup EXIT

COMPLETION_PAYLOAD="${TMP_DIR}/product_contract_routine_completion_request.json"
GUIDANCE_PAYLOAD="${TMP_DIR}/product_contract_today_guidance_request.json"
COMPLETION_RESPONSE="${TMP_DIR}/routine_completion_record_execute_response.json"
GUIDANCE_RESPONSE="${TMP_DIR}/today_practice_guidance_preview_response.json"

python - <<'PY' "${RUN_ID}" "${COMPLETION_PAYLOAD}" "${GUIDANCE_PAYLOAD}"
from __future__ import annotations

import json
import sys
from pathlib import Path

run_id = sys.argv[1]
completion_target = Path(sys.argv[2])
guidance_target = Path(sys.argv[3])
smoke_dir = Path.cwd()
completion_source = smoke_dir / "product_contract_routine_completion_request.json"
guidance_source = smoke_dir / "product_contract_today_guidance_request.json"
if not completion_source.exists() or not guidance_source.exists():
    raise SystemExit("Run this script from frontend_fixtures/harmonyos/smoke so product contract fixture JSON files are visible.")

completion = json.loads(completion_source.read_text(encoding="utf-8"))
guidance = json.loads(guidance_source.read_text(encoding="utf-8"))
forbidden = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write"}

def assert_no_forbidden(obj, path="$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in forbidden:
                raise SystemExit(f"product contract fixture leaked backend/internal field at {path}.{key}")
            assert_no_forbidden(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            assert_no_forbidden(item, f"{path}[{index}]")

assert_no_forbidden(completion)
assert_no_forbidden(guidance)

# Keep the request a HarmonyOS product request while making repeated smoke runs
# safe against idempotency replays. The backend derives idempotency from the
# frontend-owned sessionId when no explicit internal key is sent.
completion["sessionId"] = f"practice-session-product-smoke-{run_id}"
guidance["sessionId"] = f"agent-session-product-smoke-{run_id}"
completion.setdefault("routineCompletionRecord", {})["completedAt"] = "2026-05-20T20:30:00-07:00"
completion.setdefault("routineCompletionRecord", {})["notes"] = f"product contract smoke run {run_id}"

assert_no_forbidden(completion)
assert_no_forbidden(guidance)
completion_target.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
guidance_target.write_text(json.dumps(guidance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

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
    elif expected_raw.startswith("int>="):
        threshold = int(expected_raw.split(">=", 1)[1])
        if not isinstance(value, int) or value < threshold:
            raise SystemExit(f"expected {path} >= {threshold}, got {value!r}")
        continue
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

assert_product_payload_has_no_internal_fields() {
  local payload="$1"
  python - <<'PYCHECK' "${payload}"
from __future__ import annotations

import json
import sys
from pathlib import Path

obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
forbidden = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write"}

def walk(value, path="$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in forbidden:
                raise SystemExit(f"forbidden internal field {path}.{key} found in product payload")
            walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{path}[{index}]")

walk(obj)
PYCHECK
}

post_json() {
  local route="$1"
  local payload="$2"
  local response_file="$3"
  local status_file="${response_file}.status"
  local status
  status=$(curl -sS -o "${response_file}" -w "%{http_code}" -X POST "${BASE_URL}${route}" \
    -H "Content-Type: application/json" \
    -d @"${payload}")
  echo "${status}" > "${status_file}"
  if [[ "${status}" != "200" ]]; then
    echo "HTTP ${status} from ${route}" >&2
    python -m json.tool "${response_file}" || cat "${response_file}" >&2
    exit 1
  fi
}

echo "== JamMate HarmonyOS Agent black-box product-contract smoke against ${BASE_URL} =="
echo "Request payloads intentionally omit dbPath/sqliteDbPath and clientConfirmedRecordWrite/internal gate fields."
echo "Backend DB path is owned by the running server via JAMMATE_AGENT_CONTEXT_DB_PATH or its local-dev default."

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

assert_product_payload_has_no_internal_fields "${COMPLETION_PAYLOAD}"
assert_product_payload_has_no_internal_fields "${GUIDANCE_PAYLOAD}"

echo "2) POST /agent/harmonyos/routine-completion-record/execute"
post_json "/agent/harmonyos/routine-completion-record/execute" "${COMPLETION_PAYLOAD}" "${COMPLETION_RESPONSE}"
assert_json_paths "${COMPLETION_RESPONSE}" \
  "ok=true" \
  "code=routine_completion_record_persisted" \
  "message=nonempty" \
  "data.content=nonempty" \
  "data.completionRecordPersisted=true" \
  "data.nextTodayGuidanceCanReadHistory=true" \
  "debug.backendDatabaseWritten=true" \
  "debug.sqliteRowCountWritten=int>=1" \
  "safety.backendSQLiteWriteMayOccur=true" \
  "safety.writesHarmonyOSLocalState=false" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false" \
  "safety.createsPostSessionRecommendationCard=false"

echo "3) POST /agent/harmonyos/today-practice-guidance/preview"
post_json "/agent/harmonyos/today-practice-guidance/preview" "${GUIDANCE_PAYLOAD}" "${GUIDANCE_RESPONSE}"
assert_json_paths "${GUIDANCE_RESPONSE}" \
  "ok=true" \
  "code=oneof:today_guidance_ready|today_guidance_needs_context_or_provider" \
  "message=nonempty" \
  "data.content=nonempty" \
  "data.contextSource=sqlite_backend" \
  "data.requiresUserConfirmationBeforeRoutineStart=true" \
  "debug.sqliteReadbackAttempted=true" \
  "debug.backendDatabaseRead=true" \
  "debug.sqliteRowsRead=int>=1" \
  "safety.backendSQLiteWriteMayOccur=false" \
  "safety.writesHarmonyOSLocalState=false" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false" \
  "safety.createsPostSessionRecommendationCard=false"

echo "PASS: HarmonyOS Agent black-box product-contract smoke completed."
