import { NotificationsBlock } from '@features/notifications/types'
import { SliceCaseReducers } from '@shared/types'

export type NotificationsSliceState = {
  notifications: NotificationsBlock[]
  unreadCount: number
  isLoading: boolean
  isLast: boolean
  offset: number
  isMarkLoading: boolean
}

export type NotificationsSliceReducers = SliceCaseReducers<NotificationsSliceState> & {
  clearNotificationsState(state: NotificationsSliceState): void
}
