import { settingsApi } from '@features/settings/api'
import { settingsMock } from '@features/settings/api/settings.mock'
import { changePasswordApiRequest, Session } from '@features/settings/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getSessions = createAsyncThunk<
  Session[],
  void,
  { state: RootState; rejectWithValue: string }
>('getSessions', async (_, { rejectWithValue }) => {
  try {
    const response = await settingsMock.getSessions()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetSessions', type: 'error' })

    return rejectWithValue('cannotGetSessions')
  }
})

export const deleteSession = createAsyncThunk<
  void,
  string,
  { state: RootState; rejectWithValue: string }
>('deleteSession', async (sessionId, { rejectWithValue }) => {
  try {
    await settingsMock.deleteSession(sessionId)

    showToast({ messageKey: 'sessionDeleted', type: 'success' })
  } catch (e: any) {
    showToast({ messageKey: 'cannotDeleteSession', type: 'error' })

    return rejectWithValue('cannotDeleteSession')
  }
})

export const deleteOtherSessions = createAsyncThunk<
  void,
  void,
  { state: RootState; rejectWithValue: string }
>('deleteOtherSessions', async (_, { rejectWithValue }) => {
  try {
    await settingsMock.deleteOtherSessions()

    showToast({ messageKey: 'sessionsDeleted', type: 'success' })
  } catch (e: any) {
    showToast({ messageKey: 'cannotDeleteOtherSession', type: 'error' })

    return rejectWithValue('cannotDeleteOtherSession')
  }
})

export const changePassword = createAsyncThunk<
  void,
  changePasswordApiRequest,
  { state: RootState; rejectWithValue: string }
>('changePassword', async (payload, { rejectWithValue }) => {
  try {
    await settingsMock.changePassword({ ...payload })

    showToast({ messageKey: 'passwordChanged', type: 'success' })
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangePassword', type: 'error' })

    return rejectWithValue('cannotChangePassword')
  }
})
