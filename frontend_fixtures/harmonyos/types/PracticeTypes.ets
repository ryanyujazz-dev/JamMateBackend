// JamMate Practice Domain Types v2_6_1
// Copy target: entry/src/main/ets/features/practice/model/PracticeTypes.ets
// Client-domain types are camelCase. Backend raw snake_case payloads should be mapped by CaseAdapter.ets.

import type { JamMateStyle } from '../../jammateAgent/model/AgentTypes'

export type ExerciseBlockType =
  | 'technique'
  | 'time_feel'
  | 'ear_training'
  | 'guide_tone'
  | 'voicing'
  | 'comping'
  | 'improvisation'
  | 'transcription'
  | 'repertoire'
  | 'review'
  | 'custom'
  | string

export type ExerciseBlockStatus = 'pending' | 'active' | 'completed' | 'skipped' | string
export type PracticeSessionStatus = 'planned' | 'active' | 'paused' | 'completed' | 'abandoned' | string
export type SyncStatus = 'local_only' | 'pending' | 'synced' | 'conflict' | 'failed' | string

export interface PracticeMaterial {
  type: string
  tune?: string | null
  section?: string | null
  key?: string | null
  progression?: string | null
  bars?: number | null
  raw?: Record<string, unknown>
}

export interface AccompanimentPracticeConfig {
  enabled: boolean
  style: JamMateStyle | string
  tempo: number
  loopCount?: number | null
  durationMinutes?: number | null
  sectionLoop: boolean
  mutedRoles: Array<'piano' | 'bass' | 'drums' | 'melody' | string>
  countIn: boolean
  harmonicExpansionEnabled: boolean
  density: string
  practiceRole: string
  outputFormat: 'midi_base64' | 'asset_id'
  arrangementIntent: Record<string, unknown>
}

export interface ExerciseBlock {
  blockId: string
  type: ExerciseBlockType
  title: string
  intent: string
  durationMinutes: number
  material?: PracticeMaterial | null
  tempo?: number | null
  style?: string | null
  accompanimentConfig?: AccompanimentPracticeConfig | null
  successCriteria: string[]
  reviewPrompt?: string | null
  status: ExerciseBlockStatus
}

export interface PracticePlan {
  planId: string
  title: string
  durationMinutes: number
  mainFocus: string
  blocks: ExerciseBlock[]
  estimatedDifficulty: string
  explanation?: string | null
  source: 'rule_based' | 'llm' | 'template' | 'hybrid' | string
}

export interface PracticeSession {
  sessionId: string
  planId?: string | null
  startedAt?: string | null
  endedAt?: string | null
  status: PracticeSessionStatus
  totalPlannedMinutes?: number | null
  totalActualMinutes: number
  currentBlockId?: string | null
  blocks: ExerciseBlock[]
  syncStatus: SyncStatus
}

export interface StuckPoint {
  material?: string | null
  issue: string
}

export interface SessionReview {
  sessionId?: string
  completed?: boolean
  difficulty?: 'too_easy' | 'easy' | 'good_challenge' | 'too_hard' | string
  focusScore?: number | null
  timeFeel?: 'stable' | 'rushing' | 'dragging' | 'unsure' | string | null
  tempoResult?: Record<string, unknown> | null
  stuckPoints?: StuckPoint[]
  notes?: string | null
  nextActionPreference?: string | null
}

export interface NextStepRecommendation {
  recommendationId: string
  source: 'rule_based' | 'llm' | 'hybrid' | string
  summary: string
  actions: Array<Record<string, unknown>>
}
