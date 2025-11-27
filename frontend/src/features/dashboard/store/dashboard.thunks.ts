import { createAsyncThunk } from '@reduxjs/toolkit'
import { dashboardApi } from '@features/dashboard/api'

export const getDashboardData = createAsyncThunk<DashboardResponsePayload, void>(
  'getDashboardData',
  async () => {
    const data = await dashboardApi.getDashboardData()

    return data
  },
)
