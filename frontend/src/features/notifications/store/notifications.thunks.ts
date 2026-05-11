import { notificationsApi, notificationsMock } from '@features/notifications/api'
import { Notification } from '@features/notifications/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getNotifications = createAsyncThunk<
  { notifications: Notification[]; length: number },
  void,
  { state: RootState }
>('getNotifications', async (_, { getState }) => {
  try {
    const state = getState()

    const offset = state.notifications?.offset ?? 0

    // const response = await notificationsMock.getNotifications()
    const response = await notificationsApi.getNotifications(offset)

    return { notifications: response, length: response.length }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetNotifications', type: 'error' })

    return { notifications: [], length: 0 }
  }
})

export const markAsRead = createAsyncThunk<void, string, { rejectValue: 'cannotMarkAsRead' }>(
  'markAsRead',
  async (notificationId, { rejectWithValue }) => {
    try {
      const response = await notificationsApi.markAsRead(notificationId)

      return response
    } catch (e: any) {
      showToast({ messageKey: 'cannotMarkAsRead', type: 'error' })

      return rejectWithValue('cannotMarkAsRead')
    }
  },
)

export const markAllAsRead = createAsyncThunk<void, void, { rejectValue: 'cannotMarkAllAsRead' }>(
  'markAllAsRead',
  async (_, { rejectWithValue }) => {
    try {
      const response = await notificationsApi.markAllAsRead()

      return response
    } catch (e: any) {
      showToast({ messageKey: 'cannotMarkAllAsRead', type: 'error' })

      return rejectWithValue('cannotMarkAllAsRead')
    }
  },
)
