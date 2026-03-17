import { DashboardSliceReducers, DashboardSliceState } from '@features/dashboard/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getDashboardInitialState } from './dashboard.state'
import { getDashboardBudget, getDashboardGoals } from './dashboard.thunks'

export const dashboardSlice = createSlice<
  DashboardSliceState,
  DashboardSliceReducers,
  'dashboard',
  any
>({
  name: 'dashboard',
  initialState: getDashboardInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder
      .addCase(getDashboardBudget.fulfilled, (state, { payload }) => {
        state.budgetLimit = payload.budgetTotalLimit
        state.categories = payload.categories
        state.isBudgetLoading = false
      })

      .addCase(getDashboardBudget.rejected, (state) => {
        state.isBudgetLoading = false
      })

      .addCase(getDashboardBudget.pending, (state) => {
        state.isBudgetLoading = true
      })

      .addCase(getDashboardGoals.fulfilled, (state, { payload }) => {
        state.goals = payload
        state.isGoalsLoading = false
      })

      .addCase(getDashboardGoals.rejected, (state) => {
        state.isGoalsLoading = false
      })

      .addCase(getDashboardGoals.pending, (state) => {
        state.isGoalsLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof dashboardSlice> {}
}

dashboardSlice.injectInto(rootReducer)
