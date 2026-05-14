import { GoalsSliceState } from '@features/goals/types'

export function getGoalsInitialState(): GoalsSliceState {
  return {
    goals: [],

    isLoading: true,
    isCreateLoading: false,

    goalsStats: {
      targetAmount: 0,
      currentAmount: 0,
    },
  }
}
