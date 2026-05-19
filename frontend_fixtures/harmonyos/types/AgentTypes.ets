// JamMate Agent API Types v2_10_6 integration handoff
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


export interface HarmonyOSRoutineCompletionRecord {
  sessionId: string
  title?: string | null
  style?: JamMateStyle | string | null
  tempo?: number | null
  actualSeconds?: number | null
  completed?: boolean
  completedAtUtc?: string | null
  practiceGoal?: string | null
  notes?: string | null
  metadata?: Record<string, unknown>
}

export interface HarmonyOSRoutineCompletionRecordExecuteRequest {
  userId?: string | null
  sessionId?: string | null
  deviceId?: string | null
  // Product HarmonyOS clients do not need to send sqliteDbPath/environment/write gates.
  // Those are backend-owned; keep these fields optional only for local smoke/debug overrides.
  sqliteDbPath?: string | null
  environment?: 'test' | 'dev' | 'local' | string
  clientConfirmedRecordWrite?: boolean
  idempotencyKey?: string | null
  routineCompletionRecord: HarmonyOSRoutineCompletionRecord
}

export interface HarmonyOSProviderFixtureResult {
  ok: boolean
  providerName?: string | null
  model?: string | null
  content?: string | null
}

export interface HarmonyOSTodayPracticeGuidancePreviewRequest {
  userId?: string | null
  sessionId?: string | null
  deviceId?: string | null
  userMessage?: string
  userInput?: string
  // Product HarmonyOS clients do not need to send sqliteDbPath/environment.
  // Those are backend-owned; keep these fields optional only for local smoke/debug overrides.
  sqliteDbPath?: string | null
  environment?: 'test' | 'dev' | 'local' | string
  availableMinutes?: number | null
  clientContext?: ClientContext
  providerResult?: HarmonyOSProviderFixtureResult | Record<string, unknown>
}

export interface HarmonyOSAgentSafety {
  backendSQLiteWriteMayOccur: boolean
  writesHarmonyOSLocalState: boolean
  startsRoutine: boolean
  callsEngineAdapter: boolean
  createsMidiAsset: boolean
  startsPlayback: boolean
  [key: string]: unknown
}

export interface HarmonyOSRoutineCompletionRecordData {
  completionRecordPersisted: boolean
  nextTodayGuidanceCanReadHistory: boolean
  idempotentReplay?: boolean
  routineCompletionRecord?: Record<string, unknown>
  [key: string]: unknown
}

export interface HarmonyOSTodayPracticeGuidanceData {
  content?: string | null
  guidancePreviewReady: boolean
  contextSource: 'sqlite_backend' | 'terminal_memory' | 'none' | string
  actionCardPayload?: Record<string, unknown> | null
  routineCandidateCount: number
  requiresUserConfirmationBeforeRoutineStart: boolean
  [key: string]: unknown
}

export interface HarmonyOSAgentEnvelope<TData extends Record<string, unknown> = Record<string, unknown>> {
  ok: boolean
  code: string
  message: string
  data: TData
  debug: Record<string, unknown>
  safety: HarmonyOSAgentSafety
}

export type HarmonyOSRoutineCompletionRecordExecuteResponse = HarmonyOSAgentEnvelope<HarmonyOSRoutineCompletionRecordData>
export type HarmonyOSTodayPracticeGuidancePreviewResponse = HarmonyOSAgentEnvelope<HarmonyOSTodayPracticeGuidanceData>

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
  traceContractVersion: string
  traceSchemaVersion: string
  traceId: string
  taskType: string
  requestId?: string | null
  userInputPreview?: string
  createdAt?: string
  updatedAt?: string
  validationResult?: string | null
  stepCount: number
  steps?: number
  hasContextPacketSummary: boolean
  hasFinalResponseSummary: boolean
}

export interface AgentTraceStep {
  name: string
  payload?: Record<string, unknown>
  at?: string
}

