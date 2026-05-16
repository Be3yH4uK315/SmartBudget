import { NotificationsSliceState } from '@features/notifications/types'

export function getNotificationsInitialState(): NotificationsSliceState {
  return {
    notifications: [],
    unreadCount: 0,
    isLoading: true,
    isLast: false,
    offset: 0,
    isMarkLoading: false,
  }
}
