import { BudgetSettings } from '@features/budget/types'
import { changePasswordApiRequest, NotificationsSettings, Session } from '@features/settings/types'

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

let sessionsStore: Session[] = [
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
]

let refreshTokenDuration = 30

const budgetStore: Record<string, BudgetSettings> = {}

let notificationsSettingsStore: NotificationsSettings = {
  notificationsStatus: true,
  pushStatus: true,
  emailStatus: false,

  goals: true,
  transactions: true,
  budget: {
    totalLimit: true,
    categoriesLimit: false,
  },
}

class SettingsApiMock {
  baseUrl = '/settings'

  async getSessions(): Promise<{ sessions: Session[] }> {
    await delay()
    return { sessions: sessionsStore }
  }

  async deleteSession(sessionId: string): Promise<void> {
    await delay()
    sessionsStore = sessionsStore.filter((s) => s.sessionId !== sessionId)
  }

  async deleteOtherSessions(): Promise<void> {
    await delay()
    sessionsStore = sessionsStore.filter((s) => s.isCurrent)
  }

  async changePassword(payload: changePasswordApiRequest): Promise<void> {
    await delay()

    if (!payload.password || !payload.newPassword) {
      throw new Error('Invalid password payload')
    }

    if (payload.password === payload.newPassword) {
      throw new Error('New password must be different')
    }
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
  }

  async getBudgetSettings(date: string): Promise<BudgetSettings> {
    await delay()

    if (!budgetStore[date]) {
      budgetStore[date] = {
        totalLimitAmount: 0,
        isAutoRenew: false,
        categories: [],
      }
    }

    return budgetStore[date]
  }

  async setBudgetSettings(payload: BudgetSettings): Promise<void> {
    await delay()

    const dateKey = new Date().toISOString().slice(0, 7)

    budgetStore[dateKey] = payload
  }

  async getNotificationsSettings(): Promise<NotificationsSettings> {
    await delay()
    return { ...notificationsSettingsStore }
  }

  async changeNotificationsStatus(payload: { status: boolean }): Promise<void> {
    await delay()

    notificationsSettingsStore.notificationsStatus = payload.status
  }

  async updateNotificationsSettings(
    payload: Omit<NotificationsSettings, 'notificationsStatus'>,
  ): Promise<void> {
    await delay()

    notificationsSettingsStore = {
      ...notificationsSettingsStore,
      ...payload,
    }
  }
}

export const settingsMock = new SettingsApiMock()
