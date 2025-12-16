import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { GoalsSliceReducers, GoalsSliceState } from '../../types'
import { getGoalsInitialState } from './goals.state'
import { createGoal, getGoals } from './goals.thunks'

export const goalsSlice = createSlice<GoalsSliceState, GoalsSliceReducers, 'goals', any>({
  name: 'goals',
  initialState: getGoalsInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder
      .addCase(getGoals.fulfilled, (state, { payload }) => {
        const { goals, targetValue, currentValue } = payload

        state.goals = goals
        state.goalsStats.currentValue = currentValue
        state.goalsStats.targetValue = targetValue
        state.isLoading = false
      })
      .addCase(getGoals.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getGoals.pending, (state) => {
        state.isLoading = true
      })

      .addCase(createGoal.fulfilled, (state, { payload, meta }) => {
        const newGoal = {
          goalId: payload,
          ...meta.arg.payload,
          currentValue: 0,
          status: 'ongoing' as const,
        }

        state.goals.unshift(newGoal)
        state.goalsStats.targetValue += meta.arg.payload.targetValue

        state.isCreateLoading = false
      })

      .addCase(createGoal.rejected, (state) => {
        state.isCreateLoading = false
      })

      .addCase(createGoal.pending, (state) => {
        state.isCreateLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof goalsSlice> {}
}

goalsSlice.injectInto(rootReducer)
