import { BudgetSliceState } from '@features/budget/types'

export function getBudgetInitialState(): BudgetSliceState {
  return {
    budgetId: null,
    totalLimitAmount: 0,
    totalIncomeAmount: 0,

    isAutoRenew: false,

    categories: [],

    isLoading: false,
  }
}
