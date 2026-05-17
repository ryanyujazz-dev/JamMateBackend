// JamMate Agent API Types v2_4_0
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

export interface AgentContextRuntimePreviewRequest {
  requestId?: string | null
  userInput: string
  taskType?: AgentIntentType | null
  clientContext?: ClientContext
  availableMinutes?: number | null
  durationMinutes?: number | null
  instrument?: string
  localUnsyncedSummary?: Record<string, unknown>
}

export interface ContextPacket {
  contextRuntimeVersion: string
  taskType: AgentIntentType | string
  selectedContextLayers: string[]
  systemProductContext: Record<string, unknown>
  userRequest: Record<string, unknown>
  clientContext: Record<string, unknown>
  capabilities: Record<string, unknown>
  constraints: Record<string, unknown>
  allowedTools: string[]
  outputContract: Record<string, unknown>
  runtimePolicy: Record<string, unknown>
  routingHints: Record<string, unknown>
}

export interface RunLoopPreview {
  contractVersion: string
  ok: boolean
  runtimeMode: 'preview_only' | string
  llmProviderConfigured: boolean
  toolExecutionEnabled: boolean
  maxSteps: number
  allowedTools: string[]
  nextAction: string
  reason: string
  warnings: string[]
}

export interface AgentContextRuntimePreviewResponse {
  ok: boolean
  taskType: AgentIntentType | string
  contextPacket: ContextPacket
  runloopPreview: RunLoopPreview
  traceId?: string | null
  errorCode?: string | null
  message?: string | null
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
