#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
DB_PATH="${2:-/tmp/jammate_agent_harmonyos_today_guidance_runtime_smoke.sqlite}"
RUN_ID="${JAMMATE_AGENT_RUNTIME_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_agent_today_guidance_runtime_smoke_${RUN_ID}"
KEEP_TMP="${JAMMATE_AGENT_RUNTIME_SMOKE_KEEP_TMP:-false}"

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping runtime smoke temp dir: ${TMP_DIR}"
  fi
}
trap cleanup EXIT

COMPLETION_PAYLOAD="${TMP_DIR}/routine_completion_record_execute.json"
GUIDANCE_PAYLOAD="${TMP_DIR}/today_practice_guidance_preview.json"
COMPLETION_RESPONSE="${TMP_DIR}/routine_completion_record_execute_response.json"
GUIDANCE_RESPONSE="${TMP_DIR}/today_practice_guidance_preview_response.json"

python - <<'PY' "${DB_PATH}" "${RUN_ID}" "${COMPLETION_PAYLOAD}" "${GUIDANCE_PAYLOAD}"
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
# When this script is run through bash, __file__ is not the shell script path.
# Use the current working directory first because the README asks callers to run
# this from frontend_fixtures/harmonyos/smoke.
smoke_dir = Path.cwd()
completion_source = smoke_dir / "smoke_agent_harmonyos_routine_completion_record_execute.json"
guidance_source = smoke_dir / "smoke_agent_harmonyos_today_practice_guidance_preview.json"
if not completion_source.exists() or not guidance_source.exists():
    raise SystemExit("Run this script from frontend_fixtures/harmonyos/smoke so fixture JSON files are visible.")

db_path = sys.argv[1]
run_id = sys.argv[2]
completion_target = Path(sys.argv[3])
guidance_target = Path(sys.argv[4])
completion = json.loads(completion_source.read_text(encoding="utf-8"))
guidance = json.loads(guidance_source.read_text(encoding="utf-8"))
completion["sqliteDbPath"] = db_path
guidance["sqliteDbPath"] = db_path
completion["idempotencyKey"] = f"harmonyos-runtime-smoke:routine-completion:{run_id}"
completion.setdefault("routineCompletionRecord", {})["sessionId"] = f"harmonyos_runtime_smoke_session_{run_id}"
completion.setdefault("routineCompletionRecord", {})["source"] = "harmonyos_runtime_smoke"
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

echo "== JamMate HarmonyOS Agent runtime smoke against ${BASE_URL} =="
echo "DB path: ${DB_PATH}"

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

echo "2) POST /agent/harmonyos/routine-completion-record/execute"
post_json "/agent/harmonyos/routine-completion-record/execute" "${COMPLETION_PAYLOAD}" "${COMPLETION_RESPONSE}"
assert_json_paths "${COMPLETION_RESPONSE}" \
  "ok=true" \
  "code=routine_completion_record_persisted" \
  "data.completionRecordPersisted=true" \
  "data.nextTodayGuidanceCanReadHistory=true" \
  "debug.backendDatabaseWritten=true" \
  "safety.backendSQLiteWriteMayOccur=true" \
  "safety.writesHarmonyOSLocalState=false" \
  "safety.startsRoutine=false" \
  "safety.callsEngineAdapter=false" \
  "safety.createsMidiAsset=false" \
  "safety.startsPlayback=false"

echo "3) POST /agent/harmonyos/today-practice-guidance/preview"
post_json "/agent/harmonyos/today-practice-guidance/preview" "${GUIDANCE_PAYLOAD}" "${GUIDANCE_RESPONSE}"
assert_json_paths "${GUIDANCE_RESPONSE}" \
  "ok=true" \
  "code=today_guidance_ready" \
  "data.guidancePreviewReady=true" \
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
  "safety.startsPlayback=false"

echo "PASS: HarmonyOS Agent today-guidance runtime smoke completed."
