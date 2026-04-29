import { dashboardApi, dashboardMock } from '@features/dashboard/api'
import { DashboardCategory, DashboardGoal } from '@features/dashboard/types'
import { createAsyncThunk } from '@reduxjs/toolkit'

export const getDashboardGoals = createAsyncThunk<
  DashboardGoal[],
  void,
  { rejectValue: 'cannotGetDashboardGoals' }
>('getDashboardGoals', async (_, { rejectWithValue }) => {
  try {
    const response = await dashboardMock.getDashboardGoals()

    return response
  } catch (e: any) {
    return rejectWithValue('cannotGetDashboardGoals')
  }
})

export const getDashboardBudget = createAsyncThunk<
  { categories: DashboardCategory[]; budgetTotalLimit: number },
  void,
  { rejectValue: 'cannotGetDashboardBudget' }
>('getDashboardBudget', async (_, { rejectWithValue }) => {
  try {
    const response = await dashboardMock.getDashboardBudget()

    return response
  } catch (e: any) {
    return rejectWithValue('cannotGetDashboardBudget')
  }
})
