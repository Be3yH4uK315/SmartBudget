import { SliceCaseReducers } from '@shared/types'

export type NotificationsSettingsSliceState = {
  notificationsStatus: boolean
  notificationsSettings: {
    pushStatus: boolean
    emailStatus: boolean

    goals: boolean
    transactions: boolean
    budget: {
      totalLimit: boolean
      categoriesLimit: boolean
    }
  }
  isLoading: boolean
}

export type NotificationsSettingsSliceReducers =
  SliceCaseReducers<NotificationsSettingsSliceState> & {
    clearNotificationsSettingsState(state: NotificationsSettingsSliceState): void
  }
