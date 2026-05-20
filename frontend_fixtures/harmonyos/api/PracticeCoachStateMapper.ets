// JamMate Practice Coach State Mapper v2_10_27
// Copy target suggestion: entry/src/main/ets/features/jammateAgent/model/PracticeCoachStateMapper.ets
// This mapper is frontend-only guidance. It renders backend action intent; it must not infer hidden backend decisions.

import type {
  PracticeCoachMessageExecuteResponse,
  PracticeCoachMessageData,
  PracticeCoachResponseType,
  PracticeCoachSheetIntent,
  PracticeCoachPlanProposal,
  PracticeCoachRoutineCardPayload,
  PracticeCoachFrontendUiAction,
} from '../model/PracticeCoachTypes'

export type PracticeCoachUiStateKind =
  | 'loading'
  | 'chat_message'
  | 'clarifying'
  | 'profile_sheet'
  | 'plan_proposal'
  | 'routine_card'
  | 'cannot_proceed'
  | 'backend_error'
  | 'network_error'

export interface PracticeCoachUiState {
  kind: PracticeCoachUiStateKind
  message: string
  responseType?: PracticeCoachResponseType
  suggestedReplies: string[]
  missingFields: string[]
  nextClientActions: string[]
  sheetIntent?: PracticeCoachSheetIntent | null
  planProposal?: PracticeCoachPlanProposal | null
  routineCardPayload?: PracticeCoachRoutineCardPayload | null
  canOpenProfileSheet: boolean
  canShowPlanProposal: boolean
  canShowRoutineCard: boolean
  canStartRoutine: boolean
  shouldReplaceCurrentProposal: boolean
  shouldShowRecordedSummary: boolean
  safeToAutostartRoutine: false
  frontendUiAction?: PracticeCoachFrontendUiAction | null
  deviceFeedbackTracePack?: Record<string, unknown> | null
  raw?: PracticeCoachMessageExecuteResponse | null
}

export function practiceCoachLoadingState(message: string = '正在思考今天的练习安排…'): PracticeCoachUiState {
  return {
    kind: 'loading',
    message,
    suggestedReplies: [],
    missingFields: [],
    nextClientActions: [],
    canOpenProfileSheet: false,
    canShowPlanProposal: false,
    canShowRoutineCard: false,
    canStartRoutine: false,
    shouldReplaceCurrentProposal: false,
    shouldShowRecordedSummary: false,
    safeToAutostartRoutine: false,
  }
}

export function practiceCoachNetworkErrorState(message: string = '网络连接失败，请稍后重试。'): PracticeCoachUiState {
  return {
    kind: 'network_error',
    message,
    suggestedReplies: [],
    missingFields: [],
    nextClientActions: [],
    canOpenProfileSheet: false,
    canShowPlanProposal: false,
    canShowRoutineCard: false,
    canStartRoutine: false,
    shouldReplaceCurrentProposal: false,
    shouldShowRecordedSummary: false,
    safeToAutostartRoutine: false,
  }
}

export function mapPracticeCoachResponseToUiState(response: PracticeCoachMessageExecuteResponse): PracticeCoachUiState {
  if (!response.ok) {
    return buildState('backend_error', response.message || 'Practice Coach 暂时不可用。', response)
  }

  const data = response.data || ({} as PracticeCoachMessageData)
  const message = (data.content || data.message || response.message || '') as string
  const responseType = data.responseType

  switch (responseType) {
    case 'ask_clarifying_question':
      return buildState('clarifying', message, response)
    case 'request_profile_sheet':
      return buildState('profile_sheet', message, response)
    case 'practice_plan_proposal':
    case 'practice_plan_revision':
      return buildState('plan_proposal', message, response)
    case 'routine_card_ready':
      return buildState('routine_card', message, response)
    case 'cannot_proceed':
      return buildState('cannot_proceed', message, response)
    case 'chat_message':
    default:
      return buildState('chat_message', message || '我已经记录。', response)
  }
}

function buildState(
  kind: PracticeCoachUiStateKind,
  message: string,
  response: PracticeCoachMessageExecuteResponse,
): PracticeCoachUiState {
  const data = response.data || ({} as PracticeCoachMessageData)
  const nextClientActions = data.nextClientActions || []
  const routineCardPayload = data.routineCardPayload || null
  const frontendUiAction = (data.frontendUiAction || response.debug?.frontendUiAction || null) as PracticeCoachFrontendUiAction | null
  const canShowRoutineCard = (frontendUiAction?.shouldRenderRoutineCard === true) || (kind === 'routine_card' && !!routineCardPayload)

  return {
    kind,
    message,
    responseType: data.responseType,
    suggestedReplies: data.suggestedReplies || [],
    missingFields: data.missingFields || [],
    nextClientActions,
    sheetIntent: data.sheetIntent || null,
    planProposal: data.planProposal || null,
    routineCardPayload,
    canOpenProfileSheet: (frontendUiAction?.shouldOpenProfileSheet === true) || (kind === 'profile_sheet' && !!data.sheetIntent && nextClientActions.indexOf('open_profile_sheet') >= 0),
    canShowPlanProposal: (frontendUiAction?.shouldRenderPlanProposalCard === true) || (kind === 'plan_proposal' && !!data.planProposal),
    canShowRoutineCard,
    canStartRoutine: (frontendUiAction?.canStartRoutineByUserTap === true) || (canShowRoutineCard && routineCardPayload.startEnabled === true && routineCardPayload.requiresUserTapToStart === true),
    shouldReplaceCurrentProposal: frontendUiAction?.shouldReplaceCurrentProposal === true,
    shouldShowRecordedSummary: frontendUiAction?.shouldShowRecordedSummary === true,
    safeToAutostartRoutine: false,
    frontendUiAction,
    deviceFeedbackTracePack: (data.deviceFeedbackTracePack as Record<string, unknown> | undefined) || (response.debug?.deviceFeedbackTracePack as Record<string, unknown> | undefined) || null,
    raw: response,
  }
}
