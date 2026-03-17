export type NotificationType = 'info' | 'success' | 'alert' | 'warning' | 'system'
export type NotificationService = 'Goals' | 'Transactions' | 'Budget' | 'Limit' | 'Security'

export type NotificationBase = {
  id: string
  date: string
  titleKey: string
  type: NotificationType
  isRead: boolean
  link?: string
}

export type Notification<K extends keyof NotificationPropsMap = keyof NotificationPropsMap> =
  NotificationBase & {
    messageKey: K
    props: NotificationPropsMap[K]
    service: NotificationService
  }

export type NotificationPropsMap = {
  'Limit.preOverflow.message': {
    categoryId: number
  }

  'Limit.overflow.message': {
    categoryId: number
  }

  'Budget.checkResults.message': undefined
  'Budget.overflow.message': undefined
  'Budget.preOverflow.message': {
    value: number
  }

  'Budget.settingsChanged.message': {
    budgetId: string
  }

  'Goals.goalCreated.message': {
    goalId: string
    name: string
    recommendedPayment: number
  }

  'Goals.missedPayment.message': {
    goalId: string
    name: string
  }

  'Goals.almostAchieved.message': {
    goalId: string
    name: string
  }

  'Goals.achieved.message': {
    goalId: string
    name: string
  }

  'Goals.expired.message': {
    goalId: string
    name: string
  }

  'Goals.deadlineIsComing.message': {
    goalId: string
    name: string
    daysLeft: number
    currentPercent: number
  }

  'Transactions.unclassified.message': {
    value: number
  }

  'Transactions.categoryChanged.message': {
    transactionId: string
    oldCategory: number
    newCategory: number
  }

  'Security.newLogin.message': undefined
  'Security.passwordChanged.message': undefined
  'Security.suspiciousActivity.message': undefined
}

export type NotificationsBlock = {
  date: string
  items: Notification[]
}
