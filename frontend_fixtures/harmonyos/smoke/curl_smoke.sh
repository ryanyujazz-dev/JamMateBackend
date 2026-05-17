#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

echo "== JamMate API smoke against ${BASE_URL} =="

echo "1) GET /health"
curl -s "${BASE_URL}/health" | python -m json.tool

echo "2) POST /accompaniment/generate"
curl -s -X POST "${BASE_URL}/accompaniment/generate" \
  -H "Content-Type: application/json" \
  -d @smoke_direct_accompaniment_blue_bossa.json | python -m json.tool

echo "3) POST /agent/playback/prepare"
curl -s -X POST "${BASE_URL}/agent/playback/prepare" \
  -H "Content-Type: application/json" \
  -d @smoke_agent_playback_blue_bossa.json | python -m json.tool

echo "4 optional) POST /agent/practice/plan"
curl -s -X POST "${BASE_URL}/agent/practice/plan" \
  -H "Content-Type: application/json" \
  -d @smoke_agent_practice_plan_misty.json | python -m json.tool
