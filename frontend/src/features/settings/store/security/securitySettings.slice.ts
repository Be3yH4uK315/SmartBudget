import { SecuritySliceReducers, SecuritySliceState } from '@features/settings/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getSecurityInitialState } from './securitySettings.state'
import {
  changePassword,
  deleteOtherSessions,
  deleteSession,
  getSessions,
} from './securitySettings.thunks'

export const securitySlice = createSlice<
  SecuritySliceState,
  SecuritySliceReducers,
  'security',
  any
>({
  name: 'security',
  initialState: getSecurityInitialState(),
  reducers: {
    clearSecurityState() {
      return getSecurityInitialState()
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(getSessions.fulfilled, (state, { payload }) => {
        state.isLoading = false
        state.sessions = payload
      })

      .addCase(getSessions.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getSessions.pending, (state) => {
        state.isLoading = true
      })

      .addCase(deleteSession.fulfilled, (state, { meta }) => {
        state.isDeleteLoading = false
        state.sessions = state.sessions.filter((s) => s.sessionId !== meta.arg)
      })

      .addCase(deleteSession.rejected, (state) => {
        state.isDeleteLoading = false
      })

      .addCase(deleteSession.pending, (state) => {
        state.isDeleteLoading = true
      })

      .addCase(deleteOtherSessions.fulfilled, (state) => {
        state.isDeleteLoading = false
        state.sessions = state.sessions.filter((s) => s.isCurrentSession)
      })

      .addCase(deleteOtherSessions.rejected, (state) => {
        state.isDeleteLoading = false
      })

      .addCase(deleteOtherSessions.pending, (state) => {
        state.isDeleteLoading = true
      })

      .addCase(changePassword.fulfilled, (state) => {
        state.isPasswordChanging = false
      })

      .addCase(changePassword.rejected, (state) => {
        state.isPasswordChanging = false
      })

      .addCase(changePassword.pending, (state) => {
        state.isPasswordChanging = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof securitySlice> {}
}

securitySlice.injectInto(rootReducer)
export const { clearSecurityState } = securitySlice.actions
