// JamMate Practice Coach Session Types v2_10_25
// Copy target suggestion: entry/src/main/ets/features/jammateAgent/model/PracticeCoachTypes.ets
// Backend responses are canonical snake_case. JamMateApiClient maps them into these camelCase client-domain types.
// Production HarmonyOS requests must NOT include llmActionDecisionResult; that field exists only in backend smoke fixtures.

export type PracticeCoachResponseType =
  | 'chat_message'
  | 'ask_clarifying_question'
  | 'request_profile_sheet'
  | 'practice_plan_proposal'
  | 'practice_plan_revision'
  | 'routine_card_ready'
  | 'cannot_proceed'
  | string

export type PracticeCoachNextClientAction =
  | 'show_chat_message'
  | 'show_suggested_replies'
  | 'open_profile_sheet'
  | 'submit_profile_form_result'
  | 'show_practice_plan_proposal'
  | 'ask_user_to_confirm_or_adjust'
  | 'show_routine_card'
  | 'wait_for_user_start_routine'
  | string

export interface PracticeCoachProfileFormResult {
  primaryInstrument?: string | null
  skillLevel?: string | null
  dailyAvailableMinutes?: number | null
  mainGoal?: string | null
  preferredStyles?: string[]
}

export interface PracticeCoachMessageExecuteRequest {
  userId: string
  sessionId: string
  deviceId?: string | null
  userMessage: string
  profileFormResult?: PracticeCoachProfileFormResult | null
  clientLocalDate?: string | null
  clientTimezone?: string | null
  locale?: string | null
}

export interface PracticeCoachSheetField {
  key: string
  label?: string | null
  fieldType?: 'single_choice' | 'multi_choice' | 'number' | 'text' | string
  required?: boolean
  options?: string[]
  defaultValue?: string | number | string[] | null
}

export interface PracticeCoachSheetIntent {
  sheetType: 'practice_profile_setup' | string
  title?: string | null
  message?: string | null
  requiredFields?: string[]
  fields?: PracticeCoachSheetField[]
  submitAction?: 'submit_profile_form_result' | string
}

export interface PracticeCoachPlanBlock {
  blockId?: string | null
  title: string
  durationMinutes: number
  goal?: string | null
  type?: string | null
  material?: Record<string, unknown> | null
}

export interface PracticeCoachPlanProposal {
  proposalId?: string | null
  title: string
  practiceFocus?: string | null
  totalDurationMinutes: number
  blocks: PracticeCoachPlanBlock[]
  confirmationStatus?: 'awaiting_user_confirmation' | 'confirmed' | 'rejected' | string
  requiresUserConfirmation?: boolean
  routineCardCreated?: boolean
  routineStartEnabled?: boolean
}

export interface PracticeCoachRoutineCardPayload {
  routineId: string
  sourceProposalId?: string | null
  title: string
  practiceFocus?: string | null
  totalDurationMinutes: number
  blocks: PracticeCoachPlanBlock[]
  startEnabled: boolean
  backendStartsRoutine: false
  requiresUserTapToStart: true
  [key: string]: unknown
}

export interface PracticeCoachDeviceFeedbackTracePack {
  tracePackVersion: string
  purpose?: string
  copyThisForBackendIssue: boolean
  tracePackId: string
  endpoint: string
  requestSummary: Record<string, unknown>
  responseSummary: Record<string, unknown>
  decisionTrace: Record<string, unknown>
  stateTrace: Record<string, unknown>
  artifactTrace?: Record<string, unknown>
  ioTrace: Record<string, unknown>
  safetyTrace: Record<string, unknown>
  frontendFeedbackChecklist?: string[]
}

export interface PracticeCoachMessageData {
  responseType: PracticeCoachResponseType
  content?: string | null
  message?: string | null
  missingFields?: string[]
  suggestedReplies?: string[]
  nextClientActions?: PracticeCoachNextClientAction[]
  sheetIntent?: PracticeCoachSheetIntent | null
  profileSheetIntentReady?: boolean
  planProposal?: PracticeCoachPlanProposal | null
  planProposalReady?: boolean
  routineCardPayload?: PracticeCoachRoutineCardPayload | null
  routineCardReady?: boolean
  routineStartEnabled?: boolean
  requiresUserConfirmation?: boolean
  requiresUserConfirmationBeforeRoutineCard?: boolean
  conversationStatePersisted?: boolean
  selectedActionExecutor?: string | null
  llmRequestPreview?: Record<string, unknown> | null
  stateAfter?: Record<string, unknown> | null
  deviceFeedbackTracePack?: PracticeCoachDeviceFeedbackTracePack | null
  [key: string]: unknown
}

export interface PracticeCoachSafety {
  backendSQLiteWriteMayOccur: boolean
  writesHarmonyOSLocalState: false
  startsRoutine: false
  callsEngineAdapter: false
  createsMidiAsset: false
  startsPlayback: false
  frontendMayOpenNativeSheet?: boolean
  frontendOwnsNativeSheetRendering?: boolean
  llmControlsUiDirectly?: false
  backendValidatesLlmActionContract?: boolean
  clientMustStartRoutineExplicitly?: boolean
  [key: string]: unknown
}

export interface PracticeCoachMessageExecuteResponse {
  ok: boolean
  code: string
  message: string
  data: PracticeCoachMessageData
  debug: Record<string, unknown> & { deviceFeedbackTracePack?: PracticeCoachDeviceFeedbackTracePack }
  safety: PracticeCoachSafety
}
