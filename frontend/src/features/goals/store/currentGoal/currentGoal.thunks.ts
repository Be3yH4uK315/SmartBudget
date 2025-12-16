import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'
import { goalsApi } from '../../api'
import { CurrentGoal, EditGoalPayload } from '../../types'

export const getGoal = createAsyncThunk<
  CurrentGoal,
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

export const editGoal = createAsyncThunk<
  EditGoalPayload,
  EditGoalPayload,
  { state: RootState; rejectWithValue: string }
>('editGoal', async ({ ...payload }, { rejectWithValue }) => {
  try {
    await goalsApi.editGoal(payload)

    showToast({ messageKey: 'categoryChanged', type: 'success' })

    return payload
  } catch (e: any) {
    showToast({ messageKey: 'cannotEditGoal', type: 'error' })

    return rejectWithValue('cannotEditGoal')
  }
})
