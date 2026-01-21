import { PayloadAction, SliceCaseReducers } from '@shared/types'
import { GoalsFilters, GoalsStats, Priority, SimplifiedGoal, Tag } from './goals'

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
  setTags(state: GoalsSliceState, action: PayloadAction<Tag[]>): void
  setPriority(state: GoalsSliceState, action: PayloadAction<Priority[]>): void
  setIsArchived(state: GoalsSliceState, action: PayloadAction<boolean>): void
}
