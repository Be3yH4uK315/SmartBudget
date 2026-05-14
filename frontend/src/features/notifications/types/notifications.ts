export type NotificationType = 'info' | 'success' | 'alert' | 'warning' | 'system'
export type NotificationService = 'Goals' | 'Transactions' | 'Budget' | 'Limit' | 'Security'

export type NotificationBase = {
  notificationId: string
  createdAt: string
  titleKey: string
  notificationType: NotificationType
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
    spentAmount: number
    limitAmount: number
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

  'Goals.thresholdReached.message': {
    goalId: string
    name: string
    thresholdPercent: number
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
    count: number
  }

  'Transactions.categoryChanged.message': {
    transactionId: string
    oldCategoryId: number
    newCategoryId: number
  }

  'Security.newLogin.message': undefined
  'Security.passwordChanged.message': undefined
  'Security.suspiciousActivity.message': undefined
}

export type NotificationsBlock = {
  date: string
  items: Notification[]
}

export type NotificationsListResponse = {
  totalCount: number
  unreadCount: number
  items: Notification[]
}
