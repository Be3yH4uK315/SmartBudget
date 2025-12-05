import { createAsyncThunk } from '@reduxjs/toolkit'
import { user_api } from '@shared/api/user'

export const getUserInfo = createAsyncThunk<User, void, { rejectValue: 'noInfo' }>(
  'getUserInfo',
  async (_, { rejectWithValue }) => {
    try {
      const user = await user_api.getUserInfo()

      if (!user) {
        return rejectWithValue('noInfo')
      }

      return user
    } catch (e) {
      return rejectWithValue('noInfo')
    }
  },
)
