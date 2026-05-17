from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONTRACT_VERSION = "v2_3_16"


@dataclass(frozen=True)
class GeneratedContractFile:
    filename: str
    relative_path: str
    purpose: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "relative_path": self.relative_path,
            "purpose": self.purpose,
            "source": self.source,
        }


AGENT_TYPES_ETS = r'''
// JamMate Agent API Types v2_3_16
// Copy target: entry/src/main/ets/features/jammateAgent/model/AgentTypes.ets
// Backend responses are canonical snake_case. JamMateApiClient maps them into these camelCase client-domain types.

import type { PlaybackInstruction, AccompanimentAsset } from '../../practice/model/PlaybackTypes'
import type { PracticePlan, SessionReview, NextStepRecommendation } from '../../practice/model/PracticeTypes'

export type JamMateStyle = 'medium_swing' | 'bossa_nova' | 'jazz_ballad'

export type AgentIntentType =
  | 'practice_plan_generation'
  | 'immediate_practice_playback'
  | 'session_review'
  | 'coach_qa'
  | string

export interface ClientContext {
  timezone?: string
  locale?: string
  currentScreen?: string | null
  availableMinutes?: number | null
  activeSessionId?: string | null
  activePlanId?: string | null
  selectedMaterialId?: string | null
}

export interface AgentMessageRequest {
  requestId?: string | null
  userInput: string
  clientContext?: ClientContext
  localUnsyncedSummary?: Record<string, unknown>
}

export interface AgentPlanRequest {
  userInput: string
  availableMinutes?: number
  instrument?: string
  activeGoalId?: string | null
}

export interface AgentPlaybackPrepareRequest {
  userInput: string
  durationMinutes?: number
  clientContext?: ClientContext
}

export interface AgentOption {
  type: string
  label: string
}

export type RawAgentResponse = Record<string, unknown>

export interface AgentResponse {
  ok: boolean
  intentType: AgentIntentType
  plan?: PracticePlan | null
  practiceSession?: Record<string, unknown> | null
  asset?: AccompanimentAsset | null
  playbackInstruction?: PlaybackInstruction | null
  recommendation?: NextStepRecommendation | null
  explanation?: string | null
  errorCode?: string | null
  message?: string | null
  options?: AgentOption[]
  traceId?: string | null
}

export interface AgentTraceSummary {
  traceId: string
  taskType: string
  userInput?: string
  createdAt?: string
  validationResult?: string | null
}

export interface AgentTraceStep {
  name: string
  payload?: Record<string, unknown>
  at?: string
}

export interface AgentTraceDetail extends AgentTraceSummary {
  requestId?: string | null
  contextPacketSummary?: Record<string, unknown>
  steps: AgentTraceStep[]
  finalResponseSummary?: Record<string, unknown>
}

export interface AgentCapabilitiesResponse {
  ok: boolean
  manifest: Record<string, unknown>
}

export interface AgentContractFile {
  filename: string
  relativePath: string
  purpose: string
  source: string
}

export interface AgentContractFilesResponse {
  ok: boolean
  version: string
  responseCase: 'snake_case'
  clientDomainCase: 'camelCase'
  files: AgentContractFile[]
}
'''.strip() + "\n"



