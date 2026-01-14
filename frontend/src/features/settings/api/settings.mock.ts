import { changePasswordApiRequest, Session } from '@features/settings/types'

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

const sessions: Session[] = [
  {
    sessionId: '1',
    isCurrentSession: true,
    ip: '192.168.1.10',
    location: 'Москва, Россия',
    deviceName: 'Chrome / Windows',
    lastActivity: '2026-01-14 12:30',
  },
  {
    sessionId: '2',
    isCurrentSession: false,
    ip: '192.168.1.15',
    location: 'Санкт-Петербург, Россия',
    deviceName: 'Safari / iPhone',
    lastActivity: '2026-01-12 19:10',
  },
  {
    sessionId: '3',
    isCurrentSession: false,
    ip: '10.0.0.2',
    location: 'Берлин, Германия',
    deviceName: 'Firefox / Linux',
    lastActivity: '2026-01-10 08:45',
  },
]

class SettingsApiMock {
  async getSessions(): Promise<Session[]> {
    await delay()
    return sessions
  }

  async deleteSession(sessionId: string): Promise<void> {
    await delay()

    return
  }

  async deleteOtherSessions(): Promise<void> {
    await delay()

    return
  }

  async changePassword(payload: changePasswordApiRequest): Promise<void> {
    await delay()

    if (!payload.password || !payload.newPassword) {
      throw new Error('Invalid password payload')
    }

    if (payload.password === payload.newPassword) {
      throw new Error('New password must be different')
    }

    // Здесь просто имитация успешной смены пароля
    return
  }
}

export const settingsMock = new SettingsApiMock()
