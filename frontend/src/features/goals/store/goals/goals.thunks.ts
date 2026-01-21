// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { goalsApi, goalsMock } from '@features/goals/api'
import { EditGoalPayload, SimplifiedGoal } from '@features/goals/types'
import { getGoalsStats } from '@features/goals/utils'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getGoals = createAsyncThunk<
  { goals: SimplifiedGoal[]; targetValue: number; currentValue: number },
  void,
  { state: RootState; rejectWithValue: string }
>('getGoals', async (_, { getState, rejectWithValue }) => {
  try {
    const filters = getState().goals?.filters

    const response = await goalsMock.getGoals(filters)
    const { targetValue, currentValue } = getGoalsStats(response)

    return { goals: response, targetValue, currentValue }
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
    const response = await goalsMock.createGoal(payload)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotCreateGoal', type: 'error' })

    return rejectWithValue('cannotCreateGoal')
  }
})
