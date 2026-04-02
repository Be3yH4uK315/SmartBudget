import { DashboardCategory, DashboardGoal } from '@features/dashboard/types'
import { api } from '@shared/api'

class DashboardApi {
  baseUrl = '/dashboard'

  async getDashboardGoals(): Promise<DashboardGoal[]> {
    const url = `${this.baseUrl}/goals`

    const response = await api.get<DashboardGoal[]>(url)
    return response.data
  }

  async getDashboardBudget(): Promise<{
    categories: DashboardCategory[]
    budgetTotalLimit: number
  }> {
    const url = `${this.baseUrl}/budget`

    const response = await api.get<{ categories: DashboardCategory[]; budgetTotalLimit: number }>(
      url,
    )
    return response.data
  }
}

export const dashboardApi = new DashboardApi()
