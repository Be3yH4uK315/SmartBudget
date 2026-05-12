import { settingsApi, settingsMock } from '@features/settings/api'
import { NotificationsSettings } from '@features/settings/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { showToast } from '@shared/utils'

export const getNotificationsSettings = createAsyncThunk<
  NotificationsSettings,
  void,
  { rejectValue: 'cannotGetNotificationsSettings' }
>('getNotificationsSettings', async (_, { rejectWithValue }) => {
  try {
    const response = await settingsApi.getNotificationsSettings()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetNotificationsSettings', type: 'error' })

    return rejectWithValue('cannotGetNotificationsSettings')
  }
})

export const changeNotificationsStatus = createAsyncThunk<
  void,
  boolean,
  { rejectValue: 'cannotChangeNotificationsStatus' }
>('changeNotificationsStatus', async (notificationsStatus, { rejectWithValue }) => {
  try {
    const response = await settingsApi.changeNotificationsStatus({ notificationsStatus })

    showToast({ messageKey: 'NotificationsSettingsUpdated', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangeNotificationsStatus', type: 'error' })

    return rejectWithValue('cannotChangeNotificationsStatus')
  }
})

export const updateNotificationsSettings = createAsyncThunk<
  void,
  Omit<NotificationsSettings, 'notificationsStatus'>,
  { rejectValue: 'cannotUpdateNotificationsSettings' }
>('updateNotificationsSettings', async (payload, { rejectWithValue }) => {
  try {
    const response = await settingsApi.updateNotificationsSettings(payload)

    showToast({ messageKey: 'NotificationsSettingsUpdated', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotUpdateNotificationsSettings', type: 'error' })

    return rejectWithValue('cannotUpdateNotificationsSettings')
  }
})
