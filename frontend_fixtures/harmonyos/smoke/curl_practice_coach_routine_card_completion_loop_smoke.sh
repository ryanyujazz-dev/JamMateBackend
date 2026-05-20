#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
RUN_ID="${JAMMATE_PRACTICE_COACH_COMPLETION_LOOP_SMOKE_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TMP_DIR="${TMPDIR:-/tmp}/jammate_practice_coach_completion_loop_${RUN_ID}"
KEEP_TMP="${JAMMATE_PRACTICE_COACH_COMPLETION_LOOP_SMOKE_KEEP_TMP:-false}"
PC_ROUTE="/agent/harmonyos/practice-coach-session/message/execute"
COMPLETION_ROUTE="/agent/harmonyos/routine-completion-record/execute"

mkdir -p "${TMP_DIR}"
cleanup() {
  if [[ "${KEEP_TMP}" != "true" ]]; then
    rm -rf "${TMP_DIR}"
  else
    echo "Keeping Practice Coach completion loop smoke temp dir: ${TMP_DIR}"
  fi
}
trap cleanup EXIT

post_json() {
  local route="$1"
  local payload_file="$2"
  local response_file="$3"
  local status
  status=$(curl -sS -o "${response_file}" -w "%{http_code}" -X POST "${BASE_URL}${route}" \
    -H "Content-Type: application/json" \
    -d @"${payload_file}")
  if [[ "${status}" != "200" ]]; then
    echo "HTTP ${status} from ${route}" >&2
    python -m json.tool "${response_file}" || cat "${response_file}" >&2
    exit 1
  fi
}

python_assert_pc_step() {
  local response_file="$1"
  local step_name="$2"
  local expected_type="$3"
  local expected_minutes="${4:-}"
  local expected_focus="${5:-}"
  python - <<'PYASSERT' "${response_file}" "${step_name}" "${expected_type}" "${expected_minutes}" "${expected_focus}"
from __future__ import annotations
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
step_name = sys.argv[2]
expected_type = sys.argv[3]
expected_minutes = sys.argv[4]
expected_focus = sys.argv[5]
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
artifact = data.get('planProposal') if expected_type in {'practice_plan_proposal','practice_plan_revision'} else data.get('routineCardPayload')
if expected_type == 'routine_card_ready' and data.get('routineCardReady') is not True:
    raise SystemExit(f"{step_name}: expected routineCardReady=true")
if expected_type in {'practice_plan_proposal','practice_plan_revision'} and data.get('planProposalReady') is not True:
    raise SystemExit(f"{step_name}: expected planProposalReady=true")
if expected_minutes and int((artifact or {}).get('totalDurationMinutes') or 0) != int(expected_minutes):
    raise SystemExit(f"{step_name}: expected minutes {expected_minutes}, got {(artifact or {}).get('totalDurationMinutes')}")
if expected_focus and (artifact or {}).get('practiceFocus') != expected_focus:
    raise SystemExit(f"{step_name}: expected focus {expected_focus}, got {(artifact or {}).get('practiceFocus')}")
PYASSERT
}

