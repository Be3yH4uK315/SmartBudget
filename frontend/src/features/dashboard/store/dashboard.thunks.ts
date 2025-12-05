import { dashboardApi } from '@features/dashboard/api'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { dashboardMock } from '../api/dashboard.mock'

export const getDashboardData = createAsyncThunk<DashboardResponsePayload, void>('getDashboardData', () =>
  dashboardMock.getDashboardData(),
)
