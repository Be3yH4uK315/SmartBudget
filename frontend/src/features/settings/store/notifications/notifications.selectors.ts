import { createLazySliceStateSelector } from '@shared/utils/store'
import { getNotificationsSettingsInitialState } from './notifications.state'

const sliceStateSelector = createLazySliceStateSelector(
  'notificationsSettings',
  getNotificationsSettingsInitialState(),
)

export const selectNotificationsStatus = sliceStateSelector((state) => state.notificationsStatus)
export const selectNotificationsSettings = sliceStateSelector((state) => state.notificationsSettings)
export const selectNotificationsSettingsIsLoading = sliceStateSelector((state) => state.isLoading)
