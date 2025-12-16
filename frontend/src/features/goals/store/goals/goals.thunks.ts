import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'
import { goalsApi } from '../../api'
import { EditGoalPayload, Goal } from '../../types'
import { getGoalsStats } from '../../utils'

export const getGoals = createAsyncThunk<
  { goals: Goal[]; targetValue: number; currentValue: number },
  void,
  { state: RootState; rejectWithValue: string }
>('getGoals', async (_, { rejectWithValue }) => {
  try {
    const response = await goalsApi.getGoals()
    const { targetValue, currentValue } = getGoalsStats(response)

    return { goals: response, targetValue, currentValue }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetGoals', type: 'error' })

    return rejectWithValue('cannotGetGoals')
  }
})

export const createGoal = createAsyncThunk<
  string,
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
