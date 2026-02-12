import { createLazySliceStateSelector } from '@shared/utils/store'
import { getBudgetSettingsInitialState } from './budgetSettings.state'

const sliceStateSelector = createLazySliceStateSelector(
  'budgetSettings',
  getBudgetSettingsInitialState(),
)

export const selectBudgetSettings = sliceStateSelector((state) => state.budgetSettings)

export const selectIsBudgetSettingsLoading = sliceStateSelector((state) => state.isLoading)

export const selectIsBudgetSettingsUpdating = sliceStateSelector((state) => state.isUpdating)

export const selectBudgetSettingsStatus = sliceStateSelector((state) => state.status)
