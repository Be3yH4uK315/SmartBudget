import { DashboardSliceState } from '@features/dashboard/types'

export function getDashboardInitialState(): DashboardSliceState {
  return {
    goals: [],
    categories: [],
    budgetLimit: 0,
    isLoading: true,
  }
}
