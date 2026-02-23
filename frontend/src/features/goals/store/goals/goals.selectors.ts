import { createLazySliceStateSelector } from '@shared/utils/store'
import { getGoalsInitialState } from './goals.state'

const sliceStateSelector = createLazySliceStateSelector('goals', getGoalsInitialState())

export const selectIsGoalsLoading = sliceStateSelector((state) => state.isLoading)
export const selectIsCreateGoalLoading = sliceStateSelector((state) => state.isCreateLoading)
export const selectGoals = sliceStateSelector((state) => state.goals)
export const selectGoalsStats = sliceStateSelector((state) => state.goalsStats)