PRACTICE_TYPES_ETS = "\n// JamMate Practice Domain Types v2_3_16\n// Copy target: entry/src/main/ets/features/practice/model/PracticeTypes.ets\n// Client-domain types are camelCase. Backend raw snake_case payloads should be mapped by CaseAdapter.ets.\n\nimport type { JamMateStyle } from '../../jammateAgent/model/AgentTypes'\n\nexport type ExerciseBlockType =\n  | 'technique'\n  | 'time_feel'\n  | 'ear_training'\n  | 'guide_tone'\n  | 'voicing'\n  | 'comping'\n  | 'improvisation'\n  | 'transcription'\n  | 'repertoire'\n  | 'review'\n  | 'custom'\n  | string\n\nexport type ExerciseBlockStatus = 'pending' | 'active' | 'completed' | 'skipped' | string\nexport type PracticeSessionStatus = 'planned' | 'active' | 'paused' | 'completed' | 'abandoned' | string\nexport type SyncStatus = 'local_only' | 'pending' | 'synced' | 'conflict' | 'failed' | string\n\nexport interface PracticeMaterial {\n  type: string\n  tune?: string | null\n  section?: string | null\n  key?: string | null\n  progression?: string | null\n  bars?: number | null\n  raw?: Record<string, unknown>\n}\n\nexport interface AccompanimentPracticeConfig {\n  enabled: boolean\n  style: JamMateStyle | string\n  tempo: number\n  loopCount?: number | null\n  durationMinutes?: number | null\n  sectionLoop: boolean\n  mutedRoles: Array<'piano' | 'bass' | 'drums' | 'melody' | string>\n  countIn: boolean\n  harmonicExpansionEnabled: boolean\n  density: string\n  practiceRole: string\n  outputFormat: 'midi_base64' | 'asset_id'\n  arrangementIntent: Record<string, unknown>\n}\n\nexport interface ExerciseBlock {\n  blockId: string\n  type: ExerciseBlockType\n  title: string\n  intent: string\n  durationMinutes: number\n  material?: PracticeMaterial | null\n  tempo?: number | null\n  style?: string | null\n  accompanimentConfig?: AccompanimentPracticeConfig | null\n  successCriteria: string[]\n  reviewPrompt?: string | null\n  status: ExerciseBlockStatus\n}\n\nexport interface PracticePlan {\n  planId: string\n  title: string\n  durationMinutes: number\n  mainFocus: string\n  blocks: ExerciseBlock[]\n  estimatedDifficulty: string\n  explanation?: string | null\n  source: 'rule_based' | 'llm' | 'template' | 'hybrid' | string\n}\n\nexport interface PracticeSession {\n  sessionId: string\n  planId?: string | null\n  startedAt?: string | null\n  endedAt?: string | null\n  status: PracticeSessionStatus\n  totalPlannedMinutes?: number | null\n  totalActualMinutes: number\n  currentBlockId?: string | null\n  blocks: ExerciseBlock[]\n  syncStatus: SyncStatus\n}\n\nexport interface StuckPoint {\n  material?: string | null\n  issue: string\n}\n\nexport interface SessionReview {\n  sessionId?: string\n  completed?: boolean\n  difficulty?: 'too_easy' | 'easy' | 'good_challenge' | 'too_hard' | string\n  focusScore?: number | null\n  timeFeel?: 'stable' | 'rushing' | 'dragging' | 'unsure' | string | null\n  tempoResult?: Record<string, unknown> | null\n  stuckPoints?: StuckPoint[]\n  notes?: string | null\n  nextActionPreference?: string | null\n}\n\nexport interface NextStepRecommendation {\n  recommendationId: string\n  source: 'rule_based' | 'llm' | 'hybrid' | string\n  summary: string\n  actions: Array<Record<string, unknown>>\n}\n".strip() + "\n"



PLAYBACK_TYPES_ETS = "\n// JamMate Playback / Accompaniment Types v2_3_16\n// Copy target: entry/src/main/ets/features/practice/model/PlaybackTypes.ets\n// Client-domain types are camelCase. Duration is a practice-timer concern.\n\nimport type { JamMateStyle } from '../../jammateAgent/model/AgentTypes'\n\nexport type AssetLoopMode = 'loop_until_target_duration' | string\n\nexport interface DirectAccompanimentGenerateRequest {\n  leadsheet?: Record<string, unknown> | null\n  tune?: string | null\n  style?: JamMateStyle\n  tempo?: number\n  choruses?: number\n  seed?: number\n  outputPath?: string | null\n  ensemble?: Record<string, unknown>\n  voicingOverride?: Record<string, unknown>\n  outputFormat?: 'midi_base64'\n}\n\nexport interface AccompanimentAsset {\n  assetId?: string\n  format: 'midi_base64'\n  midiBase64: string\n  midiPath?: string | null\n  durationSeconds?: number | null\n  cacheKey?: string | null\n  debugSummary?: Record<string, unknown>\n}\n\nexport interface PlaybackInstruction {\n  autoStart: boolean\n  targetDurationMinutes: number\n  clientLoopUntilTargetDuration: boolean\n  assetLoopMode?: AssetLoopMode\n  stopCondition?: string\n  requiresLocalTimer?: boolean\n  cachePolicy?: {\n    cacheKey?: string | null\n    scope?: string\n    reuseWhenRequestSignatureMatches?: boolean\n  }\n}\n\nexport interface PlaybackState {\n  status: 'idle' | 'preparing_remote_asset' | 'ready_cached' | 'playing' | 'paused' | 'completed' | 'failed'\n  cacheKey?: string | null\n  assetId?: string | null\n  targetDurationMinutes?: number | null\n  elapsedSeconds: number\n  errorMessage?: string | null\n}\n\nexport interface DirectAccompanimentGenerateResponse {\n  ok: boolean\n  asset?: AccompanimentAsset\n  errorCode?: string\n  message?: string\n  options?: Array<Record<string, unknown>>\n}\n".strip() + "\n"



