import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getDashboardInitialState } from './dashboard.state'
import { getDashboardData } from './dashboard.thunks'

export const dashboardSlice = createSlice<DashboardSliceState, DashboardSliceReducers, 'dashboard', any>({
  name: 'dashboard',
  initialState: getDashboardInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder.addCase(getDashboardData.fulfilled, (state, { payload }) => {
      state.budgetLimit = payload.budgetTotalLimit
      state.categories = payload.categories
      state.goals = payload.goals
      state.isLoading = false
    })

    builder.addCase(getDashboardData.rejected, (state) => {
      state.isLoading = false
    })

    builder.addCase(getDashboardData.pending, (state) => {
      state.isLoading = true
    })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof dashboardSlice> {}
}

dashboardSlice.injectInto(rootReducer)
