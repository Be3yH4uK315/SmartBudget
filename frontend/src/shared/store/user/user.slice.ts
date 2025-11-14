import { createSlice } from '@reduxjs/toolkit'
import { getUserInitialState } from './user.state'
import { getUserInfo } from './user.thunks'

export const userSlice = createSlice<userSliceState, userSliceReducers, 'user', any>({
  name: 'user',
  initialState: getUserInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder.addCase(getUserInfo.fulfilled, (state, { payload }) => {
      state.name = payload.NAME
      state.role = payload.ROLE
      state.userId = payload.ID
      state.email = payload.EMAIL
    })
  },
})