CASE_ADAPTER_ETS = "\n// JamMate Case Adapter v2_3_16\n// Copy target: entry/src/main/ets/features/jammateAgent/api/CaseAdapter.ets\n// Backend canonical response: snake_case. Client-domain model: camelCase.\n\nimport type { AgentResponse } from '../model/AgentTypes'\nimport type { DirectAccompanimentGenerateResponse } from '../../practice/model/PlaybackTypes'\n\nfunction snakeToCamelKey(key: string): string {\n  return key.replace(/_([a-zA-Z0-9])/g, (_match: string, letter: string): string => letter.toUpperCase())\n}\n\nfunction camelToSnakeKey(key: string): string {\n  return key.replace(/[A-Z]/g, (letter: string): string => `_${letter.toLowerCase()}`)\n}\n\nexport function deepSnakeToCamel(value: unknown): unknown {\n  if (Array.isArray(value)) {\n    return value.map((item: unknown): unknown => deepSnakeToCamel(item))\n  }\n  if (value !== null && typeof value === 'object') {\n    const output: Record<string, unknown> = {}\n    Object.keys(value as Record<string, unknown>).forEach((key: string): void => {\n      output[snakeToCamelKey(key)] = deepSnakeToCamel((value as Record<string, unknown>)[key])\n    })\n    return output\n  }\n  return value\n}\n\nexport function deepCamelToSnake(value: unknown): unknown {\n  if (Array.isArray(value)) {\n    return value.map((item: unknown): unknown => deepCamelToSnake(item))\n  }\n  if (value !== null && typeof value === 'object') {\n    const output: Record<string, unknown> = {}\n    Object.keys(value as Record<string, unknown>).forEach((key: string): void => {\n      output[camelToSnakeKey(key)] = deepCamelToSnake((value as Record<string, unknown>)[key])\n    })\n    return output\n  }\n  return value\n}\n\nexport function mapAgentResponse(raw: Record<string, unknown>): AgentResponse {\n  return deepSnakeToCamel(raw) as AgentResponse\n}\n\nexport function mapDirectAccompanimentResponse(raw: Record<string, unknown>): DirectAccompanimentGenerateResponse {\n  return deepSnakeToCamel(raw) as DirectAccompanimentGenerateResponse\n}\n".strip() + "\n"


