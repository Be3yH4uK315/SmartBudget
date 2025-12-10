import { DashboardResponsePayload } from '@features/dashboard/types'
import { api } from '@shared/api'

class DashboardApi {
  baseUrl = '/dashboard'

  async getDashboardData(): Promise<DashboardResponsePayload> {
    const url = `${this.baseUrl}/main`

    const response = await api.get<DashboardResponsePayload>(url)
    return response.data
  }
}

export const dashboardApi = new DashboardApi()
