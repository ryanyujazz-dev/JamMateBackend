#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
RUN_ID="${JAMMATE_PRACTICE_COACH_PLAN_REVISION_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_practice_coach_plan_revision_e2e_${RUN_ID}"
KEEP_TMP="${JAMMATE_PRACTICE_COACH_PLAN_REVISION_SMOKE_KEEP_TMP:-false}"
ROUTE="/agent/harmonyos/practice-coach-session/message/execute"

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping Practice Coach plan revision smoke temp dir: ${TMP_DIR}"
  fi
}
trap cleanup EXIT

post_json() {
  local payload_file="$1"
  local response_file="$2"
  local status
  status=$(curl -sS -o "${response_file}" -w "%{http_code}" -X POST "${BASE_URL}${ROUTE}" \
    -H "Content-Type: application/json" \
    -d @"${payload_file}")
  if [[ "${status}" != "200" ]]; then
    echo "HTTP ${status} from ${ROUTE}" >&2
    python -m json.tool "${response_file}" || cat "${response_file}" >&2
    exit 1
  fi
}

python_assert_step() {
  local response_file="$1"
  local step_name="$2"
  local expected_type="$3"
  local expected_minutes="${4:-}"
  local expected_focus="${5:-}"
  local expected_revision_reason="${6:-}"
  python - <<'PYASSERT' "${response_file}" "${step_name}" "${expected_type}" "${expected_minutes}" "${expected_focus}" "${expected_revision_reason}"
from __future__ import annotations
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
step_name = sys.argv[2]
expected_type = sys.argv[3]
expected_minutes = sys.argv[4]
expected_focus = sys.argv[5]
expected_revision_reason = sys.argv[6]
body = json.loads(path.read_text(encoding='utf-8'))
if body.get('ok') is not True:
    raise SystemExit(f"{step_name}: expected ok=true, got {body.get('ok')} body={body}")
data = body.get('data') or {}
safety = body.get('safety') or {}
if data.get('responseType') != expected_type:
    raise SystemExit(f"{step_name}: expected responseType={expected_type}, got {data.get('responseType')} body={body}")
for key in ('startsRoutine','callsEngineAdapter','createsMidiAsset','startsPlayback','writesHarmonyOSLocalState'):
    if safety.get(key) is not False:
        raise SystemExit(f"{step_name}: expected safety.{key}=false, got {safety.get(key)}")
if expected_type in {'practice_plan_proposal','practice_plan_revision'}:
    proposal = data.get('planProposal') or {}
    if data.get('planProposalReady') is not True:
        raise SystemExit(f"{step_name}: expected planProposalReady=true")
    if data.get('routineCardPayload') is not None:
        raise SystemExit(f"{step_name}: expected routineCardPayload=null before confirmation")
    if data.get('routineStartEnabled') is not False:
        raise SystemExit(f"{step_name}: expected routineStartEnabled=false before confirmation")
    if expected_minutes and int(proposal.get('totalDurationMinutes') or 0) != int(expected_minutes):
        raise SystemExit(f"{step_name}: expected proposal minutes {expected_minutes}, got {proposal.get('totalDurationMinutes')}")
    if expected_focus and proposal.get('practiceFocus') != expected_focus:
        raise SystemExit(f"{step_name}: expected practiceFocus={expected_focus}, got {proposal.get('practiceFocus')}")
    if expected_revision_reason and proposal.get('revisionReason') != expected_revision_reason:
        raise SystemExit(f"{step_name}: expected revisionReason={expected_revision_reason}, got {proposal.get('revisionReason')}")
    state_after = data.get('stateAfter') or {}
    if state_after.get('awaiting_confirmation') is not True:
        raise SystemExit(f"{step_name}: expected stateAfter.awaiting_confirmation=true")
if expected_type == 'routine_card_ready':
    card = data.get('routineCardPayload') or {}
    if data.get('routineCardReady') is not True:
        raise SystemExit(f"{step_name}: expected routineCardReady=true")
    if card.get('backendStartsRoutine') is not False:
        raise SystemExit(f"{step_name}: expected card.backendStartsRoutine=false")
    if card.get('requiresUserTapToStart') is not True:
        raise SystemExit(f"{step_name}: expected card.requiresUserTapToStart=true")
    if expected_minutes and int(card.get('totalDurationMinutes') or 0) != int(expected_minutes):
        raise SystemExit(f"{step_name}: expected card minutes {expected_minutes}, got {card.get('totalDurationMinutes')}")
    if expected_focus and card.get('practiceFocus') != expected_focus:
        raise SystemExit(f"{step_name}: expected card focus {expected_focus}, got {card.get('practiceFocus')}")
PYASSERT
}

