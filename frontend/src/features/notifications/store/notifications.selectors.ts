import { createLazySliceStateSelector } from '@shared/utils/store'
import { getNotificationsInitialState } from './notifications.state'

const sliceStateSelector = createLazySliceStateSelector(
  'notifications',
  getNotificationsInitialState(),
)

export const selectIsNotificationsLoading = sliceStateSelector((state) => state.isLoading)
export const selectNotifications = sliceStateSelector((state) => state.notifications)
export const selectIsLastNotification = sliceStateSelector((state) => state.isLast)
