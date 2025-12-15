import { useEffect, useState } from 'react'
import { PUBLIC_ROUTES } from '@shared/constants/routes'
import { useAppDispatch } from '@shared/store'
import { getUserInfo } from '@shared/store/user'
import { logoutHelper } from '@shared/utils'
import { useLocation } from 'react-router'

export function useAuthorization() {
  const dispatch = useAppDispatch()
  const { pathname } = useLocation()

  const [isLoading, setIsLoading] = useState(true)

  const isPublicRoute = (path: string) => PUBLIC_ROUTES.includes(path)

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
