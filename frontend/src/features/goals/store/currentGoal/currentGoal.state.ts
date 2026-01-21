import { CurrentGoalSliceState } from '@features/goals/types'

export function getCurrentGoalInitialState(): CurrentGoalSliceState {
  return {
    goal: {
      goalId: '',
      name: '',
      targetValue: 0,
      currentValue: 0,
      status: 'closed',
      isArchived: false,
      tags: [],
      priority: null,
      finishDate: null,
      daysLeft: null,
      recommendedPayment: null,
    },
    transactions: [],

    isTransactionsLoading: true,
    isLoading: true,
    isEditLoading: false,
  }
}
