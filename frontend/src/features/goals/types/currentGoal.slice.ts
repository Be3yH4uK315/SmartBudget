import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { CurrentGoal, GoalTransaction } from './goals'

export type CurrentGoalSliceState = {
  goal: Omit<CurrentGoal, 'transactions'>
  transactions: GoalTransaction[]

  isLoading: boolean
  isTransactionsLoading: boolean
  isEditLoading: boolean
}

export type CurrentGoalSliceReducers = SliceCaseReducers<CurrentGoalSliceState> & {
  clearCurrentGoalState(state: CurrentGoalSliceState): void
}
