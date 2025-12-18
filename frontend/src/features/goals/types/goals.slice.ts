import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { Goal } from './goals'

export type GoalsSliceState = {
  goals: Goal[]
  isLoading: boolean
  isCreateLoading: boolean

  /** Статистика по целям */
  goalsStats: {
    targetValue: number
    currentValue: number
  }
}

export type GoalsSliceReducers = SliceCaseReducers<GoalsSliceState> & {
  clearGoalsState(state: GoalsSliceState): void
}
