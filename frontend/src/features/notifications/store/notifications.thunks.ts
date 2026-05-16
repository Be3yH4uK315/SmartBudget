import { notificationsApi } from '@features/notifications/api'
import { Notification, NotificationsFilters } from '@features/notifications/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getNotifications = createAsyncThunk<
  { notifications: Notification[]; length: number; totalCount: number; unreadCount: number },
  NotificationsFilters,
  { state: RootState }
>('getNotifications', async (filters, { getState }) => {
  try {
    const state = getState()

    const offset = state.notifications?.offset ?? 0

    const response = await notificationsApi.getNotifications(offset, filters)

    return {
      notifications: response.items,
      length: response.items.length,
      totalCount: response.totalCount,
      unreadCount: response.unreadCount,
    }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetNotifications', type: 'error' })

    return { notifications: [], length: 0, totalCount: 0, unreadCount: 0 }
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
