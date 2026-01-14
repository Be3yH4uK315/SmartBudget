import {
  DashboardCategory,
  DashboardGoal,
  DashboardResponsePayload,
} from '@features/dashboard/types'
import { api } from '@shared/api'

class DashboardApi {
  baseUrl = '/dashboard'

  async getDashboardData(): Promise<{ goals: DashboardGoal[] }> {
    const url = `${this.baseUrl}/goals`

    const response = await api.get<{ goals: DashboardGoal[] }>(url)
    return response.data
  }
}

export const dashboardApi = new DashboardApi()
