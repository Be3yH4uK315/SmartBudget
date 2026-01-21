import { SliceCaseReducers } from '@shared/types'
import { Goal, GoalTransaction } from './goals'

export type CurrentGoalSliceState = {
  goal: Goal
  transactions: GoalTransaction[]

  isLoading: boolean
  isTransactionsLoading: boolean
  isEditLoading: boolean
}

export type CurrentGoalSliceReducers = SliceCaseReducers<CurrentGoalSliceState> & {
  clearCurrentGoalState(state: CurrentGoalSliceState): void
}
