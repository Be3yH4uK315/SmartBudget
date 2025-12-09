import { createAsyncThunk } from '@reduxjs/toolkit'
import { user_api } from '@shared/api/user'
import { User } from '@shared/types'
import { showToast } from '@shared/utils'

export const getUserInfo = createAsyncThunk<User, void, { rejectValue: 'noInfo' }>(
  'getUserInfo',
  async (_, { rejectWithValue }) => {
    const user = await user_api.getUserInfo()

    if (!user) {
      showToast({ messageKey: 'noInfo', type: 'error', duration: 5000 })
      return rejectWithValue('noInfo')
    }

    return user
  },
)
