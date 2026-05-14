import { SliceCaseReducers } from './reduxToolkit'

export type userSliceState = {
  userId: string
  role: 0 | 1
  name: string
  email: string
  isAuth: boolean
  unreadCount: number
}

export type userSliceReducers = SliceCaseReducers<userSliceState> & {
  clearUserState(state: userSliceState): void
}
