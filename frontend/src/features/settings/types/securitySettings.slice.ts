import { SliceCaseReducers } from '@shared/types'
import { Session } from './settings'

export type SecuritySliceState = {
  sessions: Session[]
  isLoading: boolean

  refreshTokenDuration: number
  isRefreshLoading: boolean

  isDeleteLoading: boolean
  isPasswordChanging: boolean
}

export type SecuritySliceReducers = SliceCaseReducers<SecuritySliceState> & {
  clearSecurityState(state: SecuritySliceState): void
}
