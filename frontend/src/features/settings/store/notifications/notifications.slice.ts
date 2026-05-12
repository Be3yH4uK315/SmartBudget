import {
  NotificationsSettingsSliceReducers,
  NotificationsSettingsSliceState,
} from '@features/settings/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getNotificationsSettingsInitialState } from './notifications.state'
import {
  changeNotificationsStatus,
  getNotificationsSettings,
  updateNotificationsSettings,
} from './notifications.thunks'

export const notificationsSettingsSlice = createSlice<
  NotificationsSettingsSliceState,
  NotificationsSettingsSliceReducers,
  'notificationsSettings',
  any
>({
  name: 'notificationsSettings',
  initialState: getNotificationsSettingsInitialState(),
  reducers: {
    clearNotificationsSettingsState() {
      getNotificationsSettingsInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getNotificationsSettings.fulfilled, (state, { payload }) => {
        const { notificationsStatus, pushStatus, goals, transactions, budget, emailStatus } =
          payload
        state.notificationsStatus = notificationsStatus
        state.notificationsSettings.budget = budget
        state.notificationsSettings.emailStatus = emailStatus
        state.notificationsSettings.goals = goals
        state.notificationsSettings.pushStatus = pushStatus
        state.notificationsSettings.transactions = transactions
        state.isLoading = false
      })
      .addCase(getNotificationsSettings.rejected, (state) => {
        state.isLoading = false
      })
      .addCase(getNotificationsSettings.pending, (state) => {
        state.isLoading = true
      })

      .addCase(changeNotificationsStatus.fulfilled, (state, { meta }) => {
        state.notificationsStatus = meta.arg
      })

      .addCase(updateNotificationsSettings.fulfilled, (state, { meta }) => {
        state.notificationsSettings = meta.arg
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof notificationsSettingsSlice> {}
}

notificationsSettingsSlice.injectInto(rootReducer)
export const { clearNotificationsSettingsState } = notificationsSettingsSlice.actions
