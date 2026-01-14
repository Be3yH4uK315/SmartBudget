import { SecuritySliceState } from '@features/settings/types'

export function getSecurityInitialState(): SecuritySliceState {
  return {
    sessions: [],
    isLoading: true,

    isDeleteLoading: false,
    isPasswordChanging: false,
  }
}
