import { userSliceState } from '@shared/types'

export function getUserInitialState(): userSliceState {
  return {
    userId: '',
    role: 0,
    name: '',
    email: '',
    isAuth: false,
  }
}
