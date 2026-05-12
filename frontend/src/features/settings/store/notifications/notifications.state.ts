import { NotificationsSettingsSliceState } from '@features/settings/types'

export function getNotificationsSettingsInitialState(): NotificationsSettingsSliceState {
  return {
    notificationsStatus: false,
    notificationsSettings: {
      pushStatus: false,
      emailStatus: false,

      goals: false,
      transactions: false,
      budget: {
        totalLimit: false,
        categoriesLimit: false,
      },
    },
    isLoading: true,
  }
}
