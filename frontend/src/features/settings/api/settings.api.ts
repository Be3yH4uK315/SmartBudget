import { changePasswordApiRequest, Session } from '@features/settings/types/settings'
import { api } from '@shared/api'

class SettingsApi {
  baseUrl = '/settings'

  async getSessions(): Promise<Session[]> {
    const url = `${this.baseUrl}/sessions`

    const response = await api.get<Session[]>(url)
    return response.data
  }

  async deleteSession(sessionId: Pick<Session, 'sessionId'>): Promise<void> {
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
}

export const settingsApi = new SettingsApi()
