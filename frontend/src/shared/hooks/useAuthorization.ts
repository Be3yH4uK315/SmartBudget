import { useEffect, useState } from 'react'
import { getUserInfo } from '@shared/store/user'
import { logoutHelper } from '@shared/utils'
import { useDispatch } from 'react-redux'
import { useLocation } from 'react-router'

const publicRoutes = ['/auth/sign-in', '/auth/registration', '/auth/reset-password', '/']

export function useAuthorization() {
  const dispatch = useDispatch<AppDispatch>()
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
