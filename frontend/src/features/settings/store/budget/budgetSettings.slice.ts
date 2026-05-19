import { BudgetSettingsSliceReducers, BudgetSettingsSliceState } from '@features/settings/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getBudgetSettingsInitialState } from './budgetSettings.state'
import { getBudgetSettings, setBudgetSettings } from './budgetSettings.thunks'

export const budgetSettingsSlice = createSlice<
  BudgetSettingsSliceState,
  BudgetSettingsSliceReducers,
  'budgetSettings',
  any
>({
  name: 'budgetSettings',
  initialState: getBudgetSettingsInitialState(),
  reducers: {
    clearBudgetSettingsState() {
      getBudgetSettingsInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getBudgetSettings.fulfilled, (state, { payload }) => {
        state.budgetSettings = {
          ...payload,
        }
        state.isLoading = false
      })
      .addCase(getBudgetSettings.rejected, (state) => {
        state.isLoading = false
      })
      .addCase(getBudgetSettings.pending, (state) => {
        state.isLoading = true
      })

      .addCase(setBudgetSettings.fulfilled, (state, { meta }) => {
        state.isUpdating = false
        state.budgetSettings = meta.arg
      })
      .addCase(setBudgetSettings.rejected, (state) => {
        state.isUpdating = false
      })
      .addCase(setBudgetSettings.pending, (state) => {
        state.isUpdating = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof budgetSettingsSlice> {}
}

budgetSettingsSlice.injectInto(rootReducer)
export const { clearBudgetSettingsState } = budgetSettingsSlice.actions
