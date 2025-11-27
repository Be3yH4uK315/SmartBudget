import { createSlice, WithSlice } from "@reduxjs/toolkit";
import { getDashboardInitialState } from "./dashboard.state";
import { getDashboardData } from "./dashboard.thunks";
import { rootReducer } from "@shared/store";

export const dashboardSlice = createSlice<dashboardSliceState, dashboardSliceReducers, 'dashboard', any>({
  name: 'dashboard',
  initialState: getDashboardInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder.addCase(getDashboardData.fulfilled, (state, {payload}) => {
        state.budgetTotalLimit = payload.budgetTotalLimit
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
  }
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof dashboardSlice> {}
}

dashboardSlice.injectInto(rootReducer)