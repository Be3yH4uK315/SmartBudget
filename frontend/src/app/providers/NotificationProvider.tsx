import { PropsWithChildren, useEffect } from 'react'
import { pushApi } from '@shared/api/push'
import { selectUser, useAppDispatch, useAppSelector } from '@shared/store'
import { getUnreadNotificationsCount } from '@shared/store/user'

const POLLING_INTERVAL = 15_000

export function NotificationsProvider({ children }: PropsWithChildren) {
  const dispatch = useAppDispatch()
  const isAuth = useAppSelector(selectUser).isAuth
  const userId = useAppSelector(selectUser).userId

  useEffect(() => {
    if (!isAuth || !userId) return

    async function initPush() {
      if (
        !('serviceWorker' in navigator) ||
        !('PushManager' in window) ||
        !('Notification' in window)
      ) {
        return
      }

      try {
        await navigator.serviceWorker.register('/serviceWorker.js')

        if (Notification.permission === 'default') {
          await pushApi.enablePushNotifications(userId)
        }

        if (Notification.permission === 'granted') {
          await pushApi.enablePushNotifications(userId)
        }
      } catch (error) {
        console.error('Push initialization failed', error)
      }
    }

    initPush()

    dispatch(getUnreadNotificationsCount())

    const intervalId = window.setInterval(() => {
      dispatch(getUnreadNotificationsCount())
    }, POLLING_INTERVAL)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [dispatch, isAuth, userId])

  return <>{children}</>
}
