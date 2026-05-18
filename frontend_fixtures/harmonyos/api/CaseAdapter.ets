// JamMate Case Adapter v2_4_7
// Copy target: entry/src/main/ets/features/jammateAgent/api/CaseAdapter.ets
// Backend canonical response: snake_case. Client-domain model: camelCase.

import type { AgentResponse } from '../model/AgentTypes'
import type { DirectAccompanimentGenerateResponse } from '../../practice/model/PlaybackTypes'

function snakeToCamelKey(key: string): string {
  return key.replace(/_([a-zA-Z0-9])/g, (_match: string, letter: string): string => letter.toUpperCase())
}

function camelToSnakeKey(key: string): string {
  return key.replace(/[A-Z]/g, (letter: string): string => `_${letter.toLowerCase()}`)
}

export function deepSnakeToCamel(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item: unknown): unknown => deepSnakeToCamel(item))
  }
  if (value !== null && typeof value === 'object') {
    const output: Record<string, unknown> = {}
    Object.keys(value as Record<string, unknown>).forEach((key: string): void => {
      output[snakeToCamelKey(key)] = deepSnakeToCamel((value as Record<string, unknown>)[key])
    })
    return output
  }
  return value
}

export function deepCamelToSnake(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item: unknown): unknown => deepCamelToSnake(item))
  }
  if (value !== null && typeof value === 'object') {
    const output: Record<string, unknown> = {}
    Object.keys(value as Record<string, unknown>).forEach((key: string): void => {
      output[camelToSnakeKey(key)] = deepCamelToSnake((value as Record<string, unknown>)[key])
    })
    return output
  }
  return value
}

export function mapAgentResponse(raw: Record<string, unknown>): AgentResponse {
  return deepSnakeToCamel(raw) as AgentResponse
}

export function mapDirectAccompanimentResponse(raw: Record<string, unknown>): DirectAccompanimentGenerateResponse {
  return deepSnakeToCamel(raw) as DirectAccompanimentGenerateResponse
}
