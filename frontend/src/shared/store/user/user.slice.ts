import { createSlice } from '@reduxjs/toolkit'
import { userSliceReducers, userSliceState } from '@shared/types'
import { getUserInitialState } from './user.state'
import { getUserInfo } from './user.thunks'

export const userSlice = createSlice<userSliceState, userSliceReducers, 'user', any>({
  name: 'user',
  initialState: getUserInitialState(),
  reducers: {
    clearUserState() {
      return getUserInitialState()
    },
  },

  extraReducers: (builder) => {
    builder.addCase(getUserInfo.fulfilled, (state, { payload }) => {
      state.name = payload.name
      state.role = payload.role
      state.userId = payload.id
      state.email = payload.email
      state.isAuth = true
    })
  },
})

export const userReducer = userSlice.reducer
export const { clearUserState } = userSlice.actions
