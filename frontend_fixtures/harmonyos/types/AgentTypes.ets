// JamMate Agent API Types v2_4_7
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
  toolDescriptors?: AgentToolDescriptor[]
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

export interface AgentToolInvocationPreviewRequest {
  requestId?: string | null
  userInput?: string | null
  taskType?: AgentIntentType | string
  toolName: string
  arguments?: Record<string, unknown>
  clientContext?: ClientContext
}

export interface ToolInvocationPreviewResult {
  previewVersion: string
  toolRegistryVersion: string
  ok: boolean
  status: string
  toolName: string
  taskType: AgentIntentType | string
  knownTool: boolean
  allowedByContext: boolean
  executionEnabled: boolean
  autonomousExecutionEnabled: boolean
  wouldExecute: boolean
  descriptor?: AgentToolDescriptor | null
  normalizedArguments: Record<string, unknown>
  validation: Record<string, unknown>
  blockingReasons: string[]
  warnings: string[]
}

export interface AgentToolInvocationPreviewResponse {
  ok: boolean
  preview: ToolInvocationPreviewResult
  contextPacketSummary: Record<string, unknown>
}

export interface LLMProviderBoundarySpec {
  version: string
  boundaryVersion: string
  route: string
  status: Record<string, unknown>
  configEnv: Record<string, unknown>
  guards: Record<string, unknown>
  futureProviderContract: Record<string, unknown>
}

export interface LLMProviderBoundarySpecResponse {
  ok: boolean
  spec: LLMProviderBoundarySpec
}

export interface AgentToolDescriptor {
  registryVersion: string
  name: string
  title: string
  description: string
  category: string
  taskTypes: string[]
  requiresLlm: boolean
  directClientCallable: boolean
  deterministicWorkflow?: string | null
  route?: string | null
  inputContract: Record<string, unknown>
  outputContract: Record<string, unknown>
  adapterBoundary?: string | null
  sideEffectLevel: string
  executionEnabled: boolean
  autonomousExecutionEnabled: boolean
  guardrails: string[]
}

export interface AgentToolRegistryResponse {
  ok: boolean
  registry: {
    version: string
    registryVersion: string
    executionStatus: Record<string, unknown>
    tools: AgentToolDescriptor[]
    toolNames: string[]
    taskAllowLists: Record<string, string[]>
  }
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
