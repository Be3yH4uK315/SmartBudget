import { SliceCaseReducers } from '@shared/types'
import { GoalsStats, SimplifiedGoal } from './goals'

export type GoalsSliceState = {
  goals: SimplifiedGoal[]
  isLoading: boolean

  isCreateLoading: boolean

  goalsStats: GoalsStats
}

export type GoalsSliceReducers = SliceCaseReducers<GoalsSliceState> & {
  clearGoalsState(state: GoalsSliceState): void
}