API_CLIENT_EXAMPLE_ETS = "\n// JamMate API Client Sketch v2_3_16\n// Copy target suggestion: entry/src/main/ets/features/jammateAgent/api/JamMateApiClient.ets\n// Requests may be sent as camelCase. Responses are mapped from backend snake_case to camelCase domain types.\n\nimport type { AgentPlanRequest, AgentPlaybackPrepareRequest, AgentResponse } from '../model/AgentTypes'\nimport type { DirectAccompanimentGenerateRequest, DirectAccompanimentGenerateResponse } from '../../practice/model/PlaybackTypes'\nimport { mapAgentResponse, mapDirectAccompanimentResponse } from './CaseAdapter'\n\nexport class JamMateApiClient {\n  constructor(private readonly baseUrl: string) {}\n\n  async health(): Promise<Record<string, unknown>> {\n    return this.get('/health')\n  }\n\n  async generatePracticePlan(request: AgentPlanRequest): Promise<AgentResponse> {\n    const raw = await this.post('/agent/practice/plan', request as Record<string, unknown>)\n    return mapAgentResponse(raw)\n  }\n\n  async prepareAgentPlayback(request: AgentPlaybackPrepareRequest): Promise<AgentResponse> {\n    const raw = await this.post('/agent/playback/prepare', request as Record<string, unknown>)\n    return mapAgentResponse(raw)\n  }\n\n  async generateDirectAccompaniment(request: DirectAccompanimentGenerateRequest): Promise<DirectAccompanimentGenerateResponse> {\n    const raw = await this.post('/accompaniment/generate', request as Record<string, unknown>)\n    return mapDirectAccompanimentResponse(raw)\n  }\n\n  private async get(path: string): Promise<Record<string, unknown>> {\n    throw new Error(`Replace JamMateApiClient.get with HarmonyOS HTTP implementation: ${this.baseUrl}${path}`)\n  }\n\n  private async post(path: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {\n    throw new Error(`Replace JamMateApiClient.post with HarmonyOS HTTP implementation: ${this.baseUrl}${path} body=${JSON.stringify(body)}`)\n  }\n}\n".strip() + "\n"



def arkts_contract_files() -> dict[str, Any]:
    files = [
        GeneratedContractFile(
            filename="AgentTypes.ets",
            relative_path="entry/src/main/ets/features/jammateAgent/model/AgentTypes.ets",
            purpose="Agent request/response, trace, capability, and contract endpoint types.",
            source=AGENT_TYPES_ETS,
        ),
        GeneratedContractFile(
            filename="PracticeTypes.ets",
            relative_path="entry/src/main/ets/features/practice/model/PracticeTypes.ets",
            purpose="Local-first practice domain types: plan, session, block, review, recommendation.",
            source=PRACTICE_TYPES_ETS,
        ),
        GeneratedContractFile(
            filename="PlaybackTypes.ets",
            relative_path="entry/src/main/ets/features/practice/model/PlaybackTypes.ets",
            purpose="Direct accompaniment and playback asset/cache/timer types.",
            source=PLAYBACK_TYPES_ETS,
        ),
        GeneratedContractFile(
            filename="CaseAdapter.ets",
            relative_path="entry/src/main/ets/features/jammateAgent/api/CaseAdapter.ets",
            purpose="Response adapter: maps backend canonical snake_case payloads into camelCase client-domain objects.",
            source=CASE_ADAPTER_ETS,
        ),
        GeneratedContractFile(
            filename="JamMateApiClient.ets",
            relative_path="entry/src/main/ets/features/jammateAgent/api/JamMateApiClient.ets",
            purpose="Minimal HarmonyOS API client sketch. Replace HTTP internals in app project.",
            source=API_CLIENT_EXAMPLE_ETS,
        ),
    ]
    return {
        "version": CONTRACT_VERSION,
        "response_case": "snake_case",
        "client_domain_case": "camelCase",
        "request_case": "camelCase_or_snake_case",
        "files": [file.to_dict() for file in files],
    }


