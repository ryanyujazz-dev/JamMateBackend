// JamMate Playback / Accompaniment Types v2_3_16
// Copy target: entry/src/main/ets/features/practice/model/PlaybackTypes.ets
// Client-domain types are camelCase. Duration is a practice-timer concern.

import type { JamMateStyle } from '../../jammateAgent/model/AgentTypes'

export type AssetLoopMode = 'loop_until_target_duration' | string

export interface DirectAccompanimentGenerateRequest {
  leadsheet?: Record<string, unknown> | null
  tune?: string | null
  style?: JamMateStyle
  tempo?: number
  choruses?: number
  seed?: number
  outputPath?: string | null
  ensemble?: Record<string, unknown>
  voicingOverride?: Record<string, unknown>
  outputFormat?: 'midi_base64'
}

export interface AccompanimentAsset {
  assetId?: string
  format: 'midi_base64'
  midiBase64: string
  midiPath?: string | null
  durationSeconds?: number | null
  cacheKey?: string | null
  debugSummary?: Record<string, unknown>
}

export interface PlaybackInstruction {
  autoStart: boolean
  targetDurationMinutes: number
  clientLoopUntilTargetDuration: boolean
  assetLoopMode?: AssetLoopMode
  stopCondition?: string
  requiresLocalTimer?: boolean
  cachePolicy?: {
    cacheKey?: string | null
    scope?: string
    reuseWhenRequestSignatureMatches?: boolean
  }
}

export interface PlaybackState {
  status: 'idle' | 'preparing_remote_asset' | 'ready_cached' | 'playing' | 'paused' | 'completed' | 'failed'
  cacheKey?: string | null
  assetId?: string | null
  targetDurationMinutes?: number | null
  elapsedSeconds: number
  errorMessage?: string | null
}

export interface DirectAccompanimentGenerateResponse {
  ok: boolean
  asset?: AccompanimentAsset
  errorCode?: string
  message?: string
  options?: Array<Record<string, unknown>>
}
