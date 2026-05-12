import { settingsApi } from '@features/settings/api'
import { changePasswordApiRequest, Session } from '@features/settings/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getSessions = createAsyncThunk<
  { sessions: Session[] },
  void,
  { state: RootState; rejectWithValue: string }
>('getSessions', async (_, { rejectWithValue }) => {
  try {
    const response = await settingsApi.getSessions()

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
    await settingsApi.deleteSession(sessionId)

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
    await settingsApi.deleteOtherSessions()

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
    await settingsApi.changePassword({ ...payload })

    showToast({ messageKey: 'passwordChanged', type: 'success' })
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangePassword', type: 'error' })

    return rejectWithValue('cannotChangePassword')
  }
})

export const setRefreshTokenDuration = createAsyncThunk<
  void,
  { days: number },
  { state: RootState; rejectWithValue: string }
>('setRefreshTokenDuration', async ({ days }, { rejectWithValue }) => {
  try {
    await settingsApi.setRefreshTokenDuration(days)

    showToast({ messageKey: 'refreshTokenDurationChanged', type: 'success' })
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangeRefreshTokenDuration', type: 'error' })

    return rejectWithValue('cannotChangeRefreshTokenDuration')
  }
})

export const getRefreshTokenDuration = createAsyncThunk<
  { days: number },
  void,
  { state: RootState; rejectWithValue: string }
>('getRefreshTokenDuration', async (_, { rejectWithValue }) => {
  try {
    const response = await settingsApi.getRefreshTokenDuration()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetRefreshTokenDuration', type: 'error' })

    return rejectWithValue('cannotGetRefreshTokenDuration')
  }
})
