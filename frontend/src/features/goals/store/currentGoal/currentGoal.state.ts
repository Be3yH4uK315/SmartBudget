import { CurrentGoalSliceState } from '@features/goals/types'

export function getCurrentGoalInitialState(): CurrentGoalSliceState {
  return {
    goal: {
      goalId: '',
      name: '',
      targetValue: 0,
      currentValue: 0,
      finishDate: '',
      status: 'closed',
      daysLeft: 0,
    },
    transactions: [],

    isTransactionsLoading: true,
    isLoading: true,
    isEditLoading: false,
  }
}
