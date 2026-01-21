import { GoalsSliceState } from '@features/goals/types'

export function getGoalsInitialState(): GoalsSliceState {
  return {
    goals: [],

    isLoading: true,
    isCreateLoading: false,

    filters: {
      tags: [],
      priority: [],
      isArchived: false,
    },

    goalsStats: {
      targetValue: 0,
      currentValue: 0,
    },
  }
}
