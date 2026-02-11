import { Category } from '@features/budget/types'
import { PayloadAction, SliceCaseReducers } from '@shared/types'

export type BudgetSettingsSliceState = {
  budgetSettings: {
    totalLimit: number | null
    isAutoRenew: boolean
    categories: Omit<Category, 'currentValue'>[]
  }
  status: BudgetSettingsStatus
  isLoading: boolean
  isUpdating: boolean
}

export type BudgetSettingsStatus = 'current' | 'next'

export type BudgetSettingsSliceReducers = SliceCaseReducers<BudgetSettingsSliceState> & {
  clearBudgetSettingsState(state: BudgetSettingsSliceState): void
  setBudgetStatus(
    state: BudgetSettingsSliceState,
    action: PayloadAction<BudgetSettingsStatus>,
  ): void
}
