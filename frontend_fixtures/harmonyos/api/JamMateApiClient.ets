// JamMate API Client Sketch v2_10_6 integration handoff
// Copy target suggestion: entry/src/main/ets/features/jammateAgent/api/JamMateApiClient.ets
// Requests may be sent as camelCase. Responses are mapped from backend snake_case to camelCase domain types.

import type { AgentContextRuntimePreviewRequest, AgentContextRuntimePreviewResponse, AgentHarmonyOSRoutineCompletionRecordRequest, AgentHarmonyOSRoutineCompletionRecordResponse, AgentHarmonyOSTodayPracticeGuidanceRequest, AgentHarmonyOSTodayPracticeGuidanceResponse, AgentPlanRequest, AgentPlaybackPrepareRequest, AgentResponse, AgentToolInvocationPreviewRequest, AgentToolInvocationPreviewResponse, AgentTraceApiSpecResponse, HarmonyOSRoutineCompletionRecordExecuteRequest, HarmonyOSRoutineCompletionRecordExecuteResponse, HarmonyOSTodayPracticeGuidancePreviewRequest, HarmonyOSTodayPracticeGuidancePreviewResponse, AgentTraceDetailResponse, AgentTraceListResponse } from '../model/AgentTypes'
import type { PracticeCoachMessageExecuteRequest, PracticeCoachMessageExecuteResponse } from '../model/PracticeCoachTypes'
import type { DirectAccompanimentGenerateRequest, DirectAccompanimentGenerateResponse } from '../../practice/model/PlaybackTypes'
import { deepSnakeToCamel, mapAgentResponse, mapDirectAccompanimentResponse } from './CaseAdapter'

export class JamMateApiClient {
  constructor(private readonly baseUrl: string) {}

  async health(): Promise<Record<string, unknown>> {
    return this.get('/health')
  }

  async generatePracticePlan(request: AgentPlanRequest): Promise<AgentResponse> {
    const raw = await this.post('/agent/practice/plan', request as Record<string, unknown>)
    return mapAgentResponse(raw)
  }

  async prepareAgentPlayback(request: AgentPlaybackPrepareRequest): Promise<AgentResponse> {
    const raw = await this.post('/agent/playback/prepare', request as Record<string, unknown>)
    return mapAgentResponse(raw)
  }

  async previewAgentContextRuntime(request: AgentContextRuntimePreviewRequest): Promise<AgentContextRuntimePreviewResponse> {
    const raw = await this.post('/agent/context/runtime/preview', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as AgentContextRuntimePreviewResponse
  }

  async executeHarmonyOSRoutineCompletionRecord(request: HarmonyOSRoutineCompletionRecordExecuteRequest): Promise<HarmonyOSRoutineCompletionRecordExecuteResponse> {
    const raw = await this.post('/agent/harmonyos/routine-completion-record/execute', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as HarmonyOSRoutineCompletionRecordExecuteResponse
  }

  async previewHarmonyOSTodayPracticeGuidance(request: HarmonyOSTodayPracticeGuidancePreviewRequest): Promise<HarmonyOSTodayPracticeGuidancePreviewResponse> {
    const raw = await this.post('/agent/harmonyos/today-practice-guidance/preview', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as HarmonyOSTodayPracticeGuidancePreviewResponse
  }

  async getLLMProviderBoundarySpec(): Promise<Record<string, unknown>> {
    const raw = await this.get('/agent/llm/provider/spec')
    return deepSnakeToCamel(raw) as Record<string, unknown>
  }

  async previewAgentToolInvocation(request: AgentToolInvocationPreviewRequest): Promise<AgentToolInvocationPreviewResponse> {
    const raw = await this.post('/agent/tools/invocation/preview', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as AgentToolInvocationPreviewResponse
  }

  async getAgentTraceSpec(): Promise<AgentTraceApiSpecResponse> {
    const raw = await this.get('/agent/traces/spec')
    return deepSnakeToCamel(raw) as AgentTraceApiSpecResponse
  }

  async listAgentTraces(limit: number = 20): Promise<AgentTraceListResponse> {
    const raw = await this.get(`/agent/traces?limit=${limit}`)
    return deepSnakeToCamel(raw) as AgentTraceListResponse
  }

  async getAgentTrace(traceId: string): Promise<AgentTraceDetailResponse> {
    const raw = await this.get(`/agent/traces/${traceId}`)
    return deepSnakeToCamel(raw) as AgentTraceDetailResponse
  }



  async previewHarmonyOSTodayPracticeGuidance(request: AgentHarmonyOSTodayPracticeGuidanceRequest): Promise<AgentHarmonyOSTodayPracticeGuidanceResponse> {
    const raw = await this.post('/agent/harmonyos/today-practice-guidance/preview', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as AgentHarmonyOSTodayPracticeGuidanceResponse
  }

  async recordHarmonyOSRoutineCompletion(request: AgentHarmonyOSRoutineCompletionRecordRequest): Promise<AgentHarmonyOSRoutineCompletionRecordResponse> {
    const raw = await this.post('/agent/harmonyos/routine-completion-record/execute', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as AgentHarmonyOSRoutineCompletionRecordResponse
  }

  async getHarmonyOSTodayGuidanceContractSpec(): Promise<Record<string, unknown>> {
    const raw = await this.get('/agent/harmonyos/today-guidance-api-contract-alignment/spec')
    return deepSnakeToCamel(raw) as Record<string, unknown>
  }


  async executePracticeCoachMessage(request: PracticeCoachMessageExecuteRequest): Promise<PracticeCoachMessageExecuteResponse> {
    const raw = await this.post('/agent/harmonyos/practice-coach-session/message/execute', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as PracticeCoachMessageExecuteResponse
  }

  async generateDirectAccompaniment(request: DirectAccompanimentGenerateRequest): Promise<DirectAccompanimentGenerateResponse> {
    const raw = await this.post('/accompaniment/generate', request as Record<string, unknown>)
    return mapDirectAccompanimentResponse(raw)
  }

  private async get(path: string): Promise<Record<string, unknown>> {
    throw new Error(`Replace JamMateApiClient.get with HarmonyOS HTTP implementation: ${this.baseUrl}${path}`)
  }

  private async post(path: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {
    throw new Error(`Replace JamMateApiClient.post with HarmonyOS HTTP implementation: ${this.baseUrl}${path} body=${JSON.stringify(body)}`)
  }
}
