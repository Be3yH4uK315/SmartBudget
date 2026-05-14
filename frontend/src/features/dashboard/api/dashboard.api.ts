import { DashboardCategory, DashboardGoal } from '@features/dashboard/types'
import { api } from '@shared/api'

class DashboardApi {
  baseUrl = '/dashboard'

  async getDashboardGoals(): Promise<{ goals: DashboardGoal[] }> {
    const url = `${this.baseUrl}/goals`

    const response = await api.get<{ goals: DashboardGoal[] }>(url)
    return response.data
  }

  async getDashboardBudget(): Promise<{
    categories: DashboardCategory[]
    totalLimitAmount: number
  }> {
    const url = `${this.baseUrl}/budget`

    const response = await api.get<{ categories: DashboardCategory[]; totalLimitAmount: number }>(
      url,
    )
    return response.data
  }
}

export const dashboardApi = new DashboardApi()
