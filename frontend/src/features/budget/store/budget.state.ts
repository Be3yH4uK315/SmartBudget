import { BudgetSliceState } from '@features/budget/types'

export function getBudgetInitialState(): BudgetSliceState {
  return {
    totalLimit: 0,

    currentValue: 0,

    isAutoRenew: false,

    categories: [],

    isLoading: false,
  }
}
