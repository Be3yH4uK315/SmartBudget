import { authApi } from '@shared/api/auth'
import { clearUserState } from '@shared/store/user'

export async function logoutHelper(dispatch: AppDispatch) {
  try {
    await authApi.logout()
  } catch (_) {}

  dispatch(clearUserState())

  window.location.replace('/auth/sign-in')
}