export interface AgentTraceDetail {
  traceContractVersion: string
  traceSchemaVersion: string
  traceId: string
  taskType: string
  requestId?: string | null
  userInput: string
  contextPacketSummary: Record<string, unknown>
  steps: AgentTraceStep[]
  validationResult?: string | null
  finalResponseSummary: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface AgentTraceListResponse {
  ok: boolean
  traceContractVersion: string
  traces: AgentTraceSummary[]
}

export interface AgentTraceDetailResponse {
  ok: boolean
  traceContractVersion: string
  trace?: AgentTraceDetail | null
  errorCode?: 'TRACE_NOT_FOUND' | string | null
  message?: string | null
}

export interface AgentTraceApiSpecResponse {
  ok: boolean
  spec: Record<string, unknown>
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


export type AgentHarmonyOSTodayGuidanceCode =
  | 'today_guidance_ready'
  | 'today_guidance_needs_context_or_provider'
  | string

export type AgentHarmonyOSRoutineCompletionCode =
  | 'routine_completion_record_persisted'
  | 'routine_completion_record_blocked'
  | string

export interface AgentHarmonyOSRoutineCompletionRecord {
  sessionId: string
  title: string
  style?: JamMateStyle | string | null
  tempo?: number | null
  actualSeconds: number
  completed: boolean
  completedAtUtc?: string | null
  notes?: string | null
  source?: 'harmonyos_client' | 'terminal' | string
}

export interface AgentHarmonyOSTodayPracticeGuidanceRequest {
  userId?: string | null
  sessionId?: string | null
  deviceId?: string | null
  userMessage?: string
  userInput?: string
  sqliteDbPath?: string | null // Optional debug override; product clients should omit.
  environment?: 'test' | 'local_dev' | string
  availableMinutes?: number | null
  providerResult?: Record<string, unknown> | null
  callProvider?: boolean
  traceId?: string | null
  includeDebugPayload?: boolean
}

export interface AgentHarmonyOSRoutineCompletionRecordRequest {
  userId?: string | null
  sessionId?: string | null
  deviceId?: string | null
  sqliteDbPath?: string | null // Optional debug override; product clients should omit.
  environment?: 'test' | 'local_dev' | string
  clientConfirmedRecordWrite?: boolean // Optional debug override; product route injects confirmation when omitted.
  idempotencyKey?: string | null
  routineCompletionRecord: AgentHarmonyOSRoutineCompletionRecord
  userPracticeProfile?: Record<string, unknown> | null
  practicePlan?: Record<string, unknown> | null
  traceId?: string | null
  includeDebugPayload?: boolean
}

export interface AgentHarmonyOSEnvelope<DataT = Record<string, unknown>, CodeT = string> {
  ok: boolean
  code: CodeT
  message: string
  data: DataT
  debug: Record<string, unknown>
  safety: {
    displayOnly?: boolean
    backendSQLiteWriteMayOccur: boolean
    writesHarmonyOSLocalState: false
    startsRoutine: false
    callsAccompanimentGenerate: false
    callsEngineAdapter: false
    createsMidiAsset: false
    startsPlayback: false
    createsPostSessionRecommendationCard: false
    clientDecidesPresentation: true
    frontendFlowAssumption: false
  }
}

export interface AgentHarmonyOSTodayPracticeGuidanceData {
  content: string
  guidancePreviewReady: boolean
  contextSource: 'sqlite_backend' | 'terminal_memory' | 'provider_result_only' | 'none' | string
  actionCardPayload: Record<string, unknown>
  routineCandidateCount: number
  requiresUserConfirmationBeforeRoutineStart: boolean
}

export interface AgentHarmonyOSRoutineCompletionRecordData {
  content: string
  completionRecordPersisted: boolean
  nextTodayGuidanceCanReadHistory: boolean
  idempotentReplay: boolean
  routineCompletionRecord: AgentHarmonyOSRoutineCompletionRecord | Record<string, unknown>
}

export type AgentHarmonyOSTodayPracticeGuidanceResponse = AgentHarmonyOSEnvelope<AgentHarmonyOSTodayPracticeGuidanceData, AgentHarmonyOSTodayGuidanceCode>
export type AgentHarmonyOSRoutineCompletionRecordResponse = AgentHarmonyOSEnvelope<AgentHarmonyOSRoutineCompletionRecordData, AgentHarmonyOSRoutineCompletionCode>
