// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { goalsApi, goalsMock } from '@features/goals/api'
import { EditGoalPayload, GoalsFilters, SimplifiedGoal } from '@features/goals/types'
import { getGoalsStats } from '@features/goals/utils'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getGoals = createAsyncThunk<
  { goals: SimplifiedGoal[]; targetAmount: number; currentAmount: number },
  GoalsFilters,
  { state: RootState; rejectWithValue: string }
>('getGoals', async (filters, { rejectWithValue }) => {
  try {
    const response = await goalsApi.getGoals(filters)
    const { targetAmount, currentAmount } = getGoalsStats(response)

    return { goals: response, targetAmount, currentAmount }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetGoals', type: 'error' })

    return rejectWithValue('cannotGetGoals')
  }
})

export const createGoal = createAsyncThunk<
  { goalId: string },
  { payload: Omit<EditGoalPayload, 'goalId'> },
  { state: RootState; rejectWithValue: string }
>('createGoal', async ({ payload }, { rejectWithValue }) => {
  try {
    const response = await goalsApi.createGoal(payload)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotCreateGoal', type: 'error' })

    return rejectWithValue('cannotCreateGoal')
  }
})
