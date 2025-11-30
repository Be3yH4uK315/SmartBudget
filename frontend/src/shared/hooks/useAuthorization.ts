import { useEffect, useState } from 'react'
import { getUserInfo } from '@shared/store/user'
import { useDispatch } from 'react-redux'
import { useLocation } from 'react-router'
import { logoutHelper } from '../utils'

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
      } catch (_) {
      } finally {
        setIsLoading(false)
      }
    })()
  }, [dispatch, pathname])

  return { isLoading }
}
