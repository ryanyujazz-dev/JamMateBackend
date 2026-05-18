// JamMate API Client Sketch v2_4_7
// Copy target suggestion: entry/src/main/ets/features/jammateAgent/api/JamMateApiClient.ets
// Requests may be sent as camelCase. Responses are mapped from backend snake_case to camelCase domain types.

import type { AgentContextRuntimePreviewRequest, AgentContextRuntimePreviewResponse, AgentPlanRequest, AgentPlaybackPrepareRequest, AgentResponse, AgentToolInvocationPreviewRequest, AgentToolInvocationPreviewResponse } from '../model/AgentTypes'
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

  async getLLMProviderBoundarySpec(): Promise<Record<string, unknown>> {
    const raw = await this.get('/agent/llm/provider/spec')
    return deepSnakeToCamel(raw) as Record<string, unknown>
  }

  async previewAgentToolInvocation(request: AgentToolInvocationPreviewRequest): Promise<AgentToolInvocationPreviewResponse> {
    const raw = await this.post('/agent/tools/invocation/preview', request as Record<string, unknown>)
    return deepSnakeToCamel(raw) as AgentToolInvocationPreviewResponse
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
