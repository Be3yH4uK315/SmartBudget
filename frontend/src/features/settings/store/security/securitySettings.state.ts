import { SecuritySliceState } from '@features/settings/types'

export function getSecurityInitialState(): SecuritySliceState {
  return {
    sessions: [],
    isLoading: true,

    refreshTokenDuration: 0,
    isRefreshLoading: true,

    isDeleteLoading: false,
    isPasswordChanging: false,
  }
}
