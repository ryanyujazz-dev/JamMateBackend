#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$SCRIPT_DIR/product_practice_coach_harmonyos_ui_integration_sequence.json"
TMP_DIR="${TMPDIR:-/tmp}/jammate_practice_coach_ui_integration_smoke_$$"
mkdir -p "$TMP_DIR"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

python3 - "$BASE_URL" "$FIXTURE" "$TMP_DIR" <<'PY'
import json, sys, urllib.request
base_url, fixture_path, tmp_dir = sys.argv[1:]
fixture = json.load(open(fixture_path, encoding='utf-8'))
base = dict(fixture['baseRequest'])
base['sessionId'] = base['sessionId'] + '-curl'
pc = fixture['practiceCoachEndpoint']
completion_endpoint = fixture['completionEndpoint']

def post(endpoint, payload):
    req = urllib.request.Request(base_url + endpoint, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def assert_ui(body, expected):
    ui = body.get('data', {}).get('frontendUiAction') or body.get('debug', {}).get('frontendUiAction') or {}
    for key, value in expected.items():
        if ui.get(key) != value:
            raise AssertionError(f"frontendUiAction.{key} expected {value!r}, got {ui.get(key)!r}; ui={ui}")
    if ui.get('safeToAutostartRoutine') is not False:
        raise AssertionError('Practice Coach must never be safe to autostart Routine')
    return ui

plan = post(pc, {**base, 'userMessage': fixture['steps'][0]['userMessage']})
assert plan['ok'] is True and plan['data']['responseType'] == 'practice_plan_proposal', plan
assert_ui(plan, fixture['steps'][0]['expectedUiAction'])

revision = post(pc, {**base, 'userMessage': fixture['steps'][1]['userMessage']})
assert revision['ok'] is True and revision['data']['responseType'] == 'practice_plan_revision', revision
assert_ui(revision, fixture['steps'][1]['expectedUiAction'])

card_response = post(pc, {**base, 'userMessage': fixture['steps'][2]['userMessage']})
assert card_response['ok'] is True and card_response['data']['responseType'] == 'routine_card_ready', card_response
assert_ui(card_response, fixture['steps'][2]['expectedUiAction'])
card = card_response['data']['routineCardPayload']

completion_payload = {
    'userId': base['userId'],
    'sessionId': 'practice-session-' + base['sessionId'],
    'deviceId': base['deviceId'],
    'routineCompletionRecord': {
        'routineId': card['routineId'],
        'routineTitle': card['title'],
        'completedAt': '2026-05-20T20:30:00+08:00',
        'durationSeconds': int(card['totalDurationMinutes']) * 60,
        'status': 'completed',
        'items': [
            {
                'itemId': b.get('blockId'),
                'title': b.get('title'),
                'type': b.get('type') or 'practice_block',
                'durationSeconds': int(b.get('durationMinutes') or 0) * 60,
                'status': 'completed',
            }
            for b in card.get('blocks', [])
        ],
        'notes': 'UI integration smoke completion record.',
    },
}
completion = post(completion_endpoint, completion_payload)
assert completion['ok'] is True and completion['data']['completionRecordPersisted'] is True, completion
assert_ui(completion, fixture['steps'][3]['expectedUiAction'])

next_body = post(pc, {**base, 'sessionId': base['sessionId'] + '-next', 'userMessage': fixture['steps'][4]['userMessage']})
assert next_body['ok'] is True, next_body
blocks = next_body.get('data', {}).get('llmRequestPreview', {}).get('contextBlocks', [])
recent = [b for b in blocks if b.get('name') == 'recent_practice_memory_summary']
assert recent, next_body
assert recent[0].get('payload', {}).get('recent_sessions'), recent[0]
print('PASS: Practice Coach HarmonyOS UI integration smoke completed.')
PY
