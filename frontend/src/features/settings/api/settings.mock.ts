import { changePasswordApiRequest, Session } from '@features/settings/types'

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

const sessions: { sessions: Session[] } = {
  sessions: [
    {
      sessionId: '1',
      isCurrent: true,
      ip: '192.168.1.10',
      location: 'Москва, Россия',
      deviceName: 'Chrome / Windows',
      lastActivity: '2026-01-14 12:30',
    },
    {
      sessionId: '2',
      isCurrent: false,
      ip: '192.168.1.15',
      location: 'Санкт-Петербург, Россия',
      deviceName: 'Safari / iPhone',
      lastActivity: '2026-01-12 19:10',
    },
    {
      sessionId: '3',
      isCurrent: false,
      ip: '10.0.0.2',
      location: 'Берлин, Германия',
      deviceName: 'Firefox / Linux',
      lastActivity: '2026-01-10 08:45',
    },
  ],
}

// текущее значение хранения refresh token
let refreshTokenDuration = 30

class SettingsApiMock {
  async getSessions(): Promise<{ sessions: Session[] }> {
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

    return
  }

  async getRefreshTokenDuration(): Promise<{ days: number }> {
    await delay()

    return { days: refreshTokenDuration }
  }

  async setRefreshTokenDuration(payload: number): Promise<void> {
    await delay()

    const allowed = [7, 30, 90, 180]

    if (!allowed.includes(payload)) {
      throw new Error('Invalid refresh token duration')
    }

    refreshTokenDuration = payload
    return
  }
}

export const settingsMock = new SettingsApiMock()
