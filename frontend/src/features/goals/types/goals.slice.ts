import { PayloadAction, SliceCaseReducers } from '@shared/types'
import { FiltersTag, GoalsFilters, GoalsStats, SimplifiedGoal } from './goals'

export type GoalsSliceState = {
  goals: SimplifiedGoal[]
  isLoading: boolean

  isCreateLoading: boolean

  filters: GoalsFilters

  goalsStats: GoalsStats
}

export type GoalsSliceReducers = SliceCaseReducers<GoalsSliceState> & {
  clearGoalsState(state: GoalsSliceState): void
  resetFilters(state: GoalsSliceState): void
  setTags(state: GoalsSliceState, action: PayloadAction<FiltersTag[]>): void
  setIsArchived(state: GoalsSliceState, action: PayloadAction<boolean>): void
}
