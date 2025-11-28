import { useEffect, useState } from 'react'
import { getUserInfo } from '@shared/store/user'
import { useDispatch } from 'react-redux'
import { logoutHelper } from '../utils'

export function useAuthorization() {
  const dispatch = useDispatch<AppDispatch>()

  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
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
  }, [dispatch])

  return { isLoading }
}
