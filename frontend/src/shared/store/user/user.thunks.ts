import { createAsyncThunk } from '@reduxjs/toolkit'
import { user_api } from '@shared/api/user'
import { User } from '@shared/types'
import { showToast } from '@shared/utils'

export const getUserInfo = createAsyncThunk<User, void, { rejectValue: 'noInfo' }>(
  'getUserInfo',
  async (_, { rejectWithValue }) => {
    const user = await user_api.getUserInfo()

    if (!user) {
      showToast({ messageKey: 'noInfo', type: 'error' })
      return rejectWithValue('noInfo')
    }

    return user
  },
)

export const getUnreadNotificationsCount = createAsyncThunk<
  { unreadCount: number },
  void,
  { rejectValue: 'cannotGetUnreadCount' }
>('getUnreadNotificationsCount', async (_, { rejectWithValue }) => {
  try {
    const response = await user_api.getUnreadNotificationsCount()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetUnreadCount', type: 'error' })

    return rejectWithValue('cannotGetUnreadCount')
  }
})
