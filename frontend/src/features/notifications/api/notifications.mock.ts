import { Notification } from '@features/notifications/types'
import { Category, Transaction } from '@features/transactions/types'
import dayjs from 'dayjs'

const dates = [
  '2026-02-15T10:12:00Z',
  '2026-02-14T08:30:00Z',
  '2026-02-13T19:45:00Z',
  '2026-02-12T09:10:00Z',
  '2026-02-11T16:20:00Z',
  '2026-02-10T11:05:00Z',
]

const goalNames = ['Новая машина', 'Отпуск', 'Квартира', 'Образование']

const createMockTransaction = (id: string, i: number, date: string): Transaction => ({
  transactionId: id,
  value: 1000 + i * 250,
  categoryId: ((i % 10) + 1) as Category,
  description: i % 2 ? 'Покупка' : null,
  name: ['Pyaterochka', 'Yandex Go', 'Ozon', 'Steam'][i % 4],
  mcc: null,
  status: 'confirmed',
  date,
  type: i % 2 ? 'expense' : 'income',
})

const createNotification = (i: number, txId: string): Notification[] => {
  const date = dates[i % dates.length]

  return [
    {
      id: `limit_pre_${i}`,
      date,
      titleKey: 'Limit.preOverflow.title',
      messageKey: 'Limit.preOverflow.message',
      type: 'warning',
      isRead: !!(i % 2),
      service: 'Limit',
      props: { categoryId: (i % 10) + 1 },
    },
    {
      id: `limit_over_${i}`,
      date,
      titleKey: 'Limit.overflow.title',
      messageKey: 'Limit.overflow.message',
      type: 'alert',
      isRead: !!(i % 2),
      service: 'Limit',
      props: { categoryId: (i % 10) + 1 },
    },

    {
      id: `budget_check_${i}`,
      date,
      titleKey: 'Budget.checkResults.title',
      messageKey: 'Budget.checkResults.message',
      type: 'info',
      isRead: !!(i % 2),
      service: 'Budget',
      props: undefined,
    },
    {
      id: `budget_over_${i}`,
      date,
      titleKey: 'Budget.overflow.title',
      messageKey: 'Budget.overflow.message',
      type: 'alert',
      isRead: !!(i % 2),
      service: 'Budget',
      props: undefined,
    },
    {
      id: `budget_pre_${i}`,
      date,
      titleKey: 'Budget.preOverflow.title',
      messageKey: 'Budget.preOverflow.message',
      type: 'warning',
      isRead: !!(i % 2),
      service: 'Budget',
      props: { value: 0.8 },
    },
    {
      id: `budget_settings_${i}`,
      date,
      titleKey: 'Budget.settingsChanged.title',
      messageKey: 'Budget.settingsChanged.message',
      type: 'info',
      isRead: !!(i % 2),
      service: 'Budget',
      props: { budgetId: `budget_${i}` },
    },

    {
      id: `goal_created_${i}`,
      date,
      titleKey: 'Goals.goalCreated.title',
      messageKey: 'Goals.goalCreated.message',
      type: 'success',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
        recommendedPayment: 15000 + i * 1000,
      },
    },
    {
      id: `goal_missed_${i}`,
      date,
      titleKey: 'Goals.missedPayment.title',
      messageKey: 'Goals.missedPayment.message',
      type: 'warning',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      id: `goal_almost_${i}`,
      date,
      titleKey: 'Goals.almostAchieved.title',
      messageKey: 'Goals.almostAchieved.message',
      type: 'info',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      id: `goal_achieved_${i}`,
      date,
      titleKey: 'Goals.achieved.title',
      messageKey: 'Goals.achieved.message',
      type: 'success',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      id: `goal_expired_${i}`,
      date,
      titleKey: 'Goals.expired.title',
      messageKey: 'Goals.expired.message',
      type: 'alert',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      id: `goal_deadline_${i}`,
      date,
      titleKey: 'Goals.deadlineIsComing.title',
      messageKey: 'Goals.deadlineIsComing.message',
      type: 'warning',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
        daysLeft: (i % 10) + 1,
        currentPercent: 0.65,
      },
    },

    {
      id: `tx_unclassified_${i}`,
      date,
      titleKey: 'Transactions.unclassified.title',
      messageKey: 'Transactions.unclassified.message',
      type: 'info',
      isRead: !!(i % 2),
      service: 'Transactions',
      props: { value: (i % 10) + 1 },
    },
    {
      id: `tx_changed_${i}`,
      date,
      titleKey: 'Transactions.categoryChanged.title',
      messageKey: 'Transactions.categoryChanged.message',
      type: 'info',
      isRead: !!(i % 2),
      service: 'Transactions',
      props: {
        transactionId: txId,
        oldCategory: (i % 5) + 1,
        newCategory: ((i + 2) % 5) + 1,
      },
    },

    {
      id: `sec_login_${i}`,
      date,
      titleKey: 'Security.newLogin.title',
      messageKey: 'Security.newLogin.message',
      type: 'system',
      isRead: !!(i % 2),
      service: 'Security',
      props: undefined,
    },
    {
      id: `sec_pass_${i}`,
      date,
      titleKey: 'Security.passwordChanged.title',
      messageKey: 'Security.passwordChanged.message',
      type: 'system',
      isRead: !!(i % 2),
      service: 'Security',
      props: undefined,
    },
    {
      id: `sec_suspicious_${i}`,
      date,
      titleKey: 'Security.suspiciousActivity.title',
      messageKey: 'Security.suspiciousActivity.message',
      type: 'alert',
      isRead: !!(i % 2),
      service: 'Security',
      props: undefined,
    },
  ]
}

function generateMockData(total = 20) {
  const notifications: Notification[] = []
  const transactions = new Map<string, Transaction>()

  for (let i = 0; i < total; i++) {
    const date = dates[i % dates.length]
    const txId = `trx_${i}`

    transactions.set(txId, createMockTransaction(txId, i, date))

    notifications.push(...createNotification(i, txId))
  }

  return { notifications, transactions }
}

const { notifications, transactions } = generateMockData()

const ALL_NOTIFICATIONS: Notification[] = notifications.sort((a, b) =>
  dayjs(a.date).isAfter(dayjs(b.date)) ? -1 : 1,
)

class NotificationsMock {
  baseUrl = '/notifications'
  private data = ALL_NOTIFICATIONS
  private transactions = transactions

  private delay(ms = 500) {
    return new Promise((r) => setTimeout(r, ms))
  }

  async getNotifications(): Promise<Notification[]> {
    console.log('%cMOCK getNotifications', 'color: orange')
    await this.delay(600)
    return [...this.data]
  }

  async getTransactionById(transactionId: string): Promise<Transaction> {
    console.log('%cMOCK getTransactionById', 'color: orange', transactionId)
    await this.delay(400)

    const tx = this.transactions.get(transactionId)

    if (!tx) {
      throw new Error('Transaction not found')
    }

    return tx
  }

  async markAsRead(notificationId: string): Promise<void> {
    await this.delay(300)
    const n = this.data.find((n) => n.id === notificationId)
    if (n) n.isRead = true
  }

  async markAllAsRead(): Promise<void> {
    await this.delay(500)
    this.data.forEach((n) => (n.isRead = true))
  }
}

export const notificationsMock = new NotificationsMock()
