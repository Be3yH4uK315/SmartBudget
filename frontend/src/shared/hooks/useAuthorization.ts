import { useEffect, useState } from 'react'
import { getUserInfo } from '@shared/store/user'
import { logoutHelper } from '@shared/utils'
import { useLocation } from 'react-router'
import { useAppDispatch } from '@shared/store'

const publicRoutes = ['/auth/sign-in', '/auth/registration', '/auth/reset-password', '/']

export function useAuthorization() {
  const dispatch = useAppDispatch()
  const { pathname } = useLocation()

  const [isLoading, setIsLoading] = useState(true)

  const isPublicRoute = (path: string) => publicRoutes.includes(path)

  useEffect(() => {
    if (isPublicRoute(pathname)) {
      setIsLoading(false)
      return
    }

    ;(async () => {
      try {
        const action = await dispatch(getUserInfo())

        if (getUserInfo.rejected.match(action) && action.payload === 'noInfo') {
          await logoutHelper(dispatch)
        }
      } catch {
      } finally {
        setIsLoading(false)
      }
    })()
  }, [dispatch, pathname])

  return { isLoading }
}
