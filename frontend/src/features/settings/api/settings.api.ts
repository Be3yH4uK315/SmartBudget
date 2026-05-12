import { BudgetSettings } from '@features/budget/types'
import { changePasswordApiRequest, NotificationsSettings, Session } from '@features/settings/types'
import { api } from '@shared/api'

class SettingsApi {
  baseUrl = '/settings'

  async getSessions(): Promise<{ sessions: Session[] }> {
    const url = `${this.baseUrl}/sessions`

    const response = await api.get<{ sessions: Session[] }>(url)
    return response.data
  }

  async deleteSession(sessionId: string): Promise<void> {
    const url = `${this.baseUrl}/sessions/${sessionId}`

    const response = await api.delete<void>(url)
    return response.data
  }

  async deleteOtherSessions(): Promise<void> {
    const url = `${this.baseUrl}/sessions/logout-others`

    const response = await api.post<void>(url)
    return response.data
  }

  async changePassword({ ...payload }: changePasswordApiRequest): Promise<void> {
    const url = `${this.baseUrl}/change-password`

    const response = await api.post<void>(url, payload)
    return response.data
  }

  async getRefreshTokenDuration(): Promise<{ days: number }> {
    const url = `${this.baseUrl}/sessions/retention`

    const response = await api.get<{ days: number }>(url)
    return response.data
  }

  async setRefreshTokenDuration(days: number): Promise<void> {
    const url = `${this.baseUrl}/sessions/retention`

    const response = await api.patch<void>(url, { days })
    return response.data
  }

  async getBudgetSettings(date: string): Promise<BudgetSettings> {
    const url = `${this.baseUrl}/budget`

    const params: Record<string, string> = { date }

    const response = await api.get<BudgetSettings>(url, { params })
    return response.data
  }

  async setBudgetSettings(payload: BudgetSettings): Promise<void> {
    const url = `${this.baseUrl}/budget`

    const response = await api.patch<void>(url, { payload })
    return response.data
  }

  async getNotificationsSettings(): Promise<NotificationsSettings> {
    const url = `${this.baseUrl}/notifications`

    const response = await api.get<NotificationsSettings>(url)
    return response.data
  }

  async changeNotificationsStatus(payload: { notificationsStatus: boolean }): Promise<void> {
    const url = `${this.baseUrl}/notifications/status`

    const response = await api.patch<void>(url, payload)
    return response.data
  }

  async updateNotificationsSettings(
    payload: Omit<NotificationsSettings, 'notificationsStatus'>,
  ): Promise<void> {
    const url = `${this.baseUrl}/notifications/`

    const response = await api.patch<void>(url, payload)
    return response.data
  }
}

export const settingsApi = new SettingsApi()
