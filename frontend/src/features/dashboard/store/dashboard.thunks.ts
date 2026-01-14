import { dashboardApi } from '@features/dashboard/api'
import {
  DashboardCategory,
  DashboardGoal,
  DashboardResponsePayload,
} from '@features/dashboard/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { dashboardMock } from '../api/dashboard.mock'

export const getDashboardData = createAsyncThunk<
  { goals: DashboardGoal[] },
  void,
  { rejectValue: 'cannotGetDashboardData' }
>('getDashboardData', async (_, { rejectWithValue }) => {
  try {
    const response = await dashboardApi.getDashboardData()

    return response
  } catch (e: any) {
    return rejectWithValue('cannotGetDashboardData')
  }
})
