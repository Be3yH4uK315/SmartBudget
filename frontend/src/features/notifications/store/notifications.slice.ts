import {
  Notification,
  NotificationsSliceReducers,
  NotificationsSliceState,
} from '@features/notifications/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { groupByDate, mergeDateBlocks } from '@shared/utils'
import { getNotificationsInitialState } from './notifications.state'
import { getNotifications, markAllAsRead } from './notifications.thunks'

export const notificationsSlice = createSlice<
  NotificationsSliceState,
  NotificationsSliceReducers,
  'notifications',
  any
>({
  name: 'notifications',
  initialState: getNotificationsInitialState(),
  reducers: {
    clearNotificationsState() {
      return getNotificationsInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getNotifications.fulfilled, (state, { payload }) => {
        const length = payload.length

        if (length === 0) {
          state.isLoading = false
          state.isLast = true
          return
        }

        const blocks = groupByDate(payload.notifications)

        if (state.notifications.length === 0) {
          state.notifications = blocks
        } else {
          state.notifications = mergeDateBlocks<Notification>({
            currentBlocks: state.notifications,
            newBlocks: blocks,
          })
        }

        state.offset += length
        state.isLoading = false

        if (length < 2) {
          state.isLast = true
        }
      })

      .addCase(getNotifications.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getNotifications.pending, (state) => {
        state.isLoading = true
      })

      .addCase(markAllAsRead.fulfilled, (state) => {
        state.isMarkLoading = false
      })

      .addCase(markAllAsRead.rejected, (state) => {
        state.isMarkLoading = false
      })

      .addCase(markAllAsRead.pending, (state) => {
        state.isMarkLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof notificationsSlice> {}
}

notificationsSlice.injectInto(rootReducer)
export const { clearNotificationsState } = notificationsSlice.actions