prepare_step_payloads() {
  python - <<'PYPREP' "${RUN_ID}" "${TMP_DIR}"
from __future__ import annotations
import json, sys
from pathlib import Path
run_id = sys.argv[1]
tmp_dir = Path(sys.argv[2])
source = Path.cwd() / 'product_practice_coach_plan_revision_e2e_sequence.json'
seq = json.loads(source.read_text(encoding='utf-8'))
forbidden = {'dbPath','sqliteDbPath','sqlite_db_path','clientConfirmedRecordWrite','client_confirmed_record_write','providerResult','llmActionDecisionResult','apiKey'}
def walk(value, path='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in forbidden:
                raise SystemExit(f'forbidden field {path}.{k} in product revision sequence')
            walk(v, f'{path}.{k}')
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk(item, f'{path}[{i}]')
walk(seq)
base = dict(seq['baseRequest'])
base['sessionId'] = f"practice-coach-plan-revision-e2e-{run_id}"
for step in seq['steps']:
    payload = dict(base)
    payload['userMessage'] = step['userMessage']
    (tmp_dir / f"step_{step['step']}_{step['name']}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PYPREP
}

prepare_step_payloads

echo "== JamMate Practice Coach plan revision E2E smoke against ${BASE_URL} =="
echo "This smoke uses product-shaped frontend requests only; it does not inject providerResult/llmActionDecisionResult or SQLite paths."

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

echo "2) Ask today practice"
post_json "${TMP_DIR}/step_1_ask_today_practice.json" "${TMP_DIR}/step_1_response.json"
python_assert_step "${TMP_DIR}/step_1_response.json" "ask_today_practice" "ask_clarifying_question"

echo "3) Create initial 30-minute Bossa plan"
post_json "${TMP_DIR}/step_2_create_initial_bossa_plan.json" "${TMP_DIR}/step_2_response.json"
python_assert_step "${TMP_DIR}/step_2_response.json" "create_initial_bossa_plan" "practice_plan_proposal" "30" "bossa"

echo "4) Revise duration to 20 minutes"
post_json "${TMP_DIR}/step_3_revise_duration_to_20.json" "${TMP_DIR}/step_3_response.json"
python_assert_step "${TMP_DIR}/step_3_response.json" "revise_duration_to_20" "practice_plan_revision" "20" "bossa" "adjust_duration"

echo "5) Revise focus to fundamentals/metronome"
post_json "${TMP_DIR}/step_4_revise_focus_to_fundamentals_metronome.json" "${TMP_DIR}/step_4_response.json"
python_assert_step "${TMP_DIR}/step_4_response.json" "revise_focus_to_fundamentals_metronome" "practice_plan_revision" "20" "fundamentals" "adjust_focus"

echo "6) Revise focus to tune practice"
post_json "${TMP_DIR}/step_5_revise_focus_to_tune_practice.json" "${TMP_DIR}/step_5_response.json"
python_assert_step "${TMP_DIR}/step_5_response.json" "revise_focus_to_tune_practice" "practice_plan_revision" "20" "tune_practice" "change_tune"

echo "7) Confirm revised plan into Routine card"
post_json "${TMP_DIR}/step_6_confirm_revised_plan_to_routine_card.json" "${TMP_DIR}/step_6_response.json"
python_assert_step "${TMP_DIR}/step_6_response.json" "confirm_revised_plan_to_routine_card" "routine_card_ready" "20" "tune_practice"

echo "PASS: Practice Coach plan revision E2E smoke completed."
