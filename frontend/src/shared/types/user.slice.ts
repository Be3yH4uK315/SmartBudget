import { SliceCaseReducers } from './reduxToolkit'

export type userSliceState = {
  userId: string
  role: 0 | 1
  name: string
  email: string
  isAuth: boolean
}

export type userSliceReducers = SliceCaseReducers<userSliceState> & {
  clearUserState(state: userSliceState): void
}