prepare_initial_payloads() {
  python - <<'PYPREP' "${RUN_ID}" "${TMP_DIR}"
from __future__ import annotations
import json, sys
from pathlib import Path
run_id = sys.argv[1]
tmp_dir = Path(sys.argv[2])
source = Path.cwd() / 'product_practice_coach_routine_card_completion_loop_sequence.json'
seq = json.loads(source.read_text(encoding='utf-8'))
forbidden = set(seq['forbiddenProductFields'])
def walk(value, path='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in forbidden:
                raise SystemExit(f'forbidden field {path}.{k} in product completion loop sequence')
            walk(v, f'{path}.{k}')
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk(item, f'{path}[{i}]')
walk(seq)
base = dict(seq['baseRequest'])
base['sessionId'] = f"practice-coach-completion-loop-{run_id}"
for step in seq['steps'][:3]:
    payload = dict(base)
    payload['userMessage'] = step['userMessage']
    (tmp_dir / f"step_{step['step']}_{step['name']}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(tmp_dir / 'base.json').write_text(json.dumps(base, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PYPREP
}

build_completion_payload_from_card() {
  python - <<'PYBUILD' "${TMP_DIR}"
from __future__ import annotations
import json, sys
from pathlib import Path
tmp = Path(sys.argv[1])
base = json.loads((tmp / 'base.json').read_text(encoding='utf-8'))
card_body = json.loads((tmp / 'step_3_response.json').read_text(encoding='utf-8'))
card = (card_body.get('data') or {}).get('routineCardPayload') or {}
if not card:
    raise SystemExit('routineCardPayload missing; cannot build completion record')
items = []
for block in card.get('blocks') or []:
    minutes = int(block.get('durationMinutes') or 0)
    items.append({
        'itemId': block.get('blockId'),
        'title': block.get('title'),
        'type': block.get('type') or 'practice_block',
        'durationSeconds': minutes * 60,
        'status': 'completed',
    })
payload = {
    'userId': base['userId'],
    'sessionId': f"practice-session-{base['sessionId']}",
    'deviceId': base['deviceId'],
    'routineCompletionRecord': {
        'routineId': card.get('routineId'),
        'routineTitle': card.get('title'),
        'completedAt': '2026-05-20T20:30:00+08:00',
        'durationSeconds': int(card.get('totalDurationMinutes') or 0) * 60,
        'status': 'completed',
        'items': items,
        'notes': '今天节拍器稳定性比上次好，Bossa 切换仍需继续。',
    },
}
(tmp / 'step_4_submit_routine_completion_record.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
next_payload = dict(base)
next_payload['sessionId'] = base['sessionId'] + '-next'
next_payload['userMessage'] = '今天该练什么？'
(tmp / 'step_5_next_practice_coach_reads_completion_history.json').write_text(json.dumps(next_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PYBUILD
}

python_assert_completion() {
  python - <<'PYASSERT' "${TMP_DIR}/step_4_response.json"
from __future__ import annotations
import json, sys
from pathlib import Path
body = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if body.get('ok') is not True:
    raise SystemExit(f"completion: expected ok=true, got {body}")
data = body.get('data') or {}
if data.get('completionRecordPersisted') is not True:
    raise SystemExit(f"completion: expected persisted=true, got {data}")
if data.get('nextTodayGuidanceCanReadHistory') is not True:
    raise SystemExit(f"completion: expected nextTodayGuidanceCanReadHistory=true, got {data}")
safety = body.get('safety') or {}
if safety.get('writesHarmonyOSLocalState') is not False or safety.get('startsRoutine') is not False:
    raise SystemExit(f"completion: unexpected unsafe flags {safety}")
PYASSERT
}

python_assert_next_reads_history() {
  python - <<'PYASSERT' "${TMP_DIR}/step_5_response.json"
from __future__ import annotations
import json, sys
from pathlib import Path
body = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if body.get('ok') is not True:
    raise SystemExit(f"next guidance: expected ok=true, got {body}")
preview = ((body.get('data') or {}).get('llmRequestPreview') or {})
projection = preview.get('sourceProjection') or {}
if int(projection.get('sqliteRowsRead') or 0) < 1:
    raise SystemExit(f"next guidance: expected sqliteRowsRead >= 1, got {projection}")
blocks = preview.get('contextBlocks') or []
recent = next((b.get('payload') for b in blocks if b.get('name') == 'recent_practice_memory_summary'), {})
sessions = recent.get('recent_sessions') or []
if not sessions:
    raise SystemExit('next guidance: recent practice sessions missing')
first = sessions[0]
if first.get('title') != '今日 Bossa 练习安排':
    raise SystemExit(f"next guidance: expected completion title in recent history, got {first}")
if not first.get('item_summaries'):
    raise SystemExit(f"next guidance: expected item_summaries from completion record, got {first}")
if not first.get('user_note_summary'):
    raise SystemExit(f"next guidance: expected user_note_summary from completion record, got {first}")
for key in ('startsRoutine','callsEngineAdapter','createsMidiAsset','startsPlayback','writesHarmonyOSLocalState'):
    if (body.get('safety') or {}).get(key) is not False:
        raise SystemExit(f"next guidance: expected safety.{key}=false")
PYASSERT
}

prepare_initial_payloads

echo "== JamMate Practice Coach routine card -> completion -> next guidance loop smoke against ${BASE_URL} =="
echo "This smoke uses product-shaped frontend requests only; it does not inject providerResult/llmActionDecisionResult or SQLite paths."

echo "1) GET /health"
curl -sS "${BASE_URL}/health" | python -m json.tool >/dev/null

echo "2) Create initial 30-minute Bossa plan"
post_json "${PC_ROUTE}" "${TMP_DIR}/step_1_create_initial_bossa_plan.json" "${TMP_DIR}/step_1_response.json"
python_assert_pc_step "${TMP_DIR}/step_1_response.json" "create_initial_bossa_plan" "practice_plan_proposal" "30" "bossa"

echo "3) Revise duration to 20 minutes"
post_json "${PC_ROUTE}" "${TMP_DIR}/step_2_revise_duration_to_20.json" "${TMP_DIR}/step_2_response.json"
python_assert_pc_step "${TMP_DIR}/step_2_response.json" "revise_duration_to_20" "practice_plan_revision" "20" "bossa"

echo "4) Confirm revised plan into Routine card"
post_json "${PC_ROUTE}" "${TMP_DIR}/step_3_confirm_revised_plan_to_routine_card.json" "${TMP_DIR}/step_3_response.json"
python_assert_pc_step "${TMP_DIR}/step_3_response.json" "confirm_revised_plan_to_routine_card" "routine_card_ready" "20" "bossa"

build_completion_payload_from_card

echo "5) Submit Routine completion record"
post_json "${COMPLETION_ROUTE}" "${TMP_DIR}/step_4_submit_routine_completion_record.json" "${TMP_DIR}/step_4_response.json"
python_assert_completion

echo "6) Ask Practice Coach again and verify completion history readback"
post_json "${PC_ROUTE}" "${TMP_DIR}/step_5_next_practice_coach_reads_completion_history.json" "${TMP_DIR}/step_5_response.json"
python_assert_next_reads_history

echo "PASS: Practice Coach routine card -> completion -> next guidance loop smoke completed."
