import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { BudgetSliceReducers, BudgetSliceState } from '../types'
import { getBudgetInitialState } from './budget.state'
import { getBudgetData } from './budget.thunks'

export const budgetSlice = createSlice<BudgetSliceState, BudgetSliceReducers, 'budget', any>({
  name: 'budget',
  initialState: getBudgetInitialState(),
  reducers: {
    clearBudgetState() {
      getBudgetInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getBudgetData.fulfilled, (state, { payload }) => {
        const { totalLimit, currentValue, isAutoRenew, categories } = payload

        state.totalLimit = totalLimit
        state.isAutoRenew = isAutoRenew
        state.currentValue = currentValue
        state.categories = categories
        state.isLoading = false
      })

      .addCase(getBudgetData.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getBudgetData.pending, (state) => {
        state.isLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof budgetSlice> {}
}

budgetSlice.injectInto(rootReducer)
