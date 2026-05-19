import { Category } from '@features/budget/types'
import { SliceCaseReducers } from '@shared/types'

export type BudgetSettingsSliceState = {
  budgetSettings: {
    totalLimitAmount: number | null
    isAutoRenew: boolean
    categories: Omit<Category, 'transactionType' | 'amount'>[]
  }
  isLoading: boolean
  isUpdating: boolean
}

export type BudgetSettingsSliceReducers = SliceCaseReducers<BudgetSettingsSliceState> & {
  clearBudgetSettingsState(state: BudgetSettingsSliceState): void
}
