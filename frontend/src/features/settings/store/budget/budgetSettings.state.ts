import { BudgetSettingsSliceState } from '@features/settings/types'

export function getBudgetSettingsInitialState(): BudgetSettingsSliceState {
  return {
    budgetSettings: {
      totalLimit: null,
      isAutoRenew: false,
      categories: [],
    },
    status: 'current',

    isLoading: true,
    isUpdating: false,
  }
}