def _snake_to_camel_key(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _deep_snake_to_camel(value: Any) -> Any:
    if isinstance(value, list):
        return [_deep_snake_to_camel(item) for item in value]
    if isinstance(value, dict):
        return {_snake_to_camel_key(str(key)): _deep_snake_to_camel(item) for key, item in value.items()}
    return value


def frontend_fixture_pack() -> dict[str, Any]:
    """Stable mock fixtures for HarmonyOS UI/store development.

    The MIDI payload is intentionally tiny placeholder base64 in fixtures. Real
    playback integration should use /agent/playback/prepare or /accompaniment/generate.
    """
    fake_midi_base64 = "TVRoZAAAAAYAAQABAGBNVHJrAAAABAD/LwA="
    raw_pack = {
        "version": CONTRACT_VERSION,
        "note": "Fixtures are UI/store mocks, not golden musical output.",
        "fixtures": {
            "agentPracticePlanResponse": {
                "ok": True,
                "intent_type": "practice_plan_generation",
                "plan": {
                    "plan_id": "plan_fixture_misty_45",
                    "title": "Misty Ballad Comping 45",
                    "duration_minutes": 45,
                    "main_focus": "Misty ballad comping with stable lower foundation",
                    "estimated_difficulty": "medium",
                    "explanation": "Fixture plan for UI preview and local store testing.",
                    "source": "rule_based",
                    "blocks": [
                        {
                            "block_id": "block_fixture_voicing",
                            "type": "voicing",
                            "title": "Misty A段 lower foundation",
                            "intent": "控制 lower foundation 与 voice-leading，不让左手过乱。",
                            "duration_minutes": 12,
                            "material": {"type": "tune", "tune": "Misty", "section": "A", "key": "Eb major", "raw": {}},
                            "tempo": 76,
                            "style": "jazz_ballad",
                            "accompaniment_config": None,
                            "success_criteria": ["lower group 稳定", "top voice 不乱跳"],
                            "review_prompt": "左手 foundation 是否清楚？",
                            "status": "pending",
                        },
                        {
                            "block_id": "block_fixture_comping",
                            "type": "comping",
                            "title": "Misty A段 with bass/drums",
                            "intent": "关闭钢琴伴奏声部，跟 bass/drums 练 comping。",
                            "duration_minutes": 28,
                            "material": {"type": "tune", "tune": "Misty", "section": "A", "key": "Eb major", "raw": {}},
                            "tempo": 76,
                            "style": "jazz_ballad",
                            "accompaniment_config": {
                                "enabled": True,
                                "style": "jazz_ballad",
                                "tempo": 76,
                                "loop_count": 3,
                                "duration_minutes": None,
                                "section_loop": True,
                                "muted_roles": ["piano"],
                                "count_in": True,
                                "harmonic_expansion_enabled": False,
                                "density": "normal",
                                "practice_role": "piano_comping",
                                "output_format": "midi_base64",
                                "arrangement_intent": {},
                            },
                            "success_criteria": ["不抢拍", "和声连接清楚"],
                            "review_prompt": "是否能跟 rhythm section 稳定 comp？",
                            "status": "pending",
                        },
                        {
                            "block_id": "block_fixture_review",
                            "type": "review",
                            "title": "Review",
                            "intent": "记录本次卡点与下次动作。",
                            "duration_minutes": 5,
                            "material": None,
                            "tempo": None,
                            "style": None,
                            "accompaniment_config": None,
                            "success_criteria": [],
                            "review_prompt": "今天最卡的点是什么？",
                            "status": "pending",
                        },
                    ],
                },
                "trace_id": "trace_fixture_plan_001",
            },
            "agentPlaybackPrepareResponse": {
                "ok": True,
                "intent_type": "immediate_practice_playback",
                "practice_session": {
                    "status": "active",
                    "total_planned_minutes": 20,
                    "material": {"type": "tune", "tune": "Blue Bossa", "raw": {}},
                },
                "asset": {
                    "asset_id": "asset_fixture_blue_bossa",
                    "format": "midi_base64",
                    "midi_base64": fake_midi_base64,
                    "midi_path": "demos/fixture_blue_bossa.mid",
                    "duration_seconds": 72,
                    "cache_key": "agent_playback:blue_bossa:bossa_nova:120:choruses3:harmony0",
                    "debug_summary": {"fixture": True, "path": "agent_playback_prepare"},
                },
                "playback_instruction": {
                    "auto_start": True,
                    "target_duration_minutes": 20,
                    "client_loop_until_target_duration": True,
                    "asset_loop_mode": "loop_until_target_duration",
                    "requires_local_timer": True,
                    "stop_condition": "practice_timer_reaches_target_duration_or_user_stops",
                    "cache_policy": {
                        "cache_key": "agent_playback:blue_bossa:bossa_nova:120:choruses3:harmony0",
                        "scope": "recent_practice_asset",
                        "reuse_when_request_signature_matches": True,
                    },
                },
                "explanation": "Fixture playback response for UI/cache/player testing.",
                "trace_id": "trace_fixture_playback_001",
            },
            "directAccompanimentGenerateResponse": {
                "ok": True,
                "asset": {
                    "format": "midi_base64",
                    "midi_base64": fake_midi_base64,
                    "midi_path": "demos/fixture_direct_blue_bossa.mid",
                    "cache_key": "direct_accomp:blue_bossa:bossa_nova:120:choruses3",
                    "debug_summary": {"fixture": True, "path": "direct_accompaniment_api"},
                },
            },
            "sessionReviewRequest": {
                "sessionId": "session_fixture_001",
                "completed": True,
                "difficulty": "good_challenge",
                "focusScore": 4,
                "timeFeel": "stable",
                "tempoResult": {"tempo": 90, "stable": True, "should_raise_next_time": True},
                "stuckPoints": [{"material": "Misty A section", "issue": "left hand still gets messy"}],
                "notes": "整体稳定，但左手需要更清晰。",
                "nextActionPreference": "continue",
            },
        },
    }
    fixtures = raw_pack["fixtures"]
    return {
        "version": CONTRACT_VERSION,
        "note": raw_pack["note"],
        "response_case": "snake_case",
        "client_domain_case": "camelCase",
        "fixtures": {
            "rawBackendAgentPracticePlanResponse": fixtures["agentPracticePlanResponse"],
            "agentPracticePlanResponse": _deep_snake_to_camel(fixtures["agentPracticePlanResponse"]),
            "rawBackendAgentPlaybackPrepareResponse": fixtures["agentPlaybackPrepareResponse"],
            "agentPlaybackPrepareResponse": _deep_snake_to_camel(fixtures["agentPlaybackPrepareResponse"]),
            "rawBackendDirectAccompanimentGenerateResponse": fixtures["directAccompanimentGenerateResponse"],
            "directAccompanimentGenerateResponse": _deep_snake_to_camel(fixtures["directAccompanimentGenerateResponse"]),
            "sessionReviewRequest": fixtures["sessionReviewRequest"],
        },
    }


def frontend_fixture_pack_files() -> dict[str, Any]:
    """Filesystem-style fixture files for direct copy into HarmonyOS worktree."""
    import json

    contract_files = arkts_contract_files()["files"]
    fixture_json = json.dumps(frontend_fixture_pack(), ensure_ascii=False, indent=2)
    readme = f"""# JamMate HarmonyOS Frontend Fixture Pack {CONTRACT_VERSION}

This folder is a copy-friendly frontend contract pack for HarmonyOS development.

## Files

- `types/AgentTypes.ets`: Agent request/response and trace types.
- `types/PracticeTypes.ets`: Local-first practice plan/session/review types.
- `types/PlaybackTypes.ets`: Playback asset, cache, direct accompaniment types.
- `api/CaseAdapter.ets`: snake_case -> camelCase response adapter.
- `api/JamMateApiClient.ets`: Minimal API client sketch. Replace HTTP internals.
- `fixtures/PracticeFixtures.json`: Stable UI/store mock payloads.

## Rules

- HarmonyOS local practice workspace must run without LLM.
- Direct accompaniment uses `/accompaniment/generate` and does not require Agent.
- Natural-language planning/playback uses `/agent/*`.
- Backend responses are canonical `snake_case`.
- Client-domain objects should be camelCase after `CaseAdapter.ets` mapping.
- Requests may be sent as camelCase or snake_case.
- Practice duration is a local timer target; returned MIDI asset can be looped until target duration.
"""
    files = []
    for item in contract_files:
        rel = item["relative_path"]
        if rel.endswith("AgentTypes.ets"):
            out_rel = "types/AgentTypes.ets"
        elif rel.endswith("PracticeTypes.ets"):
            out_rel = "types/PracticeTypes.ets"
        elif rel.endswith("PlaybackTypes.ets"):
            out_rel = "types/PlaybackTypes.ets"
        elif rel.endswith("CaseAdapter.ets"):
            out_rel = "api/CaseAdapter.ets"
        elif rel.endswith("JamMateApiClient.ets"):
            out_rel = "api/JamMateApiClient.ets"
        else:
            out_rel = item["filename"]
        files.append({"relative_path": out_rel, "source": item["source"], "purpose": item["purpose"]})
    files.append({"relative_path": "fixtures/PracticeFixtures.json", "source": fixture_json + "\n", "purpose": "Stable mock payloads for UI and local-store development."})
    files.append({"relative_path": "README.md", "source": readme, "purpose": "Frontend fixture pack usage notes."})
    return {"version": CONTRACT_VERSION, "files": files}


def harmonyos_api_smoke_pack() -> dict[str, Any]:
    """Machine-readable smoke pack for HarmonyOS and LAN integration.

    These payloads are intentionally small and target the three minimum paths:
    /health, /accompaniment/generate, and /agent/playback/prepare.
    """
    direct_request = {
        "tune": "Blue Bossa",
        "style": "bossa_nova",
        "tempo": 120,
        "choruses": 1,
        "seed": 42,
        "outputFormat": "midi_base64",
    }
    agent_playback_request = {
        "userInput": "我想练 Blue Bossa 20分钟，帮我生成 Bossa Nova 伴奏",
        "durationMinutes": 20,
        "clientContext": {
            "currentScreen": "practice_home",
            "availableMinutes": 20,
            "timezone": "America/Los_Angeles",
            "locale": "zh-CN",
        },
    }
    plan_request = {
        "userInput": "我今天有45分钟，想练Misty的ballad comping",
        "availableMinutes": 45,
        "instrument": "piano",
    }
    session_review_request = {
        "sessionId": "session_smoke_001",
        "completed": True,
        "difficulty": "good_challenge",
        "focusScore": 4,
        "timeFeel": "stable",
        "tempoResult": {"tempo": 90, "stable": True, "should_raise_next_time": True},
        "stuckPoints": [{"material": "Misty A section", "issue": "left hand still gets messy"}],
        "notes": "HarmonyOS smoke review payload.",
        "nextActionPreference": "continue",
    }
    return {
        "version": CONTRACT_VERSION,
        "purpose": "Minimal HarmonyOS-to-Python smoke validation pack.",
        "base_url_examples": {
            "local_mac": "http://127.0.0.1:8000",
            "phone_to_mac_lan": "http://<MAC_LAN_IP>:8000",
        },
        "server_start": {
            "command": "PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000",
            "health_check": "GET /health",
        },
        "minimum_smoke_sequence": [
            {"step": 1, "name": "health", "method": "GET", "path": "/health", "expect": {"ok": True}},
            {"step": 2, "name": "direct_accompaniment", "method": "POST", "path": "/accompaniment/generate", "request": direct_request, "expect": {"ok": True, "asset.midi_base64": "non_empty", "asset.cache_key": "starts_with:direct_accomp:"}},
            {"step": 3, "name": "agent_playback_prepare", "method": "POST", "path": "/agent/playback/prepare", "request": agent_playback_request, "expect": {"ok": True, "asset.midi_base64": "non_empty", "playback_instruction.client_loop_until_target_duration": True}},
        ],
        "optional_smoke_sequence": [
            {"name": "agent_practice_plan", "method": "POST", "path": "/agent/practice/plan", "request": plan_request, "expect": {"ok": True, "plan.blocks": "non_empty"}},
            {"name": "session_review", "method": "POST", "path": "/agent/session/review", "request": session_review_request, "expect": {"ok": True, "recommendation.summary": "non_empty"}},
            {"name": "trace_list", "method": "GET", "path": "/agent/traces", "expect": {"ok": True}},
        ],
        "requests": {
            "directAccompanimentBlueBossa": direct_request,
            "agentPlaybackBlueBossa": agent_playback_request,
            "agentPracticePlanMisty": plan_request,
            "sessionReview": session_review_request,
        },
        "playback_assertions": {
            "duration_rule": "Practice duration is controlled by HarmonyOS local timer, not by generating a 20/30/45-minute MIDI file.",
            "loop_rule": "If playback_instruction.client_loop_until_target_duration is true, loop the returned asset until the local timer reaches targetDurationMinutes or user stops.",
            "cache_rule": "Use asset.cache_key as the local cache identity when present.",
        },
    }


def harmonyos_api_smoke_pack_files() -> dict[str, Any]:
    """Filesystem-style smoke pack for copy into HarmonyOS docs/fixtures."""
    import json

    pack = harmonyos_api_smoke_pack()
    requests = pack["requests"]
    curl = f'''#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${{1:-http://127.0.0.1:8000}}"

echo "== JamMate API smoke against ${{BASE_URL}} =="

echo "1) GET /health"
curl -s "${{BASE_URL}}/health" | python -m json.tool

echo "2) POST /accompaniment/generate"
curl -s -X POST "${{BASE_URL}}/accompaniment/generate" \\
  -H "Content-Type: application/json" \\
  -d @smoke_direct_accompaniment_blue_bossa.json | python -m json.tool

echo "3) POST /agent/playback/prepare"
curl -s -X POST "${{BASE_URL}}/agent/playback/prepare" \\
  -H "Content-Type: application/json" \\
  -d @smoke_agent_playback_blue_bossa.json | python -m json.tool

echo "4 optional) POST /agent/practice/plan"
curl -s -X POST "${{BASE_URL}}/agent/practice/plan" \\
  -H "Content-Type: application/json" \\
  -d @smoke_agent_practice_plan_misty.json | python -m json.tool
'''
    readme = f'''# JamMate HarmonyOS API Smoke Pack {CONTRACT_VERSION}

This folder contains the minimal payloads and commands for testing the Python API from HarmonyOS or from a Mac terminal.

## Start Python service on Mac

```bash
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

## Local Mac test

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_smoke.sh http://127.0.0.1:8000
```

## Phone / HarmonyOS to Mac LAN test

1. Make sure phone and Mac are on the same Wi-Fi.
2. Find Mac LAN IP, for example `ipconfig getifaddr en0`.
3. Start API with `--host 0.0.0.0 --port 8000`.
4. Open Mac firewall for port 8000 if needed.
5. Use base URL `http://<MAC_LAN_IP>:8000` in HarmonyOS.
6. First verify `GET /health`.

## Minimum smoke sequence

1. `GET /health`
2. `POST /accompaniment/generate` using `smoke_direct_accompaniment_blue_bossa.json`
3. `POST /agent/playback/prepare` using `smoke_agent_playback_blue_bossa.json`

## Playback rule

Practice duration is owned by HarmonyOS local timer. The returned MIDI asset should be looped when `playbackInstruction.clientLoopUntilTargetDuration === true`.
'''
    files = [
        {"relative_path": "README.md", "purpose": "HarmonyOS LAN smoke-test instructions.", "source": readme},
        {"relative_path": "curl_smoke.sh", "purpose": "Terminal smoke script. Pass BASE_URL as first arg.", "source": curl},
        {"relative_path": "smoke_pack.json", "purpose": "Machine-readable smoke pack.", "source": json.dumps(pack, ensure_ascii=False, indent=2) + "\n"},
        {"relative_path": "smoke_direct_accompaniment_blue_bossa.json", "purpose": "Direct engine path request without Agent/LLM.", "source": json.dumps(requests["directAccompanimentBlueBossa"], ensure_ascii=False, indent=2) + "\n"},
        {"relative_path": "smoke_agent_playback_blue_bossa.json", "purpose": "Agent immediate playback request.", "source": json.dumps(requests["agentPlaybackBlueBossa"], ensure_ascii=False, indent=2) + "\n"},
        {"relative_path": "smoke_agent_practice_plan_misty.json", "purpose": "Agent practice plan request.", "source": json.dumps(requests["agentPracticePlanMisty"], ensure_ascii=False, indent=2) + "\n"},
        {"relative_path": "smoke_session_review.json", "purpose": "Session review request.", "source": json.dumps(requests["sessionReview"], ensure_ascii=False, indent=2) + "\n"},
    ]
    return {"version": CONTRACT_VERSION, "files": files}
