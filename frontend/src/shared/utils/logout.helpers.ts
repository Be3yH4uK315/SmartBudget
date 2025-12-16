import { authApi } from '@shared/api/auth'
import { ROUTES } from '@shared/constants/routes'
import { clearUserState } from '@shared/store/user'
import { AppDispatch } from '@shared/types'

export async function logoutHelper(dispatch: AppDispatch) {
  try {
    await authApi.logout()
  } catch {}

  dispatch(clearUserState())

  window.location.replace(ROUTES.PAGES.LOGIN)
}
