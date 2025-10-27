import { createAsyncThunk } from '@reduxjs/toolkit'
import { user_api } from '@shared/api/user'

export const getUserInfo = createAsyncThunk<User, void, { state: RootState }>(
  'getUserInfo',
  async () => {
    const user = await user_api.getUserInfo()

    return user
  },
)
