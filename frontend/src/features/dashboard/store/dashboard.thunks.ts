import { dashboardApi } from '@features/dashboard/api'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { dashboardMock } from '../api/dashboard.mock'

export const getDashboardData = createAsyncThunk<
  DashboardResponsePayload,
  void,
  { rejectValue: 'cannotGetDashboardData' }
>('getDashboardData', async (_, { rejectWithValue }) => {
  try {
    const response = await dashboardMock.getDashboardData()

    return response
  } catch (e: any) {
    return rejectWithValue('cannotGetDashboardData')
  }
})
