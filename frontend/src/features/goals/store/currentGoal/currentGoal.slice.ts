import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { CurrentGoalSliceReducers, CurrentGoalSliceState } from '../../types'
import { getCurrentGoalInitialState } from './currentGoal.state'
import { editGoal, getGoal } from './currentGoal.thunks'

export const currentGoalSlice = createSlice<
  CurrentGoalSliceState,
  CurrentGoalSliceReducers,
  'currentGoal',
  any
>({
  name: 'currentGoal',
  initialState: getCurrentGoalInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder
      .addCase(getGoal.fulfilled, (state, { payload }) => {
        state.goal = payload
        state.isLoading = false
      })

      .addCase(getGoal.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getGoal.pending, (state) => {
        state.isLoading = true
      })

      .addCase(editGoal.fulfilled, (state, { payload }) => {
        state.goal = { ...state.goal, ...payload }
        state.isEditLoading = false
      })
      .addCase(editGoal.rejected, (state) => {
        state.isEditLoading = false
      })
      .addCase(editGoal.pending, (state) => {
        state.isEditLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof currentGoalSlice> {}
}

currentGoalSlice.injectInto(rootReducer)
