import { createLazySliceStateSelector } from '@shared/utils/store'
import { getCurrentGoalInitialState } from './currentGoal.state'

const sliceStateSelector = createLazySliceStateSelector('currentGoal', getCurrentGoalInitialState())

export const selectIsCurrentGoalLoading = sliceStateSelector((state) => state.isLoading)
export const selectCurrentGoal = sliceStateSelector((state) => state.goal)
