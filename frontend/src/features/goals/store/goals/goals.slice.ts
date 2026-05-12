import { GoalsSliceReducers, GoalsSliceState, SimplifiedGoal } from '@features/goals/types'
import { pushIntoSorted } from '@features/goals/utils'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getGoalsInitialState } from './goals.state'
import { createGoal, getGoals } from './goals.thunks'

export const goalsSlice = createSlice<GoalsSliceState, GoalsSliceReducers, 'goals', any>({
  name: 'goals',
  initialState: getGoalsInitialState(),
  reducers: {
    clearGoalsState() {
      return getGoalsInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getGoals.fulfilled, (state, { payload }) => {
        const { goals, targetAmount, currentAmount } = payload

        state.goals = goals
        state.goalsStats.currentAmount = currentAmount
        state.goalsStats.targetAmount = targetAmount
        state.isLoading = false
      })

      .addCase(getGoals.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getGoals.pending, (state) => {
        state.isLoading = true
      })

      .addCase(createGoal.fulfilled, (state, { payload, meta }) => {
        const newGoal: SimplifiedGoal = {
          goalId: payload.goalId,
          ...meta.arg.payload,
          currentAmount: 0,
          isArchived: false,
          status: 'ongoing',
        }

        state.goals = pushIntoSorted(state.goals, newGoal)
        state.goalsStats.targetAmount += meta.arg.payload.targetAmount

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
export const { clearGoalsState } = goalsSlice.actions
