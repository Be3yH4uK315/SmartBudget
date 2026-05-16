import { PropsWithChildren, useEffect } from 'react'
import { selectUser, useAppDispatch, useAppSelector } from '@shared/store'
import { getUnreadNotificationsCount } from '@shared/store/user'

const POLLING_INTERVAL = 60_000

export const NotificationsProvider = ({ children }: PropsWithChildren) => {
  const dispatch = useAppDispatch()
  const isAuth = useAppSelector(selectUser).isAuth

  useEffect(() => {
    if (!isAuth) return

    dispatch(getUnreadNotificationsCount())

    const intervalId = window.setInterval(() => {
      dispatch(getUnreadNotificationsCount())
    }, POLLING_INTERVAL)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [dispatch, isAuth])

  return <>{children}</>
}
