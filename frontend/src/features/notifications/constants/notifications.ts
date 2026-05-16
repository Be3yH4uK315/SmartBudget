import { NotificationService, NotificationType } from '@features/notifications/types'

export const NOTIFICATIONS_LIMIT = 20

export const NOTIFICATIONS_SERVICES: Exclude<NotificationService, 'Limit'>[] = [
  'Goals',
  'Transactions',
  'Budget',
  'Security',
]

export const NOTIFICATIONS_TYPES: NotificationType[] = [
  'info',
  'success',
  'alert',
  'warning',
  'system',
]
