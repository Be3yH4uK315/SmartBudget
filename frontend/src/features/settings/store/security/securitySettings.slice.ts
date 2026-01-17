import { SecuritySliceReducers, SecuritySliceState } from '@features/settings/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getSecurityInitialState } from './securitySettings.state'
import {
  changePassword,
  deleteOtherSessions,
  deleteSession,
  getRefreshTokenDuration,
  getSessions,
  setRefreshTokenDuration,
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
        state.sessions = payload.sessions
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
        state.sessions = state.sessions.filter((s) => s.isCurrent)
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

      .addCase(getRefreshTokenDuration.fulfilled, (state, { payload }) => {
        state.refreshTokenDuration = payload.days
        state.isRefreshLoading = false
      })
      .addCase(getRefreshTokenDuration.rejected, (state) => {
        state.isRefreshLoading = false
      })
      .addCase(getRefreshTokenDuration.pending, (state) => {
        state.isRefreshLoading = true
      })

      .addCase(setRefreshTokenDuration.fulfilled, (state, { meta }) => {
        state.refreshTokenDuration = meta.arg.days
        state.isRefreshLoading = false
      })
      .addCase(setRefreshTokenDuration.rejected, (state) => {
        state.isRefreshLoading = false
      })
      .addCase(setRefreshTokenDuration.pending, (state) => {
        state.isRefreshLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof securitySlice> {}
}

securitySlice.injectInto(rootReducer)
export const { clearSecurityState } = securitySlice.actions
