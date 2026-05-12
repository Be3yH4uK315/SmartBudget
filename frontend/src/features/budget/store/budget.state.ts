import { BudgetSliceState } from '@features/budget/types'

export function getBudgetInitialState(): BudgetSliceState {
  return {
    totalLimitAmount: 0,

    spentAmount: 0,

    isAutoRenew: false,

    categories: [],

    isLoading: false,
  }
}
