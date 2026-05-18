// JamMate Playback / Accompaniment Types v2_4_12
// Copy target: entry/src/main/ets/features/practice/model/PlaybackTypes.ets
// Client-domain types are camelCase. Duration is a practice-timer concern.

import type { JamMateStyle } from '../../jammateAgent/model/AgentTypes'

export type AssetLoopMode = 'loop_until_target_duration' | string

export interface JamMateChordEventV2 {
  beat: number
  symbol: string
  beats?: number | null
  metadata?: Record<string, unknown>
}

export interface JamMateBarV2 {
  chords: JamMateChordEventV2[]
  timeSignature?: { numerator: number; denominator: number }
  metadata?: Record<string, unknown>
}

export interface JamMateSectionV2 {
  id?: string
  label?: string
  phrase?: string
  role?: string
  bars: JamMateBarV2[]
  metadata?: Record<string, unknown>
}

export type JamMateWrittenFormItemV2 =
  | string
  | { section: string; repeat?: number; times?: number; label?: string | null; metadata?: Record<string, unknown> }
  | Record<string, unknown>

export interface JamMateLeadsheetV2 {
  schema_version: 'jammate_leadsheet_v2'
  title: string
  key?: string
  default_time_signature?: { numerator: number; denominator: number }
  sections: Record<string, JamMateSectionV2> | JamMateSectionV2[]
  written_form: JamMateWrittenFormItemV2[]
  metadata?: Record<string, unknown>
}

export interface DirectAccompanimentGenerateRequest {
  // Preferred HarmonyOS path: inline jammate_leadsheet_v2 with sections + written_form.
  leadsheet?: JamMateLeadsheetV2 | Record<string, unknown> | null
  // Optional fallback only; do not depend on tune for user-custom charts.
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
