import { goalsApi, goalsMock } from '@features/goals/api'
import {
  EditGoalPayload,
  Goal,
  GoalStatus,
  GoalTransaction,
  UpdateGoalStatusPayload,
} from '@features/goals/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getGoal = createAsyncThunk<
  Goal,
  { goalId: string },
  { state: RootState; rejectWithValue: string }
>('getGoal', async ({ goalId }, { rejectWithValue }) => {
  try {
    const response = await goalsApi.getGoal(goalId)

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

    showToast({ messageKey: 'goalEdited', type: 'success' })

    return payload
  } catch (e: any) {
    showToast({ messageKey: 'cannotEditGoal', type: 'error' })

    return rejectWithValue('cannotEditGoal')
  }
})

export const updateGoalStatus = createAsyncThunk<
  { status: GoalStatus },
  UpdateGoalStatusPayload,
  { state: RootState; rejectWithValue: string }
>('updateGoalStatus', async ({ ...payload }, { rejectWithValue }) => {
  try {
    const response = await goalsApi.updateGoalStatus(payload)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotUpdateGoalStatus', type: 'error' })

    return rejectWithValue('cannotUpdateGoalStatus')
  }
})

export const updateArchivedStatus = createAsyncThunk<
  { isArchived: boolean },
  string,
  { state: RootState; rejectWithValue: string }
>('updateArchivedStatus', async (goalId, { rejectWithValue }) => {
  try {
    const response = await goalsApi.updateArchivedStatus(goalId)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotUpdateArchivedStatus', type: 'error' })

    return rejectWithValue('cannotUpdateArchivedStatus')
  }
})
