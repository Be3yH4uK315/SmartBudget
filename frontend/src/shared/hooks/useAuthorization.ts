import { useEffect, useState } from 'react'
import { authApi } from '@shared/api/auth'
import { getUserInfo } from '@shared/store/user'
import { useDispatch } from 'react-redux'

export function useAuthorization() {
  const dispatch = useDispatch<AppDispatch>()

  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    ;;(async () => {
      try {
        const action = await dispatch(getUserInfo())

        if (getUserInfo.rejected.match(action) && action.payload === 'noInfo') {
          await authApi.logout()
        }
      } catch (_) {
      } finally {
        setIsLoading(false)
      }
    })()
  }, [dispatch])

  return { isLoading }
}
