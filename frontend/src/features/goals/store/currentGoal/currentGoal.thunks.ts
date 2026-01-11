import { goalsApi, goalsMock } from '@features/goals/api'
import { CurrentGoal, EditGoalPayload, GoalTransaction } from '@features/goals/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getGoal = createAsyncThunk<
  CurrentGoal,
  { goalId: string },
  { state: RootState; rejectWithValue: string }
>('getGoal', async ({ goalId }, { rejectWithValue }) => {
  try {
    const response = await goalsMock.getGoal(goalId)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetGoal', type: 'error' })

    return rejectWithValue('cannotGetGoal')
  }
})

export const getGoalTransactions = createAsyncThunk<
  GoalTransaction[],
  { goalId: string },
  { state: RootState; rejectWithValue: string }
>('getGoalTransactions', async ({ goalId }, { rejectWithValue }) => {
  try {
    const response = await goalsApi.getGoalTransactions(goalId)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetGoalTransactions', type: 'error' })

    return rejectWithValue('cannotGetGoalTransactions')
  }
})

export const editGoal = createAsyncThunk<
  EditGoalPayload,
  EditGoalPayload,
  { state: RootState; rejectWithValue: string }
>('editGoal', async ({ ...payload }, { rejectWithValue }) => {
  try {
    await goalsMock.editGoal(payload)

    showToast({ messageKey: 'categoryChanged', type: 'success' })

    return payload
  } catch (e: any) {
    showToast({ messageKey: 'cannotEditGoal', type: 'error' })

    return rejectWithValue('cannotEditGoal')
  }
})
