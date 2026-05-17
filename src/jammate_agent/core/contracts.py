from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentToolContract:
    name: str
    description: str
    requires_llm: bool = False
    direct_client_callable: bool = False
    input_contract: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_llm": self.requires_llm,
            "direct_client_callable": self.direct_client_callable,
            "input_contract": self.input_contract,
            "output_contract": self.output_contract,
        }


@dataclass(frozen=True)
class ContextProfileContract:
    task_type: str
    required_context_layers: list[str]
    optional_context_layers: list[str] = field(default_factory=list)
    output_schema: str | None = None
    llm_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "required_context_layers": list(self.required_context_layers),
            "optional_context_layers": list(self.optional_context_layers),
            "output_schema": self.output_schema,
            "llm_required": self.llm_required,
        }


def agent_capability_manifest() -> dict[str, Any]:
    """Machine-readable manifest for HarmonyOS and future LLM context packets."""
    tools = [
        AgentToolContract(
            name="direct_accompaniment_generate",
            description="Direct client-callable accompaniment generation path; does not require Agent/LLM.",
            requires_llm=False,
            direct_client_callable=True,
            input_contract={"route": "POST /accompaniment/generate", "schema": "DirectAccompanimentGenerateRequest"},
            output_contract={"asset_format": "midi_base64", "requires_client_looping": False},
        ),
        AgentToolContract(
            name="agent_playback_prepare",
            description="Natural-language immediate practice playback workflow. Agent resolves chart, arrangement intent, and accompaniment asset.",
            requires_llm=False,
            direct_client_callable=True,
            input_contract={"route": "POST /agent/playback/prepare", "schema": "AgentPlaybackPrepareRequest"},
            output_contract={"asset_format": "midi_base64", "playback_instruction": "client_loop_until_target_duration"},
        ),
        AgentToolContract(
            name="agent_practice_plan",
            description="Natural-language practice-plan generation. P0 is deterministic; future LLM planner can replace the planner provider.",
            requires_llm=False,
            direct_client_callable=True,
            input_contract={"route": "POST /agent/practice/plan", "schema": "AgentPlanRequest"},
            output_contract={"schema": "PracticePlan"},
        ),
        AgentToolContract(
            name="session_review_recommendation",
            description="Session review to next-step recommendation. P0 is rule-based.",
            requires_llm=False,
            direct_client_callable=True,
            input_contract={"route": "POST /agent/session/review", "schema": "SessionReviewRequest"},
            output_contract={"schema": "NextStepRecommendation"},
        ),
    ]
    return {
        "version": "v2_3_17",
        "agent_name": "JamMateAgent",
        "principle": "LLM/Agent is an enhancement path, not a required path. Direct accompaniment remains callable without LLM.",
        "available_styles": ["medium_swing", "bossa_nova", "jazz_ballad"],
        "available_tools": [tool.to_dict() for tool in tools],
        "dependency_boundary": {
            "jammate_engine_imports_jammate_agent": False,
            "jammate_agent_uses_engine_only_through_adapter": True,
            "jammate_api_assembles_engine_and_agent": True,
        },
    }


def context_profile_manifest() -> dict[str, Any]:
    profiles = [
        ContextProfileContract(
            task_type="practice_plan_generation",
            required_context_layers=["system_product_context", "capability_manifest", "user_request", "client_context"],
            optional_context_layers=["learner_summary", "active_goal", "relevant_history", "routine_templates"],
            output_schema="PracticePlan",
            llm_required=False,
        ),
        ContextProfileContract(
            task_type="immediate_practice_playback",
            required_context_layers=["system_product_context", "capability_manifest", "user_request", "chart_resolution_context"],
            optional_context_layers=["arrangement_intent", "active_session"],
            output_schema="PlaybackPrepareResult",
            llm_required=False,
        ),
        ContextProfileContract(
            task_type="session_review",
            required_context_layers=["session_review", "current_session"],
            optional_context_layers=["relevant_past_reviews", "active_goal", "learner_summary"],
            output_schema="NextStepRecommendation",
            llm_required=False,
        ),
        ContextProfileContract(
            task_type="coach_qa",
            required_context_layers=["user_question", "current_screen_or_session"],
            optional_context_layers=["music_concept_context", "relevant_history"],
            output_schema="CoachResponse",
            llm_required=True,
        ),
    ]
    return {
        "version": "v2_3_17",
        "context_rule": "LLM receives ContextPacket selected by task type; HarmonyOS sends current user input, client state, and object ids only.",
        "profiles": [profile.to_dict() for profile in profiles],
    }


