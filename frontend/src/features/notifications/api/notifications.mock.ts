import { Notification } from '@features/notifications/types'
import { CategoryNumber, Transaction } from '@features/transactions/types'
import dayjs from 'dayjs'

const createdAts = [
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
  amount: 1000 + i * 250,
  categoryId: ((i % 10) + 1) as CategoryNumber,
  description: i % 2 ? 'Покупка' : null,
  merchant: ['Pyaterochka', 'Yandex Go', 'Ozon', 'Steam'][i % 4],
  mcc: null,
  status: 'confirmed',
  date,
  transactionType: i % 2 ? 'expense' : 'income',
})

const createNotification = (i: number, txId: string): Notification[] => {
  const createdAt = createdAts[i % createdAts.length]

  return [
    {
      notificationId: `limit_pre_${i}`,
      createdAt,
      titleKey: 'Limit.preOverflow.title',
      messageKey: 'Limit.preOverflow.message',
      notificationType: 'warning',
      isRead: !!(i % 2),
      service: 'Limit',
      props: { categoryId: (i % 10) + 1 },
    },
    {
      notificationId: `limit_over_${i}`,
      createdAt,
      titleKey: 'Limit.overflow.title',
      messageKey: 'Limit.overflow.message',
      notificationType: 'alert',
      isRead: !!(i % 2),
      service: 'Limit',
      props: { categoryId: (i % 10) + 1 },
    },

    {
      notificationId: `budget_check_${i}`,
      createdAt,
      titleKey: 'Budget.checkResults.title',
      messageKey: 'Budget.checkResults.message',
      notificationType: 'info',
      isRead: !!(i % 2),
      service: 'Budget',
      props: undefined,
    },
    {
      notificationId: `budget_over_${i}`,
      createdAt,
      titleKey: 'Budget.overflow.title',
      messageKey: 'Budget.overflow.message',
      notificationType: 'alert',
      isRead: !!(i % 2),
      service: 'Budget',
      props: undefined,
    },
    {
      notificationId: `budget_pre_${i}`,
      createdAt,
      titleKey: 'Budget.preOverflow.title',
      messageKey: 'Budget.preOverflow.message',
      notificationType: 'warning',
      isRead: !!(i % 2),
      service: 'Budget',
      props: { limitAmount: 1, spentAmount: 0.2 },
    },
    {
      notificationId: `budget_settings_${i}`,
      createdAt,
      titleKey: 'Budget.settingsChanged.title',
      messageKey: 'Budget.settingsChanged.message',
      notificationType: 'info',
      isRead: !!(i % 2),
      service: 'Budget',
      props: { budgetId: `budget_${i}` },
    },

    {
      notificationId: `goal_created_${i}`,
      createdAt,
      titleKey: 'Goals.goalCreated.title',
      messageKey: 'Goals.goalCreated.message',
      notificationType: 'success',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
        recommendedPayment: 15000 + i * 1000,
      },
    },
    {
      notificationId: `goal_missed_${i}`,
      createdAt,
      titleKey: 'Goals.missedPayment.title',
      messageKey: 'Goals.missedPayment.message',
      notificationType: 'warning',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      notificationId: `goal_almost_${i}`,
      createdAt,
      titleKey: 'Goals.thresholdReached.title',
      messageKey: 'Goals.thresholdReached.message',
      notificationType: 'info',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      notificationId: `goal_achieved_${i}`,
      createdAt,
      titleKey: 'Goals.achieved.title',
      messageKey: 'Goals.achieved.message',
      notificationType: 'success',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      notificationId: `goal_expired_${i}`,
      createdAt,
      titleKey: 'Goals.expired.title',
      messageKey: 'Goals.expired.message',
      notificationType: 'alert',
      isRead: !!(i % 2),
      service: 'Goals',
      props: {
        goalId: `goal_${i}`,
        name: goalNames[i % goalNames.length],
      },
    },
    {
      notificationId: `goal_deadline_${i}`,
      createdAt,
      titleKey: 'Goals.deadlineIsComing.title',
      messageKey: 'Goals.deadlineIsComing.message',
      notificationType: 'warning',
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
      notificationId: `tx_unclassified_${i}`,
      createdAt,
      titleKey: 'Transactions.unclassified.title',
      messageKey: 'Transactions.unclassified.message',
      notificationType: 'info',
      isRead: !!(i % 2),
      service: 'Transactions',
      props: { count: (i % 10) + 1 },
    },
    {
      notificationId: `tx_changed_${i}`,
      createdAt,
      titleKey: 'Transactions.categoryChanged.title',
      messageKey: 'Transactions.categoryChanged.message',
      notificationType: 'info',
      isRead: !!(i % 2),
      service: 'Transactions',
      props: {
        transactionId: txId,
        oldCategoryId: (i % 5) + 1,
        newCategoryId: ((i + 2) % 5) + 1,
      },
    },

    {
      notificationId: `sec_login_${i}`,
      createdAt,
      titleKey: 'Security.newLogin.title',
      messageKey: 'Security.newLogin.message',
      notificationType: 'system',
      isRead: !!(i % 2),
      service: 'Security',
      props: undefined,
    },
    {
      notificationId: `sec_pass_${i}`,
      createdAt,
      titleKey: 'Security.passwordChanged.title',
      messageKey: 'Security.passwordChanged.message',
      notificationType: 'system',
      isRead: !!(i % 2),
      service: 'Security',
      props: undefined,
    },
    {
      notificationId: `sec_suspicious_${i}`,
      createdAt,
      titleKey: 'Security.suspiciousActivity.title',
      messageKey: 'Security.suspiciousActivity.message',
      notificationType: 'alert',
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
    const createdAt = createdAts[i % createdAts.length]
    const txId = `trx_${i}`

    transactions.set(txId, createMockTransaction(txId, i, createdAt))

    notifications.push(...createNotification(i, txId))
  }

  return { notifications, transactions }
}

const { notifications, transactions } = generateMockData()

const ALL_NOTIFICATIONS: Notification[] = notifications.sort((a, b) =>
  dayjs(a.createdAt).isAfter(dayjs(b.createdAt)) ? -1 : 1,
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
    const n = this.data.find((n) => n.notificationId === notificationId)
    if (n) n.isRead = true
  }

  async markAllAsRead(): Promise<void> {
    await this.delay(500)
    this.data.forEach((n) => (n.isRead = true))
  }
}

export const notificationsMock = new NotificationsMock()
