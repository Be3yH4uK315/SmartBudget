import { GoalsSliceState } from '../../types'

export function getGoalsInitialState(): GoalsSliceState {
  return {
    goals: [],
    isLoading: true,
    isCreateLoading: false,
    goalsStats: {
      targetValue: 0,
      currentValue: 0,
    },
  }
}