def arkts_contract_sketch() -> dict[str, Any]:
    """Compact contract sketch for HarmonyOS codegen/reference."""
    return {
        "version": "v2_3_17",
        "note": "This is a reference sketch. ArkTS source should define equivalent interfaces in PracticeTypes.ets / AgentTypes.ets.",
        "interfaces": {
            "ClientContext": {
                "timezone": "string",
                "locale": "string",
                "currentScreen": "string | null",
                "availableMinutes": "number | null",
                "activeSessionId": "string | null",
                "activePlanId": "string | null",
                "selectedMaterialId": "string | null",
            },
            "AgentPlanRequest": {
                "userInput": "string",
                "availableMinutes": "number",
                "instrument": "string",
                "activeGoalId": "string | null",
            },
            "AgentPlaybackPrepareRequest": {
                "userInput": "string",
                "durationMinutes": "number",
                "clientContext": "ClientContext",
            },
            "PracticePlan": {
                "planId": "string",
                "title": "string",
                "durationMinutes": "number",
                "mainFocus": "string",
                "blocks": "ExerciseBlock[]",
                "estimatedDifficulty": "string",
                "explanation": "string | null",
                "source": "rule_based | llm | template | hybrid",
            },
            "PlaybackInstruction": {
                "autoStart": "boolean",
                "targetDurationMinutes": "number",
                "clientLoopUntilTargetDuration": "boolean",
            },
            "AccompanimentAsset": {
                "assetId": "string",
                "format": "midi_base64",
                "midiBase64": "string",
                "midiPath": "string | null",
                "durationSeconds": "number | null",
                "cacheKey": "string | null",
                "debugSummary": "Record<string, Object>",
            },
            "AgentResponse": {
                "ok": "boolean",
                "intentType": "string",
                "plan": "PracticePlan | null",
                "practiceSession": "Record<string, Object> | null",
                "asset": "AccompanimentAsset | null",
                "playbackInstruction": "PlaybackInstruction | null",
                "recommendation": "NextStepRecommendation | null",
                "traceId": "string | null",
                "errorCode": "string | null",
                "message": "string | null",
                "options": "AgentOption[]",
            },
        },
    }

def harmonyos_playback_contract() -> dict[str, Any]:
    """Playback and cache rules for HarmonyOS client implementation."""
    return {
        "version": "v2_3_17",
        "response_case": "snake_case",
        "request_case": "snake_case_or_camelCase",
        "principle": "Agent/LLM is an enhancement path. HarmonyOS can run the local practice workspace without LLM and can directly call /accompaniment/generate when parameters are explicit.",
        "playback_instruction_contract": {
            "auto_start": "If true, client may start playback after caching/decoding the returned asset.",
            "target_duration_minutes": "Practice timer target. This is not the rendered MIDI length.",
            "client_loop_until_target_duration": "If true, loop the returned asset locally until target_duration_minutes is reached or user stops.",
            "asset_loop_mode": "loop_until_target_duration",
            "requires_local_timer": True,
            "stop_condition": "practice_timer_reaches_target_duration_or_user_stops",
        },
        "asset_cache_policy": {
            "canonical_field": "asset.cache_key",
            "fallback_key": "asset.asset_id",
            "cache_payload": ["midi_base64", "midi_path", "duration_seconds", "debug_summary"],
            "reuse_rule": "Reuse cached asset when cache_key matches the current request signature and the user has not requested regeneration.",
            "scope": "recent_practice_asset",
        },
        "recommended_client_state_machine": [
            "idle",
            "preparing_remote_asset",
            "ready_cached",
            "playing",
            "paused",
            "completed",
            "failed",
        ],
        "non_llm_paths": [
            "local practice task / routine / timer / review",
            "POST /accompaniment/generate for explicit manual accompaniment settings",
        ],
        "agent_paths": [
            "POST /agent/practice/plan for natural-language planning",
            "POST /agent/playback/prepare for natural-language immediate practice playback",
        ],
    }


def agent_api_usage_examples() -> dict[str, Any]:
    """Machine-readable HarmonyOS integration examples."""
    return {
        "version": "v2_3_17",
        "examples": {
            "health_check": {
                "method": "GET",
                "path": "/health",
                "expected_ok": True,
            },
            "direct_accompaniment_no_llm": {
                "method": "POST",
                "path": "/accompaniment/generate",
                "request": {
                    "tune": "Blue Bossa",
                    "style": "bossa_nova",
                    "tempo": 120,
                    "choruses": 3,
                    "seed": 42,
                },
                "response_focus": ["ok", "asset.midi_base64", "asset.cache_key"],
            },
            "agent_immediate_playback": {
                "method": "POST",
                "path": "/agent/playback/prepare",
                "request": {
                    "userInput": "我想练 Blue Bossa 20分钟，钢琴和声色彩丰富一些",
                    "durationMinutes": 20,
                },
                "response_focus": [
                    "ok",
                    "asset.midi_base64",
                    "asset.cache_key",
                    "playback_instruction.client_loop_until_target_duration",
                    "playback_instruction.cache_policy.cache_key",
                    "trace_id",
                ],
            },
            "agent_practice_plan": {
                "method": "POST",
                "path": "/agent/practice/plan",
                "request": {
                    "userInput": "我今天有45分钟，想练Misty的ballad comping",
                    "availableMinutes": 45,
                    "instrument": "piano",
                },
                "response_focus": ["ok", "plan.blocks", "trace_id"],
            },
        },
    }


