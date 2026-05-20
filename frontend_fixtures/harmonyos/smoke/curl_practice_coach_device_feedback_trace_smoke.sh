#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
ROUTE="/agent/harmonyos/practice-coach-session/message/execute"
FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUEST_FILE="$FIXTURE_DIR/product_practice_coach_device_feedback_trace_request.json"

if grep -Eq 'llmActionDecisionResult|providerResult|sqliteDbPath|dbPath|clientConfirmedRecordWrite|apiKey' "$REQUEST_FILE"; then
  echo "FAIL: product request fixture contains an internal/smoke-only field" >&2
  exit 1
fi

RESPONSE="$(curl -sS -X POST "$BASE_URL$ROUTE" \
  -H 'Content-Type: application/json' \
  --data-binary "@$REQUEST_FILE")"

python - <<'PY' "$RESPONSE"
import json
import sys

body = json.loads(sys.argv[1])
assert body.get("ok") is True, body
pack = ((body.get("debug") or {}).get("deviceFeedbackTracePack") or {})
assert pack.get("tracePackVersion") == "v2_10_25", pack
assert pack.get("copyThisForBackendIssue") is True, pack
assert pack.get("endpoint") == "POST /agent/harmonyos/practice-coach-session/message/execute", pack
assert (pack.get("requestSummary") or {}).get("userMessageDigest"), pack
assert (pack.get("responseSummary") or {}).get("responseType"), pack
assert (pack.get("ioTrace") or {}).get("sqliteRowsWritten") is True, pack
assert (pack.get("safetyTrace") or {}).get("startsRoutine") is False, pack
assert (pack.get("safetyTrace") or {}).get("callsEngineAdapter") is False, pack
assert (pack.get("safetyTrace") or {}).get("writesHarmonyOSLocalState") is False, pack
print("PASS: Practice Coach deviceFeedbackTracePack smoke completed.")
print(json.dumps(pack, ensure_ascii=False, indent=2))
PY
