import { CurrentGoalSliceState } from '../../types'

export function getCurrentGoalInitialState(): CurrentGoalSliceState {
  return {
    goal: {
      goalId: '',
      name: '',
      targetValue: 0,
      currentValue: 0,
      finishDate: '',
      status: 'closed',
      transactions: [],
      daysLeft: 0,
    },
    isLoading: true,
    isEditLoading: false,
  }
}