def arkts_contract_source() -> dict[str, Any]:
    """ArkTS source sketch that HarmonyOS can copy into AgentTypes.ets / PracticeTypes.ets."""
    source = r'''
// JamMate Agent / Practice API Contract v2_3_17
// Requests may be sent as camelCase. Current backend responses are canonical snake_case.

export type JamMateStyle = 'medium_swing' | 'bossa_nova' | 'jazz_ballad'
export type AgentIntentType = 'practice_plan_generation' | 'immediate_practice_playback' | string
export type AssetLoopMode = 'loop_until_target_duration'

export interface ClientContext {
  timezone?: string
  locale?: string
  currentScreen?: string | null
  availableMinutes?: number | null
  activeSessionId?: string | null
  activePlanId?: string | null
  selectedMaterialId?: string | null
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

export interface DirectAccompanimentGenerateRequest {
  leadsheet?: Record<string, Object> | null
  tune?: string | null
  style?: JamMateStyle
  tempo?: number
  choruses?: number
  seed?: number
  outputPath?: string | null
  ensemble?: Record<string, Object>
  voicingOverride?: Record<string, Object>
  outputFormat?: 'midi_base64'
}

export interface PracticeMaterial {
  type: string
  tune?: string | null
  section?: string | null
  key?: string | null
  progression?: string | null
  bars?: number | null
  raw?: Record<string, Object>
}

export interface AccompanimentPracticeConfig {
  enabled: boolean
  style: JamMateStyle | string
  tempo: number
  loop_count?: number | null
  duration_minutes?: number | null
  section_loop: boolean
  muted_roles: string[]
  count_in: boolean
  harmonic_expansion_enabled: boolean
  density: string
  practice_role: string
  output_format: 'midi_base64' | 'asset_id'
  arrangement_intent: Record<string, Object>
}

export interface ExerciseBlock {
  block_id: string
  type: string
  title: string
  intent: string
  duration_minutes: number
  material?: PracticeMaterial | null
  tempo?: number | null
  style?: string | null
  accompaniment_config?: AccompanimentPracticeConfig | null
  success_criteria: string[]
  review_prompt?: string | null
  status: 'pending' | 'active' | 'completed' | 'skipped' | string
}

export interface PracticePlan {
  plan_id: string
  title: string
  duration_minutes: number
  main_focus: string
  blocks: ExerciseBlock[]
  estimated_difficulty: string
  explanation?: string | null
  source: 'rule_based' | 'llm' | 'template' | 'hybrid' | string
}

export interface AccompanimentAsset {
  asset_id?: string
  format: 'midi_base64'
  midi_base64: string
  midi_path?: string | null
  duration_seconds?: number | null
  cache_key?: string | null
  debug_summary?: Record<string, Object>
}

export interface PlaybackInstruction {
  auto_start: boolean
  target_duration_minutes: number
  client_loop_until_target_duration: boolean
  asset_loop_mode?: AssetLoopMode | string
  stop_condition?: string
  requires_local_timer?: boolean
  cache_policy?: {
    cache_key?: string | null
    scope?: string
    reuse_when_request_signature_matches?: boolean
  }
}

export interface AgentOption {
  type: string
  label: string
}

export interface AgentResponse {
  ok: boolean
  intent_type: AgentIntentType
  plan?: PracticePlan | null
  practice_session?: Record<string, Object> | null
  asset?: AccompanimentAsset | null
  playback_instruction?: PlaybackInstruction | null
  recommendation?: Record<string, Object> | null
  explanation?: string | null
  error_code?: string | null
  message?: string | null
  options?: AgentOption[]
  trace_id?: string | null
}
'''.strip()
    return {
        "version": "v2_3_17",
        "filename_suggestion": "AgentTypes.ets",
        "response_case": "snake_case",
        "request_case": "camelCase_or_snake_case",
        "source": source,
    }


def response_case_policy_manifest() -> dict[str, Any]:
    """Canonical API case policy for Python backend and HarmonyOS client-domain mapping."""
    return {
        "version": "v2_3_17",
        "canonical_backend_response_case": "snake_case",
        "accepted_request_cases": ["snake_case", "camelCase"],
        "harmonyos_client_domain_case": "camelCase",
        "adapter_file": "CaseAdapter.ets",
        "api_client_file": "JamMateApiClient.ets",
        "principles": [
            "Backend API responses remain canonical snake_case for Python/Pydantic stability.",
            "HarmonyOS may send camelCase or snake_case requests; FastAPI schemas accept both.",
            "HarmonyOS UI/store code should consume camelCase domain objects after CaseAdapter mapping.",
            "Do not maintain two backend response formats unless a future compatibility requirement makes it necessary.",
        ],
        "examples": {
            "backend_raw": {
                "trace_id": "trace_001",
                "playback_instruction": {
                    "target_duration_minutes": 30,
                    "client_loop_until_target_duration": True,
                },
            },
            "harmonyos_domain": {
                "traceId": "trace_001",
                "playbackInstruction": {
                    "targetDurationMinutes": 30,
                    "clientLoopUntilTargetDuration": True,
                },
            },
        },
    }
